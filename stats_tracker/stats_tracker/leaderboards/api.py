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
    result = remove_user_from_leaderboards(user_id)
    if result is None:
        json_response = json.dumps({"status": "error"})
        logging.info(json_response)
        return make_response(json_response, 500)
    elif result == []:
        json_response = json.dumps({"status": "user not found", "removed_entries": []})
        logging.info(json_response)
        return make_response(json_response, 404)
    else:
        json_response = json.dumps(
            {"status": "succesfully removed", "removed_entries": result}
        )
        logging.info(json_response)
        return make_response(json_response, 200)
