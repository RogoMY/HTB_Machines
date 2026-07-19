import subprocess
import glob
import os
import time
import sys
import uuid
import stat
from pathlib import Path

# Container paths
#UPLOAD_DIR = "/var/www/html/uploads"
UPLOAD_DIR = "/var/www/research.bedside.htb/uploads"
OUTPUT_DIR = "/datastore/staging"

TIMEOUT = 10
SLEEP_INTERVAL = 30

os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_suspicious_filename(name: str) -> bool:
    if name.startswith("/") or ".." in name or name.startswith("-"):
        return True
    if any(ord(ch) < 32 for ch in name):
        return True
    return False

def process_pdf(pdf_path, randomized_name):
    filename = os.path.basename(pdf_path)

    reason = None

    # Basic filename check
    if is_suspicious_filename(filename):
        reason = "suspicious filename"
    # Reject symlinks
    else:
        st = os.lstat(pdf_path)
        if stat.S_ISLNK(st.st_mode):
            reason = "symlink"
        # Reject non-regular files
        elif not stat.S_ISREG(st.st_mode):
            reason = "non-regular file"

    if reason:
        print(f"[DEBUG] Skipping {filename}: {reason}")
        return

    output_file = os.path.join(OUTPUT_DIR, f"{randomized_name}.txt")

    try:
        subprocess.run(
            ["pdf2txt.py", pdf_path, "-o", output_file],
            timeout=TIMEOUT,
            check=True
        )
        print(f"Processed: {pdf_path} -> {output_file}")
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for {pdf_path}, skipping...")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {pdf_path}: {e}")
    except Exception as e:
        print(f"Unexpected error processing {pdf_path}: {e}")

def main():
    while True:
        pdf_files = glob.glob(os.path.join(UPLOAD_DIR, "*.pdf"))
        if not pdf_files:
            print("No PDF files found.")
            time.sleep(SLEEP_INTERVAL)
            continue

        for pdf_path in pdf_files:
            randomized_name = str(uuid.uuid4())
            process_pdf(pdf_path, randomized_name)

        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
