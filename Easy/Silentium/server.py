from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Figure out how much data was sent
        content_length = int(self.headers['Content-Length'])
        
        # 2. Read the actual POST data
        post_data = self.rfile.read(content_length)
        print(f"Received data: {post_data.decode('utf-8')}")

        # 3. Send a 200 OK response back to the terminal
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # 4. Send a JSON response body
        response = {"message": "POST request received successfully!"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == '__main__':
    # Run on localhost port 8000
    server_address = ('localhost', 8000)
    server = HTTPServer(server_address, RequestHandler)
    print("Server starting on http://localhost:8000...")
    server.serve_forever()
