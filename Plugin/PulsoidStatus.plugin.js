/**
 * @name PulsoidStatus
 * @author Mr. Man
 * @description Fetches BPM from local Python server and sets your Discord custom status.
 * @version 1.0.0
 */

/// The time in-between each BPM request to the local Python server
const FETCH_INTERVAL_MS = 30_000;
/// URL to the local Python server
const LOCALHOST_URL = "http://localhost:8765/bpm";
/// How many times our BPM has to be the same before showing NOT_AVAILABLE_TEXT
const MAX_SAME_BPM_COUNT = 2;
/// The status displayed when BPM is unavailable, for whatever reason
const NOT_AVAILABLE_TEXT = "n/a";

class PulsoidStatus {
	constructor() {
		// Reference to the BPM loop interval
		this.interval = null;
		// The last status we set, used to avoid unnecessary status updates if nothing has changed
		this.last_set_status = null;
		// Our last BPM. Compared with [same_bpm_count] to determine if we should show the BPM or NOT_AVAILABLE_TEXT
		this.last_bpm = 0;
		// See above
		this.same_bpm_count = 0; 
	}

	load() {
		this.modules = this.modules || (() => {
			let m = [];
			webpackChunkdiscord_app.push([['PulsoidStatus'], {}, e => {
				m = m.concat(Object.values(e.c || {}));
			}]);
			return m;
		})();

		this.authToken = this.modules.find(m => m.exports?.default?.getToken?.name === "getToken").exports.default.getToken() || (() => {
			let proxy = document.createElement("iframe")
			document.body.appendChild(proxy)
			let token = Object.assign({}, proxy.contentWindow).window.localStorage["token"]
			document.body.removeChild(proxy)
			return JSON.parse(token)
		})();
	}

	start() {
		this.loop();
		this.interval = setInterval(() => this.loop(), FETCH_INTERVAL_MS);
	}

	stop() {
		clearInterval(this.interval);
		this.setStatus(NOT_AVAILABLE_TEXT);
	}

	async loop() {
		let bpm
		try {
			const response = await fetch("http://localhost:8765/bpm");
			if (!response.ok) {
				return;
			}
			const data = await response.json();
			bpm = data.bpm;
		} catch (e) {
			//console.error("[PulsoidStatus] Error fetching BPM:", e);
		}

		this.handleBpm(bpm);
	}

	handleBpm(bpm) {
		if (bpm === this.last_bpm) {
			this.same_bpm_count++;

			if (this.same_bpm_count >= MAX_SAME_BPM_COUNT) {
				this.setStatus(NOT_AVAILABLE_TEXT);
				return;
			}
		}
		else {
			this.same_bpm_count = 0;
		}
		this.last_bpm = bpm
		
		if(bpm == null || bpm == undefined) {
			this.setStatus(NOT_AVAILABLE_TEXT);
		}
		else {
			this.setStatus(bpm);
		}
	}

	setStatus(set_status) {
		if(set_status == this.last_set_status) {
			return;
		}
		this.last_set_status = set_status;

		console.log(`[PulsoidStatus] 🫀 ${set_status}`);

		const new_status = {
			text: set_status,
			emoji_name: "🫀",
			timeout: null,
		};

		try {
			const req = new XMLHttpRequest();
			req.open("PATCH", "/api/v9/users/@me/settings", true);
			req.setRequestHeader("authorization", this.authToken);
			req.setRequestHeader("content-type", "application/json");
			req.onload = () => {
				const err = this.strError(req);
				if (err !== undefined) {
					console.error(`[PulsoidStatus] Error: ${err}`);
				}
			};
			req.send(JSON.stringify({ custom_status: new_status }));
		} catch (e) {
			console.error("[PulsoidStatus] Error setting status:", e);
		}
	}

	strError(req) {
		if (req.status < 400) return undefined;
		if (req.status === 401) return "Invalid AuthToken";
		if (req.status === 429) return "Too many requests";

		let json = JSON.parse(req.response);
		for (const s of ["errors", "custom_status", "text", "_errors", 0, "message"])
		if ((json === undefined) || ((json = json[s]) === undefined))
			return `Unknown error. (${req.status})`;

		return json;
	}
}
