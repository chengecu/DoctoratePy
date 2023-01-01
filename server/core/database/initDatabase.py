import pymysql

from constants import CONFIG_PATH
from utils import read_json
from core.database.userData import table_exists

database_config = read_json(CONFIG_PATH)["database"]

connection = pymysql.connect(
    host=database_config["host"],
    port=database_config["port"],
    user=database_config["user"],
    password=database_config["password"],
)


def initDB():

    try:
        cursor = connection.cursor()
        cursor.execute(r"CREATE DATABASE IF NOT EXISTS DoctoratePy")
        cursor.execute(r"USE DoctoratePy")
        cursor.execute(r"SHOW TABLES")
        if len(table_exists("account")) != 1:
            insertUserTable()
        if len(table_exists("mail")) != 1:
            insertMailTable()
        
    finally:
        cursor.close()
        connection.close()
    
    
def insertUserTable():

    cursor = connection.cursor()
    cursor.execute("SET NAMES utf8mb4")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DROP TABLE IF EXISTS `account`")
    cursor.execute("""CREATE TABLE `account` (
    `uid` INT NOT NULL AUTO_INCREMENT,
    `phone` VARCHAR ( 255 ) CHARACTER 
    SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
    `password` VARCHAR ( 255 ) CHARACTER 
    SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
    `secret` VARCHAR ( 255 ) CHARACTER 
    SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
    `user` json NULL,
    `mails` json NULL,
    `assistCharList` json NULL,
    `friend` json NULL,
    `ban` INT NULL DEFAULT NULL,
    PRIMARY KEY USING BTREE ( `uid` ) 
    ) ENGINE = INNODB AUTO_INCREMENT = 3 CHARACTER 
    SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;""")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.execute("ALTER TABLE account auto_increment=100000000")
    cursor.close()


def insertMailTable():

    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE mail (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name TEXT NULL,
        `from` TEXT NULL,
        subject TEXT NULL,
        content TEXT NULL,
        items JSON NULL
    );""")
    cursor.close()