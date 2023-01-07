import json
import random
from flask import Response, request, abort

from time import time
from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account


def userBindNickName() -> Response:
    '''
    result:
        1：昵称长度超过限制
        2：昵称中不允许使用特殊符号。请使用汉字、英文字母或数字
        3：这个昵称不允许被使用
        4：嗯...不好意思，能再说一遍吗？
    '''

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    nickName = str(request_data["nickName"])
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])

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

    if nickName.casefold() in ["admin", "ban", "banned", "forbidden", "root"]:
        data = {
            "result": 3
        }
        return data

    if "doctoratepy" in nickName.casefold():
        data = {
            "result": 4
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


def userUseRenameCard() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    itemId = request_data["itemId"]
    instId = str(request_data["instId"])
    nickName = str(request_data["nickName"])
    nickNumber = '{:04d}'.format(random.randint(1, 9999))
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["status"]["nickName"] = nickName
    player_data["status"]["nickNumber"] = nickNumber
    renamingCard = player_data["consumable"][itemId][instId]
    renamingCard["count"] -= 1
    
    userData.set_user_data(accounts.get_uid(), player_data)
        
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "nickName": nickName,
                    "nickNumber": nickNumber
                },
                "consumable": {
                    itemId: player_data["consumable"][itemId]
                }
            }
        }
    }

    return data


def userChangeResume() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    resume = str(request_data["resume"])
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["status"]["resume"] = resume

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "resume": player_data["status"]["resume"]
                }
            }
        }
    }

    return data


def userCheckIn() -> Response: # TODO: Add CheckIn

    data = request.data
    data = {
        "result": 0,
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data


def userChangeAvatar() -> Response:
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    avatar_id = str(request_data["id"])
    avatar_type = str(request_data["type"])
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["status"]["avatar"]["id"] = avatar_id
    player_data["status"]["avatar"]["type"] = avatar_type

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "avatar": player_data["status"]["avatar"]
                }
            }
        }
    }

    return data


def userChangeSecretary() -> Response:

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    charInstId = request_data["charInstId"]
    skinId = request_data["skinId"]

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
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


def userExchangeDiamondShard() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    count = request_data["count"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    
    if player_data["status"]["androidDiamond"] < count:
        data = {
            "result": 1,
            "errMsg": "至纯源石不足，是否前往商店购买至纯源石？"
        }
        return data
    
    player_data["status"]["androidDiamond"] -= count
    player_data["status"]["iosDiamond"] -= count
    player_data["status"]["diamondShard"] += count * 180

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": {
                    "androidDiamond": player_data["status"]["androidDiamond"],
                    "iosDiamond": player_data["status"]["iosDiamond"],
                    "diamondShard": player_data["status"]["diamondShard"]
                }
            }
        }
    }

    return data


def userBuyAp() -> Response:
    
    data = request.data
    
    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    time_now = int(time())
    addAp = int((time_now - int(player_data["status"]["lastApAddTime"])) / 360)
    
    if player_data["status"]["ap"] < player_data["status"]["maxAp"]:
        if (player_data["status"]["ap"] + addAp) >= player_data["status"]["maxAp"]:
            player_data["status"]["ap"] = player_data["status"]["maxAp"]
            player_data["status"]["lastApAddTime"] = time_now
        else:
            if addAp != 0:
                player_data["status"]["ap"] += addAp
                player_data["status"]["lastApAddTime"] = time_now

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