import json
import random
import socket
import uuid
from datetime import datetime
from time import time
from typing import Dict

from flask import Response, abort, request

from constants import CONFIG_PATH, TOWER_TABLE_URL
from core.Account import Account
from core.database import userData
from core.function.giveItem import giveItems
from core.function.update import updateData
from utils import decrypt_battle_data, read_json

# TODO: Mission System


class TemporaryData:

    battleInfo_list = {}


class BattleInfo:
    def __init__(self, stage_id: str, ts: int, battle_info: Dict):
        self.stage_id = stage_id
        self.ts = ts
        self.battle_info = battle_info


def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def createRecruitList(player_data: dict) -> None:
    candidate = []
    allCards = [str(player_data["troop"]["chars"][key]["instId"]) for key in player_data["troop"]["chars"]]
    pickedCards = [str(player_data["tower"]["current"]["cards"][key]["relation"]) for key in player_data["tower"]["current"]["cards"]]
    availableCards = list(set(allCards) - set(pickedCards))
    if len(availableCards) > 5:
        for card in availableCards:
            candidate.append({
                "groupId": player_data["troop"]["chars"][card]["charId"],
                "type": "CHAR",
                "cards": [{
                    "instId": "0",
                    "type": "CHAR",
                    "charId": player_data["troop"]["chars"][card]["charId"],
                    "relation": card,
                    "evolvePhase": player_data["troop"]["chars"][card]["evolvePhase"],
                    "level": player_data["troop"]["chars"][card]["level"],
                    "favorPoint": player_data["troop"]["chars"][card]["favorPoint"],
                    "potentialRank": player_data["troop"]["chars"][card]["potentialRank"],
                    "mainSkillLvl": player_data["troop"]["chars"][card]["mainSkillLvl"],
                    "skills": player_data["troop"]["chars"][card]["skills"],
                    "defaultSkillIndex": player_data["troop"]["chars"][card]["defaultSkillIndex"],
                    "currentEquip": player_data["troop"]["chars"][card]["currentEquip"],
                    "equip": player_data["troop"]["chars"][card]["equip"],
                    "skin": player_data["troop"]["chars"][card]["skin"]
                }]
            })
        player_data["tower"]["current"]["halftime"]["candidate"] = candidate
        player_data["tower"]["current"]["halftime"]["canGiveUp"] = random.choice([True, False])
    elif len(availableCards) == 0:
        player_data["tower"]["current"]["halftime"]["candidate"] = []
        player_data["tower"]["current"]["halftime"]["canGiveUp"] = True
    else:
        for card in availableCards:
            candidate.append({
                "groupId": player_data["troop"]["chars"][card]["charId"],
                "type": "CHAR",
                "cards": [{
                    "instId": "0",
                    "type": "CHAR",
                    "charId": player_data["troop"]["chars"][card]["charId"],
                    "relation": card,
                    "evolvePhase": player_data["troop"]["chars"][card]["evolvePhase"],
                    "level": player_data["troop"]["chars"][card]["level"],
                    "favorPoint": player_data["troop"]["chars"][card]["favorPoint"],
                    "potentialRank": player_data["troop"]["chars"][card]["potentialRank"],
                    "mainSkillLvl": player_data["troop"]["chars"][card]["mainSkillLvl"],
                    "skills": player_data["troop"]["chars"][card]["skills"],
                    "defaultSkillIndex": player_data["troop"]["chars"][card]["defaultSkillIndex"],
                    "currentEquip": player_data["troop"]["chars"][card]["currentEquip"],
                    "equip": player_data["troop"]["chars"][card]["equip"],
                    "skin": player_data["troop"]["chars"][card]["skin"]
                }]
            })
        player_data["tower"]["current"]["halftime"]["candidate"] = candidate
        player_data["tower"]["current"]["halftime"]["canGiveUp"] = True


def changeState(stageCnt: int, player_data: dict, BattleData: dict, trap: list) -> None:
    TOWER_TABLE = updateData(TOWER_TABLE_URL, True)
    if stageCnt == len(player_data["tower"]["current"]["layer"]):
        player_data["tower"]["current"]["status"]["state"] = "END"
    elif stageCnt == TOWER_TABLE["detailConst"]["subcardStageSort"] - 1:
        player_data["tower"]["current"]["status"]["state"] = "SUB_GOD_CARD_RECRUIT"
        for i in BattleData["battleData"]["stats"]["extraBattleInfo"]:
            if i.startswith("DETAILED") and i.endswith("legion_gain_reward_trap"):
                trap.append({
                    "id": i.split(",")[1],
                    "alias": i.split(",")[2],
                })
        player_data["tower"]["current"]["status"]["trap"] = trap
        return trap
    else:
        player_data["tower"]["current"]["status"]["state"] = "RECRUIT"
        player_data["tower"]["current"]["halftime"]["count"] += 1
        createRecruitList(player_data)


def towerDropSystem(stageCnt: int, player_data: dict, drop: list) -> None:
    TOWER_TABLE = updateData(TOWER_TABLE_URL, True)
    player_data["tower"]["season"]["period"]["items"].setdefault("mod_update_token_1", 0)
    player_data["tower"]["season"]["period"]["items"].setdefault("mod_update_token_2", 0)
    dropInfo = TOWER_TABLE["rewardInfoList"][stageCnt - 1]
    if player_data["tower"]["current"]["status"]["isHard"]:
        higher = dropInfo["higherItemCount"] * 2
        lower = dropInfo["lowerItemCount"] * 2
    else:
        higher = dropInfo["higherItemCount"]
        lower = dropInfo["lowerItemCount"]
    drop = [{
        "id": "mod_update_token_1",
        "before": 0,
        "after": 0,
        "max": True
    }, {
        "id": "mod_update_token_2",
        "before": 0,
        "after": 0,
        "max": True
    }]

    # mod_update_token_1
    if player_data["tower"]["current"]["reward"]["low"] + player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"] == TOWER_TABLE["detailConst"]["lowerItemLimit"]:
        drop.pop(0)
    elif player_data["tower"]["current"]["reward"]["low"] + player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"] + lower > TOWER_TABLE["detailConst"]["lowerItemLimit"]:
        drop[0] = {
            "id": "mod_update_token_1",
            "before": player_data["tower"]["current"]["reward"]["low"],
            "after": player_data["tower"]["current"]["reward"]["low"] * 2 + player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"] + lower - TOWER_TABLE["detailConst"]["lowerItemLimit"],
            "max": True
        }
        player_data["tower"]["current"]["reward"]["low"] = drop[0]["after"]
    else:
        drop[0] = {
            "id": "mod_update_token_1",
            "before": player_data["tower"]["current"]["reward"]["low"],
            "after": player_data["tower"]["current"]["reward"]["low"] + lower,
            "max": False
        }
        player_data["tower"]["current"]["reward"]["low"] = drop[0]["after"]

    # mod_update_token_2
    if player_data["tower"]["current"]["reward"]["high"] + player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"] == TOWER_TABLE["detailConst"]["higherItemLimit"]:
        if drop[0]["id"] == "mod_update_token_2":
            drop.pop(0)
        else:
            drop.pop(1)
    elif player_data["tower"]["current"]["reward"]["high"] + player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"] + higher > TOWER_TABLE["detailConst"]["higherItemLimit"]:
        if drop[0]["id"] == "mod_update_token_2":
            cnt = 0
        else:
            cnt = 1
        drop[cnt] = {
            "id": "mod_update_token_2",
            "before": player_data["tower"]["current"]["reward"]["high"],
            "after": player_data["tower"]["current"]["reward"]["high"] * 2 + player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"] + higher - TOWER_TABLE["detailConst"]["higherItemLimit"],
            "max": True
        }
        player_data["tower"]["current"]["reward"]["high"] = drop[1]["after"]
    else:
        if drop[0]["id"] == "mod_update_token_2":
            cnt = 0
        else:
            cnt = 1
        drop[cnt] = {
            "id": "mod_update_token_2",
            "before": player_data["tower"]["current"]["reward"]["high"],
            "after": player_data["tower"]["current"]["reward"]["high"] + higher,
            "max": False
        }
        player_data["tower"]["current"]["reward"]["high"] = drop[1]["after"]

    return drop


def towerRecord(player_data: dict) -> None:
    if player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        player_data["tower"]["outer"]["training"].update({
            player_data["tower"]["current"]["status"]["tower"]: 1
        })

        player_data["tower"]["outer"]["towers"].update({
            player_data["tower"]["current"]["status"]["tower"]: {
                "best": player_data["tower"]["current"]["status"]["coord"],
                "reward": [],
                "unlockHard": False,
                "hardBest": 0,
            }
        })
    elif player_data["tower"]["current"]["status"]["isHard"]:
        if player_data["tower"]["current"]["status"]["tower"] in player_data["tower"]["outer"]["towers"]:
            if player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["hardBest"] < player_data["tower"]["current"]["status"]["coord"]:
                player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["hardBest"] = player_data["tower"]["current"]["status"]["coord"]
        else:
            pass
    else:
        if player_data["tower"]["current"]["status"]["tower"] in player_data["tower"]["outer"]["towers"]:
            if player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["best"] < player_data["tower"]["current"]["status"]["coord"]:
                player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["best"] = player_data["tower"]["current"]["status"]["coord"]
        else:
            player_data["tower"]["outer"]["towers"].update({
                player_data["tower"]["current"]["status"]["tower"]: {
                    "best": player_data["tower"]["current"]["status"]["coord"],
                    "reward": [],
                    "unlockHard": False,
                    "hardBest": 0,
                }
            })


def towerCreateGame() -> Response:

    data = request.data
    request_data = request.get_json()
    TOWER_TABLE = updateData(TOWER_TABLE_URL, True)

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    selectedTower = request_data["tower"]
    difficulty = request_data["isHard"]

    if selectedTower.split("_")[1] == "tr":
        levels = TOWER_TABLE["towers"][selectedTower]["levels"]
        tactical = {
            "PIONEER": "tatical_pioneer_01",
            "WARRIOR": "tatical_warrior_01",
            "TANK": "tatical_tank_01",
            "SNIPER": "tatical_sniper_01",
            "CASTER": "tatical_caster_01",
            "SUPPORT": "tatical_support_01",
            "MEDIC": "tatical_medic_01",
            "SPECIAL": "tatical_special_01"
        }
        player_data["tower"]["current"]["status"]["tactical"] = tactical
        player_data["tower"]["current"]["status"]["strategy"] = "NONE"
        player_data["tower"]["current"]["status"]["state"] = "STANDBY"
    elif difficulty == 1:
        levels = TOWER_TABLE["towers"][selectedTower]["hardLevels"]
        player_data["tower"]["current"]["status"]["state"] = "INIT_GOD_CARD"
        player_data["tower"]["current"]["status"]["isHard"] = True
    else:
        levels = TOWER_TABLE["towers"][request_data["tower"]]["levels"]
        player_data["tower"]["current"]["status"]["state"] = "INIT_GOD_CARD"
        player_data["tower"]["current"]["status"]["isHard"] = False

    layer = []
    for level in levels:
        layer.append({
            "id": level,
            "try": 0,
            "pass": False
        })
    player_data["tower"]["current"]["layer"] = layer

    player_data["tower"]["current"]["status"]["tower"] = request_data["tower"]
    player_data["tower"]["current"]["status"]["start"] = round(time())

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerBattleStart() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    battleId = str(uuid.uuid1())
    stageId = request_data["stageId"]

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    player_data["tower"]["current"]["layer"][player_data["tower"]["current"]["status"]["coord"]]["try"] += 1

    userData.set_user_data(accounts.get_uid(), player_data)

    TemporaryData.battleInfo_list.update({
        battleId: BattleInfo(stageId, int(time()), request_data)
    })

    data = {
        "battleId": battleId,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerBattleFinish() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

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
    stageId = battleInfo.stage_id

    if stageId.split("_")[-1] == "ex":
        stageCnt = int(stageId.split("_")[-2])
    else:
        stageCnt = int(stageId.split("_")[-1])

    completeState = BattleData["completeState"]
    if server_config["developer"]["debugMode"]:
        completeState = 3

    if completeState == 1:

        data = {
            "drop": [],
            "isNewRecord": False,
            "trap": [],
            "playerDataDelta": {
                "deleted": {},
                "modified": {}
            }
        }
    else:

        trap = []
        player_data["tower"]["current"]["status"]["coord"] += 1
        player_data["tower"]["current"]["layer"][player_data["tower"]["current"]["status"]["coord"] - 1]["pass"] = True

        if stageId.split("_")[1] == "tr":
            player_data["tower"]["current"]["status"]["state"] = "END"
        else:
            changeState(stageCnt, player_data, BattleData, trap)

        drop = []
        if stageId.split("_")[1] == "tr":
            pass
        else:
            towerDropSystem(stageCnt, player_data, drop)

        if player_data["tower"]["current"]["status"]["tower"] in player_data["tower"]["outer"]["towers"]:
            if player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["best"] < player_data["tower"]["current"]["status"]["coord"]:
                isNewRecord = True
            else:
                isNewRecord = False
        else:
            isNewRecord = True

        userData.set_user_data(accounts.get_uid(), player_data)

        data = {
            "isNewRecord": isNewRecord,
            "drop": drop,
            "show": "0",  # TODO: Set to the correct value
            "trap": trap,
            "playerDataDelta": {
                "deleted": {},
                "modified": {
                    "tower": {
                        "current": player_data["tower"]["current"]
                    }
                }
            }
        }

    return data


def towerSettleGame() -> Response:

    data = request.data

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    towerRecord(player_data)

    if not player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        if player_data["tower"]["current"]["status"]["coord"] == len(player_data["tower"]["current"]["layer"]):
            player_data["tower"]["outer"]["towers"][player_data["tower"]["current"]["status"]["tower"]]["unlockHard"] = True
            player_data["tower"]["outer"]["hasTowerPass"] = 1
    else:
        pass

    if player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        pass
    else:
        if player_data["tower"]["current"]["godCard"]["subGodCardId"] == "":
            pass
        else:
            player_data["tower"]["outer"]["pickedGodCard"].setdefault(player_data["tower"]["current"]["godCard"]["id"], [])
            if player_data["tower"]["current"]["godCard"]["subGodCardId"] in player_data["tower"]["outer"]["pickedGodCard"][player_data["tower"]["current"]["godCard"]["id"]]:
                pass
            else:
                player_data["tower"]["outer"]["pickedGodCard"][player_data["tower"]["current"]["godCard"]["id"]].append(player_data["tower"]["current"]["godCard"]["subGodCardId"])

    deleted = {}
    if player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        pass
    else:
        if len(player_data["tower"]["current"]["cards"]) > 0:
            deleted.update({
                "tower": {
                    "current": {
                        "cards": [str(key) for key in player_data["tower"]["current"]["cards"]]
                    }
                }
            })
        else:
            pass

    if player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        reward = {
            "high": {
                "cnt": 0,
                "from": 0,
                "to": 0,
            },
            "low": {
                "cnt": 0,
                "from": 0,
                "to": 0,
            }
        }
    else:
        player_data["tower"]["season"]["period"]["items"].setdefault("mod_update_token_1", 0)
        player_data["tower"]["season"]["period"]["items"].setdefault("mod_update_token_2", 0)

        reward = {
            "high": {
                "cnt": player_data["tower"]["current"]["reward"]["high"],
                "from": player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"],
                "to": player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"] + player_data["tower"]["current"]["reward"]["high"],
            },
            "low": {
                "cnt": player_data["tower"]["current"]["reward"]["low"],
                "from": player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"],
                "to": player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"] + player_data["tower"]["current"]["reward"]["low"],
            }
        }
        player_data["tower"]["season"]["period"]["items"]["mod_update_token_1"] += player_data["tower"]["current"]["reward"]["low"]
        player_data["tower"]["season"]["period"]["items"]["mod_update_token_2"] += player_data["tower"]["current"]["reward"]["high"]

    for i in player_data["tower"]["season"]["period"]["items"]:
        if i == "mod_update_token_1":
            cnt = reward["low"]["cnt"]
        else:
            cnt = reward["high"]["cnt"]
        giveItems(player_data, i, "MATERIAL", cnt, -1, "TOWER_REWARD")

    if player_data["tower"]["current"]["status"]["tower"].split("_")[1] == "tr":
        pass
    else:
        if player_data["tower"]["current"]["status"]["coord"] == len(player_data["tower"]["current"]["layer"]):
            if player_data["tower"]["current"]["status"]["tower"] in player_data["tower"]["season"]["passWithGodCard"][player_data["tower"]["current"]["godCard"]["id"]]:
                pass
            else:
                player_data["tower"]["season"]["passWithGodCard"][player_data["tower"]["current"]["godCard"]["id"]].append(player_data["tower"]["current"]["status"]["tower"])

    player_data["tower"]["current"] = {
        "status": {
            "state": "NONE",
            "tower": "",
            "coord": 0,
            "tactical": {
                "PIONEER": "",
                "WARRIOR": "",
                "TANK": "",
                "SNIPER": "",
                "CASTER": "",
                "SUPPORT": "",
                "MEDIC": "",
                "SPECIAL": ""
            },
            "strategy": "OPTIMIZE",
            "start": 0,
            "isHard": False
        },
        "layer": [],
        "cards": {},
        "godCard": {
            "id": "",
            "subGodCardId": ""
        },
        "halftime": {
            "count": 0,
            "candidate": [],
            "canGiveUp": True
        },
        "trap": [],
        "reward": {
            "high": 0,
            "low": 0
        }
    }

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "reward": reward,
        "ts": round(time()),
        "playerDataDelta": {
            "deleted": deleted,
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"],
                    "outer": player_data["tower"]["outer"],
                    "season": player_data["tower"]["season"]
                }
            }
        }
    }

    return data


def towerInitGodCard() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    player_data["tower"]["current"]["status"]["state"] = "INIT_BUFF"
    player_data["tower"]["current"]["godCard"]["id"] = request_data["godCardId"]
    player_data["tower"]["season"]["passWithGodCard"].setdefault(request_data["godCardId"], [])

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerInitGame() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    player_data["tower"]["current"]["status"]["state"] = "INIT_CARD"
    player_data["tower"]["current"]["status"]["strategy"] = request_data["strategy"]  # TODO: OPTIMIZE, RANDOM
    player_data["tower"]["current"]["status"]["tactical"] = request_data["tactical"]
    player_data["tower"]["outer"]["tactical"] = request_data["tactical"]

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerInitCard() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    player_data["tower"]["current"]["status"]["state"] = "STANDBY"

    cnt = 1
    for slot in request_data["slots"]:
        player_data["tower"]["current"]["cards"][str(cnt)] = {
            "charId": player_data["troop"]["chars"][str(slot["charInstId"])]["charId"],
            "currentEquip": slot["currentEquip"],
            "defaultEquip": slot["skillIndex"],
            "equip": player_data["troop"]["chars"][str(slot["charInstId"])]["equip"],
            "evolvePhase": player_data["troop"]["chars"][str(slot["charInstId"])]["evolvePhase"],
            "favorPoint": player_data["troop"]["chars"][str(slot["charInstId"])]["favorPoint"],
            "instId": str(cnt),
            "level": player_data["troop"]["chars"][str(slot["charInstId"])]["level"],
            "mainSkillLvl": player_data["troop"]["chars"][str(slot["charInstId"])]["mainSkillLvl"],
            "potentialRank": player_data["troop"]["chars"][str(slot["charInstId"])]["potentialRank"],
            "relation": str(slot["charInstId"]),
            "skills": player_data["troop"]["chars"][str(slot["charInstId"])]["skills"],
            "skin": player_data["troop"]["chars"][str(slot["charInstId"])]["skin"],
            "type": "CHAR"
        }
        cnt += 1

    player_data["tower"]["season"]["slots"].setdefault(player_data["tower"]["current"]["status"]["tower"], [])
    found = False
    for cnt, i in enumerate(player_data["tower"]["season"]["slots"][player_data["tower"]["current"]["status"]["tower"]]):
        if i["godCardId"] == player_data["tower"]["current"]["godCard"]["id"]:
            found = True
            player_data["tower"]["season"]["slots"][player_data["tower"]["current"]["status"]["tower"]][cnt]["squad"] = request_data["slots"]
            break
    if not found:
        player_data["tower"]["season"]["slots"][player_data["tower"]["current"]["status"]["tower"]].append({
            "godCardId": player_data["tower"]["current"]["godCard"]["id"],
            "squad": request_data["slots"]
        })

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerChooseSubGodCard() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    player_data["tower"]["current"]["godCard"]["subGodCardId"] = request_data["subGodCardId"]
    player_data["tower"]["current"]["status"]["state"] = "STANDBY"

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerRecruit() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())

    if player_data["tower"]["current"]["halftime"]["count"] == 1:
        player_data["tower"]["current"]["status"]["state"] = "RECRUIT"
        player_data["tower"]["current"]["halftime"]["count"] = 0
    else:
        player_data["tower"]["current"]["status"]["state"] = "STANDBY"

    if request_data["giveUp"] == 1:
        pass
    else:
        cnt = len(player_data["tower"]["current"]["cards"]) + 1
        charInstId = str(player_data["dexNav"]["character"][request_data["charId"]]["charInstId"])
        player_data["tower"]["current"]["cards"][str(cnt)] = {
            "charId": request_data["charId"],
            "currentEquip": player_data["troop"]["chars"][charInstId]["currentEquip"],
            "defaultSkillIndex": player_data["troop"]["chars"][charInstId]["defaultSkillIndex"],
            "equip": player_data["troop"]["chars"][charInstId]["equip"],
            "evolvePhase": player_data["troop"]["chars"][charInstId]["evolvePhase"],
            "favorPoint": player_data["troop"]["chars"][charInstId]["favorPoint"],
            "instId": str(cnt),
            "level": player_data["troop"]["chars"][charInstId]["level"],
            "mainSkillLvl": player_data["troop"]["chars"][charInstId]["mainSkillLvl"],
            "potentialRank": player_data["troop"]["chars"][charInstId]["potentialRank"],
            "relation": charInstId,
            "skills": player_data["troop"]["chars"][charInstId]["skills"],
            "skin": player_data["troop"]["chars"][charInstId]["skin"],
            "type": "CHAR"
        }

    if player_data["tower"]["current"]["status"]["state"] == "RECRUIT":
        createRecruitList(player_data)
    else:
        pass

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "tower": {
                    "current": player_data["tower"]["current"]
                }
            }
        }
    }

    return data


def towerLayerReward() -> Response:

    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    server_config = read_json(CONFIG_PATH)

    if not server_config["server"]["enableServer"]:
        return abort(400)

    result = userData.query_account_by_secret(secret)

    if len(result) != 1:
        return abort(500)

    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    TOWER_TABLE = updateData(TOWER_TABLE_URL, True)

    towerId = request_data["tower"]
    receiveRewards = request_data["layers"]

    for i in receiveRewards:
        player_data["tower"]["outer"]["towers"][towerId]["reward"].append(i)

    items = []
    for i in receiveRewards:
        for j in range(len(TOWER_TABLE["towers"][towerId]["taskInfo"][i - 1]["rewards"])):
            items.append(TOWER_TABLE["towers"][towerId]["taskInfo"][i - 1]["rewards"][j])
    res = {}
    for i in items:
        if i["id"] not in res:
            res[i["id"]] = i
        else:
            res[i["id"]]["count"] += i["count"]
    items = list(res.values())

    for i in items:
        giveItems(player_data, i["id"], i["type"], i["count"], -1, "TOWER_REWARD")

    inventory = {}
    for i in items:
        inventory.update({
            i["id"]: player_data["inventory"][i["id"]]
        })

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "items": items,
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "inventory": inventory,
                "tower": {
                    "outer": player_data["tower"]["outer"]
                }
            }
        }
    }

    return data
