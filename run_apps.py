import subprocess

# Command to run the Flask app
flask_command = "cmd /k python mainapp.py"

# Command to run ngrok
ngrok_command = "cmd /k ngrok http --url=superb-monarch-charmed.ngrok-free.app 5000"

# Open a new command prompt window to run the Flask app
subprocess.Popen(['start', 'cmd', '/k', flask_command], shell=True)

# Open a new command prompt window to run ngrok
subprocess.Popen(['start', 'cmd', '/k', ngrok_command], shell=True)