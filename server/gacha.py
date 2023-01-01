import os
import json
import random
from flask import request

from time import time
from utils import read_json
from re import sub
from itertools import combinations
from typing import Dict, List, Set
from core.database import userData
from constants import CONFIG_PATH, CHARACTER_TABLE_URL, \
    CHARWORD_TABLE_URL, EQUIP_TABLE_URL, GACHA_TABLE_URL
from core.function.update import updateData
from core.Account import Account


class PassableParameters:
    
    PROFESSION_TO_TAG = {
        "MEDIC": 4,
        "WARRIOR": 1,
        "PIONEER": 8,
        "TANK": 3,
        "SNIPER": 2,
        "CASTER": 6,
        "SUPPORT": 5,
        "SPECIAL": 7,
    }
    POSITION_TO_TAG = {
        "MELEE": 9,
        "RANGED": 10,
    }
    RARITY_TO_TAG = {
        5: 11,
        4: 14,
    }
    ROBOT_TAG = 28
    

def gachaSyncNormalGacha():
    
    data = request.data

    secret = request.headers.get('secret')
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data

    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    
    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())
    if "recruitChar" not in player_data["status"]:
        player_data["status"]["recruitChar"] = ""
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "recruit": player_data["recruit"]
            }
        }
    }
    
    return data


def gachaNormalGacha():
    
    data = request.get_json()
    request_data = request.get_json()

    secret = request.headers.get('secret')
    slotId = request_data["slotId"]
    tagList = request_data["tagList"]
    duration = request_data["duration"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    
    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())
    select_tags = []
    tag_data = generate_valid_tags(tagList, duration)
    if not tag_data[0]:
        tag_data = generate_valid_tags([], duration)
    for tag in tagList:
        pick =  0
        if tag in tag_data[1]:
            pick = 1
        select_tags.append({
            "pick": pick,
            "tagId": tag
        })

    slot_data = {
        "durationInSec": duration,
        "maxFinishTs": int(time()) + duration,
        "realFinishTs": int(time()) + duration,
        "selectTags": select_tags,
        "startTs": int(time()),
        "state": 2,
        "tags": refresh_tag_list()
    }
        
    player_data["recruit"]["normal"]["slots"][str(slotId)] = slot_data
    player_data["status"]["recruitChar"] = tag_data[0]
    player_data["status"]["recruitLicense"] -= 1
    
    if duration <= 14400:
        player_data["status"]["gold"] -= 200 + ((duration - 3600) // 600) * 5
    elif duration <= 27000:
        player_data["status"]["gold"] -= 350 + ((duration - 15000) // 600) * 10
    else:
        player_data["status"]["gold"] -= 700 + ((duration - 27600) // 600) * 20

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "recruit": player_data["recruit"],
                "status": player_data["status"]
            }
        }
    }
    
    return data


def gachaBoostNormalGacha():
    
    data = request.get_json()
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    slotId = request_data["slotId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    
    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())
    player_data["recruit"]["normal"]["slots"][str(slotId)]["realFinishTs"] = int(time())
    player_data["status"]["instantFinishTicket"] -= 1

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "recruit": player_data["recruit"],
                "status": player_data["status"]
            }
        }
    }
    
    return data


def gachaCancelNormalGacha():
    
    data = request.get_json()
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    slotId = request_data["slotId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])
    
    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())

    slot_data = {
        "durationInSec": -1,
        "maxFinishTs": -1,
        "realFinishTs": -1,
        "selectTags": [],
        "startTs": -1,
        "state": 1,
        "tags": refresh_tag_list()
    }
    
    player_data["recruit"]["normal"]["slots"][str(slotId)] = slot_data

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "recruit": player_data["recruit"]
            }
        }
    }
    
    return data


def gachaFinishNormalGacha():
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    slotId = request_data["slotId"]
    server_config = read_json(CONFIG_PATH)
    
    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    CHARWORD_TABLE = updateData(CHARWORD_TABLE_URL, True)
    EQUIP_TABLE = updateData(EQUIP_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data ={
            "result": 2,
            "error": "此账户不存在"
        }
        return data
    
    accounts = Account(*result[0])

    if accounts.get_ban() == 1:
        data = {
            "statusCode": 403,
            "error": "Bad Request",
            "message": "Your account has been banned"
        }
        return data
    
    player_data = json.loads(accounts.get_user())
    chars = player_data["troop"]["chars"]
    buildingChars = player_data["building"]["chars"]
    random_char_id = player_data["status"]["recruitChar"]

    repeatCharId = 0
    for i, char in enumerate(player_data["troop"]["chars"].values()):
        if char["charId"] == random_char_id:
            repeatCharId = i + 1
            break

    item_get = []
    is_new = 0
    charinstId = repeatCharId

    if repeatCharId == 0:
        char_data = {}
        skills_array = CHARACTER_TABLE[random_char_id]["skills"]
        skills = []

        for index in range(len(skills_array)):
            new_skils = {
                "skillId": skills_array[index]["skillId"],
                "state": 0,
                "specializeLevel": 0,
                "completeUpgradeTime": -1
            }
            if skills_array[index]["unlockCond"]["phase"] == 0:
                new_skils["unlock"] = 1
            else:
                new_skils["unlock"] = 0
            skills.append(new_skils)
            
        instId = len(player_data["troop"]["chars"]) + 1
        player_data["troop"]["curCharInstId"] = instId + 1
        charinstId = instId
        
        char_data = {
            "instId": instId,
            "charId": random_char_id,
            "favorPoint": 0,
            "potentialRank": 0,
            "mainSkillLvl": 1,
            "skin": f"{random_char_id}#1",
            "level": 1,
            "exp": 0,
            "evolvePhase": 0,
            "gainTime": int(time()),
            "skills": skills,
            "voiceLan": CHARWORD_TABLE["charDefaultTypeDict"][random_char_id],
            "currentEquip": None,
            "equip": {},
            "starMark": 0
        }
        if skills == []:
            char_data["defaultSkillIndex"] = -1
        else:
            char_data["defaultSkillIndex"] = 0
            
        sub1 = random_char_id[random_char_id.index("_") + 1:]
        charName = sub1[sub1.index("_") + 1:]

        if random_char_id in EQUIP_TABLE["charEquip"]:
            for item in EQUIP_TABLE["charEquip"][random_char_id]:
                locked = 1
                if "_001_" in item:
                    locked = 0
                char_data["equip"].update({
                    item: {
                        "hide": 1,
                        "locked": locked,
                        "level": 1
                    }
                })
            char_data["currentEquip"] = f"uniequip_001_{charName}"

        player_data["troop"]["chars"][str(instId)] = char_data
        player_data["troop"]["charGroup"][random_char_id] = {"favorPoint": 0}
        
        buildingChars[str(instId)] = {
            "charId": random_char_id,
            "lastApAddTime": int(time()),
            "ap": 8640000,
            "roomSlotId": "",
            "index": -1,
            "changeScale": 0,
            "bubble": {
                "normal": { "add": -1, "ts": 0 },
                "assist": { "add": -1, "ts": -1 },
            },
            "workTime": 0,
        }
        chars[str(instId)] = char_data
        item_get = [{"type": "HGG_SHD", "id": "4004", "count": 1}]
        is_new = 1
        player_data["status"]["hggShard"] += 1
    else:
        repatChar = player_data["troop"]["chars"][str(repeatCharId)]
        potentialRank = repatChar["potentialRank"]
        rarity = CHARACTER_TABLE[random_char_id]["rarity"]

        itemName = None
        itemType = None
        itemId = None
        itemCount = 0
        
        if rarity == 0:
            itemName = "lggShard"
            itemType = "LGG_SHD"
            itemId = "4005"
            itemCount = 1
        elif rarity == 1:
            itemName = "lggShard"
            itemType = "LGG_SHD"
            itemId = "4005"
            itemCount = 1
        elif rarity == 2:
            itemName = "lggShard"
            itemType = "LGG_SHD"
            itemId = "4005"
            itemCount = 5
        elif rarity == 3:
            itemName = "lggShard"
            itemType = "LGG_SHD"
            itemId = "4005"
            itemCount = 30
        elif rarity == 4:
            itemName = "hggShard"
            itemType = "HGG_SHD"
            itemId = "4004"
            if potentialRank != 5:
                itemCount = 5
            else:
                itemCount = 8
        else:
            itemName = "hggShard"
            itemType = "HGG_SHD"
            itemId = "4004"
            if potentialRank != 5:
                itemCount = 10
            else:
                itemCount = 15
                
        item_get.append({"type": itemType, "id": itemId, "count": itemCount})
        item_get.append({"type": "MATERIAL", "id": "p_" + random_char_id, "count": 1})
        
        player_data["status"][itemName] += itemCount
        try:
            player_data["inventory"]["p_" + random_char_id] += 1
        except:
            player_data["inventory"]["p_" + random_char_id] = 1
        
        chars[str(repeatCharId)] = player_data["troop"]["chars"][str(repeatCharId)]
        
    characterList = list(player_data["dexNav"]["character"].keys())
    if random_char_id not in characterList:
        player_data["dexNav"]["character"][random_char_id] = {
            "charInstId": instId,
            "count": 1
        }
        
        new_char = CHARACTER_TABLE[random_char_id]
        teamList = [
            new_char["nationId"],
            new_char["groupId"],
            new_char["teamId"]
        ]

        for team in teamList:
            if team is not None:
                try:
                    player_data["dexNav"]["teamV2"][team].update({str(instId): 1})
                except:
                    player_data["dexNav"]["teamV2"][team] = {str(instId): 1}
    else:
        player_data["dexNav"]["character"][random_char_id]["count"] += 1
        
    player_data["troop"]["chars"] = chars
    player_data["recruit"]["normal"]["slots"][str(slotId)]["state"] = 1
    player_data["recruit"]["normal"]["slots"][str(slotId)]["selectTags"] = []

    userData.set_user_data(accounts.get_uid(), player_data)

    charGet = {
        "itemGet": item_get,
        "charId": random_char_id,
        "charInstId": charinstId,
        "isNew": is_new
    }

    data = {
        "playerDataDelta": {
            "modified": {
                "dexNav": player_data["dexNav"],
                "recruit": player_data["recruit"],
                "status": player_data["status"],
                "troop": player_data["troop"],
            },
            "deleted": {},
        },
        "charGet": charGet,
    }
    return data


def gachaGetPoolDetail():
    
    data = request.data
    request_data = request.get_json()

    poolId = request_data["poolId"]
    PoolPath = './data/gacha/' + poolId + '.json'
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    if not os.path.exists(PoolPath):
        data = {
            "detailInfo": {
                "availCharInfo": {
                    "perAvailList": []
                },
                "limitedChar": None,
                "weightUpCharInfo": None,
                "gachaObjList": [
                    {
                        "gachaObject": "TEXT",
                        "type": 7,
                        "param": poolId
                    },
                    {
                        "gachaObject": "TEXT",
                        "type": 5,
                        "param": "该卡池尚未实装，无法获取详细信息"
                    }
                ]
            }
        }
        return data
    
    return read_json(PoolPath, encoding="utf-8")


def gachaAdvancedGacha():
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    poolId = request_data["poolId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    if str(poolId) == "BOOT_0_1_1":
        return userGacha("gachaTicket", 380, secret, request_data)
    else:
        return userGacha("gachaTicket", 600, secret, request_data)


def gachaTenAdvancedGacha():
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get('secret')
    poolId = request_data["poolId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        data = {
            "statusCode": 400,
            "error": "Bad Request",
            "message": "Server is close"
        }
        return data
    
    if str(poolId) == "BOOT_0_1_1":
        return userGacha("tenGachaTicket", 3800, secret, request_data)
    else:
        return userGacha("tenGachaTicket", 6000, secret, request_data)


def refresh_tag_list():

    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    GACHA_TABLE = updateData(GACHA_TABLE_URL, True)
    
    tag_list = []
    random_rank_object = []
    random_rank_object.extend([0] * 8)
    random_rank_object.extend([1] * 20)
    random_rank_object.extend([2] * 50)
    random_rank_object.extend([3] * 20)
    random_rank_object.extend([4] * 2)
    random_rank_object.extend([5] * 1)
    random.shuffle(random_rank_object)
    
    char_data = {}
    chars_list = {
        0: [],
        1: [],
        2: [],
        3: [],
        4: [],
        5: []
    }
    
    recruitable = parse_recruitable_chars(GACHA_TABLE["recruitDetail"])
    tag_to_name = {v["tagId"]: v["tagName"] for v in GACHA_TABLE["gachaTags"][:-2]}
    name_to_tag = {v: k for k, v in tag_to_name.items()}

    for k, v in CHARACTER_TABLE.items():
        if v["tagList"] is None:
            continue
        name = v["name"]

        if name not in recruitable:
            continue
        data = {
            "name": v["name"],
            "rarity": v["rarity"],
        }
        tags = [name_to_tag[tag_name] for tag_name in v["tagList"]]
        tags.append(PassableParameters.PROFESSION_TO_TAG[v["profession"]])
        tags.append(PassableParameters.POSITION_TO_TAG[v["position"]])
        if v["displayNumber"].startswith("RCX"):
            tags.append(PassableParameters.ROBOT_TAG)
        if v["rarity"] in PassableParameters.RARITY_TO_TAG:
            tags.append(PassableParameters.RARITY_TO_TAG[v["rarity"]])
        data["tags"] = tags
        char_data[k] = data

    for char in char_data:
        if "char_" in char:
            chars_list[char_data[char]["rarity"]].append(char)
            
    while len(tag_list) < 5:
        random_rank = random.choice(random_rank_object)
        random_char_id = random.choice(chars_list[random_rank])
        tag_list.append(random.choice(char_data[random_char_id]["tags"]))
        tag_list = list(set(tag_list))

    return tag_list


def generate_valid_tags(tagList: List, duration: int):

    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    GACHA_TABLE = updateData(GACHA_TABLE_URL, True)
    
    recruitable = parse_recruitable_chars(GACHA_TABLE["recruitDetail"])
    
    tag_to_name = {v["tagId"]: v["tagName"] for v in GACHA_TABLE["gachaTags"][:-2]}
    name_to_tag = {v: k for k, v in tag_to_name.items()}
    tagIdToOpSet = {k: set() for k in tag_to_name}
    char_data = {}

    for k, v in CHARACTER_TABLE.items():

        if v["tagList"] is None:
            continue
        name = v["name"]

        if name not in recruitable:
            continue
        data = {
            "name": v["name"],
            "rarity": v["rarity"],
        }
        tags = [name_to_tag[tag_name] for tag_name in v["tagList"]]
        tags.append(PassableParameters.PROFESSION_TO_TAG[v["profession"]])
        tags.append(PassableParameters.POSITION_TO_TAG[v["position"]])
        if v["displayNumber"].startswith("RCX"):
            tags.append(PassableParameters.ROBOT_TAG)
        if v["rarity"] in PassableParameters.RARITY_TO_TAG:
            tags.append(PassableParameters.RARITY_TO_TAG[v["rarity"]])
        data["tags"] = tags
        char_data[k] = data

    random_rank_object = []
    if duration <= 13800:
        random_rank_object.extend([0] * 8)
        random_rank_object.extend([1] * 30)
        random_rank_object.extend([2] * 60)
        random_rank_object.extend([3] * 2)
    elif duration <= 27000:
        random_rank_object.extend([1] * 20)
        random_rank_object.extend([2] * 60)
        random_rank_object.extend([3] * 18)
        random_rank_object.extend([4] * 2)
    else:
        if 11 in tagList:
            random_rank_object.extend([5] * 100)
        elif 14 in tagList:
            random_rank_object.extend([5] * 100)
        else:
            random_rank_object.extend([2] * 78)
            random_rank_object.extend([3] * 20)
            random_rank_object.extend([4] * 2)
            
    random.shuffle(random_rank_object)
    random_rank = random.choice(random_rank_object)

    for char_id, _char_data in char_data.items():
        if CHARACTER_TABLE[char_id]["rarity"] == random_rank:
            for tag_id in _char_data["tags"]:
                tagIdToOpSet[tag_id].add(char_id)

    tagIdToOpSet = tagIdToOpSet
    
    tag_choices = tagList
    if len(tag_choices) == 0:
        tag_choices = [1, 2, 3, 4, 5, 6, 7, 8]
    
    n_choices = len(tag_choices)
    alternative_list = []

    for nTags in range(1, 4):
        for tagComb in combinations(range(n_choices), nTags):
            tagComb = [tag_choices[v] for v in tagComb]
            char_sets: List[Set] = []
            for tag in tagComb:
                char_sets.append(tagIdToOpSet[tag])
            if len(char_sets) == 1:
                if len(char_sets[0]) > 0:
                    for item in list(char_sets[0]):
                        alternative_list.extend([item] * len(tagComb))
                    continue
            result = char_sets[0].intersection(*char_sets[1:])
            if len(result) > 0:
                for item in list(result):
                    alternative_list.extend([item] * len(tagComb))
                    
    random.shuffle(alternative_list)
    try:
        random_char_id = random.choice(alternative_list)
        current_tags =  char_data[random_char_id]["tags"]
    except:
        random_char_id = None
        current_tags =  None
    
    return random_char_id, current_tags

    
def parse_recruitable_chars(s: str) -> Set[str]:

    ret = set()
    min_pos = s.find("★" + r"\n")
    for rarity in range(1, 7):
        start_s = r"★" * rarity + r"\n"
        start_pos = s.find(start_s, min_pos) + len(start_s)
        end_pos = s.find("\n-", start_pos)
        if end_pos == -1:
            s2 = s[start_pos:]
        else:
            s2 = s[start_pos:end_pos]
        min_pos = end_pos
        s2 = sub(r"<.*?>", "", s2)
        sl = s2.split("/")
        for v in sl:
            ret.add(v.strip())
            
    return ret

    
def userGacha(type: str, diamondShard: int, secret: str, request_data: Dict):
    
    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    CHARWORD_TABLE = updateData(CHARWORD_TABLE_URL, True)
    EQUIP_TABLE = updateData(EQUIP_TABLE_URL, True)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        data = {
            "result": 2,
            "error": "此账户不存在"
        }
        return data

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    poolId = request_data["poolId"]
    PoolPath = './data/gacha/' + poolId + '.json'
    useTkt = request_data["useTkt"]

    if "gachaCount" not in player_data["status"]:
        player_data["status"]["gachaCount"] = 0
    
    if not os.path.exists(PoolPath):
        data = {
            "result": 1,
            "errMsg": "该当前干员寻访无法使用，详情请关注官方公告"
        }
        return data

    pool_data = read_json(PoolPath, encoding="utf-8")
    gachaResultList = []
    newChars = []
    charGet = {}
    troop = {}
    usedimmond = 0
    chars = player_data["troop"]["chars"]
    
    if str(poolId) == "BOOT_0_1_1":
        usedimmond = diamondShard // 380
    else:
        usedimmond = diamondShard // 600

    for count in range(usedimmond):
        if useTkt in [1, 2]:
            if player_data["status"][type] <= 0:
                data = {
                    "result": 2,
                    "errMsg": "剩余寻访凭证不足"
                }
                return data
        else:
            if player_data["status"]["diamondShard"] < diamondShard:
                data = {
                    "result": 3,
                    "errMsg": "剩余合成玉不足"
                }
                return data

        minimum = False
        poolObjecName = None
        pool = {}

        if poolId == "BOOT_0_1_1":
            poolObjecName = "newbee"
            pool = player_data["gacha"][poolObjecName]
            cnt = pool["cnt"] - 1

            player_data["gacha"][poolObjecName]["cnt"] = cnt
            player_data["status"]["gachaCount"] += 1

            if cnt == 0:
                player_data["gacha"][poolObjecName]["openFlag"] = 0
        else:
            poolObjecName = "normal"

            if poolId not in player_data["gacha"][poolObjecName]:
                _pool = {
                    "cnt": 0,
                    "maxCnt": 10,
                    "rarity": 4,
                    "avail": True
                }
                player_data["gacha"][poolObjecName][poolId] = _pool

            pool = player_data["gacha"][poolObjecName][poolId]
            cnt = pool["cnt"] + 1

            player_data["gacha"][poolObjecName][poolId]["cnt"] = cnt
            player_data["status"]["gachaCount"] += 1

            if cnt == 10 and pool["avail"]:
                player_data["gacha"][poolObjecName][poolId]["avail"] = False
                minimum = True

        availCharInfo = pool_data["detailInfo"]["availCharInfo"]["perAvailList"]
        upCharInfo = pool_data["detailInfo"]["upCharInfo"]["perCharList"]
        random_rank_array = []
        
        for index in range(len(availCharInfo)):
            total_percent = int(availCharInfo[index]["totalPercent"] * 200)
            rarity_rank = availCharInfo[index]["rarityRank"]
            
            if rarity_rank == 5:
                total_percent += int(((player_data["status"]["gachaCount"] + 50) / 50) * 2)

            if minimum:
                if rarity_rank < pool["rarity"]:
                    continue
                
            random_rank_object = {
                "rarityRank": rarity_rank,
                "index": index
            }

            for i in range(total_percent):
                random_rank_array.append(random_rank_object)

        random.shuffle(random_rank_array)
        
        random_rank = random.choice(random_rank_array)
        
        if not poolId == "BOOT_0_1_1":
            if random_rank["rarityRank"] >= pool["rarity"]:
                player_data["gacha"][poolObjecName][poolId]["avail"] = False

        if random_rank["rarityRank"] == 5:
            player_data["status"]["gachaCount"] = 0

        random_char_array = availCharInfo[random_rank["index"]]["charIdList"]
        
        for index in range(len(upCharInfo)):
            if upCharInfo[index]["rarityRank"] == random_rank["rarityRank"]:
                percent = int(upCharInfo[index]["percent"] * 100) - 15
                up_char_id_list = upCharInfo[index]["charIdList"]

                for n in range(len(up_char_id_list)):
                    char_id = up_char_id_list[n]
                    random_char_array += [char_id] * percent

        random.shuffle(random_char_array)

        random_char_id = random.choice(random_char_array)
        repeatCharId = 0

        for i, char in enumerate(player_data["troop"]["chars"].values()):
            if char["charId"] == random_char_id:
                repeatCharId = i + 1
                break

        if repeatCharId == 0:
            get_char = {}
            char_data = {}
            skills_array = CHARACTER_TABLE[random_char_id]["skills"]
            skills = []
            
            for i in range(len(skills_array)):
                new_skills = {
                    "skillId": skills_array[i]["skillId"],
                    "state": 0,
                    "specializeLevel": 0,
                    "completeUpgradeTime": -1
                }
                if skills_array[i]["unlockCond"]["phase"] == 0:
                    new_skills["unlock"] = 1
                else:
                    new_skills["unlock"] = 0
                skills.append(new_skills)
                
            instId = len(player_data["troop"]["chars"]) + 1
            player_data["troop"]["curCharInstId"] = instId + 1
            
            char_data = {
                "instId": instId,
                "charId": random_char_id,
                "favorPoint": 0,
                "potentialRank": 0,
                "mainSkillLvl": 1,
                "skin": f"{random_char_id}#1",
                "level": 1,
                "exp": 0,
                "evolvePhase": 0,
                "gainTime": int(time()),
                "skills": skills,
                "voiceLan": CHARWORD_TABLE["charDefaultTypeDict"][random_char_id],
                "currentEquip": None,
                "equip": {},
                "starMark": 0
            }

            if skills == []:
                char_data["defaultSkillIndex"] = -1
            else:
                char_data["defaultSkillIndex"] = 0
            
            sub1 = random_char_id[random_char_id.index("_") + 1:]
            charName = sub1[sub1.index("_") + 1:]

            if random_char_id in EQUIP_TABLE["charEquip"]:
                for item in EQUIP_TABLE["charEquip"][random_char_id]:
                    locked = 1
                    if "_001_" in item:
                        locked = 0
                    char_data["equip"].update({
                        item: {
                            "hide": 1,
                            "locked": locked,
                            "level": 1
                        }
                    })
                char_data["currentEquip"] = f"uniequip_001_{charName}"
                
            player_data["troop"]["chars"][str(instId)] = char_data
            player_data["troop"]["charGroup"][random_char_id] = {"favorPoint": 0}
            buildingChars = {}
            buildingChars[str(instId)] = {
                "charId": random_char_id,
                "lastApAddTime": int(time()),
                "ap": 8640000,
                "roomSlotId": "",
                "index": -1,
                "changeScale": 0,
                "bubble": {
                    "normal": { "add": -1, "ts": 0 },
                    "assist": { "add": -1, "ts": -1 },
                },
                "workTime": 0,
            }
            
            player_data["building"]["chars"][str(instId)] = buildingChars
            get_char = {
                "charInstId": instId,
                "charId": random_char_id,
                "isNew": 1
            }
            
            item_get = []
            new_item_get = {
                "type": "HGG_SHD",
                "id": "4004",
                "count": 1
            }
            item_get.append(new_item_get)
            player_data["status"]["hggShard"] += 1

            get_char["itemGet"] = item_get
            player_data["inventory"][f"p_{random_char_id}"] = 0
            gachaResultList.append(get_char)
            newChars.append(get_char)
            charGet = get_char

            charinstId = {
                str(instId): char_data
            }
            chars[str(instId)] = char_data
            troop["chars"] = charinstId
        else:
            get_char = {
                "charInstId": repeatCharId,
                "charId": random_char_id,
                "isNew": 0
            }

            repatChar = player_data["troop"]["chars"][str(repeatCharId)]
            potentialRank = repatChar["potentialRank"]
            rarity = CHARACTER_TABLE[random_char_id]["rarity"]

            itemName = None
            itemType = None
            itemId = None
            itemCount = 0
        
            if rarity == 0:
                itemName = "lggShard"
                itemType = "LGG_SHD"
                itemId = "4005"
                itemCount = 1
            elif rarity == 1:
                itemName = "lggShard"
                itemType = "LGG_SHD"
                itemId = "4005"
                itemCount = 1
            elif rarity == 2:
                itemName = "lggShard"
                itemType = "LGG_SHD"
                itemId = "4005"
                itemCount = 5
            elif rarity == 3:
                itemName = "lggShard"
                itemType = "LGG_SHD"
                itemId = "4005"
                itemCount = 30
            elif rarity == 4:
                itemName = "hggShard"
                itemType = "HGG_SHD"
                itemId = "4004"
                if potentialRank != 5:
                    itemCount = 5
                else:
                    itemCount = 8
            else:
                itemName = "hggShard"
                itemType = "HGG_SHD"
                itemId = "4004"
                if potentialRank != 5:
                    itemCount = 10
                else:
                    itemCount = 15

            item_get = []
            new_item_get_1 = {
                "type": itemType,
                "id": itemId,
                "count": itemCount
            }
            item_get.append(new_item_get_1)
            
            player_data["status"][itemName] += count

            new_item_get_2 = {
                "type": "MATERIAL",
                "id": f"p_{random_char_id}",
                "count": 1
            }
            item_get.append(new_item_get_2)
            get_char["itemGet"] = item_get
            try:
                player_data["inventory"]["p_" + random_char_id] += 1
            except:
                player_data["inventory"]["p_" + random_char_id] = 1

            gachaResultList.append(get_char)
            charGet = get_char
            
            charinstId = {
                str(repeatCharId): player_data["troop"]["chars"][str(repeatCharId)]
            }
            chars[str(repeatCharId)] = player_data["troop"]["chars"][str(repeatCharId)]
            troop["chars"] = charinstId

        characterList = list(player_data["dexNav"]["character"].keys())
        if random_char_id not in characterList:
            player_data["dexNav"]["character"][random_char_id] = {
                "charInstId": instId,
                "count": 1
            }

            new_char = CHARACTER_TABLE[random_char_id]
            teamList = [
                new_char["nationId"],
                new_char["groupId"],
                new_char["teamId"]
            ]

            for team in teamList:
                if team is not None:
                    try:
                        player_data["dexNav"]["teamV2"][team].update({str(instId): 1})
                    except:
                        player_data["dexNav"]["teamV2"][team] = {str(instId): 1}
        else:
            player_data["dexNav"]["character"][random_char_id]["count"] += 1

    if useTkt in [1, 2]:
        player_data["status"][type] -= 1
    else:
        player_data["status"]["diamondShard"] -= diamondShard

    player_data["troop"]["chars"] = chars

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "charGet": charGet,
        "gachaResultList": gachaResultList,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dexNav": player_data["dexNav"],
                "troop": player_data["troop"],
                "consumable": player_data["consumable"],
                "status": player_data["status"],
                "inventory": player_data["inventory"],
                "gacha": player_data["gacha"]
            }
        }
    }

    return data