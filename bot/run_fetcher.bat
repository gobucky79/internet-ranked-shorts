@echo off
rem Run by Windows Task Scheduler. Keeps yt-dlp current (sites change often), then fetches any new plan's clips.
cd /d "%~dp0"
py -m pip install -q -U yt-dlp >nul 2>&1
py fetch_clips.py >> "%USERPROFILE%\.internet-ranked\fetch-console.log" 2>&1
