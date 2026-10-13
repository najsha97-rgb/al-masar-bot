@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
title BOT TELEGRAM AL-MASAR
echo ===================================================================
echo               MEMULAKAN BOT TELEGRAM AL-MASAR                      
echo ===================================================================
echo.
cd /d "%~dp0"
"C:\Users\pc\AppData\Local\Python\pythoncore-3.14-64\python.exe" bot.py
echo.
pause
