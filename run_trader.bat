@echo off
rem Run the ETF auto trader (ch8\8_4_auto_trader.py). Registered in Windows Task Scheduler.
cd /d "%~dp0ch8"
"C:\workspaces\quant\quant.venv\Scripts\python.exe" 8_4_auto_trader.py
