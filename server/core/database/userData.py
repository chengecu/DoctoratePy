import json
import pymysql

from typing import List
from constants import CONFIG_PATH
from utils import read_json
from core.Account import Account, UserInfo
from core.Search import SearchUidList, SearchAssistCharList

        
def getConnection():

    database_config = read_json(CONFIG_PATH)["database"]
    
    connection =pymysql.connect(
        host=database_config["host"],
        port=database_config["port"],
        db="DoctoratePy",
        user=database_config["user"],
        password=database_config["password"]
    )
    return connection


def query_account_by_secret(secret: str) -> List[Account]:
    
    try:
        sql = "SELECT * FROM account WHERE secret = %s"
        params = (secret,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result


def query_account_by_phone(phone: str) -> List[Account]:

    try:
        sql = "SELECT * FROM account WHERE phone = %s"
        params = (phone,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result


def query_account_by_uid(uid: int) -> List[Account]:

    try:
        sql = "SELECT * FROM account WHERE uid = %s"
        params = (uid,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result
    
    
def query_nick_name(nick_name: str) -> List:

    try:
        sql = "SELECT uid FROM account WHERE user -> '$.status.nickName' = %s"
        params = (nick_name,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result

    
def query_user_info(uid: int) -> List[UserInfo]:
    
    try:
        sql = "SELECT uid as uid,user -> '$.status' as status, user -> '$.troop.chars' as chars, user -> '$.social.assistCharList' as social_assist_char_list,assistCharList as assist_char_list,friend as friend FROM account WHERE uid = %s"
        params = (uid,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        
    finally:
        cursor.close()
        connection.close()
        return result

    
def search_player(nick_name: str, nick_number: str) -> List[SearchUidList]:

    try:
        sql = "SELECT uid as uid,user -> '$.status.level' as level FROM account  WHERE user -> '$.status.nickName' LIKE %s AND user -> '$.status.nickNumber' LIKE %s"
        params = (nick_name, nick_number)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result


def search_assist_char_list(profession: str) -> List[SearchAssistCharList]:
    
    try:
        sql = "SELECT uid as uid,user -> '$.status' as status, user -> '$.troop.chars' as chars, user -> '$.social.assistCharList' as social_assist_char_list, assistCharList -> %s as assist_char_list FROM account WHERE assistCharList -> %s"
        params = (profession, profession)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result
    

def register_account(phone: str, password: str, secret: str) -> int:
    
    try:
        sql = "INSERT INTO account (`phone`, `password`, `secret`, `user`, `mails`, `assistCharList`, `friend`, `ban`) VALUES (%s, %s, %s, '{}', '[]', '{}', '{\"list\":[],\"request\":[]}', 0)"
        params = (phone, password, secret)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        result = cursor.rowcount
    
    finally:
        cursor.close()
        connection.close()
        return result 


def login_account(phone: str, password: str) -> List[Account]:

    try:
        sql = "SELECT * FROM account WHERE `phone` = %s and `password` = %s"
        params = (phone, password)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        
    finally:
        cursor.close()
        connection.close()
        return result

    
def set_user_data(uid: int, user_data: dict) -> int:
    
    try:
        sql = "UPDATE account SET user = %s WHERE uid = %s"
        params = (json.dumps(user_data, ensure_ascii=False), uid)
        connection = getConnection()
        cursor = connection.cursor()
        result = cursor.execute(sql, params)
        connection.commit()
        
    finally:
        cursor.close()
        connection.close()
        return result


def set_friend_data(uid: int, friend_data: dict) -> int:
    
    try:
        sql = "UPDATE account SET friend = %s WHERE uid = %s"
        params = (json.dumps(friend_data, ensure_ascii=False), uid)
        connection = getConnection()
        cursor = connection.cursor()
        result = cursor.execute(sql, params)
        connection.commit()
        
    finally:
        cursor.close()
        connection.close()
        return result

    
def set_assist_char_list_data(uid: int, assist_char_list: dict) -> int:
    
    try:
        sql = "UPDATE account SET assistCharList = %s WHERE uid = %s"
        params = (json.dumps(assist_char_list, ensure_ascii=False), uid)
        connection = getConnection()
        cursor = connection.cursor()
        result = cursor.execute(sql, params)
        connection.commit()
        
    finally:
        cursor.close()
        connection.close()
        return result


def table_exists(table_name: str) -> bool:
    
    try:
        sql = "SHOW TABLES LIKE %s"
        params = (table_name,)
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
    
    finally:
        cursor.close()
        connection.close()
        return result


#### TODO: Add more functions ####