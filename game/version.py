"""
Централизованное управление версией проекта Арканоид

Этот файл является единственным источником истины для версии проекта.
Все остальные файлы должны импортировать версию отсюда.

Версия автоматически увеличивается при каждом запуске (увеличивается BUILD номер).
"""

import os
import re
from pathlib import Path
from typing import Tuple

# Путь к текущему файлу
_VERSION_FILE: Path = Path(__file__)

# Флаг для предотвращения повторного увеличения версии в одной сессии Python
_VERSION_LOADED: bool = False

# Версия в формате X.Y.ZZZZ
# X - мажорная версия (революционные изменения)
# Y - минорная версия (новые функции, исправления UI)
# ZZZZ - 4-значный индекс сборки (увеличивается автоматически при каждом запуске)

# Начальные значения (будут обновлены при загрузке)
VERSION_MAJOR: int = 2
VERSION_MINOR: int = 3
VERSION_BUILD = 169
VERSION: str = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD:04d}"
VERSION_FULL: str = VERSION
VERSION_BUILD_STRING: str = VERSION


def _load_version_from_file() -> None:
    """Загружает версию из файла и увеличивает BUILD номер"""
    global VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD, VERSION, VERSION_FULL, VERSION_BUILD_STRING, _VERSION_LOADED
    
    # Проверяем переменную окружения для пропуска увеличения версии
    import os
    skip_increment = os.environ.get("SKIP_VERSION_INCREMENT") == "1"
    
    # Предотвращаем повторное увеличение версии в одной сессии
    if _VERSION_LOADED:
        import sys
        if not getattr(sys, "frozen", False):
            print(f"[VERSION] Версия уже загружена в этой сессии, используем текущую: {VERSION}")
        return
    
    _VERSION_LOADED = True

    try:
        # Читаем текущий файл
        import sys
        if not getattr(sys, "frozen", False):
            if not skip_increment:
                print(f"[VERSION] Загружаю версию из файла: {_VERSION_FILE}")
        
        with open(_VERSION_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Извлекаем текущие значения версии
        # Поддерживаем оба формата: "VERSION_MAJOR = 2" и "VERSION_MAJOR: int = 2"
        major_match = re.search(r"VERSION_MAJOR\s*:?\s*(?:int\s*)?=\s*(\d+)", content)
        minor_match = re.search(r"VERSION_MINOR\s*:?\s*(?:int\s*)?=\s*(\d+)", content)
        build_match = re.search(r"VERSION_BUILD\s*:?\s*(?:int\s*)?=\s*(\d+)", content)

        # Логируем найденные значения для диагностики
        import sys
        if not getattr(sys, "frozen", False):
            print(f"[VERSION] Найдено: MAJOR={major_match.group(1) if major_match else 'НЕТ'}, MINOR={minor_match.group(1) if minor_match else 'НЕТ'}, BUILD={build_match.group(1) if build_match else 'НЕТ'}")

        if major_match and minor_match and build_match:
            old_build = int(build_match.group(1))
            VERSION_MAJOR = int(major_match.group(1))
            VERSION_MINOR = int(minor_match.group(1))
            VERSION_BUILD = old_build

            # Увеличиваем BUILD номер только если не установлен SKIP_VERSION_INCREMENT
            if not skip_increment:
                VERSION_BUILD += 1
                # Обновляем VERSION и VERSION_BUILD_STRING
                VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD:04d}"
                VERSION_BUILD_STRING = VERSION
                VERSION_FULL = VERSION

                # Логируем увеличение версии (только в режиме разработки)
                if not getattr(sys, "frozen", False):
                    print(f"[VERSION] Увеличиваю версию: {VERSION_MAJOR}.{VERSION_MINOR}.{old_build:04d} -> {VERSION}")
            else:
                # Не увеличиваем версию, просто используем текущую (версия уже была увеличена в create_msi.py)
                VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD:04d}"
                VERSION_BUILD_STRING = VERSION
                VERSION_FULL = VERSION

            # Обновляем файл с новой версией только если версия была увеличена
            if not skip_increment:
                # ВАЖНО: Обновляем ВСЕ вхождения VERSION_BUILD в файле
                # Поддерживаем оба формата: "VERSION_BUILD = 169" и "VERSION_BUILD = 169"
                content = re.sub(
                    r"VERSION_BUILD\s*:?\s*(?:int\s*)?=\s*\d+", f"VERSION_BUILD = {VERSION_BUILD}", content
                )
                # Обновляем VERSION, VERSION_BUILD_STRING, VERSION_FULL с поддержкой формата с типом
                content = re.sub(r'VERSION\s*:?\s*(?:str\s*)?=\s*"[^"]+"', f'VERSION = "2.3.0166"', content)
                content = re.sub(
                    r'VERSION_BUILD_STRING\s*:?\s*(?:str\s*)?=\s*"[^"]+"',
                    f'VERSION_BUILD_STRING = "2.3.0166"',
                    content,
                )
                content = re.sub(
                    r'VERSION_FULL\s*:?\s*(?:str\s*)?=\s*"[^"]+"', f'VERSION_FULL = "2.3.0166"', content
                )

                # Сохраняем обновленный файл
                with open(_VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            # Если не удалось распарсить, используем значения по умолчанию
            import sys
            if not getattr(sys, "frozen", False):
                print(f"[VERSION] ОШИБКА: Не удалось распарсить версию из файла! Использую значения по умолчанию.")
            VERSION_BUILD += 1
            VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD:04d}"
            VERSION_BUILD_STRING = VERSION
            VERSION_FULL = VERSION

    except Exception as e:
        # В случае ошибки используем значения по умолчанию и увеличиваем BUILD
        VERSION_BUILD += 1
        VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD:04d}"
        VERSION_BUILD_STRING = VERSION
        VERSION_FULL = VERSION
        # Не прерываем выполнение, просто логируем ошибку
        import sys

        if not getattr(sys, "frozen", False):  # Не выводим в exe
            print(f"[WARNING] Не удалось обновить версию в файле: {e}")


# Автоматически загружаем и обновляем версию при импорте модуля
_load_version_from_file()


def get_version() -> str:
    """Возвращает текущую версию"""
    return VERSION


def get_version_tuple() -> Tuple[int, int, int]:
    """Возвращает версию как кортеж (major, minor, build)"""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD)


def get_version_string() -> str:
    """Возвращает версию как строку в формате X.Y.ZZZZ"""
    return VERSION_BUILD_STRING


def get_version_for_poetry() -> str:
    """Возвращает версию в формате Poetry (X.Y.Z, где Z = BUILD)"""
    return f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}"


def update_version_in_all_files() -> bool:
    """
    Обновляет версию во всех файлах проекта (pyproject.toml, create_installer.iss, README.MD).
    Вызывается при сборке для синхронизации версий.
    
    Returns:
        True если обновление прошло успешно, False в противном случае
    """
    import os
    from pathlib import Path
    
    try:
        # Получаем корень проекта (на уровень выше game/)
        version_file = Path(__file__)
        project_root = version_file.parent.parent
        
        current_version = get_version_string()
        poetry_version = get_version_for_poetry()
        
        # Обновляем pyproject.toml
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding='utf-8')
            # Обновляем версию в формате "version = "X.Y.Z"" только в секции [tool.poetry]
            # Используем более точный паттерн, чтобы не затронуть python_version и pythonVersion
            content = re.sub(
                r'^(\s*version\s*=\s*)"[^"]+"(\s*#.*Poetry.*)',
                f'\\1"{poetry_version}"\\2',
                content,
                flags=re.IGNORECASE | re.MULTILINE
            )
            # Если не нашли с комментарием, ищем просто version = в секции [tool.poetry]
            if f'version = "{poetry_version}"' not in content:
                content = re.sub(
                    r'(\[tool\.poetry\]\s*\n[^\[]*?version\s*=\s*)"[^"]+"',
                    f'\\1"{poetry_version}"',
                    content,
                    flags=re.IGNORECASE | re.DOTALL
                )
            # Обновляем комментарий с версией
            content = re.sub(
                r'# Poetry формат: X\.Y\.Z \(соответствует version\.py: VERSION_MAJOR=\d+, VERSION_MINOR=\d+, VERSION_BUILD=\d+\)',
                f'# Poetry формат: X.Y.Z (соответствует version.py: VERSION_MAJOR={VERSION_MAJOR}, VERSION_MINOR={VERSION_MINOR}, VERSION_BUILD={VERSION_BUILD})',
                content
            )
            pyproject_path.write_text(content, encoding='utf-8')
        
        # Обновляем create_installer.iss
        installer_iss_path = project_root / "scripts" / "create_installer.iss"
        if installer_iss_path.exists():
            content = installer_iss_path.read_text(encoding='utf-8')
            # Обновляем версию в формате #define MyAppVersion "X.Y.ZZZZ"
            content = re.sub(
                r'#define\s+MyAppVersion\s+"[^"]+"',
                f'#define MyAppVersion "{current_version}"',
                content
            )
            installer_iss_path.write_text(content, encoding='utf-8')
        
        # Обновляем README.MD в docs/документация/
        readme_path = project_root / "docs" / "документация" / "README.MD"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            # Обновляем badge версии
            content = re.sub(
                r'!\[Версия\]\(https://img\.shields\.io/badge/version-[^)]+\)',
                f'![Версия](https://img.shields.io/badge/version-{current_version}-blue.svg)',
                content
            )
            # Обновляем заголовок версии
            content = re.sub(
                r'### Версия \d+\.\d+\.\d+',
                f'### Версия {current_version}',
                content
            )
            readme_path.write_text(content, encoding='utf-8')
        
        return True
    except Exception as e:
        import sys
        if not getattr(sys, "frozen", False):
            print(f"[WARNING] Не удалось обновить версию во всех файлах: {e}")
        return False
