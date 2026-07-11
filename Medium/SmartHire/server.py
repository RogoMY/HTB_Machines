from http.server import BaseHTTPRequestHandler, HTTPServer


class HandlePost(BaseHTTPRequestHandler):

  def do_POST(self):
    # Aflăm dimensiunea datelor primite
    content_length = int(self.headers["Content-Length"])
    # Citim conținutul brut (bytes)
    file_content = self.rfile.read(content_length)

    # Salvăm fișierul pe disk
    with open("smarthire.db", "wb") as f:
      f.write(file_content)

    # Trimitem un răspuns de succes înapoi
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Fisierul a fost primit si salvat cu succes!\n")


# Pornim serverul pe portul 8000
print("Serverul ascultă pe portul 8000...")
HTTPServer(("", 8000), HandlePost).serve_forever()
