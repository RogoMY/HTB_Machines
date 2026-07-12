#!/usr/bin/env python3

import os
import sys
import socket
import logging
import re
import hashlib

class PJLServer:
    def __init__(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def listen(self, port=9100, backlog=100):
        self._server.bind(("127.0.0.1", port))
        self._server.listen(backlog)
        logging.info("Listening on port %d" % port)

    def accept(self):
        client, addr = self._server.accept()
        logging.info("[%s] connected" % addr[0])
        return PJLClient(client, addr[0])

class PJLClient:
    def __init__(self, client, address):
        self._client = client
        self._address = address

    def get_line(self):
        """Reads until a newline to get a single PJL command."""
        line = b""
        while True:
            char = self._client.recv(1)
            if not char: return None
            line += char
            if char == b"\n": break
        return line

    def reply(self, message):
        if isinstance(message, str):
            message = message.encode("utf-8")
        self._client.sendall(message)

    def close(self):
        self._client.close()

class Filesystem:
    def __init__(self, root_dir):
        self._root = os.path.abspath(root_dir)

    def _translate(self, path):
        clean = path.replace("0:", "").replace("\\", "/").lstrip("/")
        return os.path.normpath(os.path.join(self._root, clean))

    def listdir(self, name=""):
        target = self._translate(name)
        if not os.path.exists(target): return "FILEERROR=1"
        try:
            items = os.listdir(target)
            res = [". TYPE=DIR", ".. TYPE=DIR"]
            for i in items:
                p = os.path.join(target, i)
                res.append(f"{i} TYPE={'DIR' if os.path.isdir(p) else 'FILE'} SIZE={os.path.getsize(p)}")
            return "\n".join(res)
        except: return "FILEERROR=1"

    def read(self, path):
        target = self._translate(path)
        if os.path.isfile(target):
            with open(target, "rb") as f: return f.read()
        return None

    def write(self, path, data):
        target = self._translate(path)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f: f.write(data)
            return "OK"
        except: return "FILEERROR=1"

fs = None

def handle_download(command, client):
    m = re.search(r'NAME\s*=\s*"([^"]+)"\s*SIZE\s*=\s*(\d+)', command, re.I)
    if not m: return "FILEERROR=1"
    path, size = m.group(1), int(m.group(2))
    
    logging.info(f"Receiving file: {path} ({size} bytes)")
    data = b""
    while len(data) < size:
        chunk = client._client.recv(min(size - len(data), 4096))
        if not chunk: break
        data += chunk
    return fs.write(path, data)

def handle_upload(command):
    m = re.search(r'NAME\s*=\s*"([^"]+)"', command, re.I)
    if not m: return "FILEERROR=1"
    path = m.group(1)
    data = fs.read(path)
    if data is None: return "FILEERROR=1"
    header = f'@PJL FSUPLOAD NAME="{path}" SIZE={len(data)}\n'.encode("utf-8")
    return header + data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <PORT> <ROOT_DIR>")
        sys.exit(1)

    fs = Filesystem(sys.argv[2])
    LOG_FILE = "/home/archivist/printer/logs/commands.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    server = PJLServer()
    server.listen(int(sys.argv[1]))

    while True:
        client = server.accept()
        while True:
            line_bytes = client.get_line()
            if not line_bytes: break
            
            # Filter protocol noise
            if b"@" not in line_bytes: continue
            line = line_bytes[line_bytes.find(b"@"):].decode("utf-8", errors="ignore").strip()
            
            if not line.startswith("@PJL"): continue
            logging.info(f"Command: {line}")

            if "FSDOWNLOAD" in line.upper():
                res = handle_download(line, client)
                client.reply(res + "\r\n")
            elif "FSUPLOAD" in line.upper():
                res = handle_upload(line)
                client.reply(res)
            elif "FSDIRLIST" in line.upper() or "FSQUERY" in line.upper():
                m = re.search(r'NAME\s*=\s*"([^"]+)"', line, re.I)
                res = fs.listdir(m.group(1) if m else "0:/")
                client.reply(res + "\r\n")
            elif "INFO ID" in line.upper():
                client.reply("HP LASERJET 4ML\r\n")
            elif "INFO FILESYS" in line.upper():
                client.reply("VOLUME TOTAL SIZE FREE SPACE LOCATION LABEL STATUS\n0:     1755136    1718272    <HT>     <HT>  READ-WRITE\r\n")
            elif "ECHO" in line.upper():
                client.reply(line + "\r\n")
            else:
                client.reply("OK\r\n")
        client.close()

