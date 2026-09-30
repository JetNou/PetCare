@echo off
chcp 65001 >nul

echo ===============================
echo Настройка Backend
echo ===============================

cd backend
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
echo Выберите режим запуска:
echo.
echo 1 - Создать venv и установить зависимости
echo 2 - Установить зависимости глобально (без venv)
echo 3 - Пропустить установку зависимостей (venv уже есть)
echo.

choice /c 123 /n /m "Введите номер: "

set MODE=%errorlevel%

echo.

if "%MODE%"=="1" (
    echo Создание виртуального окружения...
    if not exist venv\Scripts\activate.bat (
        python -m venv venv
    ) else (
        echo venv уже существует.
    )

    echo Активация venv...
    call venv\Scripts\activate.bat

    echo Установка зависимостей...
    pip install -r requirements.txt
)

if "%MODE%"=="2" (
    echo Установка зависимостей глобально...
    pip install -r requirements.txt
)

if "%MODE%"=="3" (
    echo Установка зависимостей пропущена.
    if not exist venv\Scripts\activate.bat (
        echo vevn не существует используйте другой способ.
    ) else (
        call venv\Scripts\activate.bat
    )
)

echo.
echo Применение миграций базы данных...
alembic upgrade head

echo.
echo ==========================================
echo Запустите redis-server.exe
echo После запуска Redis нажмите любую клавишу
echo ==========================================
pause

echo.
echo Запуск приложения...
python main.py

pause