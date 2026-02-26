"""Drop all tables and re-seed. Shortcut for: python -m backend.seed --force"""
import subprocess
import sys

sys.exit(subprocess.call([sys.executable, "-m", "backend.seed", "--force"]))
