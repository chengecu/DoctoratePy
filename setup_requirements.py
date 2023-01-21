import logging
import lzma
import os
import pathlib
import shutil
import subprocess
import sys
import time

import requests
from adbutils import adb

CERT_FILE_PATH = pathlib.Path(os.environ['USERPROFILE'], ".mitmproxy", "mitmproxy-ca-cert.cer")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Setup")

if not pathlib.Path(CERT_FILE_PATH).exists():
    logger.info("Launching mitmproxy for first time")
    p = subprocess.Popen("mitmdump")
    time.sleep(5)
    p.kill()

try:
    device = adb.device_list()[0]
except IndexError:
    logger.info("No device found. Trying to connect to one...")
    default_ports = ["5555", "7555", "62001"]
    for port in default_ports:
        logger.info(f"Trying to connect to port {port}...")
        adb.connect(f"127.0.0.1:{port}")
        time.sleep(0.5)
        if len(adb.device_list()) > 0:
            logger.info("Device found!")
            device = adb.device_list()[0]

if not device:
    logger.error("No device found. Exiting...")
    sys.exit(1)

cert_exists = device.shell('test -f /data/local/tmp/mitmproxy-ca-cert.cer && echo True').strip()
if not cert_exists:
    shutil.copy(CERT_FILE_PATH, pathlib.Path("mitmproxy-ca-cert.cer").absolute().as_posix())
    logger.info("Mitmproxy certificate not found on device. Installing it...")
    device.push("mitmproxy-ca-cert.cer", "/data/local/tmp/mitmproxy-ca-cert.cer")

    logger.info("Setting permissions...")
    device.shell("chmod 755 /data/local/tmp/mitmproxy-ca-cert.cer")

    logger.info("Removing certificate from local machine...")
    os.remove("mitmproxy-ca-cert.cer")


frida_exists = device.shell('test -f /data/local/tmp/frida-server && echo True').strip()
if not frida_exists:
    logger.info("Frida not found on device. Installing it...")
    architecture = device.shell("getprop ro.product.cpu.abi").strip().replace("-v8a", "")
    logger.info(f"Architecture: {architecture}")

    version = requests.get("https://api.github.com/repos/frida/frida/releases/latest").json()["tag_name"]
    name = f"frida-server-{version}-android-{architecture}"
    logger.info(f"Downloading {name}...")
    url = f"https://github.com/frida/frida/releases/download/{version}/{name}.xz"
    r = requests.get(url, allow_redirects=True)
    open('frida-server.xz', 'wb').write(r.content)

    logger.info("Decompressing...")
    with lzma.open("frida-server.xz") as f, open('frida-server', 'wb') as fout:
        file_content = f.read()
        fout.write(file_content)

    logger.info("Pushing to device...")
    device.push("frida-server", "/data/local/tmp/frida-server")

    logger.info("Setting permissions...")
    device.shell("chmod 755 /data/local/tmp/frida-server")

    logger.info("Removing frida-server from local machine...")
    os.remove("frida-server")
    os.remove("frida-server.xz")

adb.disconnect(device.serial)
print("\nMitmproxy certificate and frida-server are installed!")
input("Press enter to exit...")
