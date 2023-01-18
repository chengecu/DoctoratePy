import sys
from base64 import b64decode

import frida

from server.constants import CONFIG_PATH
from server.utils import read_json

HOST = read_json(CONFIG_PATH)["server"]["host"]

def on_message(message, data):
    print("[%s] => %s" % (message, data))

def main():
    device = frida.get_usb_device(timeout=1)
    while True:
        num = input("Choose your emulator.\n1. Mumu Player\n2. LDPlayer9 and Others\nChoose one: ")
        try:
            num = int(num)
        except:
            print("Invalid input")
            continue

        if num not in [1, 2]:
            print("Invalid input")
            continue

        if num == 1:
            # Mumu Player
            session = device.attach("Arknights")
            timeout = 500
            break

        elif num == 2:
            # LDPlayer9
            pid = device.spawn(b64decode('Y29tLmh5cGVyZ3J5cGguYXJrbmlnaHRz').decode())
            device.resume(pid)
            session = device.attach(pid)
            timeout = 6000
            break

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

        setTimeout(function() {{
            [0xfe978f, 0x362b87e].forEach(hookTrue);
            [0xfde384].forEach(hookFalse);
        }}, {timeout})

        redirect_traffic_to_proxy(proxy_url, proxy_port);
        replace_cert(mitm_cert_location_on_device);	
    }}

    init();

""".format(HOST=HOST, timeout=timeout))
    script.on('message', on_message)
    script.load()
    print("[!] Ctrl+D on UNIX, Ctrl+Z on Windows/cmd.exe to detach from instrumented program.\n\n")
    sys.stdin.read()
    session.detach()

if __name__ == '__main__':
    main()
