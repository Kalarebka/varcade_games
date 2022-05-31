import flask
import json

import pytest

from unittest.mock import call, MagicMock, patch

from redis import WatchError, RedisError, Redis

from core.db import initialise_db, get_stats_tracker_db

from leaderboards.api import delete_user, remove_user_from_leaderboards, make_response
from leaderboards.leaderboards import (
    record_result,
    get_top_players,
    get_user_rank,
    get_leaderboard_handler,
    register_leaderboard_handler,
    add_to_users_leaderboard_set,
    get_users_leaderboard_set,
)
from leaderboards.handlers import LeaderboardHandler


class TestLeaderboards:
    def test_record_result(self, stats_tracker_db):
        record_result("exrps", "winner", "loser")

    def test_get_top_players(self, stats_tracker_db):
        record_result("exrps", "userA", "userB")
        record_result("exrps", "userA", "userB")
        record_result("exrps", "userB", "userA")
        top_ten = get_top_players("exrps")

        assert len(top_ten) == 2
        assert top_ten[0]["user_id"] == "userA"
        assert top_ten[0]["score"] == 2
        assert top_ten[1]["user_id"] == "userB"
        assert top_ten[1]["score"] == 1

    def test_get_user_rank(self, stats_tracker_db):
        record_result("exrps", "winner", "loser")
        assert get_user_rank("exrps", "winner") == 1
        assert get_user_rank("exrps", "loser") == 0

    def test_add_to_users_leaderboard_set(self, stats_tracker_db):
        add_to_users_leaderboard_set("userA", "exrps")
        add_to_users_leaderboard_set("userA", "another_game_id")

    def test_get_users_leaderboard_set(self, stats_tracker_db):
        add_to_users_leaderboard_set("userA", "exrps")
        add_to_users_leaderboard_set("userA", "another_game_id")
        add_to_users_leaderboard_set("userB", "exrps")
        userA_leaderboards = get_users_leaderboard_set("userA")
        userB_leaderboards = get_users_leaderboard_set("userB")
        assert len(userA_leaderboards) == 2
        assert len(userB_leaderboards) == 1

    def test_get_users_leaderboard_set_no_such_user(self, stats_tracker_db):
        userC_leaderboards = get_users_leaderboard_set("userC")
        assert not userC_leaderboards


class TestLeaderboardDefaultHandler:
    def test_default_leaderboard_handler_score_calculation(self):
        handler = LeaderboardHandler()
        assert handler.get_updated_scores("winner", None, "loser", None) == (1, 0)
        assert handler.get_updated_scores("winner", 0, "loser", 0) == (1, 0)
        assert handler.get_updated_scores("winner", 1, "loser", 1) == (2, 1)
        assert handler.get_updated_scores("winner", -1, "loser", 0) == (0, 0)

    def test_register_leaderboard_handler(self):
        # Should be no issues here
        register_leaderboard_handler("product_a", LeaderboardHandler())
        assert get_leaderboard_handler("product_a") is not None

        with pytest.raises(ValueError):  # Invalid handler type
            register_leaderboard_handler("product_b", {})


class TestLeaderboardsApi:
    def test_get_leaderboard(self, stats_tracker_db, test_client):
        response = test_client.get(f"leaderboards/top_ten/exrps")
        assert response.status_code == 200
        assert json.loads(response.data) == []

        record_result("exrps", "userA", "userB")
        response = test_client.get(f"leaderboards/top_ten/exrps")
        assert response.status_code == 200
        assert json.loads(response.data) == [
            {"score": 1.0, "user_id": "userA"},
            {"score": 0.0, "user_id": "userB"},
        ]

    def test_leaderboard_api_delete_user_endpoint(self, test_client):
        """Testing with a non-existing user"""
        response = test_client.post(f"leaderboards/delete_user/some_user_id")
        assert response.status_code == 404
        assert json.loads(response.data) == {
            "status": "user not found",
            "removed_entries": [],
        }


@patch("leaderboards.leaderboards.get_stats_tracker_db")
class TestLeaderboardTransactionErrorWithMocks:
    def test_record_result_transaction_error(self, mocked_tracker_db_function_call):
        # Create a mock for the pipeline that will be used for the transaction
        pipeline_mock = MagicMock()
        pipeline_mock.execute = MagicMock(side_effect=WatchError)

        # Mock out the redis object
        redis_mock = MagicMock()
        redis_mock.pipeline = MagicMock(return_value=pipeline_mock)
        mocked_tracker_db_function_call.return_value = redis_mock

        # Record result should return False because the transaction
        # cannot complete due to forced watch error
        assert record_result("exrps", "userB", "userA") is False

    def test_record_result_transaction_error(self, mocked_tracker_db_function_call):
        # We will use this function to keep track of how many watch errors we have
        # so we can verify that we can tolerate multiple watch errors before eventually
        # succeeding

        # It's a bit ugly - but the alternative is trying to force watch errors which
        # may be even uglier
        self.watch_error_count = 0

        def watch_error_counter():
            self.watch_error_count += 1
            print(f"Watch error count: {self.watch_error_count}")
            if self.watch_error_count > 3:
                return
            else:
                raise WatchError()

        pipeline_mock = MagicMock()
        pipeline_mock.execute = MagicMock(side_effect=watch_error_counter)

        redis_mock = MagicMock()
        redis_mock.pipeline = MagicMock(return_value=pipeline_mock)
        mocked_tracker_db_function_call.return_value = redis_mock

        assert record_result("exrps", "userB", "userA") is True


class TestRemoveUserFromLeaderboards:
    @patch("leaderboards.leaderboards.get_stats_tracker_db")
    def test_remove_user_from_leaderboards_handles_db_error(
        self, mocked_tracker_db_function_call
    ):
        """ Test if: if db stops working, function handles the error"""
        redis_mock = MagicMock()
        redis_mock.smembers = MagicMock(side_effect=RedisError)

        mocked_tracker_db_function_call.return_value = redis_mock
        result = remove_user_from_leaderboards("some_user_id")
        assert result is None

    @patch("leaderboards.leaderboards.get_stats_tracker_db")
    def test_remove_user_from_leaderboards_user_does_not_exist(
        self, mocked_tracker_db_function_call
    ):
        pipeline_mock = MagicMock()
        pipeline_mock.execute = MagicMock()

        redis_mock = MagicMock()
        redis_mock.pipeline = MagicMock(return_value=pipeline_mock)
        redis_mock.smembers = MagicMock(return_value=[])
        mocked_tracker_db_function_call.return_value = redis_mock

        result = remove_user_from_leaderboards("some_user_id")
        assert result == []

    @patch("leaderboards.leaderboards.get_stats_tracker_db")
    def test_remove_user_from_leaderboards_succesfully_removed(
        self, mocked_tracker_db_function_call
    ):
        pipeline_mock = MagicMock()

        pipeline_mock.zrem = MagicMock(return_value=1)
        pipeline_mock.execute = MagicMock()

        redis_mock = MagicMock()
        redis_mock.pipeline = MagicMock(return_value=pipeline_mock)
        redis_mock.smembers = MagicMock(
            return_value=["leaderboard_id", "another_leaderboard_id"]
        )
        mocked_tracker_db_function_call.return_value = redis_mock

        result = remove_user_from_leaderboards("some_user_id")
        pipeline_mock.zrem.assert_has_calls(
            [
                call("leaderboard_id", "some_user_id"),
                call("another_leaderboard_id", "some_user_id"),
            ]
        )
        assert pipeline_mock.zrem.call_count == 2
        assert result == ["leaderboard_id", "another_leaderboard_id"]


class TestDeleteUserApiFunction:
    @patch("leaderboards.api.make_response")
    @patch("leaderboards.api.remove_user_from_leaderboards")
    def test_delete_user_with_error(self, mocked_remove, mocked_make_response):
        mocked_remove.return_value = None
        response = delete_user("some_user_id")
        mocked_remove.assert_called()
        mocked_make_response.assert_called_with('{"status": "error"}', 500)

    @patch("leaderboards.api.make_response")
    @patch("leaderboards.api.remove_user_from_leaderboards")
    def test_delete_user_not_existing_in_leaderboards(
        self, mocked_remove, mocked_make_response
    ):
        mocked_remove.return_value = []
        response = delete_user("some_user_id")
        mocked_remove.assert_called_with("some_user_id")
        mocked_make_response.assert_called_with(
            '{"status": "user not found", "removed_entries": []}', 404
        )

    @patch("leaderboards.api.make_response")
    @patch("leaderboards.api.remove_user_from_leaderboards")
    def test_delete_user_existing_in_leaderboards(
        self, mocked_remove, mocked_make_response
    ):
        mocked_remove.return_value = ["some_id", "other_id"]
        response = delete_user("some_user_id")
        mocked_remove.assert_called_with("some_user_id")
        mocked_make_response.assert_called_with(
            '{"status": "succesfully removed", "removed_entries": ["some_id", "other_id"]}',
            200,
        )
