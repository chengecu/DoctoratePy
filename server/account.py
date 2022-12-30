import json
from flask import request

from time import time
from core.function.update import updateData
from constants import CONFIG_PATH, CHARACTER_TABLE_URL, CHARWORD_TABLE_URL, \
    EQUIP_TABLE_URL, GACHA_TABLE_URL, SYNC_DATA_TEMPLATE_PATH, ITEM_TABLE_URL, \
    STAGE_TABLE_URL, MEDAL_TABLE_URL, BUILDING_DATA_URL
from utils import read_json
from core.database import userData
from core.Account import Account


def accountLogin():

    data = request.data
    request_data = request.get_json()
    
    secret = str(request_data["token"])
    clientVersion = str(request_data["clientVersion"])

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
        syncData["status"]["registerTs"] = int(time())
        syncData["status"]["lastApAddTime"] = int(time())
        
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

    ts = int(time()) # TODO: Add userTimeStamps
    player_data = json.loads(accounts.get_user())
    
    player_data["status"]["lastOnlineTs"] = int(time())
    player_data["status"]["lastRefreshTs"] = ts # TODO: Add userTimeStamps

    userData.set_user_data(accounts.get_uid(), player_data)
    
    updateData(CHARACTER_TABLE_URL)
    updateData(CHARWORD_TABLE_URL)
    updateData(EQUIP_TABLE_URL)
    updateData(GACHA_TABLE_URL)
    updateData(ITEM_TABLE_URL)
    updateData(STAGE_TABLE_URL)
    updateData(MEDAL_TABLE_URL)
    updateData(BUILDING_DATA_URL)

    data = {
        "result": 0,
        "user": player_data,
        "ts": ts # TODO: Add userTimeStamps
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
    player_data["status"]["lastOnlineTs"] = int(time())
    player_data["status"]["lastRefreshTs"] = int(time()) # TODO: Add userTimeStamps
    player_data["pushFlags"]["hasGifts"] = 0
    player_data["pushFlags"]["hasFriendRequest"] = 0

    mailbox_list = json.loads(accounts.get_mails()) # TODO: Move mail system to mysql

    friend_request = json.loads(accounts.get_friend())["request"]
    
    if len(friend_request) != 0:
        player_data["pushFlags"]["hasFriendRequest"] = 1

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "ts": int(time()), # TODO: Add userTimeStamps
        "result": {}, # TODO: Research the data that needs to be filled here
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

