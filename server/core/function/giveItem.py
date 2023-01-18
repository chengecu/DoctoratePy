from time import time
from typing import Dict, List, Tuple, Union

from constants import (CHARACTER_TABLE_URL, CHARWORD_TABLE_URL,
                       EQUIP_TABLE_URL, GAMEDATA_CONST_URL)
from core.function.update import updateData
from logger import writeLog


def giveItems(player_data: Dict,
              reward_id: str = None,
              reward_type: str = None,
              reward_count: int = 0,
              activity_id: str = None,
              activity_type: str = None,
              time_limit: int = -1,
              status: str = "OTHERS") -> Union[List, Dict, Tuple]:
    '''
    status:
        "GET_GACHA_CHAR" -> charGet - Dict
        "GET_ITEM" -> items - List [Normal]
        "OTHERS" -> player_data - Dict
    '''

    items = []

    if reward_type == "CHAR":
        CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
        CHARWORD_TABLE = updateData(CHARWORD_TABLE_URL, True)
        EQUIP_TABLE = updateData(EQUIP_TABLE_URL, True)

        charGet = {}
        chars = player_data["troop"]["chars"]
        dexNav = player_data["dexNav"]
        random_char_id = reward_id
        repeatCharId = 0

        for index in range(len(player_data["troop"]["chars"])):
            if player_data["troop"]["chars"][str(index + 1)]["charId"] == random_char_id:
                repeatCharId = index + 1
                break

        if repeatCharId == 0:
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
                "defaultSkillIndex": 0,
                "voiceLan": CHARWORD_TABLE["charDefaultTypeDict"][random_char_id],
                "currentEquip": None,
                "equip": {},
                "starMark": 0
            }

            if skills == []:
                char_data["defaultSkillIndex"] = -1

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

            player_data["troop"]["chars"][str(instId)] = char_data
            player_data["troop"]["charGroup"][random_char_id] = {"favorPoint": 0}

            # TODO: Add building

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
            chars[str(instId)] = char_data

            items.append({
                "id": random_char_id,
                "type": reward_type,
                "count": reward_count,
                "charGet": charGet
            })
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

            player_data["status"][itemName] += itemCount

            new_item_get_2 = {
                "type": "MATERIAL",
                "id": f"p_{random_char_id}",
                "count": 1
            }
            item_get.append(new_item_get_2)
            get_char["itemGet"] = item_get
            player_data["inventory"][f"p_{random_char_id}"] = player_data["inventory"].get(f"p_{random_char_id}", 0) + 1

            charGet = get_char
            chars[str(repeatCharId)] = player_data["troop"]["chars"][str(repeatCharId)]

            items.append({
                "id": random_char_id,
                "type": reward_type,
                "count": reward_count,
                "charGet": charGet
            })

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
                if team:
                    dexNav["teamV2"][team] = dexNav["teamV2"].get(team, {})
                    dexNav["teamV2"][team][str(instId)] = 1
        else:
            dexNav["character"][random_char_id]["count"] += 1

    elif reward_type == "CHAR_SKIN":
        player_data["skin"]["characterSkins"][reward_id] = 1
        player_data["skin"]["skinTs"][reward_id] = int(time())

    elif reward_type == "GOLD":
        player_data["status"]["gold"] += reward_count

    elif reward_type == "LGG_SHD":
        player_data["status"]["lggShard"] += reward_count

    elif reward_type == "HGG_SHD":
        player_data["status"]["hggShard"] += reward_count

    elif reward_type == "DIAMOND":
        player_data["status"]["androidDiamond"] += reward_count
        player_data["status"]["iosDiamond"] += reward_count

    elif reward_type == "DIAMOND_SHD":
        player_data["status"]["diamondShard"] += reward_count

    elif reward_type == "TKT_TRY":
        player_data["status"]["practiceTicket"] += reward_count

    elif reward_type == "TKT_RECRUIT":
        player_data["status"]["recruitLicense"] += reward_count

    elif reward_type == "TKT_INST_FIN":
        player_data["status"]["instantFinishTicket"] += reward_count

    elif reward_type == "TKT_GACHA":
        player_data["status"]["gachaTicket"] += reward_count

    elif reward_type == "TKT_GACHA_10":
        player_data["status"]["tenGachaTicket"] += reward_count

    elif reward_type == "AP_GAMEPLAY":
        player_data["status"]["ap"] += reward_count

    elif reward_type == "AP_BASE":
        value = player_data["building"]["status"]["labor"]["value"]
        maxValue = player_data["building"]["status"]["labor"]["maxValue"]
        if value + reward_count > maxValue:
            player_data["building"]["status"]["labor"]["value"] = maxValue
        else:
            player_data["building"]["status"]["labor"]["value"] += reward_count

    elif reward_type == "AP_ITEM":
        if "60" in reward_id:
            player_data["status"]["ap"] += 60
        elif "200" in reward_id:
            player_data["status"]["ap"] += 200
        else:
            player_data["status"]["ap"] += 100

    elif reward_type == "SOCIAL_PT":
        player_data["status"]["socialPoint"] += reward_count

    elif reward_type == "FURN":
        furniture = player_data["building"]["furniture"].setdefault(reward_id, {"count": 0, "inUse": 0})
        furniture["count"] += reward_count
        player_data["building"]["solution"]["furnitureTs"].update({
            reward_id: int(time())
        })

    elif reward_type == "EXP_PLAYER":
        GAMEDATA_CONST = updateData(GAMEDATA_CONST_URL, True)

        playerExpMap = GAMEDATA_CONST["playerExpMap"]
        playerApMap = GAMEDATA_CONST["playerApMap"]
        maxPlayerLevel = GAMEDATA_CONST["maxPlayerLevel"]
        exp = player_data["status"]["exp"]
        level = player_data["status"]["level"]

        if level < maxPlayerLevel and reward_count != 0:
            player_data["status"]["exp"] = exp + reward_count
            for index in range(len(playerExpMap)):
                if level == index + 1:
                    if (int(playerExpMap[index]) - player_data["status"]["exp"]) <= 0:
                        if (index + 2) == maxPlayerLevel:
                            player_data["status"]["level"] = maxPlayerLevel
                            player_data["status"]["exp"] = 0
                            player_data["status"]["maxAp"] = playerApMap[index + 1]
                            player_data["status"]["ap"] += player_data["status"]["maxAp"]
                        else:
                            player_data["status"]["level"] = (index + 2)
                            player_data["status"]["exp"] -= int(playerExpMap[index])
                            player_data["status"]["maxAp"] = playerApMap[index + 1]
                            player_data["status"]["ap"] += player_data["status"]["maxAp"]
                        player_data["status"]["lastApAddTime"] = int(time())
                    break

    elif reward_type in ["AP_SUPPLY", "EXTERMINATION_AGENT", "RENAMING_CARD", "TKT_GACHA_PRSV", "ITEM_PACK",
                         "LMTGS_COIN", "LIMITED_TKT_GACHA_10", "LINKAGE_TKT_GACHA_10", "VOUCHER_PICK",
                         "VOUCHER_LEVELMAX_6", "VOUCHER_LEVELMAX_5", "VOUCHER_ELITE_II_5", "VOUCHER_SKIN",
                         "VOUCHER_CGACHA", "OPTIONAL_VOUCHER_PICK", "VOUCHER_MGACHA", "ACTIVITY_POTENTIAL"]:
        consumable_set = set(int(list(item.keys())[0]) for item in player_data["consumable"].values() if item != {})
        consumableId = str(max(consumable_set) + 1) if consumable_set else '1'
        player_data["consumable"][reward_id] = {
            consumableId: {
                "ts": time_limit,
                "count": reward_count
            }
        }

    elif reward_type in ["CARD_EXP", "EPGS_COIN", "REP_COIN", "RETRO_COIN",
                         "MATERIAL", "VOUCHER_FULL_POTENTIAL"]:
        player_data["inventory"][reward_id] = player_data["inventory"].get(reward_id, 0) + reward_count

    elif reward_type in ["CRS_SHOP_COIN", "CRS_RUNE_COIN", "UNI_COLLECTION",
                         "ACTIVITY_COIN", "ET_STAGE", "RL_COIN", "RETURN_CREDIT",
                         "MEDAL"]:
        writeLog("\033[1;31mValue error: Item type not supported.\033[0;0m", "error")  # TODO
        return []

    elif reward_type == "ACTIVITY_ITEM":
        if activity_type == "BOSS_RUSH":
            BOSS_RUSH = player_data["activity"]["BOSS_RUSH"]
            if "milestone_point" in reward_id:
                BOSS_RUSH[activity_id]["milestone"]["point"] += reward_count
            elif "token_relic" in reward_id:
                BOSS_RUSH[activity_id]["relic"]["token"]["current"] += reward_count
                BOSS_RUSH[activity_id]["relic"]["token"]["total"] += reward_count
            elif "relic" in reward_id:
                BOSS_RUSH[activity_id]["relic"]["level"][reward_id] = reward_count

    if reward_type != "CHAR":
        item = {
            "id": reward_id,
            "type": reward_type,
            "count": reward_count
        }
        items.append(item)

    if status == "GET_ITEM":
        if reward_count != 0:
            return items
        else:
            return []
    elif status == "GET_GACHA_CHAR":
        return charGet
    else:
        return player_data
