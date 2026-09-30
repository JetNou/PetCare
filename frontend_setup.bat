@echo off
chcp 65001 >nul

echo ===============================
echo Настройка Frontend
echo ===============================

cd frontend
echo.

REM Проверка .env
if exist .env (
    echo Файл .env уже существует — пропускаем копирование.
) else (
    echo Копирование .env.example в .env
    copy .env.example .env
)

echo.
echo Открываем .env для настройки...
notepad .env

echo.
echo После завершения настройки .env нажмите любую клавишу.
pause

echo.
echo Выберите пакетный менеджер:
echo.
echo 1 - Bun
echo 2 - npm
echo.

choice /c 12 /n /m "Введите номер: "
set PM=%errorlevel%

echo.
echo Устанавливать зависимости?
echo.
echo 1 - Да
echo 2 - Нет
echo.

choice /c 12 /n /m "Введите номер: "
set INSTALL=%errorlevel%

echo.

REM ----------------------------
REM Bun
REM ----------------------------
if "%PM%"=="1" (
    echo Выбран Bun.

    if "%INSTALL%"=="1" (
        echo Установка зависимостей через Bun...
        bun install
    ) else (
        echo Установка зависимостей пропущена.
    )

    echo.
    echo Запуск фронтенда...
    bun run dev --host 127.0.0.1
)

REM ----------------------------
REM npm
REM ----------------------------
if "%PM%"=="2" (
    echo Выбран npm.

    if "%INSTALL%"=="1" (
        echo Установка зависимостей через npm...
        npm install
    ) else (
        echo Установка зависимостей пропущена.
    )

    echo.
    echo Запуск фронтенда...
    npm run dev -- --host=0.0.0.0
)

pause