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

# for a 30yo
HEART_RATE_ZONES = {
	1: (0, 114),
	2: (115, 133),
	3: (134, 152),
	4: (153, 171),
	5: (172, 190),
}

display_bpm = 0
display_zone = None

def get_current_time():
	return datetime.now().strftime("%H:%M:%S")

def get_unix_ms():
	return int(time.time()) * 1000

def get_zone(bpm):
	if bpm is None:
		return None
	for zone, (min_bpm, max_bpm) in HEART_RATE_ZONES.items():
		if min_bpm <= bpm <= max_bpm:
			return zone
	if bpm > HEART_RATE_ZONES[5][1]:
		return 5
	return 1

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
	
	global display_bpm, display_zone

	while True:
		bpm_data = get_bpm_data()
		if bpm_data:
			time_since_last_measured = (get_unix_ms() - bpm_data.get("measured_at")) / 1000
			if time_since_last_measured >= BPM_STALE_TIME:
				display_bpm = None
				display_zone = None
			else:
				display_bpm = bpm_data.get("data", {}).get("heart_rate")
				display_zone = get_zone(display_bpm)
			
			if last_printed_bpm != display_bpm:
				last_printed_bpm = display_bpm
				print(f"[{get_current_time()}] BPM updated: {display_bpm} | Zone: {display_zone}")

		time.sleep(UPDATE_INTERVAL)

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == "/bpm":
			self.send_response(200)
			self.send_header("Content-Type", "application/json")
			self.send_header("Access-Control-Allow-Origin", "*")
			self.end_headers()
			payload = {
				"info": f"{display_bpm} Zone {display_zone}",
			}
			self.wfile.write(json.dumps(payload).encode())
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
