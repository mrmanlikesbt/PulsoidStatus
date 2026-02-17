import os
import time
import json
import urllib.request
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

PULSOID_API_TOKEN = os.getenv("PULSOID_API_TOKEN")
PULSOID_URL = "https://dev.pulsoid.net/api/v1/data/heart_rate/latest"

# the seconds in-between fetching the latest BPM from Pulsoid
UPDATE_INTERVAL = 30
# localhost port for BetterDiscord to fetch
PORT = 8765

last_bpm = None

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_bpm():
    try:
        req = urllib.request.Request(
            PULSOID_URL,
            headers = {
                "Authorization": f"Bearer {PULSOID_API_TOKEN}",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", {}).get("heart_rate")
    except Exception as error:
        print(f"[{get_current_time()}] Error fetching BPM:", error)
    return None

def bpm_loop():
    global last_bpm

    while True:
        bpm = get_bpm()
        if bpm != last_bpm and bpm != None:
            last_bpm = bpm
            print(f"[{get_current_time()}] BPM updated: {bpm}")

        time.sleep(UPDATE_INTERVAL)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/bpm":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"bpm": last_bpm}).encode())
        else:
            self.send_response(404)
            self.end_headers()
        
    def log_message(self, format, *args):
        pass

def main():
    server = HTTPServer(("localhost", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=bpm_loop, daemon=True).start()
    print(f"[{get_current_time()}] Server running on http://localhost:{PORT}/bpm")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()
