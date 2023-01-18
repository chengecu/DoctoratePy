from time import time

from constants import CONFIG_PATH
from flask import Response, abort, request
from utils import read_json


def onlineV1Ping() -> Response:
    '''
    result:
        1：<自定义消息>message
        2：您已达到本日在线时长上限或不在可游戏时间范围内，请合理安排游戏时间
        4：<会导致客户端登录按钮消失>
    '''

    data = request.data

    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    if server_config["developer"]["timestamp"] > int(time()):
        data = {
            "result": 1,
            "message": "一场游戏需要规则，但观众们最想看到的总是突破规则的东西"
        }
        return data

    data = {
        "alertTime": 600,
        "interval": 120,
        "message": "OK",
        "result": 0,
        "timeLeft": -1
    }

    return data


def onlineV1LoginOut() -> Response:

    data = request.data
    data = {
        "result": 0
    }

    return data
