import re
import json
from flask import Response, request, abort

from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def storyFinishStory() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    storyId = request_data["storyId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["status"]["flags"][storyId] = 1
    
    # TODO
    #if "obt" in storyId and not re.match(r"obt/.*main_0[9]|obt/.*main_[1-9][0-9]", storyId):
        #player_data["status"]["progress"] += 200

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "items": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "flags": player_data["status"]["flags"],
                    #"progress": player_data["status"]["progress"]
                }
            }
        }
    }

    return data

