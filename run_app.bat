@echo off
REM Activate the virtual environment
call .venv\Scripts\activate

REM Run the Python script that starts the Flask app and ngrok
python run_apps.py