import os
import sys
import lzma
import time
import shutil

import requests
from adbutils import adb
from adbutils.errors import AdbTimeout


devices = []
count = 0
CERT_FILE_PATH = os.path.join(os.environ['USERPROFILE'], ".mitmproxy", "mitmproxy-ca-cert.cer")

while len(devices) < 1:
    print("Waiting for device...", end="\r")
    devices = adb.device_list()
    count += 1
    time.sleep(1)

    if count > 10:
        ans = input("No device found after 10 tries. Do you want to connect manually? (y/n) (Default: n): ")

        if ans.lower() != "y":
            print("Quitting...")
            sys.exit(0)
            
        ip_port = input("Please type in the IP address and port of the device: ")
        adb.connect(ip_port)
        try:
            adb.wait_for(state="device", timeout=10)
        except AdbTimeout:
            print("Cannot connect to device. Quitting...")
            sys.exit(0)
        devices = adb.device_list()
        if len(devices) < 1:
            print("Cannot connect to device. Quitting...")
            sys.exit(0)

device = devices[0]
print("\nDevice found:", device.serial)

cert_exists = device.shell('test -f /data/local/tmp/mitmproxy-ca-cert.cer && echo True').strip()
if not cert_exists:
    shutil.copy(CERT_FILE_PATH, os.path.join(os.getcwd(), "mitmproxy-ca-cert.cer"))
    print("Copying mitmproxy certificate...")
    device.push("mitmproxy-ca-cert.cer", "/data/local/tmp/mitmproxy-ca-cert.cer")

    print("Modifying permissions")
    device.shell("chmod 755 /data/local/tmp/mitmproxy-ca-cert.cer")

    print("Mitmproxy certificate is installed!")
    os.remove("mitmproxy-ca-cert.cer")

frida_exists = device.shell('test -f /data/local/tmp/frida-server && echo True').strip()
if not frida_exists:
    architecture = device.shell("getprop ro.product.cpu.abi").strip().replace("-v8a", "")
    print(f"\nArchitecture: {architecture}")

    version = requests.get("https://api.github.com/repos/frida/frida/releases/latest").json()["tag_name"]
    name = f"frida-server-{version}-android-{architecture}"
    print(f"Downloading {name}...")
    url = f"https://github.com/frida/frida/releases/download/{version}/{name}.xz"
    r = requests.get(url, allow_redirects=True)
    open('frida-server.xz', 'wb').write(r.content)

    print("Extracting....")
    with lzma.open("frida-server.xz") as f, open('frida-server', 'wb') as fout:
        file_content = f.read()
        fout.write(file_content)

    print("Copying frida-server...")
    device.push("frida-server", "/data/local/tmp/frida-server")

    print("Modifying permissions")
    device.shell("chmod 755 /data/local/tmp/frida-server")
    os.remove("frida-server")
    os.remove("frida-server.xz")

print("\nFrida-server is installed!")
input("Press enter to exit...")
