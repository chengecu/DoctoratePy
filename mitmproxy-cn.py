import json
import mitmproxy.http
import mitmproxy.proxy.context

server = json.load(open('./config/config.json', 'r'))["server"]

host = server["host"]
port = server["port"]


class AKRedirect:
    
    DOMAINS_LIST = [
        'android.bugly.qq.com',
        'ak-conf.hypergryph.com',
        'bi-track.hypergryph.com',
        'down.anticheatexpert.com',
        'log.trackingio.com',
        'wkdcm2.tingyun.com'
    ]
    
    def __init__(self):
        print('Addon for Redirecting Arknight [CN] Loaded !')

    def server_connect(self, data: mitmproxy.proxy.context.Context):
        data.server.tls = False

    def http_connect(self, flow: mitmproxy.http.HTTPFlow):
        for domain in self.DOMAINS_LIST:
            if domain in flow.request.pretty_host:
                flow.request.scheme = 'http'
                flow.request.host = host
                flow.request.port = port

    def request(self, flow: mitmproxy.http.HTTPFlow):
        for domain in self.DOMAINS_LIST:
            if domain in flow.request.pretty_host:
                if domain == 'ak-conf.hypergryph.com':
                    flow.request.scheme = 'http'
                    flow.request.host = host
                    flow.request.port = port
                else:
                    flow.response = mitmproxy.http.Response.make(200, b"")

addons = [
    AKRedirect()
]