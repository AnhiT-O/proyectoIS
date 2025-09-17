import signal
import subprocess
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

process = None
def handle_sigint(signum, frame):
	global process
	print("\nServidor detenido por el usuario (Ctrl+C). Cerrando...")
	if process:
		process.terminate()
	sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

process = subprocess.Popen(["python", "-m", "http.server", "8080"])
process.wait()