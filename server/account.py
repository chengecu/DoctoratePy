import json
from os.path import exists
from time import time
from copy import deepcopy
from base64 import b64encode
from hashlib import md5

import requests
from flask import request

from constants import USER_JSON_PATH, CONFIG_PATH, BATTLE_REPLAY_JSON_PATH, \
                    SKIN_TABLE_URL, CHARACTER_TABLE_URL, EQUIP_TABLE_URL, STORY_TABLE_URL, STAGE_TABLE_URL, \
                    SYNC_DATA_TEMPLATE_PATH, BATTLEEQUIP_TABLE_URL, DM_TABLE_URL, RETRO_TABLE_URL
from utils import read_json, write_json

def accountLogin():

    data = request.data
    data = {
        "result": 0,
        "uid": "-1",
        "secret": "yostar",
        "serviceLicenseVersion": 0
    }

    return data


def accountSyncData():

    data = request.data

    if not exists(USER_JSON_PATH):
        write_json({}, USER_JSON_PATH)

    saved_data = read_json(USER_JSON_PATH)
    player_data = read_json(SYNC_DATA_TEMPLATE_PATH, encoding="utf-8")
    config = read_json(CONFIG_PATH)

    # Load newest data
    data_skin = requests.get(SKIN_TABLE_URL).json()
    character_table = requests.get(CHARACTER_TABLE_URL).json()
    equip_table = requests.get(EQUIP_TABLE_URL).json()
    battle_equip_table = requests.get(BATTLEEQUIP_TABLE_URL).json()
    display_meta_table = requests.get(DM_TABLE_URL).json()
    retro_table = requests.get(RETRO_TABLE_URL).json()

    ts = round(time())
    cnt = 0
    cntInstId = 1
    tempSkinTable = {}
    myCharList = {}
    charGroup = {}
    buildingChars = {}

    #Tamper Skins
    skinKeys = list(data_skin["charSkins"].keys())
    player_data["user"]["skin"]["characterSkins"] = {}
    for i in data_skin["charSkins"].values():
        if "@" not in skinKeys[cnt]:
            # Not Special Skins
            cnt += 1
            continue
        
        player_data["user"]["skin"]["characterSkins"][skinKeys[cnt]] = 1
        if not i["charId"] in tempSkinTable.keys() \
                or i["displaySkin"]["onYear"] > data_skin["charSkins"][tempSkinTable[i["charId"]]]["displaySkin"]["onYear"]:
            tempSkinTable[i["charId"]] = i["skinId"]
        cnt += 1
        
    #Tamper Operators
    edit_json = config["charConfig"]

    cnt = 0
    operatorKeys = list(character_table.keys())
    equip_keys = list(equip_table["charEquip"].keys())

    for operatorKey in operatorKeys:
        if "char" not in operatorKey:
            continue

        charGroup.update({
            operatorKey: {
                "favorPoint": 25570
            }
        })

    for i in character_table:
        if "char" not in operatorKeys[cnt]:
            cnt += 1
            continue

        # Add all operators
        if edit_json["level"] == -1:
            level = character_table[i]["phases"][edit_json["evolvePhase"]]["maxLevel"]
        else:
            level = edit_json["level"]

        maxEvolvePhase = len(character_table[i]["phases"]) - 1
        evolvePhase = maxEvolvePhase

        if edit_json["evolvePhase"] != -1:
            if edit_json["evolvePhase"] > maxEvolvePhase:
                evolvePhase = maxEvolvePhase
            else:
                evolvePhase = edit_json["evolvePhase"]

        myCharList[int(cntInstId)] = {
            "instId": int(cntInstId),
            "charId": operatorKeys[cnt],
            "favorPoint": edit_json["favorPoint"],
            "potentialRank": edit_json["potentialRank"],
            "mainSkillLvl": edit_json["mainSkillLvl"],
            "skin": str(operatorKeys[cnt]) + "#1",
            "level": level,
            "exp": 0,
            "evolvePhase": evolvePhase,
            "defaultSkillIndex": len(character_table[i]["skills"])-1,
            "gainTime": int(time()),
            "skills": [],
            "voiceLan": "JP",
            "currentEquip": None,
            "equip": {},
            "starMark": 0
        }

        # set to E2 art if available skipping is2 recruits
        if operatorKeys[cnt] not in ["char_508_aguard", "char_509_acast", "char_510_amedic", "char_511_asnipe"]:
            if myCharList[int(cntInstId)]["evolvePhase"] == 2:
                myCharList[int(cntInstId)]["skin"] = str(operatorKeys[cnt]) + "#2"

        # set to seasonal skins
        if operatorKeys[cnt] in tempSkinTable.keys():
            myCharList[int(cntInstId)]["skin"] = tempSkinTable[operatorKeys[cnt]]

        # Add Skills
        for index, skill in enumerate(character_table[i]["skills"]):
            myCharList[int(cntInstId)]["skills"].append({
                "skillId": skill["skillId"],
                "unlock": 1,
                "state": 0,
                "specializeLevel": 0,
                "completeUpgradeTime": -1
            })

            # M3
            if len(skill["levelUpCostCond"]) > 0:
                myCharList[int(cntInstId)]["skills"][index]["specializeLevel"] = edit_json["skillsSpecializeLevel"]

        # Add equips
        if myCharList[int(cntInstId)]["charId"] in equip_keys:

            for equip in equip_table["charEquip"][myCharList[int(cntInstId)]["charId"]]:
                level = 1
                if equip in list(battle_equip_table.keys()):
                    level = len(battle_equip_table[equip]["phases"])
                myCharList[int(cntInstId)]["equip"].update({
                    equip: {
                        "hide": 0,
                        "locked": 0,
                        "level": level
                    }
                })
            myCharList[int(cntInstId)]["currentEquip"] = equip_table["charEquip"][myCharList[int(cntInstId)]["charId"]][-1]

        # Dexnav
        player_data["user"]["dexNav"]["character"][operatorKeys[cnt]] = {
            "charInstId": cntInstId,
            "count": 6
        }

        custom_units = edit_json["customUnitInfo"]

        for char in custom_units:
            if operatorKeys[cnt] == char:
                for key in custom_units[char]:
                    if key != "skills":
                        myCharList[int(cntInstId)][key] = custom_units[char][key]
                    else:
                        for skillIndex, skillValue in enumerate(custom_units[char]["skills"]):
                            myCharList[int(cntInstId)]["skills"][skillIndex]["specializeLevel"] = skillValue

        if operatorKeys[cnt] == "char_002_amiya":
            myCharList[int(cntInstId)].update({
                "defaultSkillIndex": -1,
                "skills": [],
                "currentTmpl": "char_002_amiya",
                "tmpl": {
                    "char_002_amiya": {
                        "skinId": "char_002_amiya@winter#1",
                        "defaultSkillIndex": 0,
                        "skills": [
                            {
                                "skillId": skill_name,
                                "unlock": 1,
                                "state": 0,
                                "specializeLevel": edit_json["skillsSpecializeLevel"],
                                "completeUpgradeTime": -1
                            } for skill_name in ["skcom_magic_rage[3]", "skcom_magic_rage[3]", "skchr_amiya_3"]
                        ]
                    },
                    "char_1001_amiya2": {
                        "skinId": "char_1001_amiya2#2",
                        "defaultSkillIndex": 0,
                        "skills": [
                            {
                                "skillId": skill_name,
                                "unlock": 1,
                                "state": 0,
                                "specializeLevel": edit_json["skillsSpecializeLevel"],
                                "completeUpgradeTime": -1
                            } for skill_name in ["skchr_amiya2_1", "skchr_amiya2_2"]
                        ]
                    }
                }
            })

        buildingChars.update({
            int(cntInstId): {
                "charId": operatorKeys[cnt],
                "lastApAddTime": round(time()) - 3600,
                "ap": 8640000,
                "roomSlotId": "",
                "index": -1,
                "changeScale": 0,
                "bubble": {
                    "normal": {
                        "add": -1,
                        "ts": 0
                    },
                    "assist": {
                        "add": -1,
                        "ts": 0
                    }
                },
                "workTime": 0
            }
        })

        cnt += 1
        cntInstId += 1

    dupe_characters = edit_json["duplicateUnits"]
    for dupeChar in dupe_characters:

        tempChar = {}
        for char in myCharList:
            if dupeChar == myCharList[char]["charId"]:
                tempChar = deepcopy(myCharList[char])
                break

        tempChar["instId"] = int(cntInstId)
        myCharList[int(cntInstId)] = tempChar
        cntInstId += 1

    player_data["user"]["troop"]["chars"] = myCharList
    player_data["user"]["troop"]["charGroup"] = charGroup
    player_data["user"]["troop"]["curCharInstId"] = cntInstId

    # Tamper story
    myStoryList = {"init": 1}
    story_table = requests.get(STORY_TABLE_URL).json()
    for story in story_table:
        myStoryList.update({story:1})

    player_data["user"]["status"]["flags"] = myStoryList

    # Tamper Stages
    myStageList = {}
    stage_table = requests.get(STAGE_TABLE_URL).json()
    for stage in stage_table["stages"]:
        myStageList.update({
            stage: {
                "completeTimes": 1,
                "hasBattleReplay": 0,
                "noCostCnt": 0,
                "practiceTimes": 0,
                "stageId": stage_table["stages"][stage]["stageId"],
                "startTimes": 1,
                "state": 3
            }
        })
    
    player_data["user"]["dungeon"]["stages"] = myStageList

    # Tamper Side Stories and Intermezzis
    block = {}
    for retro in retro_table["retroActList"]:
        block.update({
            retro: {
                "locked": 0,
                "open": 1
            }
        })
    player_data["user"]["retro"]["block"] = block

    trail = {}
    for retro in retro_table["retroTrailList"]:
        trail.update({retro:{}})
        for trailReward in retro_table["retroTrailList"][retro]["trailRewardList"]:
            trail.update({
                retro: {
                    trailReward["trailRewardId"]: 1
                }
            })
    player_data["user"]["retro"]["trail"] = trail

    # Tamper Anniliations
    for stage in stage_table["stages"]:
        if stage.startswith("camp"):
            player_data["user"]["campaignsV2"]["instances"].update({
                stage: {
                    "maxKills": 400,
                    "rewardStatus": [1, 1, 1, 1, 1, 1, 1, 1]
                }
            })

            player_data["user"]["campaignsV2"]["sweepMaxKills"].update({stage: 400})
            player_data["user"]["campaignsV2"]["open"]["permanent"].append(stage)
            player_data["user"]["campaignsV2"]["open"]["training"].append(stage)


    # Tamper Avatars and Backgrounds
    avatar_icon = {}
    for avatar in display_meta_table["playerAvatarData"]["avatarList"]:
        avatar_icon.update({
            avatar["avatarId"]: {
                "ts": round(time()),
                "src": "initial" if avatar["avatarId"].startswith("avatar_def") else "other"
            }
        })
    player_data["user"]["avatar"]["avatar_icon"] = avatar_icon

    bgs = {}
    for bg in display_meta_table["homeBackgroundData"]["homeBgDataList"]:
        bgs.update({
            bg["bgId"]: {
                "unlock": round(time())
            }
        })
    player_data["user"]["background"]["bgs"] = bgs

    # Update timestamps
    player_data["user"]["status"]["lastRefreshTs"] = ts
    player_data["user"]["status"]["lastApAddTime"] = ts
    player_data["user"]["status"]["registerTs"] = ts
    player_data["user"]["status"]["lastOnlineTs"] = ts
    player_data["user"]["crisis"]["lst"] = ts
    player_data["user"]["crisis"]["nst"] = ts + 3600
    # player_data["user"]["crisis"]["training"]["nst"] = ts + 3600
    player_data["ts"] = ts

    replay_data = read_json(BATTLE_REPLAY_JSON_PATH)
    replay_data["currentCharConfig"] = md5(b64encode(json.dumps(edit_json).encode())).hexdigest()
    write_json(replay_data, BATTLE_REPLAY_JSON_PATH)

    # if config["userConfig"]["restorePreviousStates"]["is2"]:
    #     is2_data = read_json(RLV2_JSON_PATH)
    #     player_data["user"]["rlv2"] = is2_data

    # Enable battle replays
    if replay_data["currentCharConfig"] in list(replay_data["saved"].keys()):
        for replay in replay_data["saved"][replay_data["currentCharConfig"]]:
            player_data["user"]["dungeon"]["stages"][replay]["hasBattleReplay"] = 1

    # Copy over from previous launch if data exists
    if "user" in list(saved_data.keys()) and config["userConfig"]["restorePreviousStates"]["squadsAndFavs"]:
        player_data["user"]["troop"]["squads"] = saved_data["user"]["troop"]["squads"]

        for _, saved_character in saved_data["user"]["troop"]["chars"].items():
            index = "0"
            for character_index, character in player_data["user"]["troop"]["chars"].items():
                if saved_character["charId"] == character["charId"]:
                    index = character_index
                    break

            player_data["user"]["troop"]["chars"][index]["starMark"] = saved_character["starMark"]
            player_data["user"]["troop"]["chars"][index]["voiceLan"] = saved_character["voiceLan"]

    write_json(player_data, USER_JSON_PATH)
    
    return player_data


def accountSyncStatus():
    
    data = request.data
    data = {
        "ts": round(time()),
        "result": {},
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data

