import os
import socket
import requests
from flask import abort

from datetime import datetime
from utils import read_json, write_json
from constants import CONFIG_PATH

from . import loadMods


def writeLog(data):

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def updateData(url: str, use_local: bool = False):

    BASE_URL_LIST = [
        ("https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata", './data'),
        ("https://ak-conf.hypergryph.com/config/prod/announce_meta/Android", './data/announce')
    ]

    for index in BASE_URL_LIST:
        if index[0] in url:
            if not os.path.isdir(index[1]):
                os.makedirs(index[1])
            localPath = url.replace(index[0], index[1])
            break

    if not os.path.isdir('./data/excel/'):
        os.makedirs('./data/excel/')

    if use_local:
        try:
            data = read_json(localPath, encoding = "utf-8")
            return data
        
        except:
            writeLog(f'\033[1;31mCould not load file "{os.path.basename(localPath)}"\033[0;0m')
            return abort(500)

    server_config = read_json(CONFIG_PATH)
    if "Android/version" in url:
        data = requests.get(url).json()
        return data

    loaded_mods = loadMods.loadMods(log=False)
    current_url = os.path.splitext(os.path.basename(url))[0]
    current_is_mod = False

    if server_config["assets"]["enableMods"]:
        for mod in loaded_mods["name"]:
            if current_url in mod:
                current_is_mod = True
                break
    
    if not current_is_mod:
        try:
            data = requests.get(url).json()
            write_json(data, localPath)
            writeLog(f'Auto-update of file "{os.path.basename(localPath)}" - \033[1;32mSuccessful!\033[0;0m')

        except:
            writeLog(f'Auto-update of file "{os.path.basename(localPath)}" - \033[1;31mFailed!\033[0;0m')
            if not os.path.exists(localPath):
               writeLog(f'\033[1;31mCould not find file "{os.path.basename(localPath)}"\033[0;0m')
               return abort(500)
            
    if "announce_meta" in url:
        data = read_json(localPath, encoding = "utf-8")
        return data

    return None
