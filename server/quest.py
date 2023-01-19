import json
import random
import uuid
from time import time
from typing import Dict, List, Tuple

from flask import Response, abort, request

from constants import (BUILDING_DATA_URL, CONFIG_PATH, ITEM_TABLE_URL,
                       STAGE_JSON_PATH, STAGE_TABLE_URL)
from core.Account import Account, UserInfo
from core.database import userData
from core.function.giveItem import giveItems
from core.function.update import updateData
from core.Search import SearchAssistCharList
from logger import writeLog
from utils import decrypt_battle_data, decrypt_battle_replay, read_json


class TemporaryData:

    battleInfo_list = {}


class BattleInfo:
    def __init__(self, stage_id: str, ts: int, battle_info: Dict,
                 practice_ticket: bool = False, suggest_friend: bool = False):
        self.stage_id = stage_id
        self.ts = ts
        self.practice_ticket = practice_ticket
        self.battle_info = battle_info
        self.suggest_friend = suggest_friend


def questBattleStart() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    assistFriend = request_data["assistFriend"]
    stageId = request_data["stageId"]
    usePracticeTicket = request_data["usePracticeTicket"]
    server_config = read_json(CONFIG_PATH)

    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    chars_data = player_data["troop"]["chars"]
    stage_data = STAGE_TABLE["stages"][stageId]
    dangerLevel = stage_data["dangerLevel"]

    battleId = str(uuid.uuid1())
    practiceTicket = False
    suggestFriend = False
    notifyPowerScoreNotEnoughIfFailed = False
    inApProtectPeriod = False
    isApProtect = 0

    # Check assistFriend
    if assistFriend:
        friendList = [str(friend["uid"]) for friend in json.loads(accounts.get_friend())["list"]]
        suggestFriend = assistFriend["uid"] not in friendList

    # Check user powerScore
    if request_data["squad"]:
        slots = request_data["squad"]["slots"]
        for char in slots:
            if char not in ["", None]:
                charInstId = str(char["charInstId"])
                if charInstId in chars_data:
                    if dangerLevel not in ["-", None]:
                        stageLevel = int(dangerLevel[-2:].replace(".", ""))
                        charLevel = chars_data[charInstId]["level"]
                        evolvePhase = chars_data[charInstId]["evolvePhase"]
                        if dangerLevel.startswith("精英1") and (evolvePhase < 1 or charLevel < stageLevel):
                            notifyPowerScoreNotEnoughIfFailed = True
                            break
                        elif dangerLevel.startswith("精英2") and (evolvePhase < 2 or charLevel < stageLevel):
                            notifyPowerScoreNotEnoughIfFailed = True
                            break

    # Add current stage
    if stageId not in player_data['dungeon']['stages']:
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

    # Check if PracticeTicket is used
    if usePracticeTicket == 1:
        player_data["status"]["practiceTicket"] -= 1
        player_data["dungeon"]["stages"][stageId]["practiceTimes"] += 1
        practiceTicket = True

    # Check zoneInfo of apProtect
    for zoneId, zoneInfo in STAGE_TABLE["apProtectZoneInfo"].items():
        if zoneId in stageId:
            if zoneInfo["timeRanges"][0]["startTs"] <= int(time()) <= zoneInfo["timeRanges"][0]["endTs"]:
                inApProtectPeriod = True
                isApProtect = 1
                break

    TemporaryData.battleInfo_list.update({
        battleId: BattleInfo(stageId, int(time()), request_data, practiceTicket, suggestFriend)
    })

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "apFailReturn": stage_data["apFailReturn"],
        "battleId": battleId,
        "inApProtectPeriod": inApProtectPeriod,
        "isApProtect": isApProtect,
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
        }
    }

    if player_data["dungeon"]["stages"][stageId]["noCostCnt"] == 1:
        data["isApProtect"] = 1
        data["apFailReturn"] = stage_data["apCost"]

    if stage_data["apCost"] == 0 or usePracticeTicket == 1:
        data["isApProtect"] = 0
        data["apFailReturn"] = 0

    return data


def questBattleFinish() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    BattleData = decrypt_battle_data(request_data["data"], player_data["pushFlags"]["status"])
    battleId = BattleData["battleId"]
    battleInfo = TemporaryData.battleInfo_list[battleId]
    dexNav = player_data["dexNav"]
    dropRate = server_config["developer"]["dropRate"]
    stageId = battleInfo.stage_id
    suggestFriend = battleInfo.suggest_friend

    stage_data = STAGE_TABLE["stages"][stageId]
    player_stage = player_data["dungeon"]["stages"][stageId]
    completeState = BattleData["completeState"]
    enemyList = list(BattleData["battleData"]["stats"]["enemyList"].keys())
    displayDetailRewards = stage_data["stageDropInfo"]["displayDetailRewards"]

    # Use practice ticket
    if battleInfo.practice_ticket:
        if player_data["dungeon"]["stages"][stageId]["state"] == 0:
            player_data["dungeon"]["stages"][stageId]["state"] = 1

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

    if server_config["developer"]["debugMode"]:
        completeState = 3

    apCost = stage_data["apCost"]
    expGain = stage_data["expGain"]
    goldGain = stage_data["goldGain"]

    if completeState == 3:
        expGain = int(expGain * 1.2)
        goldGain = int(goldGain * 1.2)
        goldScale = 1.2
        expScale = 1.2
    elif completeState == 2:
        goldScale = 1
        expScale = 1
    else:
        goldScale = 0
        expScale = 0

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

    unlockStages = []
    unlockStagesObject = []
    additionalRewards = []
    unusualRewards = []
    furnitureRewards = []
    firstRewards = []
    new_stages = {}
    rewards = []
    apFailReturn = 0

    # Add enemies encountered in the level to temporary data
    if player_stage["state"] == 0:
        dexNav["enemy"]["stage"][stageId] = enemyList
        player_data["dungeon"]["stages"][stageId]["state"] = 1

    # Battle lost
    if completeState == 1:
        suggestFriend = False

        if player_stage["noCostCnt"] == 1:
            apFailReturn = stage_data["apCost"]
            player_data["dungeon"]["stages"][stageId]["noCostCnt"] = 0
        else:
            apFailReturn = stage_data["apFailReturn"]

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

    else:
        # First time 3 stars pass
        FirstClear = False
        if player_stage["state"] != 3 and completeState == 3:
            FirstClear = True

        # First time 4 stars pass
        if player_stage["state"] == 3 and completeState == 4:
            FirstClear = True

        if player_stage["state"] == 1 and completeState in [2, 3]:
            # For guard Amiya
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
                        player_data["troop"]["chars"][char_id] = char_data
                        break

            # Unlock recruit
            if stageId == "main_00-02":
                for item in [0, 1]:
                    player_data["recruit"]["normal"]["slots"][str(item)]["state"] = 1

            # Unlock stage
            unlock_list = {}
            stages = STAGE_TABLE["stages"]
            for item in stages:
                unlock_list[item] = stages[item]["unlockCondition"]

            for item in unlock_list:
                pass_condition = 0
                if len(unlock_list[item]) == 0:
                    stage_list = read_json(STAGE_JSON_PATH, encoding='utf-8')  # TODO
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
                            if stage_data["stageType"] in ["MAIN", "SUB"]:
                                if stages[item]["stageType"] in ["MAIN", "SUB"]:
                                    player_data["status"]["mainStageProgress"] = item
                            player_data["dungeon"]["stages"][item] = unlockStage
                            unlockStages.append(item)
                            unlockStagesObject.append(unlockStage)

        if FirstClear:
            # First drops
            for item in displayDetailRewards:
                dropType = item["dropType"]
                reward_id = item["id"]
                reward_type = item["type"]
                reward_count = 1 * dropRate

                if dropType in [1, 8]:
                    writeLog(f"- First Drops: FirstClear -\n{item}", "debug")
                    if reward_type == "CHAR":
                        firstRewards += giveItems(player_data, reward_id, reward_type, 1, status="GET_ITEM")
                    else:
                        firstRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        if player_stage["state"] != 3 or completeState == 4:
            player_data["dungeon"]["stages"][stageId]["state"] = completeState

        player_data["dungeon"]["stages"][stageId]["completeTimes"] += 1

        # Exp drops & Level Up
        giveItems(player_data, reward_type="EXP_PLAYER", reward_count=expGain)

        # Drops reward
        additionalRewards, unusualRewards, furnitureRewards, rewards = dropReward(displayDetailRewards, player_data, completeState, dropRate, stageId)

        # LMD base drops
        if goldGain != 0:
            # Cargo Escort - LMD
            if "wk_melee" in stageId:
                goldGain = round(goldGain, -2)

            rewards += giveItems(player_data, "4001", "GOLD", goldGain, status="GET_ITEM")

        # Character trust improvement
        completeFavor = stage_data["completeFavor"]
        passFavor = stage_data["passFavor"]

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

        # Remove enemies from temporary data
        if stageId in dexNav["enemy"]["stage"]:
            del dexNav["enemy"]["stage"][stageId]

        # Unlock enemy dexNav
        for enemyId in enemyList:
            if enemyId not in dexNav["enemy"]["enemies"]:
                dexNav["enemy"]["enemies"].update({enemyId: 1})

        # Add new stages
        for item in range(len(unlockStagesObject)):
            unlock_stageId = unlockStagesObject[item]["stageId"]
            new_stages[unlock_stageId] = player_data["dungeon"]["stages"][unlock_stageId]
        new_stages[stageId] = player_data["dungeon"]["stages"][stageId]

    data = {
        "result": 0,
        "apFailReturn": apFailReturn,
        "goldScale": goldScale,
        "expScale": expScale,
        "rewards": rewards,
        "firstRewards": firstRewards,
        "unlockStages": unlockStages,
        "unusualRewards": unusualRewards,
        "additionalRewards": additionalRewards,
        "furnitureRewards": furnitureRewards,
        "alert": [],
        "suggestFriend": suggestFriend,
        "pryResult": [],
        "playerDataDelta": {
            "deleted": {
                "dexNav": {
                    "enemy": {
                        "stage": [
                            stageId
                        ]
                    }
                }
            },
            "modified": {
                "dexNav": player_data["dexNav"],
                "dungeon": {
                    "stages": new_stages
                },
                "status": player_data["status"],
                "troop": player_data["troop"],
                "inventory": player_data["inventory"],
            }
        }
    }

    if completeState == 1:
        data["playerDataDelta"]["deleted"] = {}

    userData.set_user_data(accounts.get_uid(), player_data)

    return data


def questSaveBattleReplay() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    battleReplay = decrypt_battle_replay(request_data["battleReplay"])
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
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


def questGetBattleReplay() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    stageId = request_data["stageId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    data = {
        "battleReplay": player_data["dungeon"]["stages"][stageId]["battleReplay"],
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def questChangeSquadName() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    squadId = request_data["squadId"]
    name = request_data["name"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["troop"]["squads"][squadId]["name"] = name

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "troop": {
                    "squads": {
                        squadId: player_data["troop"]["squads"][squadId]
                    }
                }
            }
        }
    }

    return data


def questSquadFormation() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    squadId = request_data["squadId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["troop"]["squads"][str(squadId)]["slots"] = request_data["slots"]

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "troop": {
                    "squads": {
                        squadId: player_data["troop"]["squads"][str(squadId)]
                    }
                }
            }
        }
    }

    return data


def questGetAssistList() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    profession = request_data["profession"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    friend_data = json.loads(accounts.get_friend())
    friend_list = friend_data["list"]

    for friend in friend_list:
        result = userData.query_account_by_uid(friend["uid"])
        if len(result) == 0:
            friend_list.remove(friend)

    userData.set_friend_data(accounts.get_uid(), friend_data)

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
                    "powerScore": 200,  # TODO: Set the correct data
                    "uid": friendUid,
                }

                for char in range(len(userSocialAssistCharList)):
                    if userSocialAssistCharList[char]:
                        charData = chars[str(userSocialAssistCharList[char]["charInstId"])]
                        charData["skillIndex"] = userSocialAssistCharList[char]["skillIndex"]
                        if "skinId" not in charData:
                            charData["skinId"] = charData["skin"]
                        charData["crisisRecord"] = {}  # TODO: Set the correct data
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
                    "powerScore": 200,  # TODO: Set the correct data
                    "uid": friendUid,
                }

                for index in range(len(userSocialAssistCharList)):
                    if userSocialAssistCharList[index]:
                        charData = chars[str(userSocialAssistCharList[index]["charInstId"])]
                        charData["skillIndex"] = userSocialAssistCharList[index]["skillIndex"]
                        if "skinId" not in charData:
                            charData["skinId"] = charData["skin"]
                        charData["crisisRecord"] = {}  # TODO: Set the correct data
                        assistCharList.append(charData)
                        if userSocialAssistCharList[index]["charInstId"] == charInstId:
                            assistInfo["assistSlotIndex"] = index
                    assistInfo["assistCharList"] = assistCharList

                    if assistInfo not in assistList:
                        assistList.append(assistInfo)

    data = {
        "allowAskTs": int(time()) + 3,  # TODO
        "assistList": assistList,
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data


def questFinishStoryStage() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    stageId = request_data["stageId"]
    server_config = read_json(CONFIG_PATH)

    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
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
                stage_list = read_json(STAGE_JSON_PATH, encoding='utf-8')  # TODO
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


def dropReward(displayDetailRewards: Dict, player_data: Dict, completeState: int, dropRate: int, stageId: str) -> Tuple[List, List, List, List]:

    ITEM_TABLE = updateData(ITEM_TABLE_URL, True)
    BUILDING_DATA = updateData(BUILDING_DATA_URL, True)

    additionalRewards = []
    unusualRewards = []
    furnitureRewards = []
    rewards = []

    for item in displayDetailRewards:
        occPercent = item["occPercent"]
        dropType = item["dropType"]
        reward_id = item["id"]
        reward_type = item["type"]
        reward_count = 1 * dropRate

        reward_rarity = 0
        addPercent = 0

        if completeState == 3:
            if reward_type not in ["CHAR"]:
                if reward_type == "FURN":
                    reward_rarity = BUILDING_DATA["customData"]["furnitures"][reward_id]["rarity"]
                else:
                    reward_rarity = ITEM_TABLE["items"][reward_id]["rarity"]

                if reward_rarity == 0:
                    # Additional drop amount
                    reward_count += random.choices([0, 1, 2], weights=(70, 20, 10), k=1)[0]
                    addPercent = 15

                elif reward_rarity == 1:
                    reward_count += random.choices([0, 1, 2], weights=(85, 10, 5), k=1)[0]
                    addPercent = 10

                elif reward_rarity == 2:
                    addPercent = 5

                elif reward_rarity == 3:
                    addPercent = 0

                elif reward_rarity == 4:
                    addPercent = 0

        elif completeState == 2:
            if reward_type not in ["FURN", "CHAR"]:
                reward_rarity = ITEM_TABLE["items"][reward_id]["rarity"]

            if reward_rarity == 0:
                reward_count += random.choices([0, 1, 2], weights=(80, 12, 8), k=1)[0]
                addPercent = 0

            elif reward_rarity == 1:
                reward_count += random.choices([0, 1, 2], weights=(97, 2, 1), k=1)[0]
                addPercent = 0

            elif reward_rarity == 2:
                addPercent = 0

            elif reward_rarity == 3:
                addPercent = 0

            elif reward_rarity == 4:
                addPercent = 0

        if "act" in stageId.lower():
            addPercent += 12
        else:
            addPercent += random.choices([-1, 0, 1], weights=(5, 90, 5), k=1)[0]

        if occPercent == 0 and dropType == 1:
            displayDetailRewards.remove(item)

        elif occPercent == 0 and dropType == 2:
            writeLog(f"- occPercent:0,dropType:2 -\n{item}", "debug")
            if reward_type == "MATERIAL":
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
                        reward_count = ToughSiege[stageId] + random.choice([1, 0, -1])
                    else:
                        reward_count = round(ToughSiege[stageId] / (2 * 1.2))
                # Aerial Threat - Skill Summary
                AerialThreat = {
                    "wk_fly_1": [3, 0, 0],
                    "wk_fly_2": [5, 0, 0],
                    "wk_fly_3": [1, 3, 0],
                    "wk_fly_4": [1, 1, 1.58],
                    "wk_fly_5": [1.49, 1.5, 2]
                }
                if stageId in AerialThreat:
                    for i, j in enumerate(AerialThreat[stageId]):
                        percent = int(divmod(j, 1)[1])
                        drop_array = random.choices([0, 1], weights=(percent, 1 - percent), k=1)[0]
                        count = int(divmod(j, 1)[0]) + drop_array
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = count
                        else:
                            reward_count = round(count / (1.5 * 1.2))
                # Resource Search - Carbon
                ResourceSearch = {
                    "wk_armor_1": [1, 1, 2],
                    "wk_armor_2": [1, 3, 4],
                    "wk_armor_3": [0, 2.5, 5],
                    "wk_armor_4": [0, 7, 2],
                    "wk_armor_5": [0, 10, 2.99]
                }
                if stageId in ResourceSearch:
                    for i, j in enumerate(ResourceSearch[stageId]):
                        if j == 0 or (int(stageId[-1]) > 3 and reward_id == "3113"):
                            continue
                        percent = int(divmod(j, 1)[1])
                        drop_array = random.choices([0, 1], weights=(percent, 1 - percent), k=1)[0]
                        count = int(divmod(j, 1)[0]) + drop_array
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = count
                                if stageId == "wk_armor_3" and reward_id == "3401":
                                    reward_count = ResourceSearch[stageId][-1]
                        else:
                            if stageId == "wk_armor_3" and reward_id == "3401":
                                count = ResourceSearch[stageId][-1]
                            reward_count = round(count / (1.5 * 1.2))

            if reward_type == "CARD_EXP":
                # Tactical Drill - Card EXP
                TacticalDrill = {
                    "wk_kc_1": [2.01, 3, 0, 0],
                    "wk_kc_2": [3.99, 4.99, 0, 0],
                    "wk_kc_3": [3, 1.73, 3, 0],
                    "wk_kc_4": [1.99, 3, 1.99, 1],
                    "wk_kc_5": [0, 1, 1, 3],
                    "wk_kc_6": [0, 0, 2, 4],
                    "sub_02-03": [6.25, 0, 0, 0],
                    "main_00-10": [4.27, 0, 0, 0],
                    "main_03-05": [0, 5, 0, 0],
                    "sub_02-10": [0, 4, 0, 0],
                    "main_04-03": [0, 0, 2.74, 0],
                    "main_07-11": [0, 0, 2.56, 0],
                    "main_08-06": [0, 0, 2.65, 0],
                    "sub_06-1-1": [0, 0, 2.82, 0],
                    "main_09-09": [0, 0, 2.73, 0],
                    "main_10-01": [0, 0, 3.38, 0],
                    "tough_10-01": [0, 0, 3.17, 0],
                    "main_11-01": [0, 0, 3.47, 0],
                    "tough_11-01": [0, 0, 3.43, 0],
                    "sub_04-3-3": [0, 0, 3.59, 0],
                    "sub_05-3-2": [0, 0, 2.87, 0]
                }
                if stageId in TacticalDrill:
                    for i, j in enumerate(TacticalDrill[stageId]):
                        percent = int(divmod(j, 1)[1])
                        drop_array = random.choices([0, 1], weights=(percent, 1 - percent), k=1)[0]
                        count = int(divmod(j, 1)[0]) + drop_array
                        if completeState == 3:
                            if reward_rarity == i + 1:
                                reward_count = count
                        else:
                            reward_count = round(count / (1.5 * 1.2))

            if reward_type == "GOLD":
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
                if stageId in SpecialGold:
                    if completeState == 3:
                        reward_count = SpecialGold[stageId]
                    else:
                        reward_count = round(SpecialGold[stageId] / 1.2)

            rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 0 and dropType == 3:
            writeLog(f"- occPercent:0,dropType:3 -\n{item}", "debug")
            unusualRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 0 and dropType == 4:
            writeLog(f"- occPercent:0,dropType:4 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(95 - addPercent, 5 + addPercent), k=1)[0]
            reward_count += 1
            if drop_array:
                additionalRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 0 and dropType == 8:
            displayDetailRewards.remove(item)

        elif occPercent == 1 and dropType == 2:
            writeLog(f"- occPercent:1,dropType:2 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(25 - addPercent, 75 + addPercent), k=1)[0]
            if drop_array:
                rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 2 and dropType == 2:
            writeLog(f"- occPercent:2,dropType:2 -\n{item}", "debug")
            if "pro_" in stageId:
                drop_array = random.choices([0, 1], weights=(50, 50), k=1)[0]
                reward_id = displayDetailRewards[drop_array]["id"]
                reward_type = displayDetailRewards[drop_array]["type"]
                rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")
                break
            else:
                addWeights = 2
                drop_array = random.choices([0, 1], weights=(60 - addPercent * addWeights, 40 + addPercent * addWeights), k=1)[0]
                if drop_array:
                    rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 3 and dropType == 2:
            writeLog(f"- occPercent:3,dropType:2 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(85 - addPercent, 15 + addPercent), k=1)[0]
            if drop_array:
                if reward_type != "FURN":
                    rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")
                else:
                    furnitureRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 3 and dropType == 4:
            writeLog(f"- occPercent:3,dropType:4 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(80 - addPercent, 20 + addPercent), k=1)[0]
            if drop_array:
                additionalRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 4 and dropType == 2:
            writeLog(f"- occPercent:4,dropType:2 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(97 - addPercent, 3 + addPercent), k=1)[0]
            if drop_array:
                if reward_type != "FURN":
                    rewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")
                else:
                    furnitureRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 4 and dropType == 3:
            writeLog(f"- occPercent:4,dropType:3 -\n{item}", "debug")
            drop_array = random.choices([0, 1], weights=(96 - addPercent, 4 + addPercent), k=1)[0]
            if drop_array:
                unusualRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        elif occPercent == 4 and dropType == 4:
            writeLog(f"- occPercent:4,dropType:4 -\n{item}", "debug")
            drop_array = random.choices([1, 0], weights=[(addPercent - 3) / 103, (100 - (addPercent - 3)) / 103], k=103)[0]
            if drop_array:
                additionalRewards += giveItems(player_data, reward_id, reward_type, reward_count, status="GET_ITEM")

        else:
            writeLog(f"\033[1;31mUnknown dropType: {item}\033[0;0m", "info")

    if not (additionalRewards + unusualRewards + rewards) and displayDetailRewards:
        guaranteed = dropReward(displayDetailRewards, player_data, completeState, dropRate, stageId)
        return guaranteed

    return additionalRewards, unusualRewards, furnitureRewards, rewards
