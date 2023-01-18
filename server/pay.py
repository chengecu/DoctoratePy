import json
import random
import secrets
import urllib.parse
from datetime import datetime
from time import time

from flask import Response, abort, request

from constants import ALLPRODUCT_LIST_PATH, CONFIG_PATH
from core.Account import Account
from core.database import userData
from core.function.giveItem import giveItems
from core.function.update import updateData
from shop import TemporaryData as ShopData
from utils import encrypt_code_data, read_json


class TemporaryData:

    order_data_list = {}


def payGetUnconfirmedOrderIdList() -> Response:

    data = request.data
    data = {
        "orderIdList": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def payCreateOrder() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    storeId = request_data["storeId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    ALLPRODUCT_LIST = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')

    for product in ALLPRODUCT_LIST["productList"]:
        if product["store_id"] == storeId:
            amount = product["price"]
            productName = product["name"]
            break

    orderId = datetime.now().strftime("%Y%m%d%H%M%S") + ''.join(str(random.randint(0, 9)) for _ in range(18))

    TemporaryData.order_data_list.update({
        orderId: request_data
    })

    data = {
        "result": 0,
        "orderId": orderId,
        "extension": json.dumps({
            "appCode": secrets.token_hex(16)[:16],
            "amount": amount,
            "productName": productName,
            "extension": {
                "appStoreProductId": storeId
            },
            "uid": ''.join(str(random.randint(0, 9)) for _ in range(13)),
            "outOrderId": orderId,
            "ts": int(time()),
            "platform": 1,
            "sign": secret
        }, ensure_ascii=False),
        "alertMinor": 0,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def payCreateOrderAlipay() -> Response:

    data = request.data
    request_data = request.get_json()

    orderId = request_data["orderId"]
    order_data = TemporaryData.order_data_list.get(orderId)
    server_config = read_json(CONFIG_PATH)

    ALLPRODUCT_LIST = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')

    if not server_config["server"]["enableServer"]:
        return abort(400)

    baseUrl = f"http://{server_config['server']['host']}:{server_config['server']['port']}"
    returnUrl = f"{baseUrl}/pay/success"

    for product in ALLPRODUCT_LIST["productList"]:
        if product["store_id"] == order_data["storeId"]:
            price = product["price"]
            name = product["name"]
            break

    data = {
        "result": 0,
        "orderId": orderId,
        "qs": urllib.parse.urlencode({
            "app_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}{str(int(time()))}"[:16],
            "biz_content": json.dumps({
                "body": name,
                "subject": "DoctoratePy",
                "out_trade_no": orderId,
                "timeout_express": "90m",
                "total_amount": "90.00",
                "product_code": "FAST_INSTANT_TRADE_PAY"
            }, ensure_ascii=False),
            "charset": "utf-8",
            "format": "JSON",
            "method": "alipay.trade.page.pay",
            "notify_url": baseUrl,
            "return_url": baseUrl,
            "timestamp": datetime.now().isoformat(),
            "sign": encrypt_code_data(secrets.token_hex(16)[:16], baseUrl, int(time()))
        }),
        "prcie": price,
        "pagePay": None,
        "returnUrl": returnUrl,
    }

    return data


def payCreateOrderWechat() -> Response:

    data = request.data
    request_data = request.get_json()

    orderId = request_data["orderId"]
    order_data = TemporaryData.order_data_list.get(orderId)
    server_config = read_json(CONFIG_PATH)

    ALLPRODUCT_LIST = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')

    if not server_config["server"]["enableServer"]:
        return abort(400)

    baseUrl = f"http://{server_config['server']['host']}:{server_config['server']['port']}"

    for product in ALLPRODUCT_LIST["productList"]:
        if product["store_id"] == order_data["storeId"]:
            price = product["price"]

    data = {
        "orderId": orderId,
        "price": price,
        "requestObj": {
            "appid": f"wx{secrets.token_hex(16)[:16]}",
            "partnerid": ''.join(str(random.randint(0, 9)) for _ in range(10)),
            "prepayid": f"wx{secrets.token_hex(16)}",
            "package": "Sign=WXPay",
            "noncestr": str(int(time())) + ''.join(str(random.randint(0, 9)) for _ in range(7)),
            "timestamp": int(time()),
            "sign": encrypt_code_data(secrets.token_hex(16)[:16], baseUrl, int(time()))
        }
    }

    return data


def payConfirmOrderAlipay() -> Response:

    data = request.data
    data = {
        "status": 0
    }

    return data


def payConfirmOrderWechat() -> Response:

    data = request.data
    data = {
        "status": 0
    }

    return data


def payConfirmOrder() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    orderId = request_data["orderId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    order_data = TemporaryData.order_data_list.get(orderId)
    CASH = player_data["shop"]["CASH"]
    GP = player_data["shop"]["GP"]

    items = []

    if "CS_" in order_data["goodId"]:
        item_data = {
            "id": order_data["goodId"],
            "count": 1
        }
        ids = [_item["id"] for _item in CASH["info"]]
        if order_data["goodId"] not in ids:
            CASH["info"].append(item_data)
            diamondCount = ShopData.cashGood_data_list.get(order_data["goodId"])["doubleCount"]
        else:
            for _item in CASH["info"]:
                _item["count"] += 1 if _item["id"] == order_data["goodId"] else 0
            diamondCount = ShopData.cashGood_data_list.get(order_data["goodId"])["usualCount"]

        if request.user_agent.platform == "iphone":
            player_data["status"]["iosDiamond"] += diamondCount
        else:
            player_data["status"]["androidDiamond"] += diamondCount

        items.append({
            "id": "4002",
            "type": "DIAMOND",
            "count": diamondCount
        })

    if "GP_" in order_data["goodId"]:
        return abort(400)
        # item_data = {
        #    "id": order_data["goodId"],
        #    "count": 1
        # }
        # if any(s in order_data["goodId"] for s in ["GP_L", "GP_freeL"]):
        #    pass
    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "receiveItems": {
            "items": items
        },
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "consumable": player_data["consumable"],
                "status": player_data["status"],
                "shop": player_data["shop"],
                "skin": player_data["skin"],
                "troop": player_data["troop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def paySuccess() -> Response:

    data = request.data
    data = {
        "status": 0,
        "message": "DoctoratePy"
    }

    return data
