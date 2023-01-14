import sys
import time
import subprocess

from adbutils import adb, adb_path
from adbutils.errors import AdbTimeout

default_ports = ["5555", "7555"]
devices = []
count = 0

while len(devices) < 1:
    for port in default_ports:
        print(f"Trying to connect to port {port}...", end="\r")
        adb.connect(f"127.0.0.1:{port}")
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

print("Restarting ADB server with root permissions...")
device.root()
adb.wait_for(state="device", timeout=10)
print("\nRunning frida\nNow you can start fridahook\n")
p = subprocess.Popen(f'"{adb_path()}" shell /data/local/tmp/frida-server &', shell=True)

while p.poll() is None:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Quitting...")
        p.terminate()
        sys.exit(0)
