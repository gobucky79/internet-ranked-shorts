@echo off
rem One-time setup for the Internet Ranked clip fetcher (Windows).
rem Run it from the folder that holds fetch_clips.py, run_fetcher.bat and this file.
cd /d "%~dp0"
echo Installing yt-dlp, requests and ffmpeg for Python...
py -m pip install -q -U yt-dlp requests imageio-ffmpeg || goto :fail
echo.
py fetch_clips.py --setup || goto :fail
echo.
echo Scheduling it: every morning 8:20 AM, retrying every 30 minutes until 12:20 PM...
schtasks /create /f /tn "Internet Ranked Clip Fetch" /tr "\"%~dp0run_fetcher.bat\"" /sc daily /st 08:20 /ri 30 /du 04:00 || goto :fail
echo.
echo All set. Your PC needs to be on (and you signed in) in the morning for it to run.
echo Log: %USERPROFILE%\.internet-ranked\fetch.log
pause
exit /b 0
:fail
echo.
echo Setup stopped because of the error above.
pause
exit /b 1
