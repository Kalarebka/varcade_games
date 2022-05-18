from django.conf import settings

import requests
import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from requests.exceptions import RequestException

from .models import Account

@receiver(post_delete, sender=Account)
def delete_user_from_leaderboards(sender, instance, **kwargs) -> None:
    user_id = instance.id
    logging.info(f"Sending request to delete user {user_id} from leaderboards")
    try:
        response = requests.post(
            f"{settings.STATS_TRACKER_CONFIG['url']}/"
            f"leaderboards/delete_user/{user_id}"
        )
        if response.status_code == 200:
            logging.info(f"User {user_id} deleted from leaderboards.")
    except RequestException as err:
        logging.error(f"Could not access leaderboard server: {err}")
    return None