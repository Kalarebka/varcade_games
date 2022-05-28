import json

import logging

from werkzeug.local import LocalProxy

from flask import Blueprint, make_response, current_app

from leaderboards.leaderboards import get_top_players, remove_user_from_leaderboards


leaderboards_blueprint = Blueprint("leaderboards", __name__)


@leaderboards_blueprint.route("/top_ten/<product_id>")
def get_leaderboard(product_id: str):
    logging.info(f"Fetching leaderboard for product: {product_id}")
    return make_response(json.dumps(get_top_players(product_id)), 200)


@leaderboards_blueprint.route("/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id: str):
    """ Deletes a user from all leaderboards."""
    logging.info(f"Removing user {user_id} from all leaderboards.")
    result = remove_user_from_leaderboards(user_id)

    if result is None:
        json_response = json.dumps({"status": "error"})
        return make_response(json_response, 500)

    if not result:
        json_response = json.dumps({"status": "user not found", "removed_entries": []})
        return make_response(json_response, 404)

    json_response = json.dumps(
        {"status": "succesfully removed", "removed_entries": result}
    )
    return make_response(json_response, 200)
