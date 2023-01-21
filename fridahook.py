import argparse
import sys
import time
from base64 import b64decode

import frida
from adbutils import adb
from loguru import logger
from server.constants import CONFIG_PATH
from server.utils import read_json

HOST = read_json(CONFIG_PATH)["server"]["host"]


def on_message(message, data):
    print("[%s] => %s" % (message, data))


def main(use_mumu=False, attach=False):

    try:
        adb_device = adb.device_list()[0]
    except IndexError:
        logger.info("No device found. Trying to connect to one...")
        default_ports = ["5555", "7555", "62001"]
        for port in default_ports:
            logger.info(f"Trying to connect to port {port}...")
            adb.connect(f"127.0.0.1:{port}")
            time.sleep(0.5)
            if len(adb.device_list()) > 0:
                logger.info("Device found!")
                adb_device = adb.device_list()[0]
                if port in ["7555", "62001"]:
                    logger.info("Device is a MUMU type emulator. Setting use_mumu to True")
                    use_mumu = True
                break

    if adb_device.shell("command -v su") == "":
        logger.error("No root access found. Exiting...")
        sys.exit(1)

    if adb_device.shell("pidof frida-server") == "":
        logger.info("Frida server not running. Starting it...")
        adb_device.shell("su -c \"/data/local/tmp/frida-server -D\"")
        time.sleep(1)

    if not attach:
        device = frida.get_usb_device(timeout=1)
        pid = device.spawn(b64decode('Y29tLmh5cGVyZ3J5cGguYXJrbmlnaHRz').decode())
        device.resume(pid)

        if use_mumu:
            logger.info("MUMU emulator detected. Restarting frida server...")
            adb_device.shell("su -c \"kill `pidof frida-server`\"")
            time.sleep(3)
            adb_device.shell("su -c \"/data/local/tmp/frida-server -D\"")

        session = device.attach(pid)
    else:
        device = frida.get_usb_device(timeout=1)
        session = device.attach('Arknights')
    script = session.create_script("""

    function redirect_traffic_to_proxy(proxy_url, proxy_port) {{
        Java.perform(function (){{
            console.log("[.] Traffic Redirection");
            var url = Java.use("java.net.URL");
            var proxyTypeI = Java.use('java.net.Proxy$Type');
            var inetSockAddrWrap = Java.use("java.net.InetSocketAddress");
            var proxy = Java.use('java.net.Proxy');

            url.$init.overload('java.lang.String').implementation = function (var0) {{
                //console.log("[*] Created new URL with value: " + var0);
                return this.$init(var0);
            }};

            url.openConnection.overload().implementation = function () {{
                var proxyImpl;

                try{{
                    proxyImpl = proxy.$new(proxyTypeI.valueOf('HTTP'), inetSockAddrWrap.$new(proxy_url, proxy_port));
                }}
                catch(e){{
                    console.log(e);
                }}

                return this.openConnection(proxyImpl);
            }};
        }});
    }}

    function replace_cert(mitm_cert_location){{
        Java.perform(function (){{
            console.log("[.] Cert Pinning Bypass/Re-Pinning");

            var CertificateFactory = Java.use("java.security.cert.CertificateFactory");
            var FileInputStream = Java.use("java.io.FileInputStream");
            var BufferedInputStream = Java.use("java.io.BufferedInputStream");
            var X509Certificate = Java.use("java.security.cert.X509Certificate");
            var KeyStore = Java.use("java.security.KeyStore");
            var TrustManagerFactory = Java.use("javax.net.ssl.TrustManagerFactory");
            var SSLContext = Java.use("javax.net.ssl.SSLContext");

            // Load CAs from an InputStream
            console.log("[+] Loading our CA...")
            var cf = CertificateFactory.getInstance("X.509");

            try {{
                var fileInputStream = FileInputStream.$new(mitm_cert_location);
            }}
            catch(err) {{
                console.log("[o] " + err);
            }}

            var bufferedInputStream = BufferedInputStream.$new(fileInputStream);
            var ca = cf.generateCertificate(bufferedInputStream);
            bufferedInputStream.close();

            var certInfo = Java.cast(ca, X509Certificate);
            console.log("[o] Our CA Info: " + certInfo.getSubjectDN());

            // Create a KeyStore containing our trusted CAs
            console.log("[+] Creating a KeyStore for our CA...");
            var keyStoreType = KeyStore.getDefaultType();
            var keyStore = KeyStore.getInstance(keyStoreType);
            keyStore.load(null, null);
            keyStore.setCertificateEntry("ca", ca);

            // Create a TrustManager that trusts the CAs in our KeyStore
            console.log("[+] Creating a TrustManager that trusts the CA in our KeyStore...");
            var tmfAlgorithm = TrustManagerFactory.getDefaultAlgorithm();
            var tmf = TrustManagerFactory.getInstance(tmfAlgorithm);
            tmf.init(keyStore);
            console.log("[+] Our TrustManager is ready...");

            console.log("[+] Hijacking SSLContext methods now...")
            console.log("[-] Waiting for the app to invoke SSLContext.init()...")

            SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").implementation = function(a,b,c) {{
                SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").call(this, a, tmf.getTrustManagers(), c);
            }}
            console.log("[o] Cert Pinning Bypass/Re-Pinning Done!");
        }});
    }}

    function get_func_by_offset(offset){{
        var module = Process.getModuleByName("libil2cpp.so");
        var addr = module.base.add(offset);
        return new NativePointer(addr.toString());
    }}

    function hookTrue(address) {{
        var func = get_func_by_offset(address);
        console.log('[+] Hooked True Function: ' + func.toString());
        Interceptor.attach(func,{{
            onEnter: function(args){{}},
            onLeave: function(retval){{
                retval.replace(0x1);
            }}
        }});
    }}

    function hookFalse(address) {{
        var func = get_func_by_offset(address);
        console.log('[+] Hooked False Function: ' + func.toString());
        Interceptor.attach(func,{{
            onEnter: function(args){{}},
            onLeave: function(retval){{
                retval.replace(0x0);
            }}
        }});
    }}

    function hookDump(address) {{
        var func = get_func_by_offset(address);
        console.log('[+] Hooked Dump Function: ' + func.toString());
        Interceptor.attach(func,{{
            onEnter: function(args){{
                console.log(typeof(Memory.readCString(args[0])));
                console.log(Memory.readCString(args[0]));
                console.log(args[0]);
                console.log(typeof(Memory.readCString(args[1])));
                console.log(args[1].readCString());
                console.log(args[1]);
            }},
            onLeave: function(retval){{
                //console.log('[!!] Hooked Dump Function: ' + Number(address).toString(16) + ' Return Value: ' + retval.readCString());
                console.log('[!!] Hooked Dump Function: ' + Number(address).toString(16) + ' Return Value: ' + retval);
            }}
        }});
    }}

    function init(){{
        var proxy_url = "{HOST}";
        var proxy_port = 8080;
        var mitm_cert_location_on_device = "/data/local/tmp/mitmproxy-ca-cert.cer";

        var awaitForCondition = function (e) {{
            var int = setInterval(function () {{
                var addr = Module.findBaseAddress("libil2cpp.so");
                if (addr) {{
                    clearInterval(int);
                    e(+addr);
                    return;
                }}
            }}, 0);
        }}
        awaitForCondition(()=>{{
            console.log('[+] libil2cpp.so Loaded!');
            [0xfe978f, 0x362b87e].forEach(hookTrue);
            [0xfde384].forEach(hookFalse);
        }});

        redirect_traffic_to_proxy(proxy_url, proxy_port);
        replace_cert(mitm_cert_location_on_device);
    }}

    init();

""".format(HOST=HOST))
    script.on('message', on_message)
    script.load()
    print("[!] Ctrl+D on UNIX, Ctrl+Z on Windows/cmd.exe to detach from instrumented program.\n\n")
    sys.stdin.read()
    session.detach()


if __name__ == '__main__':

    args = argparse.ArgumentParser(description='Doctorate Hooking Script')
    args.add_argument('-a', '--attach', action='store_true', help='Use this flag to attach to an already running process')
    args.add_argument('-m', '--mumu', action='store_true', help='Use this flag if you are having black screen issues with Mumu emulator')

    args = args.parse_args()
    try:
        main(args.mumu, args.attach)
    except KeyboardInterrupt:
        if len(adb.device_list()) > 0:
            logger.info("Killing frida-server on device")
            adb_device = adb.device_list()[0]
            adb_device.shell("su -c \"kill `pidof frida-server`\"")
