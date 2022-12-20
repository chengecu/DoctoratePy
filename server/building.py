import json
from flask import request

from time import time
from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def buildingSync():

    data = request.data
    
    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])

    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())
    
    data = {
        "ts": round(time()),
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "building": player_data["building"],
                "event": player_data["event"]
            }
        }
    }
    return data

#### TODO ####