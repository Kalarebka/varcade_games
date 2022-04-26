from django.conf import settings

import requests
import logging

from requests.exceptions import RequestException


def get_leaderboard(product_id):
    logging.info(f"Requesting top ten for product: {product_id}")
    try:
        response = requests.get(
        f"{settings.STATS_TRACKER_CONFIG['url']}/" f"leaderboards/top_ten/{product_id}"
        )
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.error(f"Could not access leaderboard server: {err}")
        return None  


def get_player_stats_for_game(product_id, user_id):
    logging.info(f"Requesting stats for user: {user_id}, product: {product_id}")
    try:
        response = requests.get(
        f"{settings.STATS_TRACKER_CONFIG['url']}/" f"stats/{product_id}/{user_id}"
        )
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.error(f"Could not access stats server: {err}")
        return None
