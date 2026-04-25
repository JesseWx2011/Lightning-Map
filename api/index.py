from http.server import BaseHTTPRequestHandler
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Security Check
        auth_header = self.headers.get('Authorization')
        if auth_header != f"Bearer {os.environ.get('CRON_SECRET')}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        # 2. Your Logic
        print("Success: The automated script is running!")
        
        # 3. Response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Cron Job Completed Successfully")
        return
