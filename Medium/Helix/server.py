import http.server
import socketserver
import os

PORT = 8003

class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        file_data = self.rfile.read(content_length)

        filename = "control.png" 
        with open(filename, 'wb') as f:
            f.write(file_data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"File received successfully!")

with socketserver.TCPServer(("", PORT), UploadHandler) as httpd:
    print(f"Server activ pe portul {PORT}")
    httpd.serve_forever()
