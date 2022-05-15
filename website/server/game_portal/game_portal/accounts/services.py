from django.conf import settings

import requests
import logging

from requests.exceptions import RequestException


def delete_user_leaderboards(user_id: str):
    logging.info(f"Sending request to delete user {user_id} from leaderboards")
    try:
        response = requests.get(
            f"{settings.STATS_TRACKER_CONFIG['url']}/"
            f"leaderboards/delete_user/{user_id}"
        )
        return response.json()
    except RequestException as err:
        logging.error(f"Could not access leaderboard server: {err}")
        return None