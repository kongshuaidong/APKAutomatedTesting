@echo off
REM 一键运行核心回归：浏览器 -> 应用商店
cd /d "%~dp0"
python run_apk_tests.py --suite core %*
