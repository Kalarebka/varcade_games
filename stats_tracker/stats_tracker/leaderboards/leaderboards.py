import logging
from os import removedirs

from typing import Optional

from redis import WatchError, RedisError

from core.db import get_stats_tracker_db
from core.errors import InvalidProductIdError

from .handlers import LeaderboardHandler


_LEADERBOARD_HANDLERS = {}


def register_leaderboard_handler(product_id: str, handler: LeaderboardHandler):
    """Adds a LeaderboardHandler for the given product ID. When game over events
    are received for this product, the registered handler will be run to
    calculated new scores.
    """
    logging.info(
        f"Registering leaderboard handler for product id: {product_id}. Handler: {handler}"
    )
    if product_id in _LEADERBOARD_HANDLERS:
        logging.warning(
            f"Unable to register leaderboard handler for product {product_id}. "
            f"A handler for this product already exists."
        )
        return

    if not isinstance(handler, LeaderboardHandler):
        raise ValueError(
            f"Unable to register stats handler for product {product_id}. "
            f"Handlers must inherit from stats_tracker.handlers.StatsHandler."
        )

    _LEADERBOARD_HANDLERS[product_id] = handler


def get_leaderboard_handler(
    product_id: str, allow_default: bool = True
) -> Optional[LeaderboardHandler]:
    """Get the leaderboard handler for the given product ID. If a specific handler
    doesn't exist for the product the default handler will be returned.

    :param allow_default:  Defaults to True. Set to False to not fall back to the registered default handler.
    """
    if not allow_default:
        return _LEADERBOARD_HANDLERS.get(product_id, None)
    return _LEADERBOARD_HANDLERS.get(product_id, None) or _LEADERBOARD_HANDLERS.get(
        "default", None
    )


def record_result(product_id: str, winner_id: str, loser_id: str) -> bool:
    """
    Save a match result to the leaderboard. This will increment the winners score
    by 1 and decrement the losers score by one.

    """
    logging.debug(
        f"Recording result. Product id: {product_id}. Winner id: {winner_id}, loser_id: {loser_id}"
    )

    leaderboard_handler = get_leaderboard_handler(product_id)
    if leaderboard_handler is None:
        raise InvalidProductIdError(f"Invalid product id: {product_id}")

    pipeline = get_stats_tracker_db().pipeline()
    leaderboard_id = _get_leaderboard_set_id(product_id, "wins")

    # Record the leaderboard id in both user's lists of leaderboards
    for user_id in (winner_id, loser_id):
        add_to_users_leaderboard_set(user_id, leaderboard_id)

    for i in range(10):
        try:
            pipeline.watch(leaderboard_id)
            winner_current_score = pipeline.zscore(leaderboard_id, winner_id)
            loser_current_score = pipeline.zscore(leaderboard_id, loser_id)

            winner_new_score, loser_new_score = leaderboard_handler.get_updated_scores(
                winner_id, winner_current_score, loser_id, loser_current_score
            )

            logging.info(
                f"Recording game result. Product id: {product_id}, winner id: {winner_id}, "
                f"new score: {winner_new_score}, loser id: {loser_id}, new score: {loser_new_score}"
            )
            pipeline.multi()
            pipeline.zadd(
                _get_leaderboard_set_id(product_id, "wins"),
                {winner_id: winner_new_score, loser_id: loser_new_score},
            )
            pipeline.execute()
            return True
        except WatchError:
            logging.warning(f"Watch error writing leaderboard. Attempt: {i}")
    logging.error(f"FAILED TO WRITE LEADERBOARD SCORE DUE TO WATCH ERRORS")
    return False


def get_top_players(product_id: str, count: int = 10) -> list:
    """
    Fetches a list of the top players for the given product ID.

    returns: a list of dicts containing a user ID and a score:

        [
            {
                "user_id": "abc123",
                "score": 100
            },
            {
                "user_id": "123abc",
                "score": 27
            },
            ...
        ]
    """
    logging.debug(f"Fetching the top {count} players for {product_id}")
    if get_leaderboard_handler(product_id) is None:
        raise InvalidProductIdError("Invalid product id specified")

    return [
        {"user_id": s[0].decode("utf-8"), "score": s[1]}
        for s in get_stats_tracker_db().zrevrange(
            _get_leaderboard_set_id(product_id, "wins"), 0, count, "WITHSCORES"
        )
    ]


def get_user_rank(product_id: str, user_id: str) -> int:
    """
    Fetch the rank of the given user for the given game ID

    """
    logging.debug(
        f"Fetching user rank for user id: {user_id}, product id: {product_id}"
    )
    if get_leaderboard_handler(product_id) is None:
        raise InvalidProductIdError("Invalid product id specified")
    return get_stats_tracker_db().zscore(
        _get_leaderboard_set_id(product_id, "wins"), user_id
    )


def _get_leaderboard_set_id(product_id: str, sub_key: str) -> str:
    """Return a key for the leaderboard that represents the given product ID.

    sub_key str:    An additional qualifier for the leaderboard key, eg. wins, losses etc...
    """
    return f"_lb:{sub_key}:{product_id}"


def _get_users_leaderboard_set_id(user_id: str) -> str:
    """Return a key for given user's list of leaderboards he's in."""
    return f"_lb:{user_id}:leaderboard_set"


def add_to_users_leaderboard_set(user_id: str, leaderboard_id: str):
    # Record the leaderboard id in user's lists of leaderboards
    try:
        db = get_stats_tracker_db()
        users_leaderboard_set_id = _get_users_leaderboard_set_id(user_id)
        db.sadd(users_leaderboard_set_id, leaderboard_id)
        logging.info(f"Added leaderboard {leaderboard_id} to user {user_id} record")
    except RedisError as err:
        logging.error(
            f"An error occured while adding leaderboard {leaderboard_id} to user {user_id} record: {err}"
        )


def get_users_leaderboard_set(user_id: str):
    # Get a set of all leaderboards user is in
    users_leaderboard_set_id = _get_users_leaderboard_set_id(user_id)
    return get_stats_tracker_db().smembers(users_leaderboard_set_id)


def delete_users_leaderboard_set(user_id: str):
    # Delete the user's leaderboards set
    users_leaderboard_set_id = _get_users_leaderboard_set_id(user_id)
    return get_stats_tracker_db().delete(users_leaderboard_set_id)


def remove_user_from_leaderboards(user_id: str):
    """Remove user records from all leaderboards he's in.
    Returns None in case of a database error and a list of leaderboards the user
    was removed from otherwise."""
    try:
        leaderboards_ids = get_users_leaderboard_set(user_id)

        if not leaderboards_ids:
            logging.info(f"User {user_id} was not found in any leaderboard")
            return []

        pipeline = get_stats_tracker_db().pipeline()
        removed_from_leaderboards = []
        for leaderboard_id in leaderboards_ids:
            removed = pipeline.zrem(leaderboard_id, user_id)
            if removed:
                logging.info(
                    f"Removed user {user_id} from leaderboard {leaderboard_id}"
                )
                removed_from_leaderboards.append(leaderboard_id)
            else:
                logging.info(
                    f"User {user_id} could not be removed from leaderboard {leaderboard_id}"
                )
        pipeline.execute()

        delete_users_leaderboard_set(user_id)

        return removed_from_leaderboards
    except RedisError as err:
        logging.error(
            f"A redis database error occured while removing user from leaderboards: {err}"
        )
        return None
