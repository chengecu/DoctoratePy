import base64
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
            "message": f"{base64.b64decode(b'5LiA5Zy65ri45oiP6ZyA6KaB6KeE5YiZ77yM5L2G6KeC5LyX5Lus5pyA5oOz55yL5Yiw55qE5oC75piv56qB56C06KeE5YiZ55qE5Lic6KW/').decode('utf-8')}"
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
