import json
import time
from flask import request

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
    
    # TODO: Improve the function
    time_now = round(time.time())
    today_4 = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime(time.time())) + ' 04:00:00', '%Y-%m-%d %H:%M:%S')))
    today_16 = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime(time.time())) + ' 16:00:00', '%Y-%m-%d %H:%M:%S')))
    tomorrow_4 = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime(time.time() + 24 * 60 * 60)) + ' 04:00:00', '%Y-%m-%d %H:%M:%S')))
    player_data = json.loads(accounts.get_user())
    
    if time_now <= today_4:
        player_data["event"]["building"] = today_4
    elif time_now <= today_16:
        player_data["event"]["building"] = today_16
    else:
        player_data["event"]["building"] = tomorrow_4

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "ts": round(time.time()), # TODO: Add userTimeStamps
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "building": player_data["building"],
                "event": player_data["event"]
            }
        }
    }
    return data

#### TODO: Add more functions ####