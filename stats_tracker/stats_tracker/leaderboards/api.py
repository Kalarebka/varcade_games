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

# Route to delete a user from all leaderboards
@leaderboards_blueprint.route("/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id: str):
    logging.info(f"Removing user {user_id} from all leaderboards.")
    try:
        remove_user_from_leaderboards(user_id)
        return make_response(json.dumps('"success": True'), 200)
    except Exception as e:
        # TODO indentify what exception can happen here
        return make_response(json.dumps(e), 500)


