import os
import json
import base64
import socket
import random
import hashlib

from datetime import datetime
from io import BytesIO
from zipfile import ZipFile
from typing import Dict
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad


def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def read_json(filepath: str, **args) -> Dict:

    with open(filepath, **args) as f:
        return json.load(f)

    
def write_json(data: dict, filepath: str) -> None:
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=False, indent=4, ensure_ascii=False)


def encrypt_code_data(data: str, app_key: str, login_time: int) -> str:
    
    data_bytes = base64.b64encode(data.encode())
    padded_data = pad(data_bytes, AES.block_size)
    src =  base64.urlsafe_b64encode(app_key.encode()).decode() + str(login_time)
    key = hashlib.md5(src.encode()).digest()
    iv = os.urandom(AES.block_size)
    aes_obj = AES.new(key, AES.MODE_CBC, iv)
    try:
        encrypted_hex_str = aes_obj.encrypt(padded_data).hex() + iv.hex()
        _pad = lambda x: x + bytes([random.randint(0, 255) for _ in range(6 - len(x) % 3)])
        encrypted_data = _pad(bytes.fromhex(encrypted_hex_str))
        return base64.b64encode(encrypted_data).decode()
    
    except Exception as e:
        writeLog("\033[1;31m" + str(e) + "\033[0;0m")
        return None

    
def decrypt_user_key(key: str, login_time: int) -> str:
    
    LOG_SECRET_KEY = "12451c15120f1c1b203d421a3b132ecf"
    
    buf = [int(x, 16) for x in [y.replace("f", "") for y in [LOG_SECRET_KEY[z:z+2] for z in range(0, len(LOG_SECRET_KEY), 2)]]]
    data_bin = "".join([format(ord(x), '08b') for x in key])
    format_data = [data_bin[i:i+8] for i in range(0, len(data_bin), 8)]
    try:
        decrypt_buf = "".join(['{:08b}'.format(int(format_data[i], 2) - buf[i]) if i in (6, 15) else '{:08b}'.format(int(format_data[i], 2) + buf[i]) for i in range(len(format_data))])
        decrypt_data = "".join(map(lambda x: chr(int(str(x), 2)), [decrypt_buf[i:i+8] for i in range(0, len(decrypt_buf), 8)])) if login_time else None
        return decrypt_data
    
    except Exception as e:
        writeLog("\033[1;31m" + str(e) + "\033[0;0m")
        return None

    
def decrypt_battle_data(data: str, login_time: int) -> Dict:
    
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

    
def decrypt_battle_replay(battle_replay: str) -> Dict:

    data = base64.decodebytes(battle_replay.encode())
    b = None
    try:
        bis = BytesIO(data)
        zip = ZipFile(bis)
        for zip_info in zip.infolist():
            with zip.open(zip_info) as f:
                b = f.read()
        zip.close()
        bis.close()
        return json.loads(b.decode("utf-8"))
    
    except Exception as e:
        writeLog("\033[1;31m" + str(e) + "\033[0;0m")
        return None