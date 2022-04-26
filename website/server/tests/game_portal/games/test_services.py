import json
import pytest


from requests.exceptions import RequestException
from unittest import mock

from game_portal.games.services import get_leaderboard, get_player_stats_for_game


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def mocked_requests_get_with_error(*args, **kwargs):
    raise RequestException


class TestServices:
    @mock.patch('requests.get', side_effect=mocked_requests_get_with_error)
    def test_get_leaderboard_handles_request_error(self, mock_get):
        result = get_leaderboard("id")
        assert result is None

    @mock.patch('requests.get')
    def test_get_leaderboard_handles_request_success(self, mock_get):
        mock_get.return_value = MockResponse('[{"user_id": "abc123", "score": 100}, {"user_id": "123abc","score": 27}]', 200)
        result = json.loads(get_leaderboard("id"))
        assert result is not None
        assert "user_id" in result[0]
        assert "score" in result[0]


    @mock.patch('requests.get', side_effect=mocked_requests_get_with_error)
    def test_get_player_stats_for_game_handles_request_error(self, mock_get):
        result = get_player_stats_for_game("player_id", "game_id")
        assert result is None

    @mock.patch('requests.get')
    def test_get_player_stats_for_game_handles_request_success(self, mock_get):
        mock_get.return_value = MockResponse('{"stat1": 1, "stat2": 20}', 200)
        result = json.loads(get_player_stats_for_game("player_id", "game_id"))
        assert result is not None
        assert 'stat1' in result
        assert 'stat2' in result



       