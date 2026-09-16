@echo off
REM ============================================================
REM allure_report.bat — 生成静态 HTML 报告并用浏览器打开
REM
REM 结果目录：allure-results
REM 输出目录：allure-report（可直接拷贝分享）
REM ============================================================

setlocal
set SCRIPT_DIR=%~dp0
set RESULTS_DIR=%SCRIPT_DIR%allure-results
set REPORT_DIR=%SCRIPT_DIR%allure-report

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

echo 正在生成静态报告到 %REPORT_DIR% ...
call allure generate "%RESULTS_DIR%" -o "%REPORT_DIR%" --clean
if errorlevel 1 (
    echo [错误] 报告生成失败
    pause
    exit /b 1
)

echo 报告已生成，正在打开 ...
call allure open "%REPORT_DIR%"
