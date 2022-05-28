from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from rest_framework import status

from requests.exceptions import RequestException
from unittest import mock

from conftest import mocked_requests_post_with_error, MockResponse
from game_portal.accounts.models import Account, AccountType
from game_portal.accounts.signals import delete_user_from_leaderboards


class TestAccounts:
    def setup_method(self):
        self.test_user = Account.objects.create_user(
            "test_user", "test@test.com", "pa88w0rd"
        )
        self.create_url = reverse("register")

    def test_create_user(self, api_client):
        """
        Ensure we can create a new user and a valid token is created with it.
        """
        data = {
            "username": "userA",
            "email": "userA@test.com",
            "password": "validPassword",
        }

        response = api_client.post(self.create_url, data, format="json")

        assert Account.objects.count() == 2
        assert response.status_code == status.HTTP_201_CREATED

        user = response.data.get("user")
        assert user is not None
        assert user["username"] == data["username"]
        assert user["id"] is not None
        assert user["account_type"] == AccountType.PLAYER
        assert "password" not in user
        assert "access" in response.data
        assert "refresh" in response.data

    def test_create_user_with_short_password(self, api_client):
        """
        Ensure user is not created for password lengths less than 8.
        """
        data = {
            "username": "foobar",
            "email": "foobarbaz@example.com",
            "password": "foo",
        }

        response = api_client.post(self.create_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Account.objects.count() == 1
        assert len(response.data["password"]) == 1

    def test_create_user_with_no_password(self, api_client):
        data = {"username": "foobar", "email": "foobarbaz@example.com", "password": ""}

        response = api_client.post(self.create_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Account.objects.count() == 1
        assert len(response.data["password"]) == 1


class TestDeleteUserFromLeaderboardsSignal:
    def setup_method(self):
        self.test_user = Account.objects.create_user(
            "test_user", "test@test.com", "pa88w0rd"
        )

    @mock.patch("requests.post")
    def test_deleting_account_triggers_delete_from_leaderboard_signal(self, mock_post):
        """ Ensure deleting the user triggers signal and calls it only once """
        self.test_user.delete()
        mock_post.assert_called_once()

    @mock.patch("requests.post", side_effect=mocked_requests_post_with_error)
    def test_delete_user_from_leaderboards_handles_stats_server_error(self, mock_post):
        result = delete_user_from_leaderboards(Account, self.test_user)
        """ The function returns None when there is no error"""
        assert result is None

    @mock.patch("requests.post")
    def test_delete_user_from_leaderboards_success(self, mock_post):
        mock_post.return_value = MockResponse('{"success": True}', 200)
        result = delete_user_from_leaderboards(Account, self.test_user)
        assert result is None

    @mock.patch("requests.post")
    def test_delete_user_from_leaderboards_failure(self, mock_post):
        mock_post.return_value = MockResponse('{"error": "some error message"}', 500)
        result = delete_user_from_leaderboards(Account, self.test_user)
        assert result is None
