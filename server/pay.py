import uuid
import json
import socket
from flask import Response, request, abort

from datetime import datetime
from constants import CONFIG_PATH, ALLPRODUCT_LIST_PATH
from utils import read_json
from core.GiveItem import giveItems
from core.function.update import updateData
from core.database import userData
from core.Account import Account
from shop import TemporaryData as ShopData


class TemporaryData:

    order_data_list = {}


def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


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

    orderIdList = []
    
    orderId = str(uuid.uuid1())
    orderIdList.append(orderId)

    TemporaryData.order_data_list.update({
        orderId: request_data
    })

    data = {
        "result": 0,
        "orderId": orderId,
        "orderIdList": orderIdList,
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
    server_config = read_json(CONFIG_PATH)["server"]

    ALLPRODUCT_LIST = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')
    
    returnUrl = f"http://{server_config['host']}:{server_config['port']}/pay/success"

    for product in ALLPRODUCT_LIST["productList"]:
        if product["store_id"] == order_data["storeId"]:
            price = product["price"] // 100
            break

    data = {
        "result": 0,
        "orderId": orderId,
        "price": price,
        "qs": "DoctoratePy",
        "pagePay": True,
        "returnUrl": returnUrl,
    }
    
    return data


def payCreateOrderWechat() -> Response:
    
    data = request.data
    data = {
        "result": 0
    }
    
    return data


def payConfirmOrderAlipay() -> Response:
    
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
            for _item in CASH["info"]: _item["count"] += 1 if _item["id"] == order_data["goodId"] else 0
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
        #item_data = {
        #    "id": order_data["goodId"],
        #    "count": 1
        #}
        #if any(s in order_data["goodId"] for s in ["GP_L", "GP_freeL"]):
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