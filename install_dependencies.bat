@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

REM Переходим в директорию, где находится скрипт
cd /d "%~dp0"

echo ========================================
echo УСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ ИГРЫ АРКАНОИД
echo ========================================
echo.

REM Проверяем наличие глобального Python
python --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Python не найден! Установите Python 3.11-3.13
    echo Убедитесь, что Python добавлен в PATH
    pause
    exit /b 1
)

echo Используется Python:
python --version
echo.

REM [ШАГ 1] Создание виртуального окружения .venv если его нет
if exist ".venv\Scripts\python.exe" (
    echo ✅ Виртуальное окружение .venv уже существует
) else (
    echo [ШАГ 1] Создание виртуального окружения .venv...
    python -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Ошибка создания виртуального окружения!
        goto error_exit
    )
    echo ✅ Виртуальное окружение .venv создано!
)

echo.
echo [ШАГ 2] Активация виртуального окружения...
call .venv\Scripts\activate.bat
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Ошибка активации виртуального окружения!
    goto error_exit
)

echo.
echo [ШАГ 3] Проверка и установка Poetry в .venv...
.venv\Scripts\python.exe -m poetry --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo ✅ Poetry уже установлен в .venv
) else (
    echo Установка Poetry в .venv...
    .venv\Scripts\python.exe -m pip install poetry --quiet
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Ошибка установки Poetry!
        goto error_exit
    )
    echo ✅ Poetry успешно установлен в .venv!
)

echo.
echo [ШАГ 4] Настройка Poetry для использования .venv...
.venv\Scripts\python.exe -m poetry env use .venv\Scripts\python.exe --quiet
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Предупреждение: не удалось настроить Poetry для использования .venv
    echo    Продолжаем установку...
)

echo.
echo [ШАГ 5] Установка зависимостей с помощью Poetry...
echo    (устанавливаем только зависимости, без установки проекта)
.venv\Scripts\python.exe -m poetry install --no-root
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Ошибка установки зависимостей!
    goto error_exit
)

echo.
echo [ШАГ 6] Проверка установки...
.venv\Scripts\python.exe -c "import pygame, numpy, sklearn; print('✅ Все зависимости работают!')"
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Библиотеки не работают после установки!
    goto error_exit
)

echo.
echo ========================================
echo ✅ УСТАНОВКА УСПЕШНА!
echo ========================================
echo.
echo 🎮 Игра готова к запуску!
echo.
echo ⚠️  ВАЖНО: Активация .venv в этом скрипте действует только внутри скрипта.
echo    После завершения скрипта активация теряется, поэтому при запуске игры
echo    нужно снова активировать .venv (или использовать полный путь к Python).
echo.
echo 📝 СПОСОБЫ ЗАПУСКА:
echo.
echo 1. Используйте скрипт run_game.bat (рекомендуется):
echo    run_game.bat
echo.
echo 2. Вручную с активацией .venv:
echo    .venv\Scripts\activate.bat
echo    python game\PyGameBall.py
echo.
echo 3. Без активации (полный путь):
echo    "%~dp0.venv\Scripts\python.exe" "%~dp0game\PyGameBall.py"
echo.
echo Виртуальное окружение: .venv\
echo Poetry установлен локально в .venv
echo.
goto success_exit

:error_exit
echo.
echo ========================================
echo ❌ УСТАНОВКА НЕ УДАЛАСЬ
echo ========================================
echo.
echo РЕШЕНИЯ:
echo 1. Убедитесь, что Python 3.11-3.13 установлен
echo 2. Проверьте, что Python добавлен в PATH
echo 3. Запустите скрипт от имени администратора
echo 4. Попробуйте вручную:
echo    python -m venv .venv
echo    .venv\Scripts\activate.bat
echo    .venv\Scripts\python.exe -m pip install poetry
echo    .venv\Scripts\python.exe -m poetry install --no-root
echo.
pause
exit /b 1

:success_exit
echo 🎯 Поддерживаемые функции:
echo    - Обычная игра
echo    - Система рекордов
echo    - Настройки сложности
echo.
pause
exit /b 0
