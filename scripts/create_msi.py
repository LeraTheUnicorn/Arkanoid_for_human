#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт автоматического создания MSI инсталлятора для игры Арканоид
Использует WiX Toolset для создания MSI файлов
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional

# Определяем корень проекта и директорию скриптов
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.dirname(os.path.abspath(__file__))


def check_wix_installation() -> bool:
    """Проверяет наличие WiX Toolset"""
    try:
        # Проверяем wix.exe
        result_wix = subprocess.run(
            ["wix", "--version"], capture_output=True, text=True
        )
        return result_wix.returncode == 0
    except FileNotFoundError:
        return False


def get_current_version() -> str:
    """
    Получает текущую версию из version.py и обновляет её во всех файлах.
    
    ВАЖНО: Версия автоматически увеличивается при импорте модуля version.py
    (функция _load_version_from_file вызывается при импорте).
    """
    try:
        sys.path.insert(0, project_root)
        # Импорт модуля version.py автоматически увеличивает BUILD номер
        from game.version import get_version_string, update_version_in_all_files
        
        # Получаем версию ПОСЛЕ автоматического увеличения
        current_version = get_version_string()
        
        # Обновляем версию во всех файлах проекта (pyproject.toml, create_installer.iss, README.MD)
        print("Обновляю версию проекта...")
        if update_version_in_all_files():
            print(f"✅ Версия обновлена во всех файлах: {current_version}")
        else:
            print("⚠️  Не удалось обновить версию во всех файлах")
        
        return current_version
    except Exception as e:
        print(f"Ошибка чтения версии из version.py: {e}")
        return "2.3.0000"


def get_publisher() -> str:
    """
    Возвращает имя издателя для MSI инсталлятора.
    Можно изменить это значение на ваше имя или название компании.
    Также можно задать через переменную окружения MSI_PUBLISHER.
    """
    # Проверяем переменную окружения
    publisher = os.environ.get("MSI_PUBLISHER", "LeraSoftware")
    return publisher


def get_publisher_url() -> str:
    """
    Возвращает URL издателя для MSI инсталлятора.
    Можно задать через переменную окружения MSI_PUBLISHER_URL.
    """
    return os.environ.get("MSI_PUBLISHER_URL", "https://github.com/developer/arkanoid")


def create_wix_files(version: str) -> Optional[Path]:
    """
    Создает файлы WiX для MSI сборки
    
    Args:
        version: Версия игры (должна быть получена один раз в начале процесса)
    """

    # Создаем директории для WiX внутри scripts/build/
    build_dir = os.path.join(scripts_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    wix_dir = Path(os.path.join(build_dir, "wix"))
    wix_dir.mkdir(exist_ok=True)

    # Ищем exe файл в разных местах
    exe_path = None
    possible_paths = [
        os.path.join(project_root, f"Arkanoid_v{version}.exe"),  # корень проекта
        os.path.join(
            project_root, "FINAL_RELEASE", f"Arkanoid_v{version}.exe"
        ),  # FINAL_RELEASE
        os.path.join(
            project_root, "dist", f"Arkanoid_v{version}.exe"
        ),  # dist (PyInstaller)
        os.path.join(
            scripts_dir, "build", "dist", f"Arkanoid_v{version}.exe"
        ),  # scripts/build/dist (PyInstaller)
    ]

    for path in possible_paths:
        print(f"Проверяю путь: {path}")
        if os.path.exists(path):
            exe_path = path
            print(f"Найден exe файл: {exe_path}")
            break

    if not exe_path:
        print(f"Ошибка: exe файл Arkanoid_v{version}.exe не найден!")
        print("Проверенные пути:")
        for path in possible_paths:
            print(f"  - {path} (существует: {os.path.exists(path)})")
        return None

    # Проверяем наличие дополнительных файлов
    readme_path = os.path.join(project_root, "README.md")
    readme_exists = os.path.exists(readme_path)
    
    # Получаем информацию об издателе
    publisher = get_publisher()
    publisher_url = get_publisher_url()
    
    # Формируем компоненты для README
    readme_component = f'<Component Id="ReadmeFile" Guid="77777777-7777-7777-7777-777777777777"><File Id="Readme" Source="{readme_path.replace(chr(92), chr(92)*2)}" /></Component>' if readme_exists else '<!-- README.md not found -->'
    readme_ref = '<ComponentRef Id="ReadmeFile" />' if readme_exists else '<!-- README.md not found -->'
    
    # Формируем компоненты для docs - включаем только README.MD из docs/документация/
    docs_readme_path = os.path.join(project_root, "docs", "документация", "README.MD")
    docs_readme_exists = os.path.exists(docs_readme_path)
    
    if docs_readme_exists:
        docs_component = f'<Component Id="DocsFiles" Guid="88888888-8888-8888-8888-888888888888" Directory="DocsFolder"><CreateFolder /><File Id="DocsReadme" Source="{docs_readme_path.replace(chr(92), chr(92)*2)}" /></Component>'
    else:
        docs_component = '<Component Id="DocsFiles" Guid="88888888-8888-8888-8888-888888888888" Directory="DocsFolder"><CreateFolder /></Component>'

    # Содержимое Product.wxs
    product_wxs = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs"
     xmlns:util="http://wixtoolset.org/schemas/v4/wxs/util">
  <Package Name="Игра Арканоид"
           Language="1049"
           Version="{version}.0"
           Manufacturer="{publisher}"
           UpgradeCode="12345678-1234-1234-1234-123456789012"
           Codepage="65001">

     <MediaTemplate EmbedCab="yes" />

     <Feature Id="ProductFeature"
              Title="Игра Арканоид"
              Level="1">
       <ComponentGroupRef Id="ProductComponents" />
       <ComponentRef Id="ApplicationShortcut" />
     </Feature>

     <StandardDirectory Id="LocalAppDataFolder">
       <Directory Id="GamesFolder" Name="Games">
         <Directory Id="INSTALLFOLDER" Name="Arkanoid">
           <Directory Id="DataFolder" Name="data">
           </Directory>
           <Directory Id="ResourcesFolder" Name="resources">
             <Directory Id="ResourcesAudioFolder" Name="audio">
             </Directory>
             <Directory Id="ResourcesImagesFolder" Name="images">
             </Directory>
           </Directory>
           <Directory Id="DocsFolder" Name="docs">
           </Directory>
           <Component Id="ProductComponents" Guid="11111111-1111-1111-1111-111111111111">
             <File Id="GameExecutable" Source="{exe_path.replace(chr(92), chr(92)*2)}" KeyPath="yes">
               <Shortcut Id="GameStartMenuShortcut"
                         Directory="ProgramMenuDir"
                         Name="Арканоид"
                         Description="Игра Арканоид"
                         WorkingDirectory="INSTALLFOLDER"
                         Icon="GameIcon" />
             </File>
           </Component>

           <Component Id="DataFiles" Guid="44444444-4444-4444-4444-444444444444" Directory="DataFolder">
             <CreateFolder />
             <File Id="HighscoresData" Source="{os.path.join(project_root, 'game', 'data', 'highscores.json').replace(chr(92), chr(92)*2)}" />
             <File Id="SettingsData" Source="{os.path.join(project_root, 'game', 'data', 'settings.json').replace(chr(92), chr(92)*2)}" />
           </Component>

           <Component Id="ResourcesAudioFiles" Guid="55555555-5555-5555-5555-555555555555" Directory="ResourcesAudioFolder">
             <CreateFolder />
             <File Id="AudioFile" Source="{os.path.join(project_root, 'resources', 'audio', 'Night_Prowler.ogg').replace(chr(92), chr(92)*2)}" />
           </Component>

           <Component Id="ResourcesImagesFiles" Guid="66666666-6666-6666-6666-666666666666" Directory="ResourcesImagesFolder">
             <CreateFolder />
             <File Id="ImageFile1" Source="{os.path.join(project_root, 'resources', 'images', 'd2.gif').replace(chr(92), chr(92)*2)}" />
           </Component>

           {readme_component}
           {docs_component}
         </Directory>
       </Directory>
     </StandardDirectory>

     <StandardDirectory Id="DesktopFolder">
       <Component Id="ApplicationShortcut" Guid="33333333-3333-3333-3333-333333333333">
         <Shortcut Id="DesktopApplicationShortcut"
                   Directory="DesktopFolder"
                   Name="Арканоид"
                   Description="Игра Арканоид"
                   WorkingDirectory="INSTALLFOLDER"
                   Target="[#GameExecutable]"
                   Icon="GameIcon" />
         <RegistryValue Root="HKCU"
                        Key="Software\\Arkanoid"
                        Name="installed"
                        Type="integer"
                        Value="1"
                        KeyPath="yes" />
       </Component>
     </StandardDirectory>

     <StandardDirectory Id="ProgramMenuFolder">
       <Directory Id="ProgramMenuDir" Name="Арканоид" />
     </StandardDirectory>

     <ComponentGroup Id="ProductComponents">
       <ComponentRef Id="ProductComponents" />
       <ComponentRef Id="DataFiles" />
       <ComponentRef Id="ResourcesAudioFiles" />
       <ComponentRef Id="ResourcesImagesFiles" />
       {readme_ref}
       <ComponentRef Id="DocsFiles" />
     </ComponentGroup>

     <Property Id="ARPPRODUCTICON" Value="GameIcon" />
     <Property Id="ARPPUBLISHER" Value="{publisher}" />
     <Property Id="ARPHELPLINK" Value="{publisher_url}" />
     <Property Id="ARPURLINFOABOUT" Value="{publisher_url}" />
     <Property Id="ARPCONTACT" Value="{publisher}" />
     <Property Id="ARPCOMMENTS" Value="Классическая игра Арканоид" />

   </Package>
</Wix>"""

    # Записываем Product.wxs
    with open(wix_dir / "Product.wxs", "w", encoding="utf-8") as f:
        f.write(product_wxs)

    # Создаем icon.wxi для иконки
    icon_wxi = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Fragment>
    <Icon Id="GameIcon" SourceFile="{os.path.join(project_root, 'resources', 'icon.ico').replace(chr(92), chr(92)*2)}" />
  </Fragment>
</Wix>"""

    with open(wix_dir / "icon.wxi", "w", encoding="utf-8") as f:
        f.write(icon_wxi)

    return wix_dir


def build_msi_with_version(version: str) -> bool:
    """
    Собирает MSI файл с помощью WiX.
    
    Args:
        version: Версия игры (должна быть получена один раз в начале процесса)
    """
    build_dir = os.path.join(scripts_dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    # Проверяем наличие exe файла с ТЕКУЩЕЙ версией
    exe_path = os.path.join(project_root, f"Arkanoid_v{version}.exe")
    final_release_path = os.path.join(
        project_root, "FINAL_RELEASE", f"Arkanoid_v{version}.exe"
    )
    
    # Проверяем, существует ли EXE с текущей версией
    exe_exists = os.path.exists(exe_path) or os.path.exists(final_release_path)
    
    # Если EXE не существует с текущей версией, пересобираем
    if not exe_exists:
        print(f"⚠️  Exe файл Arkanoid_v{version}.exe не найден.")
        print("📦 Пересобираю EXE с новой версией...")
        try:
            # Создаем exe файл с помощью build_exe.py
            # Устанавливаем переменную окружения, чтобы build_exe.py не увеличивал версию повторно
            env = os.environ.copy()
            env["SKIP_VERSION_INCREMENT"] = "1"  # Флаг для пропуска увеличения версии
            
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(project_root, "scripts", "build_exe.py"),
                ],
                check=True,
                cwd=project_root,
                env=env,
            )
            if result.returncode == 0:
                print("✅ Exe файл создан успешно!")
                # После сборки проверяем, какая версия EXE была создана
                # build_exe.py может создать EXE с другой версией, если версия увеличилась
                # Проверяем все возможные пути с разными версиями
                from game.version import get_version_string
                current_version_after_build = get_version_string()
                
                # Проверяем EXE с версией, которая была запрошена
                if os.path.exists(exe_path) or os.path.exists(final_release_path):
                    print(f"✅ Exe файл найден с версией {version}")
                # Проверяем EXE с версией после сборки (на случай, если версия изменилась)
                elif os.path.exists(os.path.join(project_root, f"Arkanoid_v{current_version_after_build}.exe")):
                    print(f"⚠️  Exe файл создан с версией {current_version_after_build} вместо {version}")
                    # Обновляем версию для использования
                    version = current_version_after_build
                    exe_path = os.path.join(project_root, f"Arkanoid_v{version}.exe")
                    final_release_path = os.path.join(project_root, "FINAL_RELEASE", f"Arkanoid_v{version}.exe")
                elif os.path.exists(os.path.join(project_root, "FINAL_RELEASE", f"Arkanoid_v{current_version_after_build}.exe")):
                    print(f"⚠️  Exe файл создан с версией {current_version_after_build} вместо {version}")
                    # Обновляем версию для использования
                    version = current_version_after_build
                    exe_path = os.path.join(project_root, f"Arkanoid_v{version}.exe")
                    final_release_path = os.path.join(project_root, "FINAL_RELEASE", f"Arkanoid_v{version}.exe")
                else:
                    print("⚠️  Предупреждение: EXE файл не найден после сборки")
            else:
                print("⚠️  Exe файл создан с ошибками")
        except Exception as e:
            print(f"❌ Ошибка создания exe файла: {e}")
            return False
    else:
        print(f"✅ Exe файл Arkanoid_v{version}.exe найден, используем его")

    print("Создаю WiX файлы...")
    # Передаем версию, чтобы не вызывать get_current_version() снова
    wix_dir = create_wix_files(version)

    if wix_dir is None:
        print("Ошибка: не удалось создать WiX файлы")
        return False

    print("Компилирую WiX исходники...")

    # Собираем MSI с помощью wix.exe
    msi_name = os.path.join(build_dir, f"Arkanoid_v{version}_Setup.msi")
    wix_cmd = [
        "wix",
        "build",
        "-arch",
        "x64",
        "-ext",
        "WixToolset.Util.wixext",
        "-o",
        msi_name,
        str(wix_dir / "Product.wxs"),
        str(wix_dir / "icon.wxi"),
    ]
    
    print(f"Выполняю команду: {' '.join(wix_cmd)}")
    print(f"Рабочая директория: {os.getcwd()}")
    print(f"WiX файлы находятся в: {wix_dir}")
    
    try:
        wix_result = subprocess.run(
            wix_cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            cwd=str(wix_dir.parent) if wix_dir else None
        )
    except FileNotFoundError:
        print("\n❌ Ошибка: WiX не найден в PATH!")
        print("Установите WiX Toolset v6.0 или новее с https://github.com/wixtoolset/wix/releases/")
        print("Добавьте WiX в PATH: C:\\Program Files\\WiX Toolset v6.0\\bin")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка при запуске WiX: {e}")
        import traceback
        traceback.print_exc()
        return False

    if wix_result.returncode != 0:
        print(f"\n❌ Ошибка сборки MSI (код возврата: {wix_result.returncode})")
        if wix_result.stderr:
            print(f"\nSTDERR:\n{wix_result.stderr}")
        if wix_result.stdout:
            print(f"\nSTDOUT:\n{wix_result.stdout}")
        if not wix_result.stderr and not wix_result.stdout:
            print("\n⚠️  WiX не вернул сообщение об ошибке. Проверьте:")
            print("  1. Установлен ли WiX Toolset v6.0 или новее")
            print("  2. Доступен ли WiX в PATH")
            print("  3. Корректны ли пути к файлам WiX")
            print(f"  4. Существуют ли файлы: {wix_dir / 'Product.wxs'}, {wix_dir / 'icon.wxi'}")
        return False

    print(f"MSI успешно создан: {msi_name}")

    # Копируем MSI в FINAL_RELEASE
    final_release_dir = os.path.join(project_root, "FINAL_RELEASE")
    os.makedirs(final_release_dir, exist_ok=True)
    final_msi_path = os.path.join(final_release_dir, f"Arkanoid_v{version}_Setup.msi")

    try:
        shutil.copy2(msi_name, final_msi_path)
        print(f"MSI скопирован в FINAL_RELEASE: {final_msi_path}")
    except Exception as e:
        print(f"Ошибка копирования MSI в FINAL_RELEASE: {e}")
        # Не возвращаем False, так как MSI уже создан успешно

    return True


def build_msi() -> bool:
    """
    Собирает MSI файл с помощью WiX.
    Обертка для обратной совместимости - получает версию и вызывает build_msi_with_version.
    """
    # Получаем версию ОДИН РАЗ в начале процесса
    # Это увеличит BUILD номер и обновит все файлы
    version = get_current_version()
    return build_msi_with_version(version)


def main() -> bool:
    print("=== Создание MSI инсталлятора для Arkanoid ===")

    if not check_wix_installation():
        print("WiX Toolset не найден!")
        print(
            "Установите WiX v6.0 или новее с https://github.com/wixtoolset/wix/releases/"
        )
        print("Добавьте WiX в PATH: C:\\Program Files\\WiX Toolset v6.0\\bin")
        return False

    # Получаем версию ОДИН РАЗ в начале, чтобы она увеличилась только один раз
    # И передаем её в build_msi, чтобы не вызывать get_current_version() повторно
    print("📌 Получаю версию из version.py (версия будет автоматически увеличена)...")
    initial_version = get_current_version()
    print(f"📌 Используется версия: {initial_version}")
    
    # Передаем версию в build_msi, чтобы избежать повторного увеличения
    if build_msi_with_version(initial_version):
        print("\n✅ MSI инсталлятор готов к распространению!")
        print(f"📦 Файл: Arkanoid_v{initial_version}_Setup.msi")
        print(f"👤 Издатель: {get_publisher()}")
        print(f"🌐 URL: {get_publisher_url()}")
        print("\nФункции инсталлятора:")
        print("- Установка в %LOCALAPPDATA%\\Games\\Arkanoid")
        print("- Создание ярлыка на рабочем столе")
        print("- Автоматическое создание папки для рекордов")
        print("- Правильная деинсталляция")
        print("\n💡 Для изменения издателя:")
        print("  1. Измените функцию get_publisher() в create_msi.py")
        print("  2. Или установите переменную окружения:")
        print("     set MSI_PUBLISHER=Ваше Имя")
        print("     set MSI_PUBLISHER_URL=https://ваш-сайт.com")
        print("\n⚠️  ВАЖНО: Windows может показывать 'Издатель: нет данных'")
        print("   для неподписанных MSI файлов. Для полного отображения")
        print("   издателя необходимо подписать MSI цифровой подписью.")
        print("   Это нормальное поведение Windows для безопасности.")
        return True
    else:
        print("\n❌ Ошибка создания MSI инсталлятора")
        return False


if __name__ == "__main__":
    main()
