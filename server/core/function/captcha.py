import random
import socket

from time import time
from datetime import datetime
 

class TemporaryData:

    codes = []
    req_num = 0
    lastSendTs = 0
    
    
class AuthCode:
    def __init__(self, code: str, ts: int, type: int):
        self.code = code
        self.ts = ts
        self.type = type


def writeLog(data: str) -> None:

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')

    
def sentSmsCode(type: int = 0) -> int:
    
    ts = int(time())
    code = "".join(str(index) for index in [random.randint(0, 9) for _ in range(6)])
    
    if ts - TemporaryData.lastSendTs <= 5:
        return 2
    
    TemporaryData.codes.append(AuthCode(code, ts, type))
    
    if ts - TemporaryData.lastSendTs >= 300:
        TemporaryData.req_num = 0

    if ts - TemporaryData.lastSendTs <= 60:
        if TemporaryData.req_num >= 5:
            TemporaryData.req_num = 0
            return 1
        TemporaryData.req_num += 1 
        
    TemporaryData.lastSendTs = ts
    writeLog('\033[1;32mVerification code: {}\033[0;0m'.format(code))
    
    return 0

    
def verifySmsCode(smsCode: str, smsCode_2: str = None, phone_check: bool = False) -> bool:
    
    pass_code = []
    for code in TemporaryData.codes:
        if code.type == 101 and code.code == smsCode:
            pass_code.insert(0, code)
        if code.type in [0, 4, 102] and code.code == smsCode:
            if int(time()) - code.ts <= 300:
                TemporaryData.codes.remove(code)
                return True
            else:
                TemporaryData.codes.remove(code)
                return None
        if code.type == 103 and code.code == smsCode_2:
            pass_code.append(code)
            
        if phone_check and len(pass_code) == 2:
            if pass_code[0].code == smsCode:
                for item in pass_code:
                    TemporaryData.codes.remove(item)
                return True
    
    return False