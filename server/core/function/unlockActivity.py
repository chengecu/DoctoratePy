from time import time
from typing import Dict

from constants import (ACTIVITY_TABLE_URL, CHARWORD_TABLE_URL, CONFIG_PATH,
                       STAGE_TABLE_URL)
from core.function.update import updateData
from mission import MissionTemplate
from utils import read_json


def unlockActivity(player_data: Dict) -> Dict:

    ACTIVITY_TABLE = updateData(ACTIVITY_TABLE_URL, True)
    CHARWORD_TABLE = updateData(CHARWORD_TABLE_URL, True)
    STAGE_TABLE = updateData(STAGE_TABLE_URL, True)

    server_config = read_json(CONFIG_PATH)
    activity = player_data["activity"]
    ts = int(time()) if server_config["developer"]["timestamp"] == -1 else server_config["developer"]["timestamp"]
    replicate_list = []

    for type, activitise in activity.items():
        for item in list(activitise.keys()):
            activity_data = ACTIVITY_TABLE["basicInfo"][item]
            if ts > activity_data["rewardEndTime"]:
                del activity[type][item]

    for id, value in ACTIVITY_TABLE["basicInfo"].items():
        activity_type = value["type"]
        player_data["activity"].setdefault(activity_type, {})

        if value["startTime"] <= ts <= value["rewardEndTime"]:
            missionIds = []
            for group in ACTIVITY_TABLE["missionGroup"]:
                if group["id"] == id:
                    missionIds = group["missionIds"]

            for mission_id in missionIds:
                for data in ACTIVITY_TABLE["missionData"]:
                    if data["id"] == mission_id:
                        template = data["template"]
                        param = data["param"]
                        getattr(MissionTemplate(None, player_data, None, mission_id, None, None), template)(*param)

            if activity_type == "BOSS_RUSH":
                default_relic = ACTIVITY_TABLE["activity"]["BOSS_RUSH"][id]["relicList"][0]["relicId"]

                player_data["activity"][activity_type].setdefault(id, {
                    "milestone": {
                        "point": 0,
                        "got": []
                    },
                    "relic": {
                        "token": {
                            "current": 0,
                            "total": 0
                        },
                        "level": {
                            default_relic: 1
                        },
                        "select": ""
                    },
                    "best": {}
                })

            if "TYPE_ACT" in activity_type:
                favorList = []
                if value["isReplicate"]:
                    replicate_list.append({
                        value["name"].replace("·复刻", ""): {
                            "activity_type": activity_type,
                            "id": id,
                        }
                    })

                for item in CHARWORD_TABLE["startTimeWithTypeDict"]["JP"]:
                    if item["timestamp"] == value["startTime"]:
                        favorList = item["charSet"]

                player_data["activity"][activity_type].setdefault(id, {
                    "coin": 0,
                    "favorList": favorList,  # TODO
                    "news": {}
                })

            # Update stages
            unlock_list = {}
            stages = STAGE_TABLE["stages"]
            for item in stages:
                unlock_list[item] = stages[item]["unlockCondition"]

            for item in unlock_list:
                pass_condition = 0
                if len(unlock_list[item]) != 0:
                    for condition in unlock_list[item]:
                        if condition["stageId"] in player_data["dungeon"]["stages"]:
                            if player_data["dungeon"]["stages"][condition["stageId"]]["state"] >= condition["completeState"]:
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
                            player_data["dungeon"]["stages"].update({item: unlockStage})

            # TODO: Add more
        if value["name"] in replicate_list:
            _activity_type = replicate_list[value["name"]]["activity_type"]
            _id = replicate_list[value["name"]]["id"]
            realTime = value["startTime"]
            favorList = []

            for item in CHARWORD_TABLE["startTimeWithTypeDict"]["JP"]:
                if item["timestamp"] == realTime:
                    favorList = item["charSet"]

            player_data["activity"][_activity_type][_id]["favorList"] = favorList

    return player_data
