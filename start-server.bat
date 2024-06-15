@echo off
if exist server.lock (
    echo Server is already running.
    pause
    exit /b
)
echo Creating lock file.
echo lock > server.lock
python server.py
del server.lock
pause
