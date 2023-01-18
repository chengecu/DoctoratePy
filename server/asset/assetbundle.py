import hashlib
import os
from datetime import datetime

import requests
from constants import CONFIG_PATH
from core.function.loadMods import loadMods
from flask import Response, redirect, stream_with_context
from logger import writeLog
from utils import read_json, write_json

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53"
}
MODS_LIST = {
    "mods": [],
    "name": [],
    "path": [],
    "download": []
}


def getFile(assetsHash: str, fileName: str) -> bytes:

    global MODS_LIST
    server_config = read_json(CONFIG_PATH)
    version = server_config["version"]["android"]["resVersion"]
    basePath = os.path.join('.', 'assets', version, 'redirect')

    if fileName == 'hot_update_list.json' and read_json(CONFIG_PATH)["assets"]["enableMods"]:
        MODS_LIST = loadMods()

    if not server_config["assets"]["downloadLocally"]:
        basePath = os.path.join('.', 'assets', version)
        if fileName != 'hot_update_list.json' and fileName not in MODS_LIST["download"]:
            return redirect('https://ak.hycdn.cn/assetbundle/official/Android/assets/{}/{}'.format(version, fileName), 302)

    if not os.path.isdir(basePath):
        os.makedirs(basePath)
    filePath = os.path.join(basePath, fileName)

    wrongSize = False
    if not os.path.basename(fileName) == 'hot_update_list.json':
        temp_hot_update_path = os.path.join(basePath, "hot_update_list.json")
        hot_update = read_json(temp_hot_update_path)
        if os.path.exists(filePath):
            for type in [hot_update["packInfos"], hot_update["abInfos"]]:
                for pack in type:
                    if pack["name"] == fileName.rsplit(".", 1)[0]:
                        wrongSize = os.path.getsize(filePath) != pack["totalSize"]
                        break

    if server_config["assets"]["enableMods"] and fileName in MODS_LIST["download"]:
        for mod, path in zip(MODS_LIST["download"], MODS_LIST["path"]):
            if fileName == mod and os.path.exists(path):
                wrongSize = False
                filePath = path

    writeLog(f'/{version}/{fileName}', "info")

    return export('https://ak.hycdn.cn/assetbundle/official/Android/assets/{}/{}'.format(version, fileName), filePath, assetsHash, wrongSize)


def downloadFile(url: str, filePath: str) -> None:

    writeLog(f'\033[1;33mDownload {os.path.basename(filePath)}\033[0;0m', "info")
    res = requests.get(url, headers=header, stream=True)
    with open(filePath, 'wb') as f:
        for chunk in res.iter_content(chunk_size=512):
            if chunk:
                f.write(chunk)
                yield chunk


def export(url: str, filePath: str, assetsHash: str, redownload: bool = False) -> Response:

    server_config = read_json(CONFIG_PATH)

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Content-Disposition": "attachment; filename=" + os.path.basename(filePath),
        "Content-Type": "application/octet-stream",
        "Expires": "0",
        "Etag": hashlib.md5(filePath.encode('utf-8')).hexdigest(),
        "Last-Modified": datetime.now(),
        "Pragma": "no-cache"
    }

    if os.path.basename(filePath) == 'hot_update_list.json':

        if os.path.exists(filePath):
            hot_update_list = read_json(filePath)
        else:
            hot_update_list = requests.get(url, headers=header).json()
            write_json(hot_update_list, filePath)

        abInfoList = hot_update_list["abInfos"]
        newAbInfos = []

        for abInfo in abInfoList:
            if server_config["assets"]["enableMods"]:
                hot_update_list["versionId"] = assetsHash
                if len(abInfo["hash"]) == 24:
                    abInfo["hash"] = assetsHash
                if abInfo["name"] not in MODS_LIST["name"]:
                    newAbInfos.append(abInfo)
            else:
                newAbInfos.append(abInfo)

        if server_config["assets"]["enableMods"]:
            for mod in MODS_LIST["mods"]:
                newAbInfos.append(mod)

        hot_update_list["abInfos"] = newAbInfos

        cachePath = './assets/cache/'
        savePath = cachePath + 'hot_update_list.json'

        if not os.path.isdir(cachePath):
            os.makedirs(cachePath)
        write_json(hot_update_list, savePath)

        with open(savePath, 'rb') as f:
            data = f.read()

        return Response(
            data,
            headers=headers
        )

    if os.path.exists(filePath) and not redownload:
        with open(filePath, "rb") as f:
            data = f.read()
        headers["Content-Length"] = os.path.getsize(filePath)

        return Response(
            data,
            headers=headers
        )

    else:
        file = requests.head(url, headers=header)
        total_size_in_bytes = int(file.headers.get('Content-length', 0))
        headers["Content-Length"] = total_size_in_bytes

    return Response(
        stream_with_context(downloadFile(url, filePath)),
        headers=headers
    )
