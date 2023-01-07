import json
from flask import Response, request, abort

from time import time
from constants import CONFIG_PATH, ALLPRODUCT_LIST_PATH
from utils import read_json
from core.Account import Account
from core.database import userData


def userV1getToken() -> Response:
    '''
    result:
        1：服务器目前暂未开放
        2：<自定义消息>error
        3：<将会导致客户端卡死>
        4：认证系统人机校验失败，请重试
    '''
    
    data = request.data
    request_data = request.get_json()

    secret = json.loads(request_data["extension"])["access_token"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "result": 2,
            "error": server_config["server"]["maintenanceMsg"]
        }
        return data
    
    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        data = {
            "result": 2,
            "error": "该用户尚不存在"
        }
        return data
    
    accounts = Account(*result[0])

    if accounts.get_ban() > 1:
        user_status = accounts.get_ban()
        if int(time()) - user_status > 0:
            userData.delete_account(accounts.get_uid())
            data = {
                "result": 2,
                "error": "此账户已注销"
            }
            return data
        else:
            accounts.set_ban(0)
            userData.set_user_status(accounts.get_uid(), accounts.get_ban())
    
    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "error": "",
        "extension": json.dumps({
            "isMinor": False,
            "isAuthenticate": True
        }),
        "channelUid": accounts.get_uid(),
        "token": secret,
        "isGuest": 0
    }

    return data


def userVerifyAccount() -> Response:
    '''
    result:
        1：服务器目前暂未开放
        2：<自定义消息>error
    '''
    
    data = request.data
    request_data = request.get_json()
    
    secret = json.loads(request_data["extension"])["access_token"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "result": 2,
            "error": server_config["server"]["maintenanceMsg"]
        }
        return data
    
    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        data = {
            "result": 2,
            "error": "该用户尚不存在"
        }
        return data
    
    accounts = Account(*result[0])

    if accounts.get_ban() > 1:
        user_status = accounts.get_ban()
        if int(time()) - user_status > 0:
            userData.delete_account(accounts.get_uid())
            data = {
                "result": 2,
                "error": "此账户已注销"
            }
            return data
        else:
            accounts.set_ban(0)
            userData.set_user_status(accounts.get_uid(), accounts.get_ban())
    
    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "error": "",
        "extension": json.dumps({
            "isGuest": False
        }),
        "channelUid": accounts.get_uid(),
        "token": secret,
        "isGuest": 0
    }

    return data


def payGetAllProductList() -> Response:
    
    data = request.data
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    productList = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')["productList"]
    
    data = {
        "productList": productList
    }

    return data
    

def payConfirmOrderState() -> Response:
    
    data = request.data
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    data = {
        "payState": 3
    }
    
    return data