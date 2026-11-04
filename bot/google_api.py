"""Tiny Google API client (Drive + YouTube) using a stored OAuth refresh token. Only needs `requests`.

Credentials come from environment variables (GitHub Actions secrets):
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
Get them once with:  python3 bot/auth_setup.py client_secret.json
"""
import json, os, time

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE = "https://www.googleapis.com/drive/v3"
YT = "https://www.googleapis.com/youtube/v3"
YT_UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
YT_THUMB = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
YTA = "https://youtubeanalytics.googleapis.com/v2/reports"
FOLDER = "application/vnd.google-apps.folder"


class Google:
    def __init__(self):
        self._tok, self._exp = None, 0
        for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"):
            if not os.environ.get(k):
                raise SystemExit(f"missing secret {k} — see AUTOPILOT.md setup step 3")

    def token(self):
        if time.time() > self._exp - 60:
            r = requests.post(TOKEN_URL, data={
                "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
            if r.status_code != 200:
                raise SystemExit(f"Google sign-in failed ({r.status_code}): {r.text[:300]}\n"
                                 "If it says invalid_grant, the refresh token expired — rerun bot/auth_setup.py "
                                 "(and make sure the OAuth app is set to 'In production', see AUTOPILOT.md).")
            j = r.json()
            self._tok, self._exp = j["access_token"], time.time() + j.get("expires_in", 3600)
        return self._tok

    def h(self, extra=None):
        return {"Authorization": f"Bearer {self.token()}", **(extra or {})}

    def get(self, url, **params):
        r = requests.get(url, headers=self.h(), params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    # ---------- Drive ----------
    def find_folder(self, name, parent=None, create=True):
        q = f"name = '{name}' and mimeType = '{FOLDER}' and trashed = false"
        if parent:
            q += f" and '{parent}' in parents"
        res = self.get(f"{DRIVE}/files", q=q, fields="files(id,name)", pageSize=10)["files"]
        if res:
            return res[0]["id"]
        if not create:
            return None
        meta = {"name": name, "mimeType": FOLDER, **({"parents": [parent]} if parent else {})}
        r = requests.post(f"{DRIVE}/files", headers=self.h(), json=meta, params={"fields": "id"}, timeout=30)
        r.raise_for_status()
        return r.json()["id"]

    def list_files(self, folder):
        return self.get(f"{DRIVE}/files", q=f"'{folder}' in parents and trashed = false", pageSize=100,
                        fields="files(id,name,mimeType,size,createdTime,modifiedTime)", orderBy="name")["files"]

    def download(self, file_id, path):
        with requests.get(f"{DRIVE}/files/{file_id}", headers=self.h(), params={"alt": "media"},
                          stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        return path

    def move(self, file_id, new_parent, old_parent):
        r = requests.patch(f"{DRIVE}/files/{file_id}", headers=self.h(),
                           params={"addParents": new_parent, "removeParents": old_parent, "fields": "id"}, timeout=30)
        r.raise_for_status()

    def upload_file(self, path, folder, mime):
        meta = {"name": os.path.basename(path), "parents": [folder]}
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files", headers=self.h(),
                          params={"uploadType": "multipart", "fields": "id,webViewLink"},
                          files={"metadata": ("m", json.dumps(meta), "application/json"),
                                 "file": (os.path.basename(path), open(path, "rb"), mime)}, timeout=600)
        r.raise_for_status()
        return r.json()

    # ---------- YouTube ----------
    def upload_video(self, path, title, description, tags, privacy="private", publish_at=None, category="23"):
        status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
        if publish_at:
            status = {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False}
        body = {"snippet": {"title": title[:100], "description": description[:5000], "tags": tags,
                            "categoryId": category}, "status": status}
        size = os.path.getsize(path)
        r = requests.post(YT_UPLOAD, headers=self.h({"X-Upload-Content-Type": "video/mp4",
                                                      "X-Upload-Content-Length": str(size)}),
                          params={"uploadType": "resumable", "part": "snippet,status"}, json=body, timeout=60)
        r.raise_for_status()
        loc = r.headers["Location"]
        for attempt in range(5):
            try:
                with open(path, "rb") as f:
                    up = requests.put(loc, headers=self.h({"Content-Type": "video/mp4"}), data=f, timeout=1800)
                if up.status_code in (200, 201):
                    return up.json()
                if up.status_code < 500:
                    raise SystemExit(f"YouTube upload failed ({up.status_code}): {up.text[:500]}")
            except requests.ConnectionError:
                pass
            time.sleep(10 * (attempt + 1))
        raise SystemExit("YouTube upload kept failing — will retry on the next run")

    def recent_uploads(self, n=15):
        """Newest n videos on the channel with status (incl. removals) and region blocks."""
        ch = self.get(f"{YT}/channels", part="contentDetails", mine="true")["items"][0]
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        items = self.get(f"{YT}/playlistItems", part="contentDetails", playlistId=uploads, maxResults=n)["items"]
        ids = [i["contentDetails"]["videoId"] for i in items]
        if not ids:
            return []
        return self.get(f"{YT}/videos", part="snippet,status,contentDetails", id=",".join(ids))["items"]

    def set_private(self, video_id):
        """Pull a video back to private. Needs the youtube.force-ssl scope (AUTOPILOT.md › Watchdog);
        returns (ok, message) instead of raising so the watchdog can fall back to alerting."""
        r = requests.put(f"{YT}/videos", headers=self.h(), params={"part": "status"},
                         json={"id": video_id, "status": {"privacyStatus": "private",
                                                              "selfDeclaredMadeForKids": False}}, timeout=60)
        return r.status_code == 200, r.text[:300]

    def set_thumbnail(self, video_id, path):
        with open(path, "rb") as f:
            r = requests.post(YT_THUMB, headers=self.h({"Content-Type": "image/jpeg"}),
                              params={"videoId": video_id}, data=f, timeout=120)
        return r.status_code == 200, r.text[:300]
