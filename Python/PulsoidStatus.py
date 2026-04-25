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
UPDATE_INTERVAL = 10
# localhost port for BetterDiscord to fetch
PORT = 8765
# how many times our BPM has to be the same before just sending null
MAX_SAME_BPM_COUNT = 3

display_bpm = None

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
    # the last BPM recieved from get_bpm()
    last_bpm = None
    # the amount of times get_bpm() has returned the same value
    same_bpm_count = 0
    # Only send one "[TIME] BPM updated: None" message
    pause_bpm_log = False
    
    global display_bpm

    while True:
        bpm = get_bpm()
        if bpm == last_bpm:
            same_bpm_count += 1

            if same_bpm_count >= MAX_SAME_BPM_COUNT:
                display_bpm = None
        else:
            same_bpm_count = 0
            display_bpm = bpm
            pause_bpm_log = False
        
        last_bpm = bpm
        
        if not pause_bpm_log:
            print(f"[{get_current_time()}] BPM updated: {display_bpm}")
            if display_bpm == None:
                pause_bpm_log = True

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
