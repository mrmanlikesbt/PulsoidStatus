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
UPDATE_INTERVAL = 25
# localhost port for BetterDiscord to fetch
PORT = 8765
# if our BPM hasn't updated in this many seconds, set display_bpm to None
BPM_STALE_TIME = 30

display_bpm = 0

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_unix_ms():
    return int(time.time()) * 1000

def get_bpm_data():
    try:
        req = urllib.request.Request(
            PULSOID_URL,
            headers = {
                "Authorization": f"Bearer {PULSOID_API_TOKEN}",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as error:
        print(f"[{get_current_time()}] Error fetching BPM:", error)
    return None

def bpm_loop():
    # So we don't send duplicate messages. i.e: "[TIME] BPM updated: None" x100
    last_printed_bpm = None
    
    global display_bpm

    while True:
        bpm_data = get_bpm_data()
        if bpm_data:
            time_since_last_measured = (get_unix_ms() - bpm_data.get("measured_at")) / 1000
            if time_since_last_measured >= BPM_STALE_TIME:
                display_bpm = None
            else:
                display_bpm = bpm_data.get("data", {}).get("heart_rate")
            
            if last_printed_bpm != display_bpm:
                last_printed_bpm = display_bpm
                print(f"[{get_current_time()}] BPM updated: {display_bpm}")

        time.sleep(UPDATE_INTERVAL)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/bpm":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"bpm": display_bpm}).encode())
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
