import json
from flask import Response, request, abort

from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def backgroundSetBackground() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    bgID = request_data["bgID"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(403)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["background"]["selected"] = bgID

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "background": {
                    "selected": bgID
                }
            }
        }
    }
    return data

