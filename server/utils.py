import json
import socket
import hashlib
import binascii

from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def writeLog(data):

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def read_json(filepath: str, **args) -> dict:

    with open(filepath, **args) as f:
        return json.load(f)


def write_json(data: dict, filepath: str) -> None:

    with open(filepath, 'w') as f:
        json.dump(data, f, sort_keys=False, indent=4)


def decrypt_battle_data(data: str, login_time: int) -> dict:
    
    LOG_TOKEN_KEY = "pM6Umv*^hVQuB6t&"
    
    battle_data = bytes.fromhex(data[:len(data) - 32])
    src = LOG_TOKEN_KEY + str(login_time)
    key = hashlib.md5(src.encode()).digest()
    iv = bytes.fromhex(data[len(data) - 32:])
    aes_obj = AES.new(key, AES.MODE_CBC, iv)
    try:
        decrypt_data = unpad(aes_obj.decrypt(battle_data), AES.block_size)
        return json.loads(decrypt_data)
    
    except Exception as e:
        writeLog("\033[1;31m" + str(e) + "\033[0;0m")
        return None