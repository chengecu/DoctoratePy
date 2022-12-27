import json
from flask import request

from constants import CONFIG_PATH
from utils import read_json
from core.Account import Account
from core.database import userData


def userV1getToken():
    
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
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    
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


def payGetAllProductList():
    
    data = request.data
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    data = {
        "productList": [] # TODO: Add productList
    }

    return data
    

def payConfirmOrderState():
    
    data = request.data
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    data = {
        "payState": 3
    }
    
    return data