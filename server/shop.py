import re
import json
from flask import Response, request, abort

from time import time, localtime, mktime
from datetime import datetime
from constants import CONFIG_PATH, SKIN_TABLE_URL, SKINPRICE_LIST_PATH, \
    ITEM_TABLE_URL, LOWGOODPRICE_LIST_PATH, GACHA_TABLE_URL
from utils import read_json
from core.GiveItem import giveItems
from core.function.update import updateData
from core.database import userData
from core.Account import Account


class TemporaryData:

    skin_data_list = {}
    lowGood_data_list = {}


def shopGetGoodPurchaseState() -> Response:

    data = request.data
    data = {
        "result": {},
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def shopGetSkinGoodList() -> Response:

    data = request.data
    request_data = request.get_json()

    charIdList = request_data["charIdList"]
    server_config = read_json(CONFIG_PATH)
    
    SKIN_TABLE = updateData(SKIN_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    goodList = []
    skin_config = read_json(SKINPRICE_LIST_PATH, encoding='utf-8')

    if len(charIdList) != 0: print(charIdList) # TODO: Remove this line

    for skinId in SKIN_TABLE["charSkins"]:
        if skinId not in charIdList and "@" in skinId:
            skinData = SKIN_TABLE["charSkins"][skinId]
            if skinData["displaySkin"]["obtainApproach"] == "采购中心":
                skinGroupName = skinData["displaySkin"]["skinGroupName"]
                skinGroupName = re.sub(r"/[IVX]+", "", skinGroupName) if re.search(r"/[IVX]+", skinGroupName) else skinGroupName
                skinName = skinData["displaySkin"]["skinName"]
                goodId = "SS_" + skinData["skinId"]
                price_data = skin_config["items"][skinGroupName.rstrip()][skinName.rstrip()]
                discount = 0
                    
                if len(price_data) == 2:
                    originPrice = price_data[0]
                    price = price_data[1]
                    discount = round(1 - (price / originPrice) if originPrice > price else price / originPrice, 2)
                else:
                    price = originPrice = price_data[0]
                        
                isRedeem = not (price > 18 or skinName in skin_config["notRedeem"])
                    
                SkinGood = {
                    "goodId": goodId,
                    "skinName": skinName,
                    "skinId": skinData["skinId"],
                    "charId": skinData["charId"],
                    "currencyUnit": "DIAMOND",
                    "originPrice": originPrice,
                    "price": price,
                    "discount": discount,
                    "desc1": skinData["displaySkin"]["dialog"],
                    "desc2": skinData["displaySkin"]["description"],
                    "startDateTime": -1,
                    "endDateTime": -1,
                    "slotId": skinData["displaySkin"]["sortId"],
                    "isRedeem": isRedeem
                }
                    
                goodList.append(SkinGood)
                TemporaryData.skin_data_list.update({goodId: price})
                
    data = {
        "goodList":goodList,
        "playerDataDelta":{
            "deleted":{},
            "modified":{}
        }
    }

    return data


def shopBuySkinGood() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    goodId = request_data["goodId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["status"]["androidDiamond"] -= TemporaryData.skin_data_list[goodId]
    player_data["status"]["iosDiamond"] -= TemporaryData.skin_data_list[goodId]
    
    giveItems(player_data, goodId, "CHAR_SKIN")

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "playerDataDelta":{
            "deleted":{},
            "modified":{
                "skin": player_data["skin"],
                "status": {
                    "androidDiamond": player_data["status"]["androidDiamond"],
                    "iosDiamond": player_data["status"]["iosDiamond"]
                }
            }
        }
    }

    return data


def shopGetLowGoodList() -> Response:
    '''
    ShopNumber = 12n + (m - 5) + 1
    '''

    data = request.data

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    LS = player_data["shop"]["LS"]
    
    time_now = localtime()
    year, month = (time_now.tm_year + 1, 1) if time_now.tm_mon == 12 else (time_now.tm_year, time_now.tm_mon + 1)
    shopEndTime = int(mktime((year, month, 1, 4, 0, 0, 0, 0, 0))) - 1
    date_now = datetime.now()
    shop_number = (date_now.year - datetime(2019, 5, 1).year) * 12 + (date_now.month - datetime(2019, 5, 1).month) + 1
    
    goodList = []
    itemData = ITEM_TABLE["items"]
    groups = [f"lggShdShopnumber{shop_number}_Group_{num}" for num in range(1, 4)]
    lowGood_config = read_json(LOWGOODPRICE_LIST_PATH, encoding='utf-8')
    
    for groupId in groups:
        goodId = "LS_" + groupId.split("_")[0]
        num = tuple(lowGood_config["groupIndex"][0]) if "Group_1" in groupId else tuple(lowGood_config["groupIndex"][1]) if "Group_2" in groupId else tuple(lowGood_config["groupIndex"][2])
        slotId = 0
        
        for index in range(*num):
            slotId += 1
            itemId = list(lowGood_config["items"].keys())[index]
            item_data = itemData[itemId.rstrip()]
            originPrice = lowGood_config["items"][itemId]["originPrice"]
            price = lowGood_config["items"][itemId]["price"]
            availCount = lowGood_config["items"][itemId]["availCount"]
            discount = round(1 - (price / originPrice) if originPrice > price else 0, 2)
            
            item = {
                "id": itemId.rstrip(),
                "count": lowGood_config["items"][itemId]["count"],
                "type": item_data["itemType"]
            }
            
            TemporaryData.lowGood_data_list.update({
                goodId + f"_{index + 1}": {
                    "availCount": availCount,
                    "price": price,
                    "item": item
                }
            })
            goodList.append({
                "goodId": goodId + f"_{index + 1}",
                "groupId": groupId,
                "displayName": item_data["name"],
                "originPrice": originPrice,
                "price": price,
                "discount": discount,
                "slotId": slotId,
                "availCount": availCount,
                "item": item
            })

    if f"lggShdShopnumber{shop_number}" != LS["curShopId"]:
        LS["curShopId"] = f"lggShdShopnumber{shop_number}"
        LS["curGroupId"] = f"lggShdShopnumber{shop_number}_Group_1"
        LS["info"] = []

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "groups": groups,
        "goodList": goodList,
        "shopEndTime": shopEndTime,
        "newFlag": [],
        "playerDataDelta":{
            "deleted":{},
            "modified":{
                "shop": {
                    "LS": LS
                }
            }
        }
    }

    return data


def shopBuyLowGood() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    goodId = request_data["goodId"]
    count = request_data["count"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    info = player_data["shop"]["LS"]["info"]
    curGroupId = player_data["shop"]["LS"]["curGroupId"]
    lggShard = player_data["status"]["lggShard"]
    lowGood_config = read_json(LOWGOODPRICE_LIST_PATH, encoding='utf-8')

    check_status = 0
    spend_shard = TemporaryData.lowGood_data_list[goodId]["price"] * count
    
    if lggShard < spend_shard:
        data = {
            "result": 1
        }
        return data

    num = tuple(lowGood_config["groupIndex"][0]) if "Group_1" in curGroupId else tuple(lowGood_config["groupIndex"][1]) if "Group_2" in curGroupId else tuple(lowGood_config["groupIndex"][2])

    for index in range(*num):
        itemId = list(TemporaryData.lowGood_data_list.keys())[index]
        item_data = {
            "id": itemId,
            "count": 0
        }
        ids = [item["id"] for item in info]
        if itemId in ids:
            continue
        else:
            info.append(item_data) 
    
    for item in info:
        if item["id"] == goodId:
            item["count"] += count
        if item["count"] == TemporaryData.lowGood_data_list[item["id"]]["availCount"]:
             check_status += 1

    if len(info) == check_status:
        id = int(curGroupId[curGroupId.rindex("_") + 1:]) + 1
        if id <= 3:
            player_data["shop"]["LS"]["curGroupId"] = curGroupId[:curGroupId.rindex("_") + 1] + str(id)

    player_data["status"]["lggShard"] -= spend_shard
    reward_id = TemporaryData.lowGood_data_list[goodId]["item"]["id"]
    reward_type = TemporaryData.lowGood_data_list[goodId]["item"]["type"]
    reward_count = TemporaryData.lowGood_data_list[goodId]["item"]["count"] * count
    
    items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "items": items,
        "playerDataDelta":{
            "deleted":{},
            "modified":{
                "status": player_data["status"],
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


#def shopGetHighGoodList() -> Response:
#    '''
#    GoodId = index * 1000 + 26n - (8 + m)
#    GoodId_2 = index * 1000 + 12n - (5 + m) + 1
#    ModuleGoodId = index * 1000 + 12(n - 2) + (5 + m)
#    ProgressGoodId = 12n - (5 + m)
#    '''
    
#    data = request.data

#    secret = request.headers.get("secret")
#    server_config = read_json(CONFIG_PATH)

#    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
#    GACHA_TABLE = updateData(GACHA_TABLE_URL, True)
    
#    if not server_config["server"]["enableServer"]:
#        return abort(400)

#    result = userData.query_account_by_secret(secret)
    
#    if len(result) != 1:
#        return abort(500)
    
#    accounts = Account(*result[0])
#    player_data = json.loads(accounts.get_user())
    
#    date_now = datetime.now()
#    good_id = 26 * (date_now.year - datetime(2019, 5, 1).year) - 8 + date_now.month
#    moduleGood_id = 12 * (date_now.year - datetime(2019, 5, 1).year - 2) + 5 + date_now.month
#    progressGood_id = 12 * (date_now.year - datetime(2019, 5, 1).year) - 5 + date_now.month
    
#    carousel = GACHA_TABLE["carousel"]
#    for gacha in carousel:
#        if gacha["startTime"] < int(time()) < gacha["endTime"]:
#            goodStartTime = gacha["startTime"]
#            goodEndTime = gacha["endTime"]
    
#    goodList = []
#    for index, number in zip(range(16), [1,2,3,4,7,8,9,10,11,12,13,14,15,16,5,6]):
#        goodId = f"HS_{1000 * (index + 1) + good_id}"
#        progressGoodId = None
#        count = 1
#        discount = 0
        
#        if index in [0, 1]:
#            priority = 1
#            goodType = "NORMAL"
#            type = "CHAR"
#            price = 180
#            availCount = 1
        
#        shop_data = {
#            "goodId": goodId,
#            "displayName": "温蒂",
#            "priority": priority,
#            "number": number,
#            "goodType": goodType,
#            "item": {
#                "id": "char_400_weedy",
#                "count": count,
#                "type": type
#            },
#            "progressGoodId": progressGoodId,
#            "price": price,
#            "originPrice": price,
#            "discount": discount,
#            "availCount": availCount,
#            "goodStartTime": goodStartTime,
#            "goodEndTime": goodEndTime
#        }
        
#        try:
#            goodList.append(shop_data)
#        except:
#            pass

#    print(goodList)
    
#    data = {
#        "goodList": goodList,
#        "progressGoodList": [],
#        "newFlag": [],
#        "playerDataDelta":{
#            "deleted":{},
#            "modified":{}
#        }
#    }

#    return data