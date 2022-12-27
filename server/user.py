import json

from flask import request
from time import time
from constants import CONFIG_PATH, USER_JSON_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def userBindNickName():

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    nickName = str(request_data["nickName"])
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
        data = {
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

    if len(nickName) > 16:
        data = {
            "result": 1
        }
        return data
    
    if any(char in nickName for char in '~!@#$%^&*()_+{}|:"<>?[]\;\',./'):
        data = {
            "result": 2
        }
        return data
    
    nick_number = '{:04d}'.format(len(userData.query_nick_name(nickName)) + 1)
    player_data = json.loads(accounts.get_user())
    player_data["status"]["nickName"] = nickName
    player_data["status"]["nickNumber"] = nick_number
    player_data["status"]["uid"] = accounts.get_uid()
    
    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "nickName": nickName
                }
            }
        }
    }
    
    return data


def userRebindNickName():

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    nickName = str(request_data["nickName"])
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
        data = {
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
    player_data["status"]["nickName"] = nickName
    player_data["inventory"]["renamingCard"] -= 1
    
    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "nickName": nickName
                },
                "inventory": {
                    "renamingCard": player_data["inventory"]["renamingCard"]
                }
            }
        }
    }
    
    return data


def userCheckIn(): # TODO: Add CheckIn

    data = request.data
    data = {
        "result": 0,
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data


def userChangeAvatar():
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    avatar_id = str(request_data["id"])
    avatar_type = str(request_data["type"])
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data = {
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
    player_data["status"]["avatar"]["id"] = avatar_id
    player_data["status"]["avatar"]["type"] = avatar_type

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "status": {
                "avatar": player_data["status"]["avatar"]
            }
        }
    }

    return data


def userChangeSecretary():

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data

    charInstId = request_data["charInstId"]
    skinId = request_data["skinId"]

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data = {
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
    player_data["status"]["secretary"] = player_data["troop"]["chars"][str(charInstId)]["charId"]
    player_data["status"]["secretarySkinId"] = skinId

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "secretary": player_data["status"]["secretary"],
                    "secretarySkinId": player_data["status"]["secretarySkinId"]
                }
            }
        }
    }
    
    return data


def userBuyAp():
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
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
        data = {
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
    time_now = round(time())

    player_data["status"]["androidDiamond"] -= 1
    player_data["status"]["iosDiamond"] -= 1
    player_data["status"]["ap"] += player_data["status"]["maxAp"]
    player_data["status"]["lastApAddTime"] = time_now
    player_data["status"]["buyApRemainTimes"] = player_data["status"]["buyApRemainTimes"]

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "androidDiamond": player_data["status"]["androidDiamond"],
                    "iosDiamond": player_data["status"]["iosDiamond"],
                    "ap": player_data["status"]["ap"],
                    "lastApAddTime": player_data["status"]["lastApAddTime"],
                    "buyApRemainTimes": player_data["status"]["buyApRemainTimes"]
                }
            }
        }
    }

    return data