import json
from flask import request

from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def storyreviewReadStory():
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    storyId = request_data["storyId"]
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
    storyGroups = player_data["storyreview"]["groups"]
    groupId = storyId.split('_')[0]
    readCount = 1

    if "min" in groupId and "mini" not in groupId:
        groupId += "i"
    
    if len(storyGroups[groupId]["stories"]) != 0:
        for story in storyGroups[groupId]["stories"]:
            if story["id"] == storyId:
                story["rc"] += 1
                readCount = story["rc"]
                break

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "storyreview": {
                    "groups": {
                        groupId: storyGroups[groupId]
                    }
                }
            }
        },
        "readCount": readCount
    }

    return data


def storyreviewMarkStoryAcceKnown():
    
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
    player_data["storyreview"]["tags"]["knownStoryAcceleration"] = 1

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "storyreview":  player_data["storyreview"]
            }
        }
    }

    return data