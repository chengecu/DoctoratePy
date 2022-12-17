import hashlib
from unittest import result

from flask import request
from utils import read_json
from constants import CONFIG_PATH
from core.database import userData
from core.Account import Account
from core.function.captcha import sentSmsCode, verifySmsCode

LOG_TOKEN_KEY = "IxMMveJRWsxStJgX"


def userV1NeedCloudAuth():

    data = request.data
    data = {
        "status": 0,
        "msg": "OK"
    }

    return data


def userOAuth2V1Grant():

    data = request.data
    data = {
        "result": 0,
    }

    return data


def userV1GuestLogin():

    data = request.data
    data = {
        "result": 6,
        "message": "禁止游客登录"
    }

    return data


def userAuthenticateUserIdentity():

    data = request.data
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userUpdateAgreement():

    data = request.data
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userCheckIdCard():

    data = request.data
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userSendSmsCode():

    data = request.data
    body = request.json

    server_config = read_json(CONFIG_PATH)
    account = body["account"]

    if not server_config["server"]["enableCaptcha"]:
        data = {
            "result": 4
        }
        return data
    
    else:
        if account:
            sentSmsCode()
            data = {
                "result": 0
            }
            return data


def userRegister():
    
    data = request.data
    body = request.json
    
    account = str(body["account"])
    password = str(body["password"])
    smsCode = str(body["smsCode"])

    secret = hashlib.md5((account + LOG_TOKEN_KEY).encode()).hexdigest()
    
    if len(userData.query_account_by_phone(account)) != 0:
        data = {
            "result": 5,
            "errMsg": "该账户已存在，请检查注册信息"
        }
        return data
    
    server_config = read_json(CONFIG_PATH)
    
    if server_config["server"]["enableCaptcha"]:
        if not verifySmsCode(smsCode):
            data = {
                "result": 5,
                "errMsg": "验证码错误"
            }
            return data
    
    if userData.register_account(account, hashlib.md5((password + LOG_TOKEN_KEY).encode()).hexdigest(), secret) != 1:
        data = {
            "result": 5,
            "errMsg": "注册失败，未知错误"
        }
        return data
    
    data = {
        "result": 0,
        "uid": 0,
        "token": secret,
        "isAuthenticate": True,
        "isMinor": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }
    
    return data


def userLogin():
    
    data = request.data
    body = request.json

    account = str(body["account"])
    password = str(body["password"])

    if len(userData.query_account_by_phone(account)) == 0:
        data = {
            "result": 1,
        }
        return data
    
    result = userData.login_account(account, hashlib.md5((password + LOG_TOKEN_KEY).encode()).hexdigest())

    if len(result) != 1:
        data = {
            "result": 1,
        }
        return data

    accounts = Account(*result[0])
    
    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "token": accounts.get_secret(),
        "isAuthenticate": True,
        "isMinor": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }

    return data


def userLoginBySmsCode():
    
    data = request.data
    body = request.json

    account = str(body["account"])
    smsCode = str(body["smsCode"])

    if len(userData.query_account_by_phone(account)) == 0:
        data = {
            "result": 1,
        }
        return data
    
    if not verifySmsCode(smsCode):
        data = {
            "result": 5
        }
        return data
    
    result = userData.login_account(account, hashlib.md5((account + LOG_TOKEN_KEY).encode()).hexdigest())

    if len(result) != 1:
        data = {
            "result": 1,
        }
        return data

    accounts = Account(*result[0])

    data = {
        "result": 0,
        "uid": accounts.get_uid(),
        "token": accounts.get_secret(),
        "isAuthenticate": True,
        "isMinor": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }

    return data


def userAuth():

    data = request.data
    body = request.json

    secret = str(body["token"])
    
    if secret is None or len(secret) < 0:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Missing token"
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
        "uid": accounts.get_uid(),
        "isMinor": False,
        "isAuthenticate": True,
        "isGuest": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }
    
    return data