@echo off
echo Starting IDFC P2P Platform — Backend API
echo ==========================================
cd /d "%~dp0backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
