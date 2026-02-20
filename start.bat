@echo off
echo [*] ACTIVATING MAGI ENVIRONMENT...
call .venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: Failed to activate vitual environment.
    pause
    exit /b %ERRORLEVEL%
)

echo [*] LAUNCHING MAGI SYSTEM...
python run_magi.py
pause
