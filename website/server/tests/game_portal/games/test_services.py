import pytest 
import requests
from unittest import mock

from game_portal.games.services import get_leaderboard, get_player_stats_for_game


def mocked_requests_get_with_error(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    raise requests.exceptions.RequestException


class TestServices:
    @mock.patch('requests.get', side_effect=mocked_requests_get_with_error)
    def test_get_leaderboard_handles_request_error(self, mock_get):
        result = get_leaderboard("id")
        assert result is None

    @mock.patch('requests.get', side_effect=mocked_requests_get_with_error)
    def test_get_player_stats_for_game_handles_request_error(self, mock_get):
        result = get_player_stats_for_game("player_id", "game_id")
        assert result is None
        