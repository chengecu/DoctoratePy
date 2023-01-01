import random
import socket

from datetime import datetime
 

class AuthCode:
    
    code = None


def writeLog(data):

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def sentSmsCode():
    
    arrs = [0] * 6

    for i in range(len(arrs)):
        arrs[i] = random.randint(0,9)

    AuthCode.code = "".join([str(_) for _ in arrs])
    
    writeLog('\033[1;32mVerification code: {}\033[0;0m'.format(AuthCode.code))


def verifySmsCode(smsCode):
    
    if smsCode == AuthCode.code:
        return True
    else:
        return False