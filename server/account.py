import json

from time import time
from flask import request
from constants import CONFIG_PATH, SYNC_DATA_TEMPLATE_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def accountLogin():

    data = request.data
    body = request.json
    
    secret = str(body["token"])
    clientVersion = str(body["clientVersion"])

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data = {
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    server_config = read_json(CONFIG_PATH)
    
    if accounts.get_ban() == 1:
        data = {
            "result": 1,
            "error": "您的账户已被服务器封禁"
        }
        return data

    if clientVersion != server_config["version"]["android"]["clientVersion"]:
        data = {
            "result": 2,
            "error": "客户端版本已过时，请更新客户端"
        }
        return data

    if accounts.get_user() == "{}":
        syncData = read_json(SYNC_DATA_TEMPLATE_PATH, encoding='utf8')
        syncData["status"]["registerTs"] = round(time())
        syncData["status"]["lastApAddTime"] = round(time())
        
        userData.set_user_data(accounts.get_uid(), syncData)
    
    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "secret": secret,
        "serviceLicenseVersion": 0
    }

    return data


def accountSyncData():

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

    ts = round(time()) # TODO
    player_data = json.loads(accounts.get_user())
    
    player_data["status"]["lastOnlineTs"] = round(time())
    player_data["status"]["lastRefreshTs"] = ts # TODO

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "user": player_data,
        "ts": ts # TODO
    }
    
    return data
    

def accountSyncStatus():
    
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
    player_data["status"]["lastOnlineTs"] = round(time())
    player_data["status"]["lastRefreshTs"] = round(time()) # TODO
    player_data["pushFlags"]["hasGifts"] = 0
    player_data["pushFlags"]["hasFriendRequest"] = 0

    mailbox_list = json.loads(accounts.get_mails()) # TODO

    friend_request = json.loads(accounts.get_friend())["request"]
    
    if len(friend_request) != 0:
        player_data["pushFlags"]["hasFriendRequest"] = 1

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "ts": round(time()),
        "result": {
            "4": {
                "announcementVersion": "1195",
			    "announcementPopUpVersion": "1090"
            }
        },
        "playerDataDelta": {
            "modified": {
                "status": player_data["status"],
                "gacha": player_data["gacha"],
                "inventory": player_data["inventory"],
                "pushFlags": player_data["pushFlags"],
                "consumable": player_data["consumable"],
                "rlv2": player_data["rlv2"]
            },
            "deleted": {}
        }
    }

    return data

