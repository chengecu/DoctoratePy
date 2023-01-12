import json
import os

mitmproxy_server = json.load(open('./config/config.json', 'r'))["server"]
mitmproxy_host = mitmproxy_server["host"]

os.system(
    f"mitmweb.exe --set connection_strategy=lazy --listen-host {mitmproxy_host} --listen-port 8080 -s mitmproxy-cn.py"
)