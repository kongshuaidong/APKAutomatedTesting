@echo off
REM ============================================================
REM allure_serve.bat — 一键打开 Allure 报告（临时预览模式）
REM
REM 前置：已安装 allure CLI（https://github.com/allure-framework/allure2/releases）
REM 用法：双击本文件，或在命令行执行 `allure_serve.bat`
REM ============================================================

setlocal
set SCRIPT_DIR=%~dp0
set RESULTS_DIR=%SCRIPT_DIR%allure-results

where allure >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 allure 命令。
    echo 请从 https://github.com/allure-framework/allure2/releases 下载并把 bin/ 加入 PATH。
    pause
    exit /b 1
)

if not exist "%RESULTS_DIR%" (
    echo [错误] 未找到结果目录 %RESULTS_DIR%
    echo 请先执行 `python run_apk_tests.py --apk <APK>` 生成结果。
    pause
    exit /b 1
)

echo 正在启动 Allure Serve（临时报告，关掉窗口即结束）...
call allure serve "%RESULTS_DIR%"
