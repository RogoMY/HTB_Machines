echo "import socket, threading
def t(s, d):
    while 1:
        b = s.recv(4096)
        if not b: break
        d.sendall(b)
    s.close(); d.close()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', 8888))
s.listen(5)
while 1:
    lc, _ = s.accept()
    rc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rc.connect(('10.10.16.56', 6969))
    threading.Thread(target=t, args=(lc, rc)).start()
    threading.Thread(target=t, args=(rc, lc)).start()" > proxy.py
