import json
import uuid
import base64
import random
import socket
from flask import request

from time import time
from datetime import datetime
from constants import CONFIG_PATH, CHARACTER_TABLE_URL, CHARWORD_TABLE_URL, \
    EQUIP_TABLE_URL, ITEM_TABLE_URL, STAGE_JSON_PATH, STAGE_TABLE_URL, BUILDING_DATA_URL
from utils import read_json, decrypt_battle_data, decrypt_battle_replay
from core.function.update import updateData
from core.database import userData
from core.Account import Account, UserInfo
from core.Search import SearchAssistCharList


class PassableParameters:
    
    PracticeTicket = False
    suggestFriend = False

    
def writeLog(data):

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def questBattleStart():

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    assistFriend = request_data["assistFriend"]
    stageId = request_data["stageId"]
    usePracticeTicket = request_data["usePracticeTicket"]
    server_config = read_json(CONFIG_PATH)

    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
    
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
    player_data["status"]["battleId"] = str(base64.b64encode(stageId.encode('utf-8')), 'utf-8')
    chars_data = player_data["troop"]["chars"]
    stage_table = STAGE_TABLE["stages"][stageId]
    dangerLevel = stage_table["dangerLevel"]

    if assistFriend is not None:
        friend_data = json.loads(accounts.get_friend())["list"]
        friendList = []
        
        for friend in friend_data:
            friendList.append(str(friend["uid"]))
            
        if assistFriend["uid"] not in friendList:
            PassableParameters.suggestFriend = True

    notifyPowerScoreNotEnoughIfFailed = False
    if request_data["squad"] is not None:
        slots = request_data["squad"]["slots"]
        for char in slots:
            if char is not None:
                charInstId = str(char["charInstId"])
                if charInstId in chars_data:
                    if dangerLevel in ["-", None]:
                        break
            
                    stageLevel = int(dangerLevel[-2:].replace(".", ""))
                    charLevel = chars_data[charInstId]["level"]
                    evolvePhase = chars_data[charInstId]["evolvePhase"]
            
                    if "精英1" in dangerLevel:
                        if evolvePhase >= 1 and charLevel >= stageLevel:
                            continue
                        else:
                            notifyPowerScoreNotEnoughIfFailed = True
                            break
                    elif "精英2" in dangerLevel:
                        if evolvePhase >= 2 and charLevel >= stageLevel:
                            continue
                        else:
                            notifyPowerScoreNotEnoughIfFailed = True
                            break
                    else:
                        if evolvePhase == 0 and charLevel < stageLevel:
                            notifyPowerScoreNotEnoughIfFailed = True
                            break
    
    if not stageId in player_data['dungeon']['stages']:
        stagesData = {
            "stageId": stageId,
            "completeTimes": 0,
            "startTimes": 0,
            "practiceTimes": 0,
            "state": 0,
            "hasBattleReplay": 0,
            "noCostCnt": 1
        }
        
        if "guide" in stageId:
            stagesData["noCostCnt"] = 0

        player_data['dungeon']['stages'][stageId] = stagesData
    else:
        player_data['dungeon']['stages'][stageId]["startTimes"] += 1
        
    if usePracticeTicket == 1:
        player_data["status"]["practiceTicket"] -= 1
        player_data["dungeon"]["stages"][stageId]["practiceTimes"] += 1
        PassableParameters.PracticeTicket = True
        
    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "apFailReturn": stage_table["apFailReturn"],
        "battleId": str(uuid.uuid1()),
        "inApProtectPeriod": False,
        "isApProtect": 0,
        "notifyPowerScoreNotEnoughIfFailed": notifyPowerScoreNotEnoughIfFailed,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dungeon": {
                    "stages": {
                        stageId: player_data['dungeon']['stages'][stageId]
                    }
                },
                "status": player_data["status"]
            }
        },
        "result": 0
    }
    
    if player_data["dungeon"]["stages"][stageId]["noCostCnt"] == 1:
        data["isApProtect"] = 1
        data["apFailReturn"] = stage_table["apCost"]

    if stage_table["apCost"] == 0 or usePracticeTicket == 1:
        data["isApProtect"] = 0
        data["apFailReturn"] = 0

    return data


def questBattleFinish():

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    CHARWORD_TABLE = updateData(CHARWORD_TABLE_URL, True)
    EQUIP_TABLE = updateData(EQUIP_TABLE_URL, True)
    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    BUILDING_DATA = updateData(BUILDING_DATA_URL, True)
    
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
    BattleData = decrypt_battle_data(request_data["data"], player_data["pushFlags"]["status"])
    dexNav = player_data["dexNav"]
    dropRate = server_config["developer"]["dropRate"] # Drop Rate Multiplier
    stageId = str(base64.b64decode(player_data["status"]["battleId"]), 'utf-8')
    stage_table = STAGE_TABLE["stages"][stageId]
    if server_config["developer"]["debugMode"]:
        writeLog("\033[1;33mBattleData: " + str(BattleData) + "\033[0;0m")
    
    if PassableParameters.PracticeTicket:
        if player_data["dungeon"]["stages"][stageId]["state"] == 0:
            player_data["dungeon"]["stages"][stageId]["state"] = 1
        PassableParameters.PracticeTicket = False
        
        userData.set_user_data(accounts.get_uid(), player_data)

        data = {
            "result": 0,
            "playerDataDelta": {
                "deleted": {},
                "modified": {
                    "dungeon": {
                        "stages": {
                            stageId: player_data["dungeon"]["stages"][stageId]
                        }
                    },
                    "status": player_data["status"]
                }
            }
        }
        return data

    chars = player_data["troop"]["chars"]
    troop = {}
    
    completeState = BattleData["completeState"]
    if server_config["developer"]["debugMode"]:
        completeState = 3

    apCost = stage_table["apCost"]
    expGain = stage_table["expGain"]
    goldGain = stage_table["goldGain"]
    
    goldScale = 1
    expScale = 1
    
    if completeState == 3:
        expGain = int(expGain * 1.2)
        goldGain = int(goldGain * 1.2)
        goldScale = 1.2
        expScale = 1.2
        
    time_now = int(time())
    addAp = int((time_now - int(player_data["status"]["lastApAddTime"])) / 360)
    
    if player_data["status"]["ap"] < player_data["status"]["maxAp"]:
        if (player_data["status"]["ap"] + addAp) >= player_data["status"]["maxAp"]:
            player_data["status"]["ap"] = player_data["status"]["maxAp"]
            player_data["status"]["lastApAddTime"] = time_now
        else:
            if addAp != 0:
                player_data["status"]["ap"] += addAp
                player_data["status"]["lastApAddTime"] = time_now

    player_data["status"]["ap"] -= apCost
    
    # Battle lost
    if completeState == 1:
        apFailReturn = stage_table["apFailReturn"]
        
        if player_data["dungeon"]["stages"][stageId]["noCostCnt"] == 1:
            apFailReturn = stage_table["apCost"]
            player_data["dungeon"]["stages"][stageId]["noCostCnt"] = 0
            
        time_now = int(time())
        addAp = int((player_data["status"]["lastApAddTime"] - time_now) / 360)

        if player_data["status"]["ap"] < player_data["status"]["maxAp"]:
            if (player_data["status"]["ap"] + addAp) >= player_data["status"]["maxAp"]:
                player_data["status"]["ap"] = player_data["status"]["maxAp"]
                player_data["status"]["lastApAddTime"] = time_now
            else:
                player_data["status"]["ap"] += addAp
                player_data["status"]["lastApAddTime"] = time_now
                
        player_data["status"]["ap"] += apFailReturn
        player_data["status"]["lastApAddTime"] = time_now

        userData.set_user_data(accounts.get_uid(), player_data)

        data = {
            "result": 0,
            "additionalRewards": [],
            "alert": [],
            "firstRewards": [],
            "furnitureRewards": [],
            "unlockStages": [],
            "unusualRewards": [],
            "rewards": [],
            "expScale": 0,
            "goldScale": 0,
            "apFailReturn": apFailReturn,
            "suggestFriend": False,
            "playerDataDelta": {
                "deleted": {},
                "modified": {
                    "dungeon": {},
                    "stages": {
                        stageId: player_data["dungeon"]["stages"][stageId]
                    }
                }
            }
        }
        return data
    
    if player_data["dungeon"]["stages"][stageId]["state"] == 0:
        player_data["dungeon"]["stages"][stageId]["state"] = 1
        
    stages_data = player_data["dungeon"]["stages"][stageId]
    unlockStages = []
    unlockStagesObject = []
    additionalRewards = []
    unusualRewards = []
    furnitureRewards = []
    firstRewards = []
    rewards = []

    # First time 3 stars pass
    FirstClear = False
    if stages_data["state"] != 3 and completeState == 3:
        FirstClear = True
        
    # First time 4 stars pass
    if stages_data["state"] == 3 and completeState == 4:
        FirstClear = True
        
    if stages_data["state"] == 1:
        if completeState == 3 or completeState == 2:
            # For sword Amiya
            if stageId == "main_08-16":
                for char_id, char_data in player_data["troop"]["chars"].items():
                    if char_data["charId"] == "char_002_amiya":
                        amiya_skills = char_data["skills"]
                        amiya_skin = char_data["skin"]
                        amiya_default_skill_index = char_data["defaultSkillIndex"]
                        char_data["skin"] = None
                        char_data["defaultSkillIndex"] = -1
                        char_data["skills"] = []
                        char_data["currentTmpl"] = "char_1001_amiya2"
                        tmpl = {}
                        amiya = {
                            "skinId": amiya_skin,
                            "defaultSkillIndex": amiya_default_skill_index,
                            "skills": amiya_skills,
                            "currentEquip": None,
                            "equip": {}
                        }
                        tmpl["char_002_amiya"] = amiya
                        sword_amiya_skills = []
                        skchr_amiya2_1 = {
                            "skillId": "skchr_amiya2_1",
                            "unlock": 1,
                            "state": 0,
                            "specializeLevel": 0,
                            "completeUpgradeTime": -1
                        }
                        sword_amiya_skills.append(skchr_amiya2_1)
                        skchr_amiya2_2 = {
                            "skillId": "skchr_amiya2_1",
                            "unlock": 1,
                            "state": 0,
                            "specializeLevel": 0,
                            "completeUpgradeTime": -1
                        }
                        sword_amiya_skills.append(skchr_amiya2_2)
                        sword_amiya = {
                            "skinId": "char_1001_amiya2#2",
                            "defaultSkillIndex": 0,
                            "skills": sword_amiya_skills,
                            "currentEquip": None,
                            "equip": {}
                        }
                        tmpl["char_1001_amiya2"] = sword_amiya
                        char_data["tmpl"] = tmpl
                        charinstId = {
                            char_id: char_data
                        }
                        troop["chars"] = charinstId
                        player_data["troop"]["chars"][char_id] = char_data
                        break
                    
            # Unlock recruit
            if stageId == "main_00-02":
                for item in [0, 1]:
                    player_data["recruit"]["normal"]["slots"][str(item)]["state"] = 1

            # Unlock stage
            unlock_list = {}
            stage_data = STAGE_TABLE["stages"]
            for item in list(stage_data.keys()):
                unlock_list[item] = stage_data[item]["unlockCondition"]

            for item in list(unlock_list.keys()):
                pass_condition = 0
                if len(unlock_list[item]) == 0:
                    stage_list = read_json(STAGE_JSON_PATH, encoding='utf-8')
                    unlock_list[item] = stage_list[item]
                if len(unlock_list[item]) != 0:
                    for condition in unlock_list[item]:
                        if condition["stageId"] in player_data["dungeon"]["stages"]:
                            if player_data["dungeon"]["stages"][condition["stageId"]]["state"] >= condition["completeState"]:
                                pass_condition += 1
                        if stageId == condition["stageId"]:
                            if completeState >= condition["completeState"]:
                                pass_condition += 1
                    if pass_condition == len(unlock_list[item]):
                        
                        unlockStage = {
                            "stageId": item,
                            "practiceTimes": 0,
                            "completeTimes": 0,
                            "startTimes": 0,
                            "state": 0,
                            "hasBattleReplay": 0,
                            "noCostCnt": 1
                        }
                            
                        for chr in ["#f#", "hard_", "tr_"]:
                            if chr in item:
                                unlockStage["noCostCnt"] = 0
                            
                        if item not in player_data["dungeon"]["stages"]:
                            if stage_table["stageType"] in ["MAIN", "SUB"]:
                                if stage_data[item]["stageType"] in ["MAIN", "SUB"]:
                                    player_data["status"]["mainStageProgress"] = item
                            player_data["dungeon"]["stages"][item] = unlockStage
                            unlockStages.append(item)
                            unlockStagesObject.append(unlockStage)
    
    if FirstClear:
        # First drops
        if server_config["developer"]["debugMode"]:
            writeLog("- First Drops: FirstClear -")
        displayDetailRewards = stage_table["stageDropInfo"]["displayDetailRewards"]
        for index in range(len(displayDetailRewards)):
            dropType = displayDetailRewards[index]["dropType"]
            reward_count = 1 * dropRate
            reward_id = displayDetailRewards[index]["id"]
            reward_type = displayDetailRewards[index]["type"]

            if dropType in [1, 8]:
                if reward_type == "CHAR":
                    charGet = {}
                    random_char_id = reward_id
                    repeatCharId = 0
                    
                    for n in range(len(player_data["troop"]["chars"])):
                        if player_data["troop"]["chars"][str(n + 1)]["charId"] == random_char_id:
                            repeatCharId = n + 1
                            break

                    if repeatCharId == 0:
                        # Add new character
                        get_char = {}
                        char_data = {}
                        skills_array = CHARACTER_TABLE[random_char_id]["skills"]
                        skills = []
                        
                        for m in range(len(skills_array)):
                            new_skills = {
                                "skillId": skills_array[m]["skillId"],
                                "state": 0,
                                "specializeLevel": 0,
                                "completeUpgradeTime": -1
                            }
                            if skills_array[m]["unlockCond"]["phase"] == 0:
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
                        charGet = get_char

                        charinstId = {
                            str(instId): char_data
                        }
                        chars[str(instId)] = char_data
                        troop["chars"] = charinstId
                    else:
                        # Already has this character
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
            
                        player_data["status"][itemName] += itemCount

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

                        charGet = get_char

                        charinstId = {
                            str(repeatCharId): player_data["troop"]["chars"][str(repeatCharId)]
                        }
                        chars[str(repeatCharId)] = player_data["troop"]["chars"][str(repeatCharId)]
                        troop["chars"] = charinstId
                        
                    # Unlock character dexNav
                    characterList = list(dexNav["character"].keys())
                    if random_char_id not in characterList:
                        dexNav["character"][random_char_id] = {
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
                                    dexNav["teamV2"][team].update({str(instId): 1})
                                except:
                                    dexNav["teamV2"][team] = {str(instId): 1}
                    else:
                        dexNav["character"][random_char_id]["count"] += 1
                        
                    first_reward = {
                        "count": 1,
                        "id": reward_id,
                        "type": reward_type,
                        "charGet": charGet
                    }
                    firstRewards.append(first_reward)
                else:
                    if reward_type == "MATERIAL":
                        try:
                            player_data["inventory"][reward_id] += reward_count
                        except:
                            player_data["inventory"][reward_id] = reward_count
                    if reward_type == "CARD_EXP":
                        try:
                            player_data["inventory"][reward_id] += reward_count
                        except:
                            player_data["inventory"][reward_id] = reward_count
                    if reward_type == "DIAMOND":
                        player_data["status"]["androidDiamond"] += reward_count
                        player_data["status"]["iosDiamond"] += reward_count
                    if reward_type == "GOLD":
                        player_data["status"]["gold"] += reward_count
                    if reward_type == "TKT_RECRUIT":
                        player_data["status"]["recruitLicense"] += reward_count
                    if reward_type == "FURN":
                        if reward_id not in player_data["building"]["furniture"]:
                            furniture = {
                                "count": 1,
                                "inUse": 0
                            }
                            player_data["building"]["furniture"][reward_id] = furniture
                        player_data["building"]["furniture"][reward_id]["count"] += 1
                    first_reward = {
                        "count": reward_count,
                        "id": reward_id,
                        "type": reward_type
                    }
                    firstRewards.append(first_reward)

    if player_data["dungeon"]["stages"][stageId]["state"] != 3:
        player_data["dungeon"]["stages"][stageId]["state"] = completeState

    if completeState == 4:
        player_data["dungeon"]["stages"][stageId]["state"] = completeState

    player_data["dungeon"]["stages"][stageId]["completeTimes"] += 1

    player_exp_map = [
        500,800,1240,1320,
        1400,1480,1560,1640,
        1720,1800,1880,1960,
        2040,2120,2200,2280,
        2360,2440,2520,2600,
        2680,2760,2840,2920,
        3000,3080,3160,3240,
        3350,3460,3570,3680,
        3790,3900,4200,4500,
        4800,5100,5400,5700,
        6000,6300,6600,6900,
        7200,7500,7800,8100,
        8400,8700,9000,9500,
        10000,10500,11000,11500,
        12000,12500,13000,13500,
        14000,14500,15000,15500,
        16000,17000,18000,19000,
        20000,21000,22000,23000,
        24000,25000,26000,27000,
        28000,29000,30000,31000,
        32000,33000,34000,35000,
        36000,37000,38000,39000,
        40000,41000,42000,43000,
        44000,45000,46000,47000,
        48000,49000,50000,51000,
        52000,54000,56000,58000,
        60000,62000,64000,66000,
        68000,70000,73000,76000,
        79000,82000,85000,88000,
        91000,94000,97000,100000
    ]
    player_ap_map = [
        82,84,86,88,
        90,91,92,93,
        94,95,96,97,
        98,99,100,101,
        102,103,104,105,
        106,107,108,109,
        110,111,112,113,
        114,115,116,117,
        118,119,120,120,
        120,120,120,121,
        121,121,121,121,
        122,122,122,122,
        122,123,123,123,
        123,123,124,124,
        124,124,124,125,
        125,125,125,125,
        126,126,126,126,
        126,127,127,127,
        127,127,128,128,
        128,128,128,129,
        129,129,129,129,
        130,130,130,130,
        130,130,130,130,
        130,130,130,130,
        130,130,130,130,
        131,131,131,131,
        132,132,132,132,
        133,133,133,133,
        134,134,134,134,
        135,135,135,135
    ]
    gold = player_data["status"]["gold"]
    exp = player_data["status"]["exp"]
    level = player_data["status"]["level"]
    
    # LMD drops
    SpecialGold = {
        "main_01-01": 660,      # 1-1
        "main_02-07": 1500,     # 2-7
        "main_03-06": 2040,     # 3-6
        "main_04-01": 2700,     # 4-1
        "main_06-01": 1216,     # 6-1
        "main_07-02": 1216,     # 7-3
        "main_08-01": 2700,     # R8-1
        "main_08-04": 1216,     # R8-4
        "main_09-01": 2700,     # Standard 9-2
        "main_09-02": 1216,     # Standard 9-3
        "main_10-07": 3480,     # Standard 10-8
        "tough_10-07": 3480,    # Adverse 10-8
        "main_11-08": 3480,     # Standard 11-9
        "tough_11-08": 3480,    # Adverse 11-9
        "sub_02-02": 1020,      # S2-2
        "sub_04-2-3": 3480,     # S4-6
        "sub_05-1-2": 2700,     # S5-2
        "sub_05-2-1": 1216,     # S5-3
        "sub_05-3-1": 1216,     # S5-5
        "sub_06-1-2": 1216,     # S6-2
        "sub_06-2-2": 2700,     # S6-4
        "sub_07-1-1": 2700,     # S7-1
        "sub_07-1-2": 1216,     # S7-2
        "act18d0_05": 1644,     # WD-5
        "act17side_03": 1128,   # SN-3
        "act5d0_01": 1000,      # CB-1
        "act5d0_03": 1000,      # CB-3
        "act5d0_05": 2000,      # CB-5
        "act5d0_07": 2000,      # CB-7
        "act5d0_09": 3000,      # CB-9
        "act11d0_04": 1644,     # TW-4
        "act16d5_04": 1644,     # WR-4
    }
    if goldGain != 0 and stageId not in SpecialGold:
        # Cargo Escort - LMD
        if "wk_melee" in stageId:
            goldGain = round(goldGain, -2)
        player_data["status"]["gold"] = gold + goldGain
        rewards_gold = {
            "count": goldGain,
            "id": "4001",
            "type": "GOLD"
        }
        rewards.append(rewards_gold)

    # Exp drops & Level Up
    if level < 120 and expGain != 0:
        player_data["status"]["exp"] = exp + expGain
        for index in range(len(player_exp_map)):
            if level == index + 1:
                if (int(player_exp_map[index]) - player_data["status"]["exp"]) <= 0:
                    if (index + 2) == 120:
                        player_data["status"]["level"] = 120
                        player_data["status"]["exp"] = 0
                        player_data["status"]["maxAp"] = player_ap_map[index + 1]
                        player_data["status"]["ap"] += player_data["status"]["maxAp"]
                    else:
                        player_data["status"]["level"] = (index + 2)
                        player_data["status"]["exp"] -= int(player_exp_map[index])
                        player_data["status"]["maxAp"] = player_ap_map[index + 1]
                        player_data["status"]["ap"] += player_data["status"]["maxAp"]
                    player_data["status"]["lastApAddTime"] = int(time())
                break
        
    # Drops reward
    displayDetailRewards = stage_table["stageDropInfo"]["displayDetailRewards"]
    
    for index in range(len(displayDetailRewards)):
        occPercent = displayDetailRewards[index]["occPercent"]
        dropType = displayDetailRewards[index]["dropType"]
        reward_count = 1 * dropRate

        reward_id = displayDetailRewards[index]["id"]
        reward_type = displayDetailRewards[index]["type"]

        reward_rarity = 0
        percent = 0
        addPercent = 0

        if completeState == 3:
            if reward_type not in ["CHAR"]:
                if reward_type == "FURN":
                    reward_rarity = BUILDING_DATA["customData"]["furnitures"][reward_id]["rarity"]
                    if server_config["developer"]["debugMode"]:
                        writeLog(BUILDING_DATA["customData"]["furnitures"][reward_id])
                else:
                    reward_rarity = ITEM_TABLE["items"][reward_id]["rarity"]
                    if server_config["developer"]["debugMode"]:
                        writeLog(ITEM_TABLE["items"][reward_id])
                        
                if reward_rarity == 0:
                    drop_array = []

                    for n in range(70):
                        drop_array.append(0)
                    for n in range(20):
                        drop_array.append(1)
                    for n in range(10):
                        drop_array.append(2)

                    random.shuffle(drop_array)

                    random_num = random.choice(drop_array)
                    reward_count += random_num
                    percent = 10
                    addPercent = 0
                    
                if reward_rarity == 1:
                    drop_array = []

                    for n in range(70):
                        drop_array.append(0)
                    for n in range(10):
                        drop_array.append(1)
                    for n in range(5):
                        drop_array.append(2)

                    random.shuffle(drop_array)

                    random_num = random.choice(drop_array)
                    reward_count += random_num
                    percent = 5
                    addPercent = 0
                elif reward_rarity == 2:
                    percent = 0
                    addPercent = 110
                elif reward_rarity == 3:
                    percent = 0
                    addPercent = 120
                elif reward_rarity == 4:
                    percent = 0
                    addPercent = 130

        if completeState == 2:
            if reward_type not in ["FURN", "CHAR"]:
                reward_rarity = ITEM_TABLE["items"][reward_id]["rarity"]
                if reward_rarity == 0:
                    drop_array = []

                    for n in range(90 + percent):
                        drop_array.append(0)
                    for n in range(12 + percent):
                        drop_array.append(1)
                    for n in range(8 + addPercent):
                        drop_array.append(2)

                    random.shuffle(drop_array)

                    random_num = random.choice(drop_array)
                    reward_count += random_num
                    percent = 0
                    addPercent = 0

                if reward_rarity == 1:
                    drop_array = []

                    for n in range(110 + percent):
                        drop_array.append(0)
                    for n in range(8 + percent):
                        drop_array.append(1)
                    for n in range(2 + addPercent):
                        drop_array.append(2)

                    random.shuffle(drop_array)

                    random_num = random.choice(drop_array)
                    reward_count += random_num
                    percent = 0
                    addPercent = 0
                elif reward_rarity == 2:
                    percent = 0
                    addPercent = 120
                elif reward_rarity == 3:
                    percent = 0
                    addPercent = 140
                elif reward_rarity == 4:
                    percent = 0
                    addPercent = 160

        # Regular Drops: Guaranteed
        if occPercent == 0 and dropType == 2:
            if server_config["developer"]["debugMode"]:
                writeLog("- Regular Drops: Guaranteed -")
            if reward_type == "MATERIAL":
                random_value = random.choice([1, 0, -1])
                # Tough Siege - Purchase Certificate
                ToughSiege = {
                    "wk_toxic_1": 5,
                    "wk_toxic_2": 8,
                    "wk_toxic_3": 11,
                    "wk_toxic_4": 15,
                    "wk_toxic_5": 21
                }
                if stageId in ToughSiege:
                    if completeState == 3:
                        reward_count = ToughSiege[stageId] + random_value
                    else:
                        reward_count = round(ToughSiege[stageId] / (2 * 1.2))
                # Aerial Threat - Skill Summary
                AerialThreat = {
                    "wk_fly_1": [3, 0, 0],
                    "wk_fly_2": [5, 0, 0],
                    "wk_fly_3": [1, 3, 0],
                    "wk_fly_4": [1, 1, 2],
                    "wk_fly_5": [0, 2, 3]
                }
                if stageId in AerialThreat:
                    for i, j in enumerate(AerialThreat[stageId]):
                        if j == 0:
                            continue
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = j
                        else:
                            reward_count = round(j / (1.5 * 1.2))
                # Resource Search - Carbon
                ResourceSearch = {
                    "wk_armor_1": [1, 1, 2],
                    "wk_armor_2": [1, 3, 4],
                    "wk_armor_3": [0, 3, 5],
                    "wk_armor_4": [0, 7, 2],
                    "wk_armor_5": [0, 10, 3]
                }
                if stageId in ResourceSearch:
                    for i, j in enumerate(ResourceSearch[stageId]):
                        if j == 0:
                            continue
                        if int(stageId[-1]) > 3 and reward_id == "3113":
                            continue
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = j
                                if reward_id != "3401":
                                    reward_count = ResourceSearch[stageId][-1]
                        else:
                            if reward_id != "3401":
                                j = ResourceSearch[stageId][-1]
                            reward_count = round(j / (1.5 * 1.2))
                try:
                    player_data["inventory"][reward_id] += reward_count
                except:
                    player_data["inventory"][reward_id] = reward_count
            if reward_type == "CARD_EXP":
                # Tactical Drill - Card EXP
                random_value = random.choice([1, 0])
                TacticalDrill = {
                    "wk_kc_1": [2, 3, 0, 0],
                    "wk_kc_2": [4, 5, 0, 0],
                    "wk_kc_3": [3, 2, 3, 0],
                    "wk_kc_4": [2, 4, 2, 1],
                    "wk_kc_5": [0, 1, 1, 3],
                    "wk_kc_6": [0, 0, 2, 4],
                    "sub_02-03": [6 + random_value, 0, 0, 0],
                    "main_00-10": [4 + random_value, 0, 0, 0],
                    "main_03-05": [0, 5, 0, 0],
                    "sub_02-10": [0, 4, 0, 0],
                    "main_04-03": [0, 0, 2 + random_value, 0],
                    "main_07-11": [0, 0, 2 + random_value, 0],
                    "main_08-06": [0, 0, 2 + random_value, 0],
                    "sub_06-1-1": [0, 0, 2 + random_value, 0],
                    "main_09-09": [0, 0, 2 + random_value, 0],
                    "main_10-01": [0, 0, 3 + random_value, 0],
                    "tough_10-01": [0, 0, 3 + random_value, 0],
                    "main_11-01": [0, 0, 3 + random_value, 0],
                    "tough_11-01": [0, 0, 3 + random_value, 0],
                    "sub_04-3-3": [0, 0, 3 + random_value, 0],
                    "sub_05-3-2": [0, 0, 2 + random_value, 0]
                }
                if stageId in TacticalDrill:
                    for i, j in enumerate(TacticalDrill[stageId]):
                        if j == 0:
                            continue
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = j
                        else:
                            reward_count = round(j / (1.5 * 1.2))
                try:
                    player_data["inventory"][reward_id] += reward_count
                except:
                    player_data["inventory"][reward_id] = reward_count
            if reward_type == "DIAMOND":
                player_data["status"]["androidDiamond"] +=  reward_count
                player_data["status"]["iosDiamond"] +=  reward_count
            if reward_type == "TKT_RECRUIT":
                player_data["status"]["recruitLicense"] += reward_count

            if reward_type == "GOLD":
                if stageId in SpecialGold:
                    if completeState == 3:
                        reward_count = SpecialGold[stageId]
                    else:
                        reward_count = round(SpecialGold[stageId] / 1.2)
                        
                player_data["status"]["gold"] += reward_count

            normal_reward = {
                "count": reward_count,
                "id": reward_id,
                "type": reward_type
            }
            rewards.append(normal_reward)
            
        # Regular Drops: Common
        if occPercent == 1 and dropType == 2:
            if server_config["developer"]["debugMode"]:
                writeLog("- Regular Drops: Common -")
            drop_array = []
            
            for n in range(80 + percent):
                drop_array.append(1)
            for n in range(20 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                    
                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                rewards.append(normal_reward)
                
        # Regular Drops: Uncommon
        if occPercent == 2 and dropType == 2:
            if server_config["developer"]["debugMode"]:
                writeLog("- Regular Drops: Uncommon -")
            if "pro_" in stageId:
                drop_array = []
                
                for n in range(5):
                    drop_array.append(1)
                for n in range(5):
                    drop_array.append(0)

                random.shuffle(drop_array)
                
                cur = random.choice(drop_array)
                reward_id = displayDetailRewards[cur]["id"]
                reward_type = displayDetailRewards[cur]["type"]

                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count

                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                rewards.append(normal_reward)

                break
            
            drop_array = []
            
            for n in range(50 + percent):
                drop_array.append(1)
            for n in range(50 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count

                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                rewards.append(normal_reward)

        # Regular Drops: Rare
        if occPercent == 3 and dropType == 2:
            if server_config["developer"]["debugMode"]:
                writeLog("- Regular Drops: Rare -")
            drop_array = []

            for n in range(15 + percent):
                drop_array.append(1)
            for n in range(90 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                if reward_type == "FURN":
                    if reward_id not in player_data["building"]["furniture"]:
                        furniture = {
                            "count": 1,
                            "inUse": 0
                        }
                        player_data["building"]["furniture"][reward_id] = furniture
                    player_data["building"]["furniture"][reward_id]["count"] += 1

                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                if reward_type != "FURN":
                    rewards.append(normal_reward)
                else:
                    furnitureRewards.append(normal_reward)

        # Regular Drops: Very Rare
        if occPercent == 4 and dropType == 2:
            if server_config["developer"]["debugMode"]:
                writeLog("- Regular Drops: Very Rare -")
            drop_array = []
            
            for n in range(10 + percent):
                drop_array.append(1)
            for n in range(90 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                if reward_type == "FURN":
                    if reward_id not in player_data["building"]["furniture"]:
                        furniture = {
                            "count": 1,
                            "inUse": 0
                        }
                        player_data["building"]["furniture"][reward_id] = furniture
                    player_data["building"]["furniture"][reward_id]["count"] += 1

                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                if reward_type != "FURN":
                    rewards.append(normal_reward)
                else:
                    furnitureRewards.append(normal_reward)

        # Special Drops: Guaranteed
        if occPercent == 0 and dropType == 3:
            if server_config["developer"]["debugMode"]:
                writeLog("- Special Drops: Guaranteed -")
            if reward_type == "MATERIAL":
                try:
                    player_data["inventory"][reward_id] += reward_count
                except:
                    player_data["inventory"][reward_id] = reward_count
            if reward_type == "CARD_EXP":
                try:
                    player_data["inventory"][reward_id] += reward_count
                except:
                    player_data["inventory"][reward_id] = reward_count
            if reward_type == "DIAMOND":
                player_data["status"]["androidDiamond"] += reward_count
                player_data["status"]["iosDiamond"] += reward_count
            if reward_type == "GOLD":
                player_data["status"]["gold"] += reward_count
            if reward_type == "TKT_RECRUIT":
                player_data["status"]["recruitLicense"] += reward_count

            normal_reward = {
                "count": reward_count,
                "id": reward_id,
                "type": reward_type
            }

            unusualRewards.append(normal_reward)
            
        # Special Drops: Rare
        if occPercent == 3 and dropType == 3:
            if server_config["developer"]["debugMode"]:
                writeLog("- Special Drops: Rare -")
            drop_array = []
            
            for n in range(5 + percent):
                drop_array.append(1)
            for n in range(95 + addPercent):
                drop_array.append(0)
                
            random.shuffle(drop_array)
            
            cur = random.choice(drop_array)
            
            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count

                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                unusualRewards.append(normal_reward)
        
        # Special Drops: Very Rare
        if occPercent == 4 and dropType == 3:
            if server_config["developer"]["debugMode"]:
                writeLog("- Special Drops: Very Rare -")
            drop_array = []

            for n in range(5 + percent):
                drop_array.append(1)
            for n in range(95 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                    
                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                unusualRewards.append(normal_reward)

        # Extra Drops: Rare
        if occPercent == 4 and dropType == 4:
            if server_config["developer"]["debugMode"]:
                writeLog("- Extra Drops: Rare -")
            drop_array = []

            for n in range(25 + percent):
                drop_array.append(1)
            for n in range(75 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                    
                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                additionalRewards.append(normal_reward)
        
        # Extra Drops: Very Rare
        if occPercent == 3 and dropType == 4:
            if server_config["developer"]["debugMode"]:
                writeLog("- Extra Drops: Very Rare -")
            drop_array = []
            
            for n in range(5 + percent):
                drop_array.append(1)
            for n in range(95 + addPercent):
                drop_array.append(0)

            random.shuffle(drop_array)

            cur = random.choice(drop_array)

            if cur == 1:
                if reward_type == "MATERIAL":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "CARD_EXP":
                    try:
                        player_data["inventory"][reward_id] += reward_count
                    except:
                        player_data["inventory"][reward_id] = reward_count
                if reward_type == "DIAMOND":
                    player_data["status"]["androidDiamond"] += reward_count
                    player_data["status"]["iosDiamond"] += reward_count
                if reward_type == "GOLD":
                    player_data["status"]["gold"] += reward_count
                if reward_type == "TKT_RECRUIT":
                    player_data["status"]["recruitLicense"] += reward_count
                    
                normal_reward = {
                    "count": reward_count,
                    "id": reward_id,
                    "type": reward_type
                }
                
                additionalRewards.append(normal_reward)
                
    # Character trust improvement
    completeFavor = stage_table["completeFavor"]
    passFavor = stage_table["passFavor"]

    charList = BattleData["battleData"]["stats"]["charList"]
    
    for inst_id in list(charList.keys()):
        if inst_id in player_data["troop"]["chars"]:
            charData = player_data["troop"]["chars"][inst_id]
            charId = charData["charId"]
            charFavor = charData["favorPoint"]

            if completeState in [3, 4]:
                charData["favorPoint"] = charFavor + completeFavor
                if charId in player_data["troop"]["charGroup"]:
                    player_data["troop"]["charGroup"][charId]["favorPoint"] = charFavor + completeFavor
            else:
                charData["favorPoint"] = charFavor + passFavor
                if charId in player_data["troop"]["charGroup"]:
                    player_data["troop"]["charGroup"][charId]["favorPoint"] = charFavor + passFavor
    
    # Unlock enemy dexNav
    enemyList = list(BattleData["battleData"]["stats"]["enemyList"].keys())
    for enemyId in enemyList:
        if enemyId not in dexNav["enemy"]["enemies"]:
            dexNav["enemy"]["enemies"].update({enemyId: 1})
            
    stages = {}
    for index in range(len(unlockStagesObject)):
        unlock_stageId = unlockStagesObject[index]["stageId"]
        stages[unlock_stageId] = player_data["dungeon"]["stages"][unlock_stageId]
    stages[stageId] = player_data["dungeon"]["stages"][stageId]

    data = {
        "result": 0,
        "apFailReturn": 0,
        "goldScale": goldScale,
        "expScale": expScale,
        "rewards": rewards,
        "firstRewards": firstRewards,
        "unlockStages": unlockStages,
        "unusualRewards": unusualRewards,
        "additionalRewards": additionalRewards,
        "furnitureRewards": furnitureRewards,
        "alert": [],
        "suggestFriend": PassableParameters.suggestFriend,
        "pryResult": [],
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dexNav": dexNav,
                "dungeon": {
                    "stages": stages
                },
                "status": player_data["status"],
                "troop": troop,
                "inventory": player_data["inventory"],
            }
        }
    }

    userData.set_user_data(accounts.get_uid(), player_data)

    return data


def questSaveBattleReplay():

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    battleReplay = decrypt_battle_replay(request_data["battleReplay"])
    server_config = read_json(CONFIG_PATH)
    if server_config["developer"]["debugMode"]:
        writeLog("\033[1;33mBattleReplay: " + str(battleReplay) + "\033[0;0m")
    
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
    stageId = battleReplay["journal"]["metadata"]["stageId"]
    stages_data = player_data["dungeon"]["stages"][stageId]
    
    stages_data["hasBattleReplay"] = 1
    stages_data["battleReplay"] = request_data["battleReplay"]

    userData.set_user_data(accounts.get_uid(), player_data)


    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dungeon": {
                    "stages": {
                        stageId: player_data["dungeon"]["stages"][stageId]
                    }
                }
            }
        }
    }

    return data


def questGetBattleReplay():

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    stageId = request_data["stageId"]
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
    
    data = {
        "battleReplay": player_data["dungeon"]["stages"][stageId]["battleReplay"],
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }
    
    return data


def questChangeSquadName():

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    squadId = request_data["squadId"]
    name = request_data["name"]
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
    player_data["troop"]["squads"][squadId]["name"] = name

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta":{
            "deleted":{},
            "modified":{
                "troop":{
                    "squads":{
                        squadId: player_data["troop"]["squads"][squadId]
                    }
                }
            }
        }
    }

    return data


def questSquadFormation():

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    squadId = request_data["squadId"]
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
    player_data["troop"]["squads"][str(squadId)]["slots"] = request_data["slots"]

    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "playerDataDelta":{
            "deleted":{},
            "modified":{
                "troop":{
                    "squads":{
                        squadId: player_data["troop"]["squads"][str(squadId)]
                    }
                }
            }
        }
    }

    return data


def questGetAssistList():

    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    profession = request_data["profession"]
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
    
    friend_list = json.loads(accounts.get_friend())["list"]
    assist_char_array = []
    assistList = []
    friend_array = []
    
    random.shuffle(friend_list)

    for index in range(len(friend_list)):
        if len(assistList) == 6:
            break
        
        friendUid = str(friend_list[index]["uid"])
        friendAlias = friend_list[index]["alias"]
        
        friend_array.append(friendUid)
        
        result = userData.query_user_info(friendUid)
        userInfo = UserInfo(*result[0])

        userSocialAssistCharList = json.loads(userInfo.get_social_assist_char_list())
        userAssistCharList = json.loads(userInfo.get_assist_char_list())
        userStatus = json.loads(userInfo.get_status())
        chars = json.loads(userInfo.get_chars())

        if profession in userAssistCharList:
            charList = userAssistCharList[profession]
            random.shuffle(charList)
            assistCharData = charList[0]

            charId = assistCharData["charId"]
            charInstId = assistCharData["charInstId"]
            
            if charId not in assist_char_array:
                assist_char_array.append(charId)

                assistCharList = []

                assistInfo = {
                    "aliasName": friendAlias,
                    "assistCharList": [],
                    "assistSlotIndex": 0,
                    "avatar": userStatus["avatar"],
                    "avatarId": userStatus["avatarId"],
                    "canRequestFriend": False,
                    "isFriend": True,
                    "lastOnlineTime": userStatus["lastOnlineTs"],
                    "level": userStatus["level"],
                    "nickName": userStatus["nickName"],
                    "nickNumber": userStatus["nickNumber"],
                    "powerScore": 200, # TODO: Set the correct data
                    "uid": friendUid,
                }
                
                for char in range(len(userSocialAssistCharList)):
                    if userSocialAssistCharList[char] is not None:
                        charData = chars[str(userSocialAssistCharList[char]["charInstId"])]
                        charData["skillIndex"] = userSocialAssistCharList[char]["skillIndex"]
                        if "skinId" not in charData:
                            charData["skinId"] = charData["skin"]
                        charData["crisisRecord"] = {} # TODO: Set the correct data
                        assistCharList.append(charData)
                        if userSocialAssistCharList[char]["charInstId"] == charInstId:
                            assistInfo["assistSlotIndex"] = char
                    assistInfo["assistCharList"] = assistCharList
                    
                    if assistInfo not in assistList:
                        assistList.append(assistInfo)
                    
    result = userData.search_assist_char_list(f"$.{profession}")
    search_array = []
    
    if len(result) != 0:
        for index in range(len(result)):
            searchAssist = SearchAssistCharList(*result[index])
            if searchAssist.get_uid() == accounts.get_uid() or str(searchAssist.get_uid()) in friend_array:
                searchAssist.set_uid(-1)
            search_array.append({"tmp": searchAssist})
            
    random.shuffle(search_array)

    for item in search_array:
        searchAssist = item["tmp"]
        friendUid = searchAssist.get_uid()
        
        if friendUid != -1:
            if len(assistList) == 9:
                break
            
            userSocialAssistCharList = json.loads(searchAssist.get_social_assist_char_list())
            charList = json.loads(searchAssist.get_assist_char_list())
            userStatus = json.loads(searchAssist.get_status())
            chars = json.loads(searchAssist.get_chars())
            
            random.shuffle(charList)

            assistCharData = charList[0]
            charId = assistCharData["charId"]
            charInstId = assistCharData["charInstId"]

            if charId not in assist_char_array:
                assist_char_array.append(charId)
                assistCharList = []
                
                assistInfo = {
                    "aliasName": None,
                    "assistCharList": [],
                    "assistSlotIndex": 0,
                    "avatar": userStatus["avatar"],
                    "avatarId": userStatus["avatarId"],
                    "canRequestFriend": True,
                    "isFriend": False,
                    "lastOnlineTime": userStatus["lastOnlineTs"],
                    "level": userStatus["level"],
                    "nickName": userStatus["nickName"],
                    "nickNumber": userStatus["nickNumber"],
                    "powerScore": 200, # TODO: Set the correct data
                    "uid": friendUid,
                }
                
                for index in range(len(userSocialAssistCharList)):
                    if userSocialAssistCharList[index] is not None:
                        charData = chars[str(userSocialAssistCharList[index]["charInstId"])]
                        charData["skillIndex"] = userSocialAssistCharList[index]["skillIndex"]
                        if "skinId" not in charData:
                            charData["skinId"] = charData["skin"]
                        charData["crisisRecord"] = {} # TODO: Set the correct data
                        assistCharList.append(charData)
                        if userSocialAssistCharList[index]["charInstId"] == charInstId:
                            assistInfo["assistSlotIndex"] = index
                    assistInfo["assistCharList"] = assistCharList
                    
                    if assistInfo not in assistList:
                        assistList.append(assistInfo)

    data = {
        "allowAskTs": int(time()) + 3,
        "assistList": assistList,
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data


def questFinishStoryStage():
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    stageId = request_data["stageId"]
    server_config = read_json(CONFIG_PATH)

    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)
    
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
    stage_state = player_data["dungeon"]["stages"][stageId]["state"]
    dropRate = server_config["developer"]["dropRate"]

    rewards = []
    unlockStages = []
    unlockStagesObject = []

    if stage_state != 3:
        player_data["dungeon"]["stages"][stageId]["state"] = 3


        unlock_list = {}
        stage_data = STAGE_TABLE["stages"]
        for item in list(stage_data.keys()):
            unlock_list[item] = stage_data[item]["unlockCondition"]

        for item in list(unlock_list.keys()):
            pass_condition = 0
            if len(unlock_list[item]) == 0:
                    stage_list = read_json(STAGE_JSON_PATH, encoding='utf-8')
                    unlock_list[item] = stage_list[item]
            if len(unlock_list[item]) != 0:
                for condition in unlock_list[item]:
                    if condition["stageId"] in list(player_data["dungeon"]["stages"].keys()):
                        if player_data["dungeon"]["stages"][condition["stageId"]]["state"] >= condition["completeState"]:
                            pass_condition += 1
                if pass_condition == len(unlock_list[item]):
                        
                    unlockStage = {
                        "hasBattleReplay": 0,
                        "noCostCnt": 0,
                        "practiceTimes": 0,
                        "completeTimes": 0,
                        "state": 0,
                        "stageId": item,
                        "startTimes": 0
                    }
                            
                    if item not in player_data["dungeon"]["stages"]:
                        player_data["dungeon"]["stages"][item] = unlockStage
                        unlockStages.append(item)
                        unlockStagesObject.append(unlockStage)
                        
        reward = {
            "type": "DIAMOND",
            "id": "4002",
            "count": 1 * dropRate
        }

        rewards.append(reward)

        player_data["status"]["androidDiamond"] += 1 * dropRate
        player_data["status"]["iosDiamond"] += 1 * dropRate

    stages = {}
    for index in range(len(unlockStagesObject)):
        unlock_stageId = unlockStagesObject[index]["stageId"]
        stages[unlock_stageId] = player_data["dungeon"]["stages"][unlock_stageId]
    stages[stageId] = player_data["dungeon"]["stages"][stageId]
    
    data = {
        "result": 0,
        "alert": [],
        "rewards": rewards,
        "unlockStages": unlockStages,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dungeon": {
                    "stages": stages
                },
                "status": {
                    "androidDiamond": player_data["status"]["androidDiamond"],
                    "iosDiamond": player_data["status"]["iosDiamond"]
                }
            }
        }
    }
    
    userData.set_user_data(accounts.get_uid(), player_data)
    
    return data