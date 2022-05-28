import pytest

from requests.exceptions import RequestException

from rest_framework.test import APIClient

from rest_framework_simplejwt.tokens import RefreshToken

from game_portal.accounts.models import Account


@pytest.fixture(scope="session")
def test_user():
    return Account.objects.create_user("test_user", "test@test.com", "pa88w0rd")


@pytest.fixture(scope="class")
def api_client():
    api_client = APIClient()
    # refresh = RefreshToken.for_user(test_user)
    # api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# Tells pytest for enable test db access for all tests
# Tests can also be decorated individually with `@pytest.mark.django_db`
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


# Mocking requests and api responses
class MockResponse:
    """ Mocking api responses"""

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_requests_post_with_error(*args, **kwargs):
    """Simulating request errors"""
    raise RequestException
