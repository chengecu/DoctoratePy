import re
import json
import uuid
import math
import pickle
import socket
import random
from flask import Response, request, abort

from time import time, localtime, mktime
from datetime import datetime
from itertools import product
from constants import CONFIG_PATH, SKIN_TABLE_URL, SKIN_CONFIG_PATH, \
    ITEM_TABLE_URL, LOWGOOD_CONFIG_PATH, GACHA_TABLE_URL, CHARACTER_TABLE_URL, \
    HIGHGOOD_CONFIG_PATH, EXTRAGOOD_LIST_PATH, EPGSGOOD_CONFIG_PATH, REPGOOD_CONFIG_PATH, \
    BUILDING_DATA_URL, SHOP_CLIENT_TABLE_URL, FURNIOOD_CONFIG_PATH, ALLPRODUCT_LIST_PATH
from utils import read_json, write_json
from core.GiveItem import giveItems
from core.function.update import updateData
from core.database import userData
from core.Account import Account


class TemporaryData:

    skin_data_list = {}
    cashGood_data_list = {}
    lowGood_data_list = {}
    highGood_data_list = {}
    epgsGood_data_list = {}
    repGood_data_list = {}
    furniture_data_list = {}

    
def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def shopGetGoodPurchaseState() -> Response:

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    goodIdMap = request_data["goodIdMap"]

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    result = {}

    for goodType in goodIdMap:
        if goodType == "GP":
            good_list = {}
            for type in list(player_data["shop"]["GP"].keys()):
                good_list.update({d["id"]: d["count"] for d in player_data["shop"]["GP"][type]["info"]})
        else:
            good_list = {d["id"]: d["count"] for d in player_data["shop"][goodType]["info"]} if goodType != "CASH" else player_data["shop"]["FURNI"].get("groupInfo", {})
        for item in goodIdMap[goodType]:
            if item in good_list:
                result.update({item: -1})
            else:
                result.update({item: 1})
    
    data = {
        "result": result,
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
    SHOP_CLIENT_TABLE = updateData(SHOP_CLIENT_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    goodList = []
    selling_list = []
    skin_config = read_json(SKIN_CONFIG_PATH, encoding='utf-8')
    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(skin_config["items"])))

    if len(charIdList) != 0:
        writeLog(f"\033[1;31mNeed Report: {str(charIdList)}\033[0;0m")

    for item in SHOP_CLIENT_TABLE["carousels"]:
        for skin in item["items"]:
            if skin["cmd"] == "SKINSHOP" and skin["startTime"] < int(time()) < skin["endTime"]:
                selling_list.append(skin["skinId"])

    for skinId in SKIN_TABLE["charSkins"]:
        if skinId not in charIdList and "@" in skinId:
            skinData = SKIN_TABLE["charSkins"][skinId]
            if skinData["displaySkin"]["obtainApproach"] == "采购中心":
                skinGroupName = skinData["displaySkin"]["skinGroupName"]
                skinGroupName = re.sub(r"/[IVX]+", "", skinGroupName) if re.search(r"/[IVX]+", skinGroupName) else skinGroupName
                skinName = skinData["displaySkin"]["skinName"]
                skinId = skinData["skinId"]
                goodId = "SS_" + skinData["skinId"]
                try:
                    price_data = skin_config["items"][skinGroupName.rstrip()][skinName.rstrip()]
                except:
                    price_data = [18]
                    writeLog(f"\033[1;31mMissing key: {skinGroupName.rstrip()} - {skinName.rstrip()}\033[0;0m")
                discount = 0
                    
                if len(price_data) == 2:
                    originPrice = price_data[0]
                    price = price_data[1]
                    discount = round(1 - (price / originPrice) if originPrice > price else 0, 2)
                else:
                    price = originPrice = price_data[0]
                        
                isRedeem = not (price > 18 or skinName in skin_config["notRedeem"])
                
                if skinId in selling_list:
                    slotId = len(SKIN_TABLE["charSkins"]) - selling_list.index(skinId) + 1
                else:
                    slotId = skinData["displaySkin"]["sortId"]
                    
                SkinGood = {
                    "goodId": goodId,
                    "skinName": skinName,
                    "skinId": skinId,
                    "charId": skinData["charId"],
                    "currencyUnit": "DIAMOND",
                    "originPrice": originPrice,
                    "price": price,
                    "discount": discount,
                    "desc1": skinData["displaySkin"]["dialog"],
                    "desc2": skinData["displaySkin"]["description"],
                    "startDateTime": -1,
                    "endDateTime": -1,
                    "slotId": slotId,
                    "isRedeem": isRedeem
                }
                    
                goodList.append(SkinGood)
                TemporaryData.skin_data_list.update({goodId: price})

    if thash != skin_config["thash"]:
        skin_config["thash"] = thash
        write_json(skin_config, SKIN_CONFIG_PATH)
                
    data = {
        "goodList": goodList,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
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
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "skin": player_data["skin"],
                "status": {
                    "androidDiamond": player_data["status"]["androidDiamond"],
                    "iosDiamond": player_data["status"]["iosDiamond"]
                }
            }
        },
        "result": 0
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
    lowGood_config = read_json(LOWGOOD_CONFIG_PATH, encoding='utf-8')
    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(lowGood_config["items"])))

    group_1 = len(lowGood_config["items"]["group_1"])
    group_2 = group_1 + len(lowGood_config["items"]["group_2"])
    group_3 = group_2 + len(lowGood_config["items"]["group_3"])
    
    for groupId in groups:
        goodId = "LS_" + groupId.split("_")[0]
        group = groupId[-7:].lower()
        num = (0, group_1) if "Group_1" in groupId else (group_1, group_2) if "Group_2" in groupId else (group_2, group_3)
        slotId = 0

        for index, number in enumerate(range(*num)):
            slotId += 1
            itemId = list(lowGood_config["items"][group].keys())[index]
            item_data = itemData[itemId]
            originPrice = lowGood_config["items"][group][itemId]["originPrice"]
            price = lowGood_config["items"][group][itemId]["price"]
            availCount = lowGood_config["items"][group][itemId]["availCount"]
            discount = round(1 - (price / originPrice) if originPrice > price else 0, 2)
            
            item = {
                "id": itemId,
                "count": lowGood_config["items"][group][itemId]["count"],
                "type": item_data["itemType"]
            }
            
            TemporaryData.lowGood_data_list.update({
                goodId + f"_{number + 1}": {
                    "availCount": availCount,
                    "price": price,
                    "item": item
                }
            })
            goodList.append({
                "goodId": goodId + f"_{number + 1}",
                "groupId": groupId,
                "displayName": item_data["name"],
                "originPrice": originPrice,
                "price": price,
                "discount": discount,
                "slotId": slotId,
                "availCount": availCount,
                "item": item
            })

    if f"lggShdShopnumber{shop_number}" != LS["curShopId"] or thash != lowGood_config["thash"]:
        LS["curShopId"] = f"lggShdShopnumber{shop_number}"
        LS["curGroupId"] = f"lggShdShopnumber{shop_number}_Group_1"
        LS["info"] = []
        lowGood_config["thash"] = thash
        write_json(lowGood_config, LOWGOOD_CONFIG_PATH)

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "groups": groups,
        "goodList": goodList,
        "shopEndTime": shopEndTime,
        "newFlag": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {
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
    lowGood_config = read_json(LOWGOOD_CONFIG_PATH, encoding='utf-8')

    group_1 = len(lowGood_config["items"]["group_1"])
    group_2 = group_1 + len(lowGood_config["items"]["group_2"])
    group_3 = group_2 + len(lowGood_config["items"]["group_3"])

    check_status = 0
    spend_shard = TemporaryData.lowGood_data_list[goodId]["price"] * count
    
    if lggShard < spend_shard:
        data = {
            "result": 1
        }
        return data

    num = (0, group_1) if "Group_1" in curGroupId else (group_1, group_2) if "Group_2" in curGroupId else (group_2, group_3)

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
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopGetHighGoodList() -> Response:
    '''
    GoodId = index * 1000 + 26n - (8 + m)
    GoodId_2 = index * 1000 + 12n - (5 + m) + 1
    ModuleGoodId = index * 1000 + 12(n - 3) + (5 + m)
    ProgressGoodId = 12n - (5 + m)
    '''
    
    data = request.data

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    GACHA_TABLE = updateData(GACHA_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    highGood_config = read_json(HIGHGOOD_CONFIG_PATH, encoding='utf-8')
    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(highGood_config["items"])))
    HS = player_data["shop"]["HS"]
    
    date_now = datetime.now()
    good_id = 26 * (date_now.year - datetime(2019, 5, 1).year) - 8 + date_now.month
    moduleGood_id = 12 * (date_now.year - datetime(2019, 5, 1).year - 3) + 5 + date_now.month
    progressGood_id = 12 * (date_now.year - datetime(2019, 5, 1).year) - 5 + date_now.month
    
    carousel = GACHA_TABLE["carousel"]
    for gacha in carousel:
        if gacha["startTime"] < int(time()) < gacha["endTime"]:
            goodStartTime = gacha["startTime"]
            goodEndTime = gacha["endTime"]
            randomSeed = goodStartTime
    
    goodList = []
    materialList = []

    chars_part = highGood_config["items"]["chars"]
    material_part = highGood_config["items"]["materials"]
    normal_part = highGood_config["items"]["normal"]
    rules = highGood_config["items"]["rules"]
    
    for index, item in enumerate(rules):
        max_key = len(list(material_part.keys()))
        limit = len([key for key, _ in ITEM_TABLE["items"].items() if "tier6_" in key]) * 2 if index == 0 else max_key * 2
        rules[index] = min(item + 1, limit) if item % 2 != 0 and item < limit else min(item, limit)
        
    total = len(chars_part) + 2 + rules[0] + rules[1] + len(normal_part)
    
    for index in range(total):
        random.seed(randomSeed)
        goodId = f"HS_{1000 * (index + 1) + good_id}"
        goodType = "NORMAL"
        progressGoodId = None
        item = None
        availCount = 1
        count = 1
        discount = 0
        price = 0

        if index < len(chars_part):
            number = index + 1
            priority = 1
            displayName = CHARACTER_TABLE[chars_part[index]]["name"]
            rarity = CHARACTER_TABLE[chars_part[index]]["rarity"]
            price = 180 if rarity == 5 else 45
            item = {
                "id": chars_part[index],
                "count": count,
                "type": "CHAR"
            }
        elif (index - len(chars_part)) < 2:
            number = index - len(chars_part) + 3
            goodId = f"HS_{1000 * (index + 1) + progressGood_id + 1}"
            priority = 2
            goodType = "PROGRESS"
            
            if index - len(chars_part) == 1:
                displayName = "干员寻访凭证"
                progressGoodId = f"AAA{progressGood_id}"
            else:
                displayName = "加急许可"
                progressGoodId = f"BBB{progressGood_id}"
        elif (index - len(chars_part) - 2) < rules[0]:
            number = index - len(chars_part) + 5
            priority = 3
            availCount = 4
            item_list = [
                [key for key, _ in ITEM_TABLE["items"].items() if "tier5_" in key],
                [key for key, _ in ITEM_TABLE["items"].items() if "tier6_" in key]
            ]
            
            if len(materialList) < rules[0]:
                random.shuffle(item_list[0])
                materialList += random.sample(item_list[0], rules[0] // 2)
                random.shuffle(item_list[1])
                materialList += random.sample(item_list[1], rules[0] // 2)
                randomSeed += random.randint(0, goodEndTime)
                    
            id = materialList[index - len(chars_part) - 2]
            price = 135 if "tier6_" in id else 35
            displayName = ITEM_TABLE["items"][id]["name"]
            item = {
                "id": id,
                "count": count,
                "type": ITEM_TABLE["items"][id]["itemType"]
            }
        elif (index - len(chars_part) - 2 - rules[0]) < rules[1]:
            number = index - len(chars_part) + 5
            priority = 3
            availCount = -1
            item_list = list(material_part.keys())

            if len(materialList) < (rules[0] + rules[1]):
                random.shuffle(item_list)
                tmp_list = random.sample(item_list, rules[1])
                materialList += sorted(tmp_list, key=lambda x: material_part[x]['price'])
                randomSeed += random.randint(0, goodEndTime)

            id = material_part[materialList[index - 4]]["id"]
            price = material_part[materialList[index- 4]]["price"]
            displayName = materialList[index - 4]
            item = {
                "id": id,
                "count": count,
                "type": ITEM_TABLE["items"][id]["itemType"]
            }
        elif (index - len(chars_part) - 2 - rules[0] - rules[1]) < len(normal_part):
            number = index + 1 - rules[0] - rules[1]
            priority = 3
            key, value = list(normal_part.items())[index - len(chars_part) - 2 - rules[0] - rules[1]]
            displayName = key
            id = value["id"]
            price = value["price"]
            availCount = value["availCount"]
            goodId = f"HS_{1000 * (index + 1) + moduleGood_id}" if id == "mod_unlock_token" else goodId
            item = {
                "id": id,
                "count": count,
                "type": ITEM_TABLE["items"][id]["itemType"]
            }
        
        shop_data = {
            "goodId": goodId,
            "displayName": displayName,
            "priority": priority,
            "number": number,
            "goodType": goodType,
            "item": item,
            "progressGoodId": progressGoodId,
            "price": price,
            "originPrice": price,
            "discount": discount,
            "availCount": availCount,
            "goodStartTime": goodStartTime,
            "goodEndTime": goodEndTime
        }

        TemporaryData.highGood_data_list.update({
            goodId: {
                "availCount": availCount,
                "progressGoodId": progressGoodId,
                "price": price,
                "item": item
            }
        })
        
        goodList.append(shop_data)
        
    goodList = sorted(goodList, key = lambda x: x["number"])

    if thash != highGood_config["thash"]:
        HS["info"] = []
        HS["progressInfo"] = {}
        highGood_config["thash"] = thash
        write_json(highGood_config, HIGHGOOD_CONFIG_PATH)

    for item in ["AAA", "BBB"]:
        if f"{item}{progressGood_id}" not in HS["progressInfo"]:
            HS["progressInfo"].update({
                f"{item}{progressGood_id}": {
                    "count": 0,
                    "order": 1
                }
            })

    progressGoodList = {
        f"AAA{progressGood_id}": highGood_config["progress"]["AAA"],
        f"BBB{progressGood_id}": highGood_config["progress"]["BBB"]
    }

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "goodList": goodList,
        "progressGoodList": progressGoodList,
        "newFlag": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "shop": {
                    "HS": HS
                }
            }
        }
    }

    return data


def shopBuyHighGood() -> Response:
    
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
    highGood_config = read_json(HIGHGOOD_CONFIG_PATH, encoding='utf-8')
    info = player_data["shop"]["HS"]["info"]
    progressInfo = player_data["shop"]["HS"]["progressInfo"]
    hggShard = player_data["status"]["hggShard"]
    
    for itemId, data in TemporaryData.highGood_data_list.items():
        if itemId == goodId:
            progress = data["progressGoodId"]
            if progress:
                progressInfo[progress]["count"] += count
                order = progressInfo[progress]["order"]
                
                for item in highGood_config["progress"][progress[:3]]:
                    if item["order"] == order:
                        spend_shard = item["price"]
                        reward_id = item["item"]["id"]
                        reward_type = item["item"]["type"]
                        reward_count = item["item"]["count"]
                        if order < 5:
                            progressInfo[progress]["count"] = 0
                            progressInfo[progress]["order"] += 1
            else:
                spend_shard = data["price"] * count
                reward_id = data["item"]["id"]
                reward_type = data["item"]["type"]
                reward_count = data["item"]["count"] * count

                item_data = {
                    "id": itemId,
                    "count": count
                }
                ids = [item["id"] for item in info]
                if itemId not in ids:
                    info.append(item_data)
                else:
                    for item in info: item["count"] += count if item["id"] == itemId else 0
            break

    if hggShard < spend_shard:
        data = {
            "result": 1
        }
        return data
    
    player_data["status"]["hggShard"] -= spend_shard
    
    items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")

    userData.set_user_data(accounts.get_uid(), player_data)
            
    data = {
        "result": 0,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "skin": player_data["skin"],
                "status": player_data["status"],
                "shop": player_data["shop"],
                "troop": player_data["troop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopGetExtraGoodList() -> Response:
    '''
    MonthId = 12(n - 3) + (3 + m)
    ShopId = n - eta
    '''
    
    data = request.data

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    extraGood_list = read_json(EXTRAGOOD_LIST_PATH, encoding='utf-8')
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    ES = player_data["shop"]["ES"]
    curShopId = ES["curShopId"]
    lastClick = ES.get("lastClick")
    if not lastClick: lastClick = int(time())
    ES["lastClick"] = int(time())

    time_now = localtime()
    year, month = (time_now.tm_year + 1, 1) if time_now.tm_mon == 12 else (time_now.tm_year, time_now.tm_mon + 1)
    goodEndTime = int(mktime((year, month, 1, 4, 0, 0, 0, 0, 0))) - 1
    date_now = datetime.now()
    shop_number = (date_now.year - datetime(2021, 10, 15).year)
    MonthId = 12 * (date_now.year - datetime(2019, 5, 1).year - 3) + 3 + date_now.month
    ShopId = f"xShdShopnumber{shop_number}"

    if curShopId != ShopId:
        ES["curShopId"] = ShopId

    for item in extraGood_list["goodList"]:
        if "Month" in item["goodId"]:
            item["goodId"] = f"ES_xShdShopMonth{MonthId}_1"
            item["goodEndTime"] = goodEndTime
            write_json(extraGood_list, EXTRAGOOD_LIST_PATH)
            break

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "goodList": extraGood_list["goodList"],
        "newFlag": [],
        "lastClick": lastClick,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "shop": {
                    "ES": ES
                }
            }
        }
    }

    return data


def shopBuyExtraGood() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    goodId = request_data["goodId"]
    count = request_data["count"]
    server_config = read_json(CONFIG_PATH)

    extraGood_list = read_json(EXTRAGOOD_LIST_PATH, encoding='utf-8')

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    info = player_data["shop"]["ES"]["info"]

    if player_data["inventory"].setdefault("4006", 0) < count:
        data = {
            "result": 1
        }
        return data

    for item in extraGood_list["goodList"]:
        if item["goodId"] == goodId:
            itemInfo = item
            item_data = {
                "id": goodId,
                "count": count
            }
            ids = [_item["id"] for _item in info]
            if goodId not in ids:
                info.append(item_data)
            else:
                for _item in info: _item["count"] += count if _item["id"] == goodId else 0
            break
    
    price = itemInfo["price"] * count
    player_data["inventory"]["4006"] -= price

    reward_id = itemInfo["item"]["id"]
    reward_type = itemInfo["item"]["type"]
    reward_count = itemInfo["item"]["count"] * count

    items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "skin": player_data["skin"],
                "status": player_data["status"],
                "shop": player_data["shop"],
                "troop": player_data["troop"],
                "inventory": player_data["inventory"]
            }
        },
        "result": 0
    }

    return data


def shopGetEPGSGoodList() -> Response:
    
    data = request.data
    
    server_config = read_json(CONFIG_PATH)
    
    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    EPGSGood_config = read_json(EPGSGOOD_CONFIG_PATH, encoding='utf-8')
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(EPGSGood_config["items"])))

    goodList = []
    sortId = 0
    
    for rarity in reversed(range(4)):
        tmp_list = []
        for id, data in ITEM_TABLE["items"].items():
            goodType = "NORMAL"
            availCount = -1
            if data["classifyType"] == "MATERIAL" and "MTL_SL_" in data["iconId"] and data["rarity"] == rarity:
                count = [8, 4, 2, 1][rarity]
                goodId = f"good_EPGS_{id}"
                try:
                    startTime = EPGSGood_config["items"][id]["startTime"]
                    price = EPGSGood_config["items"][id]["price"]
                except:
                    startTime = int(time()) - 3600
                    price = 15 * (rarity + 1)
                    writeLog(f"\033[1;31mMissing key: {id} - {data['name']}\033[0;0m")
                    
                item = {
                    "id": id,
                    "count": count,
                    "type": data["classifyType"]
                }
                
                shop_data = {
                    "goodId": goodId,
                    "goodType": goodType,
                    "startTime": startTime,
                    "item": item,
                    "price": price,
                    "availCount": availCount
                }

                TemporaryData.epgsGood_data_list.update({
                    goodId: {
                        "price": price,
                        "item": item
                    }
                })
                
                tmp_list.append(shop_data)
                tmp_list = sorted(tmp_list, key = lambda x: x["goodId"], reverse = True)
        goodList += tmp_list

    for sortId, item in enumerate(goodList):
        item["sortId"] = sortId + 1

    if thash != EPGSGood_config["thash"]:
        EPGSGood_config["thash"] = thash
        write_json(EPGSGood_config, EPGSGOOD_CONFIG_PATH)

    data = {
        "goodList": goodList,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def shopBuyEPGSGood() -> Response:
    
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
    
    if player_data["inventory"].setdefault("EPGS_COIN", 0) < count:
        data = {
            "result": 1
        }
        return data
    
    EPGS = player_data["shop"].setdefault("EPGS", {"info": []})
    
    for itemId, data in TemporaryData.epgsGood_data_list.items():
        if itemId == goodId:
            item_data = {
                "id": goodId,
                "count": count
            }
            ids = [_item["id"] for _item in EPGS["info"]]
            if goodId not in ids:
                EPGS["info"].append(item_data)
            else:
                for _item in EPGS["info"]: _item["count"] += count if _item["id"] == goodId else 0
    
            price = data["price"] * count
            player_data["inventory"]["EPGS_COIN"] -= price

            reward_id = data["item"]["id"]
            reward_type = data["item"]["type"]
            reward_count = data["item"]["count"] * count
            
            items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")

            userData.set_user_data(accounts.get_uid(), player_data)
            break
    
    data = {
        "result": 0,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopGetRepGoodList() -> Response:
    
    data = request.data
    
    server_config = read_json(CONFIG_PATH)
    
    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    repGood_config = read_json(REPGOOD_CONFIG_PATH, encoding='utf-8')
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(repGood_config["items"])))
    
    goodList = []
    sortId = 0
    
    for id, data in ITEM_TABLE["items"].items():
        if data["classifyType"] == "MATERIAL" and "MTL_SL_" in data["iconId"] and data["rarity"] == 3:
            goodId = f"good_REP_{id}"
            goodType = "NORMAL"
            availCount = 8
            count = 1
            try:
                startTime = repGood_config["items"]["materials"][id]["startTime"]
                price = repGood_config["items"]["materials"][id]["price"]
            except:
                startTime = int(time()) - 3600
                price = 65
                writeLog(f"\033[1;31mMissing key: {id} - {data['name']}\033[0;0m")

            item = {
                "id": id,
                "count": count,
                "type": data["classifyType"]
            }
            
            shop_data = {
                "goodId": goodId,
                "goodType": goodType,
                "startTime": startTime,
                "item": item,
                "price": price,
                "availCount": availCount
            }
            
            goodList.append(shop_data)
            goodList = sorted(goodList, key = lambda x: x["goodId"])

    for item in repGood_config["items"]["common"]:
        goodList.insert(0, item) if repGood_config["items"]["common"].index(item) == 0 else goodList.append(item)

    for item in goodList:
        TemporaryData.repGood_data_list.update({
            item["goodId"]: {
                "price": item["price"],
                "item": item["item"]
            }
        })
    
    for sortId, item in enumerate(goodList):
        item["sortId"] = sortId + 1

    if thash != repGood_config["thash"]:
        repGood_config["thash"] = thash
        write_json(repGood_config, REPGOOD_CONFIG_PATH)

    data = {
        "goodList": goodList,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def shopBuyRepGood() -> Response:
    
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

    if player_data["inventory"].setdefault("REP_COIN", 0) < count:
        data = {
            "result": 1
        }
        return data
    
    REP = player_data["shop"].setdefault("REP", {"info": []})
    
    for itemId, data in TemporaryData.repGood_data_list.items():
        if itemId == goodId:
            item_data = {
                "id": goodId,
                "count": count
            }
            ids = [_item["id"] for _item in REP["info"]]
            if goodId not in ids:
                REP["info"].append(item_data)
            else:
                for _item in REP["info"]: _item["count"] += count if _item["id"] == goodId else 0
    
            price = data["price"] * count
            player_data["inventory"]["REP_COIN"] -= price

            reward_id = data["item"]["id"]
            reward_type = data["item"]["type"]
            reward_count = data["item"]["count"] * count
            
            items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")

            userData.set_user_data(accounts.get_uid(), player_data)
            break
    
    data = {
        "result": 0,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopGetFurniGoodList() -> Response:
    
    data = request.data
    
    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)
    
    BUILDING_DATA = updateData(BUILDING_DATA_URL, True)
    SHOP_CLIENT_TABLE = updateData(SHOP_CLIENT_TABLE_URL, True)
    furniGood_config = read_json(FURNIOOD_CONFIG_PATH, encoding='utf-8')
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    FURNI = player_data["shop"]["FURNI"]
    
    with open('./server/core/model/pred_furnPrice.pkl', 'rb') as f:
        pred_model = pickle.load(f)
        
    pred_diamond = lambda x: round(0.006028*x + 0.54538757) if math.modf(0.006028*x + 0.54538757)[0] > 0.6555 else int(0.006028*x + 0.54538757)

    goods = []
    groups = []
    normal_list = []
    limit_list = []
    filter_list = []
    carouselGroups = {}
    sortId = 0
    groupId = 0
    groupName = None

    for id, furniture in BUILDING_DATA["customData"]["furnitures"].items():
        shopDisplay = 1
        priceDia = 0
        if any(s in furniture["obtainApproach"] for s in ["家具商店", "幸运掉落"]):
            comfort = furniture["comfort"]
            count = furniture["isOnly"]
            if any(s in furniture["obtainApproach"] for s in ["限时购买", "幸运掉落"]) and "beach" not in furniture["obtainApproach"]:
                tmp_id = furniture["id"].split("_")[1]
            else:
                tmp_id = furniture["id"].split("_")[1] + "_" + furniture["id"].split("_")[-1]
            if "durin" in tmp_id:
                continue
            sequence = len(BUILDING_DATA["customData"]["furnitures"]) + 1000 + furniture["sortId"]

            if groupName != tmp_id:
                groupIndex = 1
                groupName = tmp_id
            else:
                groupIndex += 1
                
            goodId = f"{tmp_id}_{groupIndex}"
            furniId = id
            displayName = furniture["name"]
            priceCoin = int(pred_model.predict([[comfort]]))
            priceDia = pred_diamond(comfort)
            
            if "single" in tmp_id:
                goodId = f"single_{groupIndex}"
            if "pizza" in tmp_id:
                goodId = f"event1_{groupIndex}"
            if "guitar" in tmp_id:
                goodId = f"event2_{groupIndex}"
            
            shop_data = {
                "goodId": goodId,
                "furniId": furniId,
                "shopDisplay": shopDisplay,
                "displayName": displayName,
                "priceCoin": priceCoin,
                "priceDia": priceDia,
                "discount": 0,
                "originPriceCoin": priceCoin,
                "originPriceDia": priceDia,
                "end": -1,
                "count": count,
                "sequence": sequence
            }

            TemporaryData.furniture_data_list.setdefault("items", {})
            TemporaryData.furniture_data_list["items"].update({
                goodId: {
                    "id": furniId,
                    "priceCoin": priceCoin,
                    "priceDia": priceDia
                }
            })
            
            if "限时购买" in furniture["obtainApproach"]:
                limit_list.append(shop_data)
            else:
                normal_list.append(shop_data)

    for index, item in enumerate(reversed(limit_list)):
        item["sequence"] = index + 1
        
    goods += limit_list + normal_list
    
    for item in reversed(furniGood_config["items"]["groups"]):
        SHOP_CLIENT_TABLE["recommendList"].insert(0, {
            "tagName": item["tagName"],
            "groupList": [{
                "dataList": [{
                    "cmd": "FURNSHOP",
                    "param1": item["param1"],
                    "hasDia": item["hasDia"]
                }]
            }]
        })
        
    purchased = []
    groupInfo = player_data["shop"]["FURNI"].setdefault("groupInfo", {})
    goods = {d["furniId"]: d for d in goods}
 
    for item in reversed(SHOP_CLIENT_TABLE["recommendList"]):
        cmd_check = item["groupList"][0]["dataList"][0]["cmd"] == "FURNSHOP"
        tag_check = "限时家具" not in item["tagName"] and item["tagName"].rstrip() not in filter_list
        if cmd_check and tag_check:
            filter_list.append(item["tagName"].rstrip())
            packageId = item["groupList"][0]["dataList"][0]["param1"]
            hasDia = item["groupList"][0]["dataList"][0].get("hasDia")
            if packageId is None:
                continue
            name = item["tagName"].rstrip()
            packageId = packageId.replace("shop_", "")
            if name == "急救专家组办公室":
                packageId = "icu_2021"
            icon = f"icon_furngroup_{packageId}"
            if name == "气密防化安全舱":
                icon = icon.lower() + "_0"
            decoration = 0
            goodList = []
            eventGoodList = []
            
            for theme, furni in BUILDING_DATA["customData"]["themes"].items():
                if name == furni["name"]:
                    description = furni["desc"]
                    furnitures = furni["furnitures"]
                    sequence = 0

                    if furni["themeType"] in ["EVENT", "LINKAGE", "LUCKY"] or name == "茨沃涅克乡野营地":
                        if packageId not in carouselGroups:
                            carouselGroups.update({
                                packageId: 1
                            })
                            
                        if furni["themeType"] != "LUCKY" and groupInfo.get(packageId, 0) > 0:
                            purchased.append(packageId)
                            
                    for id in furnitures:
                        decoration += BUILDING_DATA["customData"]["furnitures"][id]["comfort"] * BUILDING_DATA["customData"]["furnitures"][id]["quantity"]

                    for key, value in BUILDING_DATA["customData"]["groups"].items():
                        if theme in key:
                            decoration = min(decoration + value["comfort"], 5000)
                            sequence += 1
                            for _id in product(value["furniture"], [key]):
                                _id, group_key = _id
                                group_value = BUILDING_DATA["customData"]["groups"][group_key]
                                set_name = group_value["name"]
                                _count = BUILDING_DATA["customData"]["furnitures"][_id]["quantity"]
                                if _id in goods:
                                    if hasDia == False:
                                        goods[_id]["priceDia"] = 0
                                    if sortId != 0:
                                        goods[_id]["shopDisplay"] = 0
                                    goodId = goods[_id]["goodId"]

                                    good_data = {
                                        "goodId": goodId,
                                        "count": _count,
                                        "set": set_name,
                                        "sequence": sequence
                                    }

                                    goodList.append(good_data)
                                else:

                                    event_data = {
                                        "name": BUILDING_DATA["customData"]["furnitures"][_id]["name"],
                                        "count": _count,
                                        "furniId": _id,
                                        "set": set_name,
                                        "sequence": sequence
                                    }

                                    eventGoodList.append(event_data)
            sortId += 1
            groupId += 1
            imageList = []
            
            for index in range(6):
                imageList.append({
                    "picId": f"{packageId}_{index + 1}",
                    "index": index
                })
                
            goodList = sorted(goodList, key = lambda x: int(x["goodId"].split("_")[-1]))
            _sequence = sortId + len(BUILDING_DATA["customData"]["furnitures"]) if sortId != 1 else 0

            group_data = {
                "packageId": packageId,
                "icon": icon,
                "name": name,
                "description": description,
                "sequence": _sequence,
                "saleBegin": 1556697600,
                "saleEnd": -1,
                "decoration": decoration,
                "goodList": goodList,
                "eventGoodList": eventGoodList,
                "imageList": imageList
            }

            TemporaryData.furniture_data_list.setdefault("groups", {})
            TemporaryData.furniture_data_list["groups"].update({
                packageId: {
                    "goodList": goodList
                }
            })
            
            groups.append(group_data)
            
    goods = list(goods.values())

    for item in groups:
        if item["packageId"] in purchased:
            item["sequence"] += len(groups)

    for item in goods:
        ids = [_item["id"] for _item in FURNI["info"]]
        if item["goodId"] not in ids:
            item_data = {
                "id": item["goodId"],
                "count": 0
            }
            FURNI["info"].append(item_data)

    thash = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(groups)))

    if thash != furniGood_config["thash"]:
        furniGood_config["thash"] = thash
        write_json(furniGood_config, FURNIOOD_CONFIG_PATH)

        player_data["carousel"] = {
            "furnitureShop": {
                "goods": {},
                "groups": {}
            }
        }
    
        carouselGoods = player_data["carousel"]["furnitureShop"]["goods"]
        player_data["carousel"]["furnitureShop"]["groups"] = carouselGroups
    
        for item in limit_list:
            if item["goodId"] not in carouselGoods:
                carouselGoods.update({
                    item["goodId"]: 1
                })
            
    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "goods": goods,
        "groups": groups,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "shop": {
                    "FURNI": FURNI
                }
            }
        }
    }

    return data


def shopBuyFurniGood() -> Response:
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    buyCount = request_data["buyCount"]
    costType = request_data["costType"]
    goodId = request_data["goodId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    FURNI = player_data["shop"]["FURNI"]
    
    if costType == "COIN_FURN":
        spend = TemporaryData.furniture_data_list["items"][goodId]["priceCoin"] * buyCount
        if player_data["inventory"].setdefault("3401", 0) < spend:
            data = {
                "result": 1
            }
            return data
        
        player_data["inventory"]["3401"] -= spend
    else:
        spend = TemporaryData.furniture_data_list["items"][goodId]["priceDia"] * buyCount
        if request.user_agent.platform == "iphone":
            if player_data["status"]["iosDiamond"] < spend:
                data = {
                    "result": 1
                }
                return data

            player_data["status"]["iosDiamond"] -= spend
        else:
            if player_data["status"]["androidDiamond"] < spend:
                data = {
                    "result": 1
                }
                return data
            
            player_data["status"]["androidDiamond"] -= spend

    for _item in FURNI["info"]: _item["count"] += buyCount if _item["id"] == goodId else 0
        
    reward_id = TemporaryData.furniture_data_list["items"][goodId]["id"]
    reward_type = "FURN"
    reward_count = buyCount

    items = giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")
    
    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "result": 0,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "building": {
                    "furniture": player_data["building"]["furniture"],
                    "solution": player_data["building"]["solution"]
                },
                "carousel": player_data["carousel"],
                "status": player_data["status"],
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopBuyFurniGroup() -> Response:
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    costType = request_data["costType"]
    goods = request_data["goods"]
    groupId = request_data["groupId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    FURNI = player_data["shop"]["FURNI"]
    
    items = []
    spendCoin = 0
    spendDia = 0
    
    for item in goods:
        spendCoin += TemporaryData.furniture_data_list["items"][item["id"]]["priceCoin"] * item["count"]
        spendDia += TemporaryData.furniture_data_list["items"][item["id"]]["priceDia"] * item["count"]
    
    if costType == "COIN_FURN":
        if player_data["inventory"].setdefault("3401", 0) < spendCoin:
            data = {
                "result": 1
            }
            return data
        
        player_data["inventory"]["3401"] -= spendCoin
    else:
        if request.user_agent.platform == "iphone":
            if player_data["status"]["iosDiamond"] < spendDia:
                data = {
                    "result": 1
                }
                return data

            player_data["status"]["iosDiamond"] -= spendDia
        else:
            if player_data["status"]["androidDiamond"] < spendDia:
                data = {
                    "result": 1
                }
                return data
            
            player_data["status"]["androidDiamond"] -= spendDia
            
    FURNI["info"] = {d["id"]: d for d in FURNI["info"]}

    for item in goods:
        FURNI["info"][item["id"]]["count"] += item["count"]
        reward_id = TemporaryData.furniture_data_list["items"][item["id"]]["id"]
        reward_type = "FURN"
        reward_count = item["count"]

        items += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_SHOP_ITEM")
            
    FURNI["info"] = list(FURNI["info"].values())
    groupInfo = player_data["shop"]["FURNI"].setdefault("groupInfo", {})
    groupInfo[groupId] = groupInfo.get(groupId, 0) + 1

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "result": 0,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "building": {
                    "furniture": player_data["building"]["furniture"],
                    "solution": player_data["building"]["solution"]
                },
                "carousel": player_data["carousel"],
                "status": player_data["status"],
                "shop": player_data["shop"],
                "inventory": player_data["inventory"]
            }
        }
    }

    return data


def shopGetGPGoodList() -> Response:
    
    data = request.data
    
    server_config = read_json(CONFIG_PATH)
    
    #ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    #EPGSGood_config = read_json(EPGSGOOD_CONFIG_PATH, encoding='utf-8')
    
    #if not server_config["server"]["enableServer"]:
    #    return abort(400)

    #with open('./getGPGoodList.json','r',encoding='utf-8') as f:
    #    data2 = json.load(f)

    data = {
        "goodList": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def shopGetCashGoodList() -> Response:
    
    data = request.data
    
    server_config = read_json(CONFIG_PATH)
    
    ALLPRODUCT_LIST = read_json(ALLPRODUCT_LIST_PATH, encoding='utf-8')
    
    if not server_config["server"]["enableServer"]:
        return abort(400)

    cash_list = []
    goodList = []

    for product in reversed(ALLPRODUCT_LIST["productList"]):
        if len(cash_list) == 6:
            break
        if "CS_" in product["product_id"]:
            cash_list.insert(0, product)

    for index, item in enumerate(cash_list):
        diamondNum_map = [1, 6, 20, 40, 66, 130]
        plusNum_map = [0, 1, 4, 10, 24, 55]
        doubleCount = diamondNum_map[index] * 2 if index != 0 else 3
        
        shop_data = {
            "goodId": item["product_id"],
            "slotId": index + 1,
            "price": item["price"] // 100,
            "diamondNum": diamondNum_map[index],
            "doubleCount": doubleCount,
            "plusNum": plusNum_map[index],
            "desc": item["desc"]
        }
        
        TemporaryData.cashGood_data_list.update({
            item["product_id"]: {
                "usualCount": diamondNum_map[index] + plusNum_map[index],
                "doubleCount": doubleCount
            }
        })

        goodList.append(shop_data)

    data = {
        "goodList": goodList,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data
