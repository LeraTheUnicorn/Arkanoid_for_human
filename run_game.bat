@echo off
setlocal
chcp 65001 >nul

REM Переходим в директорию, где находится скрипт
cd /d "%~dp0"

echo ========================================
echo ЗАПУСК ИГРЫ АРКАНОИД
echo ========================================
echo.

REM Проверяем наличие виртуального окружения
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Виртуальное окружение .venv не найдено!
    echo.
    echo Сначала запустите install_dependencies.bat для установки зависимостей.
    echo.
    pause
    exit /b 1
)

REM Проверяем наличие файла игры
if not exist "game\PyGameBall.py" (
    echo ❌ Файл игры game\PyGameBall.py не найден!
    echo.
    pause
    exit /b 1
)

echo ✅ Виртуальное окружение найдено
echo ✅ Запуск игры...
echo.

REM Запускаем игру используя Python из .venv
.venv\Scripts\python.exe game\PyGameBall.py

REM Если игра завершилась с ошибкой
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo ❌ Игра завершилась с ошибкой (код: !ERRORLEVEL!)
    echo.
    echo РЕШЕНИЯ:
    echo 1. Убедитесь, что зависимости установлены: install_dependencies.bat
    echo 2. Проверьте, что все файлы игры на месте
    echo 3. Запустите игру снова
    echo.
    pause
    exit /b !ERRORLEVEL!
)

exit /b 0
