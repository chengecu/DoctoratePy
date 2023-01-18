import json
import uuid
from time import time
from typing import Dict

from flask import Response, abort, request

from constants import ACTIVITY_TABLE_URL, CONFIG_PATH, STAGE_TABLE_URL
from core.Account import Account
from core.database import userData
from core.function.giveItem import giveItems
from core.function.update import updateData
from logger import writeLog
from mission import MissionTemplate
from utils import decrypt_battle_data, read_json


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


def activityConfirmActivityMission() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    missionId = request_data["missionId"]
    server_config = read_json(CONFIG_PATH)

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    mission_data_list = {data["id"]: data for data in ACTIVITY_TABLE["missionData"]}
    missionData = mission_data_list[missionId]
    rewards = missionData["rewards"]

    items = []
    missionIds = []

    for group in ACTIVITY_TABLE["missionGroup"]:
        if group["id"] == activityId:
            missionIds = group["missionIds"]

    for item in rewards:
        items += giveItems(player_data, item["id"], item["type"], item["count"], activityId, "BOSS_RUSH", status="GET_ITEM")

    getattr(MissionTemplate(None, player_data, None, missionId, None, None), "CompleteMission")({activityId: missionIds})

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "skin": player_data["skin"],
                "troop": player_data["troop"],
                "buliding": player_data["building"],
                "consumable": player_data["consumable"],
                "inventory": player_data["inventory"],
                "activity": player_data["activity"],
                "mission": player_data["mission"]
            }
        }
    }

    return data


def activityConfirmActivityMissionList() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    missionIds = request_data["missionIds"]
    server_config = read_json(CONFIG_PATH)

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    mission_data_list = {data["id"]: data for data in ACTIVITY_TABLE["missionData"]}

    items = []
    _missionIds = []

    for group in ACTIVITY_TABLE["missionGroup"]:
        if group["id"] == activityId:
            _missionIds = group["missionIds"]

    for missionId in missionIds:
        missionData = mission_data_list[missionId]
        rewards = missionData["rewards"]

        for item in rewards:
            items += giveItems(player_data, item["id"], item["type"], item["count"], activityId, "BOSS_RUSH", status="GET_ITEM")

        getattr(MissionTemplate(None, player_data, None, missionId, None, None), "CompleteMission")({activityId: _missionIds})

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "skin": player_data["skin"],
                "troop": player_data["troop"],
                "buliding": player_data["building"],
                "consumable": player_data["consumable"],
                "inventory": player_data["inventory"],
                "activity": player_data["activity"],
                "mission": player_data["mission"]
            }
        }
    }

    return data


def activityRewardMilestone() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    milestoneId = request_data["milestoneId"]
    server_config = read_json(CONFIG_PATH)

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    activity_type = ACTIVITY_TABLE["basicInfo"][activityId]["type"]

    items = []

    if activity_type == "BOSS_RUSH":
        player_data["activity"]["BOSS_RUSH"][activityId]["milestone"]["got"].append(milestoneId)
        mileStone = {d["mileStoneId"]: d for d in ACTIVITY_TABLE["activity"][activity_type][activityId]["mileStoneList"]}[milestoneId]
        rewardItem = mileStone["rewardItem"]

        items = giveItems(player_data, rewardItem["id"], rewardItem["type"], rewardItem["count"], status="GET_ITEM")

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "skin": player_data["skin"],
                "troop": player_data["troop"],
                "buliding": player_data["building"],
                "consumable": player_data["consumable"],
                "inventory": player_data["inventory"],
                "activity": player_data["activity"]
            }
        }
    }

    return data


def activityRewardAllMilestone() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    server_config = read_json(CONFIG_PATH)

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    activity_type = ACTIVITY_TABLE["basicInfo"][activityId]["type"]

    items = []
    milestoneList = []

    if activity_type == "BOSS_RUSH":
        BOSS_RUSH = player_data["activity"]["BOSS_RUSH"]
        hasGot = player_data["activity"]["BOSS_RUSH"][activityId]["milestone"]["got"]
        mileStone_list = {d["mileStoneId"]: d for d in ACTIVITY_TABLE["activity"][activity_type][activityId]["mileStoneList"]}

        for id, data in mileStone_list.items():
            if data["needPointCnt"] <= BOSS_RUSH[activityId]["milestone"]["point"] and id not in hasGot:
                milestoneList.append(id)

        for item in milestoneList:
            rewardItem = mileStone_list[item]["rewardItem"]

            items += giveItems(player_data, rewardItem["id"], rewardItem["type"], rewardItem["count"], status="GET_ITEM")

        player_data["activity"]["BOSS_RUSH"][activityId]["milestone"]["got"] += milestoneList

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "milestoneList": milestoneList,
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "status": player_data["status"],
                "skin": player_data["skin"],
                "troop": player_data["troop"],
                "buliding": player_data["building"],
                "consumable": player_data["consumable"],
                "inventory": player_data["inventory"],
                "activity": player_data["activity"]
            }
        }
    }

    return data


def activityBossRushBattleStart() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    assistFriend = request_data["assistFriend"]
    stageId = request_data["stageId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    battleId = str(uuid.uuid1())
    suggestFriend = False

    if assistFriend:
        friendList = [str(friend["uid"]) for friend in json.loads(accounts.get_friend())["list"]]
        suggestFriend = assistFriend["uid"] not in friendList

    if stageId not in player_data['dungeon']['stages']:
        stagesData = {
            "stageId": stageId,
            "completeTimes": 0,
            "startTimes": 0,
            "practiceTimes": 0,
            "state": 0,
            "hasBattleReplay": 0,
            "noCostCnt": 0
        }

        player_data['dungeon']['stages'][stageId] = stagesData

    player_data["dungeon"]["stages"][stageId]["noCostCnt"] = 0

    TemporaryData.battleInfo_list.update({
        battleId: BattleInfo(stageId, int(time()), request_data, False, suggestFriend)
    })

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "battleId": battleId,
        "apFailReturn": 0,
        "isApProtect": 0,
        "inApProtectPeriod": False,
        "notifyPowerScoreNotEnoughIfFailed": False,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "dungeon": {
                    "stages": {
                        stageId: player_data['dungeon']['stages'][stageId]
                    }
                }
            }
        }
    }

    return data


def activityBossRushBattleFinish() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    server_config = read_json(CONFIG_PATH)

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)
    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    BOSS_RUSH = player_data["activity"]["BOSS_RUSH"]
    dexNav = player_data["dexNav"]
    BattleData = decrypt_battle_data(request_data["data"], player_data["pushFlags"]["status"])
    battleId = BattleData["battleId"]
    battleInfo = TemporaryData.battleInfo_list[battleId]
    stageId = battleInfo.stage_id

    enemyList = list(BattleData["battleData"]["stats"]["enemyList"].keys())
    extraBattleInfo = BattleData["battleData"]["stats"]["extraBattleInfo"]
    completeState = BattleData["completeState"]
    stage_data = player_data["dungeon"]["stages"][stageId]
    suggestFriend = battleInfo.suggest_friend

    unlockStages = []
    unlockStagesObject = []
    firstRewards = []
    rewards = []
    milestoneAdd = 0
    tokenAdd = 0
    wave = 0

    if stage_data["state"] == 0:
        stage_data["state"] = 1

    # Get wave info
    for info, value in extraBattleInfo.items():
        if "bossrush_finished_wave" in info:
            wave = value
            break

    # Check milestone & token
    milestoneBefore = BOSS_RUSH[activityId]["milestone"]["point"]
    isMileStoneMax = milestoneBefore >= 3625
    isTokenMax = BOSS_RUSH[activityId]["relic"]["token"]["total"] >= 240

    # Add enemies encountered in the level to temporary data
    if stage_data["state"] == 1:
        dexNav["enemy"]["stage"][stageId] = enemyList

    FirstClear = False
    if stage_data["state"] != 3 and completeState in [2, 3]:
        FirstClear = True
        # Unlock stage
        unlock_list = {}
        stages = STAGE_TABLE["stages"]

        for item in list(stages.keys()):
            unlock_list[item] = stages[item]["unlockCondition"]

        for item in list(unlock_list.keys()):
            pass_condition = 0
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
                        "noCostCnt": 0
                    }

                    if item not in player_data["dungeon"]["stages"]:
                        player_data["dungeon"]["stages"][item] = unlockStage
                        unlockStages.append(item)
                        unlockStagesObject.append(unlockStage)

    if stage_data["state"] != 3:
        stage_data["state"] = completeState

    displayDetailRewards = ACTIVITY_TABLE["activity"]["BOSS_RUSH"][activityId]["stageDropDataMap"][stageId][str(wave)]["displayDetailRewards"]

    for index in range(len(displayDetailRewards)):
        dropType = displayDetailRewards[index]["dropType"]
        reward_count = displayDetailRewards[index]["dropCount"]
        reward_id = displayDetailRewards[index]["id"]
        reward_type = displayDetailRewards[index]["type"]
        occPercent = displayDetailRewards[index]["occPercent"]

        if FirstClear:
            writeLog("- First Drops: FirstClear -", "debug")
            if dropType == 1:
                if "milestone_point" in reward_id:
                    milestoneAdd += reward_count
                if "token_relic" in reward_id:
                    tokenAdd += reward_count

                firstRewards += giveItems(player_data, reward_id, reward_type, reward_count, activityId, "BOSS_RUSH", status="GET_ITEM")

        # Regular Drops: Guaranteed
        if occPercent == 0 and dropType == 2 and reward_count != 0 and completeState != 1:
            writeLog("- Regular Drops: Guaranteed -", "debug")
            if "milestone_point" in reward_id:
                if isMileStoneMax:
                    continue
                milestoneAdd += reward_count
            if "token_relic" in reward_id:
                if isTokenMax:
                    continue
                tokenAdd += reward_count

            rewards += giveItems(player_data, reward_id, reward_type, reward_count, activityId, "BOSS_RUSH", status="GET_ITEM")

    # Remove enemies from temporary data
    if stageId in dexNav["enemy"]["stage"]:
        del dexNav["enemy"]["stage"][stageId]

    # Add enemies to dexNav
    for enemyId in enemyList:
        if enemyId not in dexNav["enemy"]["enemies"]:
            dexNav["enemy"]["enemies"].update({enemyId: 1})

    # Add levels that need to be unlocked
    stages = {}
    for index in range(len(unlockStagesObject)):
        unlock_stageId = unlockStagesObject[index]["stageId"]
        stages[unlock_stageId] = player_data["dungeon"]["stages"][unlock_stageId]
    stages[stageId] = player_data["dungeon"]["stages"][stageId]

    # Reset milestone & token
    if isMileStoneMax:
        BOSS_RUSH[activityId]["milestone"]["point"] = 3625
    if isTokenMax:
        BOSS_RUSH[activityId]["relic"]["token"]["total"] = 240

    # Set the best score
    if wave != 0 and wave > BOSS_RUSH[activityId]["best"].get(stageId, 0):
        BOSS_RUSH[activityId]["best"][stageId] = wave

    # Update mission
    mission_data_list = {data["id"]: data for data in ACTIVITY_TABLE["missionData"]}

    for group in ACTIVITY_TABLE["missionGroup"]:
        if group["id"] == activityId:
            missionIds = group["missionIds"]
            for mission_id in missionIds:
                data = mission_data_list[mission_id]
                template = data["template"]
                param = data["param"]
                getattr(MissionTemplate(BattleData, player_data, battleInfo.battle_info, mission_id, stageId, None), template)(*param)

    if completeState == 1:
        suggestFriend = False

    data = {
        "result": 0,
        "apFailReturn": 0,
        "expScale": 0,
        "goldScale": 0,
        "rewards": rewards,
        "firstRewards": firstRewards,
        "unlockStages": unlockStages,
        "unusualRewards": [],
        "additionalRewards": [],
        "furnitureRewards": [],
        "alert": [],
        "suggestFriend": suggestFriend,
        "pryResult": [],
        "wave": wave,
        "milestoneBefore": milestoneBefore,
        "milestoneAdd": milestoneAdd,
        "isMileStoneMax": isMileStoneMax,
        "tokenAdd": tokenAdd,
        "isTokenMax": isTokenMax,
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
                "activity": {
                    "BOSS_RUSH": {
                        activityId: player_data["activity"]["BOSS_RUSH"][activityId]
                    }
                },
                "dungeon": {
                    "stages": stages
                },
                "mission": player_data["mission"]
            }
        }
    }

    if completeState == 1:
        data["playerDataDelta"]["deleted"] = {}

    userData.set_user_data(accounts.get_uid(), player_data)

    return data


def activityBossRushRelicUpgrade() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    relicId = request_data["relicId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    BOSS_RUSH = player_data["activity"]["BOSS_RUSH"]
    token = BOSS_RUSH[activityId]["relic"]["token"]
    level = BOSS_RUSH[activityId]["relic"]["level"]

    level[relicId] = level.setdefault(relicId, 1) + 1
    token["current"] -= 20

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "activity": {
                    "BOSS_RUSH": {
                        activityId: player_data["activity"]["BOSS_RUSH"][activityId]
                    }
                }
            }
        }
    }

    return data


def activityBossRushRelicSelect() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    activityId = request_data["activityId"]
    relicId = request_data["relicId"]
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    BOSS_RUSH = player_data["activity"]["BOSS_RUSH"]
    BOSS_RUSH[activityId]["relic"]["select"] = relicId

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "activity": {
                    "BOSS_RUSH": {
                        activityId: player_data["activity"]["BOSS_RUSH"][activityId]
                    }
                }
            }
        }
    }

    return data
