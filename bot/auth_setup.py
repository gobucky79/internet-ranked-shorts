"""One-time sign-in: gets the refresh token the bots use for YouTube + Google Drive.

Run this ON YOUR OWN COMPUTER (it opens your browser):
    python3 bot/auth_setup.py path/to/client_secret.json

client_secret.json is the "Desktop app" OAuth client you download from Google Cloud Console (AUTOPILOT.md step 2).
It prints three values — paste them into GitHub > repo Settings > Secrets and variables > Actions:
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
Standard library only — nothing to install.
"""
import http.server, json, secrets, sys, threading, urllib.parse, urllib.request, webbrowser

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",          # upload Shorts + set thumbnails
    "https://www.googleapis.com/auth/youtube.readonly",        # weekly stats: list your videos
    "https://www.googleapis.com/auth/yt-analytics.readonly",   # weekly stats: retention, subs gained
    "https://www.googleapis.com/auth/drive",                   # read the inbox folder, file finished Shorts
]


def main(path):
    cfg = json.load(open(path))
    c = cfg.get("installed") or cfg.get("web")
    cid, csec = c["client_id"], c["client_secret"]
    state = secrets.token_urlsafe(16)
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Done - you can close this tab and go back to the terminal.</h2>")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": " ".join(SCOPES),
        "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening your browser to sign in with the Google account that owns Internet Ranked...\n"
          f"If it doesn't open, paste this link:\n{url}\n")
    webbrowser.open(url)
    t = threading.Thread(target=srv.handle_request)
    t.start()
    t.join(timeout=300)
    if "code" not in got:
        sys.exit(f"Sign-in didn't finish: {got.get('error', 'timed out')}")
    data = urllib.parse.urlencode({"code": got["code"], "client_id": cid, "client_secret": csec,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data))
    if "refresh_token" not in tok:
        sys.exit("No refresh token came back — remove the app's access at myaccount.google.com/permissions and rerun.")
    print("Add these three as GitHub Actions secrets (repo Settings > Secrets and variables > Actions):\n")
    print(f"GOOGLE_CLIENT_ID      = {cid}")
    print(f"GOOGLE_CLIENT_SECRET  = {csec}")
    print(f"GOOGLE_REFRESH_TOKEN  = {tok['refresh_token']}")
    print("\nKeep these private — anyone with them can upload to your channel.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
