import hashlib

from flask import request
from core.database import userData
from core.Account import Account

user_key = "IxMMveJRWsxStJgX"


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
        "message": "Forbid visitors to log in."
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

    data = {
        "result": 4
    }
    return data


def userRegister():
    
    data = request.data
    body = request.json
    
    account = str(body["account"])
    password = str(body["password"])
    smsCode = str(body["smsCode"]) # TODO

    secret = hashlib.md5((account + user_key).encode()).hexdigest()
    
    if len(userData.query_account_by_phone(account)) != 0:
        data = {
            "result": 5,
            "errMsg": "Account already exists."
        }
        return data
    
    if userData.register_account(account, hashlib.md5((password + user_key).encode()).hexdigest(), secret) != 1:
        data = {
            "result": 5,
            "errMsg": "Registration failed, unknown error."
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
            "result": 2,
        }
        return data
    
    result = userData.login_account(account, hashlib.md5((password + user_key).encode()).hexdigest())

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
    
    accounts = userData.query_account_by_secret(secret)
    
    if len(accounts) != 1:
        data = {
            "result": 2,
            "error": "Unable to query this account."
        }
        return data
    
    for item in accounts:
        uid = item.uid
        
    data = {
        "uid": uid,
        "isMinor": False,
        "isAuthenticate": True,
        "isGuest": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }
    
    return data