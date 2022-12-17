import json
import pymysql

from typing import List
from constants import CONFIG_PATH
from utils import read_json
from core.Account import Account

        
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
    
    
def query_nick_name(nick_name: str):

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


def register_account(phone, password, secret):
    
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


def login_account(phone, password):

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


def set_user_data(uid, user_data):
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


def table_exists(table_name):
    
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


#### TODO ####