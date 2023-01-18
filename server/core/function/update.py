import json
import os
from functools import lru_cache

import requests
from constants import CONFIG_PATH
from flask import abort
from logger import writeLog
from utils import read_json, write_json

from . import loadMods


class CacheData:

    cached_data = {}

    @classmethod
    @lru_cache(maxsize=10485760)
    def read_cache(cls, localPath):
        current_modification_time = os.path.getmtime(localPath)
        if localPath in cls.cached_data and current_modification_time == cls.cached_data[localPath]["modification_time"]:
            return cls.cached_data[localPath]["data"]
        data = read_json(localPath, encoding='utf-8')
        modification_time = os.path.getmtime(localPath)
        cls.cached_data[localPath] = {"data": data, "modification_time": modification_time}
        return data


def updateData(url: str, use_local: bool = False) -> None:

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
            cache_data = CacheData()
            data = cache_data.read_cache(localPath)
            return data

        except json.decoder.JSONDecodeError:
            writeLog(f'\033[1;31mCould not load file "{os.path.basename(localPath)}"\033[0;0m', "error")
            return abort(500)

        except IOError:
            writeLog(f'\033[1;31mCould not open file "{os.path.basename(localPath)}"\033[0;0m', "error")
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
            writeLog(f'Auto-update of file "{os.path.basename(localPath)}" - \033[1;32mSuccessful!\033[0;0m', "info")

        except requests.exceptions.RequestException:
            writeLog(f'Auto-update of file "{os.path.basename(localPath)}" - \033[1;31mFailed!\033[0;0m', "error")
            if not os.path.exists(localPath):
                writeLog(f'\033[1;31mCould not find file "{os.path.basename(localPath)}"\033[0;0m', "error")
                return abort(500)

    if "announce_meta" in url:
        data = read_json(localPath, encoding='utf-8')
        return data

    return None
