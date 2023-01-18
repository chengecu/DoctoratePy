import hashlib
import os
import zipfile
from typing import List

from logger import writeLog


def loadMods(log: bool = True) -> List:

    fileList = []
    loadedModList = {
        "mods": [],
        "name": [],
        "path": [],
        "download": []
    }

    for file in os.listdir('./mods/'):
        if file != ".placeholder" and file.endswith(".dat"):
            fileList.append('./mods/' + file)

    for filePath in fileList:
        modFile = zipfile.ZipFile(filePath, 'r')

        try:
            if not zipfile.is_zipfile(filePath) and os.path.getsize(filePath) == 0:
                continue

            for fileName, info in zip(modFile.namelist(), modFile.infolist()):
                if not zipfile.ZipInfo.is_dir(info):
                    modName = fileName
                    if modName in loadedModList["name"]:
                        writeLog(filePath + ' - \033[1;33mConflict with other mods...\033[0;0m', "warning")
                        continue

                    byteBuffer = modFile.read(fileName)
                    totalSize = os.path.getsize(filePath)
                    abSize = len(byteBuffer)
                    modMd5 = hashlib.md5(byteBuffer).hexdigest()

                    abInfo = {
                        "name": modName,
                        "hash": modMd5,
                        "md5": modMd5,
                        "totalSize": totalSize,
                        "abSize": abSize
                    }

                    if log:
                        writeLog(filePath + ' - \033[1;32mMod loaded successfully...\033[0;0m', "info")

                    loadedModList["mods"].append(abInfo)
                    loadedModList["name"].append(modName)
                    loadedModList["path"].append(filePath)
                    downloadName = modName.replace("/", "_").replace("#", "__").replace(".ab", ".dat")
                    loadedModList["download"].append(downloadName)

        except Exception as e:
            writeLog(str(e), "debug")
            writeLog(filePath + ' - \033[1;31mMod file loading failed...\033[0;0m', "error")

    return loadedModList
