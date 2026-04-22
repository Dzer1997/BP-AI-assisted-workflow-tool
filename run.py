import subprocess
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

env = os.environ.copy()
env["PYTHONPATH"] = str(SRC)

print("Starting Flask API...")
flask = subprocess.Popen(
    ["python", "-m", "web.backend.app"],
    env=env
)

print("Starting Pipeline...")
pipeline = subprocess.Popen(
    ["python", "-m", "realview_chat.app"],
    env=env
)

flask.wait()
pipeline.wait()