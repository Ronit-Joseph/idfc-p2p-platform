"""Convenience wrapper — seeds the database from the project root.

Usage:
    python scripts/seed_db.py           # seed if empty
    python scripts/seed_db.py --force   # drop + re-seed
"""
import subprocess
import sys

sys.exit(subprocess.call([sys.executable, "-m", "backend.seed"] + sys.argv[1:]))
