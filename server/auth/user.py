import re
import json
import socket
import random
import hashlib
from flask import Response, request, abort

from time import time, strftime, sleep
from datetime import datetime
from constants import CONFIG_PATH
from utils import read_json
from core.database import userData
from core.Account import Account
from utils import encrypt_code_data, decrypt_user_key
from core.function.captcha import sentSmsCode, verifySmsCode

USER_TOKEN_KEY = "7318def77669979d"


def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def userV1NeedCloudAuth() -> Response:

    data = request.data
    data = {
        "status": 0,
        "msg": "OK"
    }

    return data


def userOAuth2V1Grant() -> Response:
    '''
    status:
        1：获取用户授权信息失败，请重试 - 错误号:0
        2：<自定义消息>msg
    '''
    data = request.data
    request_data = request.get_json()
    
    appCode = request_data["appCode"]
    token = request_data["token"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "status": 2,
            "msg": server_config["server"]["maintenanceMsg"]
        }
        return data
    
    result = userData.query_account_by_secret(token)
    
    if len(result) != 1:
        data = {
            "status": 2,
            "msg": "该用户尚不存在，请先注册"
        }
        return data
    
    code_data = encrypt_code_data(appCode, token, int(time()))

    data = {
        "data": {
            "code": code_data,
            "uid": ''.join(str(random.randint(0, 9)) for _ in range(12)) # TODO: Add track server UID
        },
        "status": 0,
        "msg": "OK"
    }

    return data


def userOauth2V1UnbindGrant() -> Response:
    '''
    status:
        1：注销游戏账户失败 - 错误号:0
        2：<自定义消息>msg
        4：人机校验失败，请重试
        5：手机验证码不正确，请重试
    '''

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    phoneCode = request_data["phoneCode"]
    token = request_data["token"]

    if token != secret:
        data = {
            "status": 4
        }
        return data
    
    if verifySmsCode(phoneCode) is None:
        data = {
            "status": 2,
            "msg": "验证码已过期，请重新获取"
        }
        return data

    if not verifySmsCode(phoneCode):
        data = {
            "status": 5
        }
        return data

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "status": 2,
            "msg": "该用户尚不存在"
        }
        return data
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    
    time_now = int(time())
    accounts.set_ban(time_now + 60 * 5)
    player_data["status"]["lastOnlineTs"] = time_now
    
    userData.set_user_data(accounts.get_uid(), player_data)
    userData.set_user_status(accounts.get_uid(), accounts.get_ban())
    
    data = {
        "status": 0,
        "msg": "OK"
    }
    
    return data


def userV1GuestLogin() -> Response:
    '''
    result:
        1：用户名或密码错误，请重新登录
        2：此账号未申请IOS平台测试资格，如有疑问请联系客服
        3：此账号尚未激活，如有疑问请联系客服
        7：认证系统人机校验失败，请重试
        8：网络异常，登录失败，请稍后重试 - 错误号0
    '''

    data = request.data
    
    if request.user_agent.platform == "iphone":
        data = {
            "result": 2
        }
        return data
    
    data = {
        "result": 3
    }

    return data


def userAuthenticateUserIdentity() -> Response:
    '''
    result:
        1：证件信息填写有误，请检查后重试
        2：网络异常，实名认证失败，请稍后重试 - 错误号2
        3：<自定义消息>message
    '''
    data = request.data
    request_data = request.get_json()

    name = request_data["name"]
    
    if name != "DoctoratePy":
        data = {
            "result": 1
        }
        return data
    
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userUpdateAgreement() -> Response:

    data = request.data
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userCheckIdCard() -> Response:
    '''
    result:
        1：证件信息填写有误，请检查后重试
        2：<自定义消息>message
    '''

    data = request.data
    request_data = request.get_json()

    idCardNum = request_data["idCardNum"]

    if re.match(r"^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$", idCardNum):
        check_sum = 0
        check_sum = sum(((1 << (17 - index)) % 11) * int(idCardNum[index]) for index in range(0, 17))
        check_digit = (12 - (check_sum % 11)) % 11
        check_digit = check_digit if check_digit < 10 else 'X'
    
    if str(check_digit) != idCardNum[-1]:
        data = {
            "result": 1
        }
        return data
    
    data = {
        "result": 0,
        "message": "OK",
        "isMinor": False
    }

    return data


def userInfoV1SendPhoneCode() -> Response:
    '''
    status:
        1：验证码发送服务失败 - 错误号:0
        2：<自定义消息>msg
        4：人机校验失败，请重试
        5：手机验证码不正确，请重试
    '''
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    type = request_data["type"]
    token = request_data["token"]

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "status": 2,
            "msg": "该用户尚不存在"
        }
        return data
    
    if token != "":
        sentSmsCode(type)
        data = {
            "status": 0,
            "msg": "OK"
        }
        return data
    
    data = {
        "status": 1
    }

    return data


def userSendSmsCode() -> Response:
    '''
    result:
        1：请求验证码过于频繁，请稍后
        2：验证码平台正忙，发送失败，请稍后重试
        5：发送验证码时遇到未知错误，请稍后重试
        7：认证系统人机校验失败，请重试
        8：网络异常，验证码发送失败，请稍后重试。 - 错误号:0
    '''

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    account = request_data["account"]
    type = request_data["type"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "result": 8
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if type != 0 and len(result) != 1:
        data ={
            "result": 7
        }
        return data
    
    if account:
        status = sentSmsCode(type)
        data = {
            "result": status
        }
        if status == 0:
            data["msg"] = "OK"
        return data
    
    data = {
        "result": 5
    }

    return data


def userRegister() -> Response:
    '''
    result:
        4：验证码错误或已失效，请重新输入
        5：<自定义消息>errMsg
        8：<需要人机验证>message & captcha
    '''
    
    data = request.data
    request_data = request.get_json()

    sign = request_data["sign"]
    account = request_data["account"]
    captcha = request_data["captcha"]
    password = request_data["password"]
    smsCode = request_data["smsCode"]

    secret = hashlib.md5((account + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest()
    user_gt = hashlib.md5((str(int(time())) + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest()
    challenge = hashlib.md5(sign.encode()).hexdigest()
    pattern = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,16}$')

    if not pattern.match(password):
        data = {
            "result": 5,
            "errMsg": "<color=red>密码格式错误</color>\n密码应为8-16位大小写字母和数字的组合\n其中可以选择包含一些常用字符"
        }
        return data
    
    if len(userData.query_account_by_phone(account)) != 0:
        data = {
            "result": 5,
            "errMsg": "该账户已存在，请检查注册信息"
        }
        return data

    if captcha == "" and not verifySmsCode(smsCode):
        data = {
            "result": 4
        }
        return data

    weights = {
        1: 7, 2: 9, 3: 10, 4: 5, 5: 8, 6: 4, 7: 2, 8: 1, 9: 6,
        10: 3, 11: 7, 12: 9, 13: 10, 14: 5, 15: 8, 16: 4, 17: 2
    }
    check_digits = {
        0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7',
        6: '6', 7: '5', 8: '4', 9: '3', 10: '2'
    }
    province = [
        11, 12, 13, 14, 15, 21, 22, 23, 31, 32, 33, 34, 35, 36, 37, 41,
        42, 43, 44, 45, 46, 50, 51, 52, 53, 54, 61, 62, 63, 64, 65, 66
    ]
    
    def generateFakeIdCard() -> str:
        try:
            random_year = random.randint(int(strftime('%Y')) - 82, int(strftime('%Y')) - 18)
            random_month = '0' + str(random.randint(1, 12)) if random.randint(1, 12) < 10 else random.randint(1, 12)
            random_day = '0' + str(random.randint(1, 27)) if random.randint(1, 27) < 10 else random.randint(1, 27)
            birthday = f"{random_year}{random_month}{random_day}"
            serial_number = "0" + str(random.randint(10, 99)) if random.randint(10, 199) < 100 else str(random.randint(10, 199))
            area_code = str(province[random.randint(0, len(province))]) + "0101"
            part_code = area_code + birthday + serial_number
            fake_code = part_code + check_digits[sum(int(part_code[index:index+1]) * weights[index+1] for index in range(17)) % 11]
            return fake_code
        except:
            return ""
        
    if captcha == "":
        success = 1 if sign == "" else 0
        data = {
            "result": 8,
            "message": "需要人机验证",
            "captcha": {
                "success": success,
                "gt": user_gt,
                "challenge": challenge,
                "new_captcha": True,
            }
        }
        return data
    
    sleep(1)
        
    while captcha:
        fake_id_card = generateFakeIdCard()
        if re.match(r"^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$", fake_id_card):
            check_sum = 0
            check_sum = sum(((1 << (17 - index)) % 11) * int(fake_id_card[index]) for index in range(0, 17))
            check_digit = (12 - (check_sum % 11)) % 11
            check_digit = check_digit if check_digit < 10 else 'X'
            if str(check_digit) == fake_id_card[-1]:
                writeLog(f"\033[1;32mFake ID Card: {fake_id_card} - Name: DoctoratePy\033[0;0m")
                break

    if userData.register_account(account, hashlib.md5((password + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest(), secret) != 1:
        data = {
            "result": 5,
            "errMsg": "注册失败，未知错误"
        }
        return data
    
    data = {
        "result": 0,
        "uid": 0,
        "token": secret,
        "isAuthenticate": False,
        "isMinor": False,
        "needAuthenticate": True,
        "isLatestUserAgreement": True
    }
    
    return data


def userLogin() -> Response:
    '''
    result:
        1：用户名或密码错误，请重新登录
        2：此账号未申请IOS平台测试资格，如有疑问请联系客服
        3：此账号尚未激活，如有疑问请联系客服
        7：认证系统人机校验失败，请重试
        8：<需要人机验证>message & captcha
    '''
    
    data = request.data
    request_data = request.get_json()

    sign = request_data["sign"]
    captcha = request_data["captcha"]
    account = request_data["account"]
    password = request_data["password"]

    user_gt = hashlib.md5((str(int(time())) + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest()
    challenge = hashlib.md5((sign).encode()).hexdigest()

    if request.user_agent.platform == "iphone":
        data = {
            "result": 2
        }
        return data

    if len(userData.query_account_by_phone(account)) == 0:
        data = {
            "result": 4
        }
        return data

    result = userData.login_account(account, hashlib.md5((password + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest())

    if len(result) != 1:
        data = {
            "result": 1
        }
        return data

    if captcha == "":
        success = 1 if sign == "" else 0
        data = {
            "result": 8,
            "message": "需要人机验证",
            "captcha": {
                "success": success,
                "gt": user_gt,
                "challenge": challenge,
                "new_captcha": True,
            }
        }
        return data
    else:
        sleep(1)
        if sign == "":
            data = {
                "result": 7
            }
            return data

    accounts = Account(*result[0])
    
    if accounts.get_user() == "{}":
        data = {
            "result": 3
        }
        return data
    
    data = {
        "result": 0,
        "uid": "0",
        "token": accounts.get_secret(),
        "isAuthenticate": True,
        "isMinor": False,
        "needAuthenticate": False,
        "isLatestUserAgreement": True
    }

    return data


def userLoginBySmsCode() -> Response:
    '''
    result:
        1：该用户尚不存在，请先注册
        4：验证码错误或已失效，请重新输入
        7：认证系统人机校验失败，请重试
        8：网络异常，登录失败，请稍后重试 - 错误号:0
    '''
    
    data = request.data
    request_data = request.get_json()

    account = str(request_data["account"])
    smsCode = str(request_data["smsCode"])
    
    result = userData.query_account_by_phone(account)

    if len(result) != 1:
        data = {
            "result": 1
        }
        return data
    
    if not verifySmsCode(smsCode):
        data = {
            "result": 4
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


def userChangePassword() -> Response:
    '''
    result:
        1：格式错误
        2：验证码输入错误
    '''
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    newPassword = request_data["newPassword"]
    phoneCode = request_data["phoneCode"]

    result = userData.query_account_by_secret(secret)
    accounts = Account(*result[0])
    password = accounts.get_password()
    
    if hashlib.md5((newPassword + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest() == password:
        data = {
            "result": 1
        }
        return data
    
    pattern = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,16}$')

    if not pattern.match(newPassword):
        data = {
            "result": 1
        }
        return data

    if not verifySmsCode(phoneCode):
        data = {
            "result": 2
        }
        return data
    
    accounts.set_password(hashlib.md5((newPassword + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest())
    userData.set_password(secret, accounts.get_password())
    
    data = {
        "result": 0
    }

    return data


def userChangePhoneCheck() -> Response:
    '''
    result:
        11：每个账号换绑时间不得少于7天
    '''
    
    data = request.data
    
    secret = request.headers.get('secret')
    result = userData.query_account_by_secret(secret)
    accounts = Account(*result[0])

    player_data = json.loads(accounts.get_user())
    registerTs = player_data["status"]["registerTs"]

    if int(time()) - registerTs < 604800:
        data = {
            "result": 11
        }
        return data

    data = {
        "result": 0
    }

    return data


def userChangePhone() -> Response:
    '''
    result:
        8：手机号已被使用
        12：验证码输入错误
    '''

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get('secret')
    newPhone = request_data["newPhone"]
    phoneCode = request_data["phoneCode"]
    newPhoneCode = request_data["newPhoneCode"]
    
    result = userData.query_account_by_secret(secret)
    accounts = Account(*result[0])

    if len(userData.query_account_by_phone(newPhone)) == 1:
        data = {
            "result": 8
        }
        return data

    if not verifySmsCode(newPhoneCode, phoneCode, True):
        data = {
            "result": 12
        }
        return data
    
    new_secret = hashlib.md5((newPhone + decrypt_user_key(USER_TOKEN_KEY, int(time()))).encode()).hexdigest()
    
    player_data = json.loads(accounts.get_user())
    player_data["status"]["registerTs"] = int(time())
    accounts.set_phone(newPhone)
    accounts.set_secret(new_secret)
    
    userData.set_user_data(accounts.get_uid(), player_data)
    userData.set_phone(secret, accounts.get_phone(), new_secret)

    data = {
        "result": 0
    }

    return data


def userAuth() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = str(request_data["token"])
    
    if secret is None or len(secret) < 0:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
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