import json
from flask import Response, request, abort

from time import time
from core.function.update import updateData
from constants import CONFIG_PATH, CHARACTER_TABLE_URL, CHARWORD_TABLE_URL, \
    EQUIP_TABLE_URL, GACHA_TABLE_URL, SYNC_DATA_TEMPLATE_PATH, ITEM_TABLE_URL, \
    STAGE_TABLE_URL, MEDAL_TABLE_URL, BUILDING_DATA_URL, RL_TABLE_URL, SKIN_TABLE_URL, \
    GAMEDATA_CONST_URL
from utils import read_json
from core.database import userData
from core.Account import Account


def accountLogin() -> Response:
    '''
    result:
        1：此账号禁止登入游戏，详情请咨询客服
        2：当前客户端版本已过时，将检测最新客户端
        3：记忆已经模糊，清重新输入登录信息
        4：数据文件已过期，请重新登录
        5：网络配置已过期，请重新登录
        6：账号时间信息失去同步，请确认账号信息后重试
    '''

    data = request.data
    request_data = request.get_json()

    secret = request_data["token"]
    clientVersion = request_data["clientVersion"]
    networkVersion = str(request_data["networkVersion"])

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data = {
            "result": 3
        }
        return data
    
    accounts = Account(*result[0])
    server_config = read_json(CONFIG_PATH)
    
    if accounts.get_ban() == 1:
        data = {
            "result": 1
        }
        return data

    if clientVersion != server_config["version"]["android"]["clientVersion"]:
        data = {
            "result": 2
        }
        return data
    
    if networkVersion != server_config["networkConfig"]["content"]["configVer"]:
        data = {
            "result": 5
        }
        return data
    
    try:
        if accounts.get_user() != "{}":
            player_data = json.loads(accounts.get_user())
            registerTs = player_data["status"]["registerTs"]

            if int(time()) < registerTs:
                data = {
                    "result": 6
                }
                return data
    except:
        data = {
            "result": 4
        }
        return data

    if accounts.get_user() == "{}":
        ts = int(time())
        syncData = read_json(SYNC_DATA_TEMPLATE_PATH, encoding='utf8')
        syncData["status"]["registerTs"] = ts
        syncData["status"]["lastApAddTime"] = ts
        
        userData.set_user_data(accounts.get_uid(), syncData)

    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "secret": secret,
        "serviceLicenseVersion": 0
    }

    return data


def accountSyncData() -> Response:
    '''
    result:
        1：账号时间信息失去同步，请确认账号信息后重试
    '''

    data = request.data
    
    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    ts = int(time()) # TODO: Add userTimeStamps
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    
    player_data["status"]["lastOnlineTs"] = int(time())
    player_data["status"]["lastRefreshTs"] = ts # TODO: Add userTimeStamps

    userData.set_user_data(accounts.get_uid(), player_data)
    
    updateData(CHARACTER_TABLE_URL)
    updateData(CHARWORD_TABLE_URL)
    updateData(EQUIP_TABLE_URL)
    updateData(RL_TABLE_URL)
    updateData(GACHA_TABLE_URL)
    updateData(ITEM_TABLE_URL)
    updateData(STAGE_TABLE_URL)
    updateData(MEDAL_TABLE_URL)
    updateData(SKIN_TABLE_URL)
    updateData(GAMEDATA_CONST_URL)
    updateData(BUILDING_DATA_URL)

    data = {
        "result": 0,
        "ts": ts, # TODO: Add userTimeStamps
        "user": player_data
    }
    
    return data
    

def accountSyncStatus() -> Response:
    
    data = request.data

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    ts = int(time()) # TODO: Add userTimeStamps
    accounts = Account(*result[0])
    
    player_data = json.loads(accounts.get_user())
    player_data["status"]["lastOnlineTs"] = int(time())
    player_data["status"]["lastRefreshTs"] = ts
    player_data["pushFlags"]["hasGifts"] = 0
    player_data["pushFlags"]["hasFriendRequest"] = 0
    
    consumable = player_data["consumable"]

    for index in list(consumable.keys()):
        for item in list(consumable[index].keys()):
            tmp = consumable[index][item]
            if tmp["ts"] != -1:
                if tmp["ts"] <= int(time()) or tmp["count"] == 0:
                    del consumable[index][item]

    mailbox_list = json.loads(accounts.get_mails())

    for index in range(len(mailbox_list)):
        if mailbox_list[index]["state"] == 0:
            if int(time()) <= mailbox_list[index]["expireAt"]:
                player_data["pushFlags"]["hasGifts"] = 1
                break
            else:
                mailbox_list[index]["remove"] = 1
                
    friend_data = json.loads(accounts.get_friend())
    friend_request = friend_data["request"]
    
    for friend in friend_request:
        result = userData.query_account_by_uid(friend["uid"])
        if len(result) == 0:
            friend_request.remove(friend)
    
    userData.set_friend_data(accounts.get_uid(), friend_data)
            
    if len(friend_request) != 0:
        player_data["pushFlags"]["hasFriendRequest"] = 1
        
    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "ts": ts, 
        "result": {
            "4": {
                "announcementVersion": "1061",
                "announcementPopUpVersion": "1937"
            }
        }, # TODO: Research the data that needs to be filled here
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