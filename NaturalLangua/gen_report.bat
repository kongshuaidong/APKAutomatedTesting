@echo off
REM ============================================================
REM gen_report.bat — 生成并打开 HTML 测试报告（无需 Allure CLI）
REM
REM 直接把 allure-results/*.json 渲染成一个自包含 report.html
REM ============================================================

setlocal
set SCRIPT_DIR=%~dp0

if not exist "%SCRIPT_DIR%allure-results" (
    echo [错误] 未找到 %SCRIPT_DIR%allure-results
    echo 请先执行 `python run_apk_tests.py --apk ^<APK^>` 生成结果。
    pause
    exit /b 1
)

python "%SCRIPT_DIR%gen_report.py" --open
if errorlevel 1 (
    echo [错误] 报告生成失败
    pause
    exit /b 1
)
