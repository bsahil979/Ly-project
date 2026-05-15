@echo off
REM Start Analytics Engine Only (FastAPI)
cd /d "%~dp0analytics-engine"
echo Starting Analytics Engine API on port 8000...
pip install -r requirements.txt
uvicorn api:app --port 8000 --reload
pause
