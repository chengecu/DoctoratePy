import logging
import os
import socket
from datetime import datetime

logger = logging.getLogger('werkzeug')
logger.setLevel(logging.DEBUG)

if not os.path.exists("./log"):
    os.mkdir("./log")

time_now = datetime.now()
log_files = [f for f in os.listdir("./log") if f.startswith("DoctoratePy_")]

if log_files:
    last_log = max(log_files, key=lambda x: os.path.getctime(os.path.join("log", x)))
    last_log_ctime = datetime.fromtimestamp(os.stat(os.path.join("log", last_log)).st_ctime)

    if (time_now - last_log_ctime).total_seconds() < 3600:
        timestamp = last_log_ctime.strftime("%Y-%m-%d_%H-%M-%S")
    else:
        timestamp = time_now.strftime("%Y-%m-%d_%H-%M-%S")
else:
    timestamp = time_now.strftime("%Y-%m-%d_%H-%M-%S")

file_handler = logging.FileHandler(f"./log/DoctoratePy_{timestamp}.log")
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def writeLog(data: str, log_level: str = "info") -> None:

    clearLog()
    os.system("")

    log_level_map = {
        "debug": logger.debug,
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error
    }

    time = time_now.strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    log_func = log_level_map.get(log_level.lower(), logger.info)
    log_func(f"{clientIp} - - [{time}] {data}")


def clearLog() -> None:

    for filename in log_files:
        file_path = os.path.join("log", filename)
        file_time = datetime.strptime(filename.replace("DoctoratePy_", ""), "%Y-%m-%d_%H-%M-%S.log")
        if (time_now - file_time).days > 7:
            try:
                os.remove(file_path)
            except Exception as e:
                writeLog(str(e), "debug")
                continue

    if len(log_files) > 100:
        log_files.sort(key=lambda x: datetime.strptime(x.replace("DoctoratePy_", ""), "%Y-%m-%d_%H-%M-%S.log"))
        for filename in log_files[:len(log_files) - 100]:
            file_path = os.path.join("log", filename)
            try:
                os.remove(file_path)
            except Exception as e:
                writeLog(str(e), "debug")
                continue
