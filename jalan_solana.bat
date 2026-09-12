@echo off
E:
cd \WhaleMonitor
call .venv\Scripts\activate
python src\run_solana.py
pause