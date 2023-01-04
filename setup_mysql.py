import contextlib
import os
import sys
import signal
import pathlib
import subprocess
from zipfile import ZipFile

import textwrap
import requests
import psutil
from tqdm import tqdm

from server.constants import CONFIG_PATH
from server.utils import read_json, write_json

MYSQL_BASE_PATH = r"mysql"
MYSQLD_PATH = r"bin\mysqld.exe"
MYSQLADMIN_PATH = r"bin\mysqladmin.exe"

if pathlib.Path(MYSQL_BASE_PATH, MYSQLD_PATH).exists():
    print("Mysql already installed.")
    sys.exit(0)

print("No mysql file found. Downloading...")
r = requests.get("https://cdn.mysql.com/archives/mysql-8.0/mysql-8.0.30-winx64.zip", allow_redirects=True, stream=True)
progress = tqdm(total=int(r.headers.get('content-length', 0)), unit='iB', unit_scale=True, leave=False, unit_divisor=1024, desc="Downloading mysql")
with open('mysql.zip', 'wb') as f:
    for chunk in r.iter_content(chunk_size=2048):
        progress.update(len(chunk))
        f.write(chunk)
progress.close()

print("Extracting mysql...")
ZipFile('mysql.zip').extractall(".")
pathlib.Path("mysql.zip").unlink()
pathlib.Path("mysql-8.0.30-winx64").rename(MYSQL_BASE_PATH)

print("Setting up mysql...")
with open(pathlib.Path(MYSQL_BASE_PATH, "my.ini"), "w") as f:
    f.write(textwrap.dedent(f"""\
    [client] 
    port=3306 
    default-character-set=utf8mb4 
    [mysqld] 
    authentication_policy=mysql_native_password 
    max_allowed_packet=500M 
    wait_timeout=2147483
    interactive_timeout=2147483
    max_connect_errors=10 
    max_connections=20 
    port=3306 
    character_set_server=utf8mb4 
    basedir="{pathlib.Path().absolute().joinpath(MYSQL_BASE_PATH)}" 
    datadir="{pathlib.Path().absolute().joinpath(MYSQL_BASE_PATH, "data")}" 
    default-storage-engine=INNODB 
    [WinMySQLAdmin]
    {pathlib.Path().absolute().joinpath(MYSQL_BASE_PATH, "bin", "mysqld.exe")}
    """))

print("Mysql installed successfully.")
print("Setting up mysql database...")
result = subprocess.run([pathlib.Path(MYSQL_BASE_PATH, MYSQLD_PATH), "--initialize", "--console", "--user=root"], capture_output=True, text=True)
temp_password = result.stderr.split("\n")[-2].split("root@localhost:")[1].strip()
new_password = input(f"Enter a new password for root user (current password is {temp_password}): ")
if not new_password:
    new_password = temp_password
print("Changing root password...")
p = subprocess.Popen([pathlib.Path(MYSQL_BASE_PATH, MYSQLD_PATH)])
subprocess.run(f'{pathlib.Path(MYSQL_BASE_PATH, MYSQLADMIN_PATH)} -uroot -p"{temp_password}" password "{new_password}"', check=True, shell=True)

config = read_json(CONFIG_PATH)
config["database"]["password"] = new_password
write_json(config, CONFIG_PATH)

print("New password set successfully.")
parent = psutil.Process(p.pid)
children = parent.children(recursive=True)
for p in children:
    with contextlib.suppress(Exception):
        os.kill(p.pid, signal.CTRL_BREAK_EVENT)