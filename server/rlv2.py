import random

from flask import request

from constants import RLV2_CONFIG_PATH, RLV2_JSON_PATH, RL_TABLE_URL, \
                    RLV2_CHOICEBUFFS, RLV2_RECRUITGROUPS
from rlUtils import process_buff, update_recruit, generate_recruit_list, \
                    generate_zone_map
from utils import read_json, write_json
from core.function.update import updateData


def rlv2CreateGame():

    data = request.data
    request_data = request.get_json()
    rlv2_config = read_json(RLV2_CONFIG_PATH)
    start_options = {}

    RL_TABLE = updateData(RL_TABLE_URL, True)
    
    for init_detail in RL_TABLE["details"][request_data["theme"]]["init"]:
        if (
            init_detail["modeId"] == request_data["mode"] and 
            init_detail["predefinedId"] == request_data["predefinedId"]
        ):
            start_options = init_detail
            break
    
    rlv2 = {
        "outer": {
            "rogue_1": {
                "record": {
                    "last": 0,
                    "modeCnt": {},
                    "endingCnt": {},
                    "stageCnt": {},
                    "bandCnt": {}
                }
            }
        },
        "current": {
            "player": {
                "state": "INIT",
                "property": {
                    "exp": 0,
                    "level": 1,
                    "hp": start_options["initialHp"] + rlv2_config["bonus"]["hp"],
                    "gold": start_options["initialGold"] + rlv2_config["bonus"]["gold"],
                    "capacity": start_options["initialSquadCapacity"] +  + rlv2_config["bonus"]["capacity"],
                    "population": {
                        "cost": 0,
                        "max": start_options["initialPopulation"]
                    },
                    "conPerfectBattle": 0
                },
                "cursor": {
                    "zone": 0,
                    "position": None
                },
                "trace": [],
                "pending": [],
                "status": {
                    "bankPut": 0
                },
                "toEnding": "ro_ending_1",
                "chgEnding": None
            },
            "map": {
                "zones": {}
            },
            "troop": {
                "chars": {}
            },
            "inventory": {
                "relic": {},
                "recruit": {},
                "trap": None
            },
            "game": {
                "mode": "NORMAL",
                "predefined": None,
                "theme": "rogue_1",
                "outer": {
                    "support": True
                },
                "start": 0
            },
            "buff": {
                "tmpHP": 0 + rlv2_config["bonus"]["tmpHP"],
                "capsule": None
            },
            "record": {
                "brief": None
            }
        }
    }
    init_items = {}
    
    current_step = 1
    steps = 3
    if rlv2_config["intialSupport"]: steps = 4

    for init_item in start_options["initialBandRelic"]:
        init_items.update({
            str(start_options["initialBandRelic"].index(init_item)): {
                "id": init_item,
                "count": 1
            }
        })

    rlv2["current"]["player"]["pending"].append({
        "index": "e_" + str(current_step - 1),
        "type": "GAME_INIT_RELIC",
        "content": {
            "initRelic": {
                "step": [current_step, steps],
                "items": init_items
            }
        }
    })
    current_step += 1

    if rlv2_config["intialSupport"]:
        rlv2["current"]["player"]["pending"].append({
            "index": "e_" + str(current_step - 1),
            "type": "GAME_INIT_SUPPORT",
            "content": {
                "initSupport": {
                    "step": [current_step, steps],
                    "scene": {
                        "id": "scene_startbuff_enter",
                        "choices": {}
                    }
                }
            }
        })

        initial_supports = [
            "choice_startbuff_1",
            "choice_startbuff_2",
            "choice_startbuff_3",
            "choice_startbuff_4",
            "choice_startbuff_5",
            "choice_startbuff_6"
        ]
        for init_support in initial_supports:
            rlv2["current"]["player"]["pending"][-1]["content"]["initSupport"]["scene"]["choices"].update({init_support: 1})
        
        current_step += 1
    
    rlv2["current"]["player"]["pending"].append({
        "index": "e_" + str(current_step - 1),
        "type": "GAME_INIT_RECRUIT_SET",
        "content": {
            "initRecruitSet": {
                "step": [current_step, steps],
                "option": start_options["initialRecruitGroup"]
            }
        }
    })
    current_step += 1

    rlv2["current"]["player"]["pending"].append({
        "index": "e_" + str(current_step - 1),
        "type": "GAME_INIT_RECRUIT",
        "content": {
            "initRecruit": {
                "step": [current_step, steps],
                "tickets": []
            }
        }
    })

    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": rlv2,
            },
            "deleted": {}
        }
    }

    write_json(rlv2, RLV2_JSON_PATH)

    return data

def rlv2ChooseInitialRelic():

    data = request.data
    chosenRelic = request.get_json()

    is2_data = read_json(RLV2_JSON_PATH)
    init_relic = is2_data["current"]["player"]["pending"].pop(0)

    relic = {
        "relic": True,
        "items": [{
            "id": init_relic["content"]["initRelic"]["items"][chosenRelic["select"]]["id"],
            "count": 1
        }]
    }

    is2_data = process_buff(is2_data, relic)
    write_json(is2_data, RLV2_JSON_PATH)
    
    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data

def rlv2SelectChoice():

    data = request.data
    chosen_choice = request.get_json()["choice"]

    is2_data = read_json(RLV2_JSON_PATH)
    buff_list = read_json(RLV2_CHOICEBUFFS)
    is2_data["current"]["player"]["pending"].pop(0)

    is2_data = process_buff(is2_data, buff_list[chosen_choice])
    write_json(is2_data, RLV2_JSON_PATH)
    
    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    if buff_list[chosen_choice]["relic"]:
        data.update({
            "items": buff_list[chosen_choice]["items"]
        })
        data.update({
            "pushMessage": [{
                "path": "rlv2GotRandRelic",
                "payload": {
                    "idList": [buff_list[chosen_choice]["items"][0]["id"]]
                }
            }]
        })

    return data

def rlv2ChooseInitialRecruitSet():

    data = request.data
    chosen_recruit = request.get_json()["select"]

    recruit_data = read_json(RLV2_RECRUITGROUPS)
    is2_data = read_json(RLV2_JSON_PATH)

    is2_data["current"]["player"]["pending"].pop(0)

    init_recruit_list = recruit_data["RecruitSet"][chosen_recruit]
    chosen_recruit_list = []
    if chosen_recruit == "recruit_group_random":
        chosen_recruit_list += random.choices(init_recruit_list["special"], k=1)
        chosen_recruit_list += random.choices(init_recruit_list["normal"], k=2)
    else:
        chosen_recruit_list = init_recruit_list

    is2_data = update_recruit(is2_data, chosen_recruit_list)
    write_json(is2_data, RLV2_JSON_PATH)
    
    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data

def rlv2ActiveRecruitTicket():

    data = request.data
    chosenRecruit = request.get_json()["id"]

    is2_data = read_json(RLV2_JSON_PATH)
    chosenTicket = is2_data["current"]["inventory"]["recruit"][chosenRecruit]["id"]

    recruitCharList = generate_recruit_list(is2_data, chosenTicket)

    eventNums = [event["index"].split("e_")[1] for event in is2_data["current"]["player"]["pending"]]
    eventNums.sort()

    is2_data["current"]["inventory"]["recruit"][chosenRecruit]["list"] = recruitCharList
    is2_data["current"]["player"]["pending"].insert(0, {
        "index": "e_" + str(int(eventNums[-1]) + 1),
        "type": "RECRUIT",
        "content": {
            "recruit": {
                "ticket": chosenRecruit
            }
        }
    })

    write_json(is2_data, RLV2_JSON_PATH)
    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data

def rlv2RecruitChar():

    data = request.data
    chosenRecruit = request.get_json()

    is2_data = read_json(RLV2_JSON_PATH)

    chosenChar = is2_data["current"]["inventory"]["recruit"][chosenRecruit["ticketIndex"]]["list"][int(chosenRecruit["optionId"])]
    is2_data["current"]["inventory"]["recruit"][chosenRecruit["ticketIndex"]]["result"] = chosenChar
    tempInstId = chosenChar["instId"]

    keyCount = len(list(is2_data["current"]["troop"]["chars"].keys()))
    chosenChar["instId"] = keyCount+1
    is2_data["current"]["troop"]["chars"].update({
        str(keyCount+1): chosenChar
    })
    
    is2_data["current"]["player"]["pending"].pop(0)
    is2_data["current"]["player"]["property"]["population"]["cost"] += chosenChar["population"]
    is2_data["current"]["inventory"]["recruit"][chosenRecruit["ticketIndex"]]["state"] = 2
    is2_data["current"]["inventory"]["recruit"][chosenRecruit["ticketIndex"]]["list"] = []

    write_json(is2_data, RLV2_JSON_PATH)

    data = {
        "chars": [chosenChar],
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }
    data["chars"][0]["instId"] = tempInstId

    return data

def rlv2CloseRecruitTicket():

    data = request.data
    chosenRecruit = request.get_json()

    is2_data = read_json(RLV2_JSON_PATH)
    
    is2_data["current"]["player"]["pending"].pop(0)
    is2_data["current"]["inventory"]["recruit"][chosenRecruit["id"]]["state"] = 2
    is2_data["current"]["inventory"]["recruit"][chosenRecruit["id"]]["list"] = []

    write_json(is2_data, RLV2_JSON_PATH)

    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data

def rlv2FinishEvent():

    data = request.data

    is2_data = read_json(RLV2_JSON_PATH)

    is2_data["current"]["player"]["state"] = "WAIT_MOVE"
    is2_data["current"]["player"]["pending"] = []

    if not is2_data["current"]["player"]["cursor"]["zone"]:
        is2_data["current"]["player"]["cursor"]["zone"] = 1

    is2_data["current"]["map"] = {
        "zones": {
            "1": {
                "id": "zone_1",
                "index": 1,
                "nodes": generate_zone_map(1)
            }
        }
    }

    write_json(is2_data, RLV2_JSON_PATH)

    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data

def rlv2MoveAndBattleStart():

    data = request.data
    request_data = request.get_json()

    is2_data = read_json(RLV2_JSON_PATH)

    is2_data["battleId"] = "1234567890-abcd-abcd-1234567890"
    is2_data["current"]["player"]["state"] = "PENDING"
    is2_data["current"]["player"]["cursor"]["position"] = request_data["to"]
    is2_data["current"]["player"]["trace"].append({
        "zone": is2_data["current"]["player"]["cursor"]["zone"],
        "position": request_data["to"]
    })
    is2_data["current"]["player"]["pending"].append({
        "index": "e_1",
        "type": "BATTLE",
        "content": {
            "battle": {
                "state": 1,
                "chestCnt": 5,
                "goldTrapCnt": 5,
                "tmpChar": [],
                "unKeepBuff": [
                {
                    "key": "char_attribute_mul",
                    "blackboard": [
                        {
                            "key": "selector.profession",
                            "valueStr": "warrior|sniper|tank|medic|support|caster|special|pioneer"
                        },
                        {
                            "key": "respawn_time",
                            "value": -1.0
                        },
                        {
                            "key": "cost",
                            "value": -50.0
                        }
                    ]
                },
                {
                    "key": "char_attribute_add",
                    "blackboard": [
                        {
                            "key": "attack_speed",
                            "value": 500
                        },
                        {
                            "key": "stack_by_res",
                            "valueStr": "rogue_1_gold"
                        },
                        {
                            "key": "stack_by_res_cnt",
                            "value": 0
                        }
                    ]
                },
                {
                    "key": "global_buff_normal",
                    "blackboard": [
                        {
                            "key": "key",
                            "valueStr": "damage_resistance[filter_tag]"
                        },
                        {
                            "key": "tag",
                            "valueStr": "originiumartscraft"
                        },
                        {
                            "key": "damage_resistance",
                            "value": 1.0
                        },
                        {
                            "key": "selector.profession",
                            "valueStr": "warrior|sniper|tank|medic|support|caster|special|pioneer"
                        }
                    ]
                },
                {
                    "key": "level_init_cost_add",
                    "blackboard": [
                        {
                            "key": "value",
                            "value": 99.0
                        }
                    ]
                },
                {
                    "key": "global_buff_stack",
                    "blackboard": [
                        {
                            "key": "key",
                            "valueStr": "modify_sp[born]"
                        },
                        {
                            "key": "selector.profession",
                            "valueStr": "warrior|sniper|tank|medic|support|caster|special|pioneer"
                        },
                        {
                            "key": "sp",
                            "value": 50.0
                        }
                    ]
                }
                ]
            }
        }
    })

    write_json(is2_data, RLV2_JSON_PATH)

    data = {
        "playerDataDelta": {
            "modified": {
                "rlv2": is2_data,
            },
            "deleted": {}
        }
    }

    return data
