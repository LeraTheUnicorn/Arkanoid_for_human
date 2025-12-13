# Игра Арканоид
# Версия импортируется из централизованного файла version.py

import os
import sys

# Исправление для запуска файла напрямую: добавляем корневую директорию проекта в sys.path
# Это должно быть сделано ДО всех остальных импортов
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)  # game/
# Поднимаемся на один уровень вверх: game/ -> project_root
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import warnings
from contextlib import contextmanager
from typing import Generator

# Контекстный менеджер для ограниченного подавления предупреждений
@contextmanager
def suppress_pkg_resources_warnings() -> Generator[None, None, None]:
    """Временно подавляет предупреждения о pkg_resources от pygame в ограниченной области"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)
        yield

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"  # Скрыть сообщение поддержки pygame

import random
import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any

# Базовое логирование
import logging
from datetime import datetime

# Создаем директорию для логов
# Для установленного приложения используем каталог данных игры
if getattr(sys, "frozen", False):
    # Для exe файлов используем системные каталоги
    if sys.platform == "win32":
        # Windows: используем LOCALAPPDATA
        try:
            localappdata = os.environ.get("LOCALAPPDATA")
            if localappdata:
                game_dir = os.path.join(localappdata, "Games", "Arkanoid")
                log_dir = os.path.join(game_dir, "logs")
            else:
                # Fallback: директория exe
                log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
        except (KeyError, OSError):
            # Fallback: директория exe
            log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
    else:
        # Linux/Mac: используем XDG_DATA_HOME или ~/.local/share
        try:
            xdg_data_home = os.environ.get("XDG_DATA_HOME")
            if xdg_data_home:
                game_dir = os.path.join(xdg_data_home, "Arkanoid")
            else:
                home = os.path.expanduser("~")
                game_dir = os.path.join(home, ".local", "share", "Arkanoid")
            log_dir = os.path.join(game_dir, "logs")
        except (KeyError, OSError):
            # Fallback: директория exe
            log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
else:
    # В режиме разработки используем logs/ в корне проекта
    log_dir = os.path.join(project_root, "logs")

try:
    os.makedirs(log_dir, exist_ok=True)
except (OSError, PermissionError):
    # Если не удалось создать в logs, используем текущую директорию
    log_dir = os.path.dirname(os.path.abspath(__file__))

# Удаляем старые файлы логов при запуске
try:
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            # Удаляем только файлы логов (начинающиеся с "game_" и заканчивающиеся на ".log")
            if os.path.isfile(file_path) and filename.startswith("game_") and filename.endswith(".log"):
                try:
                    os.remove(file_path)
                except (OSError, PermissionError) as e:
                    # Если не удалось удалить файл, просто пропускаем его
                    if not getattr(sys, "frozen", False):
                        print(f"[WARNING] Не удалось удалить старый лог файл {file_path}: {e}")
except (OSError, PermissionError) as e:
    # Если не удалось очистить логи, продолжаем работу
    if not getattr(sys, "frozen", False):
        print(f"[WARNING] Не удалось очистить каталог логов: {e}")

# Имя файла лога с датой и временем
log_filename = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(log_dir, log_filename)

# Проверяем переменную окружения для управления логированием в консоль
# ENABLE_CONSOLE_LOGGING может быть: "1", "true", "yes" (включить) или "0", "false", "no" (выключить)
# По умолчанию включено для обратной совместимости
enable_console_logging = os.environ.get("ENABLE_CONSOLE_LOGGING", "1").lower() in ("1", "true", "yes")

# Настраиваем обработчики логирования
handlers: list[logging.Handler] = [logging.FileHandler(log_filepath, encoding='utf-8')]
if enable_console_logging:
    handlers.append(logging.StreamHandler())  # Вывод в консоль

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)
console_status = "включено" if enable_console_logging else "выключено"
logger.info(f"Логирование настроено. Лог файл: {log_filepath}, консоль: {console_status}")

# Импортируем pygame с ограниченным подавлением предупреждений
with suppress_pkg_resources_warnings():
    import pygame

# Импорты с поддержкой как относительных, так и абсолютных путей
try:
    # Пытаемся использовать относительные импорты (когда запускается как модуль)
    from .highscores import HighScoreManager
    from .settings import SettingsManager
    from .game_models import Ball, Paddle
except ImportError:
    # Если относительные импорты не работают (когда запускается напрямую), используем абсолютные
    from game.highscores import HighScoreManager
    from game.settings import SettingsManager
    from game.game_models import Ball, Paddle

def resource_path(relative_path: str) -> str:
    """
    Получает абсолютный путь к ресурсу, работает как в разработке, так и в exe.
    
    Кросс-платформенная функция для получения правильного пути к ресурсам.
    Использует os.path.join для корректной работы на разных ОС.
    
    Args:
        relative_path: Относительный путь к ресурсу (например, "audio/file.ogg" или "images/d2.gif")
                      Путь должен быть относительно resources/
        
    Returns:
        Абсолютный путь к ресурсу, нормализованный для текущей ОС
        
    Note:
        В режиме разработки использует директорию resources/ в корне проекта.
        В скомпилированном exe (PyInstaller) ресурсы находятся в _MEIPASS/resources/.
        После установки через MSI ресурсы находятся в {app}/resources/ рядом с exe.
    """
    # Проверяем, запущено ли приложение как exe
    if getattr(sys, "frozen", False):
        # Для установленного через MSI exe: ресурсы находятся рядом с exe в resources/
        # СНАЧАЛА проверяем путь рядом с exe (для установленного через MSI)
        exe_dir = os.path.dirname(sys.executable)
        resources_path = os.path.join(exe_dir, "resources")
        
        # Проверяем существование файла ресурса по этому пути
        test_path = os.path.join(resources_path, relative_path)
        if os.path.exists(test_path):
            # Ресурсы найдены рядом с exe (установлено через MSI)
            full_path = os.path.join(resources_path, relative_path)
            return os.path.normpath(full_path)
        
        # Если не найдено рядом с exe, пробуем альтернативные пути
        alt_paths = [
            os.path.join(exe_dir, "..", "resources"),  # На уровень выше
            os.path.join(os.path.dirname(exe_dir), "resources"),  # Родительская директория
        ]
        for alt_path in alt_paths:
            alt_path = os.path.normpath(alt_path)
            test_path = os.path.join(alt_path, relative_path)
            if os.path.exists(test_path):
                full_path = os.path.join(alt_path, relative_path)
                return os.path.normpath(full_path)
        
        # Если не найдено рядом с exe, используем _MEIPASS (для PyInstaller без установки)
        try:
            base_path = sys._MEIPASS  # type: ignore[attr-defined]
            resources_path = os.path.join(base_path, "resources")
            full_path = os.path.join(resources_path, relative_path)
            return os.path.normpath(full_path)
        except AttributeError:
            # Fallback: пробуем resources/ в корне проекта (для разработки)
            resources_path = os.path.join(project_root, "resources")
    else:
        # В режиме разработки используем resources/ в корне проекта
        resources_path = os.path.join(project_root, "resources")

    # Используем os.path.join для кросс-платформенной совместимости
    # и нормализуем путь для корректной работы на всех ОС
    full_path = os.path.join(resources_path, relative_path)
    return os.path.normpath(full_path)

# Импортируем конфигурацию из централизованного файла
try:
    from .game_config import (
        BALL_SIZE,
        BALL_SPEED_DEFAULT,
        BRICK_COLS,
        BRICK_HEIGHT,
        BRICK_OFFSET_TOP,
        BRICK_PADDING,
        BRICK_ROWS,
        BRICK_WIDTH,
        FPS,
        MAX_LIVES,
        PADDLE_HEIGHT,
        PADDLE_SPEED,
        PADDLE_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_WIDTH,
        SEPARATION_ZONE_BOTTOM,
        SEPARATION_ZONE_TOP,
    )
except ImportError:
    from game.game_config import (
        BALL_SIZE,
        BALL_SPEED_DEFAULT,
        BRICK_COLS,
        BRICK_HEIGHT,
        BRICK_OFFSET_TOP,
        BRICK_PADDING,
        BRICK_ROWS,
        BRICK_WIDTH,
        FPS,
        MAX_LIVES,
        PADDLE_HEIGHT,
        PADDLE_SPEED,
        PADDLE_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_WIDTH,
        SEPARATION_ZONE_BOTTOM,
        SEPARATION_ZONE_TOP,
    )

def generate_tone_sound(
    frequency: float, duration: float, sample_rate: int = 44100, volume: float = 0.3
) -> pygame.mixer.Sound:
    """
    Генерирует короткий тональный звук для звуковых эффектов.
    
    Создает синусоидальную волну с гармониками и затуханием для более естественного звука.
    
    Args:
        frequency: Частота звука в герцах
        duration: Длительность звука в секундах
        sample_rate: Частота дискретизации (по умолчанию 44100 Гц)
        volume: Громкость звука от 0.0 до 1.0 (по умолчанию 0.3)
        
    Returns:
        pygame.mixer.Sound объект со сгенерированным звуком
    """
    frames = int(duration * sample_rate)
    t = np.linspace(0, duration, frames)

    # Генерируем синусоидальную волну с небольшим количеством гармоник для более богатого звука
    wave = np.sin(2 * np.pi * frequency * t)
    wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)  # Первая гармоника
    wave += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)  # Вторая гармоника

    # Добавляем затухание
    envelope = np.exp(-3 * t)  # Быстрое затухание
    wave = wave * envelope

    # Нормализуем и приводим к 16-битному формату
    wave = np.clip(wave * volume, -1.0, 1.0)
    wave_16bit = (wave * 32767).astype(np.int16)

    # Создаем pygame Sound объект
    stereo_wave = np.zeros((len(wave_16bit), 2), dtype=np.int16)
    stereo_wave[:, 0] = wave_16bit
    stereo_wave[:, 1] = wave_16bit

    return pygame.sndarray.make_sound(stereo_wave)

def is_valid_player_name_char(char: str) -> bool:
    """
    Проверяет, является ли символ допустимым для имени игрока.
    
    Args:
        char: Символ для проверки
        
    Returns:
        True если символ допустим (латинские или кириллические буквы), False иначе
    """
    if not char or len(char) != 1:  # Проверяем пустые строки и многосимвольные строки
        return False
    # Разрешаем только буквы (латинские и кириллические)
    # isalpha() поддерживает Unicode, включая кириллицу
    return char.isalpha() and not char.isspace()

def generate_paddle_sound() -> pygame.mixer.Sound:
    """
    Генерирует звук отскока от платформы.
    
    Returns:
        pygame.mixer.Sound объект со звуком отскока (нота E4, 330 Гц)
    """
    return generate_tone_sound(330, 0.15, volume=0.4)  # E4 - 330 Гц

def get_player_name(
    screen: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    highscore_manager: HighScoreManager,
) -> tuple[str, bool, bool]:
    """
    Получает имя игрока через ввод с клавиатуры.
    
    Отображает экран ввода имени.
    Поддерживает валидацию ввода (только буквы).
    
    Args:
        screen: Поверхность pygame для отрисовки
        font: Шрифт для обычного текста
        big_font: Шрифт для заголовков
        highscore_manager: Менеджер рекордов для отображения таблицы
        
    Returns:
        Кортеж из 3 элементов:
        - Имя игрока (str)
        - Состояние звука (bool)
        - Флаг выхода из игры (bool)
    """
    input_text = ""
    input_active = True
    sound_enabled = True
    exit_game = False
    while input_active:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game = True
                return (
                    "",
                    sound_enabled,
                    exit_game,
                )  # Выход из игры по крестику
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Имя обязательно для ввода!
                    cleaned_name = input_text.strip()
                    if not cleaned_name:
                        # Имя пустое - не запускаем игру, показываем предупреждение
                        input_text = ""  # Очищаем поле для повторного ввода
                        continue  # Продолжаем ввод
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif (
                    len(input_text) < 20
                    and event.unicode
                    and is_valid_player_name_char(event.unicode)
                ):  # Ограничение длины имени и допустимых символов
                    input_text += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    # Выход из игры
                    return "", sound_enabled, True
                elif event.key == pygame.K_m:
                    # Переключение всех звуков (музыки и эффектов)
                    if sound_enabled:
                        pygame.mixer.music.stop()
                        sound_enabled = False
                    else:
                        pygame.mixer.music.play(-1)
                        sound_enabled = True

        # Отрисовка экрана
        screen.fill((10, 10, 30))

        # Заголовок
        title = big_font.render("Введите ваше имя:", True, (255, 255, 255))
        title_rect = title.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
        )
        screen.blit(title, title_rect)

        # Поле ввода
        input_surface = font.render(input_text, True, (255, 255, 255))
        input_rect = input_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        )

        # Рамка поля ввода (красная для пустого поля)
        if not input_text.strip():
            pygame.draw.rect(
                screen, (255, 100, 100), input_rect.inflate(20, 10), 2
            )  # Красная рамка для пустого поля
        else:
            pygame.draw.rect(
                screen, (255, 255, 255), input_rect.inflate(20, 10), 2
            )  # Белая рамка для заполненного
        screen.blit(input_surface, input_rect)

        # Подсказка
        render_colored_hint(
            screen,
            font,
            "Введите имя игрока и нажмите Enter",
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 20),
        )

        # Подсказка о звуке
        render_colored_hint(
            screen,
            font,
            "Нажмите M для отключения всех звуков",
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50),
        )

        # Подсказка о настройках
        render_colored_hint(
            screen,
            font,
            "Для управления скоростью мяча нажимайте ↑ ↓",
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 80),
        )

        pygame.display.flip()

    # ФИНАЛЬНАЯ ВАЛИДАЦИЯ: убеждаемся, что имя корректно
    final_name = input_text.strip()
    if not final_name:
        final_name = "Player"

    return final_name, sound_enabled, exit_game

def show_highscores(
    screen: pygame.Surface,
    font: pygame.font.Font,
    highscore_manager: HighScoreManager,
    exit_on_esc: bool = False,
) -> tuple[bool, bool]:
    """
    Отображает таблицу рекордов.
    Возвращает (состояние_звука, exit_game).
    Если exit_on_esc=True, то ESC выходит из игры полностью, иначе возвращает False.
    """
    # Создаем моноширинный шрифт для правильного отображения таблицы
    # Используем список резервных шрифтов для кросс-платформенной совместимости
    mono_font_names = ["consolas", "courier new", "courier", "monospace", "liberation mono"]
    mono_font = None
    
    for font_name in mono_font_names:
        try:
            mono_font = pygame.font.SysFont(font_name, 18)
            break
        except (OSError, ValueError):
            continue
    
    # Если ни один системный шрифт не доступен, используем встроенный моноширинный шрифт pygame
    if mono_font is None:
        try:
            mono_font = pygame.font.Font(pygame.font.get_default_font(), 18)
        except:
            mono_font = font  # Последний резерв - используем обычный шрифт

    # Состояние звука
    sound_enabled = True

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return sound_enabled, True  # Выход из игры по крестику
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if exit_on_esc:
                        return sound_enabled, True  # Выход из игры
                    else:
                        waiting = False  # Возвращаемся назад
                elif event.key == pygame.K_BACKSPACE:
                    waiting = False  # Возвращаемся назад
                elif event.key == pygame.K_m:
                    # Переключение всех звуков
                    if sound_enabled:
                        pygame.mixer.music.stop()
                        sound_enabled = False
                    else:
                        pygame.mixer.music.play(-1)
                        sound_enabled = True

        # Отрисовка экрана рекордов
        screen.fill((10, 10, 30))

        # Заголовок
        title = font.render("ТАБЛИЦА РЕКОРДОВ", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 30))
        screen.blit(title, title_rect)

        # Получаем отформатированные данные для отображения
        highscores = highscore_manager.get_top_scores()

        if not highscores:
            no_scores = font.render("Пока нет рекордов", True, (200, 200, 200))
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 150))
            screen.blit(no_scores, no_scores_rect)
        else:
            # Линии разделителя
            separator_line = "=" * 69
            separator_surf = mono_font.render(separator_line, True, (150, 150, 150))
            separator_rect = separator_surf.get_rect(center=(SCREEN_WIDTH // 2, 70))
            screen.blit(separator_surf, separator_rect)

            # Заголовки колонок
            headers = "   Место | Игрок               | Очки | Время  "
            headers_surf = mono_font.render(headers, True, (255, 255, 255))
            headers_rect = headers_surf.get_rect(center=(SCREEN_WIDTH // 2, 95))
            screen.blit(headers_surf, headers_rect)

            # Вторая линия разделителя
            separator_surf2 = mono_font.render(separator_line, True, (150, 150, 150))
            separator_rect2 = separator_surf2.get_rect(center=(SCREEN_WIDTH // 2, 120))
            screen.blit(separator_surf2, separator_rect2)

            # Данные таблицы
            y_offset = 145
            for i, score_data in enumerate(highscores, 1):
                # Форматируем данные точно как в правильном файле
                if i < 10:
                    place = f"   {i}.  "
                else:
                    place = f"  {i}.  "

                player_name = score_data["player_name"]
                player = f"{player_name[:20]:<20}"
                score = f"{score_data['score']:>3}"
                time = f"{score_data['time_formatted']:>5}"

                # Собираем строку
                row = f"{place}| {player}| {score}  | {time}"

                # Отображаем строку
                row_surf = mono_font.render(row, True, (255, 255, 255))
                row_rect = row_surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(row_surf, row_rect)

                y_offset += 25

        # Подсказки для возврата
        if exit_on_esc:
            render_colored_hint(
                screen,
                font,
                "Backspace - возврат, ESC - выход из игры",
                (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 70),
            )
        else:
            render_colored_hint(
                screen,
                font,
                "BackSpace - возврат",
                (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 70),
            )

        pygame.display.flip()

    return sound_enabled, False  # Возвращаемся, не выходя из игры

def trigger_instant_victory(
    screen: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    score: int,
    player_name: str,
    game_time_seconds: int,
    highscore_manager: "HighScoreManager",
    settings_manager: "SettingsManager",
    ball: "Ball",
) -> tuple[bool, bool, bool]:
    """
    Показывает заставку победы и экран результатов.
    Используется для немедленной победы (например, при тройном нажатии "1").
    
    Args:
        screen: Поверхность pygame для отрисовки
        font: Шрифт для обычного текста
        big_font: Шрифт для заголовков
        score: Финальный счет игрока
        player_name: Имя игрока
        game_time_seconds: Время игры в секундах
        highscore_manager: Менеджер рекордов
        settings_manager: Менеджер настроек игры
        ball: Объект мяча
        
    Returns:
        Кортеж из 3 элементов:
        - Состояние звука (bool)
        - Флаг перезапуска игры (bool)
        - Флаг выхода из игры (bool)
    """
    # Показываем заставку победы
    try:
        logger.info("Показываю заставку победы...")
        show_victory_splash(screen, duration_seconds=5.0)
        logger.info("Заставка победы показана успешно")
    except Exception as e:
        logger.error(f"Ошибка при показе заставки победы: {e}")
        import traceback
        logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
        # В установленной версии также логируем ошибки
        if not getattr(sys, "frozen", False):
            traceback.print_exc()
    
    # Показываем экран результатов
    return show_game_results(
        screen,
        font,
        big_font,
        score,
        player_name,
        game_time_seconds,
        highscore_manager,
        settings_manager,
        ball,
    )

def show_victory_splash(screen: pygame.Surface, duration_seconds: float = 5.0) -> None:
    """
    Показывает заставку победы с анимированным изображением.
    Использует Pyglet для загрузки анимированного GIF.
    
    Args:
        screen: Поверхность pygame для отрисовки
        duration_seconds: Длительность показа заставки в секундах (по умолчанию 5)
    """
    logger.info("=== НАЧАЛО ПОКАЗА АНИМАЦИИ ПОБЕДЫ ===")
    logger.info(f"Длительность показа: {duration_seconds} секунд")
    
    # Загружаем изображение
    image_path = resource_path("images/d2.gif")
    logger.info(f"Получен путь через resource_path: {image_path}")
    
    # Логируем путь для диагностики
    logger.debug(f"Путь к анимации победы: {image_path}")
    logger.debug(f"Файл существует: {os.path.exists(image_path)}")
    
    if not os.path.exists(image_path):
        logger.warning(f"Анимация не найдена по пути: {image_path}")
        # Пробуем альтернативные пути для установленного через MSI приложения
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            alt_paths = [
                os.path.join(exe_dir, "resources", "images", "d2.gif"),
                os.path.join(exe_dir, "..", "resources", "images", "d2.gif"),
            ]
            for alt_path in alt_paths:
                alt_path = os.path.normpath(alt_path)
                logger.debug(f"Проверяю альтернативный путь: {alt_path} (существует: {os.path.exists(alt_path)})")
                if os.path.exists(alt_path):
                    logger.info(f"Найден альтернативный путь: {alt_path}")
                    image_path = alt_path
                    break
        else:
            # В режиме разработки проверяем прямой путь
            dev_path = os.path.join(project_root, "resources", "images", "d2.gif")
            if os.path.exists(dev_path):
                logger.info(f"Использую путь разработки: {dev_path}")
                image_path = dev_path
    
    # Финальная проверка - если файл все еще не найден, выходим
    if not os.path.exists(image_path):
        logger.error(f"Анимация победы не найдена ни по одному из путей! Финальный путь: {image_path}")
        return
    
    try:
        # Используем PIL для загрузки и изменения размера GIF (НЕ МЕНЯЕМ размер окна!)
        try:
            logger.debug(f"Пытаюсь загрузить анимацию через PIL: {image_path}")
            from PIL import Image, ImageSequence
            
            # Получаем размеры экрана (НЕ МЕНЯЕМ их!)
            screen_width, screen_height = screen.get_size()
            
            # Определяем правильный фильтр для изменения размера (совместимость с разными версиями Pillow)
            # Pillow >= 9.0.0 использует Image.Resampling.LANCZOS, старые версии - Image.LANCZOS
            if hasattr(Image, 'Resampling'):
                lanczos_filter = Image.Resampling.LANCZOS
            else:
                # Для старых версий Pillow используем getattr для безопасного доступа
                # Совместимость со старыми версиями Pillow, где LANCZOS это int
                lanczos_filter: Any = getattr(Image, 'LANCZOS', 1)  # type: ignore[no-redef]  # 1 - это числовая константа LANCZOS
            
            # Загружаем GIF с помощью PIL
            logger.debug(f"Открываю GIF файл: {image_path}")
            with Image.open(image_path) as im:
                logger.debug(f"GIF открыт успешно. Формат: {im.format}, Размер: {im.size}, Режим: {im.mode}")
                # Получаем длительность кадров из метаданных
                default_duration = im.info.get("duration", 100)
                logger.debug(f"Длительность кадра по умолчанию: {default_duration} мс")
                
                # Изменяем размер каждого кадра до размера экрана (800x600)
                frames = []
                frame_durations = []
                
                frame_count = 0
                for i, frame in enumerate(ImageSequence.Iterator(im)):
                    frame_count += 1
                    # Копируем кадр и изменяем размер до размера экрана
                    resized_frame = frame.copy().resize((screen_width, screen_height), lanczos_filter)
                    logger.debug(f"Обработан кадр {i+1}, размер: {resized_frame.size}")
                    
                    # Получаем длительность кадра
                    duration = frame.info.get("duration", default_duration)
                    frame_durations.append(duration)
                    
                    # Конвертируем PIL Image в pygame Surface
                    # Конвертируем в RGBA для поддержки прозрачности
                    if resized_frame.mode != 'RGBA':
                        resized_frame = resized_frame.convert('RGBA')
                    
                    # Получаем данные изображения
                    img_data = resized_frame.tobytes()
                    
                    # Создаем pygame Surface
                    try:
                        frame_surface = pygame.image.fromstring(
                            img_data, (screen_width, screen_height), 'RGBA'
                        )
                    except (AttributeError, TypeError):
                        # Fallback для новых версий pygame
                        frame_surface = pygame.image.frombuffer(
                            img_data, (screen_width, screen_height), 'RGBA'
                        )
                    frame_surface = frame_surface.convert_alpha()
                    
                    frames.append(frame_surface)
                    
            
            logger.info(f"Загружено кадров анимации: {len(frames)}")
            if len(frames) == 0:
                logger.error("Не удалось загрузить кадры анимации - список кадров пуст")
                raise ValueError("Не удалось загрузить кадры анимации")
            
            # Изображение уже имеет размер экрана, координаты (0, 0)
            x = 0
            y = 0
            
            
            # Время начала показа
            start_time = time.time()
            clock = pygame.time.Clock()
            frame_index = 0
            frame_accumulator = 0.0
            last_frame_time = time.time()
            
            logger.info(f"Начинаю показ анимации. Кадров: {len(frames)}, Длительность: {duration_seconds} сек")
            
            # Показываем заставку в течение указанного времени
            
            # Если только один кадр, просто показываем его
            if len(frames) == 1:
                logger.debug("Показываю один кадр анимации")
                while time.time() - start_time < duration_seconds:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return
                    screen.fill((0, 0, 0))
                    screen.blit(frames[0], (x, y))
                    pygame.display.flip()
                    clock.tick(30)
            else:
                # Анимация с несколькими кадрами
                logger.debug(f"Показываю анимацию с {len(frames)} кадрами")
                while time.time() - start_time < duration_seconds:
                    # Обрабатываем события (чтобы окно не зависало)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return
                    
                    # Вычисляем время, прошедшее с последнего кадра
                    current_frame_time = time.time()
                    delta_time = current_frame_time - last_frame_time
                    last_frame_time = current_frame_time
                    frame_accumulator += delta_time
                    
                    # Переключаем кадры анимации на основе длительности кадра
                    frame_duration_sec = frame_durations[frame_index] / 1000.0
                    # Минимальная длительность кадра - 30 FPS (33 мс)
                    if frame_duration_sec < 0.033:
                        frame_duration_sec = 0.033
                    
                    # Если накопилось достаточно времени, переключаем кадр
                    if frame_accumulator >= frame_duration_sec:
                        old_index = frame_index
                        frame_index = (frame_index + 1) % len(frames)
                        frame_accumulator -= frame_duration_sec
                        
                    
                    # Очищаем экран
                    screen.fill((0, 0, 0))
                    
                    # Рисуем текущий кадр (уже размером с экран)
                    try:
                        screen.blit(frames[frame_index], (x, y))
                    except (IndexError, pygame.error) as blit_error:
                        logger.error(f"Ошибка при отрисовке кадра {frame_index}: {blit_error}")
                        # Если ошибка при отрисовке, выходим
                        return
                    
                    # Обновляем экран
                    pygame.display.flip()
                    
                    # Ограничиваем FPS для плавной анимации
                    clock.tick(30)
                
                logger.info(f"Анимация показана успешно. Прошло времени: {time.time() - start_time:.2f} сек")
                    
        except (ImportError, Exception) as e:
            # Если PIL не установлен или произошла ошибка, используем pygame для загрузки первого кадра
            logger.warning(f"Ошибка при загрузке через PIL: {e}. Пробую загрузить через pygame")
            # Загружаем статическое изображение через pygame (только первый кадр)
            try:
                logger.debug(f"Пытаюсь загрузить через pygame: {image_path}")
                image = pygame.image.load(image_path)
                logger.debug(f"Изображение загружено через pygame. Размер: {image.get_size()}")
                
                # Получаем размеры экрана (НЕ МЕНЯЕМ их!)
                screen_width, screen_height = screen.get_size()
                
                # Конвертируем изображение в формат, поддерживающий smoothscale
                if image.get_bitsize() not in (24, 32):
                    image = image.convert()
                
                # Растягиваем изображение до размера экрана
                try:
                    image = pygame.transform.smoothscale(image, (screen_width, screen_height))
                except ValueError:
                    # Если smoothscale не работает, используем обычный scale
                    image = pygame.transform.scale(image, (screen_width, screen_height))
                
                # Координаты (0, 0) - изображение уже размером с экран
                x = 0
                y = 0
                
                # Показываем статическое изображение
                start_time = time.time()
                clock = pygame.time.Clock()
                
                while time.time() - start_time < duration_seconds:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return
                    
                    screen.fill((0, 0, 0))
                    screen.blit(image, (x, y))
                    pygame.display.flip()
                    clock.tick(30)
                    
            except Exception as e2:
                # Если даже pygame не может загрузить, просто выходим и переходим к результатам
                logger.error(f"Ошибка при загрузке через pygame: {e2}")
                import traceback
                logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
                # Выходим из функции, чтобы сразу перейти к экрану результатов
                return
                
    except Exception as e:
        # Если не удалось загрузить изображение, просто выходим и переходим к результатам
        logger.error(f"Критическая ошибка при загрузке анимации победы: {e}")
        import traceback
        logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
        # Выходим из функции, чтобы сразу перейти к экрану результатов
        return

def show_game_results(
    screen: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    score: int,
    player_name: str,
    game_time_seconds: int,
    highscore_manager: HighScoreManager,
    settings_manager: SettingsManager,
    ball: "Ball",
) -> tuple[bool, bool, bool]:
    """
    Отображает экран с результатами игры и таблицей рекордов.
    
    Показывает финальный счет, время игры, таблицу рекордов и позволяет
    игроку перезапустить игру или выйти.
    
    Args:
        screen: Поверхность pygame для отрисовки
        font: Шрифт для обычного текста
        big_font: Шрифт для заголовков
        score: Финальный счет игрока
        player_name: Имя игрока
        game_time_seconds: Время игры в секундах
        highscore_manager: Менеджер рекордов для сохранения и отображения
        settings_manager: Менеджер настроек игры
        ball: Объект мяча для доступа к настройкам
        
    Returns:
        Кортеж из 3 элементов:
        - Состояние звука (bool)
        - Флаг перезапуска игры (bool)
        - Флаг выхода из игры (bool)
    """
    game_time_formatted = f"{game_time_seconds // 60}:{game_time_seconds % 60:02d}"

    # Добавляем результат в рекорды и проверяем, попал ли он в топ-10
    score_saved = highscore_manager.add_score(player_name, score, game_time_seconds)

    # Состояние звука
    sound_enabled = True
    restart_game = False
    exit_game = False

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game = True
                return sound_enabled, False, exit_game  # Выход из игры по крестику
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC выходит из игры
                    exit_game = True
                    return sound_enabled, False, exit_game
                elif event.key == pygame.K_RETURN:
                    waiting = False
                    restart_game = True
                elif event.key == pygame.K_h:
                    # Показываем таблицу рекордов (ESC выходит из игры)
                    sound_enabled, exit_game = show_highscores(
                        screen, font, highscore_manager, exit_on_esc=True
                    )
                    if exit_game:
                        exit_game = True
                        return sound_enabled, False, exit_game  # Выход из игры
                elif event.key == pygame.K_m:
                    # Переключение всех звуков
                    if sound_enabled:
                        pygame.mixer.music.stop()
                        sound_enabled = False
                    else:
                        pygame.mixer.music.play(-1)
                        sound_enabled = True

        # Отрисовка экрана результатов
        screen.fill((10, 10, 30))

        # Заголовок
        if score > 0:
            title = big_font.render("Игра окончена!", True, (255, 255, 255))
        else:
            title = big_font.render("Игра окончена", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)

        # Результаты игрока
        result_text = f"Игрок: {player_name}"
        score_text = f"Очки: {score}"
        time_text = f"Время игры: {game_time_formatted}"

        surf1 = font.render(result_text, True, (255, 255, 255))
        surf2 = font.render(score_text, True, (255, 255, 255))
        surf3 = font.render(time_text, True, (255, 255, 255))

        screen.blit(surf1, (SCREEN_WIDTH // 2 - 100, 200))
        screen.blit(surf2, (SCREEN_WIDTH // 2 - 100, 250))
        screen.blit(surf3, (SCREEN_WIDTH // 2 - 100, 300))

        # Сообщение о топ-10
        if not score_saved:
            warning_text = "Результат не попал в топ-10, таблица рекордов не обновлена"
            warning_surface = font.render(warning_text, True, (255, 200, 100))
            warning_rect = warning_surface.get_rect(center=(SCREEN_WIDTH // 2, 360))
            screen.blit(warning_surface, warning_rect)

        # Подсказки
        render_colored_hint(
            screen,
            font,
            "Enter - новая игра, H - рекорды",
            (SCREEN_WIDTH // 2 - 150, 400),
        )
        render_colored_hint(
            screen, font, "ESC - выход из игры", (SCREEN_WIDTH // 2 - 150, 430)
        )

        pygame.display.flip()

    return sound_enabled, restart_game, exit_game

# КРИТИЧНО: Классы Paddle и Ball импортируются из game_models.py


def build_bricks() -> List[pygame.Rect]:
    """
    Создает сетку кирпичей для игры.
    
    Returns:
        Список pygame.Rect объектов, представляющих кирпичи на экране
        
    Note:
        Для использования новой архитектуры см. game_controllers.GameController.build_bricks()
    """
    bricks = []
    start_x = (
        SCREEN_WIDTH - (BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_PADDING)
        ) // 2
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = start_x + col * (BRICK_WIDTH + BRICK_PADDING)
            y = BRICK_OFFSET_TOP + row * (BRICK_HEIGHT + BRICK_PADDING)
            bricks.append(pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT))
    return bricks

def draw_bricks(screen: pygame.Surface, bricks: List[pygame.Rect]) -> None:
    """
    Отрисовывает все кирпичи на экране.
    
    Каждый ряд кирпичей имеет свой цвет из палитры. Кирпичи отрисовываются
    с цветной заливкой и темной рамкой.
    
    Args:
        screen: Поверхность pygame для отрисовки
        bricks: Список прямоугольников кирпичей для отрисовки
        
    Note:
        Для использования новой архитектуры с оптимизацией отрисовки см. game_views.BricksView
    """
    try:
        from .game_config import BRICK_COLORS, BRICK_BORDER_COLOR
    except ImportError:
        from game.game_config import BRICK_COLORS, BRICK_BORDER_COLOR
    
    for idx, brick in enumerate(bricks):
        color = BRICK_COLORS[idx // BRICK_COLS % len(BRICK_COLORS)]
        pygame.draw.rect(screen, color, brick)
        pygame.draw.rect(screen, BRICK_BORDER_COLOR, brick, 2)

def draw_hud(
    screen: pygame.Surface,
    score: int,
    lives_left: int,
    font: pygame.font.Font,
    ball: Ball,
) -> None:
    text = f"Очки: {score} | Жизни: {lives_left} | Скорость: {ball.get_speed()} | ↑ ↓ - скорость"

    surf = font.render(
        text,
        True,
        (255, 255, 255),
    )
    screen.blit(surf, (SCREEN_WIDTH - surf.get_width() - 20, 20))

def render_colored_hint(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: Tuple[int, int],
    base_color: Tuple[int, int, int] = (200, 200, 200),
    key_color: Tuple[int, int, int] = (255, 255, 0),
) -> int:
    """Отображает подсказку с выделенными ключевыми словами цветом"""
    words = text.split()
    x, y = pos
    key_words = ["Enter", "H", "M", "ESC", "↑", "↓"]

    for word in words:
        # Убираем знаки препинания для сравнения
        clean_word = word.rstrip(".,:!?")

        if clean_word in key_words:
            # Выделяем ключевое слово цветом
            color = key_color
        else:
            color = base_color

        surf = font.render(word, True, color)
        screen.blit(surf, (x, y))
        x += surf.get_width() + font.size(" ")[0]  # добавляем пробел

    return x - pos[0]  # возвращаем ширину текста

def draw_start_hint(screen: pygame.Surface, font: pygame.font.Font) -> None:
    text = "Для начала игры нажми ← или →"
    surf = font.render(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(surf, rect)

def draw_pause_hint(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """Отображает подсказку о паузе при потере жизни"""
    text = "Нажмите SPACE для продолжения"
    surf = font.render(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(surf, rect)

def main() -> None:
    startup_start_time = time.time()
    if not getattr(sys, "frozen", False):
        print(f"[STARTUP] Начало инициализации игры...")
    
    pygame.init()
    pygame.mixer.init()  # Инициализация аудио микшера
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Арканоид")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 42, bold=True)
    
    if not getattr(sys, "frozen", False):
        pygame_init_time = time.time() - startup_start_time
        print(f"[STARTUP] pygame инициализирован за {pygame_init_time:.3f} сек")

    # Инициализация менеджеров
    highscore_manager = HighScoreManager()
    settings_manager = SettingsManager()

    # Загрузка звуковых эффектов и генерация звуков удара по кубикам
    try:
        # Генерируем звук отскока от платформы
        paddle_bounce_sound = generate_paddle_sound()

        # Генерируем разные тональные звуки для ударов по кубикам
        brick_hit_sounds = [
            generate_tone_sound(440, 0.2),  # A4 - 440 Гц
            generate_tone_sound(523.25, 0.2),  # C5 - ~523 Гц
            generate_tone_sound(659.25, 0.2),  # E5 - ~659 Гц
        ]
        # Пытаемся загрузить фоновую музыку (но не запускаем автоматически)
        try:
            music_path = resource_path("audio/Night_Prowler.ogg")
            # Нормализуем путь для корректной работы на Windows
            music_path = os.path.normpath(music_path)
            
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.3)
                # Музыка будет запущена после ввода имени игрока
            else:
                # Файл не найден - выводим отладочную информацию только в режиме разработки
                if not getattr(sys, "frozen", False):
                    print(f"[DEBUG] Файл музыки не найден по пути: {music_path}")
                    # Пробуем альтернативный путь относительно корня проекта
                    alt_path = os.path.join(project_root, "resources", "audio", "Night_Prowler.ogg")
                    alt_path = os.path.normpath(alt_path)
                    if os.path.exists(alt_path):
                        print(f"[DEBUG] Найден альтернативный путь: {alt_path}")
                        pygame.mixer.music.load(alt_path)
                        pygame.mixer.music.set_volume(0.3)
        except (pygame.error, FileNotFoundError, OSError) as e:
            # Музыка не загружена - выводим информацию только в режиме разработки
            if not getattr(sys, "frozen", False):
                print(f"[DEBUG] Не удалось загрузить фоновую музыку: {e}")
    except pygame.error as e:
        # Не выводим в exe файле
        if not getattr(sys, "frozen", False):
            print(f"Звуковые эффекты не загружены: {e}")
        paddle_bounce_sound = None
        brick_hit_sounds = None

    # Инициализация переменных
    score = 0
    lives_left = MAX_LIVES
    game_over = False
    game_started = False
    game_paused = False  # Флаг паузы при потере жизни
    running = True
    sound_enabled = True
    should_exit = False  # Флаг для полного выхода из игры

    while True:  # Внешний цикл для возврата к вводу имени
        running = True  # Всегда начинаем с флага running=True

        # ПОЛНЫЙ СБРОС СОСТОЯНИЯ ИГРЫ ПРИ КАЖДОМ НОВОМ ЗАПУСКЕ
        paddle = Paddle()
        ball = Ball()
        ball_speed = settings_manager.get_ball_speed()
        ball.set_speed(ball_speed)
        ball.reset(paddle.rect)
        ball.vel_y = 0
        bricks = build_bricks()
        score = 0
        game_over = False
        game_started = False
        game_paused = False

        # Ввод имени игрока
        player_name, sound_enabled, exit_game = get_player_name(screen, font, big_font, highscore_manager)
        if exit_game:
            should_exit = True
            break  # Выходим из внешнего цикла

        lives_left = MAX_LIVES

        # Запускаем музыку после ввода имени (если звук включен)
        if sound_enabled:
            try:
                pygame.mixer.music.play(-1)  # Цикличное воспроизведение фоновой музыки
            except pygame.error:
                # Не выводим в exe файле
                if not getattr(sys, "frozen", False):
                    print("Не удалось запустить фоновую музыку")

        # Отсчет времени игры
        game_start_time = time.time()

        # Отслеживание тройного нажатия "1" для немедленной победы
        key_1_press_count = 0
        key_1_last_press_time = 0.0
        KEY_1_RESET_TIME = 2.0  # Время в секундах для сброса счетчика
        
        # Флаг для пропуска обработки кадра после перезапуска
        skip_frame_processing = False
        
        # Отслеживание состояния клавиш для плавного управления платформой
        left_key_pressed = False
        right_key_pressed = False

        while running:
            
            # КРИТИЧНО: Обработка событий должна быть первой и всегда выполняться
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    # QUIT всегда закрывает приложение немедленно
                    running = False
                    should_exit = True
                    break  # Выходим из игрового цикла
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # ESC всегда закрывает приложение немедленно
                        running = False
                        should_exit = True
                        break  # Выходим из игрового цикла
                    elif event.key == pygame.K_m:
                        # Переключение всех звуков
                        if sound_enabled:
                            pygame.mixer.music.stop()
                            sound_enabled = False
                        else:
                            pygame.mixer.music.play(-1)
                            sound_enabled = True
                    elif event.key == pygame.K_SPACE:
                        # Выход из паузы при потере жизни - сразу продолжаем игру
                        if game_paused:
                            game_paused = False
                            # Если игра была запущена, сразу запускаем мяч
                            if game_started:
                                # Восстанавливаем скорость мяча в случайном направлении
                                ball.vel_x = random.choice([-ball.get_speed(), ball.get_speed()])
                                ball.vel_y = -ball.get_speed()
                    elif event.key == pygame.K_UP:
                        # Увеличение скорости мяча (работает даже во время паузы)
                        ball.increase_speed(settings_manager)
                    elif event.key == pygame.K_DOWN:
                        # Уменьшение скорости мяча (работает даже во время паузы)
                        ball.decrease_speed(settings_manager)
                    elif event.key == pygame.K_LEFT:
                        # Начало движения влево (не работает во время паузы)
                        if not game_paused:
                            left_key_pressed = True
                            if not game_over:
                                paddle.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        # Начало движения вправо (не работает во время паузы)
                        if not game_paused:
                            right_key_pressed = True
                            if not game_over:
                                paddle.move(1)
                    elif event.key == pygame.K_1 or event.key == ord('1'):
                        # Обработка тройного нажатия "1" для немедленной победы
                        current_time = time.time()
                        # Если прошло больше времени сброса, сбрасываем счетчик
                        if current_time - key_1_last_press_time > KEY_1_RESET_TIME:
                            key_1_press_count = 0
                        
                        key_1_press_count += 1
                        key_1_last_press_time = current_time
                        
                        # Если нажали три раза подряд
                        if key_1_press_count >= 3:
                            # Очищаем кирпичи для победы
                            bricks = []
                            key_1_press_count = 0  # Сбрасываем счетчик
                            if not getattr(sys, "frozen", False):
                                print(f"[CHEAT] Активирована немедленная победа")
                            
                            # Немедленно устанавливаем победу
                            game_over = True
                            game_time_seconds = int(time.time() - game_start_time)
                            
                            # Используем отдельный метод для показа заставки и результатов
                            try:
                                sound_enabled, restart_game, exit_game = trigger_instant_victory(
                                    screen,
                                    font,
                                    big_font,
                                    score,
                                    player_name,
                                    game_time_seconds,
                                    highscore_manager,
                                    settings_manager,
                                    ball,
                                )
                            except Exception as e:
                                if not getattr(sys, "frozen", False):
                                    print(f"[ERROR] Ошибка в trigger_instant_victory: {e}")
                                    import traceback
                                    traceback.print_exc()
                                # В случае ошибки показываем только экран результатов
                                sound_enabled, restart_game, exit_game = show_game_results(
                                    screen,
                                    font,
                                    big_font,
                                    score,
                                    player_name,
                                    game_time_seconds,
                                    highscore_manager,
                                    settings_manager,
                                    ball,
                                )
                            
                            # Обработка выхода или перезапуска
                            if exit_game:
                                pygame.quit()
                                return
                            
                            # Обработка перезапуска
                            if restart_game:
                                # Перезапускаем игру - ПОЛНЫЙ СБРОС СОСТОЯНИЯ
                                # Сначала очищаем все события клавиатуры, чтобы избежать "залипания" клавиш
                                pygame.event.clear(pygame.KEYDOWN)
                                pygame.event.clear(pygame.KEYUP)
                                
                                paddle = Paddle()
                                # Убеждаемся, что платформа в центре экрана
                                paddle.rect.centerx = SCREEN_WIDTH // 2
                                
                                ball = Ball()
                                ball_speed = settings_manager.get_ball_speed()
                                ball.set_speed(ball_speed)
                                ball.reset(paddle.rect)
                                ball.vel_y = 0
                                bricks = build_bricks()
                                score = 0
                                lives_left = MAX_LIVES
                                game_over = False
                                game_started = False
                                game_paused = False
                                # Сброс состояния клавиш платформы
                                left_key_pressed = False
                                right_key_pressed = False
                                # Перезапускаем отсчет времени игры
                                game_start_time = time.time()
                                # Устанавливаем флаг для пропуска обработки кадра
                                skip_frame_processing = True
                            else:
                                # Выходим из игры
                                running = False
                                should_exit = True
                                break
                elif event.type == pygame.KEYUP:
                    # Обработка отпускания клавиш для платформы
                    if event.key == pygame.K_LEFT:
                        left_key_pressed = False
                    elif event.key == pygame.K_RIGHT:
                        right_key_pressed = False
            
            # Пропускаем обработку кадра после перезапуска
            if skip_frame_processing:
                skip_frame_processing = False
                # Убеждаемся, что платформа в центре экрана после перезапуска
                paddle.rect.centerx = SCREEN_WIDTH // 2
                # Продолжаем цикл для отрисовки нового состояния
                continue
            
            keys = pygame.key.get_pressed()
            
            # Позиционируем мяч на платформе если игра не запущена или на паузе
            if not game_started and not game_paused:
                ball.rect.center = paddle.rect.midtop
                ball.rect.y -= BALL_SIZE
                # Игнорируем Enter при проверке старта игры (чтобы избежать случайного старта)
                if keys[pygame.K_LEFT] and not keys[pygame.K_RETURN]:
                    game_started = True
                    ball.vel_x = -ball.get_speed()
                    ball.vel_y = -ball.get_speed()
                elif keys[pygame.K_RIGHT] and not keys[pygame.K_RETURN]:
                    game_started = True
                    ball.vel_x = ball.get_speed()
                    ball.vel_y = -ball.get_speed()
            elif game_paused:
                # Во время паузы мяч должен быть на платформе
                ball.rect.center = paddle.rect.midtop
                ball.rect.y -= BALL_SIZE
            # Обработка перезапуска после окончания игры (только для ручного режима)
            if game_over and keys[pygame.K_r]:
                # В ручном режиме R перезапускает игру
                # Сброс состояния игры
                paddle = Paddle()
                ball = Ball()
                ball_speed = settings_manager.get_ball_speed()
                ball.set_speed(ball_speed)
                ball.reset(paddle.rect)
                ball.vel_y = 0
                bricks = build_bricks()
                score = 0
                lives_left = MAX_LIVES
                game_over = False
                game_started = False
                # Сброс состояния клавиш платформы
                left_key_pressed = False
                right_key_pressed = False

            if not game_over and not game_paused:
                # Ручное управление платформой - плавное движение каждый кадр
                if left_key_pressed:
                    paddle.move(-1)
                elif right_key_pressed:
                    paddle.move(1)

                if game_started:
                    # КРИТИЧНО: Проверяем отскок от потолка БЕЗ попадания в кубики ПЕРЕД обновлением мяча
                    # Это позволяет отследить отбитие в пустоту
                    ball_was_at_top = ball.rect.top <= 0 and ball.vel_y < 0
                    
                    # Обычное обновление мяча (непрерывная проверка столкновений встроена в update)
                    try:
                        ball.update()
                    except Exception as e:
                        if not getattr(sys, "frozen", False):
                            print(f"[ERROR] Ошибка в ball.update(): {e}")
                            import traceback
                            traceback.print_exc()
                        raise
                    
                    # КРИТИЧНО: Проверяем, не попал ли мяч обратно в платформу после ball.update()
                    # Это может произойти, если мяч был установлен слишком близко к платформе
                    # НО: не обрабатываем, если мяч только что отскочил (предотвращаем ложные срабатывания)
                    just_bounced = getattr(ball, '_just_bounced', False)
                    # Сбрасываем флаг, если мяч уже далеко от платформы
                    if just_bounced and ball.rect.bottom < paddle.rect.top - 20:
                        ball._just_bounced = False
                    
                    if (ball.rect.colliderect(paddle.rect) and ball.vel_y > 0 and not just_bounced):
                        logger.debug("[PADDLE COLLISION] Мяч попал обратно в платформу после update, исправляем позицию")
                        # Мяч попал обратно в платформу - принудительно перемещаем его выше
                        ball_radius = BALL_SIZE // 2
                        min_distance = abs(ball.vel_y) + 15  # Скорость + запас
                        ball.rect.centery = paddle.rect.top - ball_radius - min_distance
                        # Убеждаемся, что мяч движется вверх
                        if ball.vel_y >= 0:
                            ball.vel_y = -ball.get_speed()
                        # Устанавливаем флаг отскока
                        ball._just_bounced = True
                    
                    # КРИТИЧНО: Защита от vel_y == 0 во время игры (кроме начального состояния)
                    # Если мяч не двигается по вертикали и игра запущена - это ошибка
                    if game_started and ball.vel_y == 0:
                        # Мяч застрял с нулевой скоростью - принудительно запускаем его
                        ball.vel_y = -ball.get_speed()
                        # Логируем для диагностики
                    
                    # КРИТИЧНО: После обновления проверяем, отскочил ли мяч от потолка
                    # КРИТИЧНО: Проверяем столкновение ТОЛЬКО с верхней поверхностью платформы
                    # ВАЖНО: Проверка столкновения должна быть ДО проверки потери мяча!
                    # Мяч может быть отбит только верхней поверхностью платформы
                    # Если мяч попадает на боковую сторону - это потеря мяча
                    
                    # КРИТИЧНО: Проверяем столкновение ТОЛЬКО с верхней поверхностью платформы
                    # Верхняя поверхность: мяч должен быть по горизонтали в пределах платформы
                    # и нижняя часть мяча должна касаться верхней части платформы
                    # Боковое столкновение: мяч касается боковой стороны платформы (левой или правой)
                    
                    # Проверяем, попадает ли мяч в верхнюю поверхность платформы
                    # Условия для верхней поверхности:
                    # 1. Мяч движется вниз (vel_y > 0)
                    # 2. Центр мяча по горизонтали в пределах платформы (с небольшим запасом)
                    # 3. Нижняя часть мяча касается верхней части платформы
                    # 4. Мяч НЕ находится слишком глубоко внутри платформы (не боковой удар)
                    try:
                        # КРИТИЧНО: Проверяем, не отскочил ли мяч только что (предотвращаем повторную обработку)
                        just_bounced = getattr(ball, '_just_bounced', False)
                        
                        # Логируем состояние для диагностики
                        collides = ball.rect.colliderect(paddle.rect)
                        if collides and ball.vel_y > 0:
                            logger.debug(
                                f"[PADDLE COLLISION] Мяч касается платформы: "
                                f"ball.bottom={ball.rect.bottom}, paddle.top={paddle.rect.top}, "
                                f"ball.top={ball.rect.top}, ball.centerx={ball.rect.centerx}, "
                                f"paddle.left={paddle.rect.left}, paddle.right={paddle.rect.right}, "
                                f"vel_y={ball.vel_y}, just_bounced={just_bounced}"
                            )
                        
                        # Если мяч только что отскочил, не обрабатываем столкновение
                        if just_bounced:
                            ball_hits_paddle_top = False
                            if collides:
                                logger.debug("[PADDLE COLLISION] Мяч только что отскочил, пропускаем обработку")
                        else:
                            # Упрощенная логика: если мяч касается платформы, движется вниз, 
                            # и центр мяча по горизонтали в пределах платформы - это отскок от верха
                            ball_hits_paddle_top = (
                                ball.rect.colliderect(paddle.rect) 
                                and ball.vel_y > 0  # Мяч движется вниз
                                and paddle.rect.left <= ball.rect.centerx <= paddle.rect.right  # Центр мяча в пределах платформы
                            )
                            
                            if ball_hits_paddle_top:
                                logger.debug("[PADDLE COLLISION] Определено столкновение с верхней поверхностью платформы")
                    except Exception as e:
                        logger.error(f"[ERROR] Ошибка в вычислении ball_hits_paddle_top: {e}", exc_info=True)
                        raise
                    
                    # Проверяем боковое столкновение - это потеря мяча
                    # Боковое столкновение: мяч касается платформы, но НЕ попадает в верхнюю поверхность
                    # Это происходит, когда мяч касается левой или правой стороны платформы
                    try:
                        ball_hits_paddle_side = (
                            ball.rect.colliderect(paddle.rect)
                            and ball.vel_y > 0
                            and not ball_hits_paddle_top  # Не верхняя поверхность
                            and (
                                # Мяч касается левой стороны платформы (центр мяча слева от платформы)
                                ball.rect.centerx < paddle.rect.left
                                or
                                # Мяч касается правой стороны платформы (центр мяча справа от платформы)
                                ball.rect.centerx > paddle.rect.right
                            )
                        )
                        
                        if ball_hits_paddle_side:
                            logger.debug(
                                f"[PADDLE COLLISION] Боковое столкновение! "
                                f"ball.centerx={ball.rect.centerx}, paddle.left={paddle.rect.left}, "
                                f"paddle.right={paddle.rect.right}"
                            )
                    except Exception as e:
                        logger.error(f"[ERROR] Ошибка в вычислении ball_hits_paddle_side: {e}", exc_info=True)
                        raise
                    
                    if ball_hits_paddle_side:
                        # Мяч попал на боковую сторону платформы - это потеря мяча
                        lives_left -= 1
                        if lives_left > 0:
                            # КРИТИЧНО: Правильно сбрасываем мяч после бокового удара
                            # Сначала сбрасываем позицию и скорость
                            ball.reset(paddle.rect)
                            # КРИТИЧНО: Принудительно устанавливаем мяч ВЫШЕ платформы, чтобы избежать прилипания
                            ball_radius = BALL_SIZE // 2
                            ball.rect.centery = paddle.rect.top - ball_radius - 5  # Мяч должен быть минимум на 5 пикселей выше платформы
                            # КРИТИЧНО: Убеждаемся, что мяч не находится внутри платформы
                            if ball.rect.colliderect(paddle.rect):
                                # Если мяч все еще внутри платформы, перемещаем его еще выше
                                ball.rect.centery = paddle.rect.top - ball_radius - 15
                            # КРИТИЧНО: После бокового удара мяч потерян, но не устанавливаем vel_y = 0
                            # Вместо этого мяч будет обработан в логике потери жизни ниже
                            # КРИТИЧНО: Сбрасываем все трекеры после бокового удара
                            # Ставим игру на паузу (сохраняем game_started = True для продолжения после паузы)
                            game_paused = True
                            ball.vel_y = 0
                        else:
                            game_over = True
                            game_time_seconds = int(time.time() - game_start_time)
                            
                            # Показываем экран результатов
                            sound_enabled, restart_game, exit_game = show_game_results(
                                screen,
                                font,
                                big_font,
                                score,
                                player_name,
                                game_time_seconds,
                                highscore_manager,
                                settings_manager,
                                ball,
                            )

                            # Если игрок хочет выйти из игры
                            if exit_game:
                                pygame.quit()
                                return

                            # Обработка перезапуска
                            if restart_game:
                                # Перезапускаем игру - ПОЛНЫЙ СБРОС СОСТОЯНИЯ
                                paddle = Paddle()
                                ball = Ball()
                                ball_speed = settings_manager.get_ball_speed()
                                ball.set_speed(ball_speed)
                                ball.reset(paddle.rect)
                                ball.vel_y = 0
                                bricks = build_bricks()
                                score = 0
                                lives_left = MAX_LIVES
                                game_over = False
                                game_started = False
                                game_paused = False
                                # Перезапускаем отсчет времени игры
                                game_start_time = time.time()
                                # Устанавливаем флаг для пропуска обработки кадра
                                skip_frame_processing = True
                            else:
                                # Выходим из игры
                                running = False
                                should_exit = True
                                break
                        
                        continue  # Пропускаем проверку верхней поверхности после бокового удара
                    
                    # КРИТИЧНО: Проверяем, что мяч не "прилип" к платформе
                    # Если мяч находится слишком близко к платформе и не движется вниз - это ошибка
                    # Это может произойти после бокового удара или других ошибок координат
                    # Улучшенная проверка: мяч считается "прилипшим", если он внутри платформы или слишком близко
                    try:
                        # КРИТИЧНО: Прилипание определяется только если мяч ВНУТРИ платформы и НЕ движется
                        # Не проверяем прилипание, если мяч просто находится над платформой и движется вверх - это нормально
                        # КРИТИЧНО: Прилипание определяется только если мяч ВНУТРИ платформы и НЕ движется
                        # НО: не проверяем прилипание, если игра только что запущена (game_started=True, но мяч еще не двигался)
                        ball_stuck = (
                            ball.rect.colliderect(paddle.rect)  # Мяч ВНУТРИ платформы (пересекается с ней)
                            and ball.vel_y == 0  # КРИТИЧНО: Мяч неподвижен по вертикали (vel_y == 0)
                            and not ball_hits_paddle_top  # Не обрабатываем, если это нормальный отскок
                            and game_started  # КРИТИЧНО: Игра должна быть запущена (не начальное состояние ожидания)
                        )
                    except Exception as e:
                        if not getattr(sys, "frozen", False):
                            print(f"[ERROR] Ошибка в вычислении ball_stuck: {e}")
                            import traceback
                            traceback.print_exc()
                        ball_stuck = False
                    
                    if ball_stuck:
                        # Мяч "прилип" к платформе - принудительно перемещаем его выше
                        ball_radius = BALL_SIZE // 2
                        # КРИТИЧНО: Перемещаем мяч ВЫШЕ платформы, используя centerx/centery для согласованности
                        ball.rect.centery = paddle.rect.top - ball_radius - 15  # Увеличиваем расстояние для надежности
                        # КРИТИЧНО: Убеждаемся, что мяч не находится внутри платформы
                        if ball.rect.colliderect(paddle.rect):
                            # Если мяч все еще внутри платформы, перемещаем его еще выше
                            ball.rect.centery = paddle.rect.top - ball_radius - 25
                        # Устанавливаем скорость вверх, чтобы мяч оторвался
                        if ball.vel_y <= 0:
                            ball.vel_y = -ball.get_speed()
                        # Также устанавливаем горизонтальную скорость, чтобы мяч не оставался на месте
                        if abs(ball.vel_x) < 2:
                            ball.vel_x = random.choice([-ball.get_speed(), ball.get_speed()])
                        # КРИТИЧНО: Убеждаемся, что координаты согласованы (используем только centerx/centery)
                        # Не используем x/y напрямую, чтобы избежать конфликтов координат
                        
                        continue  # Пропускаем обработку отскока, так как мяч уже перемещен
                    
                    if ball_hits_paddle_top:
                        logger.debug("[PADDLE COLLISION] Обрабатываем отскок от верхней поверхности платформы")
                        # КРИТИЧНО: Сначала вычисляем и устанавливаем скорости, ПОТОМ корректируем позицию
                        # Это важно, чтобы мяч начал двигаться в правильном направлении ДО корректировки позиции
                        
                        # Вычисляем точное смещение от центра платформы
                        paddle_center = paddle.rect.centerx
                        ball_center = ball.rect.centerx
                        offset = (ball_center - paddle_center) / (paddle.rect.width / 2)

                        # Ограничиваем offset в диапазоне [-1, 1]
                        offset = max(-1.0, min(1.0, offset))

                        # ✅ ДОБАВЛЕНО: Логирование фактической и предсказанной позиций при успешном отскоке
                        # Устанавливаем новые скорости ПЕРВЫМ ДЕЛОМ
                        ball.bounce_vertical()
                        # КРИТИЧНО: Убеждаемся, что мяч движется вверх (vel_y < 0)
                        if ball.vel_y >= 0:
                            ball.vel_y = -ball.get_speed()
                        ball.vel_x = int(offset * ball.get_speed())
                        
                        # ТЕПЕРЬ корректируем позицию мяча, чтобы он был выше платформы
                        # Используем centery для согласованности с методом update()
                        ball_radius = BALL_SIZE // 2
                        # КРИТИЧНО: Устанавливаем мяч достаточно далеко от платформы
                        # Расстояние должно быть больше скорости мяча, чтобы в следующем кадре мяч не попал обратно
                        # Минимум: скорость мяча + запас 10 пикселей
                        min_distance = abs(ball.vel_y) + 10  # Скорость + запас
                        ball.rect.centery = paddle.rect.top - ball_radius - min_distance
                        
                        # КРИТИЧНО: Убеждаемся, что мяч не находится внутри платформы
                        if ball.rect.colliderect(paddle.rect):
                            # Если мяч все еще внутри платформы, перемещаем его еще выше
                            ball.rect.centery = paddle.rect.top - ball_radius - (min_distance + 10)
                        
                        # КРИТИЧНО: Убеждаемся, что нижняя часть мяча выше верхней части платформы
                        if ball.rect.bottom >= paddle.rect.top:
                            ball.rect.centery = paddle.rect.top - ball_radius - (min_distance + 5)
                        
                        # КРИТИЧНО: Устанавливаем флаг, что мяч только что отскочил
                        # Это предотвратит повторную обработку столкновения в следующем кадре
                        ball._just_bounced = True

                        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Предотвращение зацикливания
                        # Если offset слишком мал, принудительно устанавливаем значительное горизонтальное движение
                        min_horizontal_speed = max(
                            2, ball.get_speed() // 2
                        )  # Минимум 2 пикселя или половина скорости
                        if abs(ball.vel_x) < min_horizontal_speed:
                            # Принудительно устанавливаем направление в сторону от текущего положения
                            if ball.rect.centerx < SCREEN_WIDTH // 2:
                                ball.vel_x = min_horizontal_speed  # Двигаемся вправо
                            else:
                                ball.vel_x = -min_horizontal_speed  # Двигаемся влево

                            # Добавляем небольшую случайность для разнообразия
                            ball.vel_x += random.choice([-1, 0, 1])

                        # Дополнительная защита от зацикливания - проверяем, не была ли предыдущая скорость слишком малой
                        # Если предыдущая горизонтальная скорость была очень малой, а новая тоже
                        if abs(ball._last_vel_x) <= 1 and abs(ball.vel_x) <= 1:
                            # Принудительно меняем направление
                            ball.vel_x = random.choice(
                                [-min_horizontal_speed, min_horizontal_speed]
                            )

                        # Сохраняем текущую скорость для следующей проверки
                        ball._last_vel_x = ball.vel_x

                        # Ограничиваем горизонтальную скорость (но оставляем место для мин. скорости)
                        max_horizontal = ball.get_speed()
                        ball.vel_x = max(
                            -max_horizontal, min(max_horizontal, ball.vel_x)
                        )
                        
                        # КРИТИЧНО: Финальная проверка - убеждаемся, что мяч находится выше платформы и движется вверх
                        # Проверяем несколько раз, чтобы гарантировать, что мяч не пересекается с платформой
                        max_attempts = 5
                        for attempt in range(max_attempts):
                            if ball.rect.colliderect(paddle.rect) or ball.rect.bottom >= paddle.rect.top:
                                # Если мяч все еще пересекается с платформой, перемещаем его еще выше
                                ball.rect.centery = paddle.rect.top - ball_radius - (25 + attempt * 5)
                            else:
                                break
                        
                        # КРИТИЧНО: Убеждаемся, что мяч движется вверх с достаточной скоростью
                        # НИКОГДА не допускаем vel_y == 0 после отскока (кроме начального состояния)
                        if ball.vel_y == 0:
                            # КРИТИЧНО: Если vel_y == 0, это ошибка - устанавливаем скорость вверх
                            ball.vel_y = -ball.get_speed()
                        elif ball.vel_y >= 0:
                            ball.vel_y = -ball.get_speed()
                        # Дополнительная проверка: если скорость слишком мала, увеличиваем её
                        if abs(ball.vel_y) < ball.get_speed():
                            ball.vel_y = -ball.get_speed()
                        
                        # КРИТИЧНО: Сбрасываем флаг отскока через несколько кадров
                        # Это позволит обрабатывать новые столкновения, но предотвратит повторную обработку сразу после отскока
                        # Сбрасываем флаг, если мяч уже достаточно далеко от платформы
                        if ball.rect.bottom < paddle.rect.top - 20:
                            ball._just_bounced = False
                            logger.debug("[PADDLE COLLISION] Флаг just_bounced сброшен, мяч далеко от платформы")

                        # Play paddle bounce sound if sound is enabled
                        if sound_enabled and paddle_bounce_sound:
                            paddle_bounce_sound.play()

                    # КРИТИЧНО: Проверяем потерю мяча ПОСЛЕ проверки столкновения с платформой
                    # Если мяч ниже верхней границы платформы И не было столкновения - он потерян
                    if ball.rect.bottom > paddle.rect.top and not ball_hits_paddle_top:
                        # Мяч ниже верхней границы платформы и не отскочил - он потерян
                        lives_left -= 1
                        if lives_left > 0:
                            ball.reset(paddle.rect)
                            ball.vel_y = 0
                            # Ставим игру на паузу (сохраняем game_started = True для продолжения после паузы)
                            game_paused = True
                        else:
                            game_over = True
                            # Рассчитываем время игры и сохраняем результат
                            game_time_seconds = int(time.time() - game_start_time)

                            # Показываем экран результатов
                            sound_enabled, restart_game, exit_game = show_game_results(
                                screen,
                                font,
                                big_font,
                                score,
                                player_name,
                                game_time_seconds,
                                highscore_manager,
                                settings_manager,
                                ball,
                            )

                            # Если игрок хочет выйти из игры
                            if exit_game:
                                pygame.quit()
                                return

                            # Обработка перезапуска
                            if restart_game:
                                # Перезапускаем игру - ПОЛНЫЙ СБРОС СОСТОЯНИЯ
                                paddle = Paddle()
                                ball = Ball()
                                ball_speed = settings_manager.get_ball_speed()
                                ball.set_speed(ball_speed)
                                ball.reset(paddle.rect)
                                ball.vel_y = 0
                                bricks = build_bricks()
                                score = 0
                                lives_left = MAX_LIVES
                                game_over = False
                                game_started = False
                                game_paused = False
                                # Перезапускаем отсчет времени игры
                                game_start_time = time.time()
                                # Устанавливаем флаг для пропуска обработки кадра
                                skip_frame_processing = True
                            else:
                                # Выходим из игры
                                running = False
                                should_exit = True
                                break
                        continue  # Пропускаем остальную обработку кадра

                    # Оптимизация: проверяем столкновения только если есть кирпичи
                    # и мяч находится в области кирпичей (выше зоны разделения)
                    hit_index = -1
                    if bricks and ball.rect.bottom <= SEPARATION_ZONE_TOP + 50:
                        try:
                            hit_index = ball.rect.collidelist(bricks)
                        except Exception as e:
                            if not getattr(sys, "frozen", False):
                                print(f"[ERROR] Ошибка в collidelist: {e}")
                                import traceback
                                traceback.print_exc()
                            hit_index = -1
                    if hit_index != -1:
                        ball.bounce_vertical()
                        destroyed_brick = bricks.pop(hit_index)
                        score += 1

                        # Play random brick hit sound if sound is enabled
                        if sound_enabled and brick_hit_sounds:
                            brick_hit_sounds[
                                random.randint(0, len(brick_hit_sounds) - 1)
                            ].play()
                    
                    # Проверяем победу (все кубики сбиты)
                    if not bricks:
                        game_over = True
                        game_time_seconds = int(time.time() - game_start_time)
                        
                        logger.info("=== ПОБЕДА! Все кирпичи уничтожены ===")
                        
                        # Используем trigger_instant_victory для показа анимации и результатов
                        try:
                            sound_enabled, restart_game, exit_game = trigger_instant_victory(
                                screen,
                                font,
                                big_font,
                                score,
                                player_name,
                                game_time_seconds,
                                highscore_manager,
                                settings_manager,
                                ball,
                            )
                        except Exception as e:
                            logger.error(f"Ошибка в trigger_instant_victory: {e}")
                            import traceback
                            logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
                            # В случае ошибки показываем только экран результатов
                            sound_enabled, restart_game, exit_game = show_game_results(
                                screen,
                                font,
                                big_font,
                                score,
                                player_name,
                                game_time_seconds,
                                highscore_manager,
                                settings_manager,
                                ball,
                            )

                        # Если игрок хочет выйти из игры
                        if exit_game:
                            pygame.quit()
                            return

                        # Обработка перезапуска
                        if restart_game:
                            # Перезапускаем игру - ПОЛНЫЙ СБРОС СОСТОЯНИЯ
                            paddle = Paddle()
                            ball = Ball()
                            ball_speed = settings_manager.get_ball_speed()
                            ball.set_speed(ball_speed)
                            ball.reset(paddle.rect)
                            ball.vel_y = 0
                            bricks = build_bricks()
                            score = 0
                            lives_left = MAX_LIVES
                            game_over = False
                            game_started = False
                            game_paused = False
                            # Перезапускаем отсчет времени игры
                            game_start_time = time.time()
                            # Устанавливаем флаг для пропуска обработки кадра
                            skip_frame_processing = True
                        else:
                            # Выходим из игры
                            running = False
                            should_exit = True
                            break
                        continue  # Пропускаем остальную обработку кадра

                    if ball.rect.bottom >= SCREEN_HEIGHT:
                        # Мяч за границей экрана - уменьшаем жизни
                        lives_left -= 1
                        if lives_left > 0:
                            # Ставим игру на паузу (сохраняем game_started = True для продолжения после паузы)
                            ball.reset(paddle.rect)
                            ball.vel_y = 0
                            game_paused = True
                        elif lives_left <= 0:
                            game_over = True
                            # Рассчитываем время игры и сохраняем результат
                            game_time_seconds = int(time.time() - game_start_time)

                            # Показываем экран результатов
                            sound_enabled, restart_game, exit_game = show_game_results(
                                screen,
                                font,
                                big_font,
                                score,
                                player_name,
                                game_time_seconds,
                                highscore_manager,
                                settings_manager,
                                ball,
                            )

                            # Если игрок хочет выйти из игры
                            if exit_game:
                                pygame.quit()
                                return

                            # Обработка перезапуска
                            if restart_game:
                                # Перезапускаем игру - ПОЛНЫЙ СБРОС СОСТОЯНИЯ
                                paddle = Paddle()
                                ball = Ball()
                                ball_speed = settings_manager.get_ball_speed()
                                ball.set_speed(ball_speed)
                                ball.reset(paddle.rect)
                                ball.vel_y = 0
                                bricks = build_bricks()
                                score = 0
                                lives_left = MAX_LIVES
                                game_over = False
                                game_started = False
                                game_paused = False
                                # Перезапускаем отсчет времени игры
                                game_start_time = time.time()
                                # Устанавливаем флаг для пропуска обработки кадра
                                skip_frame_processing = True
                            else:
                                # Выходим из игры
                                running = False
                                should_exit = True
                                break
                        else:
                            ball.reset(paddle.rect)
                            ball.vel_y = 0
                            game_started = False

            # Отрисовка игры
            screen.fill((10, 10, 30))  # Темно-синий фон
            draw_bricks(screen, bricks)  # Отрисовка кубиков
            # Отрисовка платформы с цветными секциями для подсказки направления отскока
            left_rect = pygame.Rect(
                paddle.rect.x, paddle.rect.y, paddle.rect.width // 3, paddle.rect.height
            )
            pygame.draw.rect(
                screen, (255, 0, 0), left_rect
            )  # Красный для отскока влево
            mid_rect = pygame.Rect(
                paddle.rect.x + paddle.rect.width // 3,
                paddle.rect.y,
                paddle.rect.width // 3,
                paddle.rect.height,
            )
            pygame.draw.rect(
                screen, (240, 240, 240), mid_rect
            )  # Белый для прямого отскока
            right_rect = pygame.Rect(
                paddle.rect.x + 2 * paddle.rect.width // 3,
                paddle.rect.y,
                paddle.rect.width - 2 * paddle.rect.width // 3,
                paddle.rect.height,
            )
            pygame.draw.rect(
                screen, (0, 0, 255), right_rect
            )  # Синий для отскока вправо
            pygame.draw.ellipse(screen, (230, 90, 90), ball.rect)

            draw_hud(
                screen,
                score,
                lives_left,
                font,
                ball,
            )

            if not game_started and not game_paused:
                draw_start_hint(screen, big_font)
            
            if game_paused:
                draw_pause_hint(screen, big_font)

            pygame.display.flip()
            clock.tick(FPS)
            
            # Проверяем флаг выхода из игры
            if should_exit:
                break  # Выходим из игрового цикла

        # Проверяем флаг выхода из игры перед продолжением
        if should_exit:
            pygame.quit()
            sys.exit(0)  # Полный выход из процесса
        
        # Продолжаем внешний цикл для возврата к вводу имени
        continue
    
    # Если мы вышли из внешнего цикла (через break), закрываем игру
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
