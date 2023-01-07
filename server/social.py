import json
from flask import Response, request, abort

from constants import CONFIG_PATH, CHARACTER_TABLE_URL, MEDAL_TABLE_URL
from utils import read_json
from core.function.update import updateData
from core.database import userData
from core.Account import Account, UserInfo
from core.Search import SearchUidList


def socialSetAssistCharList() -> Response:
    
    data = request.data
    request_data = request.get_json()
    
    secret = request.headers.get("secret")
    assistCharList = request_data["assistCharList"]
    server_config = read_json(CONFIG_PATH)

    CHARACTER_TABLE = updateData(CHARACTER_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    assistChar = {}
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    player_data["social"]["assistCharList"] = assistCharList

    userData.set_user_data(accounts.get_uid(), player_data)

    for index in range(len(assistCharList)):
        if assistCharList[index] is not None:
            charInfo = assistCharList[index]
            charInstId = str(charInfo["charInstId"])
            charId = player_data["troop"]["chars"][charInstId]["charId"]
            charInfo["charId"] = charId
            profession = CHARACTER_TABLE[charId]["profession"]
            
            if profession not in assistChar:
                assistChar[profession] = []

            assistChar[profession].append(charInfo)
            
    userData.set_assist_char_list_data(accounts.get_uid(), assistChar)
    
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "social": player_data["social"]
            }
        }
    }

    return data


def socialGetSortListInfo() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    type = request_data["type"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)

    resultList = []
    infoShare = 0
    accounts = Account(*result[0])
    friend_data = json.loads(accounts.get_friend())
    friend_request = friend_data["request"]
    friend_list = friend_data["list"]
    
    for friend in friend_request:
        result = userData.query_account_by_uid(friend["uid"])
        if len(result) == 0:
            friend_request.remove(friend)
            
    for friend in friend_list:
        result = userData.query_account_by_uid(friend["uid"])
        if len(result) == 0:
            friend_list.remove(friend)

    accounts.set_friend(json.dumps(friend_data))
    userData.set_friend_data(accounts.get_uid(), friend_data)

    if type == 0:
        nickNumber = request_data["param"]["nickNumber"]
        nickName = request_data["param"]["nickName"]

        result = userData.search_player("%" + nickName + "%", "%" + nickNumber + "%")
        if len(result) != 0:
            for n in range(len(result)):
                search = SearchUidList(*result[n])
                if search.get_uid() != accounts.get_uid():
                    friendInfo = {
                        "level": search.get_level(),
                        "uid": str(search.get_uid())
                    }
                    resultList.append(friendInfo)

    if type == 1:
        friendList = json.loads(accounts.get_friend())["list"]

        for index in range(len(friendList)):
            friendUid = str(friendList[index]["uid"])
            result = userData.query_user_info(friendUid)
            userInfo = UserInfo(*result[0])
            userStatus = json.loads(userInfo.get_status())

            result = userData.query_account_by_uid(friendUid)
            friendAccounts = Account(*result[0])
            friend_data = json.loads(friendAccounts.get_user())
            rooms = friend_data["building"]["rooms"]

            if "MEETING" in rooms:
                for item in rooms["MEETING"]:
                    infoShare = rooms["MEETING"][item]["infoShare"]["ts"]
                    break
                
            friendInfo = {
                "level": userStatus["level"],
                "infoShare": infoShare,
                "uid": friendUid
            }
            
            resultList.append(friendInfo)
    
    if type == 2:
        friendRequest = json.loads(accounts.get_friend())["request"]
        resultList = friendRequest
            
    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        },
        "result": resultList
    }

    return data


def socialGetFriendList() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    idList = request_data["idList"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    friends = []
    friendAlias = []
    accounts = Account(*result[0])
    
    for index in range(len(idList)):
        board = []
        infoShare = 0
        friendUid = idList[index]
        medalBoard = {
            "custom": None,
            "template": None,
            "type": "EMPTY"
        }

        result = userData.query_user_info(friendUid)
        userInfo = UserInfo(*result[0])

        result = userData.query_account_by_uid(friendUid)
        friendAccounts = Account(*result[0])
        friend_data = json.loads(friendAccounts.get_user())
        
        teamV2 = friend_data["dexNav"]["teamV2"]
        furn = friend_data["building"]["furniture"]
        rooms = friend_data["building"]["rooms"]
        
        for item in teamV2:
            teamV2[item] = len(teamV2[item].keys())

        if "MEETING" in rooms:
            for item in rooms["MEETING"]:
                board = list(rooms["MEETING"][item]["board"].keys())
                infoShare = rooms["MEETING"][item]["infoShare"]["ts"]
                break
            
        if "medalBoard" in friend_data["social"]:
            custom = friend_data["social"]["medalBoard"]["custom"]
            if custom is not None:
                medalBoard["custom"] = friend_data["medal"]["custom"]["customs"][custom]
                medalBoard["template"] = None
            else:
                medalBoard["template"] = {
                    "groupId": friend_data["social"]["medalBoard"]["template"],
                    "medalList": friend_data["social"]["medalBoard"]["templateMedalList"]
            }
            medalBoard["type"] = friend_data["social"]["medalBoard"]["type"]

        userAssistCharList = json.loads(userInfo.get_social_assist_char_list())
        userStatus = json.loads(userInfo.get_status())
        chars = json.loads(userInfo.get_chars())
        userFriend = json.loads(accounts.get_friend())

        assistCharList = []

        for n in range(len(userAssistCharList)):
            if userAssistCharList[n] is not None:
                charInstId = str(userAssistCharList[n]["charInstId"])
                char_data = chars[charInstId]
                char_data["skillIndex"] = userAssistCharList[n]["skillIndex"]
                assistCharList.append(char_data)
            else:
                assistCharList.append(None)

        friendInfo = {
            "assistCharList": assistCharList,
            "avatar": userStatus["avatar"],
            "avatarId": userStatus["avatarId"],
            "board": board,
            "charCnt": len(chars),
            "friendNumLimit": userStatus["friendNumLimit"],
            "furnCnt": len(furn),
            "infoShare": infoShare,
            "lastOnlineTime": userStatus["lastOnlineTs"],
            "level": userStatus["level"],
            "mainStageProgress": userStatus["mainStageProgress"],
            "medalBoard": medalBoard,
            "nickName": userStatus["nickName"],
            "nickNumber": userStatus["nickNumber"],
            "recentVisited": 0,  # TODO: Set correct data
            "registerTs": userStatus["registerTs"],
            "resume": userStatus["resume"],
            "secretary": userStatus["secretary"],
            "secretarySkinId": userStatus["secretarySkinId"],
            "serverName": "泰拉",
            "teamV2": teamV2,
            "uid": friendUid
        }
        
        friends.append(friendInfo)

        friendList = userFriend["list"]
        
        for n in range(len(friendList)):
            if str(friendList[n]["uid"]) == friendUid:
                friendAlias.append(friendList[n]["alias"])

    data = {
        "friendAlias": friendAlias,
        "friends": friends,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        },
        "resultIdList": idList
    }

    return data
    

def socialSearchPlayer() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    idList = request_data["idList"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    friends = []
    friendStatusList = []
    accounts = Account(*result[0])

    for index in range(len(idList)):
        friendUid = idList[index]
        medalBoard = {
            "custom": None,
            "template": None,
            "type": "EMPTY"
        }
        
        result = userData.query_user_info(friendUid)
        userInfo = UserInfo(*result[0])
        
        result = userData.query_account_by_uid(friendUid)
        friendAccounts = Account(*result[0])
        friend_data = json.loads(friendAccounts.get_user())
            
        if "medalBoard" in friend_data["social"]:
            custom = friend_data["social"]["medalBoard"]["custom"]
            if custom is not None:
                medalBoard["custom"] = friend_data["medal"]["custom"]["customs"][custom]
                medalBoard["template"] = None
            else:
                medalBoard["template"] = {
                    "groupId": friend_data["social"]["medalBoard"]["template"],
                    "medalList": friend_data["social"]["medalBoard"]["templateMedalList"]
            }
            medalBoard["type"] = friend_data["social"]["medalBoard"]["type"]

        userAssistCharList = json.loads(userInfo.get_social_assist_char_list())
        userStatus = json.loads(userInfo.get_status())
        chars = json.loads(userInfo.get_chars())
        userFriend = json.loads(userInfo.get_friend())

        assistCharList = []

        for n in range(len(userAssistCharList)):
            if userAssistCharList[n] is not None:
                charInstId = str(userAssistCharList[n]["charInstId"])
                char_data = chars[charInstId]
                char_data["skillIndex"] = userAssistCharList[n]["skillIndex"]
                assistCharList.append(char_data)
            else:
                assistCharList.append(None)
                
        friendInfo = {
            "assistCharList": assistCharList,
            "avatarId": userStatus["avatarId"],
            "uid": friendUid,
            "friendNumLimit": userStatus["friendNumLimit"],
            "medalBoard": medalBoard,
            "lastOnlineTime": userStatus["lastOnlineTs"],
            "level": userStatus["level"],
            "nickName": userStatus["nickName"],
            "nickNumber": userStatus["nickNumber"],
            "avatar": userStatus["avatar"],
            "resume": userStatus["resume"],
            "serverName": "泰拉",
        }
        friends.append(friendInfo)

        friendRequest = userFriend["request"]
        friendList = userFriend["list"]
        
        is_set = False
        for n in range(len(friendList)):
            if friendList[n]['uid'] == accounts.get_uid():
                friendStatusList.append(2)
                is_set = True
        for n in range(len(friendRequest)):
            if friendRequest[n]['uid'] == accounts.get_uid():
                friendStatusList.append(1)
                is_set = True
        if not is_set:
            friendStatusList.append(0)

    data = {
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        },
        "players": friends,
        "resultIdList": idList,
        "friendStatusList": friendStatusList
    }

    return data


def socialGetFriendRequestList() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    idList = request_data["idList"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    friends = []
    
    for index in range(len(idList)):
        board = []
        infoShare = 0
        friendUid = idList[index]
        medalBoard = {
            "custom": None,
            "template": None,
            "type": "EMPTY"
        }
        
        result = userData.query_user_info(friendUid)
        userInfo = UserInfo(*result[0])

        result = userData.query_account_by_uid(friendUid)
        friendAccounts = Account(*result[0])
        friend_data = json.loads(friendAccounts.get_user())
        
        teamV2 = friend_data["dexNav"]["teamV2"]
        furn = friend_data["building"]["furniture"]
        rooms = friend_data["building"]["rooms"]
        
        for item in teamV2:
            teamV2[item] = len(teamV2[item].keys())
        
        if "MEETING" in rooms:
            for item in rooms["MEETING"]:
                board = list(rooms["MEETING"][item]["board"].keys())
                infoShare = rooms["MEETING"][item]["infoShare"]["ts"]
                break
            
        if "medalBoard" in friend_data["social"]:
            custom = friend_data["social"]["medalBoard"]["custom"]
            if custom is not None:
                medalBoard["custom"] = friend_data["medal"]["custom"]["customs"][custom]
                medalBoard["template"] = None
            else:
                medalBoard["template"] = {
                    "groupId": friend_data["social"]["medalBoard"]["template"],
                    "medalList": friend_data["social"]["medalBoard"]["templateMedalList"]
            }
            medalBoard["type"] = friend_data["social"]["medalBoard"]["type"]

        userAssistCharList = json.loads(userInfo.get_social_assist_char_list())
        userStatus = json.loads(userInfo.get_status())
        chars = json.loads(userInfo.get_chars())

        assistCharList = []

        for n in range(len(userAssistCharList)):
            if userAssistCharList[n] is not None:
                charInstId = str(userAssistCharList[n]["charInstId"])
                char_data = chars[charInstId]
                char_data["skillIndex"] = userAssistCharList[n]["skillIndex"]
                assistCharList.append(char_data)
            else:
                assistCharList.append(None)
                
        friendInfo = {
            "assistCharList": assistCharList,
            "avatar": userStatus["avatar"],
            "avatarId": userStatus["avatarId"],
            "board": board,
            "charCnt": len(chars),
            "friendNumLimit": userStatus["friendNumLimit"],
            "furnCnt": len(furn),
            "infoShare": infoShare,
            "lastOnlineTime": userStatus["lastOnlineTs"],
            "level": userStatus["level"],
            "mainStageProgress": userStatus["mainStageProgress"],
            "medalBoard": medalBoard,
            "nickName": userStatus["nickName"],
            "nickNumber": userStatus["nickNumber"],
            "recentVisited": 0, # TODO: Set correct data
            "registerTs": userStatus["registerTs"],
            "resume": userStatus["resume"],
            "secretary": userStatus["secretary"],
            "secretarySkinId": userStatus["secretarySkinId"],
            "serverName": "泰拉",
            "teamV2": teamV2,
            "uid": friendUid
        }
        
        friends.append(friendInfo)

    data = {
        "requestList": friends,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        },
        "resultIdList": idList
    }

    return data


def socialProcessFriendRequest() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    action = request_data["action"]
    friendId = request_data["friendId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    friend_data = json.loads(accounts.get_friend())
    friendRequest = friend_data["request"]
    friendList = friend_data["list"]
    
    for index in friendList:
        for item in friendRequest:
            if item["uid"] == index["uid"]:
                friendRequest.pop(index)

    for index in range(len(friendRequest)):
        if str(friendRequest[index]["uid"]) == friendId:
            friendRequest.pop(index)
            friend_data["request"] = friendRequest
            
            userData.set_friend_data(accounts.get_uid(), friend_data)
            
            if action == 1:
                friend = {
                    "uid": int(friendId),
                    "alias": None
                }
                friendList.append(friend)
                friend_data["list"] = friendList
                
                userData.set_friend_data(accounts.get_uid(), friend_data)
    
    if action == 1:
        result = userData.query_user_info(friendId)
        userInfo = UserInfo(*result[0])

        _fdata = json.loads(userInfo.get_friend())
        _flist = _fdata["list"]
        _freq = _fdata["request"]
        
        for m, n in enumerate(_freq):
            if n["uid"] == accounts.get_uid():
                _freq.pop(m)
        
        friend = {
            "uid": accounts.get_uid(),
            "alias": None
        }
        _flist.append(friend)
        _fdata["list"] = _flist
        _fdata["request"] = _freq
        
        userData.set_friend_data(friendId, _fdata)

    if len(friendRequest) == 0:
        player_data["pushFlags"]["hasFriendRequest"] = 0

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "friendNum": len(friendList),
        "playerDataDelta": {
            "deleted": {},
            "modified": {
                "pushFlags": player_data["pushFlags"]
            }
        }
    }

    return data


def socialSendFriendRequest() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    friendId = request_data["friendId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    result = userData.query_user_info(friendId)
    userInfo = UserInfo(*result[0])

    result = userData.query_account_by_uid(friendId)
    friendAccounts = Account(*result[0])

    friend_data = json.loads(userInfo.get_friend())
    friendRequest = friend_data["request"]
    friendList = friend_data["list"]
    
    if len(friendList) == json.loads(friendAccounts.get_user())["status"]["friendNumLimit"] or len(json.loads(accounts.get_friend())["list"]) == player_data["status"]["friendNumLimit"]:
        data = {
            "result": 1,
            "error": "好友数量达到上限，无法发送好友申请"
        }
        return data
    
    for index in range(len(friendList)):
        if friendList[index]["uid"] == accounts.get_uid():
            data = {
                "result": 3,
                "error": "好友已添加"
            }
            return data

    for index in range(len(friendRequest)):
        if friendRequest[index]["uid"] == accounts.get_uid():
            data = {
                "result": 2,
                "error": "好友申请已发送"
            }
            return data

    req = {"uid": accounts.get_uid()}
    friendRequest.append(req)

    friend_data["request"] = friendRequest
    
    userData.set_friend_data(friendId, friend_data)
    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def socialSetFriendAlias() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    alias = request_data["alias"]
    friendId = request_data["friendId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    result = userData.query_user_info(accounts.get_uid())
    userInfo = UserInfo(*result[0])

    friend_data = json.loads(userInfo.get_friend())
    friendList = friend_data["list"]

    for index in range(len(friendList)):
        if str(friendList[index]["uid"]) == friendId:
            friendList[index]["alias"] = alias

    friend_data["list"] = friendList
    
    userData.set_friend_data(accounts.get_uid(), friend_data)
    userData.set_user_data(accounts.get_uid(), player_data)
    
    data = {
        "result": 0,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def socialDeleteFriend() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    friendId = request_data["friendId"]
    server_config = read_json(CONFIG_PATH)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    result = userData.query_user_info(accounts.get_uid())
    userInfo = UserInfo(*result[0])

    friend_data = json.loads(userInfo.get_friend())
    friendList = friend_data["list"]
    
    for index in range(len(friendList)):
        if str(friendList[index]["uid"]) == friendId:
            friendList.pop(index)

    friend_data["list"] = friendList

    userData.set_friend_data(accounts.get_uid(), friend_data)
    
    result = userData.query_user_info(friendId)
    userFriend = UserInfo(*result[0])

    friend_data = json.loads(userFriend.get_friend())
    friendList = friend_data["list"]

    for index in range(len(friendList)):
        if friendList[index]["uid"] == accounts.get_uid():
            friendList.pop(index)

    friend_data["list"] = friendList
    
    userData.set_friend_data(friendId, friend_data)
    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "result": 0,
        "playerDataDelta": {
            "deleted": {},
            "modified": {}
        }
    }

    return data


def socialSetCardShowMedal() -> Response:
    
    data = request.data
    request_data = request.get_json()

    secret = request.headers.get("secret")
    customIndex = request_data["customIndex"]
    templateGroup = request_data["templateGroup"]
    type = request_data["type"]
    server_config = read_json(CONFIG_PATH)

    MEDAL_TABLE = updateData(MEDAL_TABLE_URL, True)
    
    if not server_config["server"]["enableServer"]:
        return abort(400)
    
    result = userData.query_account_by_secret(secret)
    
    if len(result) != 1:
        return abort(500)
    
    accounts = Account(*result[0])
    player_data = json.loads(accounts.get_user())
    medal_data = MEDAL_TABLE
    medalBoard = player_data["social"]["medalBoard"]
    medalBoard["type"] = type

    if type == "TEMPLATE":
        medalBoard["custom"] = None
        medalBoard["template"] = templateGroup
        templateMedalList = []
        
        if "Activity" in templateGroup:
            medalGroupId = "activityMedal"
        if "Rogue" in templateGroup:
            medalGroupId = "rogueMedal"
    
        for item in medal_data["medalTypeData"][medalGroupId]["groupData"]:
            if item["groupId"] == templateGroup:
                medalIdList = item["medalId"]

        for index in medalIdList:
            for item in medal_data["medalList"]:
                if item["medalId"] == index and item["advancedMedal"] is not None:
                    medalIdList.append(item["advancedMedal"])

        for item in medalIdList:
            if item in player_data["medal"]["medals"]:
                templateMedalList.append(item)

        medalBoard["templateMedalList"] = templateMedalList
    elif type == "CUSTOM":
        medalBoard["custom"] = customIndex
        medalBoard["template"] = None
        medalBoard["templateMedalList"] = None
    else:
        medalBoard["custom"] = None
        medalBoard["template"] = None
        medalBoard["templateMedalList"] = None

    userData.set_user_data(accounts.get_uid(), player_data)

    data = {
        "playerDataDelta":{
            "deleted": {},
            "modified": {
                "social": {
                    "medalBoard": medalBoard
                }
            }
        }
    }

    return data