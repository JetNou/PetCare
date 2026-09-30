@echo off
chcp 65001 >nul
title Project Starter

echo ===============================
echo Запуск Backend и Frontend
echo ===============================
echo.

echo Открываем Backend...
start "Backend Server" cmd /k "%~dp0backend_setup.bat"

echo Открываем Frontend...
start "Frontend Server" cmd /k "%~dp0frontend_setup.bat"

echo.
echo Все процессы запущены в отдельных окнах.
pause