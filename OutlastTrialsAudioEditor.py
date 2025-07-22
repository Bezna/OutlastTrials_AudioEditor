import sys
import os
import json
import subprocess
import tempfile
import shutil
import threading
import csv
import traceback
import requests
from packaging import version
from functools import partial
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
from PyQt5.QtCore import QObject, pyqtSignal
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import struct
from collections import namedtuple

CuePoint = namedtuple('CuePoint', ['id', 'position', 'chunk_id', 'chunk_start', 'block_start', 'sample_offset'])
Label = namedtuple('Label', ['id', 'text'])

if sys.platform == "win32":
    import subprocess
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    CREATE_NO_WINDOW = 0x08000000
else:
    startupinfo = None
    CREATE_NO_WINDOW = 0
current_version = "v0.5.9-beta"

TRANSLATIONS = {
    "en": {
        # === ОСНОВНЫЕ ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ===
        "app_title": "OutlastTrials AudioEditor",
        "file_menu": "File",
        "edit_menu": "Edit",
        "tools_menu": "Tools",
        "help_menu": "Help",
        "save_subtitles": "Save Subtitles",
        "export_subtitles": "Export Subtitles...",
        "import_subtitles": "Import Subtitles...",
        "import_custom_subtitles": "Import Custom Subtitles (Beta)...",
        "exit": "Exit",
        "revert_to_original": "Revert to Original",
        "find_replace": "Find && Replace...",
        "compile_mod": "Compile Mod",
        "deploy_and_run": "Deploy Mod && Run Game",
        "show_debug": "Show Debug Console",
        "settings": "Settings...",
        "about": "About",
        
        # === ФИЛЬТРЫ И СОРТИРОВКА ===
        "filter": "Filter:",
        "sort": "Sort:",
        "all_files": "All Files",
        "with_subtitles": "With Subtitles",
        "without_subtitles": "Without Subtitles",
        "modified": "Modified",
        "modded": "Modded (Audio)",
        "name_a_z": "Name (A-Z)",
        "name_z_a": "Name (Z-A)",
        "id_asc": "ID ↑",
        "id_desc": "ID ↓",
        "recent_first": "Recent First",
        
        # === ОСНОВНЫЕ СЛОВА ===
        "name": "Name",
        "id": "ID",
        "subtitle": "Subtitle",
        "status": "Status",
        "mod": "MOD",
        "path": "Path",
        "source": "Source",
        "original": "Original",
        "save": "Save",
        "cancel": "Cancel",
        "browse": "Browse...",
        "confirmation": "Confirmation",
        "error": "Error",
        "warning": "Warning",
        "success": "Success",
        "info": "Information",
        "close": "Close",
        "ready": "Ready",
        "waiting": "Waiting...",
        "done": "Done",
        "error_status": "Error",
        "size_warning": "Size Warning",
        "loading": "Loading...",
        "processing": "Processing...",
        "converting": "Converting...",
        "complete": "Complete",
        "stop": "Stop",
        "clear": "Clear",
        "language": "Language",
        
        # === ДИАЛОГИ И СООБЩЕНИЯ ===
        "edit_subtitle": "Edit Subtitle",
        "subtitle_preview": "Subtitle Preview",
        "file_info": "File Information",
        "select_game_path": "Select game root folder",
        "game_path_saved": "Game path saved",
        "mod_deployed": "Mod deployed successfully!",
        "game_launching": "Launching game...",
        "no_game_path": "Please set game path in settings first",
        "no_changes": "No Changes",
        "no_modified_subtitles": "No modified subtitles to export",
        "import_error": "Import Error",
        "export_error": "Export Error",
        "save_error": "Save Error",
        "file_not_found": "File not found",
        "conversion_stopped": "Conversion stopped",
        "deployment_complete": "Deployment complete",
        "characters": "Characters:",
        
        # === КОНФЛИКТЫ СУБТИТРОВ ===
        "conflict_detected": "Subtitle Conflict Detected",
        "conflict_message": "The following keys already have subtitles:\n\n{conflicts}\n\nWhich subtitles would you like to keep?",
        "use_existing": "Keep Existing",
        "use_new": "Use New",
        "merge_all": "Merge All (Keep Existing)",
        
        # === КОНВЕРТЕР WAV TO WEM ===
        "wav_to_wem_converter": "WAV to WEM Converter",
        "conversion_mode": "Conversion Mode",
        "strict_mode": "Strict Mode",
        "adaptive_mode": "Adaptive Mode",
        "strict_mode_desc": "❌ Fails if too large",
        "adaptive_mode_desc": "✅ Auto-adjusts quality",
        "path_configuration": "Path Configuration",
        "wwise_path": "Wwise:",
        "project_path": "Project:",
        "wav_path": "WAV:",
        "files_for_conversion": "Files for Conversion",
        "add_all_wav": "Add All WAV Files",
        "convert": "Convert",
        "files_ready": "Files ready:",
        "wav_file": "WAV File",
        "target_wem": "Target WEM",
        "target_size": "Target Size",
        "files_ready_count": "Files ready: {count}",
        "confirm_clear": "Clear all files?",
        
        # === КОНВЕРТАЦИЯ И ЛОГИ ===
        "conversion_complete": "Conversion Complete",
        "conversion_logs": "Conversion Logs",
        "clear_logs": "Clear Logs",
        "save_logs": "Save Logs",
        "logs_cleared": "Logs cleared...",
        "logs_saved": "Logs saved",
        "error_saving_logs": "Failed to save logs",
        "starting_conversion": "Starting conversion in {mode} mode...",
        "file_status": "File {current}/{total}: {name}",
        "attempting": "attempt {attempts} (Conversion={value})",
        "testing_sample_rate": "Testing {rate}Hz...",
        "resampled_to": "Resampled to {rate}Hz",
        "results_summary": "✅ Conversion and deployment complete!\n\nSuccessful: {successful}\nErrors: {failed}\nSize warnings: {warnings}\n\nFiles deployed to MOD_P\nSee 'Logs' tab for detailed results",
        "add_files_warning": "Please add files for conversion first!",
        
        # === ИНСТРУКЦИИ ===
        "converter_instructions": "WAV to WEM Converter:\n1) Set Wwise path 2) Choose temp project folder 3) Select WAV folder 4) Add files 5) Convert",
        "converter_instructions2": "WEM Converter:\n1) Set Wwise project path 2) Convert to mod",
        
        # === ПУТИ И ПЛЕЙСХОЛДЕРЫ ===
        "wwise_path_placeholder": "Wwise installation path... (Example: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "New/Old Project path... (Example: D:/ExampleProjects/MyNewProject) P.S. Can be empty",
        "wav_folder_placeholder": "WAV files folder...",
        
        # === ПОИСК И ОБРАБОТКА ===
        "select_wav_folder": "Please select WAV folder first!",
        "wems_folder_not_found": "Wems folder not found",
        "no_wav_files": "No WAV files found in folder!",
        "search_complete": "Search complete",
        "auto_search_result": "Automatically found matches: {matched} of {total}",
        "target_language": "Target language for voice files",
        "no_matches_found": "No matches found for",
        
        # === ЭКСПОРТ СУБТИТРОВ ===
        "cleanup_mod_subtitles": "Clean Up MOD_P Subtitles",
        "export_subtitles_for_game": "Export Subtitles for Game",
        "subtitle_export_ready": "Ready to export subtitles...",
        "deploying_files": "Deploying files to game structure...",
        "deployment_error": "Deployment error",
        "conversion_failed": "Conversion failed",
        "all_files_failed": "All files failed",
        "see_logs_for_details": "See 'Logs' tab for details",
        "localization_editor": "Localization Editor",    
        # === WEM ПРОЦЕССОР ===
        "wem_processor_warning": "⚠️ WEM Processor (Not Recommended)",
        "wem_processor_desc": "Legacy tool for processing ready WEM files.",
        "wem_processor_recommendation": "Use 'WAV to WEM' for beginners.",
        
        # === ЭКСПОРТЕР ЛОКАЛИЗАЦИИ ===
        "localization_exporter": "Localization Exporter",
        "export_modified_subtitles": "Export Modified Subtitles",
        "localization_editor_desc": "Edit localization directly. Use the global search bar above to filter results.",
        # === ОЧИСТКА СУБТИТРОВ ===
        "cleanup_subtitles_found": "Found {count} subtitle files in MOD_P",
        "select_files_to_delete": "Please select files to delete",
        "confirm_deletion": "Confirm Deletion",
        "delete_files_warning": "Are you sure you want to delete {count} subtitle files?\n\nThis action cannot be undone!",
        "cleanup_complete": "Cleanup Complete",
        "cleanup_with_errors": "Cleanup Complete with Errors",
        "files_deleted_successfully": "Successfully deleted {count} subtitle files from MOD_P",
        "files_deleted_with_errors": "Deleted {count} files successfully\n{errors} files had errors\n\nCheck the status log for details",
        "no_localization_found": "No Files Found",
        "no_localization_message": "No localization folder found at:\n{path}",
        "no_subtitle_files": "No subtitle files found in:\n{path}",
        "select_all": "Select All",
        "select_none": "Select None",
        "quick_select": "Quick select:",
        "select_by_language": "Select by language...",
        "delete_selected": "Delete Selected",
        "no_selection": "No Selection",
        
        # === АУДИО ИНФОРМАЦИЯ ===
        "audio_comparison": "Audio Comparison",
        "original_audio": "Original Audio",
        "modified_audio": "Modified Audio",
        "duration": "Duration",
        "size": "Size",
        "sample_rate": "Sample Rate",
        "bitrate": "Bitrate",
        "channels": "Channels",
        "audio_markers": "Audio Markers",
        "original_markers": "Original Markers",
        "modified_markers": "Modified Markers",
        
        # === КОНТЕКСТНОЕ МЕНЮ ===
        "play_original": "▶ Play Original",
        "play_mod": "▶ Play Mod",
        "export_as_wav": "💾 Export as WAV",
        "delete_mod_audio": "🗑 Delete Mod Audio",
        "copy_key": "📋 Copy Key",
        "copy_text": "📋 Copy Text",
        "remove": "❌ Remove",
        "browse_target_wem": "📁 Browse for Target WEM...",
        "quick_select_menu": "⚡ Quick Select",
        
        # === ИНСТРУМЕНТЫ ===
        "expand_all": "📂 Expand All",
        "collapse_all": "📁 Collapse All",
        "edit_button": "✏ Edit",
        "export_button": "💾 Export",
        "delete_mod_button": "🗑 Delete Mod AUDIO",
        "wemprocces_desc": "Select language for renaming and placing WEM files during processing",
        # === ЭКСПОРТ АУДИО ===
        "export_audio": "Export Audio",
        "which_version_export": "Which version would you like to export?",
        "save_as_wav": "Save as WAV",
        "wav_files": "WAV Files",
        "batch_export": "Batch Export",
        "select_output_directory": "Select Output Directory",
        "exporting_files": "Exporting {count} files...",
        "export_results": "Exported {successful} files successfully.\n{errors} errors occurred.",
        "export_complete": "Export Complete",
        
        # === ДИАЛОГИ СОХРАНЕНИЯ ===
        "save_changes_question": "Save Changes?",
        "unsaved_changes_message": "You have unsaved subtitle changes. Save before closing?",
        
        # === КОМПИЛЯЦИЯ МОДОВ ===
        "mod_not_found_compile": "Mod file not found. Compile it first?",
        "mod_compilation_failed": "Mod compilation failed",
        "repak_not_found": "repak.exe not found!",
        "compiling_mod": "Compiling Mod",
        "running_repak": "Running repak...",
        "mod_compiled_successfully": "Mod compiled successfully!",
        "compilation_failed": "Compilation failed!",
        
        # === НАСТРОЙКИ ===
        "auto_save": "Auto-save subtitles every 5 minutes",
        "interface_language": "Interface Language (NEED RESTART):",
        "theme": "Theme:",
        "subtitle_language": "Subtitle Language:",
        "game_path": "Game Path:",
        "wem_process_language": "WEM Process Language:",
        "light": "Light",
        "dark": "Dark",
        "rename_french_audio": "Rename French audio files to ID (in addition to English)",
        
        # === СПРАВКА И ОТЧЕТЫ ===
        "keyboard_shortcuts": "Keyboard Shortcuts",
        "documentation": "📖 Documentation",
        "check_updates": "🔄 Check for Updates",
        "report_bug": "🐛 Report Bug",
        "getting_started": "Getting Started",
        "features": "Features",
        "file_structure": "File Structure",
        "credits": "Credits",
        "license": "License",
        "github": "GitHub",
        "discord": "Discord",
        "donate": "Donate",
        
        # === ОТЧЕТ ОБ ОШИБКЕ ===
        "bug_report_info": "Found a bug? Please provide details below.\nDebug logs will be automatically included.",
        "description": "Description",
        "email_optional": "Email (optional)",
        "copy_report_clipboard": "Copy Report to Clipboard",
        "open_github_issues": "Open GitHub Issues",
        "bug_report_copied": "Bug report copied to clipboard!",
        
        # === TOOLTIPS ===
        "has_audio_file": "Has audio file",
        "no_audio_file": "No audio file",
        
        # === О ПРОГРАММЕ ===
        "about_description": "A tool for managing WEM audio files and game subtitles for Outlast Trials, designed for modders and localization teams.",
        "key_features": "Key Features",
        "audio_management": "🎵 <b>Audio Management:</b> Play, convert, and organize WEM files",
        "subtitle_editing": "📝 <b>Subtitle Editing:</b> Easy editing with conflict resolution",
        "mod_creation": "📦 <b>Mod Creation:</b> One-click mod compilation and deployment",
        "multi_language": "🌍 <b>Multi-language:</b> Support for 14+ languages",
        "modern_ui": "🎨 <b>Modern UI:</b> Clean interface with dark/light themes",
        "technology_stack": "Technology Stack",
        "built_with": "Built with Python 3 and PyQt5, utilizing:",
        "unreal_locres_tool": "UnrealLocres for .locres file handling",
        "vgmstream_tool": "vgmstream for audio conversion",
        "repak_tool": "repak for mod packaging",
        "development_team": "Development Team",
        "lead_developer": "<b>Lead Developer:</b> Bezna",
        "special_thanks": "Special Thanks",
        "vgmstream_thanks": "vgmstream team - For audio conversion tools",
        "unreal_locres_thanks": "UnrealLocres developers - For localization support",
        "hypermetric_thanks": "hypermetric - For mod packaging",
        "red_barrels_thanks": "Red Barrels - For creating Outlast Trials",
        "open_source_libraries": "Open Source Libraries",
        "pyqt5_lib": "PyQt5 - GUI Framework",
        "python_lib": "Python Standard Library",
        "software_disclaimer": "This software is provided \"as is\" without warranty of any kind. Use at your own risk.",
        "license_agreement": "License Agreement",
        "copyright_notice": "Copyright (c) 2025 OutlastTrials AudioEditor",
        "mit_license_text": "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.",
        
        # === ГОРЯЧИЕ КЛАВИШИ ===
        "shortcuts_table_action": "Action",
        "shortcuts_table_shortcut": "Shortcut",
        "shortcuts_table_description": "Description",
        "shortcut_edit_subtitle": "Edit Subtitle",
        "shortcut_save_subtitles": "Save Subtitles",
        "shortcut_export_audio": "Export Audio",
        "shortcut_revert_original": "Revert to Original",
        "shortcut_deploy_run": "Deploy & Run",
        "shortcut_debug_console": "Debug Console",
        "shortcut_settings": "Settings",
        "shortcut_documentation": "Documentation",
        "shortcut_exit": "Exit",
        "shortcut_edit_selected": "Edit selected subtitle",
        "shortcut_save_all_changes": "Save all subtitle changes",
        "shortcut_export_selected": "Export selected audio as WAV",
        "shortcut_revert_selected": "Revert selected subtitle to original",
        "shortcut_deploy_launch": "Deploy mod and launch game",
        "shortcut_show_debug": "Show debug console",
        "shortcut_open_settings": "Open settings dialog",
        "shortcut_show_help": "Show documentation",
        "shortcut_close_app": "Close application",
        "mouse_actions": "Mouse Actions",
        "mouse_double_subtitle": "<b>Double-click subtitle:</b> Edit subtitle",
        "mouse_double_file": "<b>Double-click file:</b> Play audio",
        "exports_modified_subtitles_desc": "Exports modified subtitles in proper structure for the game:",
        "creates_mod_p_structure": "Creates MOD_P/OPP/Content/Localization/ structure",
        "supports_multiple_categories": "Supports multiple subtitle categories",
        "each_language_separate_folder": "Each language placed in separate folder",
        "ready_files_for_mods": "Ready files can be used in mods",
        "mouse_right_click": "<b>Right-click:</b> Show context menu"
    },
    
    "ru": {
        # === ОСНОВНЫЕ ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ===
        "wemprocces_desc": "Выберите язык для переименования и размещения файлов WEM во время обработки",
        "exports_modified_subtitles_desc": "Экспортирует изменённые субтитры в правильной структуре для игры:",
        "creates_mod_p_structure": "Создаёт структуру MOD_P/OPP/Content/Localization/",
        "supports_multiple_categories": "Поддерживает несколько категорий субтитров",
        "each_language_separate_folder": "Каждый язык в отдельной папке",
        "ready_files_for_mods": "Готовые файлы можно использовать в модах",
        "app_title": "OutlastTrials AudioEditor",
        "file_menu": "Файл",
        "edit_menu": "Правка",
        "tools_menu": "Инструменты",
        "help_menu": "Справка",
        "save_subtitles": "Сохранить субтитры",
        "export_subtitles": "Экспорт субтитров...",
        "import_subtitles": "Импорт субтитров...",
        "import_custom_subtitles": "Импорт пользовательских субтитров (Бета)...",
        "exit": "Выход",
        "revert_to_original": "Вернуть оригинал",
        "find_replace": "Найти и заменить...",
        "compile_mod": "Скомпилировать мод",
        "deploy_and_run": "Установить мод и запустить игру",
        "show_debug": "Показать консоль отладки",
        "settings": "Настройки...",
        "about": "О программе",
        
        # === ФИЛЬТРЫ И СОРТИРОВКА ===
        "filter": "Фильтр:",
        "sort": "Сортировка:",
        "all_files": "Все файлы",
        "with_subtitles": "С субтитрами",
        "without_subtitles": "Без субтитров",
        "modified": "Изменённые",
        "modded": "С модиф. аудио",
        "name_a_z": "Имя (А-Я)",
        "name_z_a": "Имя (Я-А)",
        "id_asc": "ID ↑",
        "id_desc": "ID ↓",
        "recent_first": "Сначала новые",
        
        # === ОСНОВНЫЕ СЛОВА ===
        "name": "Имя",
        "id": "ID",
        "subtitle": "Субтитр",
        "status": "Статус",
        "mod": "МОД",
        "path": "Путь",
        "source": "Источник",
        "original": "Оригинал",
        "save": "Сохранить",
        "cancel": "Отмена",
        "browse": "Обзор...",
        "confirmation": "Подтверждение",
        "error": "Ошибка",
        "warning": "Предупреждение",
        "success": "Успех",
        "info": "Информация",
        "close": "Закрыть",
        "ready": "Готов",
        "waiting": "Ожидание...",
        "done": "Готово",
        "error_status": "Ошибка",
        "size_warning": "Предупреждение о размере",
        "loading": "Загрузка...",
        "processing": "Обработка...",
        "converting": "Конвертация...",
        "complete": "Завершено",
        "stop": "Стоп",
        "clear": "Очистить",
        "language": "Язык",
        
        # === ДИАЛОГИ И СООБЩЕНИЯ ===
        "edit_subtitle": "Редактировать субтитр",
        "subtitle_preview": "Предпросмотр субтитров",
        "file_info": "Информация о файле",
        "select_game_path": "Выберите корневую папку игры",
        "game_path_saved": "Путь к игре сохранён",
        "mod_deployed": "Мод успешно установлен!",
        "game_launching": "Запуск игры...",
        "no_game_path": "Сначала укажите путь к игре в настройках",
        "no_changes": "Нет изменений",
        "no_modified_subtitles": "Нет изменённых субтитров для экспорта",
        "import_error": "Ошибка импорта",
        "export_error": "Ошибка экспорта",
        "save_error": "Ошибка сохранения",
        "file_not_found": "Файл не найден",
        "conversion_stopped": "Конвертация остановлена",
        "deployment_complete": "Размещение завершено",
        "characters": "Символов:",
        
        # === КОНФЛИКТЫ СУБТИТРОВ ===
        "conflict_detected": "Обнаружен конфликт субтитров",
        "conflict_message": "Следующие ключи уже имеют субтитры:\n\n{conflicts}\n\nКакие субтитры использовать?",
        "use_existing": "Оставить существующие",
        "use_new": "Использовать новые",
        "merge_all": "Объединить все (оставить существующие)",
        
        # === КОНВЕРТЕР WAV TO WEM ===
        "wav_to_wem_converter": "Конвертер WAV в WEM",
        "conversion_mode": "Режим конвертации",
        "strict_mode": "Строгий режим",
        "adaptive_mode": "Адаптивный режим",
        "strict_mode_desc": "❌ Ошибка, если слишком большой",
        "adaptive_mode_desc": "✅ Авто-подстройка качества",
        "path_configuration": "Настройка путей",
        "wwise_path": "Wwise:",
        "project_path": "Проект:",
        "wav_path": "WAV:",
        "files_for_conversion": "Файлы для конвертации",
        "add_all_wav": "Добавить все WAV файлы",
        "convert": "Конвертировать",
        "files_ready": "Файлов готово:",
        "wav_file": "WAV файл",
        "target_wem": "Целевой WEM",
        "target_size": "Целевой размер",
        "files_ready_count": "Файлов готово: {count}",
        "confirm_clear": "Очистить весь список файлов?",
        
        # === КОНВЕРТАЦИЯ И ЛОГИ ===
        "conversion_complete": "Конвертация завершена",
        "conversion_logs": "Логи конвертации",
        "clear_logs": "Очистить логи",
        "save_logs": "Сохранить логи",
        "logs_cleared": "Логи очищены...",
        "logs_saved": "Логи сохранены",
        "error_saving_logs": "Не удалось сохранить логи",
        "starting_conversion": "Начинается конвертация в режиме {mode}...",
        "file_status": "Файл {current}/{total}: {name}",
        "attempting": "попытка {attempts} (Conversion={value})",
        "testing_sample_rate": "Тестирование {rate}Гц...",
        "resampled_to": "Изменена частота на {rate}Гц",
        "results_summary": "✅ Конвертация и размещение завершены!\n\nУспешно: {successful}\nОшибок: {failed}\nПредупреждений о размере: {warnings}\n\nФайлы размещены в MOD_P\nСм. вкладку 'Логи' для подробностей",
        "add_files_warning": "Сначала добавьте файлы для конвертации!",
        
        # === ИНСТРУКЦИИ ===
        "converter_instructions": "Конвертер WAV в WEM:\n1) Укажите путь Wwise 2) Выберите папку для проекта 3) Выберите папку WAV 4) Добавьте файлы 5) Конвертируйте",
        "converter_instructions2": "Конвертер WEM:\n1) Укажите путь Wwise проекта 2) Конвертируйте в мод",
        
        # === ПУТИ И ПЛЕЙСХОЛДЕРЫ ===
        "wwise_path_placeholder": "Путь установки Wwise... (Пример: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "Путь нового/старого проекта... (Пример: D:/ExampleProjects/MyNewProject) P.S. Может быть пустым",
        "wav_folder_placeholder": "Папка с WAV файлами...",
        
        # === ПОИСК И ОБРАБОТКА ===
        "select_wav_folder": "Сначала выберите папку с WAV файлами!",
        "wems_folder_not_found": "Папка Wems не найдена",
        "no_wav_files": "В папке нет WAV файлов!",
        "search_complete": "Поиск завершен",
        "auto_search_result": "Автоматически найдено соответствий: {matched} из {total}",
        "target_language": "Целевой язык для голосовых файлов",
        "no_matches_found": "Не найдены соответствия для",
        
        # === ЭКСПОРТ СУБТИТРОВ ===
        "cleanup_mod_subtitles": "Очистить субтитры MOD_P",
        "export_subtitles_for_game": "Экспорт субтитры для игры",
        "subtitle_export_ready": "Готов к экспорту субтитров...",
        "deploying_files": "Размещение файлов в игровой структуре...",
        "deployment_error": "Ошибка размещения",
        "conversion_failed": "Конвертация не удалась",
        "all_files_failed": "Все файлы не удалось обработать",
        "see_logs_for_details": "См. вкладку 'Логи' для подробностей",
        
        # === WEM ПРОЦЕССОР ===
        "wem_processor_warning": "⚠️ Процессор WEM (Не рекомендуется)",
        "wem_processor_desc": "Устаревший инструмент для обработки готовых WEM файлов.",
        "wem_processor_recommendation": "Рекомендуется использовать 'WAV to WEM' для новичков.",
        
        # === ЭКСПОРТЕР ЛОКАЛИЗАЦИИ ===
        "localization_exporter": "Экспортер локализации",
        "export_modified_subtitles": "Экспорт измененных субтитров",
        "localization_editor_desc": "Редактируйте локализацию напрямую. Используйте глобальную строку поиска выше для фильтрации результатов.",
        # === ОЧИСТКА СУБТИТРОВ ===
        "cleanup_subtitles_found": "Найдено {count} файлов субтитров в MOD_P",
        "select_files_to_delete": "Пожалуйста, выберите файлы для удаления",
        "confirm_deletion": "Подтвердить удаление",
        "delete_files_warning": "Вы уверены, что хотите удалить {count} файлов субтитров?\n\nЭто действие нельзя отменить!",
        "cleanup_complete": "Очистка завершена",
        "cleanup_with_errors": "Очистка завершена с ошибками",
        "files_deleted_successfully": "Успешно удалено {count} файлов субтитров из MOD_P",
        "files_deleted_with_errors": "Удалено {count} файлов успешно\n{errors} файлов с ошибками\n\nПроверьте журнал состояния для подробностей",
        "no_localization_found": "Файлы не найдены",
        "no_localization_message": "Папка локализации не найдена:\n{path}",
        "no_subtitle_files": "Файлы субтитров не найдены в:\n{path}",
        "select_all": "Выбрать все",
        "select_none": "Снять выделение",
        "quick_select": "Быстрый выбор:",
        "select_by_language": "Выбрать по языку...",
        "delete_selected": "Удалить выбранные",
        "no_selection": "Нет выбора",
        "localization_editor": "Редактор локализации",        
        # === АУДИО ИНФОРМАЦИЯ ===
        "audio_comparison": "Сравнение аудио",
        "original_audio": "Оригинальное аудио",
        "modified_audio": "Изменённое аудио",
        "duration": "Длительность:",
        "size": "Размер:",
        "sample_rate": "Частота дискретизации:",
        "bitrate": "Битрейт:",
        "channels": "Каналы:",
        "audio_markers": "Аудио маркеры",
        "original_markers": "Оригинальные маркеры",
        "modified_markers": "Изменённые маркеры",
        
        # === КОНТЕКСТНОЕ МЕНЮ ===
        "play_original": "▶ Воспроизвести оригинал",
        "play_mod": "▶ Воспроизвести мод",
        "export_as_wav": "💾 Экспорт в WAV",
        "delete_mod_audio": "🗑 Удалить мод аудио",
        "copy_key": "📋 Копировать ключ",
        "copy_text": "📋 Копировать текст",
        "remove": "❌ Удалить",
        "browse_target_wem": "📁 Выбрать целевой WEM...",
        "quick_select_menu": "⚡ Быстрый выбор",
        
        # === ИНСТРУМЕНТЫ ===
        "expand_all": "📂 Развернуть все",
        "collapse_all": "📁 Свернуть все",
        "edit_button": "✏ Редактировать",
        "export_button": "💾 Экспорт",
        "delete_mod_button": "🗑 Удалить мод АУДИО",
        
        # === ЭКСПОРТ АУДИО ===
        "export_audio": "Экспорт аудио",
        "which_version_export": "Какую версию вы хотите экспортировать?",
        "save_as_wav": "Сохранить как WAV",
        "wav_files": "Файлы WAV",
        "batch_export": "Пакетный экспорт",
        "select_output_directory": "Выберите папку вывода",
        "exporting_files": "Экспорт {count} файлов...",
        "export_results": "Экспортировано {successful} файлов успешно.\nВозникло {errors} ошибок.",
        "export_complete": "Экспорт завершён",
        
        # === ДИАЛОГИ СОХРАНЕНИЯ ===
        "save_changes_question": "Сохранить изменения?",
        "unsaved_changes_message": "У вас есть несохранённые изменения субтитров. Сохранить перед закрытием?",
        
        # === КОМПИЛЯЦИЯ МОДОВ ===
        "mod_not_found_compile": "Файл мода не найден. Скомпилировать сначала?",
        "mod_compilation_failed": "Компиляция мода не удалась",
        "repak_not_found": "repak.exe не найден!",
        "compiling_mod": "Компиляция мода",
        "running_repak": "Запуск repak...",
        "mod_compiled_successfully": "Мод скомпилирован успешно!",
        "compilation_failed": "Компиляция не удалась!",
        
        # === НАСТРОЙКИ ===
        "auto_save": "Автосохранение субтитров каждые 5 минут",
        "interface_language": "Язык интерфейса (ТРЕБУЕТ ПЕРЕЗАПУСК):",
        "theme": "Тема:",
        "subtitle_language": "Язык субтитров:",
        "game_path": "Путь к игре:",
        "wem_process_language": "Язык обработки WEM:",
        "light": "Светлая",
        "dark": "Тёмная",
        "rename_french_audio": "Переименовать французские аудиофайлы в ID (дополнительно к английским)",
        
        # === СПРАВКА И ОТЧЕТЫ ===
        "keyboard_shortcuts": "Горячие клавиши",
        "documentation": "📖 Документация",
        "check_updates": "🔄 Проверить обновления",
        "report_bug": "🐛 Сообщить об ошибке",
        "getting_started": "Начало работы",
        "features": "Возможности",
        "file_structure": "Структура файлов",
        "credits": "Создатели",
        "license": "Лицензия",
        "github": "GitHub",
        "discord": "Discord",
        "donate": "Поддержать",
        
        # === ОТЧЕТ ОБ ОШИБКЕ ===
        "bug_report_info": "Нашли баг? Пожалуйста, предоставьте подробности ниже.\nЛоги отладки будут включены автоматически.",
        "description": "Описание",
        "email_optional": "Email (необязательно)",
        "copy_report_clipboard": "Копировать отчёт в буфер",
        "open_github_issues": "Открыть GitHub Issues",
        "bug_report_copied": "Отчёт об ошибке скопирован в буфер обмена!",
        
        # === TOOLTIPS ===
        "has_audio_file": "Есть аудиофайл",
        "no_audio_file": "Нет аудиофайла",
        
        # === О ПРОГРАММЕ ===
        "about_description": "Инструмент для управления WEM аудиофайлами и субтитрами игры для Outlast Trials, разработанный для моддеров и команд локализации.",
        "key_features": "Ключевые возможности",
        "audio_management": "🎵 <b>Управление аудио:</b> Воспроизведение, конвертация и организация WEM файлов",
        "subtitle_editing": "📝 <b>Редактирование субтитров:</b> Простое редактирование с разрешением конфликтов",
        "mod_creation": "📦 <b>Создание модов:</b> Компиляция и развёртывание модов в один клик",
        "multi_language": "🌍 <b>Многоязычность:</b> Поддержка 14+ языков",
        "modern_ui": "🎨 <b>Современный интерфейс:</b> Чистый интерфейс с тёмной/светлой темами",
        "technology_stack": "Технологический стек",
        "built_with": "Создано с Python 3 и PyQt5, используя:",
        "unreal_locres_tool": "UnrealLocres для работы с .locres файлами",
        "vgmstream_tool": "vgmstream для конвертации аудио",
        "repak_tool": "repak для упаковки модов",
        "development_team": "Команда разработки",
        "lead_developer": "<b>Ведущий разработчик:</b> Bezna",
        "special_thanks": "Особая благодарность",
        "vgmstream_thanks": "Команда vgmstream - За инструменты конвертации аудио",
        "unreal_locres_thanks": "Разработчики UnrealLocres - За поддержку локализации",
        "hypermetric_thanks": "hypermetric - За упаковку модов",
        "red_barrels_thanks": "Red Barrels - За создание Outlast Trials",
        "open_source_libraries": "Библиотеки с открытым исходным кодом",
        "pyqt5_lib": "PyQt5 - GUI Framework",
        "python_lib": "Стандартная библиотека Python",
        "software_disclaimer": "Это программное обеспечение предоставляется \"как есть\" без каких-либо гарантий. Используйте на свой страх и риск.",
        "license_agreement": "Лицензионное соглашение",
        "copyright_notice": "Copyright (c) 2025 OutlastTrials AudioEditor",
        "mit_license_text": "Настоящим предоставляется бесплатное разрешение любому лицу, получившему копию данного программного обеспечения и связанных с ним файлов документации (\"Программное обеспечение\"), на использование Программного обеспечения без ограничений, включая неограниченное право на использование, копирование, изменение, слияние, публикацию, распространение, сублицензирование и/или продажу копий Программного обеспечения, а также лицам, которым предоставляется данное Программное обеспечение, при соблюдении следующих условий:\n\nВышеуказанное уведомление об авторском праве и данное уведомление о разрешении должны быть включены во все копии или существенные части данного Программного обеспечения.\n\nДАННОЕ ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ ПРЕДОСТАВЛЯЕТСЯ \"КАК ЕСТЬ\", БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ, ЯВНЫХ ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ ГАРАНТИИ ТОВАРНОЙ ПРИГОДНОСТИ, СООТВЕТСТВИЯ ПО ЕГО КОНКРЕТНОМУ НАЗНАЧЕНИЮ И ОТСУТСТВИЯ НАРУШЕНИЙ, НО НЕ ОГРАНИЧИВАЯСЬ ИМИ. НИ В КАКОМ СЛУЧАЕ АВТОРЫ ИЛИ ПРАВООБЛАДАТЕЛИ НЕ НЕСУТ ОТВЕТСТВЕННОСТИ ПО КАКИМ-ЛИБО ИСКАМ, ЗА УЩЕРБ ИЛИ ПО ИНОЙ ОТВЕТСТВЕННОСТИ, БУДЬ ТО В ДЕЙСТВИИ ПО ДОГОВОРУ, ДЕЛИКТУ ИЛИ ИНОМУ, ВЫТЕКАЮЩИХ ИЗ, СВЯЗАННЫХ С ИЛИ В СВЯЗИ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ ИЛИ ИСПОЛЬЗОВАНИЕМ ИЛИ ИНЫМИ ДЕЙСТВИЯМИ В ПРОГРАММНОМ ОБЕСПЕЧЕНИИ.",
        
        # === ГОРЯЧИЕ КЛАВИШИ ===
        "shortcuts_table_action": "Действие",
        "shortcuts_table_shortcut": "Горячая клавиша",
        "shortcuts_table_description": "Описание",
        "shortcut_edit_subtitle": "Редактировать субтитр",
        "shortcut_save_subtitles": "Сохранить субтитры",
        "shortcut_export_audio": "Экспорт аудио",
        "shortcut_revert_original": "Вернуть к оригиналу",
        "shortcut_deploy_run": "Развернуть и запустить",
        "shortcut_debug_console": "Консоль отладки",
        "shortcut_settings": "Настройки",
        "shortcut_documentation": "Документация",
        "shortcut_exit": "Выход",
        "shortcut_edit_selected": "Редактировать выбранный субтитр",
        "shortcut_save_all_changes": "Сохранить все изменения субтитров",
        "shortcut_export_selected": "Экспортировать выбранное аудио как WAV",
        "shortcut_revert_selected": "Вернуть выбранный субтитр к оригиналу",
        "shortcut_deploy_launch": "Развернуть мод и запустить игру",
        "shortcut_show_debug": "Показать консоль отладки",
        "shortcut_open_settings": "Открыть диалог настроек",
        "shortcut_show_help": "Показать документацию",
        "shortcut_close_app": "Закрыть приложение",
        "mouse_actions": "Действия мыши",
        "mouse_double_subtitle": "<b>Двойной клик по субтитру:</b> Редактировать субтитр",
        "mouse_double_file": "<b>Двойной клик по файлу:</b> Воспроизвести аудио",
        "mouse_right_click": "<b>Правый клик:</b> Показать контекстное меню"
    },
    
    "pl": {
        # === PODSTAWOWE ELEMENTY INTERFEJSU ===
        "wemprocces_desc": "Wybierz język do zmiany nazwy i umieszczenia plików WEM podczas przetwarzania",
        "exports_modified_subtitles_desc": "Eksportuje zmodyfikowane napisy w odpowiedniej strukturze dla gry:",
        "creates_mod_p_structure": "Tworzy strukturę MOD_P/OPP/Content/Localization/",
        "supports_multiple_categories": "Obsługuje wiele kategorii napisów",
        "each_language_separate_folder": "Każdy język w osobnym folderze",
        "ready_files_for_mods": "Gotowe pliki można używać w modach",
        "app_title": "OutlastTrials AudioEditor",
        "file_menu": "Plik",
        "edit_menu": "Edycja",
        "tools_menu": "Narzędzia",
        "help_menu": "Pomoc",
        "save_subtitles": "Zapisz napisy",
        "export_subtitles": "Eksportuj napisy...",
        "import_subtitles": "Importuj napisy...",
        "import_custom_subtitles": "Importuj niestandardowe napisy (Beta)...",
        "exit": "Wyjście",
        "revert_to_original": "Przywróć oryginał",
        "find_replace": "Znajdź i zamień...",
        "compile_mod": "Kompiluj mod",
        "deploy_and_run": "Wdróż mod i uruchom grę",
        "show_debug": "Pokaż konsolę debugowania",
        "settings": "Ustawienia...",
        "about": "O programie",
        
        # === FILTRY I SORTOWANIE ===
        "filter": "Filtr:",
        "sort": "Sortuj:",
        "all_files": "Wszystkie pliki",
        "with_subtitles": "Z napisami",
        "without_subtitles": "Bez napisów",
        "modified": "Zmodyfikowane",
        "modded": "Zmodyfikowane (audio)",
        "name_a_z": "Nazwa (A-Z)",
        "name_z_a": "Nazwa (Z-A)",
        "id_asc": "ID ↑",
        "id_desc": "ID ↓",
        "recent_first": "Najnowsze pierwsze",
        
        # === PODSTAWOWE SŁOWA ===
        "name": "Nazwa",
        "id": "ID",
        "subtitle": "Napisy",
        "status": "Status",
        "mod": "MOD",
        "path": "Ścieżka",
        "source": "Źródło",
        "original": "Oryginał",
        "save": "Zapisz",
        "cancel": "Anuluj",
        "browse": "Przeglądaj...",
        "confirmation": "Potwierdzenie",
        "error": "Błąd",
        "warning": "Ostrzeżenie",
        "success": "Sukces",
        "info": "Informacja",
        "close": "Zamknij",
        "ready": "Gotowy",
        "waiting": "Oczekiwanie...",
        "done": "Gotowe",
        "error_status": "Błąd",
        "size_warning": "Ostrzeżenie rozmiaru",
        "loading": "Ładowanie...",
        "processing": "Przetwarzanie...",
        "converting": "Konwertowanie...",
        "complete": "Zakończone",
        "stop": "Stop",
        "clear": "Wyczyść",
        "language": "Język",
        
        # === OKNA DIALOGOWE I KOMUNIKATY ===
        "edit_subtitle": "Edytuj napisy",
        "subtitle_preview": "Podgląd napisów",
        "file_info": "Informacje o pliku",
        "select_game_path": "Wybierz główny folder gry",
        "game_path_saved": "Ścieżka gry zapisana",
        "mod_deployed": "Mod wdrożony pomyślnie!",
        "game_launching": "Uruchamianie gry...",
        "no_game_path": "Najpierw ustaw ścieżkę gry w ustawieniach",
        "no_changes": "Brak zmian",
        "no_modified_subtitles": "Brak zmodyfikowanych napisów do eksportu",
        "import_error": "Błąd importu",
        "export_error": "Błąd eksportu",
        "save_error": "Błąd zapisu",
        "file_not_found": "Plik nie znaleziony",
        "conversion_stopped": "Konwersja zatrzymana",
        "deployment_complete": "Wdrożenie zakończone",
        "characters": "Znaków:",
        
        # === KONFLIKTY NAPISÓW ===
        "conflict_detected": "Wykryto konflikt napisów",
        "conflict_message": "Następujące klucze już mają napisy:\n\n{conflicts}\n\nKtóre napisy chcesz zachować?",
        "use_existing": "Zachowaj istniejące",
        "use_new": "Użyj nowych",
        "merge_all": "Połącz wszystkie (zachowaj istniejące)",
        
        # === KONWERTER WAV DO WEM ===
        "wav_to_wem_converter": "Konwerter WAV do WEM",
        "conversion_mode": "Tryb konwersji",
        "strict_mode": "Tryb ścisły",
        "adaptive_mode": "Tryb adaptacyjny",
        "strict_mode_desc": "❌ Zawodzi jeśli za duży",
        "adaptive_mode_desc": "✅ Auto-dostosowanie jakości",
        "path_configuration": "Konfiguracja ścieżek",
        "wwise_path": "Wwise:",
        "project_path": "Projekt:",
        "wav_path": "WAV:",
        "files_for_conversion": "Pliki do konwersji",
        "add_all_wav": "Dodaj wszystkie pliki WAV",
        "convert": "Konwertuj",
        "files_ready": "Pliki gotowe:",
        "wav_file": "Plik WAV",
        "target_wem": "Docelowy WEM",
        "target_size": "Docelowy rozmiar",
        "files_ready_count": "Pliki gotowe: {count}",
        "confirm_clear": "Wyczyścić wszystkie pliki?",
        
        # === KONWERSJA I LOGI ===
        "conversion_complete": "Konwersja zakończona",
        "conversion_logs": "Logi konwersji",
        "clear_logs": "Wyczyść logi",
        "save_logs": "Zapisz logi",
        "logs_cleared": "Logi wyczyszczone...",
        "logs_saved": "Logi zapisane",
        "error_saving_logs": "Nie udało się zapisać logów",
        "starting_conversion": "Rozpoczynanie konwersji w trybie {mode}...",
        "file_status": "Plik {current}/{total}: {name}",
        "attempting": "próba {attempts} (Conversion={value})",
        "testing_sample_rate": "Testowanie {rate}Hz...",
        "resampled_to": "Przepróbkowano do {rate}Hz",
        "results_summary": "✅ Konwersja i wdrożenie zakończone!\n\nUdane: {successful}\nBłędy: {failed}\nOstrzeżenia rozmiaru: {warnings}\n\nPliki wdrożone do MOD_P\nZobacz zakładkę 'Logi' dla szczegółów",
        "add_files_warning": "Najpierw dodaj pliki do konwersji!",
        
        # === INSTRUKCJE ===
        "converter_instructions": "Konwerter WAV do WEM:\n1) Ustaw ścieżkę Wwise 2) Wybierz folder tymczasowego projektu 3) Wybierz folder WAV 4) Dodaj pliki 5) Konwertuj",
        "converter_instructions2": "Konwerter WEM:\n1) Ustaw ścieżkę projektu Wwise 2) Konwertuj do moda",
        
        # === ŚCIEŻKI I PLACEHOLDERY ===
        "wwise_path_placeholder": "Ścieżka instalacji Wwise... (Przykład: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "Ścieżka nowego/starego projektu... (Przykład: D:/ExampleProjects/MyNewProject) P.S. Może być pusta",
        "wav_folder_placeholder": "Folder z plikami WAV...",
        
        # === WYSZUKIWANIE I PRZETWARZANIE ===
        "select_wav_folder": "Najpierw wybierz folder WAV!",
        "wems_folder_not_found": "Nie znaleziono folderu Wems",
        "no_wav_files": "Nie znaleziono plików WAV w folderze!",
        "search_complete": "Wyszukiwanie zakończone",
        "auto_search_result": "Automatycznie znaleziono dopasowania: {matched} z {total}",
        "target_language": "Język docelowy dla plików głosowych",
        "no_matches_found": "Nie znaleziono dopasowań dla",
        
        # === EKSPORT NAPISÓW ===
        "cleanup_mod_subtitles": "Wyczyść napisy MOD_P",
        "export_subtitles_for_game": "Eksportuj napisy dla gry",
        "subtitle_export_ready": "Gotowy do eksportu napisów...",
        "deploying_files": "Wdrażanie plików do struktury gry...",
        "deployment_error": "Błąd wdrożenia",
        "conversion_failed": "Konwersja nieudana",
        "all_files_failed": "Wszystkie pliki nieudane",
        "see_logs_for_details": "Zobacz zakładkę 'Logi' dla szczegółów",
        
        # === PROCESOR WEM ===
        "wem_processor_warning": "⚠️ Procesor WEM (Niezalecane)",
        "wem_processor_desc": "Starsze narzędzie do przetwarzania gotowych plików WEM.",
        "wem_processor_recommendation": "Zaleca się używanie „WAV do WEM” dla nowych użytkowników.",
        
        # === EKSPORTER LOKALIZACJI ===
        "localization_exporter": "Eksporter lokalizacji",
        "export_modified_subtitles": "Eksportuj zmodyfikowane napisy",
        "localization_editor": "Edytor lokalizacji",
        "localization_editor_desc": "Edytuj lokalizację bezpośrednio. Użyj globalnego pola wyszukiwania powyżej, aby filtrować wyniki.",
        # === CZYSZCZENIE NAPISÓW ===
        "cleanup_subtitles_found": "Znaleziono {count} plików napisów w MOD_P",
        "select_files_to_delete": "Proszę wybrać pliki do usunięcia",
        "confirm_deletion": "Potwierdź usunięcie",
        "delete_files_warning": "Czy na pewno chcesz usunąć {count} plików napisów?\n\nTej akcji nie można cofnąć!",
        "cleanup_complete": "Czyszczenie zakończone",
        "cleanup_with_errors": "Czyszczenie zakończone z błędami",
        "files_deleted_successfully": "Pomyślnie usunięto {count} plików napisów z MOD_P",
        "files_deleted_with_errors": "Usunięto {count} plików pomyślnie\n{errors} plików z błędami\n\nSprawdź log statusu dla szczegółów",
        "no_localization_found": "Nie znaleziono plików",
        "no_localization_message": "Nie znaleziono folderu lokalizacji w:\n{path}",
        "no_subtitle_files": "Nie znaleziono plików napisów w:\n{path}",
        "select_all": "Zaznacz wszystkie",
        "select_none": "Odznacz wszystkie",
        "quick_select": "Szybki wybór:",
        "select_by_language": "Wybierz według języka...",
        "delete_selected": "Usuń wybrane",
        "no_selection": "Brak wyboru",
        
        # === INFORMACJE O AUDIO ===
        "audio_comparison": "Porównanie audio",
        "original_audio": "Oryginalne audio",
        "modified_audio": "Zmodyfikowane audio",
        "duration": "Czas trwania",
        "size": "Rozmiar",
        "sample_rate": "Częstotliwość próbkowania",
        "bitrate": "Bitrate",
        "channels": "Kanały",
        "audio_markers": "Markery audio",
        "original_markers": "Oryginalne markery",
        "modified_markers": "Zmodyfikowane markery",
        
        # === MENU KONTEKSTOWE ===
        "play_original": "▶ Odtwórz oryginał",
        "play_mod": "▶ Odtwórz mod",
        "export_as_wav": "💾 Eksportuj jako WAV",
        "delete_mod_audio": "🗑 Usuń audio moda",
        "copy_key": "📋 Kopiuj klucz",
        "copy_text": "📋 Kopiuj tekst",
        "remove": "❌ Usuń",
        "browse_target_wem": "📁 Przeglądaj docelowy WEM...",
        "quick_select_menu": "⚡ Szybki wybór",
        
        # === NARZĘDZIA ===
        "expand_all": "📂 Rozwiń wszystkie",
        "collapse_all": "📁 Zwiń wszystkie",
        "edit_button": "✏ Edytuj",
        "export_button": "💾 Eksportuj",
        "delete_mod_button": "🗑 Usuń mod AUDIO",
        
        # === EKSPORT AUDIO ===
        "export_audio": "Eksport audio",
        "which_version_export": "Którą wersję chcesz wyeksportować?",
        "save_as_wav": "Zapisz jako WAV",
        "wav_files": "Pliki WAV",
        "batch_export": "Eksport wsadowy",
        "select_output_directory": "Wybierz katalog wyjściowy",
        "exporting_files": "Eksportowanie {count} plików...",
        "export_results": "Wyeksportowano {successful} plików pomyślnie.\nWystąpiło {errors} błędów.",
        "export_complete": "Eksport zakończony",
        
        # === DIALOGI ZAPISU ===
        "save_changes_question": "Zapisać zmiany?",
        "unsaved_changes_message": "Masz niezapisane zmiany napisów. Zapisać przed zamknięciem?",
        
        # === KOMPILACJA MODÓW ===
        "mod_not_found_compile": "Plik moda nie znaleziony. Skompilować najpierw?",
        "mod_compilation_failed": "Kompilacja moda nieudana",
        "repak_not_found": "repak.exe nie znaleziony!",
        "compiling_mod": "Kompilowanie moda",
        "running_repak": "Uruchamianie repak...",
        "mod_compiled_successfully": "Mod skompilowany pomyślnie!",
        "compilation_failed": "Kompilacja nieudana!",
        
        # === USTAWIENIA ===
        "auto_save": "Automatyczny zapis napisów co 5 minut",
        "interface_language": "Język interfejsu (WYMAGA RESTART):",
        "theme": "Motyw:",
        "subtitle_language": "Język napisów:",
        "game_path": "Ścieżka gry:",
        "wem_process_language": "Język przetwarzania WEM:",
        "light": "Jasny",
        "dark": "Ciemny",
        "rename_french_audio": "Zmień nazwy francuskich plików audio na ID (dodatkowo do angielskich)",
        
        # === POMOC I RAPORTY ===
        "keyboard_shortcuts": "Skróty klawiszowe",
        "documentation": "📖 Dokumentacja",
        "check_updates": "🔄 Sprawdź aktualizacje",
        "report_bug": "🐛 Zgłoś błąd",
        "getting_started": "Rozpoczęcie pracy",
        "features": "Funkcje",
        "file_structure": "Struktura plików",
        "credits": "Autorzy",
        "license": "Licencja",
        "github": "GitHub",
        "discord": "Discord",
        "donate": "Wspomóż",
        
        # === RAPORT BŁĘDU ===
        "bug_report_info": "Znalazłeś błąd? Podaj szczegóły poniżej.\nLogi debugowania zostaną automatycznie dołączone.",
        "description": "Opis",
        "email_optional": "Email (opcjonalnie)",
        "copy_report_clipboard": "Kopiuj raport do schowka",
        "open_github_issues": "Otwórz GitHub Issues",
        "bug_report_copied": "Raport błędu skopiowany do schowka!",
        
        # === PODPOWIEDZI ===
        "has_audio_file": "Ma plik audio",
        "no_audio_file": "Brak pliku audio",
        
        # === O PROGRAMIE ===
        "about_description": "Narzędzie do zarządzania plikami audio WEM i napisami gry dla Outlast Trials, zaprojektowane dla moddersów i zespołów lokalizacyjnych.",
        "key_features": "Kluczowe funkcje",
        "audio_management": "🎵 <b>Zarządzanie audio:</b> Odtwarzanie, konwersja i organizacja plików WEM",
        "subtitle_editing": "📝 <b>Edycja napisów:</b> Łatwa edycja z rozwiązywaniem konfliktów",
        "mod_creation": "📦 <b>Tworzenie modów:</b> Kompilacja i wdrażanie modów jednym kliknięciem",
        "multi_language": "🌍 <b>Wielojęzyczność:</b> Wsparcie dla 14+ języków",
        "modern_ui": "🎨 <b>Nowoczesny interfejs:</b> Czysty interfejs z ciemnymi/jasnymi motywami",
        "technology_stack": "Stos technologiczny",
        "built_with": "Zbudowane z Python 3 i PyQt5, wykorzystując:",
        "unreal_locres_tool": "UnrealLocres do obsługi plików .locres",
        "vgmstream_tool": "vgmstream do konwersji audio",
        "repak_tool": "repak do pakowania modów",
        "development_team": "Zespół deweloperski",
        "lead_developer": "<b>Główny deweloper:</b> Bezna",
        "special_thanks": "Specjalne podziękowania",
        "vgmstream_thanks": "Zespół vgmstream - Za narzędzia konwersji audio",
        "unreal_locres_thanks": "Deweloperzy UnrealLocres - Za wsparcie lokalizacji",
        "hypermetric_thanks": "hypermetric - Za pakowanie modów",
        "red_barrels_thanks": "Red Barrels - Za stworzenie Outlast Trials",
        "open_source_libraries": "Biblioteki open source",
        "pyqt5_lib": "PyQt5 - GUI Framework",
        "python_lib": "Standardowa biblioteka Python",
        "software_disclaimer": "To oprogramowanie jest dostarczane \"jak jest\" bez żadnych gwarancji. Używaj na własne ryzyko.",
        "license_agreement": "Umowa licencyjna",
        "copyright_notice": "Copyright (c) 2025 OutlastTrials AudioEditor",
        "mit_license_text": "Niniejszym udziela się bezpłatnego zezwolenia każdej osobie uzyskującej kopię tego oprogramowania i powiązanych plików dokumentacji (\"Oprogramowanie\") na nieograniczone korzystanie z Oprogramowania, w tym bez ograniczeń prawami do używania, kopiowania, modyfikowania, łączenia, publikowania, dystrybucji, sublicencjonowania i/lub sprzedaży kopii Oprogramowania, oraz zezwalania osobom, którym Oprogramowanie jest dostarczone, na takie działania, pod warunkiem spełnienia następujących warunków:\n\nPowyższa informacja o prawach autorskich i niniejsza informacja o zezwoleniu muszą być zawarte we wszystkich kopiach lub istotnych częściach Oprogramowania.\n\nOPROGRAMOWANIE JEST DOSTARCZANE \"JAK JEST\", BEZ JAKICHKOLWIEK GWARANCJI, WYRAŹNYCH LUB DOROZUMIANYCH, W TYM GWARANCJI PRZYDATNOŚCI HANDLOWEJ, PRZYDATNOŚCI DO OKREŚLONEGO CELU I NIENARUSZANIA PRAW. W ŻADNYM PRZYPADKU AUTORZY LUB POSIADACZE PRAW AUTORSKICH NIE PONOSZĄ ODPOWIEDZIALNOŚCI ZA JAKIEKOLWIEK ROSZCZENIA, SZKODY LUB INNE ZOBOWIĄZANIA, CZY TO W RAMACH UMOWY, DELIKTU CZY W INNY SPOSÓB, WYNIKAJĄCE Z LUB W ZWIĄZKU Z OPROGRAMOWANIEM LUB UŻYTKOWANIEM LUB INNYMI DZIAŁANIAMI W OPROGRAMOWANIU.",
        
        # === SKRÓTY KLAWISZOWE ===
        "shortcuts_table_action": "Akcja",
        "shortcuts_table_shortcut": "Skrót",
        "shortcuts_table_description": "Opis",
        "shortcut_edit_subtitle": "Edytuj napisy",
        "shortcut_save_subtitles": "Zapisz napisy",
        "shortcut_export_audio": "Eksport audio",
        "shortcut_revert_original": "Przywróć do oryginału",
        "shortcut_deploy_run": "Wdróż i uruchom",
        "shortcut_debug_console": "Konsola debugowania",
        "shortcut_settings": "Ustawienia",
        "shortcut_documentation": "Dokumentacja",
        "shortcut_exit": "Wyjście",
        "shortcut_edit_selected": "Edytuj wybrany napis",
        "shortcut_save_all_changes": "Zapisz wszystkie zmiany napisów",
        "shortcut_export_selected": "Eksportuj wybrane audio jako WAV",
        "shortcut_revert_selected": "Przywróć wybrany napis do oryginału",
        "shortcut_deploy_launch": "Wdróż mod i uruchom grę",
        "shortcut_show_debug": "Pokaż konsolę debugowania",
        "shortcut_open_settings": "Otwórz dialog ustawień",
        "shortcut_show_help": "Pokaż dokumentację",
        "shortcut_close_app": "Zamknij aplikację",
        "mouse_actions": "Akcje myszy",
        "mouse_double_subtitle": "<b>Podwójne kliknięcie napisu:</b> Edytuj napis",
        "mouse_double_file": "<b>Podwójne kliknięcie pliku:</b> Odtwórz audio",
        "mouse_right_click": "<b>Prawy klik:</b> Pokaż menu kontekstowe"
    }
}
class DebugLogger:
    def __init__(self):
        self.logs = []
        self.callbacks = []
        self.settings = None
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry) 
        
        for callback in self.callbacks:
            callback(log_entry)
            
    def add_callback(self, callback):
        self.callbacks.append(callback)
        
    def get_logs(self):
        return "\n".join(self.logs)

DEBUG = DebugLogger()

class DebugWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Console")
        self.setMinimumSize(800, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Controls
        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        
        self.auto_scroll = QtWidgets.QCheckBox("Auto-scroll")
        self.auto_scroll.setChecked(True)
        
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        
        save_btn = QtWidgets.QPushButton("Save Log")
        save_btn.clicked.connect(self.save_log)
        
        controls_layout.addWidget(self.auto_scroll)
        controls_layout.addStretch()
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(save_btn)
        
        layout.addWidget(controls)
        
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(self.log_display)
        
        self.log_display.setPlainText(DEBUG.get_logs())
        
        DEBUG.add_callback(self.append_log)
        
    def append_log(self, log_entry):
        self.log_display.append(log_entry)
        if self.auto_scroll.isChecked():
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def clear_logs(self):
        self.log_display.clear()
        DEBUG.logs.clear()
        
    def save_log(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Debug Log", 
            f"wem_subtitle_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Log Files (*.log)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(DEBUG.get_logs())

class ModernButton(QtWidgets.QPushButton):
    def __init__(self, text="", icon=None, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setProperty("primary", primary)
        if icon:
            self.setIcon(QtGui.QIcon(icon))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMinimumHeight(36)
class WEMAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.sample_rate = 0
        self.channels = 0
        self.cue_points = []
        self.labels = {}
        
    def read_chunk_header(self, file):
  
        chunk_id = file.read(4)
        if len(chunk_id) < 4:
            return None, 0
        chunk_size = struct.unpack('<I', file.read(4))[0]
        return chunk_id.decode('ascii', errors='ignore'), chunk_size
    
    def parse_fmt_chunk(self, file, size):
   
        fmt_data = file.read(size)
        
        if len(fmt_data) < 8:
            return
            
        audio_format = struct.unpack('<H', fmt_data[0:2])[0]
        self.channels = struct.unpack('<H', fmt_data[2:4])[0]
        self.sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
        

        DEBUG.log(f"Audio format: 0x{audio_format:04X}")
        DEBUG.log(f"Channels: {self.channels}")
        DEBUG.log(f"Sample rate: {self.sample_rate} Hz")
    def parse_cue_chunk(self, file, size):
        
        cue_data = file.read(size)
        
        num_cues = struct.unpack('<I', cue_data[0:4])[0]
        offset = 4
        
        for i in range(num_cues):
            if offset + 24 <= len(cue_data):
                cue_id = struct.unpack('<I', cue_data[offset:offset+4])[0]
                position = struct.unpack('<I', cue_data[offset+4:offset+8])[0]
                chunk_id = cue_data[offset+8:offset+12].decode('ascii', errors='ignore').rstrip('\x00')
                chunk_start = struct.unpack('<I', cue_data[offset+12:offset+16])[0]
                block_start = struct.unpack('<I', cue_data[offset+16:offset+20])[0]
                sample_offset = struct.unpack('<I', cue_data[offset+20:offset+24])[0]
                
                cue_point = CuePoint(cue_id, position, chunk_id, chunk_start, block_start, sample_offset)
                self.cue_points.append(cue_point)
                offset += 24
    
    def parse_list_chunk(self, file, size):
     
        list_data = file.read(size)
        
        if len(list_data) < 4:
            return
            
        list_type = list_data[0:4].decode('ascii', errors='ignore')
        
        if list_type == 'adtl':  # Associated Data List
            offset = 4
            while offset < len(list_data):
                if offset + 8 > len(list_data):
                    break
                    
                sub_chunk_id = list_data[offset:offset+4].decode('ascii', errors='ignore')
                sub_chunk_size = struct.unpack('<I', list_data[offset+4:offset+8])[0]
                
                if sub_chunk_id == 'labl' and offset + 8 + sub_chunk_size <= len(list_data):
                   
                    cue_id = struct.unpack('<I', list_data[offset+8:offset+12])[0]
                    
                    label_data = list_data[offset+12:offset+8+sub_chunk_size]
                    
                    
                    try:
                        label_text = label_data.decode('ascii', errors='ignore').rstrip('\x00')
                     
                        label_text = ''.join(char for char in label_text if char.isprintable() or char.isspace())
                        label_text = label_text.strip()
                        
                        if label_text:
                            self.labels[cue_id] = label_text
                            DEBUG.log(f"Found label ID {cue_id}: '{label_text}'")
                            
                    except Exception as e:
                        DEBUG.log(f"Error decoding label for cue {cue_id}: {e}", "ERROR")
                
              
                offset += 8 + sub_chunk_size
                if sub_chunk_size % 2 == 1:
                    offset += 1
    def analyze(self):

        try:
            with open(self.filename, 'rb') as f:
                riff_id = f.read(4)
                if riff_id != b'RIFF':
                    DEBUG.log(f"Not a RIFF file: {self.filename}", "ERROR")
                    return False
                
                file_size = struct.unpack('<I', f.read(4))[0]
                wave_id = f.read(4)
                
                if wave_id != b'WAVE':
                    DEBUG.log(f"Not a WAVE file: {self.filename}", "ERROR")
                    return False
                
                DEBUG.log(f"Analyzing WEM file: {os.path.basename(self.filename)} (size: {file_size + 8} bytes)")
                
                while f.tell() < file_size + 8:
                    chunk_id, chunk_size = self.read_chunk_header(f)
                    if chunk_id is None:
                        break
                    
                    current_pos = f.tell()
                    
                    if chunk_id == 'fmt ':
                        self.parse_fmt_chunk(f, chunk_size)
                    elif chunk_id == 'cue ':
                        self.parse_cue_chunk(f, chunk_size)
                    elif chunk_id == 'LIST':
                        self.parse_list_chunk(f, chunk_size)
                    else:
                        f.seek(current_pos + chunk_size)
                    
                    if chunk_size % 2 == 1:
                        f.read(1)
                
           
                DEBUG.log(f"Final analysis result:")
                DEBUG.log(f"  Sample rate: {self.sample_rate} Hz")
                DEBUG.log(f"  Channels: {self.channels}")
                DEBUG.log(f"  Cue points: {len(self.cue_points)}")
                DEBUG.log(f"  Labels: {len(self.labels)}")
                
          
                for cue in self.cue_points:
                    if self.sample_rate > 0:
                        calc_time = cue.position / self.sample_rate
                        DEBUG.log(f"  Cue {cue.id}: {cue.position} samples = {calc_time:.3f} seconds")
                
                return True
                
        except Exception as e:
            DEBUG.log(f"Error analyzing WEM file {self.filename}: {e}", "ERROR")
            return False
    def get_markers_info(self):
     
        markers = []
        
 
        sorted_cues = sorted(self.cue_points, key=lambda x: x.position)
        
        DEBUG.log(f"Processing {len(sorted_cues)} cue points with sample rate {self.sample_rate}")
        
        for cue in sorted_cues:
       
            time_seconds = 0.0
            if self.sample_rate > 0:
                time_seconds = float(cue.position) / float(self.sample_rate)
            
           
            label = self.labels.get(cue.id, "")
            
            marker_info = {
                'id': cue.id,
                'position': cue.position,
                'time_seconds': time_seconds,
                'label': label
            }
            markers.append(marker_info)
            
            DEBUG.log(f"Marker {cue.id}: pos={cue.position} samples, time={time_seconds:.3f}s, label='{label}'")
        
        return markers
class SearchBar(QtWidgets.QWidget):
    searchChanged = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_icon = QtWidgets.QLabel("🔍")
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.clear_btn = QtWidgets.QPushButton("✕")
        self.clear_btn.setMaximumWidth(30)
        self.clear_btn.hide()
        
        layout.addWidget(self.search_icon)
        layout.addWidget(self.search_input)
        layout.addWidget(self.clear_btn)
        
        self.search_input.textChanged.connect(self._on_text_changed)
        self.clear_btn.clicked.connect(self.clear)
        
    def _on_text_changed(self, text):
        self.clear_btn.setVisible(bool(text))
        self.searchChanged.emit(text)
        
    def clear(self):
        self.search_input.clear()
        
    def text(self):
        return self.search_input.text()

class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        self.label = QtWidgets.QLabel("Please wait...")
        self.progress = QtWidgets.QProgressBar()
        self.details = QtWidgets.QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(100)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.details)
        
    def set_progress(self, value, text=""):
        self.progress.setValue(value)
        if text:
            self.label.setText(text)
            
    def append_details(self, text):
        self.details.append(text)

class SubtitleLoaderThread(QtCore.QThread):

    dataLoaded = QtCore.pyqtSignal(dict) 
    statusUpdate = QtCore.pyqtSignal(str) 
    progressUpdate = QtCore.pyqtSignal(int) 
    
    def __init__(self, parent, all_subtitle_files, locres_manager, subtitles, original_subtitles, 
                 selected_lang, selected_category, orphaned_only, modified_only, with_audio_only, 
                 search_text, audio_keys_cache, modified_subtitles):
        super().__init__(parent)
        self.all_subtitle_files = all_subtitle_files
        self.locres_manager = locres_manager
        self.subtitles = subtitles
        self.original_subtitles = original_subtitles
        self.selected_lang = selected_lang
        self.selected_category = selected_category
        self.orphaned_only = orphaned_only
        self.modified_only = modified_only
        self.with_audio_only = with_audio_only
        self.search_text = search_text.lower().strip()
        self.audio_keys_cache = audio_keys_cache
        self.modified_subtitles = modified_subtitles
        self._should_stop = False
        
    def stop(self):
        self._should_stop = True
    def run(self):
        try:
            subtitles_to_show = {}
            files_processed = 0

            relevant_files = []
            for key, file_info in self.all_subtitle_files.items():
           
                lang_match = (self.selected_lang == "All Languages" or 
                            file_info.get('language') == self.selected_lang)
                
                category_match = (self.selected_category == "All Categories" or 
                                file_info.get('category') == self.selected_category)
                
                if lang_match and category_match:
                    relevant_files.append((key, file_info))
            
            total_files = len(relevant_files)
            
            if total_files == 0:
                self.dataLoaded.emit({})
                return

            for i, (key, file_info) in enumerate(relevant_files):
                if self._should_stop:
                    return
                    
                progress = int((i / total_files) * 70) 
                self.progressUpdate.emit(progress)
                self.statusUpdate.emit(f"Processing {file_info['filename']}...")
                
                try:
                    file_subtitles = self.locres_manager.export_locres(file_info['path'])
                    files_processed += 1
                    
                    for sub_key, sub_value in file_subtitles.items():
                        if self._should_stop:
                            return

                        has_audio = sub_key in self.audio_keys_cache if self.audio_keys_cache else False
                        
                        if self.orphaned_only and has_audio:
                            continue
                        
                        if self.with_audio_only and not has_audio:
                            continue

                        current_text = self.subtitles.get(sub_key, sub_value)
                        is_modified = sub_key in self.modified_subtitles
                        
                        if self.modified_only and not is_modified:
                            continue

                        if self.search_text:
                            if (self.search_text not in sub_key.lower() and 
                                self.search_text not in sub_value.lower() and
                                self.search_text not in current_text.lower()):
                                continue
                        
                        subtitles_to_show[sub_key] = {
                            'original': sub_value,
                            'current': current_text,
                            'file_info': file_info,
                            'has_audio': has_audio,
                            'is_modified': is_modified
                        }
                        
                except Exception as e:
                    DEBUG.log(f"Error loading subtitles from {file_info['path']}: {e}", "ERROR")
            
            self.progressUpdate.emit(80)
            self.statusUpdate.emit("Processing additional subtitles...")

      
            for sub_key, sub_value in self.subtitles.items():
                if self._should_stop:
                    return
                    
                if sub_key not in subtitles_to_show:
                    has_audio = sub_key in self.audio_keys_cache if self.audio_keys_cache else False
                    
                    if self.orphaned_only and has_audio:
                        continue
                    
                    if self.with_audio_only and not has_audio:
                        continue
                    
                    is_modified = sub_key in self.modified_subtitles
                    
                    if self.modified_only and not is_modified:
                        continue
                    
                    if self.search_text:
                        original_text = self.original_subtitles.get(sub_key, "")
                        if (self.search_text not in sub_key.lower() and 
                            self.search_text not in sub_value.lower() and
                            self.search_text not in original_text.lower()):
                            continue
                    
                    if self.selected_category != "All Categories" or self.selected_lang != "All Languages":
  
                        continue
                    
                    subtitles_to_show[sub_key] = {
                        'original': self.original_subtitles.get(sub_key, ""),
                        'current': sub_value,
                        'file_info': None,
                        'has_audio': has_audio,
                        'is_modified': is_modified
                    }
            
            self.progressUpdate.emit(100)
            self.statusUpdate.emit(f"Loaded {len(subtitles_to_show)} subtitles from {files_processed} files")
            
            if not self._should_stop:
                self.dataLoaded.emit(subtitles_to_show)
                
        except Exception as e:
            DEBUG.log(f"Error in subtitle loader thread: {e}", "ERROR")
            self.dataLoaded.emit({})        
class UnrealLocresManager:
    """Manager for UnrealLocres.exe operations with debug logging"""
    
    def __init__(self, unreal_locres_path):
        self.unreal_locres_path = unreal_locres_path
        if not os.path.isabs(self.unreal_locres_path):
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            self.unreal_locres_path = os.path.join(base_path, self.unreal_locres_path)
        DEBUG.log(f"UnrealLocresManager initialized with path: {self.unreal_locres_path}")
        
    def export_locres(self, locres_path):
        """Export locres file to CSV and return subtitle data"""
        DEBUG.log(f"Starting export_locres for: {locres_path}")
        subtitles = {}
        
        try:
            if not os.path.exists(locres_path):
                DEBUG.log(f"ERROR: Locres file not found: {locres_path}", "ERROR")
                return subtitles
                
            DEBUG.log(f"Locres file size: {os.path.getsize(locres_path)} bytes")
            
            if not os.path.exists(self.unreal_locres_path):
                DEBUG.log(f"ERROR: UnrealLocres.exe not found at: {self.unreal_locres_path}", "ERROR")
                return subtitles

            cmd = [self.unreal_locres_path, "export", locres_path]
            DEBUG.log(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.unreal_locres_path) or ".",
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            DEBUG.log(f"Command return code: {result.returncode}")
            if result.stdout:
                DEBUG.log(f"Command stdout: {result.stdout}")
            if result.stderr:
                DEBUG.log(f"Command stderr: {result.stderr}", "WARNING")
            
            if result.returncode != 0:
                DEBUG.log(f"UnrealLocres export failed with code {result.returncode}", "ERROR")
                return subtitles
                
            csv_filename = os.path.basename(locres_path).replace('.locres', '.csv')
            csv_path = os.path.join(os.path.dirname(self.unreal_locres_path) or ".", csv_filename)
            
            DEBUG.log(f"Looking for CSV at: {csv_path}")
            
            import time
            for i in range(10):
                if os.path.exists(csv_path):
                    break
                time.sleep(0.1)
            
            if not os.path.exists(csv_path):
                alt_paths = [
                    os.path.join(".", csv_filename),
                    os.path.join(os.path.dirname(locres_path), csv_filename),
                    csv_filename
                ]
                
                for alt_path in alt_paths:
                    DEBUG.log(f"Trying alternative CSV path: {alt_path}")
                    if os.path.exists(alt_path):
                        csv_path = alt_path
                        break
                        
                if not os.path.exists(csv_path):
                    DEBUG.log(f"ERROR: CSV file not found after trying all paths", "ERROR")
                    return subtitles
                    
            DEBUG.log(f"Found CSV file at: {csv_path}")
            DEBUG.log(f"CSV file size: {os.path.getsize(csv_path)} bytes")

            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                DEBUG.log(f"CSV content preview (first 500 chars): {content[:500]}")

                f.seek(0)
                reader = csv.reader(f)
                row_count = 0
                subtitle_count = 0
                
                header = next(reader, None)
                if header:
                    DEBUG.log(f"CSV Header: {header}")
                
                for row in reader:
                    row_count += 1
                    if len(row) >= 2:
                        key = row[0].strip()
                        value = row[1].strip()

                        if row_count <= 5:
                            DEBUG.log(f"CSV Row {row_count}: key='{key}', value='{value[:50]}...'")

                        if key and value:
  
                            if key.startswith('Subtitles/'):

                                clean_key = key[10:] 
                            else:
                           
                                clean_key = key.lstrip('/')
                            
                            subtitles[clean_key] = value
                            subtitle_count += 1

                            if subtitle_count <= 3:
                                DEBUG.log(f"Found subtitle: {clean_key} = {value[:50]}...")
                                
                DEBUG.log(f"Total CSV rows processed: {row_count}")
                DEBUG.log(f"Total subtitles found: {subtitle_count}")

            try:
                os.remove(csv_path)
                DEBUG.log(f"Cleaned up CSV file: {csv_path}")
            except Exception as e:
                DEBUG.log(f"Failed to clean up CSV: {e}", "WARNING")
                
        except Exception as e:
            DEBUG.log(f"ERROR in export_locres: {str(e)}", "ERROR")
            DEBUG.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            
        DEBUG.log(f"export_locres completed, returning {len(subtitles)} subtitles")
        return subtitles
    def import_locres(self, locres_path, subtitles):
        """Import subtitle data to locres file"""
        DEBUG.log(f"Starting import_locres for: {locres_path}")
        DEBUG.log(f"Importing {len(subtitles)} subtitles")
        
        try:
            csv_filename = os.path.basename(locres_path).replace('.locres', '.csv')
            csv_path = os.path.join(os.path.dirname(self.unreal_locres_path) or ".", csv_filename)
            
            DEBUG.log(f"Exporting current locres to get all data...")
            
            result = subprocess.run(
                [self.unreal_locres_path, "export", locres_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.unreal_locres_path) or ".",
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                DEBUG.log(f"Export failed: {result.stderr}", "ERROR")
                raise Exception(f"Export failed: {result.stderr}")
                
            import time
            for i in range(10):
                if os.path.exists(csv_path):
                    break
                time.sleep(0.1)
                
            if not os.path.exists(csv_path):
                DEBUG.log(f"CSV not found at: {csv_path}", "ERROR")
                raise Exception("CSV file not created")
                
            DEBUG.log(f"Reading CSV from: {csv_path}")

            original_rows = []
            key_to_original = {}
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    original_rows.append(row)
                    if len(row) >= 2: 
                        key = row[0].strip()
                        
                  
                        clean_key = None
                        if key.startswith('Subtitles/'):
                            clean_key = key.replace('Subtitles/', '')
                        elif key.startswith('/'):
                            clean_key = key[1:] 
                        else:
                            clean_key = key
                        
                        key_to_original[clean_key] = row[1] if len(row) >= 2 else ""
                        
            DEBUG.log(f"Found {len(key_to_original)} VO entries in original CSV")

            rows = []
            translated_count = 0
            
            for row in original_rows:
                if len(row) >= 2:  
                    key = row[0].strip()

                    clean_key = None
                    if key.startswith('Subtitles/'):
                        clean_key = key.replace('Subtitles/', '')
                    elif key.startswith('/'):
                        clean_key = key[1:]
                    else:
                        clean_key = key
                    
                    if clean_key and clean_key in subtitles:
                        original_text = row[1] if len(row) >= 2 else ""
                        translated_text = subtitles[clean_key]
                        
                        new_row = [row[0], original_text, translated_text]
                        rows.append(new_row)
                        translated_count += 1
                        
                        if translated_count <= 5:
                            DEBUG.log(f"Translation row {translated_count}:")
                            DEBUG.log(f"  Key: {row[0]}")
                            DEBUG.log(f"  Original: {original_text[:50]}...")
                            DEBUG.log(f"  Translation: {translated_text[:50]}...")
                    else:
                        rows.append(row)
                else:
                    rows.append(row)     
            new_count = 0
            for key, value in subtitles.items():
                if key not in key_to_original: 
                    
                    if rows and len(rows) > 0:
                        sample_key = None
                        for row in rows:
                            if len(row) >= 1:
                                sample_key = row[0]
                                break
                        
                        if sample_key:
                            if sample_key.startswith('Subtitles/'):
                                formatted_key = f"Subtitles/{key}"
                            elif sample_key.startswith('/'):
                                formatted_key = f"/{key}"
                            else:
                                formatted_key = key
                        else:
                            formatted_key = f"/{key}" if not key.startswith('/') else key
                    else:
                        formatted_key = f"/{key}" if not key.startswith('/') else key

                    rows.append([formatted_key, "", value])
                    new_count += 1
                    
                    if new_count <= 5:
                        DEBUG.log(f"New entry {new_count}: {formatted_key} = {value[:50]}...")
                        
            DEBUG.log(f"Total rows with translations: {translated_count}")
            DEBUG.log(f"New entries added: {new_count}")
            DEBUG.log(f"Total rows in CSV: {len(rows)}")
            
            DEBUG.log(f"Writing CSV to: {csv_path}")
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
                
            DEBUG.log("Sample of CSV content (first 10 translation rows):")
            translation_rows_shown = 0
            for row in rows:
                if len(row) >= 3 and 'VO_' in row[0] and row[2]: 
                    DEBUG.log(f"  {row[0]} | {row[1][:30]}... | {row[2][:30]}...")
                    translation_rows_shown += 1
                    if translation_rows_shown >= 10:
                        break

            DEBUG.log("Importing CSV back to locres...")
            cmd = [self.unreal_locres_path, "import", locres_path, csv_path]
            DEBUG.log(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.unreal_locres_path) or ".",
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            DEBUG.log(f"Import return code: {result.returncode}")
            if result.stdout:
                DEBUG.log(f"Import stdout: {result.stdout}")
            if result.stderr:
                DEBUG.log(f"Import stderr: {result.stderr}", "WARNING")
            
            if result.returncode != 0:
                raise Exception(f"Import failed: {result.stderr}")
                
            new_file_path = f"{locres_path}.new"
            DEBUG.log(f"Checking for new file at: {new_file_path}")
            
            for i in range(10):
                if os.path.exists(new_file_path):
                    break
                time.sleep(0.1)
                
            if os.path.exists(new_file_path):
                DEBUG.log(f"Found .new file, renaming...")
                try:
                    if os.path.exists(locres_path):
                        os.remove(locres_path)
                    os.rename(new_file_path, locres_path)
                    DEBUG.log("Successfully renamed .new file")
                except Exception as e:
                    DEBUG.log(f"Error renaming .new file: {e}", "ERROR")
                    raise
            else:
                DEBUG.log("No .new file found, assuming in-place update", "WARNING")

            try:
                os.remove(csv_path)
                DEBUG.log("Cleaned up CSV file")
            except:
                pass
                
            DEBUG.log("import_locres completed successfully")
            return True
            
        except Exception as e:
            DEBUG.log(f"ERROR in import_locres: {str(e)}", "ERROR")
            DEBUG.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False

class AppSettings:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.path = os.path.join(base_path, "config.json")
        
        self.data = {
            "ui_language": "en",
            "theme": "light", 
            "subtitle_lang": "en",
            "last_directory": "",
            "window_geometry": None,
            "auto_save": True,
            "show_tooltips": True,
            "debug_mode": False,
            "game_path": "",
            "wem_process_language": "english"
        }
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.data.update(loaded_data)
        except Exception as e:
            self.save()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            DEBUG.log(f"Failed to save settings: {e}", "ERROR")

class AudioPlayer(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal(int)
    positionChanged = QtCore.pyqtSignal(int)
    durationChanged = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.player = QtMultimedia.QMediaPlayer()
        self.player.stateChanged.connect(self.stateChanged.emit)
        self.player.positionChanged.connect(self.positionChanged.emit)
        self.player.durationChanged.connect(self.durationChanged.emit)
        
    def play(self, filepath):
        url = QtCore.QUrl.fromLocalFile(filepath)
        content = QtMultimedia.QMediaContent(url)
        self.player.setMedia(content)
        self.player.play()
        
    def stop(self):
        self.player.stop()
        
    def pause(self):
        self.player.pause()
        
    def resume(self):
        self.player.play()
        
    def set_position(self, position):
        self.player.setPosition(position)
        
    @property
    def is_playing(self):
        return self.player.state() == QtMultimedia.QMediaPlayer.PlayingState
class WavToWemConverter(QtCore.QObject):
    progress_updated = QtCore.pyqtSignal(int)
    status_updated = QtCore.pyqtSignal(str, str) 
    conversion_finished = QtCore.pyqtSignal(list)
    
    SUPPORTED_SAMPLE_RATES = [48000, 44100, 36000, 32000, 28000, 24000, 22050, 
                              20000, 18000, 16000, 14000, 12000, 11025, 10000, 8000, 6000]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_pairs = []
        self.should_stop = False
        self.parent = parent
        self.wwise_path = ""
        self.project_path = ""
        self.output_folder = ""
        self.conversion_cache = {}
        self.adaptive_mode = False  
         
    def reset_state(self):
        """Reset converter state after stop or error"""
        self.should_stop = False
        self.status_updated.emit("Ready", "green")
        
        # IMPORTANT: Clear conversion cache
        self.conversion_cache.clear()
        DEBUG.log("Conversion cache cleared")
        
        # Clean up any temporary files
        if self.output_folder and os.path.exists(self.output_folder):
            try:
                for file in os.listdir(self.output_folder):
                    if file.startswith("temp_") or file.startswith("best_") or file.startswith("test_"):
                        temp_file = os.path.join(self.output_folder, file)
                        try:
                            os.remove(temp_file)
                            DEBUG.log(f"Cleaned up temp file: {file}")
                        except:
                            pass
            except Exception as e:
                DEBUG.log(f"Error cleaning temp files: {e}", "WARNING")
        
        # Clean up temp conversion directories
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(script_dir, "temp_conversion")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                DEBUG.log("Cleaned up temp_conversion directory")
            except Exception as e:
                DEBUG.log(f"Error cleaning temp_conversion: {e}", "WARNING")
    def set_adaptive_mode(self, enabled):
        """Enable or disable adaptive conversion mode"""
        self.adaptive_mode = enabled
        
    def set_paths(self, wwise_path, project_path, output_folder):
        self.wwise_path = wwise_path
        self.project_path = project_path
        self.output_folder = output_folder
        self.conversion_cache.clear()
    def add_file_pair(self, wav_file, target_wem):
        if not os.path.exists(wav_file) or not os.path.exists(target_wem):
            return False
            
        file_pair = {
            "wav_file": wav_file,
            "target_wem": target_wem,
            "wav_name": os.path.basename(wav_file),
            "target_name": os.path.basename(target_wem),
            "target_size": os.path.getsize(target_wem)
        }
        
        self.file_pairs.append(file_pair)
        return True
        
    def clear_file_pairs(self):
        self.file_pairs.clear()
        
    def ensure_project_exists(self):
        
        if not self.wwise_path or not self.project_path:
            raise Exception("Please specify Wwise path and project path")
            
        project_dir = os.path.normpath(self.project_path)
        project_name = os.path.basename(project_dir)
        wproj_path = os.path.normpath(os.path.join(project_dir, f"{project_name}.wproj"))
        
        if os.path.exists(wproj_path):
            self.create_default_work_unit(project_dir)
            return wproj_path
            
        self.status_updated.emit("Creating Wwise project...", "blue")
        
        wwisecli_path = os.path.normpath(os.path.join(
            self.wwise_path, "Authoring", "x64", "Release", "bin", "WwiseCLI.exe"
        ))
        
        if not os.path.exists(wwisecli_path):
            raise FileNotFoundError(f"WwiseCLI.exe not found at: {wwisecli_path}")
        
        
        
        cmd = [
            wwisecli_path, f'"{wproj_path}"', "-CreateNewProject",
            "-Platform", "Windows", "-Quiet"
        ]
        os.removedirs(project_dir)
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False, creationflags=CREATE_NO_WINDOW)
        
        if result.returncode != 0:
            raise Exception(f"Failed to create project: {result.stderr}")
        
        self.create_default_work_unit(project_dir)
        return wproj_path
        
    
    def create_default_work_unit(self, project_dir):
        """Create default work unit in project directory"""
        conversion_settings_dir = os.path.join(project_dir, "Conversion Settings")
        os.makedirs(conversion_settings_dir, exist_ok=True)
        
        project_wwu_path = os.path.join(conversion_settings_dir, "Default Work Unit.wwu")
        
        if os.path.exists(project_wwu_path):
            try:
                os.remove(project_wwu_path)
                DEBUG.log(f"Deleted existing work unit file: {project_wwu_path}")
            except Exception as e:
                DEBUG.log(f"Error deleting existing work unit file: {e}", "ERROR")
        

        if getattr(sys, 'frozen', False):

            base_dir = os.path.dirname(sys.executable)
        else:
     
            base_dir = os.path.dirname(os.path.abspath(__file__))

        data_wwu_path = os.path.join(base_dir, "data", "Default Work Unit.wwu")
        
        DEBUG.log(f"Base directory: {base_dir}") 
        DEBUG.log(f"Looking for work unit file at: {data_wwu_path}") 
        
        if os.path.exists(data_wwu_path):
            shutil.copy2(data_wwu_path, project_wwu_path)
            DEBUG.log(f"Copied work unit file from data to project")
        else:
            DEBUG.log(f"Work unit file not found in data directory: {data_wwu_path}", "ERROR")
            
    def resample_wav_file(self, input_wav, output_wav, target_sample_rate):
        """Resample WAV file to target sample rate using simple Python audio libraries"""
        try:
            import wave
            import struct
            import array
            
            with wave.open(input_wav, 'rb') as wav_in:
                params = wav_in.getparams()
                frames = wav_in.readframes(params.nframes)
                
                original_rate = params.framerate
                
                if original_rate == target_sample_rate:
              
                    shutil.copy2(input_wav, output_wav)
                    return True
                

                if params.sampwidth == 1:
                    fmt = 'B' 
                    samples = array.array(fmt, frames)
                elif params.sampwidth == 2:
                    fmt = 'h'  
                    samples = array.array(fmt, frames)
                elif params.sampwidth == 4:
                    fmt = 'i'  
                    samples = array.array(fmt, frames)
                else:
               
                    shutil.copy2(input_wav, output_wav)
                    return False
                
      
                ratio = target_sample_rate / original_rate
                new_length = int(len(samples) * ratio / params.nchannels) * params.nchannels
                
               
                resampled = array.array(fmt)
                
                for i in range(new_length):
                
                    orig_pos = i / ratio
                    orig_idx = int(orig_pos)
                    
                    if orig_idx < len(samples) - 1:
           
                        frac = orig_pos - orig_idx
                        val = samples[orig_idx] * (1 - frac) + samples[orig_idx + 1] * frac
                        resampled.append(int(val))
                    elif orig_idx < len(samples):
                        resampled.append(samples[orig_idx])
                    else:
                        resampled.append(0)
                
                with wave.open(output_wav, 'wb') as wav_out:
                    wav_out.setparams((
                        params.nchannels,
                        params.sampwidth,
                        target_sample_rate,
                        len(resampled) // params.nchannels,
                        params.comptype,
                        params.compname
                    ))
                    wav_out.writeframes(resampled.tobytes())
                
                return True
                
        except Exception as e:
            DEBUG.log(f"Resampling error: {e}", "ERROR")

            shutil.copy2(input_wav, output_wav)
            return False
            
    def create_wsources_file(self, path, wav_file, conversion_value=10):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wav_path = os.path.normpath(wav_file)
        
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<ExternalSourcesList SchemaVersion="1" Root="{script_dir}">
    <Source Path="{wav_path}" Conversion="{conversion_value}"/>
</ExternalSourcesList>'''
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
            
    def convert_with_quality(self, wav_file, conversion_value):
        """Convert with detailed size logging"""
        cache_key = f"{wav_file}_{conversion_value}"
        if cache_key in self.conversion_cache:
            cached_result = self.conversion_cache[cache_key]
            DEBUG.log(f"Using cached result for Conversion={conversion_value}: {cached_result['size']:,} bytes")
            return cached_result
            
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(script_dir, "temp_conversion")
        os.makedirs(temp_dir, exist_ok=True)
        
        data_dir = os.path.join(script_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        wsources_path = os.path.join(data_dir, "convert.wsources")
        
        wav_size = os.path.getsize(wav_file)
        wav_name = os.path.basename(wav_file)
        DEBUG.log(f"Converting {wav_name} (input size: {wav_size:,} bytes) with Conversion={conversion_value}")
     
        if hasattr(self.parent, 'append_conversion_log'):
            self.parent.append_conversion_log(f"  → Testing Conversion={conversion_value} for {wav_name} (input: {wav_size:,} bytes)")
        
        self.create_wsources_file(wsources_path, wav_file, conversion_value)
        
        wwisecli_path = os.path.normpath(os.path.join(
            self.wwise_path, "Authoring", "x64", "Release", "bin", "WwiseCLI.exe"
        ))
        
        project_dir = os.path.normpath(self.project_path)
        project_name = os.path.basename(project_dir)
        wproj_path = os.path.normpath(os.path.join(project_dir, f"{project_name}.wproj"))
        
        cmd = [
            wwisecli_path, wproj_path, "-ConvertExternalSources", "Windows",
            wsources_path, "-ExternalSourcesOutput", temp_dir, "-Quiet"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False, creationflags=CREATE_NO_WINDOW)
        
        if result.returncode != 0:
            DEBUG.log(f"Conversion failed for Conversion={conversion_value}: {result.stderr}", "ERROR")
            if hasattr(self.parent, 'append_conversion_log'):
                self.parent.append_conversion_log(f"    ✗ Conversion={conversion_value} failed: {result.stderr}")
            raise Exception(f"Conversion error: {result.stderr}")
        
        wav_name_no_ext = os.path.splitext(wav_name)[0]
        wem_file = self.find_wem_file(temp_dir, wav_name_no_ext)
        
        if wem_file:
            file_size = os.path.getsize(wem_file)
            
            DEBUG.log(f"SUCCESS: Conversion={conversion_value} produced {file_size:,} bytes (ratio: {file_size/wav_size:.2f}x)")
                   
            if hasattr(self.parent, 'append_conversion_log'):
                self.parent.append_conversion_log(f"    ✓ Conversion={conversion_value} → {file_size:,} bytes")
            
            result_data = {
                'file': wem_file,
                'size': file_size,
                'dir': temp_dir,
                'conversion': conversion_value
            }
            self.conversion_cache[cache_key] = result_data
            return result_data
        else:
            DEBUG.log(f"No WEM file found after conversion with Conversion={conversion_value}", "ERROR")
            if hasattr(self.parent, 'append_conversion_log'):
                self.parent.append_conversion_log(f"    ✗ Conversion={conversion_value} - no output file")
                
        return None

    def find_wem_file(self, script_dir, wav_name):
        possible_paths = [
            os.path.join(script_dir, "Windows", f"{wav_name}.wem"),
            os.path.join(script_dir, f"{wav_name}.wem")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
        
    def increase_file_size(self, file_path, target_size_bytes):
        """Simple file size increase with logging"""
        if not os.path.exists(file_path):
            DEBUG.log(f"ERROR: File not found: {file_path}", "ERROR")
            return False
        
        current_size = os.path.getsize(file_path)
        DEBUG.log(f"increase_file_size: current={current_size:,}, target={target_size_bytes:,}")
        
        if target_size_bytes <= current_size:
            DEBUG.log(f"File already at or above target size ({current_size:,} >= {target_size_bytes:,})")
            return True
        
        bytes_to_add = target_size_bytes - current_size
        DEBUG.log(f"Adding {bytes_to_add:,} bytes of padding...")
        
        try:
            with open(file_path, 'ab') as file:
                file.write(b'\x00' * bytes_to_add)
            
            new_size = os.path.getsize(file_path)
            DEBUG.log(f"File size increased from {current_size:,} to {new_size:,} bytes")
            
            if new_size != target_size_bytes:
                DEBUG.log(f"WARNING: New size {new_size:,} != target {target_size_bytes:,}", "WARNING")
            
            return True
            
        except Exception as e:
            DEBUG.log(f"ERROR while increasing file size: {e}", "ERROR")
            return False
    def convert_single_file(self, file_pair):
        """Convert single file with stop checking"""
        
        if self.should_stop:
            return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
        
        try:
            wav_file = file_pair['wav_file']
            target_wem = file_pair['target_wem']
            target_size = file_pair['target_size']
            
            if self.should_stop:
                return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}

            wav_info = self.get_wav_info(wav_file)
            if not wav_info:
                return {'success': False, 'error': 'Could not read WAV file info'}

            if self.should_stop:
                return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
       
            current_sample_rate = wav_info.get('sample_rate', 44100)
            target_sample_rate = current_sample_rate
            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
       
                if self.should_stop:
                    return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
                
                attempts += 1
                
                result = self.convert_with_sample_rate(wav_file, target_sample_rate, target_wem)
                
                if result.get('success'):
                    final_size = result.get('file_size', 0)
                    size_diff = abs(final_size - target_size) / target_size * 100
                    
                    return {
                        'success': True,
                        'output_path': result['output_path'],
                        'final_size': final_size,
                        'target_size': target_size,
                        'size_diff_percent': size_diff,
                        'sample_rate': target_sample_rate,
                        'attempts': attempts,
                        'resampled': target_sample_rate != current_sample_rate,
                        'conversion': f"{current_sample_rate}Hz → {target_sample_rate}Hz" if target_sample_rate != current_sample_rate else f"{current_sample_rate}Hz"
                    }
                
                if self.adaptive_mode and result.get('error', '').find('too large') != -1:
                    if target_sample_rate > 22050:
                        target_sample_rate = 22050
                    elif target_sample_rate > 16000:
                        target_sample_rate = 16000
                    elif target_sample_rate > 11025:
                        target_sample_rate = 11025
                    else:
                        break
                else:
                    break
            
            return result if result else {'success': False, 'error': 'Conversion failed after all attempts'}
            
        except Exception as e:
            return {'success': False, 'error': f'Exception during conversion: {str(e)}'}
    def get_wav_sample_rate(self, wav_file):
        """Get sample rate from WAV file"""
        try:
            import wave
            with wave.open(wav_file, 'rb') as wav:
                return wav.getframerate()
        except Exception as e:
            DEBUG.log(f"Error reading WAV sample rate: {e}", "ERROR")
            return 48000 
    def convert_single_file_main(self, file_pair, file_index, total_files):
        """Main conversion method that chooses between adaptive or normal mode"""
        if self.should_stop:
            return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
        
        try:
            if self.adaptive_mode:
                return self.convert_single_file_adaptive(file_pair, file_index, total_files)
            else:
                wav_file = file_pair['wav_file']
                target_size = file_pair['target_size']
                wav_name = os.path.splitext(os.path.basename(wav_file))[0]
                
                DEBUG.log(f"Starting conversion for {wav_name} (target: {target_size:,} bytes)")
                return self.try_conversion_with_binary_search(wav_file, target_size, file_index, total_files, wav_name)
        
        except Exception as e:
            DEBUG.log(f"Error in convert_single_file_main: {e}", "ERROR")
            return {'success': False, 'error': f'Conversion error: {str(e)}'}
    
    def convert_single_file_adaptive(self, file_pair, file_index, total_files):
        """Adaptive conversion with sample rate adjustment"""
        if self.should_stop:
            return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
        
        try:
            wav_file = file_pair['wav_file']
            target_size = file_pair['target_size']
            wav_name = os.path.splitext(os.path.basename(wav_file))[0]
            
            DEBUG.log(f"Starting adaptive conversion for {wav_name}")
            
            original_sample_rate = self.get_wav_sample_rate(wav_file)
            DEBUG.log(f"Original sample rate: {original_sample_rate}Hz")
            
            try:
                result = self.try_conversion_with_binary_search(wav_file, target_size, file_index, total_files, wav_name)
                if result.get('success'):
                    result['resampled'] = False
                    result['sample_rate'] = original_sample_rate
                    result['conversion'] = f"{original_sample_rate}Hz (original)"
                    return result
            except Exception as e:
                DEBUG.log(f"Original quality conversion failed: {e}")
            
            optimal_rate_idx = self.find_optimal_sample_rate(wav_file, target_size, file_index, total_files, wav_name)
            
            if optimal_rate_idx >= 0:
                optimal_rate = self.SUPPORTED_SAMPLE_RATES[optimal_rate_idx]
                
                if optimal_rate < original_sample_rate: 
                    DEBUG.log(f"Using reduced sample rate: {optimal_rate}Hz (from {original_sample_rate}Hz)")
                    
                    temp_wav = os.path.join(self.output_folder, f"resampled_{wav_name}_{optimal_rate}.wav")
                    if not self.resample_wav_file(wav_file, temp_wav, optimal_rate):
                        return {'success': False, 'error': 'Failed to resample audio file'}
                    
                    result = self.try_conversion_with_binary_search(temp_wav, target_size, file_index, total_files, wav_name)
                    
                    if os.path.exists(temp_wav):
                        try:
                            os.remove(temp_wav)
                        except:
                            pass
                    
                    if result.get('success'):
                        result['resampled'] = True
                        result['sample_rate'] = optimal_rate
                        result['conversion'] = f"{original_sample_rate}Hz → {optimal_rate}Hz"
                    
                    return result
                else:
                    DEBUG.log(f"Optimal rate {optimal_rate}Hz is not lower than original {original_sample_rate}Hz")
            
            return {'success': False, 'error': 'Could not find suitable sample rate for target size'}
            
        except Exception as e:
            DEBUG.log(f"Error in adaptive conversion: {e}", "ERROR")
            return {'success': False, 'error': f'Adaptive conversion error: {str(e)}'}
    def find_optimal_sample_rate(self, wav_file, target_size, file_index, total_files, wav_name):
        """Binary search to find optimal sample rate for target size"""
        
        original_sample_rate = self.get_wav_sample_rate(wav_file)
        DEBUG.log(f"Original sample rate: {original_sample_rate}Hz")
        
        valid_rates = [rate for rate in self.SUPPORTED_SAMPLE_RATES if rate <= original_sample_rate]
        
        if not valid_rates:
            DEBUG.log(f"No valid sample rates found for original rate {original_sample_rate}Hz")
            return -1
        
        DEBUG.log(f"Valid sample rates for search: {valid_rates}")
        
        left, right = 0, len(valid_rates) - 1
        best_idx = -1
        
        while left <= right:
            mid = (left + right) // 2
            sample_rate = valid_rates[mid]
            
            self.status_updated.emit(
                f"File {file_index}/{total_files}: {wav_name} - Testing {sample_rate}Hz...", 
                "blue"
            )
            
            temp_wav = os.path.join(self.output_folder, f"test_{wav_name}_{sample_rate}.wav")
            if not self.resample_wav_file(wav_file, temp_wav, sample_rate):
                left = mid + 1
                continue
            
            try:
                result = self.convert_with_quality(temp_wav, -2)  
                
                if result and result['size'] <= target_size:
                    best_idx = mid
                    right = mid - 1 
                else:
                    left = mid + 1
                    
            except Exception as e:
                DEBUG.log(f"Error testing sample rate {sample_rate}: {e}", "ERROR")
                left = mid + 1
            finally:
                try:
                    os.remove(temp_wav)
                except:
                    pass
        
        if best_idx >= 0:
            best_rate = valid_rates[best_idx]
            original_idx = self.SUPPORTED_SAMPLE_RATES.index(best_rate)
            DEBUG.log(f"Found optimal sample rate: {best_rate}Hz (original: {original_sample_rate}Hz)")
            return original_idx
        
        return -1
    def try_conversion_with_binary_search(self, wav_file, target_size, file_index, total_files, wav_name):
        """Binary search with file copy to prevent cache corruption"""
        left, right = -2, 10
        best_result = None
        attempts = 0
        
        DEBUG.log(f"\n=== BINARY SEARCH START for {wav_name} ===")
        DEBUG.log(f"Target size: {target_size:,} bytes")
        DEBUG.log(f"Search range: [{left}, {right}]")
        
        if hasattr(self.parent, 'append_conversion_log'):
            self.parent.append_conversion_log(f"\n📊 Binary search for {wav_name}:")
            self.parent.append_conversion_log(f"   Target size: {target_size:,} bytes")
        
        all_attempts = []
        
        while left <= right:
            mid = (left + right) // 2
            attempts += 1
            
            DEBUG.log(f"\nAttempt {attempts}: Testing Conversion={mid} (range: [{left}, {right}])")
            
            self.status_updated.emit(
                f"File {file_index}/{total_files}: {wav_name} - attempt {attempts} (Conversion={mid})", 
                "blue"
            )
            
            try:
                result = self.convert_with_quality(wav_file, mid)
                
                if not result or not result.get('size'):
                    DEBUG.log(f"  → No result for Conversion={mid}")
                    all_attempts.append({'conversion': mid, 'size': None, 'status': 'failed'})
                    right = mid - 1
                    continue
                    
                current_size = result['size']
                size_ratio = current_size / target_size
                
                DEBUG.log(f"  → Result: {current_size:,} bytes ({size_ratio:.1%} of target)")
                
                attempt_info = {
                    'conversion': mid,
                    'size': current_size,
                    'ratio': size_ratio,
                    'status': 'ok' if current_size <= target_size else 'too_large'
                }
                all_attempts.append(attempt_info)
                
                if current_size <= target_size:
                    DEBUG.log(f"  → Acceptable size! Saving as best result")
                    
                    temp_best_file = os.path.join(self.output_folder, f"best_{wav_name}_{mid}.wem")
                    os.makedirs(self.output_folder, exist_ok=True)
                    shutil.copy2(result['file'], temp_best_file)
                    
                    best_result = {
                        'file': temp_best_file, 
                        'size': current_size,
                        'conversion': mid
                    }
                    
                    DEBUG.log(f"  → Copied best result to: {temp_best_file}")
                    
                    left = mid + 1 
                else:
                    DEBUG.log(f"  → Too large! Reducing quality")
                    right = mid - 1
                    
            except Exception as e:
                DEBUG.log(f"  → ERROR: {e}", "ERROR")
                all_attempts.append({'conversion': mid, 'size': None, 'status': 'error', 'error': str(e)})
                right = mid - 1
        
        DEBUG.log(f"\n=== BINARY SEARCH COMPLETE ===")
        DEBUG.log(f"Total attempts: {attempts}")
        DEBUG.log(f"All attempts summary:")
        for attempt in all_attempts:
            if attempt['size']:
                DEBUG.log(f"  Conversion={attempt['conversion']}: {attempt['size']:,} bytes ({attempt['status']})")
            else:
                DEBUG.log(f"  Conversion={attempt['conversion']}: FAILED ({attempt['status']})")
        
        if hasattr(self.parent, 'append_conversion_log'):
            self.parent.append_conversion_log(f"   Search complete after {attempts} attempts")
        
        if best_result:
            DEBUG.log(f"\nBest result: Conversion={best_result['conversion']}, size={best_result['size']:,} bytes")
            DEBUG.log(f"Best result file: {best_result['file']}")
            
            if not os.path.exists(best_result['file']):
                DEBUG.log(f"ERROR: Best result file disappeared: {best_result['file']}", "ERROR")
                return {'success': False, 'error': 'Best result file not found'}
            
            current_file_size = os.path.getsize(best_result['file'])
            DEBUG.log(f"Best result file current size: {current_file_size:,} bytes")
            
            if current_file_size != best_result['size']:
                DEBUG.log(f"WARNING: File size changed! Expected {best_result['size']:,}, got {current_file_size:,}", "WARNING")
                best_result['size'] = current_file_size 
 
            padding_needed = target_size - best_result['size']
            DEBUG.log(f"Padding needed: {padding_needed:,} bytes")
            
            if hasattr(self.parent, 'append_conversion_log'):
                self.parent.append_conversion_log(f"   Best: Conversion={best_result['conversion']} → {best_result['size']:,} bytes")
                self.parent.append_conversion_log(f"   Adding {padding_needed:,} bytes padding...")
            
           
            success = self.increase_file_size(best_result['file'], target_size)
            
            if success:
           
                final_size_after_padding = os.path.getsize(best_result['file'])
                DEBUG.log(f"File size after padding: {final_size_after_padding:,} bytes")
                
              
                output_filename = f"{wav_name}.wem"
                output_path = os.path.join(self.output_folder, output_filename)
                
                counter = 1
                while os.path.exists(output_path) and output_path != best_result['file']:
                    output_filename = f"{wav_name}_{counter}.wem"
                    output_path = os.path.join(self.output_folder, output_filename)
                    counter += 1
                
                if output_path != best_result['file']:
                    shutil.copy2(best_result['file'], output_path)
                    DEBUG.log(f"Copied to final output: {output_path}")
                else:
                    DEBUG.log(f"Final output is same as best result file: {output_path}")
                
                final_size = os.path.getsize(output_path)
                size_difference = abs(final_size - target_size)
                size_percentage = (size_difference / target_size) * 100
                
                DEBUG.log(f"FINAL: Output file {output_filename} = {final_size:,} bytes (target was {target_size:,})")
                
                if final_size != target_size:
                    DEBUG.log(f"WARNING: Final size mismatch! Difference: {size_difference:,} bytes ({size_percentage:.1f}%)", "WARNING")
                
                if hasattr(self.parent, 'append_conversion_log'):
                    if final_size == target_size:
                        self.parent.append_conversion_log(f"   ✅ Success! Final size: {final_size:,} bytes (exact match)")
                    else:
                        self.parent.append_conversion_log(f"   ⚠️ Final size: {final_size:,} bytes (diff: {size_difference:,} bytes)")
                
             
                if best_result['file'] != output_path and os.path.exists(best_result['file']):
                    try:
                        os.remove(best_result['file'])
                        DEBUG.log(f"Cleaned up temporary file: {best_result['file']}")
                    except:
                        pass
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'final_size': final_size,
                    'attempts': attempts,
                    'conversion': best_result.get('conversion', 0),
                    'size_diff_percent': size_percentage
                }
            else:
                DEBUG.log("Failed to adjust file size!", "ERROR")
                return {'success': False, 'error': 'Failed to adjust file size'}
        else:
            DEBUG.log("\nNo acceptable result found!", "ERROR")
            
          
            try:
                min_result = self.convert_with_quality(wav_file, -2)
                if min_result and min_result.get('size'):
                    min_size = min_result['size']
                    if min_size > target_size:
                        size_diff = ((min_size - target_size) / target_size) * 100
                        DEBUG.log(f"Minimum possible size: {min_size:,} bytes ({size_diff:.1f}% over target)", "ERROR")
                        
                        if hasattr(self.parent, 'append_conversion_log'):
                            self.parent.append_conversion_log(f"   ❌ Failed! Minimum size {min_size:,} > target {target_size:,}")
                        
                        return {
                            'success': False, 
                            'error': f'Cannot achieve target size. Minimum: {min_size:,} bytes, Target: {target_size:,} bytes ({size_diff:.1f}% over). Try reducing WAV quality.',
                            'size_warning': True
                        }
            except:
                pass
                
            return {'success': False, 'error': 'Failed to create WEM file. Please check your WAV file.'}
    def convert_single_file(self, file_pair, file_index, total_files):
        """Main conversion method that chooses between adaptive or normal mode"""
        if self.should_stop:
            return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
        if self.adaptive_mode:
            return self.convert_single_file_adaptive(file_pair, file_index, total_files)
        else:
      
            wav_file = file_pair['wav_file']
            target_size = file_pair['target_size']
            wav_name = os.path.splitext(os.path.basename(wav_file))[0]
            
            return self.try_conversion_with_binary_search(wav_file, target_size, file_index, total_files, wav_name)
            
    def convert_all_files(self):
            """Convert all files with stop checking"""
            try:
                self.should_stop = False
                results = []
                total_files = len(self.file_pairs)
                
                if total_files == 0:
                    self.conversion_finished.emit([])
                    return
                
                self.conversion_cache.clear()
                DEBUG.log("Starting conversion - cache cleared")
                
                try:
                    wproj_path = self.ensure_project_exists()
                    
                    DEBUG.log(f"Using Wwise project: {wproj_path}")
                except Exception as e:
                    error_result = {
                        'file_pair': {'wav_name': 'Project Setup'},
                        'result': {'success': False, 'error': f'Failed to setup Wwise project: {str(e)}'}
                    }
                    self.conversion_finished.emit([error_result])
                    return
                
                for i, file_pair in enumerate(self.file_pairs):
           
                    if self.should_stop:
                        DEBUG.log(f"Conversion stopped at file {i+1}/{total_files}")
                    
                        for j in range(i, total_files):
                            results.append({
                                'file_pair': self.file_pairs[j],
                                'result': {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}
                            })
                        break
                    
                    progress = int((i / total_files) * 100)
                    self.progress_updated.emit(progress)
                    self.status_updated.emit(f"Converting {i+1}/{total_files}: {file_pair['wav_name']}", "blue")
                    
                    result = self.convert_single_file_main(file_pair, i+1, total_files)
                    results.append({
                        'file_pair': file_pair,
                        'result': result
                    })
                    
                    if self.should_stop:
                        break
                
                self.conversion_finished.emit(results)
                
            except Exception as e:
                DEBUG.log(f"Error in convert_all_files: {e}", "ERROR")
                error_result = {
                    'file_pair': {'wav_name': 'Unknown'},
                    'result': {'success': False, 'error': f'Conversion thread error: {str(e)}'}
                }
                self.conversion_finished.emit([error_result])
        
    def cleanup_temp_directories(self, temp_dirs):
        self.status_updated.emit("Cleaning up temporary files...", "blue")
        
        for temp_dir in temp_dirs:
            try:
                if os.path.exists(temp_dir) and "temp" in temp_dir.lower():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                DEBUG.log(f"Failed to delete temp folder {temp_dir}: {e}", "WARNING")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "data")
        wsources_file = os.path.join(data_dir, "convert.wsources")
        if os.path.exists(wsources_file):
            try:
                os.remove(wsources_file)
            except:
                pass
    def stop_conversion(self):
        """Signal the conversion process to stop"""
        self.should_stop = True
        self.status_updated.emit("Stopping conversion...", "orange")
        
        self.conversion_cache.clear()
        DEBUG.log("Conversion stopped - cache cleared")
    
 
class SubtitleEditor(QtWidgets.QDialog):
    def __init__(self, parent=None, key="", subtitle="", original_subtitle=""):
        super().__init__(parent)
        self.tr = parent.tr if parent else lambda x: x
        self.setWindowTitle(self.tr("edit_subtitle"))
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        key_label = QtWidgets.QLabel(f"Key: {key}")
        key_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(key_label)
        
        if original_subtitle and original_subtitle != subtitle:
            original_group = QtWidgets.QGroupBox(f"{self.tr('original')} Subtitle")
            original_layout = QtWidgets.QVBoxLayout(original_group)
            
            original_text = QtWidgets.QTextEdit()
            original_text.setPlainText(original_subtitle)
            original_text.setReadOnly(True)
            original_text.setMaximumHeight(100)
            original_text.setStyleSheet("background-color: #f0f0f0;")
            original_layout.addWidget(original_text)
            
            layout.addWidget(original_group)

        edit_group = QtWidgets.QGroupBox("Current Subtitle")
        edit_layout = QtWidgets.QVBoxLayout(edit_group)
        
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setPlainText(subtitle)
        edit_layout.addWidget(self.text_edit)
        
        layout.addWidget(edit_group)
        
        self.char_count = QtWidgets.QLabel()
        self.update_char_count()
        layout.addWidget(self.char_count)
        
        btn_layout = QtWidgets.QHBoxLayout()
        
        if original_subtitle and original_subtitle != subtitle:
            self.revert_btn = ModernButton(f"{self.tr('revert_to_original')}")
            self.revert_btn.clicked.connect(lambda: self.text_edit.setPlainText(original_subtitle))
            btn_layout.addWidget(self.revert_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = ModernButton(self.tr("cancel"))
        self.save_btn = ModernButton(self.tr("save"), primary=True)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        self.text_edit.textChanged.connect(self.update_char_count)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def update_char_count(self):
        count = len(self.text_edit.toPlainText())
        self.char_count.setText(f"{self.tr('characters')} {count}")
        
    def get_text(self):
        return self.text_edit.toPlainText()

class WemSubtitleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        DEBUG.log("=== OutlastTrials AudioEditor Starting ===")
        
        self.settings = AppSettings()
        self.translations = TRANSLATIONS
        self.current_lang = self.settings.data["ui_language"]
        
        self.setWindowTitle(self.tr("app_title"))
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        
        if getattr(sys, 'frozen', False):

            self.base_path = os.path.dirname(sys.executable)
        else:

            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        DEBUG.log(f"Base path: {self.base_path}")
        
        self.data_path = os.path.join(self.base_path, "data")
        self.libs_path = os.path.join(self.base_path, "libs")   
        
        self.unreal_locres_path = os.path.join(self.data_path, "UnrealLocres.exe")
        self.repak_path = os.path.join(self.data_path, "repak.exe")
        self.vgmstream_path = os.path.join(self.data_path, "vgmstream", "vgmstream-cli.exe")
        
        self.soundbanks_path = os.path.join(self.base_path, "SoundbanksInfo.json")
        self.wem_root = os.path.join(self.base_path, "Wems")
        self.mod_p_path = os.path.join(self.base_path, "MOD_P")
        
        self.check_required_files()
        
        DEBUG.log(f"Paths configured:")
        DEBUG.log(f"  data_path: {self.data_path}")
        DEBUG.log(f"  unreal_locres_path: {self.unreal_locres_path}")
        DEBUG.log(f"  repak_path: {self.repak_path}")
        DEBUG.log(f"  vgmstream_path: {self.vgmstream_path}")

        self.locres_manager = UnrealLocresManager(self.unreal_locres_path)
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_subtitle_files = {}
        self.all_files = self.load_all_soundbank_files(self.soundbanks_path)
        self.entries_by_lang = self.group_by_language()

        self.audio_player = AudioPlayer()
        self.temp_wav = None
        self.currently_playing_item = None
        self.is_playing_mod = False
        self.original_duration = 0
        self.mod_duration = 0
        self.original_size = 0
        self.mod_size = 0
        self.populated_tabs = set()
        self.modified_subtitles = set()
        self.current_file_duration = 0

        self.debug_window = None
        
        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_subtitles)
        self.auto_save_enabled = False  
        
        self.create_ui()
   
        self.apply_settings()
        self.restore_window_state()

        self.load_subtitles()

        self.update_auto_save_timer()
        self.check_updates_on_startup()    
        DEBUG.log("=== OutlastTrials AudioEditor Started Successfully ===")

    def update_auto_save_timer(self):
        auto_save_setting = self.settings.data.get("auto_save", True)
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            DEBUG.log("Auto-save timer stopped")
        

        if auto_save_setting:
            self.auto_save_timer.start(300000) 
            self.auto_save_enabled = True
            DEBUG.log("Auto-save timer started (5 minutes)")
        else:
            self.auto_save_enabled = False
            DEBUG.log("Auto-save disabled")

    def auto_save_subtitles(self):
        if not self.auto_save_enabled or not self.settings.data.get("auto_save", True):
            DEBUG.log("Auto-save skipped - disabled")
            return
        
        if not self.modified_subtitles:
            DEBUG.log("Auto-save skipped - no changes")
            return
        
        DEBUG.log(f"Auto-saving {len(self.modified_subtitles)} modified subtitles...")
        
        try:

            self.status_bar.showMessage("Auto-saving...", 2000)
            
            QtCore.QTimer.singleShot(100, self.perform_auto_save)
            
        except Exception as e:
            DEBUG.log(f"Auto-save error: {e}", "ERROR")

    def perform_auto_save(self):
        try:
            self.save_subtitles_to_file()
            DEBUG.log(f"Auto-save completed successfully")
            self.status_bar.showMessage("Auto-saved", 1000)
        except Exception as e:
            DEBUG.log(f"Auto-save failed: {e}", "ERROR")
            self.status_bar.showMessage("Auto-save failed", 2000)

    def delete_mod_audio(self, entry, lang):
        """Delete modified audio file(s)"""
        widgets = self.tab_widgets.get(lang) 
        if not widgets:
            DEBUG.log(f"No widgets found for language: {lang}", "WARNING")
            return
        
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if len(items) > 1:
            file_list = []
            for item in items:
                if item.childCount() == 0:
                    entry = item.data(0, QtCore.Qt.UserRole)
                    if entry:
                        id_ = entry.get("Id", "")
                        if lang != "SFX":
                            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{id_}.wem")
                        else:
                            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{id_}.wem")
                        if os.path.exists(mod_path):
                            file_list.append((entry.get("ShortName", ""), mod_path))
            
            if not file_list:
                return
                
            reply = QtWidgets.QMessageBox.question(
                self, "Delete Multiple Mod Audio",
                f"Delete modified audio for {len(file_list)} files?\n\nThis action cannot be undone.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                deleted = 0
                for shortname, path in file_list:
                    try:
                        os.remove(path)
                        deleted += 1
                        DEBUG.log(f"Deleted mod audio: {path}")
                    except Exception as e:
                        DEBUG.log(f"Error deleting {shortname}: {e}", "ERROR")
                
                if "play_mod_btn" in widgets:
                    widgets["play_mod_btn"].hide()
                if "info_labels" in widgets and "mod_duration" in widgets["info_labels"]:
                    widgets["info_labels"]["mod_duration"].setText("N/A")
                if "size_warning" in widgets:
                    widgets["size_warning"].hide()
                
                self.populate_tree(lang)
                self.status_bar.showMessage(f"Deleted {deleted} mod audio files", 3000)
            return
            
        id_ = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        if lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{id_}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{id_}.wem")
        
        if not os.path.exists(mod_wem_path):
            DEBUG.log(f"Mod file does not exist: {mod_wem_path}", "INFO")
            QtWidgets.QMessageBox.information(
                self, "Info", 
                f"No modified audio found for {shortname}"
            )
            return
            
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Mod Audio",
            f"Delete modified audio for:\n{shortname}\n\nThis action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                os.remove(mod_wem_path)
                DEBUG.log(f"Deleted mod audio: {mod_wem_path}")

                if "play_mod_btn" in widgets:
                    widgets["play_mod_btn"].hide()
                if "info_labels" in widgets and "mod_duration" in widgets["info_labels"]:
                    widgets["info_labels"]["mod_duration"].setText("N/A")
                if "size_warning" in widgets:
                    widgets["size_warning"].hide()
                
                self.populate_tree(lang)
                self.status_bar.showMessage(f"Deleted mod audio for {shortname}", 3000)
                
            except Exception as e:
                DEBUG.log(f"Error deleting mod audio: {e}", "ERROR")
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to delete file: {str(e)}")
    def tr(self, key):
        """Translate key to current language"""
        return self.translations.get(self.current_lang, {}).get(key, key)
        
    def check_required_files(self):
        """Check if all required files exist"""
        missing_files = []
        
        required_files = [
            (self.unreal_locres_path, "UnrealLocres.exe"),
            (self.repak_path, "repak.exe"),
            (self.vgmstream_path, "vgmstream-cli.exe")
        ]
        
        for file_path, file_name in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_name)
                DEBUG.log(f"Missing required file: {file_path}", "WARNING")
        
        if missing_files:
            msg = f"Missing required files in data folder:\n" + "\n".join(f"• {f}" for f in missing_files)
            msg += "\n\nPlease ensure all files are in the correct location."
            QtWidgets.QMessageBox.warning(None, "Missing Files", msg)
            
    def load_subtitles(self):
        DEBUG.log("=== Loading Subtitles (Fixed Structure) ===")
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_subtitle_files = {}

        self.scan_localization_folder()

        subtitle_lang = self.settings.data["subtitle_lang"]
        self.load_subtitles_for_language(subtitle_lang)

        self.modified_subtitles.clear()
        for key, value in self.subtitles.items():
            if key in self.original_subtitles and self.original_subtitles[key] != value:
                self.modified_subtitles.add(key)
        
        DEBUG.log(f"Found {len(self.modified_subtitles)} modified subtitles")
        DEBUG.log("=== Subtitle Loading Complete ===")

    def scan_localization_folder(self):
        """Scan Localization folder for all subtitle files"""
        localization_path = os.path.join(self.base_path, "Localization")
        DEBUG.log(f"Scanning localization folder: {localization_path}")
        
        self.all_subtitle_files = {}
        
        if not os.path.exists(localization_path):
            DEBUG.log("Localization folder not found, creating structure", "WARNING")

            os.makedirs(localization_path, exist_ok=True)

            default_langs = ["en", "ru-RU", "fr-FR", "de-DE", "es-ES"]
            for lang in default_langs:
                lang_path = os.path.join(localization_path, "OPP_Subtitles", lang)
                os.makedirs(lang_path, exist_ok=True)

                locres_path = os.path.join(lang_path, "OPP_Subtitles.locres")
                if not os.path.exists(locres_path):

                    empty_subtitles = {}
                    self.create_empty_locres_file(locres_path, empty_subtitles)

            return self.scan_localization_folder()

        try:
            for item in os.listdir(localization_path):
                item_path = os.path.join(localization_path, item)
                
                if not os.path.isdir(item_path):
                    continue
                    
                DEBUG.log(f"Found subtitle category: {item}")

                try:
                    for lang_item in os.listdir(item_path):
                        lang_path = os.path.join(item_path, lang_item)
                        
                        if not os.path.isdir(lang_path):
                            continue
                            
                        DEBUG.log(f"Found language folder: {lang_item} in {item}")
   
                        try:
                            for file_item in os.listdir(lang_path):
                                if file_item.endswith('.locres') and not file_item.endswith('_working.locres'):
                                    file_path = os.path.join(lang_path, file_item)
                                    
                                    key = f"{item}/{lang_item}/{file_item}"
                                    self.all_subtitle_files[key] = {
                                        'path': file_path,
                                        'category': item,
                                        'language': lang_item,
                                        'filename': file_item,
                                        'relative_path': f"Localization/{item}/{lang_item}/{file_item}"
                                    }
                                    
                                    DEBUG.log(f"Found subtitle file: {key}")
                                    
                        except PermissionError:
                            DEBUG.log(f"Permission denied accessing {lang_path}", "WARNING")
                            continue
                            
                except PermissionError:
                    DEBUG.log(f"Permission denied accessing {item_path}", "WARNING")
                    continue
                    
        except Exception as e:
            DEBUG.log(f"Error scanning localization folder: {e}", "ERROR")
        
        DEBUG.log(f"Total subtitle files found: {len(self.all_subtitle_files)}")

    def create_empty_locres_file(self, path, subtitles):
        """Create an empty locres file"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            csv_path = path.replace('.locres', '.csv')
            
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)

                for key, value in subtitles.items():
                    writer.writerow([f"Subtitles/{key}", value])
            
            if os.path.exists(self.unreal_locres_path):
                result = subprocess.run(
                    [self.unreal_locres_path, "import", path, csv_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.unreal_locres_path) or ".",
                    startupinfo=startupinfo,
                    creationflags=CREATE_NO_WINDOW
                )
                
                if result.returncode != 0:
                    DEBUG.log(f"Failed to create locres file: {result.stderr}", "WARNING")

            if os.path.exists(csv_path):
                os.remove(csv_path)
                
        except Exception as e:
            DEBUG.log(f"Error creating empty locres file: {e}", "ERROR")

    def load_subtitles_for_language(self, language):
        DEBUG.log(f"Loading subtitles for language: {language}")
        
        self.subtitles = {}
        self.original_subtitles = {}

        for key, file_info in self.all_subtitle_files.items():
            if file_info['language'] == language:
                DEBUG.log(f"Loading file: {file_info['path']}")

                original_subtitles = self.locres_manager.export_locres(file_info['path'])
                self.original_subtitles.update(original_subtitles)

                working_path = file_info['path'].replace('.locres', '_working.locres')
                if os.path.exists(working_path):
                    DEBUG.log(f"Found working copy: {working_path}")
                    working_subtitles = self.locres_manager.export_locres(working_path)
                    self.subtitles.update(working_subtitles)
                else:

                    self.subtitles.update(original_subtitles)
                    
                DEBUG.log(f"Loaded {len(original_subtitles)} subtitles from {file_info['filename']}")

    def create_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_menu_bar()
        self.create_toolbar()

        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)

        self.global_search = SearchBar()
        self.global_search.searchChanged.connect(self.on_global_search)
        content_layout.addWidget(self.global_search)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tab_widgets = {}

        languages = list(self.entries_by_lang.keys())

        if "French(France)" not in languages and any("French" in lang for lang in languages):
            french_variants = [lang for lang in languages if "French" in lang]
            if french_variants:
                languages = languages
                
        if "SFX" not in languages:
            self.entries_by_lang["SFX"] = []
            languages.append("SFX")
            
        for lang in sorted(languages):
            self.create_language_tab(lang)

        self.create_converter_tab()
        self.create_subtitle_editor_tab()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)

        if self.entries_by_lang:
            first_lang = sorted(self.entries_by_lang.keys())[0]
            self.populate_tree(first_lang)
            self.populated_tabs.add(first_lang)
            
        def delayed_init():
            if hasattr(self, 'subtitle_lang_combo'):
                self.populate_subtitle_editor_controls()

        QtCore.QTimer.singleShot(500, delayed_init)

    def refresh_subtitle_editor(self):
        """Refresh subtitle editor data"""
        DEBUG.log("Refreshing subtitle editor")
        self.scan_localization_folder()
        self.populate_subtitle_editor_controls()
        self.status_bar.showMessage("Localization editor refreshed", 2000)

    def on_global_search_changed_for_subtitles(self, text):
        """Handle global search changes when on subtitle editor tab"""
        if self.tabs.currentWidget() == self.tabs.widget(self.tabs.count() - 1):
            self.on_subtitle_filter_changed()

    def get_global_search_text(self):
        """Get text from global search bar"""
        return self.global_search.text() if hasattr(self, 'global_search') else ""

    def create_subtitle_editor_tab(self):
        """Create tab for editing subtitles without audio files"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel(f"""
        <h3>{self.tr("localization_editor")}</h3>
        <p>{self.tr("localization_editor_desc")}</p>
        """)
        layout.addWidget(header)
        
        status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(status_widget)
        
        self.subtitle_status_label = QtWidgets.QLabel("Ready")
        self.subtitle_status_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.subtitle_progress = QtWidgets.QProgressBar()
        self.subtitle_progress.setVisible(False)
        self.subtitle_progress.setMaximumHeight(20)
        
        self.subtitle_cancel_btn = QtWidgets.QPushButton("Cancel")
        self.subtitle_cancel_btn.setVisible(False)
        self.subtitle_cancel_btn.setMaximumWidth(80)
        self.subtitle_cancel_btn.clicked.connect(self.cancel_subtitle_loading)
        
        status_layout.addWidget(self.subtitle_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.subtitle_progress)
        status_layout.addWidget(self.subtitle_cancel_btn)
        
        layout.addWidget(status_widget)
        
        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        
        category_label = QtWidgets.QLabel("Category:")
        self.subtitle_category_combo = QtWidgets.QComboBox()
        self.subtitle_category_combo.setMinimumWidth(150)
        
        self.orphaned_only_checkbox = QtWidgets.QCheckBox("Without audio")
        self.orphaned_only_checkbox.setToolTip("Show only subtitles that don't have corresponding audio files")
        
        self.modified_only_checkbox = QtWidgets.QCheckBox("Modified only")
        self.modified_only_checkbox.setToolTip("Show only subtitles that have been modified")
        
        self.with_audio_only_checkbox = QtWidgets.QCheckBox("With audio only")
        self.with_audio_only_checkbox.setToolTip("Show only subtitles that have corresponding audio files")
        
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh subtitle data from files")
        refresh_btn.clicked.connect(self.refresh_subtitle_editor)
        
        controls_layout.addWidget(category_label)
        controls_layout.addWidget(self.subtitle_category_combo)
        controls_layout.addWidget(self.orphaned_only_checkbox)
        controls_layout.addWidget(self.modified_only_checkbox)
        controls_layout.addWidget(self.with_audio_only_checkbox)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)
        
        layout.addWidget(controls)
        
        self.subtitle_category_combo.currentTextChanged.connect(self.on_subtitle_filter_changed)
        self.orphaned_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        self.modified_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        self.with_audio_only_checkbox.toggled.connect(self.on_subtitle_filter_changed)
        
        self.subtitle_table = QtWidgets.QTableWidget()
        self.subtitle_table.setColumnCount(4)
        self.subtitle_table.setHorizontalHeaderLabels(["Key", "Original", "Current", "Audio"])
        
        header = self.subtitle_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        
        self.subtitle_table.setAlternatingRowColors(True)
        self.subtitle_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.subtitle_table.itemDoubleClicked.connect(self.edit_subtitle_from_table)
        
        self.subtitle_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.subtitle_table.customContextMenuRequested.connect(self.show_subtitle_table_context_menu)
        
        layout.addWidget(self.subtitle_table)
        
        btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_widget)
        
        edit_btn = QtWidgets.QPushButton("✏ Edit Selected")
        edit_btn.clicked.connect(self.edit_selected_subtitle)
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        
        save_all_btn = QtWidgets.QPushButton("💾 Save All Changes")
        save_all_btn.clicked.connect(self.save_all_subtitle_changes)
        btn_layout.addWidget(save_all_btn)
        
        layout.addWidget(btn_widget)
        
        self.subtitle_editor_loaded = False
        self.audio_keys_cache = None
        self.subtitle_loader_thread = None
        
        self.tabs.addTab(tab, self.tr("localization_editor"))
        self.global_search.searchChanged.connect(self.on_global_search_changed_for_subtitles)

    def cancel_subtitle_loading(self):
        """Cancel current subtitle loading operation"""
        if self.subtitle_loader_thread and self.subtitle_loader_thread.isRunning():
            self.subtitle_loader_thread.stop()
            self.subtitle_loader_thread.wait(2000)
        
        self.hide_subtitle_loading_ui()
        self.subtitle_status_label.setText("Loading cancelled")

    def show_subtitle_loading_ui(self):
        """Show loading UI elements"""
        self.subtitle_progress.setVisible(True)
        self.subtitle_cancel_btn.setVisible(True)
        
        self.subtitle_category_combo.setEnabled(False)
        self.orphaned_only_checkbox.setEnabled(False)

    def hide_subtitle_loading_ui(self):
        """Hide loading UI elements"""
        self.subtitle_progress.setVisible(False)
        self.subtitle_cancel_btn.setVisible(False)
        
        self.subtitle_category_combo.setEnabled(True)
        self.orphaned_only_checkbox.setEnabled(True)

    def populate_subtitle_editor_controls(self):
        """Populate category controls"""
        DEBUG.log("Populating subtitle editor controls")
        
        self.subtitle_category_combo.currentTextChanged.disconnect()
        
        try:
            categories = set()
            
            for file_info in self.all_subtitle_files.values():
                categories.add(file_info['category'])
            
            DEBUG.log(f"Found categories: {categories}")
            
            current_category = self.subtitle_category_combo.currentText()
            
            self.subtitle_category_combo.clear()
            self.subtitle_category_combo.addItem("All Categories")
            if categories:
                sorted_categories = sorted(categories)
                self.subtitle_category_combo.addItems(sorted_categories)
                
                if current_category and current_category != "All Categories":
                    if current_category in categories:
                        self.subtitle_category_combo.setCurrentText(current_category)
            
            DEBUG.log(f"Category combo: {self.subtitle_category_combo.count()} items")
            
        finally:
            self.subtitle_category_combo.currentTextChanged.connect(self.on_subtitle_filter_changed)
        
        self.load_subtitle_editor_data()

    
    def on_subtitle_filter_changed(self):
        """Handle filter changes with debouncing"""
        if hasattr(self, 'filter_timer'):
            self.filter_timer.stop()
        
        self.filter_timer = QtCore.QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.load_subtitle_editor_data)
        self.filter_timer.start(500)

    def build_audio_keys_cache(self):
        """Build cache of audio keys for orphaned subtitle detection"""
        if self.audio_keys_cache is not None:
            return self.audio_keys_cache
        
        DEBUG.log("Building audio keys cache...")
        self.audio_keys_cache = set()
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            if shortname:
                audio_key = os.path.splitext(shortname)[0]
                self.audio_keys_cache.add(audio_key)
        
        DEBUG.log(f"Built cache with {len(self.audio_keys_cache)} audio keys")
    
        sample_keys = list(self.audio_keys_cache)[:5]
        DEBUG.log(f"Sample audio keys: {sample_keys}")
        
        return self.audio_keys_cache

    def load_subtitle_editor_data(self):
        """Load subtitle data for editor asynchronously"""
        selected_category = self.subtitle_category_combo.currentText()
        orphaned_only = self.orphaned_only_checkbox.isChecked()
        modified_only = self.modified_only_checkbox.isChecked()
        with_audio_only = self.with_audio_only_checkbox.isChecked()
        search_text = self.get_global_search_text()
        
        DEBUG.log(f"Loading subtitle editor data: category={selected_category}, language={self.settings.data['subtitle_lang']}, orphaned={orphaned_only}, modified={modified_only}, with_audio={with_audio_only}")
        
 
        if orphaned_only and with_audio_only:
            self.with_audio_only_checkbox.setChecked(False)
            with_audio_only = False
            DEBUG.log("Disabled 'with_audio_only' because 'orphaned_only' is active")
        
        if self.subtitle_loader_thread and self.subtitle_loader_thread.isRunning():
            self.subtitle_loader_thread.stop()
            self.subtitle_loader_thread.wait(1000)

        if (orphaned_only or with_audio_only):
            if self.audio_keys_cache is None:
                self.build_audio_keys_cache()
            DEBUG.log(f"Audio cache has {len(self.audio_keys_cache) if self.audio_keys_cache else 0} keys")
        
        self.show_subtitle_loading_ui()
        self.subtitle_status_label.setText("Loading subtitles...")
        self.subtitle_progress.setValue(0)
        
        self.subtitle_table.setRowCount(0)

        self.subtitle_loader_thread = SubtitleLoaderThread(
            self, self.all_subtitle_files, self.locres_manager, 
            self.subtitles, self.original_subtitles,
            self.settings.data["subtitle_lang"], selected_category, orphaned_only, modified_only, with_audio_only,
            search_text, self.audio_keys_cache, self.modified_subtitles
        )
        
        self.subtitle_loader_thread.dataLoaded.connect(self.on_subtitle_data_loaded)
        self.subtitle_loader_thread.statusUpdate.connect(self.subtitle_status_label.setText)
        self.subtitle_loader_thread.progressUpdate.connect(self.subtitle_progress.setValue)
        
        self.subtitle_loader_thread.start()
    def on_subtitle_data_loaded(self, subtitles_to_show):
        """Handle loaded subtitle data"""
        self.hide_subtitle_loading_ui()
        
        self.populate_subtitle_table(subtitles_to_show)
        
        status_parts = [f"{len(subtitles_to_show)} subtitles"]
        
        filters_active = []
        if self.orphaned_only_checkbox.isChecked():
            filters_active.append("without audio")
        
        if self.modified_only_checkbox.isChecked():
            filters_active.append("modified only")
            
        if self.with_audio_only_checkbox.isChecked():
            filters_active.append("with audio only")
        
        search_text = self.get_global_search_text().strip()
        if search_text:
            filters_active.append(f"search: '{search_text}'")
        
        selected_category = self.subtitle_category_combo.currentText()
        if selected_category and selected_category != "All Categories":
            filters_active.append(f"category: {selected_category}")
        
        if filters_active:
            status_parts.append(f"({', '.join(filters_active)})")
        
        self.subtitle_status_label.setText(" ".join(status_parts))

    def populate_subtitle_table(self, subtitles_to_show):
        """Populate the subtitle table with data"""
        self.subtitle_table.setRowCount(len(subtitles_to_show))
        
        if len(subtitles_to_show) == 0:
            return
        
        sorted_items = sorted(subtitles_to_show.items())
        
        for row, (key, data) in enumerate(sorted_items):
            key_item = QtWidgets.QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.subtitle_table.setItem(row, 0, key_item)
            
            original_text = data['original']
            original_display = self.truncate_text(original_text, 150)
            original_item = QtWidgets.QTableWidgetItem(original_display)
            original_item.setFlags(original_item.flags() & ~QtCore.Qt.ItemIsEditable)
            original_item.setToolTip(original_text)
            self.subtitle_table.setItem(row, 1, original_item)
            
            current_text = data['current']
            current_display = self.truncate_text(current_text, 150)
            current_item = QtWidgets.QTableWidgetItem(current_display)
            current_item.setToolTip(current_text)
            self.subtitle_table.setItem(row, 2, current_item)
            
            has_audio = data.get('has_audio', False)
            audio_item = QtWidgets.QTableWidgetItem("🔊" if has_audio else "")
            audio_item.setFlags(audio_item.flags() & ~QtCore.Qt.ItemIsEditable)
            audio_item.setToolTip(self.tr("has_audio_file") if has_audio else self.tr("no_audio_file"))
            audio_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.subtitle_table.setItem(row, 3, audio_item)
            
            is_modified = data.get('is_modified', False)
            if is_modified:
                for col in range(4):
                    item = self.subtitle_table.item(row, col)
                    if item:
                        item.setBackground(QtGui.QColor(255, 255, 200))
            
            search_text = self.get_global_search_text().lower().strip()
            if search_text:
                if (search_text in key.lower() or 
                    search_text in original_text.lower() or 
                    search_text in current_text.lower()):
                    for col in range(4):
                        item = self.subtitle_table.item(row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)

    def truncate_text(self, text, max_length):
        """Truncate text for display"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def edit_subtitle_from_table(self, item):
        """Edit subtitle from table double-click"""
        if not item:
            return
            
        try:
            row = item.row()
            key = self.subtitle_table.item(row, 0).text()
            current_text = self.subtitle_table.item(row, 2).toolTip() or self.subtitle_table.item(row, 2).text()
            original_text = self.subtitle_table.item(row, 1).toolTip() or self.subtitle_table.item(row, 1).text()
            
            stored_key = key
            stored_row = row
            
            editor = SubtitleEditor(self, key, current_text, original_text)
            if editor.exec_() == QtWidgets.QDialog.Accepted:
                new_text = editor.get_text()
                self.subtitles[key] = new_text
                
                if new_text != original_text:
                    self.modified_subtitles.add(key)
                else:
                    self.modified_subtitles.discard(key)
                
                target_row = self.find_table_row_by_key(stored_key)
                if target_row >= 0:
                    try:
                        current_item = self.subtitle_table.item(target_row, 2)
                        if current_item:
                            display_text = self.truncate_text(new_text, 150)
                            current_item.setText(display_text)
                            current_item.setToolTip(new_text)
                            
                            if new_text != original_text:
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(QtGui.QColor(255, 255, 200))
                            else:
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(QtGui.QColor(255, 255, 255))
                                        
                    except RuntimeError as e:
                        DEBUG.log(f"Table item was deleted during update: {e}", "WARNING")
                        self.load_subtitle_editor_data()
                else:
                    DEBUG.log("Table row not found after edit, refreshing")
                    self.load_subtitle_editor_data()
                
                self.update_status()
                
        except RuntimeError as e:
            DEBUG.log(f"Error in edit_subtitle_from_table: {e}", "ERROR")
            self.load_subtitle_editor_data()

    def find_table_row_by_key(self, target_key):
        """Find table row by subtitle key"""
        for row in range(self.subtitle_table.rowCount()):
            try:
                key_item = self.subtitle_table.item(row, 0)
                if key_item and key_item.text() == target_key:
                    return row
            except RuntimeError:
                continue
        return -1

    def edit_selected_subtitle(self):
        """Edit currently selected subtitle"""
        current_row = self.subtitle_table.currentRow()
        if current_row >= 0:
            item = self.subtitle_table.item(current_row, 0)
            if item:
                self.edit_subtitle_from_table(item)

    def save_all_subtitle_changes(self):
        """Save all subtitle changes to working files"""
        self.save_subtitles_to_file()
        QtWidgets.QMessageBox.information(self, "Saved", "All subtitle changes have been saved!")

    def show_subtitle_table_context_menu(self, pos):
        """Show context menu for subtitle table"""
        item = self.subtitle_table.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        key = self.subtitle_table.item(row, 0).text()
        has_audio = self.subtitle_table.item(row, 3).text() == "🔊"
        
        menu = QtWidgets.QMenu()
        
        edit_action = menu.addAction("✏ Edit Subtitle")
        edit_action.triggered.connect(lambda: self.edit_subtitle_from_table(item))
        
        revert_action = menu.addAction("↩ Revert to Original")
        revert_action.triggered.connect(lambda: self.revert_subtitle_from_table(row, key))
        
        menu.addSeparator()
        
        if has_audio:
            goto_audio_action = menu.addAction("🔊 Go to Audio File")
            goto_audio_action.triggered.connect(lambda: self.go_to_audio_file(key))
        
        menu.addSeparator()
        
        copy_key_action = menu.addAction("📋 Copy Key")
        copy_key_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(key))
        
        copy_text_action = menu.addAction("📋 Copy Text")
        current_text = self.subtitle_table.item(row, 2).toolTip() or self.subtitle_table.item(row, 2).text()
        copy_text_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(current_text))
        
        menu.exec_(self.subtitle_table.mapToGlobal(pos))

    def go_to_audio_file(self, subtitle_key):
        """Navigate to audio file corresponding to subtitle"""
        DEBUG.log(f"Looking for audio file for subtitle key: {subtitle_key}")
        
        target_entry = None
        target_lang = None
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            if shortname:
                audio_key = os.path.splitext(shortname)[0]
                if audio_key == subtitle_key:
                    target_entry = entry
                    target_lang = entry.get("Language", "SFX")
                    break
        
        if not target_entry:
            QtWidgets.QMessageBox.information(
                self, "Audio Not Found", 
                f"Could not find audio file for subtitle key: {subtitle_key}"
            )
            return
        
        DEBUG.log(f"Found audio file: {target_entry.get('ShortName')} in language: {target_lang}")
        
        for i in range(self.tabs.count()):
            tab_text = self.tabs.tabText(i)
            if target_lang in tab_text:
                self.tabs.setCurrentIndex(i)
                
                if target_lang not in self.populated_tabs:
                    self.populate_tree(target_lang)
                    self.populated_tabs.add(target_lang)
                
                self.find_and_select_audio_item(target_lang, target_entry)
                
                self.status_bar.showMessage(f"Navigated to audio file: {target_entry.get('ShortName')}", 3000)
                return
        
        QtWidgets.QMessageBox.information(
            self, "Tab Not Found", 
            f"Could not find tab for language: {target_lang}"
        )

    def find_and_select_audio_item(self, lang, target_entry):
        """Find and select audio item in tree"""
        if lang not in self.tab_widgets:
            return
        
        tree = self.tab_widgets[lang]["tree"]
        target_id = target_entry.get("Id", "")
        target_shortname = target_entry.get("ShortName", "")
        
        def search_items(parent_item):
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                
                if item.childCount() == 0:
                    try:
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            if (entry.get("Id") == target_id or 
                                entry.get("ShortName") == target_shortname):
                                tree.clearSelection()
                                tree.setCurrentItem(item)
                                item.setSelected(True)
                                
                                parent = item.parent()
                                if parent:
                                    parent.setExpanded(True)
                                
                                tree.scrollToItem(item)
                                self.on_selection_changed(lang)
                                
                                return True
                    except RuntimeError:
                        continue
                else:
                    if search_items(item):
                        return True
            return False
        
        try:
            root = tree.invisibleRootItem()
            if not search_items(root):
                DEBUG.log(f"Could not find item in tree for: {target_shortname}")
        except RuntimeError:
            pass

    def revert_subtitle_from_table(self, row, key):
        """Revert subtitle to original from table"""
        original_text = self.subtitle_table.item(row, 1).toolTip() or self.subtitle_table.item(row, 1).text()
        
        self.subtitles[key] = original_text
        self.modified_subtitles.discard(key)
        
        current_item = self.subtitle_table.item(row, 2)
        current_item.setText(self.truncate_text(original_text, 150))
        current_item.setToolTip(original_text)
        
        for col in range(4):
            item = self.subtitle_table.item(row, col)
            if item:
                item.setBackground(QtGui.QColor(255, 255, 255))
        
        self.update_status()

 
    def process_wem_files(self):
        wwise_root = self.wwise_path_edit_old.text()
        if not wwise_root or not os.path.exists(wwise_root):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid WWISE folder path!")
            return
            
        progress = ProgressDialog(self, "Processing WEM Files")
        progress.show()
        
        # Find SFX paths
        sfx_paths = []
        for root, dirs, files in os.walk(wwise_root):
            if root.endswith(".cache\\Windows\\SFX"):
                sfx_paths.append(root)
                
        if not sfx_paths:
            progress.close()
            QtWidgets.QMessageBox.warning(self, "Error", "No .cache/Windows/SFX/ folders found!")
            return
        

        selected_language = self.settings.data.get("wem_process_language", "english")
        DEBUG.log(f"Selected WEM process language: {selected_language}")
        

        if selected_language == "english":
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Francais")
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
            voice_lang_filter = ["English(US)"]
        
        target_dir_sfx = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
        
        os.makedirs(target_dir_voice, exist_ok=True)
        os.makedirs(target_dir_sfx, exist_ok=True)
        
        all_wem_files = []
        vo_wem_files = []
        
        for sfx_path in sfx_paths:
            for filename in os.listdir(sfx_path):
                if filename.endswith(".wem"):
                    base_name = os.path.splitext(filename)[0]
                    all_wem_files.append(base_name)
                    if base_name.startswith("VO_"):
                        vo_wem_files.append(base_name)
        
        DEBUG.log(f"Found {len(all_wem_files)} total WEM files on disk")
        DEBUG.log(f"Found {len(vo_wem_files)} VO WEM files on disk")
        DEBUG.log(f"First 10 VO WEM files on disk: {vo_wem_files[:10]}")
        
        voice_mapping = {}  
        sfx_mapping = {}    
        voice_files_in_db = []

        vo_from_streamed = 0
        vo_from_media_files = 0
        vo_skipped_wrong_lang = 0
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            base_shortname = os.path.splitext(shortname)[0]
            file_id = entry.get("Id", "")
            language = entry.get("Language", "")
            source = entry.get("Source", "")
            
            file_info = {
                'id': file_id,
                'language': language,
                'source': source,
                'original_name': shortname
            }

            if base_shortname.startswith("VO_"):

                if language in voice_lang_filter:
                    voice_mapping[base_shortname] = file_info
                    voice_files_in_db.append(base_shortname)
                    
                    if source == "StreamedFiles":
                        vo_from_streamed += 1
                        DEBUG.log(f"Added StreamedFiles VO: {base_shortname} -> ID {file_id} ({language})")
                    elif source == "MediaFilesNotInAnyBank":
                        vo_from_media_files += 1
                        if vo_from_media_files <= 10:  
                            DEBUG.log(f"Added MediaFilesNotInAnyBank VO: {base_shortname} -> ID {file_id} ({language})")
                else:
          
                    vo_skipped_wrong_lang += 1
                    if vo_skipped_wrong_lang <= 5: 
                        DEBUG.log(f"Skipped VO (wrong language): {base_shortname} -> ID {file_id} ({language})")
            
            elif language == "SFX" or (source == "MediaFilesNotInAnyBank" and not base_shortname.startswith("VO_")):
                sfx_mapping[base_shortname] = file_info
        
        DEBUG.log(f"Voice files from StreamedFiles: {vo_from_streamed}")
        DEBUG.log(f"Voice files from MediaFilesNotInAnyBank: {vo_from_media_files}")
        DEBUG.log(f"Voice files skipped (wrong language): {vo_skipped_wrong_lang}")
        DEBUG.log(f"Total voice files for {selected_language}: {len(voice_files_in_db)}")
        DEBUG.log(f"First 10 voice files in database: {voice_files_in_db[:10]}")

        exact_matches = []
        potential_matches = []
        
        for wem_file in vo_wem_files:
            if wem_file in voice_mapping:
                exact_matches.append(wem_file)
            else:
   
                wem_without_hex = wem_file

                if '_' in wem_file:
                    parts = wem_file.split('_')
   
                    if len(parts) > 1 and len(parts[-1]) == 8:
                        try:
                            int(parts[-1], 16) 
                            wem_without_hex = '_'.join(parts[:-1])
                            DEBUG.log(f"Removing hex suffix: {wem_file} -> {wem_without_hex}")
                        except ValueError:
                            pass
                
                if wem_without_hex in voice_mapping and wem_without_hex != wem_file:
                    potential_matches.append((wem_file, wem_without_hex))
        
        DEBUG.log(f"Exact matches found: {len(exact_matches)}")
        DEBUG.log(f"Potential matches (after removing hex): {len(potential_matches)}")
        DEBUG.log(f"First 5 exact matches: {exact_matches[:5]}")
        DEBUG.log(f"First 5 potential matches: {potential_matches[:5]}")

        for wem_file, db_file in potential_matches:
            if db_file in voice_mapping:
                voice_mapping[wem_file] = voice_mapping[db_file].copy()
                voice_mapping[wem_file]['matched_via'] = f"hex_removal_from_{db_file}"
                DEBUG.log(f"Added potential match: {wem_file} -> {voice_mapping[wem_file]['id']} (via {db_file}) [{voice_mapping[wem_file]['language']}]")
        
        DEBUG.log(f"Voice mapping after adding potential matches: {len(voice_mapping)} files")

        name_to_ids = {}
        for name, info in voice_mapping.items():
            base_name = name.split('_')
            if len(base_name) > 3:
                check_name = '_'.join(base_name[:4]) 
                if check_name not in name_to_ids:
                    name_to_ids[check_name] = []
                name_to_ids[check_name].append((info['id'], info['language']))
        
        for name, ids in name_to_ids.items():
            if len(ids) > 1:
                DEBUG.log(f"WARNING: Multiple IDs for similar name '{name}': {ids}")
        
        self.converter_status.clear()
        self.converter_status.append(f"=== Processing WEM Files for {selected_language.capitalize()} ===")
        self.converter_status.append(f"Voice target: {target_dir_voice}")
        self.converter_status.append(f"SFX target: {target_dir_sfx}")
        self.converter_status.append("")
        self.converter_status.append(f"Analysis Results:")
        self.converter_status.append(f"  WEM files on disk: {len(all_wem_files)} total, {len(vo_wem_files)} VO files")
        self.converter_status.append(f"  Voice files in database for {selected_language}: {len(voice_files_in_db)}")
        self.converter_status.append(f"    - From StreamedFiles: {vo_from_streamed}")
        self.converter_status.append(f"    - From MediaFilesNotInAnyBank: {vo_from_media_files}")
        self.converter_status.append(f"    - Skipped (wrong language): {vo_skipped_wrong_lang}")
        self.converter_status.append(f"  Exact matches: {len(exact_matches)}")
        self.converter_status.append(f"  Potential matches (hex removal): {len(potential_matches)}")
        self.converter_status.append(f"  Total mappable files: {len(exact_matches) + len(potential_matches)}")
        self.converter_status.append("")
        
        processed = 0
        voice_processed = 0
        sfx_processed = 0
        skipped = 0
        renamed_count = 0
        total_files = len(all_wem_files)
        
        for sfx_path in sfx_paths:
            DEBUG.log(f"Processing folder: {sfx_path}")
            
            for filename in os.listdir(sfx_path):
                if filename.endswith(".wem"):
                    src_path = os.path.join(sfx_path, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    file_info = None
                    dest_filename = filename
                    target_dir = target_dir_sfx
                    is_voice = base_name.startswith("VO_")
                    classification = "Unknown"
                    
                    if is_voice:
                        target_dir = target_dir_voice
                        classification = f"Voice ({selected_language})"

                        if base_name in voice_mapping:
                            file_info = voice_mapping[base_name]
                            dest_filename = f"{file_info['id']}.wem"
                            match_method = file_info.get('matched_via', 'exact_match')
                            file_language = file_info.get('language', 'Unknown')
                            classification += f" (ID {file_info['id']}, {match_method}, {file_language})"
                            renamed_count += 1
                            DEBUG.log(f"FOUND MATCH: {filename} -> {dest_filename} ({match_method}) [Language: {file_language}]")
                        else:
                            classification += " (no ID found - keeping original name)"
                            DEBUG.log(f"NO MATCH FOUND for {filename}")
                            
                    else:

                        classification = "SFX"
                        search_keys = [
                            base_name,
                            base_name.rsplit("_", 1)[0] if "_" in base_name else base_name,
                        ]
                        
                        for search_key in search_keys:
                            if search_key in sfx_mapping:
                                file_info = sfx_mapping[search_key]
                                dest_filename = f"{file_info['id']}.wem"
                                classification += f" (matched '{search_key}' -> ID {file_info['id']})"
                                renamed_count += 1
                                break
                        
                        if not file_info:
                            classification += " (no ID found - keeping original name)"
                    
                    dest_path = os.path.join(target_dir, dest_filename)
                    
                    try:

                        if os.path.exists(dest_path):
                            base_dest_name = os.path.splitext(dest_filename)[0]
                            counter = 1
                            while os.path.exists(os.path.join(target_dir, f"{base_dest_name}_{counter}.wem")):
                                counter += 1
                            dest_filename = f"{base_dest_name}_{counter}.wem"
                            dest_path = os.path.join(target_dir, dest_filename)
                            classification += " (duplicate renamed)"
                        
                        shutil.move(src_path, dest_path)
                        processed += 1
                        
                        if is_voice:
                            voice_processed += 1
                            icon = "🎙"
                        else:
                            sfx_processed += 1
                            icon = "🔊"
                        
                        progress.set_progress(int((processed / total_files) * 100), f"Processing {filename}...")
                        
                        self.converter_status.append(f"{icon} {classification}: {filename} → {dest_filename}")
                        QtWidgets.QApplication.processEvents()
                        
                    except Exception as e:
                        self.converter_status.append(f"✗ ERROR: {filename} - {str(e)} [{classification}]")
                        skipped += 1
                        DEBUG.log(f"Error processing {filename}: {e}", "ERROR")
                        
        progress.close()
        
        success_rate = (renamed_count / voice_processed * 100) if voice_processed > 0 else 0
        
        self.converter_status.append("")
        self.converter_status.append("=== Processing Complete ===")
        self.converter_status.append(f"Total files processed: {processed}")
        self.converter_status.append(f"Voice files ({selected_language}): {voice_processed}")
        self.converter_status.append(f"SFX files: {sfx_processed}")
        self.converter_status.append(f"Files renamed to ID: {renamed_count}")
        self.converter_status.append(f"Files kept original name: {processed - renamed_count}")
        self.converter_status.append(f"Voice rename success rate: {success_rate:.1f}%")
        if skipped > 0:
            self.converter_status.append(f"Skipped/Errors: {skipped}")
        
        QtWidgets.QMessageBox.information(
            self, "Processing Complete",
            f"Processed {processed} files for {selected_language.capitalize()} language.\n"
            f"Voice files: {voice_processed}\n"
            f"Renamed to ID: {renamed_count}\n"
            f"Success rate: {success_rate:.1f}%\n"
            f"Kept original names: {processed - renamed_count}"
        )

    def save_subtitles_to_file(self):

        DEBUG.log("=== Saving Subtitles (Fixed) ===")
        
        if not self.modified_subtitles:
            DEBUG.log("No modified subtitles to save")
            return
        
        try:
            saved_files = 0
            current_language = self.settings.data["subtitle_lang"]

            files_to_save = {}
            
            for modified_key in self.modified_subtitles:
                found_in_file = None
                
                for file_key, file_info in self.all_subtitle_files.items():
                    if file_info['language'] != current_language:
                        continue
                    
                    if '.original.' in file_info['filename']:
                        continue

                    working_path = file_info['path'].replace('.locres', '_working.locres')
                    check_path = working_path if os.path.exists(working_path) else file_info['path']
                    
                    file_subtitles = self.locres_manager.export_locres(check_path)
                    if modified_key in file_subtitles:
                        found_in_file = file_info
                        break
                
                if found_in_file:
                    file_path = found_in_file['path']
                    if file_path not in files_to_save:

                        working_path = file_path.replace('.locres', '_working.locres')
                        source_path = working_path if os.path.exists(working_path) else file_path
                        
                        files_to_save[file_path] = {
                            'file_info': found_in_file,
                            'all_subtitles': self.locres_manager.export_locres(source_path),
                            'working_path': working_path
                        }

                    files_to_save[file_path]['all_subtitles'][modified_key] = self.subtitles[modified_key]
                else:
                    DEBUG.log(f"Warning: Could not find source file for modified key: {modified_key}", "WARNING")
            
            DEBUG.log(f"Found {len(files_to_save)} files to save for language {current_language}")
            
            if not files_to_save:
                DEBUG.log("No files found to save modifications", "WARNING")
                return

            for file_path, data in files_to_save.items():
                file_info = data['file_info']
                all_subtitles = data['all_subtitles']
                working_path = data['working_path']
                
                DEBUG.log(f"Saving working copy: {working_path}")

                os.makedirs(os.path.dirname(working_path), exist_ok=True)

                if not os.path.exists(working_path):
                    shutil.copy2(file_path, working_path)
                    DEBUG.log(f"Created working copy from original: {file_path}")

                success = self.locres_manager.import_locres(working_path, all_subtitles)
                
                if success:
                    saved_files += 1
                    DEBUG.log(f"Successfully saved {file_info['filename']}")
                else:
                    DEBUG.log(f"Failed to save {file_info['filename']}", "ERROR")

            self.update_status()
            
            if saved_files > 0:
                self.status_bar.showMessage(f"Saved {saved_files} subtitle files", 3000)
                DEBUG.log(f"Successfully saved {saved_files} files")

            if hasattr(self, 'subtitle_table'):
                QtCore.QTimer.singleShot(100, self.load_subtitle_editor_data)

            for lang in self.populated_tabs:
                self.populate_tree(lang)
                
        except Exception as e:
            DEBUG.log(f"Save error: {str(e)}", "ERROR")
            DEBUG.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Save Error", str(e))
            
        DEBUG.log("=== Save Complete ===")

    def show_settings_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("settings"))
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        lang_combo = QtWidgets.QComboBox()
        lang_combo.addItem("English", "en")
        lang_combo.addItem("Русский", "ru")
        lang_combo.addItem("Polski", "pl")
        current_lang = self.settings.data["ui_language"]
        if current_lang == "en":
            lang_combo.setCurrentIndex(0)
        elif current_lang == "ru":
            lang_combo.setCurrentIndex(1)
        elif current_lang == "pl":
            lang_combo.setCurrentIndex(2)
        else:
            lang_combo.setCurrentIndex(0)
        
        theme_combo = QtWidgets.QComboBox()
        theme_combo.addItem(f"{self.tr("light")}", "light")
        theme_combo.addItem(f"{self.tr("dark")}", "dark")
        theme_combo.setCurrentIndex(0 if self.settings.data["theme"] == "light" else 1)
        
        subtitle_combo = QtWidgets.QComboBox()
        subtitle_langs = [
            "de-DE", "en", "es-ES", "es-MX", "fr-FR", "it-IT", "ja-JP", "ko-KR",
            "pl-PL", "pt-BR", "ru-RU", "tr-TR", "zh-CN", "zh-TW"
        ]
        subtitle_combo.addItems(subtitle_langs)
        subtitle_combo.setCurrentText(self.settings.data["subtitle_lang"])
        
        game_path_widget = QtWidgets.QWidget()
        game_path_layout = QtWidgets.QHBoxLayout(game_path_widget)
        game_path_layout.setContentsMargins(0, 0, 0, 0)
        
        game_path_edit = QtWidgets.QLineEdit()
        game_path_edit.setText(self.settings.data.get("game_path", ""))
        game_path_edit.setPlaceholderText("Path to game root folder")
        
        game_path_btn = QtWidgets.QPushButton(self.tr("browse"))
        game_path_btn.clicked.connect(lambda: self.browse_game_path(game_path_edit))
        
        game_path_layout.addWidget(game_path_edit)
        game_path_layout.addWidget(game_path_btn)

        auto_save_check = QtWidgets.QCheckBox(self.tr("auto_save"))
        auto_save_check.setChecked(self.settings.data.get("auto_save", True))

        french_audio_check = QtWidgets.QCheckBox(self.tr("rename_french_audio"))
        french_audio_check.setChecked(self.settings.data.get("rename_french_audio", False))
        french_audio_check.setToolTip("When enabled, French VO files will also be renamed to their ID when processing WEM files")
        
        layout.addRow(f"{self.tr("interface_language")}", lang_combo)
        layout.addRow(f"{self.tr("theme")}", theme_combo)
        layout.addRow(f"{self.tr("subtitle_language")}", subtitle_combo)
        layout.addRow(f"{self.tr("game_path")}", game_path_widget)
        layout.addRow(auto_save_check)
        wem_lang_combo = QtWidgets.QComboBox()
        wem_lang_combo.addItem("English (US)", "english")
        wem_lang_combo.addItem("Francais (France)", "french")
        current_wem_lang = self.settings.data.get(f"{self.tr("wem_process_language")}", "english")
        wem_lang_combo.setCurrentIndex(0 if current_wem_lang == "english" else 1)
        wem_lang_combo.setToolTip(f"{self.tr("wemprocces_desc")}")

        layout.addRow(f"{self.tr("wem_process_language")}", wem_lang_combo)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addRow(btn_box)
        
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            old_lang = self.settings.data["subtitle_lang"]
            old_ui_lang = self.settings.data["ui_language"]
            old_auto_save = self.settings.data.get("auto_save", True)
            old_wem_lang = self.settings.data.get("wem_process_language", "english")
            
            self.settings.data["ui_language"] = lang_combo.currentData()
            self.settings.data["theme"] = theme_combo.currentData()
            self.settings.data["subtitle_lang"] = subtitle_combo.currentText()
            self.settings.data["game_path"] = game_path_edit.text()
            self.settings.data["auto_save"] = auto_save_check.isChecked()
            self.settings.data["wem_process_language"] = wem_lang_combo.currentData() 
            self.settings.save()

            if wem_lang_combo.currentData() != old_wem_lang:
                DEBUG.log(f"WEM process language changed: {old_wem_lang} → {wem_lang_combo.currentData()}")

            if auto_save_check.isChecked() != old_auto_save:
                DEBUG.log(f"Auto-save setting changed: {old_auto_save} → {auto_save_check.isChecked()}")
                self.update_auto_save_timer()

            if lang_combo.currentData() != old_ui_lang:
                self.current_lang = lang_combo.currentData()
                self.update_ui_language()

            self.apply_settings()

            if subtitle_combo.currentText() != old_lang:
                DEBUG.log(f"Subtitle language changed from {old_lang} to {subtitle_combo.currentText()}")
                self.load_subtitles()
                self.modified_subtitles.clear()

                for lang in list(self.populated_tabs):
                    self.populate_tree(lang)
                    
                self.update_status()

    def browse_game_path(self, edit_widget):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("select_game_path"), 
            edit_widget.text() or ""
        )
        
        if folder:
            edit_widget.setText(folder)

    def update_ui_language(self):
        self.setWindowTitle(self.tr("app_title"))
        
        # update menus
        self.menuBar().clear()
        self.create_menu_bar()
        
        # update tabs
        for i, (lang, widgets) in enumerate(self.tab_widgets.items()):
            if i < self.tabs.count() - 1:
                # update filter combo
                current_filter = widgets["filter_combo"].currentIndex()
                widgets["filter_combo"].clear()
                widgets["filter_combo"].addItems([
                    self.tr("all_files"), 
                    self.tr("with_subtitles"), 
                    self.tr("without_subtitles"), 
                    self.tr("modified"),
                    self.tr("modded")
                ])
                widgets["filter_combo"].setCurrentIndex(current_filter)
                
                tab_widget = self.tabs.widget(i)
                if tab_widget:
                    self.update_group_boxes_recursively(tab_widget)

    def update_group_boxes_recursively(self, widget):

        if isinstance(widget, QtWidgets.QGroupBox):
            title = widget.title()

            if "subtitle" in title.lower() or "preview" in title.lower():
                widget.setTitle(self.tr("subtitle_preview"))
            elif "file" in title.lower() or "info" in title.lower():
                widget.setTitle(self.tr("file_info"))

        for child in widget.findChildren(QtWidgets.QWidget):
            if isinstance(child, QtWidgets.QGroupBox):
                title = child.title()

                if "subtitle" in title.lower() or "preview" in title.lower():
                    child.setTitle(self.tr("subtitle_preview"))
                elif "file" in title.lower() or "info" in title.lower():
                    child.setTitle(self.tr("file_info"))

    def update_status(self):
        total_files = len(self.all_files)
        total_subtitles = len(self.subtitles)
        modified = len(self.modified_subtitles)
        
        status_text = f"Files: {total_files} | Subtitles: {total_subtitles}"
        if modified > 0:
            status_text += f" | Modified: {modified}"
            
        self.status_bar.showMessage(status_text)

    def load_all_soundbank_files(self, path):
        DEBUG.log(f"Loading soundbank files from: {path}")
        all_files = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            soundbanks_info = data.get("SoundBanksInfo", {})

            streamed_files = soundbanks_info.get("StreamedFiles", [])
            for file_entry in streamed_files:
                file_entry["Source"] = "StreamedFiles"
            all_files.extend(streamed_files)
            DEBUG.log(f"Loaded {len(streamed_files)} StreamedFiles")

            media_files = soundbanks_info.get("MediaFilesNotInAnyBank", [])
            for file_entry in media_files:
                file_entry["Source"] = "MediaFilesNotInAnyBank"
            all_files.extend(media_files)
            DEBUG.log(f"Loaded {len(media_files)} MediaFilesNotInAnyBank")
            
            DEBUG.log(f"Total files loaded: {len(all_files)}")
            return all_files
            
        except Exception as e:
            DEBUG.log(f"Error loading soundbank: {e}", "ERROR")
            return []

    def group_by_language(self):
        entries_by_lang = {}
        for entry in self.all_files:
            lang = entry.get("Language", "SFX")
            entries_by_lang.setdefault(lang, []).append(entry)
            
        DEBUG.log(f"Files grouped by language: {list(entries_by_lang.keys())}")
        for lang, entries in entries_by_lang.items():
            DEBUG.log(f"  {lang}: {len(entries)} files")
            
        return entries_by_lang

    def get_current_language(self):
   
        current_index = self.tabs.currentIndex()
        if current_index >= 0 and current_index < len(self.tab_widgets):
            languages = list(self.tab_widgets.keys())
            if current_index < len(languages):
                return languages[current_index]
        return None

    def populate_tree(self, lang):
        DEBUG.log(f"Populating tree for language: {lang}")
        
        if lang not in self.tab_widgets:
            DEBUG.log(f"Language {lang} not in tab_widgets", "WARNING")
            return
            
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        selected_keys = []
        try:
            for item in tree.selectedItems():
                if item.childCount() == 0:  # Leaf item
                    entry = item.data(0, QtCore.Qt.UserRole)
                    if entry:
                        shortname = entry.get("ShortName", "")
                        key = os.path.splitext(shortname)[0]
                        selected_keys.append(key)
        except RuntimeError:

            pass
        filter_type = widgets["filter_combo"].currentIndex()
        sort_type = widgets["sort_combo"].currentIndex()
        search_text = self.global_search.text().lower()
        
        try:
            tree.clear()
        except RuntimeError:
            DEBUG.log("Error clearing tree, creating new tree", "WARNING")
   
            return
        
        filtered_entries = []
        for entry in self.entries_by_lang.get(lang, []):
            shortname = entry.get("ShortName", "")
            key = os.path.splitext(shortname)[0]
            subtitle = self.subtitles.get(key, "")
            if lang != "SFX":
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{entry.get('Id', '')}.wem")
            else:
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{entry.get('Id', '')}.wem")
            has_mod_audio = os.path.exists(mod_wem_path)
            
            if filter_type == 1 and not subtitle:  # With subtitles
                continue
            elif filter_type == 2 and subtitle:  # Without subtitles
                continue
            elif filter_type == 3 and key not in self.modified_subtitles:  # Modified
                continue
            elif filter_type == 4 and not has_mod_audio:  # Modded (audio)
                continue
                
            if search_text:
                searchable = f"{entry.get('Id', '')} {shortname} {subtitle}".lower()
                if search_text not in searchable:
                    continue
                    
            filtered_entries.append(entry)
        
        DEBUG.log(f"Filtered entries: {len(filtered_entries)} out of {len(self.entries_by_lang.get(lang, []))}")
        
        if sort_type == 0:  # Name A-Z
            filtered_entries.sort(key=lambda x: x.get("ShortName", "").lower())
        elif sort_type == 1:  # Name Z-A
            filtered_entries.sort(key=lambda x: x.get("ShortName", "").lower(), reverse=True)
        elif sort_type == 2:  # ID ascending
            filtered_entries.sort(key=lambda x: int(x.get("Id", "0")))
        elif sort_type == 3:  # ID descending
            filtered_entries.sort(key=lambda x: int(x.get("Id", "0")), reverse=True)
        
        groups = {}
        vo_count = 0
        for entry in filtered_entries:
            shortname = entry.get("ShortName", "")
            parts = shortname.replace(".wav", "").split("_")
            
            if len(parts) >= 3 and parts[0] == "VO":
                group = f"{parts[1]}_{parts[2]}"
                vo_count += 1
            else:
                group = "Other"
                
            groups.setdefault(group, []).append(entry)
        
        DEBUG.log(f"VO files found: {vo_count}")
        DEBUG.log(f"Groups created: {len(groups)}")
        
        # Populate tree
        for group_name in sorted(groups.keys()):
            group_item = QtWidgets.QTreeWidgetItem(tree, [f"{group_name} ({len(groups[group_name])})", "", "", ""])
            group_item.setExpanded(True)
            
            for entry in groups[group_name]:
                shortname = entry.get("ShortName", "")
                key = os.path.splitext(shortname)[0]
                subtitle = self.subtitles.get(key, "")
                
                mod_status = ""
                if lang != "SFX":
                    mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{entry.get('Id', '')}.wem")
                else:
                    mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{entry.get('Id', '')}.wem")
                if os.path.exists(mod_wem_path):
                    mod_status = "♪"
                
                item = QtWidgets.QTreeWidgetItem(group_item, [
                    shortname,
                    entry.get("Id", ""),
                    subtitle,
                    "✓" + mod_status if key in self.modified_subtitles else mod_status
                ])
                

                item.setData(0, QtCore.Qt.UserRole, entry)
                

                if not subtitle:
                    item.setForeground(2, QtGui.QBrush(QtGui.QColor(128, 128, 128)))
                    
                if entry.get("Source") == "MediaFilesNotInAnyBank":
                    item.setForeground(0, QtGui.QBrush(QtGui.QColor(100, 100, 200)))
        
        if selected_keys:
                self.restore_tree_selection(tree, selected_keys)
        subtitle_count = sum(1 for entry in filtered_entries if self.subtitles.get(os.path.splitext(entry.get("ShortName", ""))[0], ""))
        widgets["stats_label"].setText(f"Showing {len(filtered_entries)} of {len(self.entries_by_lang.get(lang, []))} files | Subtitles: {subtitle_count}")
    
    def restore_tree_selection(self, tree, target_keys):
        """Restore tree selection after refresh"""
        def search_and_select(parent_item):
            for i in range(parent_item.childCount()):
                try:
                    item = parent_item.child(i)
                    if item.childCount() == 0:  # Leaf item
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            shortname = entry.get("ShortName", "")
                            key = os.path.splitext(shortname)[0]
                            if key in target_keys:
                                item.setSelected(True)
                                tree.setCurrentItem(item)
                                return True
                    else:
                        if search_and_select(item):
                            return True
                except RuntimeError:
                    continue
            return False
        
        try:
            root = tree.invisibleRootItem()
            search_and_select(root)
        except RuntimeError:
            pass

    def on_selection_changed(self, lang):
        """Updated selection handler without summary"""
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            widgets["play_mod_btn"].hide()
            return
            
        item = items[0]
        if item.childCount() > 0:  # Group item
            widgets["play_mod_btn"].hide()
            return
            
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            widgets["play_mod_btn"].hide()
            return

        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        subtitle = self.subtitles.get(key, "")
        original_subtitle = self.original_subtitles.get(key, "")
        
        widgets["subtitle_text"].setPlainText(subtitle)

        if original_subtitle and original_subtitle != subtitle:
            widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
            widgets["original_subtitle_label"].show()
        else:
            widgets["original_subtitle_label"].hide()
        
        # Basic file info
        widgets["info_labels"]["id"].setText(entry.get("Id", ""))
        widgets["info_labels"]["name"].setText(shortname)
        widgets["info_labels"]["path"].setText(entry.get("Path", ""))
        widgets["info_labels"]["source"].setText(entry.get("Source", ""))
        
        # Check for mod file
        file_id = entry.get("Id", "")
        if lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        
        has_mod = os.path.exists(mod_wem_path)
        widgets["play_mod_btn"].setVisible(has_mod)
        
        self.load_audio_comparison_info(file_id, lang, widgets)
    def load_audio_comparison_info(self, file_id, lang, widgets):

        original_wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        
        if lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        
        original_info = None
        if os.path.exists(original_wem_path):
            original_info = self.get_wem_audio_info_with_markers(original_wem_path)
            if original_info:
                original_info['file_size'] = os.path.getsize(original_wem_path)
        
        modified_info = None
        modified_exists = os.path.exists(mod_wem_path)
        if modified_exists:
            modified_info = self.get_wem_audio_info_with_markers(mod_wem_path)
            if modified_info:
                modified_info['file_size'] = os.path.getsize(mod_wem_path)
        
        if original_info:
            formatted_original = self.format_audio_info(original_info)
            widgets["original_info_labels"]["duration"].setText(formatted_original["duration"])
            widgets["original_info_labels"]["sample_rate"].setText(formatted_original["sample_rate"])
            widgets["original_info_labels"]["bitrate"].setText(formatted_original["bitrate"])
            widgets["original_info_labels"]["channels"].setText(formatted_original["channels"])
            
            size_kb = original_info['file_size'] / 1024
            if size_kb >= 1024:
                widgets["original_info_labels"]["size"].setText(f"{size_kb/1024:.1f} MB")
            else:
                widgets["original_info_labels"]["size"].setText(f"{size_kb:.1f} KB")
            
            original_markers = self.format_markers_for_display(original_info.get('markers', []))
            widgets["original_markers_list"].clear()
            if original_markers:
                widgets["original_markers_list"].addItems(original_markers)
            else:
                widgets["original_markers_list"].addItem("No markers found")
                
        else:
      
            for label in widgets["original_info_labels"].values():
                label.setText("N/A")
            widgets["original_markers_list"].clear()
            widgets["original_markers_list"].addItem("File not available")
        
        if modified_exists and modified_info:
            formatted_modified = self.format_audio_info(modified_info)
            widgets["modified_info_labels"]["duration"].setText(formatted_modified["duration"])
            widgets["modified_info_labels"]["sample_rate"].setText(formatted_modified["sample_rate"])
            widgets["modified_info_labels"]["bitrate"].setText(formatted_modified["bitrate"])
            widgets["modified_info_labels"]["channels"].setText(formatted_modified["channels"])
            
            size_kb = modified_info['file_size'] / 1024
            if size_kb >= 1024:
                size_text = f"{size_kb/1024:.1f} MB"
            else:
                size_text = f"{size_kb:.1f} KB"
            
            if original_info and modified_info['file_size'] < original_info['file_size']:
                size_text = f"{size_text} ⚠ (Smaller than original!)"
                widgets["modified_info_labels"]["size"].setStyleSheet("color: red; font-weight: bold;")
            else:
                widgets["modified_info_labels"]["size"].setStyleSheet("")
            
            widgets["modified_info_labels"]["size"].setText(size_text)
            
            modified_markers = self.format_markers_for_display(modified_info.get('markers', []))
            widgets["modified_markers_list"].clear()
            if modified_markers:
                widgets["modified_markers_list"].addItems(modified_markers)
            else:
                widgets["modified_markers_list"].addItem("No markers found")
                
        else:

            for label in widgets["modified_info_labels"].values():
                label.setText("N/A")
                label.setStyleSheet("")  # Reset style
            widgets["modified_markers_list"].clear()
            widgets["modified_markers_list"].addItem("No modified audio")
    def get_file_durations(self, file_id, lang, widgets):
        """Get the duration of both original and mod WEM files"""

        wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        self.original_duration = 0
        
        if os.path.exists(wem_path):
            duration = self.get_wem_duration(wem_path)
            if duration > 0:
                self.original_duration = duration
                minutes = int(duration // 60000)
                seconds = (duration % 60000) / 1000.0
                widgets["info_labels"]["duration"].setText(f"{minutes:02d}:{seconds:05.2f}")
            else:
                widgets["info_labels"]["duration"].setText("Unknown")
        else:
            widgets["info_labels"]["duration"].setText("N/A")
            

        if lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        self.mod_duration = 0
        
        if os.path.exists(mod_wem_path):
            duration = self.get_wem_duration(mod_wem_path)
            if duration > 0:
                self.mod_duration = duration
                minutes = int(duration // 60000)
                seconds = (duration % 60000) / 1000.0
                widgets["info_labels"]["mod_duration"].setText(f"{minutes:02d}:{seconds:05.2f}")
                
            else:
                widgets["info_labels"]["mod_duration"].setText("Unknown")
        else:
            widgets["info_labels"]["mod_duration"].setText("N/A")
    
    def get_wem_duration(self, wem_path):
        """Get the duration of a WEM file in milliseconds"""
        try:
            result = subprocess.run(
                [self.vgmstream_path, "-m", wem_path],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                samples = None
                sample_rate = 48000  # default
                
                for line in result.stdout.split('\n'):
                    if "stream total samples:" in line:
                        samples = int(line.split(':')[1].strip().split()[0])
                    elif "sample rate:" in line:
                        sample_rate = int(line.split(':')[1].strip().split()[0])
                
                if samples:
                    duration_ms = int((samples / sample_rate) * 1000)
                    return duration_ms
                    
        except Exception as e:
            DEBUG.log(f"Error getting duration: {e}", "ERROR")
            
        return 0   
    def get_file_size(self, file_id, lang, widgets):
        """Get the size of both original and mod WEM files"""
   
        wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        if os.path.exists(wem_path):
            self.original_size = os.path.getsize(wem_path)
            widgets["info_labels"]["size"].setText(f"{self.original_size / 1024:.1f} KB")
        else:
            self.original_size = 0
            widgets["info_labels"]["size"].setText("N/A")
            
        if lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        
        if os.path.exists(mod_wem_path):
            self.mod_size = os.path.getsize(mod_wem_path)
            widgets["info_labels"]["mod_size"].setText(f"{self.mod_size / 1024:.1f} KB")
            
            
            if self.original_size > 0 and self.mod_size < self.original_size:
                widgets["size_warning"].setText("⚠ Mod file size is smaller than original!")
                widgets["size_warning"].show()
            else:
                widgets["size_warning"].hide()
        else:
            self.mod_size = 0
            widgets["info_labels"]["mod_size"].setText("N/A")
            widgets["size_warning"].hide()
        

    def play_current(self, play_mod=False):
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
            
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        id_ = entry.get("Id", "")
        
        if play_mod:
       
            if current_lang != "SFX":
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", current_lang, f"{entry.get('Id', '')}.wem")
            else:
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{entry.get('Id', '')}.wem")
            if not os.path.exists(wem_path):
                self.status_bar.showMessage("Mod audio not found", 3000)
                return
            self.is_playing_mod = True
        else:
            wem_path = os.path.join(self.wem_root, current_lang, f"{id_}.wem")
            if not os.path.exists(wem_path):
                self.status_bar.showMessage(f"File not found: {wem_path}", 3000)
                return
            self.is_playing_mod = False
            
        source_type = "MOD" if play_mod else "Original"
        self.status_bar.showMessage(f"Converting {source_type} to WAV...")
        QtWidgets.QApplication.processEvents()
        
        temp_wav = os.path.join(tempfile.gettempdir(), f"wem_temp_{id_}_{source_type}.wav")
        print(wem_path, temp_wav, current_lang)
        thread = threading.Thread(target=self._convert_and_play, args=(wem_path, temp_wav, current_lang))
        thread.start()

    def _convert_and_play(self, wem_path, wav_path, lang):
        ok, err = self.wem_to_wav_vgmstream(wem_path, wav_path)
        
        QtCore.QMetaObject.invokeMethod(self, "_play_converted", 
                                       QtCore.Qt.QueuedConnection,
                                       QtCore.Q_ARG(bool, ok),
                                       QtCore.Q_ARG(str, wav_path),
                                       QtCore.Q_ARG(str, err),
                                       QtCore.Q_ARG(str, lang))

    @QtCore.pyqtSlot(bool, str, str, str)
    def _play_converted(self, ok, wav_path, error, lang):
        if ok:
            self.temp_wav = wav_path
            self.audio_player.play(wav_path)
            source_type = "MOD" if self.is_playing_mod else "Original"
            self.status_bar.showMessage(f"Playing {source_type} audio...", 2000)
            

            if lang in self.tab_widgets:
                widgets = self.tab_widgets[lang]
                
                try:
                    self.audio_player.positionChanged.disconnect()
                    self.audio_player.durationChanged.disconnect()
                except:
                    pass
                    
                self.audio_player.positionChanged.connect(
                    lambda pos: self.update_audio_position(pos, widgets))
                self.audio_player.durationChanged.connect(
                    lambda dur: self.update_audio_duration(dur, widgets))
        else:
            self.status_bar.showMessage(f"Conversion failed: {error}", 3000)

    def update_audio_position(self, position, widgets):
        widgets["audio_progress"].setValue(position)
        self.update_time_label(widgets)

    def update_audio_duration(self, duration, widgets):
        widgets["audio_progress"].setMaximum(duration)
        self.update_time_label(widgets)

    def update_time_label(self, widgets):
        position = self.audio_player.player.position()
        duration = self.audio_player.player.duration()
        
        pos_min = position // 60000
        pos_sec = (position % 60000) // 1000
        dur_min = duration // 60000
        dur_sec = (duration % 60000) // 1000
        
        source_type = " [MOD]" if self.is_playing_mod else ""
        widgets["time_label"].setText(f"{pos_min:02d}:{pos_sec:02d} / {dur_min:02d}:{dur_sec:02d}{source_type}")

    def stop_audio(self):
        self.audio_player.stop()
        if self.temp_wav and os.path.exists(self.temp_wav):
            try:
                os.remove(self.temp_wav)
            except:
                pass
        self.temp_wav = None
        self.is_playing_mod = False

    def edit_current_subtitle(self):
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
            
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        current_subtitle = self.subtitles.get(key, "")
        original_subtitle = self.original_subtitles.get(key, "")
        
        item_key = key
        item_entry = entry.copy() if isinstance(entry, dict) else entry
        
        DEBUG.log(f"Editing subtitle for: {key}")
        DEBUG.log(f"Current subtitle: {current_subtitle[:50] if current_subtitle else 'None'}...")
        
        editor = SubtitleEditor(self, key, current_subtitle, original_subtitle)
        if editor.exec_() == QtWidgets.QDialog.Accepted:
            new_subtitle = editor.get_text()
            self.subtitles[key] = new_subtitle
            
      
            if new_subtitle != original_subtitle:
                self.modified_subtitles.add(key)
            else:
                self.modified_subtitles.discard(key)
            
            DEBUG.log(f"Subtitle updated for {key}")
            DEBUG.log(f"New subtitle: {new_subtitle[:50]}...")
            
            updated_item = self.find_tree_item_by_key(tree, item_key, item_entry)
            
            if updated_item and not self.is_item_deleted(updated_item):
                try:
    
                    updated_item.setText(2, new_subtitle)
                    
                    current_status = updated_item.text(3).replace("✓", "")  # Remove existing checkmark
                    if key in self.modified_subtitles:
                        updated_item.setText(3, "✓" + current_status)
                    else:
                        updated_item.setText(3, current_status)
                        
                except RuntimeError as e:
                    DEBUG.log(f"Item was deleted during update, refreshing tree: {e}", "WARNING")
             
                    self.populate_tree(current_lang)
            else:

                DEBUG.log("Item not found after edit, refreshing tree")
                self.populate_tree(current_lang)
            
            try:
                current_items = tree.selectedItems()
                if current_items and len(current_items) > 0:
                    current_item = current_items[0]
                    current_entry = current_item.data(0, QtCore.Qt.UserRole)
                    if current_entry and current_entry.get("ShortName") == shortname:
                        # Update details
                        widgets["subtitle_text"].setPlainText(new_subtitle)
                        if original_subtitle and original_subtitle != new_subtitle:
                            widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
                            widgets["original_subtitle_label"].show()
                        else:
                            widgets["original_subtitle_label"].hide()
            except RuntimeError:
        
                pass
            
            self.status_bar.showMessage("Subtitle updated", 2000)
            self.update_status()

    def find_tree_item_by_key(self, tree, target_key, target_entry):
        """Find tree item by key and entry data"""
        def search_items(parent_item):
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                
                if item.childCount() == 0: 
                    try:
                        entry = item.data(0, QtCore.Qt.UserRole)
                        if entry:
                            shortname = entry.get("ShortName", "")
                            key = os.path.splitext(shortname)[0]
                            
                            if key == target_key:
                                return item
                    except RuntimeError:
                  
                        continue
                else:
           
                    result = search_items(item)
                    if result:
                        return result
            return None
        
        try:
            root = tree.invisibleRootItem()
            return search_items(root)
        except RuntimeError:
            return None

    def is_item_deleted(self, item):
        """Check if QTreeWidgetItem is still valid"""
        try:
 
            _ = item.text(0)
            return False
        except RuntimeError:
            return True

    def revert_subtitle(self):
        """Revert selected subtitle to original"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
            
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        
        if key in self.original_subtitles:
            original = self.original_subtitles[key]
            self.subtitles[key] = original
            self.modified_subtitles.discard(key)
            

            item.setText(2, original)
            current_status = item.text(3).replace("✓", "")
            item.setText(3, current_status)
            
            widgets["subtitle_text"].setPlainText(original)
            widgets["original_subtitle_label"].hide()
            
            self.status_bar.showMessage("Subtitle reverted to original", 2000)
            self.update_status()

    def import_custom_subtitles(self):
        """Import custom subtitles from another locres file"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("import_custom_subtitles"), "", "Locres Files (*.locres)"
        )
        
        if not path:
            return
            
        DEBUG.log(f"Importing custom subtitles from: {path}")
        
        try:

            custom_subtitles = self.locres_manager.export_locres(path)
            
            if not custom_subtitles:
                QtWidgets.QMessageBox.warning(self, "Import Error", "No subtitles found in the selected file")
                return
                
            DEBUG.log(f"Found {len(custom_subtitles)} subtitles in custom file")
            
            conflicts = {}
            for key, new_value in custom_subtitles.items():
                if key in self.subtitles and self.subtitles[key]:
                    conflicts[key] = {
                        "existing": self.subtitles[key],
                        "new": new_value
                    }
            
            if conflicts:

                conflict_list = []
                for key, values in list(conflicts.items())[:10]: 
                    conflict_list.append(f"{key}:\n  Existing: {values['existing'][:50]}...\n  New: {values['new'][:50]}...")
                
                if len(conflicts) > 10:
                    conflict_list.append(f"\n... and {len(conflicts) - 10} more conflicts")
                
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle(self.tr("conflict_detected"))
                msg.setText(self.tr("conflict_message").format(conflicts="\n\n".join(conflict_list)))
                
                use_existing_btn = msg.addButton(self.tr("use_existing"), QtWidgets.QMessageBox.ActionRole)
                use_new_btn = msg.addButton(self.tr("use_new"), QtWidgets.QMessageBox.ActionRole)
                merge_btn = msg.addButton(self.tr("merge_all"), QtWidgets.QMessageBox.ActionRole)
                msg.addButton(QtWidgets.QMessageBox.Cancel)
                
                msg.exec_()
                
                if msg.clickedButton() == use_existing_btn:

                    for key, value in custom_subtitles.items():
                        if key not in self.subtitles or not self.subtitles[key]:
                            self.subtitles[key] = value
                            if key not in self.original_subtitles:
                                self.original_subtitles[key] = ""
                            self.modified_subtitles.add(key)
                elif msg.clickedButton() == use_new_btn:

                    for key, value in custom_subtitles.items():
                        self.subtitles[key] = value
                        if key not in self.original_subtitles:
                            self.original_subtitles[key] = ""
                        if value != self.original_subtitles.get(key, ""):
                            self.modified_subtitles.add(key)
                elif msg.clickedButton() == merge_btn:

                    for key, value in custom_subtitles.items():
                        if key not in self.subtitles or not self.subtitles[key]:
                            self.subtitles[key] = value
                            if key not in self.original_subtitles:
                                self.original_subtitles[key] = ""
                            self.modified_subtitles.add(key)
                else:
                    return  
            else:
                
                for key, value in custom_subtitles.items():
                    self.subtitles[key] = value
                    if key not in self.original_subtitles:
                        self.original_subtitles[key] = ""
                    if value != self.original_subtitles.get(key, ""):
                        self.modified_subtitles.add(key)
            
            current_lang = self.get_current_language()
            if current_lang and current_lang in self.tab_widgets:
                self.populate_tree(current_lang)
                
            self.update_status()
            self.status_bar.showMessage(f"Imported {len(custom_subtitles)} subtitles", 3000)
            
        except Exception as e:
            DEBUG.log(f"Error importing custom subtitles: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Import Error", str(e))

    def deploy_and_run_game(self):
        """Deploy mod to game and run it"""
        game_path = self.settings.data.get("game_path", "")
        
        if not game_path or not os.path.exists(game_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_game_path"))
            return
            
        mod_file = f"{self.mod_p_path}.pak"
        
        if not os.path.exists(mod_file):
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("compile_mod"), 
                self.tr("mod_not_found_compile"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.compile_mod()
                
                import time
                for i in range(10):
                    if os.path.exists(mod_file):
                        break
                    time.sleep(1)
                    
                if not os.path.exists(mod_file):
                    QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("mod_compilation_failed"))
                    return
            else:
                return
        

        try:
            paks_path = os.path.join(game_path, "OPP", "Content", "Paks")
            os.makedirs(paks_path, exist_ok=True)
            
            target_mod_path = os.path.join(paks_path, os.path.basename(mod_file))
            
            DEBUG.log(f"Deploying mod from {mod_file} to {target_mod_path}")
            shutil.copy2(mod_file, target_mod_path)
            
            self.status_bar.showMessage(self.tr("mod_deployed"), 3000)
            
            exe_files = []
            for file in os.listdir(game_path):
                if file.endswith(".exe") and "Shipping" in file:
                    exe_files.append(file)
                    
            if not exe_files:

                for file in os.listdir(game_path):
                    if file.endswith(".exe"):
                        exe_files.append(file)
                        
            if exe_files:
                game_exe = os.path.join(game_path, exe_files[0])
                DEBUG.log(f"Launching game: {game_exe}")
                self.status_bar.showMessage(self.tr("game_launching"), 3000)
                subprocess.Popen(
                    [game_exe],
                    startupinfo=startupinfo,
                    creationflags=CREATE_NO_WINDOW
                )
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Game executable not found")
                
        except Exception as e:
            DEBUG.log(f"Error deploying mod: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Error", str(e))
    def export_subtitles_for_game(self):
        """Export modified subtitles to game mod structure with language filtering"""
        DEBUG.log("=== Export Subtitles for Game (Fixed Language Filter) ===")
        
        if not self.modified_subtitles:
            QtWidgets.QMessageBox.information(self, "No Changes", "No modified subtitles to export")
            return
        
        current_language = self.settings.data["subtitle_lang"]
        DEBUG.log(f"Exporting for language: {current_language}")
        
        progress = ProgressDialog(self, "Exporting Subtitles for Game")
        progress.show()
        

        self.subtitle_export_status.clear()
        self.subtitle_export_status.append("=== Starting Export ===")
        self.subtitle_export_status.append(f"Language: {current_language}")
        self.subtitle_export_status.append(f"Modified subtitles: {len(self.modified_subtitles)}")
        self.subtitle_export_status.append("")
        
        try:
            exported_files = 0
            
            # Group modified subtitles by their source files
            subtitle_files_to_update = {}
            
            for modified_key in self.modified_subtitles:
                found_in_file = None
                
                for file_key, file_info in self.all_subtitle_files.items():
                    if file_info['language'] != current_language:
                        continue
                        
                    working_path = file_info['path'].replace('.locres', '_working.locres')
                    check_path = working_path if os.path.exists(working_path) else file_info['path']
                    
                    file_subtitles = self.locres_manager.export_locres(check_path)
                    if modified_key in file_subtitles:
                        found_in_file = file_info
                        break
                
                if found_in_file:
                    file_path = found_in_file['path']
                    if file_path not in subtitle_files_to_update:
                        working_path = file_path.replace('.locres', '_working.locres')
                        source_path = working_path if os.path.exists(working_path) else file_path
                        
                        subtitle_files_to_update[file_path] = {
                            'file_info': found_in_file,
                            'all_subtitles': self.locres_manager.export_locres(source_path),
                            'working_path': working_path
                        }

                    subtitle_files_to_update[file_path]['all_subtitles'][modified_key] = self.subtitles[modified_key]
                else:
                    DEBUG.log(f"Warning: Could not find source file for modified key: {modified_key}", "WARNING")
            
            DEBUG.log(f"Found {len(subtitle_files_to_update)} files to save for language {current_language}")
            
            if not subtitle_files_to_update:
                QtWidgets.QMessageBox.warning(
                    self, "Export Error", 
                    f"No subtitle files found for language '{current_language}'.\n"
                    f"Please check that you have the correct subtitle files in your Localization folder."
                )
                progress.close()
                return

            # Process each file
            for i, (file_path, data) in enumerate(subtitle_files_to_update.items()):
                file_info = data['file_info']
                all_subtitles = data['all_subtitles']
                
                progress.set_progress(
                    int((i / len(subtitle_files_to_update)) * 100),
                    f"Processing {file_info['filename']} ({current_language})..."
                )
                
                # Create target directory structure
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", 
                    "Localization", file_info['category'], current_language
                )
                os.makedirs(target_dir, exist_ok=True)
                
                target_file = os.path.join(target_dir, file_info['filename'])
                
                DEBUG.log(f"Exporting to: {target_file}")
                
                shutil.copy2(file_path, target_file)
                
                modified_subs = {k: v for k, v in all_subtitles.items() if k in self.modified_subtitles}
                
             
                success = self.locres_manager.import_locres(target_file, all_subtitles)
                
                if success:
                    exported_files += 1
                    self.subtitle_export_status.append(f"✓ {file_info['relative_path']} ({len(modified_subs)} subtitles)")
                    DEBUG.log(f"Successfully exported {file_info['filename']} with {len(modified_subs)} modified subtitles")
                else:
                    self.subtitle_export_status.append(f"✗ {file_info['relative_path']} - FAILED")
                    DEBUG.log(f"Failed to export {file_info['filename']}", "ERROR")
            
            progress.set_progress(100, "Export complete!")
            
            self.subtitle_export_status.append("")
            self.subtitle_export_status.append("=== Export Complete ===")
            self.subtitle_export_status.append(f"Files exported: {exported_files}")
            self.subtitle_export_status.append(f"Location: {os.path.join(self.mod_p_path, 'OPP', 'Content', 'Localization')}")
            
            QtWidgets.QMessageBox.information(
                self, "Success", 
                f"Subtitles exported successfully!\n\n"
                f"Language: {current_language}\n"
                f"Files exported: {exported_files}\n"
                f"Modified subtitles: {len(self.modified_subtitles)}\n\n"
                f"Location: {os.path.join(self.mod_p_path, 'OPP', 'Content', 'Localization')}"
            )
            
        except Exception as e:
            DEBUG.log(f"Export error: {str(e)}", "ERROR")
            self.subtitle_export_status.append(f"ERROR: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Export Error", str(e))
            
        progress.close()
        DEBUG.log("=== Export Complete ===")
    def save_current_wav(self):
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            return

        if len(items) > 1:
            self.batch_export_wav(items, current_lang)
            return
            
        item = items[0]
        if item.childCount() > 0:
            return
            
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        id_ = entry.get("Id", "")
        shortname = entry.get("ShortName", "")

        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("export_audio"))
        msg.setText(self.tr("which_version_export"))
        
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        mod_btn = None
        
        if current_lang != "SFX":
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", current_lang, f"{entry.get('Id', '')}.wem")
        else:
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{entry.get('Id', '')}.wem")
        if os.path.exists(mod_wem_path):
            mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
            
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        
        if msg.clickedButton() == original_btn:
            wem_path = os.path.join(self.wem_root, current_lang, f"{id_}.wem")
            suffix = ""
        elif mod_btn and msg.clickedButton() == mod_btn:
            wem_path = mod_wem_path
            suffix = "_MOD"
        else:
            return
            
        if not os.path.exists(wem_path):
            self.status_bar.showMessage(f"File not found: {wem_path}", 3000)
            return
            
        base_name = os.path.splitext(shortname)[0]
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_as_wav"), f"{base_name}{suffix}.wav", 
            f"{self.tr('wav_files')} (*.wav)"
        )
        
        if save_path:
            ok, err = self.wem_to_wav_vgmstream(wem_path, save_path)
            if ok:
                self.status_bar.showMessage(f"Saved: {save_path}", 3000)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"Conversion failed: {err}")

    def wem_to_wav_vgmstream(self, wem_path, wav_path):
        try:
            result = subprocess.run(
                [self.vgmstream_path, wem_path, "-o", wav_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stderr.decode()
        except Exception as e:
            return False, str(e)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(self.tr("file_menu"))

        self.save_action = file_menu.addAction(self.tr("save_subtitles"))
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_subtitles_to_file)

        # self.export_action = file_menu.addAction(self.tr("export_subtitles"))
        # self.export_action.triggered.connect(self.export_subtitles)

        # self.import_action = file_menu.addAction(self.tr("import_subtitles"))
        # self.import_action.triggered.connect(self.import_subtitles)

        file_menu.addSeparator()

        self.exit_action = file_menu.addAction(self.tr("exit"))
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu(self.tr("edit_menu"))
        
        self.revert_action = edit_menu.addAction(self.tr("revert_to_original"))
        self.revert_action.setShortcut("Ctrl+R")
        self.revert_action.triggered.connect(self.revert_subtitle)
        
        edit_menu.addSeparator()
        
        
        # Tools menu
        tools_menu = menubar.addMenu(self.tr("tools_menu"))
        
        self.compile_mod_action = tools_menu.addAction(self.tr("compile_mod"))
        self.compile_mod_action.triggered.connect(self.compile_mod)
        
        self.deploy_action = tools_menu.addAction(self.tr("deploy_and_run"))
        self.deploy_action.setShortcut("F5")
        self.deploy_action.triggered.connect(self.deploy_and_run_game)
        
        tools_menu.addSeparator()
        
        self.debug_action = tools_menu.addAction(self.tr("show_debug"))
        self.debug_action.setShortcut("Ctrl+D")
        self.debug_action.triggered.connect(self.show_debug_console)
        
        tools_menu.addSeparator()
        
        self.settings_action = tools_menu.addAction(self.tr("settings"))
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.show_settings_dialog)
        
        # Help menu
        help_menu = menubar.addMenu(self.tr("help_menu"))

        # self.documentation_action = help_menu.addAction("📖 Documentation")
        # self.documentation_action.setShortcut("F1")
        # self.documentation_action.triggered.connect(self.show_documentation)

        self.shortcuts_action = help_menu.addAction(self.tr("keyboard_shortcuts"))
        self.shortcuts_action.triggered.connect(self.show_shortcuts)

        help_menu.addSeparator()

        self.check_updates_action = help_menu.addAction(self.tr("check_updates"))
        self.check_updates_action.triggered.connect(self.check_updates)

        self.report_bug_action = help_menu.addAction(self.tr("report_bug"))
        self.report_bug_action.triggered.connect(self.report_bug)

        help_menu.addSeparator()

        self.about_action = help_menu.addAction(self.tr("about"))
        self.about_action.triggered.connect(self.show_about)

    def show_debug_console(self):
        if self.debug_window is None:
            self.debug_window = DebugWindow(self)
        self.debug_window.show()
        self.debug_window.raise_()

    def create_toolbar(self):
        toolbar = QtWidgets.QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        self.edit_subtitle_action = toolbar.addAction(self.tr("edit_button"))
        self.edit_subtitle_action.setShortcut("F2")
        self.edit_subtitle_action.triggered.connect(self.edit_current_subtitle)
        
        self.save_wav_action = toolbar.addAction(self.tr("export_button"))
        self.save_wav_action.setShortcut("Ctrl+E")
        self.save_wav_action.triggered.connect(self.save_current_wav)
        self.delete_mod_action = toolbar.addAction(self.tr("delete_mod_button"))
        self.delete_mod_action.setToolTip("Delete modified audio for selected file")
        self.delete_mod_action.triggered.connect(self.delete_current_mod_audio)
        toolbar.addSeparator()
        
        self.expand_all_action = toolbar.addAction(self.tr("expand_all"))
        self.expand_all_action.triggered.connect(self.expand_all_trees)
        
        self.collapse_all_action = toolbar.addAction(self.tr("collapse_all"))
        self.collapse_all_action.triggered.connect(self.collapse_all_trees)
        
    def delete_current_mod_audio(self):
        """Delete mod audio for currently selected file"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items or items[0].childCount() > 0:
            return
            
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        self.delete_mod_audio(entry, current_lang)

    def on_item_double_clicked(self, item, column):
        if item.childCount() > 0: 
            return
            
        if column == 2:  
            self.edit_current_subtitle()
        else:
            self.play_current()

    def show_context_menu(self, lang, pos):
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            return
            
        menu = QtWidgets.QMenu()
        
    
        if len(items) == 1 and items[0].childCount() == 0:
            play_action = menu.addAction(self.tr("play_original"))
            play_action.triggered.connect(self.play_current)
            
        
            entry = items[0].data(0, QtCore.Qt.UserRole)
            if entry:
                if lang != "SFX":
                    mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{entry.get('Id', '')}.wem")
                else:
                    mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{entry.get('Id', '')}.wem")
                if os.path.exists(mod_wem_path):
                    play_mod_action = menu.addAction(self.tr("play_mod"))
                    play_mod_action.triggered.connect(lambda: self.play_current(play_mod=True))

                    menu.addSeparator()
                    delete_mod_action = menu.addAction(self.tr("delete_mod_audio"))
                    delete_mod_action.triggered.connect(lambda: self.delete_mod_audio(entry, lang))

            
            edit_action = menu.addAction(f"✏ {self.tr('edit_subtitle')}")
            edit_action.triggered.connect(self.edit_current_subtitle)

            shortname = entry.get("ShortName", "")
            key = os.path.splitext(shortname)[0]
            if key in self.modified_subtitles:
                revert_action = menu.addAction(f"↩ {self.tr('revert_to_original')}")
                revert_action.triggered.connect(self.revert_subtitle)
            
            menu.addSeparator()
            
            export_action = menu.addAction(self.tr("export_as_wav"))
            export_action.triggered.connect(self.save_current_wav)
            
        menu.exec_(tree.viewport().mapToGlobal(pos))

    def batch_export_wav(self, items, lang):

        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            return
            
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("batch_export"))
        msg.setText(self.tr("which_version_export"))
        msg.addButton("Original", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        msg.exec_()
        
        if msg.result() != 0:
            return
            
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("select_output_directory"))
        if not directory:
            return
            
        progress = ProgressDialog(self, self.tr("exporting_files").format(count=len(file_items)))
        progress.show()
        
        errors = []
        
        for i, item in enumerate(file_items):
            entry = item.data(0, QtCore.Qt.UserRole)
            if not entry:
                continue
                
            id_ = entry.get("Id", "")
            shortname = entry.get("ShortName", "")
            wem_path = os.path.join(self.wem_root, lang, f"{id_}.wem")
            wav_path = os.path.join(directory, shortname)
            
            progress.set_progress(int((i / len(file_items)) * 100), f"Converting {shortname}...")
            QtWidgets.QApplication.processEvents()
            
            if os.path.exists(wem_path):
                ok, err = self.wem_to_wav_vgmstream(wem_path, wav_path)
                if not ok:
                    errors.append(f"{shortname}: {err}")
                    progress.append_details(f"Failed: {shortname}")
            else:
                errors.append(f"{shortname}: File not found")
                
        progress.close()
        
        if errors:
            QtWidgets.QMessageBox.warning(
                self, self.tr("export_complete"),
                self.tr("export_results").format(
                    successful=len(file_items) - len(errors),
                    errors=len(errors)
                )
            )
        else:
            self.status_bar.showMessage(f"Exported {len(file_items)} files successfully", 3000)

    def on_global_search(self, text):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.populate_tree(current_lang)

    def on_tab_changed(self, index):

        if index >= len(self.tab_widgets):
            return
            
        lang = self.get_current_language()
        if lang and lang in self.tab_widgets and lang not in self.populated_tabs:
            self.populate_tree(lang)
            self.populated_tabs.add(lang)

    def expand_all_trees(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.tab_widgets[current_lang]["tree"].expandAll()

    def collapse_all_trees(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.tab_widgets[current_lang]["tree"].collapseAll()

    def apply_settings(self):

        theme = self.settings.data["theme"]
        if theme == "dark":
            self.setStyleSheet(self.get_dark_theme())
        else:
            self.setStyleSheet(self.get_light_theme())

    def get_dark_theme(self):
        return """
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        
        QMenuBar {
            background-color: #2d2d30;
            border-bottom: 1px solid #3e3e42;
        }
        
        QMenuBar::item:selected {
            background-color: #094771;
        }
        
        QMenu {
            background-color: #252526;
            border: 1px solid #3e3e42;
        }
        
        QMenu::item:selected {
            background-color: #094771;
        }
        
        QToolBar {
            background-color: #2d2d30;
            border: none;
            spacing: 5px;
            padding: 5px;
        }
        
        QToolButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }
        
        QToolButton:hover {
            background-color: #3e3e42;
        }
        
        QTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #1e1e1e;
        }
        
        QTabBar::tab {
            background-color: #2d2d30;
            color: #d4d4d4;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom: 2px solid #007acc;
        }
        
        QTreeWidget {
            background-color: #252526;
            alternate-background-color: #2d2d30;
            border: 1px solid #3e3e42;
            selection-background-color: #094771;
        }
        
        QTreeWidget::item:hover {
            background-color: #2a2d2e;
        }
        
        QHeaderView::section {
            background-color: #2d2d30;
            border: none;
            border-right: 1px solid #3e3e42;
            padding: 5px;
        }
        
        QPushButton {
            background-color: #0e639c;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #1177bb;
        }
        
        QPushButton:pressed {
            background-color: #094771;
        }
        
        QPushButton[primary="true"] {
            background-color: #007acc;
        }
        
        QPushButton[primary="true"]:hover {
            background-color: #1ba1e2;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            padding: 5px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #007acc;
        }
        
        QGroupBox {
            border: 1px solid #3e3e42;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #007acc;
            color: white;
        }
        """

    def get_light_theme(self):
        return """
        QMainWindow, QWidget {
            background-color: #f3f3f3;
            color: #1e1e1e;
        }
        
        QMenuBar {
            background-color: #e7e7e7;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item:selected {
            background-color: #bee6fd;
        }
        
        QMenu {
            background-color: #f3f3f3;
            border: 1px solid #cccccc;
        }
        
        QMenu::item:selected {
            background-color: #bee6fd;
        }
        
        QToolBar {
            background-color: #e7e7e7;
            border: none;
            spacing: 5px;
            padding: 5px;
        }
        
        QToolButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }
        
        QToolButton:hover {
            background-color: #dadada;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #e7e7e7;
            color: #1e1e1e;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #0078d4;
        }
        
        QTreeWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            border: 1px solid #cccccc;
            selection-background-color: #bee6fd;
        }
        
        QTreeWidget::item:hover {
            background-color: #e5f3ff;
        }
        
        QHeaderView::section {
            background-color: #e7e7e7;
            border: none;
            border-right: 1px solid #cccccc;
            padding: 5px;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton[primary="true"] {
            background-color: #107c10;
        }
        
        QPushButton[primary="true"]:hover {
            background-color: #0e7b0e;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 5px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #0078d4;
        }
        
        QGroupBox {
            border: 1px solid #cccccc;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            background-color: #e7e7e7;
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #0078d4;
            color: white;
        }
        """

    def compile_mod(self):
        if not os.path.exists(self.repak_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("repak_not_found"))
            return
            
        progress = ProgressDialog(self, self.tr("compiling_mod"))
        progress.show()
        progress.set_progress(50, self.tr("running_repak"))
        
        command = [self.repak_path, "pack", "--version", "V11", "--compression", "Zlib", self.mod_p_path]
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            progress.set_progress(100, "Complete")
            
            if result.returncode == 0:
                progress.append_details(result.stdout)
                QtWidgets.QMessageBox.information(self, self.tr("success"), self.tr("mod_compiled_successfully"))
            else:
                progress.append_details(result.stderr)
                QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("compilation_failed"))
                
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e))
            
        progress.close()

    def select_wwise_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select WWISE Folder", 
            self.settings.data.get("last_directory", "")
        )
        
        if folder:
            self.wwise_path_edit.setText(folder)
            self.settings.data["last_directory"] = folder
            self.settings.save()

    def open_target_folder(self):
        """Open target folder with choice for SFX or Voice"""
        voice_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
        sfx_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
        loc_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Select Folder to Open")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        label = QtWidgets.QLabel("Which folder would you like to open?")
        layout.addWidget(label)
        
        btn_layout = QtWidgets.QVBoxLayout()
        
        if os.path.exists(voice_dir):
            voice_btn = QtWidgets.QPushButton(f"🎙 Voice Files\n{voice_dir}")
            voice_btn.clicked.connect(lambda: (os.startfile(voice_dir), dialog.accept()))
            btn_layout.addWidget(voice_btn)
        
        if os.path.exists(sfx_dir) and sfx_dir != voice_dir:
            sfx_btn = QtWidgets.QPushButton(f"🔊 SFX Files\n{sfx_dir}")
            sfx_btn.clicked.connect(lambda: (os.startfile(sfx_dir), dialog.accept()))
            btn_layout.addWidget(sfx_btn)
        
        if os.path.exists(loc_dir):
            loc_btn = QtWidgets.QPushButton(f"📝 Subtitles\n{loc_dir}")
            loc_btn.clicked.connect(lambda: (os.startfile(loc_dir), dialog.accept()))
            btn_layout.addWidget(loc_btn)
        
        layout.addLayout(btn_layout)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        if not any(os.path.exists(d) for d in [voice_dir, sfx_dir, loc_dir]):
            QtWidgets.QMessageBox.warning(self, "Error", "No target folders found!")
            return
        
        dialog.exec_()

    def create_wav_to_wem_tab(self):
        """Create simplified WAV to WEM converter tab with logs"""
        main_tab = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_tab)
        main_layout.setSpacing(5)
        
        self.wav_converter_tabs = QtWidgets.QTabWidget()
        
        converter_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(converter_tab)
        layout.setSpacing(5)
        
        instructions = QtWidgets.QLabel(f"""
        <p><b>{self.tr("wav_to_wem_converter")}:</b> {self.tr("converter_instructions")}</p>
        """)
        instructions.setWordWrap(True)
        instructions.setMaximumHeight(40)
        layout.addWidget(instructions)
        
        top_section = QtWidgets.QWidget()
        top_layout = QtWidgets.QHBoxLayout(top_section)
        top_layout.setSpacing(10)
        
        mode_group = QtWidgets.QGroupBox(self.tr("conversion_mode"))
        mode_group.setMaximumHeight(120)
        mode_layout = QtWidgets.QVBoxLayout(mode_group)
        mode_layout.setSpacing(2)
        
        self.strict_mode_radio = QtWidgets.QRadioButton(self.tr("strict_mode"))
        self.strict_mode_radio.setChecked(True)
        self.strict_mode_radio.setToolTip(
            "Standard conversion mode. If the file is too large, an error will be thrown.\n"
            "Use this mode when you want full control over your audio files."
        )
        
        self.adaptive_mode_radio = QtWidgets.QRadioButton(self.tr("adaptive_mode"))
        self.adaptive_mode_radio.setToolTip(
            "Automatically resamples audio to lower sample rates if the file is too large.\n"
            "The system will find the optimal sample rate to match the target file size.\n"
            "Useful for batch processing when exact audio quality is less critical."
        )
        
        strict_desc = QtWidgets.QLabel(f"<small>{self.tr('strict_mode_desc')}</small>")
        strict_desc.setStyleSheet("padding-left: 20px; color: #666;")
        
        adaptive_desc = QtWidgets.QLabel(f"<small>{self.tr('adaptive_mode_desc')}</small>")
        adaptive_desc.setStyleSheet("padding-left: 20px; color: #666;")
        
        mode_layout.addWidget(self.strict_mode_radio)
        mode_layout.addWidget(strict_desc)
        mode_layout.addWidget(self.adaptive_mode_radio)
        mode_layout.addWidget(adaptive_desc)
        mode_layout.addStretch()
        
        top_layout.addWidget(mode_group)
        
        paths_group = QtWidgets.QGroupBox(self.tr("path_configuration"))
        paths_group.setMaximumHeight(120)
        paths_layout = QtWidgets.QFormLayout(paths_group)
        paths_layout.setSpacing(5)
        paths_layout.setContentsMargins(5, 5, 5, 5)
        
        wwise_widget = QtWidgets.QWidget()
        wwise_layout = QtWidgets.QHBoxLayout(wwise_widget)
        wwise_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wwise_path_edit = QtWidgets.QLineEdit()
        self.wwise_path_edit.setPlaceholderText(self.tr("wwise_path_placeholder"))
        self.wwise_path_edit.setText(self.settings.data.get("wav_wwise_path", ""))
        wwise_browse_btn = QtWidgets.QPushButton("...")
        wwise_browse_btn.setMaximumWidth(30)
        wwise_browse_btn.clicked.connect(self.browse_wwise_path)
        
        wwise_layout.addWidget(self.wwise_path_edit)
        wwise_layout.addWidget(wwise_browse_btn)
        paths_layout.addRow(f"{self.tr('wwise_path')}", wwise_widget)
        
        project_widget = QtWidgets.QWidget()
        project_layout = QtWidgets.QHBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        
        self.converter_project_path_edit = QtWidgets.QLineEdit()
        self.converter_project_path_edit.setPlaceholderText(self.tr("project_path_placeholder"))
        self.converter_project_path_edit.setText(self.settings.data.get("wav_project_path", ""))
        project_browse_btn = QtWidgets.QPushButton("...")
        project_browse_btn.setMaximumWidth(30)
        project_browse_btn.clicked.connect(self.browse_converter_project_path)
        
        project_layout.addWidget(self.converter_project_path_edit)
        project_layout.addWidget(project_browse_btn)
        paths_layout.addRow(f"{self.tr('project_path')}", project_widget)
        
        wav_widget = QtWidgets.QWidget()
        wav_layout = QtWidgets.QHBoxLayout(wav_widget)
        wav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wav_folder_edit = QtWidgets.QLineEdit()
        self.wav_folder_edit.setPlaceholderText(self.tr("wav_folder_placeholder"))
        self.wav_folder_edit.setText(self.settings.data.get("wav_folder_path", ""))
        wav_browse_btn = QtWidgets.QPushButton("...")
        wav_browse_btn.setMaximumWidth(30)
        wav_browse_btn.clicked.connect(self.browse_wav_folder)
        
        wav_layout.addWidget(self.wav_folder_edit)
        wav_layout.addWidget(wav_browse_btn)
        paths_layout.addRow(f"{self.tr('wav_path')}", wav_widget)
        
        top_layout.addWidget(paths_group)
        
        layout.addWidget(top_section)
        
        files_group = QtWidgets.QGroupBox(self.tr("files_for_conversion"))
        files_layout = QtWidgets.QVBoxLayout(files_group)
        files_layout.setSpacing(5)
        
        controls_widget = QtWidgets.QWidget()
        controls_widget.setMaximumHeight(35)
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        add_all_wav_btn = QtWidgets.QPushButton(self.tr("add_all_wav"))
        add_all_wav_btn.clicked.connect(self.add_all_wav_files_auto)
        
        clear_files_btn = QtWidgets.QPushButton(self.tr("clear"))
        clear_files_btn.clicked.connect(self.clear_conversion_files)
        
        self.convert_btn = QtWidgets.QPushButton(self.tr("convert"))
        self.convert_btn.setMaximumWidth(150)
        self.convert_btn.setMaximumHeight(30)
        self.convert_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 5px 15px; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        # Connect to a method that handles both convert and stop
        self.convert_btn.clicked.connect(self.toggle_conversion)
        
        # Add conversion state tracking
        self.is_converting = False
        self.conversion_thread = None
        
        self.files_count_label = QtWidgets.QLabel(self.tr("files_ready_count").format(count=0))
        self.files_count_label.setStyleSheet("font-weight: bold; color: #666;")
        
        controls_layout.addWidget(add_all_wav_btn)
        controls_layout.addWidget(clear_files_btn)
        controls_layout.addWidget(self.convert_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.files_count_label)
        
        files_layout.addWidget(controls_widget)
        
        self.conversion_files_table = QtWidgets.QTableWidget()
        self.conversion_files_table.setColumnCount(5)
        self.conversion_files_table.setHorizontalHeaderLabels([
            self.tr("wav_file"), self.tr("target_wem"), self.tr("language"), 
            self.tr("target_size"), self.tr("status")
        ])
        
        self.conversion_files_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.conversion_files_table.customContextMenuRequested.connect(self.show_conversion_context_menu)
        
        header = self.conversion_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch) 
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        
        self.conversion_files_table.setAlternatingRowColors(True)
        self.conversion_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        files_layout.addWidget(self.conversion_files_table, 1)
        
        layout.addWidget(files_group, 1)
        
        bottom_widget = QtWidgets.QWidget()
        bottom_widget.setMaximumHeight(60)
        bottom_layout = QtWidgets.QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(2)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_widget = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)
        
        self.conversion_progress = QtWidgets.QProgressBar()
        self.conversion_progress.setMaximumHeight(15)
        
        self.conversion_status = QtWidgets.QLabel(self.tr("ready"))
        self.conversion_status.setStyleSheet("color: #666; font-size: 11px;")
        self.conversion_status.setMinimumWidth(200)
        
        progress_layout.addWidget(self.conversion_progress)
        progress_layout.addWidget(self.conversion_status)
        
        bottom_layout.addWidget(progress_widget)
        
        layout.addWidget(bottom_widget)
        
        self.wav_converter_tabs.addTab(converter_tab, self.tr("convert"))
        
        self.create_conversion_logs_tab()
        
        main_layout.addWidget(self.wav_converter_tabs)
        
        self.wav_converter = WavToWemConverter(self)
        self.wav_converter.progress_updated.connect(self.conversion_progress.setValue)
        self.wav_converter.status_updated.connect(self.update_conversion_status)
        self.wav_converter.conversion_finished.connect(self.on_conversion_finished)
        
        self.converter_tabs.addTab(main_tab, self.tr("wav_to_wem_converter"))
    def toggle_conversion(self):
        """Toggle between start and stop conversion"""
        if not self.is_converting:
            self.start_wav_conversion()
        else:
            self.stop_wav_conversion()
    def create_converter_tab(self):
        """Create updated converter tab"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5) 
        layout.setSpacing(5)
        
        header = QtWidgets.QLabel("Audio Converter & Processor")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        
        self.converter_tabs = QtWidgets.QTabWidget()
        
     
        self.create_wav_to_wem_tab()
        self.create_localization_exporter_simple_tab()
 
        self.create_wem_processor_main_tab()
        
        layout.addWidget(self.converter_tabs)
        
        self.tabs.addTab(tab, "Converter")
    def show_conversion_context_menu(self, pos):
        """Show context menu for conversion table"""
        item = self.conversion_files_table.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        if row < 0 or row >= len(self.wav_converter.file_pairs):
            return
        
        menu = QtWidgets.QMenu()
        
        change_target_action = menu.addAction("📁 Browse for Target WEM...")
        change_target_action.triggered.connect(lambda: self.select_custom_target_wem(row))
        
        wems_folder = os.path.join(self.base_path, "Wems")
        available_folders = []
        
        if os.path.exists(wems_folder):
            for folder in os.listdir(wems_folder):
                folder_path = os.path.join(wems_folder, folder)
                if os.path.isdir(folder_path):
                   
                    wem_count = sum(1 for f in os.listdir(folder_path) if f.endswith('.wem'))
                    if wem_count > 0:
                        available_folders.append((folder, folder_path, wem_count))
        
        if available_folders:
            menu.addSeparator()
            quick_menu = menu.addMenu("⚡ Quick Select")
            
            available_folders.sort(key=lambda x: x[2], reverse=True)
            
            for folder_name, folder_path, file_count in available_folders:
                folder_action = quick_menu.addAction(f"📁 {folder_name} ({file_count} files)")
                folder_action.triggered.connect(
                    lambda checked, p=folder_path, r=row: self.quick_select_from_folder(p, r)
                )
        
        menu.addSeparator()
        
        remove_action = menu.addAction("❌ Remove")
        remove_action.triggered.connect(lambda: self.remove_conversion_file(row))
        
        menu.exec_(self.conversion_files_table.mapToGlobal(pos))

    def quick_select_from_folder(self, folder_path, row):
        """Quick select WEM from specific folder"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        wem_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            f"Select Target WEM for {wav_name} from {os.path.basename(folder_path)}",
            folder_path,
            "WEM Audio Files (*.wem);;All Files (*.*)"
        )
        
        if not wem_file:
            return
        
        self.process_selected_wem_file(wem_file, row)
    def process_selected_wem_file(self, wem_file, row):
        """Process selected WEM file and update conversion table"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        try:
           
            file_size = os.path.getsize(wem_file)
            file_name = os.path.basename(wem_file)
            file_id = os.path.splitext(file_name)[0]
           
            parent_folder = os.path.basename(os.path.dirname(wem_file))
            
            file_info = None
            for entry in self.all_files:
                if entry.get("Id", "") == file_id:
                    file_info = entry
                    break
            
            if file_info:
                language = file_info.get("Language", parent_folder)
                original_name = file_info.get("ShortName", file_name)
                self.append_conversion_log(f"Found {file_id} in database: {original_name}")
            else:
                
                language = parent_folder
                original_name = file_name
                self.append_conversion_log(f"File {file_id} not found in database, using folder name as language")
            
            self.wav_converter.file_pairs[row] = {
                "wav_file": file_pair['wav_file'],
                "target_wem": wem_file,
                "wav_name": file_pair['wav_name'],
                "target_name": file_name,
                "target_size": file_size,
                "language": language,
                "file_id": file_id
            }
            
            self.update_conversion_files_table()
            
            size_kb = file_size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            
            self.append_conversion_log(
                f"✓ Changed target for {wav_name}:\n"
                f"  → {file_name} (ID: {file_id})\n"
                f"  → Language: {language}\n"
                f"  → Size: {size_str}\n"
                f"  → Path: {wem_file}"
            )
            
            self.status_bar.showMessage(f"Target updated: {wav_name} → {file_name}", 3000)
            
        except Exception as e:
            self.append_conversion_log(f"✗ Error processing {wem_file}: {str(e)}")
            QtWidgets.QMessageBox.warning(
                self, "Error", 
                f"Error processing selected file:\n{str(e)}"
            )
    def select_custom_target_wem(self, row):
        """Select custom target WEM file from file system"""
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
        
        wems_folder = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_folder):
            wems_folder = self.base_path
        
        wem_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            f"Select Target WEM for {wav_name}",
            wems_folder,
            "WEM Audio Files (*.wem);;All Files (*.*)"
        )
        
        if not wem_file:
            return
      
        self.process_selected_wem_file(wem_file, row)

    def remove_conversion_file(self, row):
        """Remove file from conversion list"""
        if row < 0 or row >= len(self.wav_converter.file_pairs):
            return
        
        file_pair = self.wav_converter.file_pairs[row]
        wav_name = file_pair['wav_name']
       
        del self.wav_converter.file_pairs[row]
       
        self.update_conversion_files_table()
   
        self.append_conversion_log(f"Removed {wav_name} from conversion list")        
    def create_conversion_logs_tab(self):
        """Create logs tab for conversion results"""
        logs_tab = QtWidgets.QWidget()
        logs_layout = QtWidgets.QVBoxLayout(logs_tab)
        
       
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        
        header_label = QtWidgets.QLabel(self.tr("conversion_logs"))
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        clear_logs_btn = QtWidgets.QPushButton(self.tr("clear_logs"))
        clear_logs_btn.setMaximumWidth(120)
        clear_logs_btn.clicked.connect(self.clear_conversion_logs)
        
        save_logs_btn = QtWidgets.QPushButton(self.tr("save_logs"))
        save_logs_btn.setMaximumWidth(120)
        save_logs_btn.clicked.connect(self.save_conversion_logs)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_logs_btn)
        header_layout.addWidget(save_logs_btn)
        
        logs_layout.addWidget(header_widget)
        
    
        self.conversion_logs = QtWidgets.QTextEdit()
        self.conversion_logs.setReadOnly(True)
        self.conversion_logs.setFont(QtGui.QFont("Consolas", 9))
        self.conversion_logs.setPlainText(self.tr("subtitle_export_ready"))
        
        logs_layout.addWidget(self.conversion_logs)
        
        self.wav_converter_tabs.addTab(logs_tab, self.tr("conversion_logs"))
    def clear_conversion_logs(self):
        """Clear conversion logs"""
        self.conversion_logs.clear()
        self.conversion_logs.setPlainText(self.tr("logs_cleared"))

    def save_conversion_logs(self):
        """Save conversion logs to file"""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_logs"),
            f"conversion_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.conversion_logs.toPlainText())
                self.update_conversion_status(self.tr("logs_saved"), "green")
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, self.tr("error"), 
                    f"{self.tr('error_saving_logs')}: {str(e)}"
                )

    def append_conversion_log(self, message):
        """Append message to conversion logs if available"""
        if hasattr(self, 'conversion_logs'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.conversion_logs.append(log_entry)
            
            scrollbar = self.conversion_logs.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    def add_all_wav_files_auto(self):
        """Automatically add all WAV files with matching WEM files by ID"""
        wav_folder = self.wav_folder_edit.text()
        if not wav_folder or not os.path.exists(wav_folder):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                self.tr("select_wav_folder")
            )
            return
        
        wems_folder = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_folder):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                f"{self.tr('wems_folder_not_found')}: {wems_folder}"
            )
            return

        self.wav_converter.clear_file_pairs()
        self.conversion_files_table.setRowCount(0)

        self.clear_conversion_logs()
        self.append_conversion_log(self.tr("search_complete"))

        wav_files = [f for f in os.listdir(wav_folder) if f.endswith('.wav')]
        if not wav_files:
            QtWidgets.QMessageBox.warning(
                self, self.tr("warning"), 
                self.tr("no_wav_files")
            )
            return
        
        self.append_conversion_log(f"Found {len(wav_files)} WAV files")
       
        selected_language = self.settings.data.get("wem_process_language", "english")
        self.append_conversion_log(f"Selected language from settings: {selected_language}")
        
        if selected_language == "english":
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = "Francais"
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        
     
        voice_mapping = {}
        sfx_mapping = {}
        voice_files_in_db = []
        
        vo_from_streamed = 0
        vo_from_media_files = 0
        vo_skipped_wrong_lang = 0
        
        for entry in self.all_files:
            shortname = entry.get("ShortName", "")
            base_shortname = os.path.splitext(shortname)[0]
            file_id = entry.get("Id", "")
            language = entry.get("Language", "")
            source = entry.get("Source", "")
            
            file_info = {
                'id': file_id,
                'language': language,
                'source': source,
                'original_name': shortname
            }
            
            if base_shortname.startswith("VO_"):
           
                if language in voice_lang_filter:
                    voice_mapping[base_shortname] = file_info
                    voice_files_in_db.append(base_shortname)
                    
                    if source == "StreamedFiles":
                        vo_from_streamed += 1
                    elif source == "MediaFilesNotInAnyBank":
                        vo_from_media_files += 1
                else:
                    vo_skipped_wrong_lang += 1
            elif language == "SFX" or (source == "MediaFilesNotInAnyBank" and not base_shortname.startswith("VO_")):
                sfx_mapping[base_shortname] = file_info
        
       
        potential_matches = []
        for wav_file in wav_files:
            wav_name = os.path.splitext(wav_file)[0]
            
            if wav_name.startswith("VO_") and wav_name not in voice_mapping:
  
                wem_without_hex = wav_name
                if '_' in wav_name:
                    parts = wav_name.split('_')
                    if len(parts) > 1 and len(parts[-1]) == 8:
                        try:
                            int(parts[-1], 16)  
                            wem_without_hex = '_'.join(parts[:-1])
                        except ValueError:
                            pass
                
                if wem_without_hex in voice_mapping and wem_without_hex != wav_name:
                    potential_matches.append((wav_name, wem_without_hex))
        
        for wav_name, db_file in potential_matches:
            if db_file in voice_mapping:
                voice_mapping[wav_name] = voice_mapping[db_file].copy()
                voice_mapping[wav_name]['matched_via'] = f"hex_removal_from_{db_file}"
               
      
        wem_index = {}
        for root, dirs, files in os.walk(wems_folder):
            folder_name = os.path.basename(root)
            for file in files:
                if file.endswith('.wem'):
                    file_id = os.path.splitext(file)[0]
                    if file_id not in wem_index:
                        wem_index[file_id] = {}
                        
                    wem_index[file_id][folder_name] = {
                        'path': os.path.join(root, file),
                        'size': os.path.getsize(os.path.join(root, file))
                    }
        
        
        matched_count = 0
        unmatched_files = []
        
        for wav_file in wav_files:
            wav_name = os.path.splitext(wav_file)[0]
            wav_path = os.path.join(wav_folder, wav_file)
            
            if wav_name.startswith("VO_"):
           
                if wav_name in voice_mapping:
                    file_info = voice_mapping[wav_name]
                    file_id = file_info['id']
                    file_language = file_info['language']
      
                    if file_id in wem_index:
                        wem_options = wem_index[file_id]
                        wem_info = None
                        
                      
                        if target_dir_voice in wem_options:
                            wem_info = wem_options[target_dir_voice]
                        else:
         
                            language_folders = [folder for folder in wem_options.keys() 
                                            if folder not in ["SFX", "Windows"]]
                            if language_folders:
                                wem_info = wem_options[language_folders[0]]                 
                        
                        if wem_info:
                            file_pair = {
                                "wav_file": wav_path,
                                "target_wem": wem_info['path'],
                                "wav_name": wav_file,
                                "target_name": f"{file_id}.wem",
                                "target_size": wem_info['size'],
                                "language": target_dir_voice,  
                                "file_id": file_id
                            }
                            
                            self.wav_converter.file_pairs.append(file_pair)
                            matched_count += 1
                        else:
                            self.append_conversion_log(f"✗ {wav_name}: WEM File ID {file_id} not found in Wems")
                            unmatched_files.append(f"{wav_name} (ID: {file_id} not found in Wems)")
                    else:
                        self.append_conversion_log(f"✗ {wav_name}: WEM File ID {file_id} not found")
                        unmatched_files.append(f"{wav_name} (ID: {file_id} not found in Wems)")
                else:
                    self.append_conversion_log(f"✗ {wav_name}: Not found in SoundbanksInfo for language {selected_language}")
                    unmatched_files.append(f"{wav_name} (not found for {selected_language})")
            else:
            
                if wav_name in sfx_mapping:
                    file_info = sfx_mapping[wav_name]
                    file_id = file_info['id']
                    
                    if file_id in wem_index:
                        wem_options = wem_index[file_id]
                        wem_info = None
                        
                        if "SFX" in wem_options:
                            wem_info = wem_options["SFX"]
                        elif wem_options:
                            wem_info = list(wem_options.values())[0]
                        
                        if wem_info:
                            file_pair = {
                                "wav_file": wav_path,
                                "target_wem": wem_info['path'],
                                "wav_name": wav_file,
                                "target_name": f"{file_id}.wem",
                                "target_size": wem_info['size'],
                                "language": "SFX",
                                "file_id": file_id
                            }
                            
                            self.wav_converter.file_pairs.append(file_pair)
                            matched_count += 1
                            
                            self.append_conversion_log(f"✓ {wav_name} -> ID {file_id} -> SFX ({wem_info['size']:,} bytes)")
                        else:
                            self.append_conversion_log(f"✗ {wav_name}: WEM File ID {file_id} not found in Wems")
                            unmatched_files.append(f"{wav_name} (ID: {file_id} not found in Wems)")
                    else:
                        self.append_conversion_log(f"✗ {wav_name}: WEM File ID {file_id} not found")
                        unmatched_files.append(f"{wav_name} (ID: {file_id} not found in Wems)")
                else:
                    self.append_conversion_log(f"✗ {wav_name}: Not found in SoundbanksInfo for language {selected_language}")
                    unmatched_files.append(f"{wav_name} (not found for {selected_language})")
        
        self.update_conversion_files_table()
        
        self.append_conversion_log(f"Search finished: {matched_count}/{len(wav_files)} files matched")
        
        message = self.tr("auto_search_result").format(matched=matched_count, total=len(wav_files))
        message += f"\n{self.tr('target_language')}: {target_dir_voice}"
        
        if unmatched_files and len(unmatched_files) <= 5:
            message += f"\n\n{self.tr('no_matches_found')}:\n" + "\n".join(unmatched_files)
        elif unmatched_files:
            message += f"\n\n{self.tr('no_matches_found')} {len(unmatched_files)} files (see logs for details)"
        
        QtWidgets.QMessageBox.information(self, self.tr("search_complete"), message)
    def determine_language(self, language_from_soundbank):
        lang_map = {
            'English(US)': 'English(US)',
            'French(France)': 'French(France)', 
            'Francais': 'French(France)',
            'SFX': 'SFX'
        }
        
        return lang_map.get(language_from_soundbank, 'SFX')

    def update_conversion_files_table(self):
        """Update conversion files table with tooltips"""
        self.conversion_files_table.setRowCount(len(self.wav_converter.file_pairs))
        
        for i, pair in enumerate(self.wav_converter.file_pairs):
   
            wav_item = QtWidgets.QTableWidgetItem(pair['wav_name'])
            wav_item.setFlags(wav_item.flags() & ~QtCore.Qt.ItemIsEditable)
            wav_item.setToolTip(f"Path: {pair['wav_file']}")
            self.conversion_files_table.setItem(i, 0, wav_item)
            
            wem_display = f"{pair['file_id']}.wem"
            wem_item = QtWidgets.QTableWidgetItem(wem_display)
            wem_item.setFlags(wem_item.flags() & ~QtCore.Qt.ItemIsEditable)
            wem_item.setToolTip(f"Source: {pair['target_wem']}")
            self.conversion_files_table.setItem(i, 1, wem_item)

            lang_item = QtWidgets.QTableWidgetItem(pair['language'])
            lang_item.setFlags(lang_item.flags() & ~QtCore.Qt.ItemIsEditable)
     
            if pair['language'] == 'English(US)':
                lang_item.setBackground(QtGui.QColor(230, 255, 230))
            elif pair['language'] == 'Francais':
                lang_item.setBackground(QtGui.QColor(230, 230, 255))
            else:  
                lang_item.setBackground(QtGui.QColor(255, 250, 230))
                
            self.conversion_files_table.setItem(i, 2, lang_item)
   
            size_kb = pair['target_size'] / 1024
            size_item = QtWidgets.QTableWidgetItem(f"{size_kb:.1f} KB")
            size_item.setFlags(size_item.flags() & ~QtCore.Qt.ItemIsEditable)
            size_item.setToolTip(f"Exact size: {pair['target_size']:,} bytes")
            self.conversion_files_table.setItem(i, 3, size_item)
            
       
            status_item = QtWidgets.QTableWidgetItem(self.tr("ready"))
            status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
            status_item.setToolTip("File ready for conversion")
            self.conversion_files_table.setItem(i, 4, status_item)
  
        count = len(self.wav_converter.file_pairs)
        self.files_count_label.setText(self.tr("files_ready_count").format(count=count))
        
        if count > 0:
            self.files_count_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.files_count_label.setStyleSheet("font-weight: bold; color: #666;")

    def update_conversion_status(self, message, color="green"):
      
        color_map = {
            "green": "#4CAF50",
            "blue": "#2196F3", 
            "red": "#F44336",
            "orange": "#FF9800"
        }
        self.conversion_status.setText(message)
        self.conversion_status.setStyleSheet(f"color: {color_map.get(color, color)}; font-size: 12px;")

    def start_wav_conversion(self):
        """Start WAV file conversion"""
        if not self.wav_converter.file_pairs:
            QtWidgets.QMessageBox.warning(
                self, self.tr("warning"), 
                self.tr("add_files_warning")
            )
            return
        
        if not all([self.wwise_path_edit.text(), self.converter_project_path_edit.text()]):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                "Please specify Wwise and project paths!"
            )
            return
        
        self.append_conversion_log("=== CONVERSION DIAGNOSTICS ===")
        self.append_conversion_log(f"Wwise path: {self.wwise_path_edit.text()}")
        self.append_conversion_log(f"Project path: {self.converter_project_path_edit.text()}")
        self.append_conversion_log(f"Files to convert: {len(self.wav_converter.file_pairs)}")
        self.append_conversion_log(f"Adaptive mode: {self.adaptive_mode_radio.isChecked()}")
        
        wwise_path = self.wwise_path_edit.text()
        project_path = self.converter_project_path_edit.text()
        
        if not os.path.exists(wwise_path):
            self.append_conversion_log(f"ERROR: Wwise path does not exist: {wwise_path}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Wwise path does not exist:\n{wwise_path}")
            return
        
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
            
        self.set_conversion_state(True)
        
        self.wav_converter.set_adaptive_mode(self.adaptive_mode_radio.isChecked())
        
        temp_output = os.path.join(self.base_path, "temp_wem_output")
        os.makedirs(temp_output, exist_ok=True)
        
        self.wav_converter.set_paths(wwise_path, project_path, temp_output)
        
        for i in range(self.conversion_files_table.rowCount()):
            status_item = self.conversion_files_table.item(i, 4)
            status_item.setText(self.tr("waiting"))
            status_item.setBackground(QtGui.QColor(255, 255, 200))
        
        self.conversion_progress.setValue(0)
        
        mode_text = self.tr("adaptive_mode") if self.adaptive_mode_radio.isChecked() else self.tr("strict_mode")
        self.update_conversion_status(
            self.tr("starting_conversion").format(mode=mode_text), 
            "blue"
        )
        self.append_conversion_log(f"=== {self.tr('starting_conversion').format(mode=mode_text.upper())} ===")
        
        # Start conversion in thread
        self.conversion_thread = threading.Thread(target=self.wav_converter.convert_all_files)
        self.conversion_thread.daemon = True  
        self.conversion_thread.start()
    
    def set_conversion_state(self, converting):
        """Set the conversion state and update UI accordingly"""
        self.is_converting = converting
        
        if converting:

            self.convert_btn.setText("Stop")
            self.convert_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #F44336; 
                    color: white; 
                    font-weight: bold; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
            
            self.strict_mode_radio.setEnabled(False)
            self.adaptive_mode_radio.setEnabled(False)
            self.wwise_path_edit.setEnabled(False)
            self.converter_project_path_edit.setEnabled(False)
            self.wav_folder_edit.setEnabled(False)
            
        else:

            self.convert_btn.setText(self.tr("convert"))
            self.convert_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    font-weight: bold; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            self.strict_mode_radio.setEnabled(True)
            self.adaptive_mode_radio.setEnabled(True)
            self.wwise_path_edit.setEnabled(True)
            self.converter_project_path_edit.setEnabled(True)
            self.wav_folder_edit.setEnabled(True)
            
            self.wav_converter.reset_state()
    
    def stop_wav_conversion(self):
        """Stop the current conversion process"""
        if self.is_converting:
      
            self.wav_converter.stop_conversion()
            
            self.update_conversion_status("Stopping conversion...", "orange")
            self.append_conversion_log("User requested conversion stop")
            
            if hasattr(self, 'conversion_thread') and self.conversion_thread and self.conversion_thread.is_alive():
                self.conversion_thread.join(timeout=3.0)
                
                if self.conversion_thread.is_alive():
                    self.append_conversion_log("Warning: Conversion thread did not stop gracefully")
            
            self.set_conversion_state(False)
            self.update_conversion_status("Conversion stopped by user", "red")
            self.append_conversion_log("Conversion stopped")
            
            self.conversion_progress.setValue(0)
    def on_conversion_finished(self, results):
        """Handle conversion completion with logging"""

        self.set_conversion_state(False)
        
        successful = [r for r in results if r['result'].get('success', False)]
        failed = [r for r in results if not r['result'].get('success', False)]
        size_warnings = [r for r in results if r['result'].get('size_warning', False)]
        resampled = [r for r in successful if r['result'].get('resampled', False)]
        stopped = [r for r in results if r['result'].get('stopped', False)]
        
        self.conversion_progress.setValue(100)
    
        self.append_conversion_log("=" * 50)
        
        if stopped:
            self.append_conversion_log("CONVERSION STOPPED BY USER")
            self.update_conversion_status("Conversion stopped", "orange")
        else:
            self.append_conversion_log("CONVERSION RESULTS")
        
        self.append_conversion_log("=" * 50)
        self.append_conversion_log(f"Successful: {len(successful)}")
        if resampled:
            self.append_conversion_log(f"Resampled: {len(resampled)}")
        self.append_conversion_log(f"Failed: {len(failed)}")
        if size_warnings:
            self.append_conversion_log(f"Size warnings: {len(size_warnings)}")
        if stopped:
            self.append_conversion_log(f"Stopped: {len(stopped)}")
    
        for i, result_item in enumerate(results):
            if i < self.conversion_files_table.rowCount():
                status_item = self.conversion_files_table.item(i, 4)
                result = result_item['result']
                wav_name = result_item['file_pair']['wav_name']
                
                if result.get('stopped', False):
                    status_item.setText("⏹ Stopped")
                    status_item.setBackground(QtGui.QColor(255, 200, 100))
                    status_item.setToolTip("Conversion stopped by user")
                    self.append_conversion_log(f"⏹ {wav_name}: Stopped by user")
                    
                elif result.get('success', False):
                    size_diff = result.get('size_diff_percent', 0)
                    status_text = "✓ Done"
                    tooltip_text = "Converted successfully"
                    
                    if result.get('resampled', False):
                        sample_rate = result.get('sample_rate', 'unknown')
                        status_text = f"✓ Done ({sample_rate}Hz)"
                        tooltip_text = f"Converted with resampling to {sample_rate}Hz"
                    
                    if size_diff > 2:
                        status_text += f" (~{size_diff:.1f}%)"
                        status_item.setBackground(QtGui.QColor(255, 255, 200))
                    else:
                        status_item.setBackground(QtGui.QColor(230, 255, 230))
                    
                    status_item.setText(status_text)
                    status_item.setToolTip(tooltip_text)
            
                    final_size = result.get('final_size', 0)
                    attempts = result.get('attempts', 0)
                    conversion = result.get('conversion', 'N/A')
                    language = result_item['file_pair']['language']
                    
                    log_msg = f"✓ {wav_name} -> {language} ({final_size:,} bytes, attempts: {attempts}, Conversion: {conversion})"
                    if result.get('resampled', False):
                        log_msg += f" [Resampled to {result.get('sample_rate')}Hz]"
                    
                    self.append_conversion_log(log_msg)
                    
                else:
                    if result.get('size_warning', False):
                        status_item.setText("⚠ Size")
                        status_item.setBackground(QtGui.QColor(255, 200, 200))
                    else:
                        status_item.setText("✗ Error")
                        status_item.setBackground(QtGui.QColor(255, 230, 230))
                    
                    status_item.setToolTip(result['error'])
                    self.append_conversion_log(f"✗ {wav_name}: {result['error']}")
        
        if successful and not stopped:
            self.update_conversion_status("Deploying files...", "blue")
            self.append_conversion_log("Deploying files...")
            
            try:
                deployed_count = self.auto_deploy_converted_files_by_language(successful)
                
                self.update_conversion_status(
                    f"Done! Converted: {len(successful)}, deployed: {deployed_count}", 
                    "green"
                )
                
                self.append_conversion_log(f"Files deployed to MOD_P: {deployed_count}")
                self.append_conversion_log("Conversion completed successfully!")

                message = f"Conversion completed!\n\nSuccessful: {len(successful)}\nFailed: {len(failed)}"
                if size_warnings:
                    message += f"\nSize warnings: {len(size_warnings)}"
                
                QtWidgets.QMessageBox.information(
                    self, "Conversion Complete", message
                )
                
            except Exception as e:
                self.update_conversion_status("Deployment error", "red")
                self.append_conversion_log(f"DEPLOYMENT ERROR: {str(e)}")
                QtWidgets.QMessageBox.warning(
                    self, "Error", 
                    f"Conversion complete, but deployment error:\n{str(e)}"
                )
        elif stopped:
            self.update_conversion_status("Conversion stopped by user", "orange")
            QtWidgets.QMessageBox.information(
                self, "Conversion Stopped", 
                f"Conversion was stopped by user.\n\nCompleted: {len(successful)}\nRemaining: {len(stopped)}"
            )
        else:
            self.update_conversion_status("Conversion failed", "red")
            self.append_conversion_log("All files failed to convert")

            self.wav_converter_tabs.setCurrentIndex(1)
            
            QtWidgets.QMessageBox.warning(
                self, "Error", 
                f"All files failed to convert: {len(failed)} files.\n"
                f"See logs for details."
            )
    def auto_deploy_converted_files_by_language(self, successful_conversions):
        deployed_count = 0
        
        for conversion in successful_conversions:
            try:
                source_path = conversion['result']['output_path']
                file_pair = conversion['file_pair']
                language = file_pair['language']
                file_id = file_pair['file_id']
                
                if language == "SFX":
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
                else:
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", language)
                
                os.makedirs(target_dir, exist_ok=True)
                
                dest_filename = f"{file_id}.wem"
                dest_path = os.path.join(target_dir, dest_filename)
                
                shutil.copy2(source_path, dest_path)
                deployed_count += 1
                
                DEBUG.log(f"Deployed: {file_pair['wav_name']} -> {dest_filename} in {language}")
                
            except Exception as e:
                DEBUG.log(f"Error deploying {file_pair['wav_name']}: {e}", "ERROR")
                raise e
        
        return deployed_count

    def auto_deploy_converted_files(self, successful_conversions):
       
        language = self.target_language_combo.currentText()
        
        if language == "SFX":
            target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
        else:
            target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", language)
        
        os.makedirs(target_dir, exist_ok=True)
        
        copied_count = 0
        for conversion in successful_conversions:
            try:
                source_path = conversion['result']['output_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(target_dir, filename)
                
                shutil.copy2(source_path, dest_path)
                copied_count += 1
                
                DEBUG.log(f"Deployed: {filename} to {language}")
                
            except Exception as e:
                DEBUG.log(f"Error deploying {filename}: {e}", "ERROR")
                raise e
        
        DEBUG.log(f"Auto-deployed {copied_count} files to {target_dir}")
    def create_wem_processor_main_tab(self):
        """Create WEM processor with subtabs"""
   
        wem_tab = QtWidgets.QWidget()
        wem_layout = QtWidgets.QVBoxLayout(wem_tab)
        
  
        warning_label = QtWidgets.QLabel(f"""
        <div style="background-color: #ffebcc; border: 2px solid #ff9800; padding: 10px; border-radius: 5px;">
        <h3 style="color: #e65100; margin: 0;">{self.tr("wem_processor_warning")}</h3>
        <p style="margin: 5px 0;"><b>{self.tr("wem_processor_desc")}</b></p>
        <p style="margin: 5px 0;">{self.tr("wem_processor_recommendation")}</p>
        </div>
        """)
        wem_layout.addWidget(warning_label)
   
        self.wem_processor_tabs = QtWidgets.QTabWidget()

        self.create_wem_processing_tab()
        
        wem_layout.addWidget(self.wem_processor_tabs)
        
        self.converter_tabs.addTab(wem_tab, "WEM Processor (Old)")
    def show_cleanup_dialog(self, subtitle_files, localization_path):
        """Show dialog for selecting files to delete"""
        
        if subtitle_files:
            DEBUG.log(f"First subtitle file keys: {list(subtitle_files[0].keys())}")
            DEBUG.log(f"First subtitle file: {subtitle_files[0]}")
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("cleanup_mod_subtitles"))
        dialog.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(dialog)

        header_label = QtWidgets.QLabel(self.tr("cleanup_subtitles_found").format(count=len(subtitle_files)))
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(header_label)
        
        info_label = QtWidgets.QLabel(f"Location: {localization_path}")
        info_label.setStyleSheet("color: #666; padding-bottom: 10px;")
        layout.addWidget(info_label)

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        
        select_all_btn = QtWidgets.QPushButton(self.tr("select_all"))
        select_none_btn = QtWidgets.QPushButton(self.tr("select_none"))
        
        controls_layout.addWidget(select_all_btn)
        controls_layout.addWidget(select_none_btn)
        controls_layout.addStretch()

        group_label = QtWidgets.QLabel(self.tr("quick_select"))
        controls_layout.addWidget(group_label)

        languages = set()
        for f in subtitle_files:
            if 'language' in f:
                languages.add(f['language'])
            elif 'lang' in f:
                languages.add(f['lang'])
        
        lang_combo = None
        if len(languages) > 1:
            lang_combo = QtWidgets.QComboBox()
            lang_combo.addItem(self.tr("select_by_language"))
            for lang in sorted(languages):
                count = sum(1 for f in subtitle_files if f.get('language', f.get('lang', '')) == lang)
                lang_combo.addItem(f"{lang} ({count} files)")
            controls_layout.addWidget(lang_combo)
        
        layout.addWidget(controls_widget)
        
        list_widget = QtWidgets.QListWidget()
        checkboxes = []
        
        for file_info in subtitle_files:
            item_widget = QtWidgets.QWidget()
            item_layout = QtWidgets.QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)
            
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True) 
            checkboxes.append(checkbox)
            
            filename = file_info.get('file') or file_info.get('filename') or file_info.get('path') or str(file_info)
            language = file_info.get('language') or file_info.get('lang') or 'Unknown'
            
            if isinstance(filename, str) and ('/' in filename or '\\' in filename):
                filename = os.path.basename(filename)
            
            file_label = QtWidgets.QLabel(f"{filename} ({language})")
            
            item_layout.addWidget(checkbox)
            item_layout.addWidget(file_label)
            item_layout.addStretch()
            
            list_item = QtWidgets.QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            list_widget.addItem(list_item)
            list_widget.setItemWidget(list_item, item_widget)
        
        layout.addWidget(list_widget)
        
        def select_all():
            for checkbox in checkboxes:
                checkbox.setChecked(True)
        
        def select_none():
            for checkbox in checkboxes:
                checkbox.setChecked(False)
        
        def select_by_language(index):
            if lang_combo and index > 0:
                selected_lang = lang_combo.itemText(index).split(' (')[0]
                for i, file_info in enumerate(subtitle_files):
                    file_lang = file_info.get('language') or file_info.get('lang', '')
                    checkboxes[i].setChecked(file_lang == selected_lang)
        
        select_all_btn.clicked.connect(select_all)
        select_none_btn.clicked.connect(select_none)
        if lang_combo:
            lang_combo.currentIndexChanged.connect(select_by_language)
        
        button_box = QtWidgets.QDialogButtonBox()
        delete_btn = button_box.addButton(self.tr("delete_selected"), QtWidgets.QDialogButtonBox.ActionRole)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        
        cancel_btn = button_box.addButton(QtWidgets.QDialogButtonBox.Cancel)
        
        layout.addWidget(button_box)

        def delete_selected():
            selected_files = []
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    selected_files.append(subtitle_files[i])
            
            if not selected_files:
                QtWidgets.QMessageBox.warning(
                    dialog, self.tr("no_selection"), 
                    self.tr("select_files_to_delete")
                )
                return

            reply = QtWidgets.QMessageBox.question(
                dialog, self.tr("confirm_deletion"),
                self.tr("delete_files_warning").format(count=len(selected_files)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.delete_subtitle_files(selected_files)
                dialog.accept()
        
        delete_btn.clicked.connect(delete_selected)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
    def delete_subtitle_files(self, files_to_delete):
        """Delete selected subtitle files"""
        DEBUG.log(f"Deleting {len(files_to_delete)} subtitle files")
        
        progress = ProgressDialog(self, "Deleting Subtitle Files")
        progress.show()
        
        deleted_count = 0
        error_count = 0

        self.subtitle_export_status.clear()
        self.subtitle_export_status.append("=== Cleaning Up MOD_P Subtitles ===")
        self.subtitle_export_status.append(f"Deleting {len(files_to_delete)} files...")
        self.subtitle_export_status.append("")
        
        for i, file_info in enumerate(files_to_delete):
            progress.set_progress(
                int((i / len(files_to_delete)) * 100),
                f"Deleting {file_info['filename']}..."
            )
            
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
                    deleted_count += 1
                    self.subtitle_export_status.append(f"✓ Deleted: {file_info['relative_path']}")
                    DEBUG.log(f"Deleted: {file_info['path']}")
 
                    dir_path = os.path.dirname(file_info['path'])
                    try:
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self.subtitle_export_status.append(f"✓ Removed empty directory: {os.path.basename(dir_path)}")
                            
              
                            parent_dir = os.path.dirname(dir_path)
                            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                                self.subtitle_export_status.append(f"✓ Removed empty directory: {os.path.basename(parent_dir)}")
                    except OSError:
                        pass 
                        
                else:
                    self.subtitle_export_status.append(f"⚠ File already deleted: {file_info['relative_path']}")
                    
            except Exception as e:
                error_count += 1
                self.subtitle_export_status.append(f"✗ Error deleting {file_info['relative_path']}: {str(e)}")
                DEBUG.log(f"Error deleting {file_info['path']}: {e}", "ERROR")
        
        progress.close()
        
        self.subtitle_export_status.append("")
        self.subtitle_export_status.append("=== Cleanup Complete ===")
        self.subtitle_export_status.append(f"Files deleted: {deleted_count}")
        if error_count > 0:
            self.subtitle_export_status.append(f"Errors: {error_count}")
        
     
        if error_count == 0:
            QtWidgets.QMessageBox.information(
                self, "Cleanup Complete",
                f"Successfully deleted {deleted_count} subtitle files from MOD_P"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Cleanup Complete with Errors",
                f"Deleted {deleted_count} files successfully\n"
                f"{error_count} files had errors\n\n"
                f"Check the status log for details"
            )
        
        DEBUG.log(f"Cleanup complete: {deleted_count} deleted, {error_count} errors")
    def cleanup_mod_p_subtitles(self):
        """Clean up subtitle files from MOD_P folder"""
        DEBUG.log("=== Cleanup MOD_P Subtitles ===")
        
        localization_path = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
        
        if not os.path.exists(localization_path):
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_localization_message").format(path=localization_path)
            )
            return
        

        subtitle_files = []
        
        try:
            for root, dirs, files in os.walk(localization_path):
                for file in files:
                    if file.endswith('.locres'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, localization_path)
                        
                     
                        path_parts = relative_path.split(os.sep)
                        if len(path_parts) >= 3:
                            category = path_parts[0]
                            language = path_parts[1]
                            filename = path_parts[2]
                        else:
                            category = "Unknown"
                            language = "Unknown"
                            filename = file
                  
                        file_size = os.path.getsize(file_path)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        subtitle_files.append({
                            'path': file_path,
                            'relative_path': relative_path,
                            'category': category,
                            'language': language,
                            'filename': filename,
                            'size': file_size,
                            'modified': file_time
                        })
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error scanning localization folder:\n{str(e)}")
            return
        
        if not subtitle_files:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_subtitle_files").format(path=localization_path)
            )
            return
        
        DEBUG.log(f"Found {len(subtitle_files)} subtitle files in MOD_P")
        

        self.show_cleanup_dialog(subtitle_files, localization_path)
    def create_localization_exporter_simple_tab(self):
        """Create simple localization exporter tab with cleanup functionality"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel(self.tr("localization_exporter"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        info_group = QtWidgets.QGroupBox(self.tr("export_modified_subtitles"))
        info_layout = QtWidgets.QVBoxLayout(info_group)
        
        info_text = QtWidgets.QLabel(f"""   
            <h3>{self.tr("export_modified_subtitles")}</h3>
            <p>{self.tr("exports_modified_subtitles_desc")}</p>
            <ul>
                <li>{self.tr("creates_mod_p_structure")}</li>
                <li>{self.tr("supports_multiple_categories")}</li>
                <li>{self.tr("each_language_separate_folder")}</li>
                <li>{self.tr("ready_files_for_mods")}</li>
            </ul>
            """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
    
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
      
        export_btn = QtWidgets.QPushButton(self.tr("export_subtitles_for_game"))
        export_btn.setMaximumWidth(200)
        export_btn.clicked.connect(self.export_subtitles_for_game)
        
 
        cleanup_btn = QtWidgets.QPushButton(self.tr("cleanup_mod_subtitles"))
        cleanup_btn.setMaximumWidth(200)
        cleanup_btn.clicked.connect(self.cleanup_mod_p_subtitles)
        
        buttons_layout.addWidget(export_btn)
        buttons_layout.addWidget(cleanup_btn)
        buttons_layout.addStretch()
        
        layout.addWidget(buttons_widget)
        
     
        self.subtitle_export_status = QtWidgets.QTextEdit()
        self.subtitle_export_status.setReadOnly(True)
        self.subtitle_export_status.setPlainText(self.tr("subtitle_export_ready"))
        layout.addWidget(self.subtitle_export_status)
        
        self.converter_tabs.addTab(tab, self.tr("localization_exporter"))
    def create_wem_processing_tab(self):

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel("WEM File Processing")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        card = QtWidgets.QGroupBox("Instructions")
        card_layout = QtWidgets.QVBoxLayout(card)
        
        instructions = QtWidgets.QLabel(self.tr("converter_instructions2"))
        instructions.setWordWrap(True)
        card_layout.addWidget(instructions)
        
        layout.addWidget(card)
        
        path_group = QtWidgets.QGroupBox("Source Path")
        path_layout = QtWidgets.QHBoxLayout(path_group)
        
        self.wwise_path_edit_old = QtWidgets.QLineEdit()
        self.wwise_path_edit_old.setPlaceholderText("Select WWISE folder...")
        
        browse_btn = ModernButton(self.tr("browse"), primary=True)
        browse_btn.clicked.connect(self.select_wwise_folder_old)
        
        path_layout.addWidget(self.wwise_path_edit_old)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        self.process_btn = ModernButton("Process WEM Files", primary=True)
        self.process_btn.clicked.connect(self.process_wem_files)
        layout.addWidget(self.process_btn)
        
    
        self.open_target_btn = ModernButton("Open Target Folder")
        self.open_target_btn.clicked.connect(self.open_target_folder)
        layout.addWidget(self.open_target_btn)
        
        self.converter_status_old = QtWidgets.QTextEdit()
        self.converter_status_old.setReadOnly(True)
        layout.addWidget(self.converter_status_old)
        
        self.wem_processor_tabs.addTab(tab, "Process WEM")

    def browse_wwise_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Wwise path",
            self.wwise_path_edit.text() or ""
        )
        if folder:
            self.wwise_path_edit.setText(folder)
            self.settings.data["wav_wwise_path"] = folder
            self.settings.save()

    def browse_converter_project_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose path for Wwise project",
            self.converter_project_path_edit.text() or ""
        )
        if folder:
            self.converter_project_path_edit.setText(folder)
            self.settings.data["wav_project_path"] = folder
            self.settings.save()

    def browse_wav_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose folder with WAV files",
            self.wav_folder_edit.text() or ""
        )
        if folder:
            self.wav_folder_edit.setText(folder)
            self.settings.data["wav_folder_path"] = folder
            self.settings.save()

    def clear_conversion_files(self):
        """Clear conversion files list"""
        if self.wav_converter.file_pairs:
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("confirmation"), 
                self.tr("confirm_clear"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.wav_converter.clear_file_pairs()
                self.conversion_files_table.setRowCount(0)
                self.update_conversion_files_table()

    def update_conversion_files_list(self):
        self.conversion_files_list.clear()
        for i, pair in enumerate(self.wav_converter.file_pairs):
            display_text = f"{i+1}. {pair['wav_name']} → {pair['target_name']} ({pair['target_size']:,} bytes)"
            self.conversion_files_list.addItem(display_text)


    def update_conversion_status(self, message, color="green"):
        color_map = {
            "green": "#4CAF50",
            "blue": "#2196F3", 
            "red": "#F44336",
            "orange": "#FF9800"
        }
        self.conversion_status.setText(message)
        self.conversion_status.setStyleSheet(f"color: {color_map.get(color, color)};")


    def select_wwise_folder_old(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select WWISE Folder", 
            self.settings.data.get("last_directory", "")
        )
        
        if folder:
            self.wwise_path_edit_old.setText(folder)
            self.settings.data["last_directory"] = folder
            self.settings.save()
    def create_language_tab(self, lang):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        controls = QtWidgets.QWidget()
        controls.setMaximumHeight(40)
        controls_layout = QtWidgets.QHBoxLayout(controls)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        filter_combo = QtWidgets.QComboBox()
        filter_combo.addItems([
            self.tr("all_files"), 
            self.tr("with_subtitles"), 
            self.tr("without_subtitles"), 
            self.tr("modified"),
            self.tr("modded")
        ])
        filter_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))

        sort_combo = QtWidgets.QComboBox()
        sort_combo.addItems([
            self.tr("name_a_z"), 
            self.tr("name_z_a"), 
            self.tr("id_asc"), 
            self.tr("id_desc"), 
            self.tr("recent_first")
        ])
        sort_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))
        
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("filter")))
        controls_layout.addWidget(filter_combo)
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("sort")))
        controls_layout.addWidget(sort_combo)
        controls_layout.addStretch()

        stats_label = QtWidgets.QLabel()
        controls_layout.addWidget(stats_label)
        
        layout.addWidget(controls)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels([self.tr("name"), self.tr("id"), self.tr("subtitle"), self.tr("status")])
        tree.setColumnWidth(0, 350)
        tree.setColumnWidth(1, 100)
        tree.setColumnWidth(2, 400)
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(lambda pos: self.show_context_menu(lang, pos))
        tree.itemSelectionChanged.connect(lambda: self.on_selection_changed(lang))
        tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        splitter.addWidget(tree)
        

        details_panel = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(details_panel)
        

        player_widget = QtWidgets.QWidget()
        player_layout = QtWidgets.QVBoxLayout(player_widget)
        

        audio_progress = QtWidgets.QProgressBar()
        audio_progress.setTextVisible(False)
        audio_progress.setMaximumHeight(10)
        player_layout.addWidget(audio_progress)
        

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        

        play_btn = QtWidgets.QPushButton("▶")
        play_btn.setMaximumWidth(40)
        play_btn.clicked.connect(lambda: self.play_current())
        
        play_mod_btn = QtWidgets.QPushButton(f"▶ {self.tr('mod')}")
        play_mod_btn.setMaximumWidth(60)
        play_mod_btn.setToolTip("Play modified audio if available")
        play_mod_btn.clicked.connect(lambda: self.play_current(play_mod=True))
        play_mod_btn.hide()  
        
        stop_btn = QtWidgets.QPushButton("■")
        stop_btn.setMaximumWidth(40)
        stop_btn.clicked.connect(self.stop_audio)
        

        time_label = QtWidgets.QLabel("00:00 / 00:00")
        time_label.setAlignment(QtCore.Qt.AlignCenter)
        

        size_warning = QtWidgets.QLabel()
        size_warning.setStyleSheet("color: red; font-weight: bold;")
        size_warning.hide()
        
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(play_mod_btn)
        controls_layout.addWidget(stop_btn)
        controls_layout.addWidget(time_label)
        controls_layout.addWidget(size_warning)
        controls_layout.addStretch()
        
        player_layout.addWidget(controls_widget)
        details_layout.addWidget(player_widget)
        

        subtitle_group = QtWidgets.QGroupBox(self.tr("subtitle_preview"))
        subtitle_layout = QtWidgets.QVBoxLayout(subtitle_group)
        
        subtitle_text = QtWidgets.QTextEdit()
        subtitle_text.setReadOnly(True)
        subtitle_text.setMaximumHeight(150)
        subtitle_layout.addWidget(subtitle_text)
        

        original_subtitle_label = QtWidgets.QLabel()
        original_subtitle_label.setWordWrap(True)
        original_subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        original_subtitle_label.hide()
        subtitle_layout.addWidget(original_subtitle_label)
        
        details_layout.addWidget(subtitle_group)
        

        info_group = QtWidgets.QGroupBox(self.tr("file_info"))
        info_layout = QtWidgets.QVBoxLayout(info_group)

        basic_info_widget = QtWidgets.QWidget()
        basic_info_layout = QtWidgets.QFormLayout(basic_info_widget)

        info_labels = {
            "id": QtWidgets.QLabel(),
            "name": QtWidgets.QLabel(),
            "path": QtWidgets.QLabel(),
            "source": QtWidgets.QLabel()
        }

        basic_info_layout.addRow(f"{self.tr('id')}:", info_labels["id"])
        basic_info_layout.addRow(f"{self.tr('name')}:", info_labels["name"])
        basic_info_layout.addRow(f"{self.tr('path')}:", info_labels["path"])
        basic_info_layout.addRow(f"{self.tr('source')}:", info_labels["source"])
        info_layout.addWidget(basic_info_widget)


        comparison_group = QtWidgets.QGroupBox(self.tr("audio_comparison"))
        comparison_layout = QtWidgets.QHBoxLayout(comparison_group)

      
        original_widget = QtWidgets.QWidget()
        original_layout = QtWidgets.QVBoxLayout(original_widget)
        original_header = QtWidgets.QLabel(self.tr("original_audio"))
        original_header.setStyleSheet("font-weight: bold; color: #2196F3; padding: 5px;")
        original_layout.addWidget(original_header)

        original_info_layout = QtWidgets.QFormLayout()
        original_info_labels = {
            "duration": QtWidgets.QLabel(),
            "size": QtWidgets.QLabel(),
            "sample_rate": QtWidgets.QLabel(),
            "bitrate": QtWidgets.QLabel(),
            "channels": QtWidgets.QLabel()
        }

        original_info_layout.addRow(self.tr("duration"), original_info_labels["duration"])
        original_info_layout.addRow(self.tr("size"), original_info_labels["size"])
        original_info_layout.addRow(self.tr("sample_rate"), original_info_labels["sample_rate"])
        original_info_layout.addRow(self.tr("bitrate"), original_info_labels["bitrate"])
        original_info_layout.addRow(self.tr("channels"), original_info_labels["channels"])

        original_layout.addLayout(original_info_layout)

     
        modified_widget = QtWidgets.QWidget()
        modified_layout = QtWidgets.QVBoxLayout(modified_widget)
        modified_header = QtWidgets.QLabel(self.tr("modified_audio"))
        modified_header.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 5px;")
        modified_layout.addWidget(modified_header)

        modified_info_layout = QtWidgets.QFormLayout()
        modified_info_labels = {
            "duration": QtWidgets.QLabel(),
            "size": QtWidgets.QLabel(),
            "sample_rate": QtWidgets.QLabel(),
            "bitrate": QtWidgets.QLabel(),
            "channels": QtWidgets.QLabel()
        }

        modified_info_layout.addRow(f"{self.tr("duration")}", modified_info_labels["duration"])
        modified_info_layout.addRow(f"{self.tr("size")}", modified_info_labels["size"])
        modified_info_layout.addRow(f"{self.tr("sample_rate")}", modified_info_labels["sample_rate"])
        modified_info_layout.addRow(f"{self.tr("bitrate")}", modified_info_labels["bitrate"])
        modified_info_layout.addRow(f"{self.tr("channels")}", modified_info_labels["channels"])

        modified_layout.addLayout(modified_info_layout)

     
        comparison_layout.addWidget(original_widget)

   
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #cccccc; }")
        comparison_layout.addWidget(separator)

        comparison_layout.addWidget(modified_widget)

        info_layout.addWidget(comparison_group)


        markers_group = QtWidgets.QGroupBox(self.tr("audio_markers"))
        markers_layout = QtWidgets.QVBoxLayout(markers_group)

 
        markers_comparison = QtWidgets.QHBoxLayout()


        original_markers_widget = QtWidgets.QWidget()
        original_markers_layout = QtWidgets.QVBoxLayout(original_markers_widget)

        original_markers_header = QtWidgets.QLabel(self.tr("original_markers"))
        original_markers_header.setStyleSheet("font-weight: bold; color: #2196F3; padding: 2px;")
        original_markers_layout.addWidget(original_markers_header)

        original_markers_list = QtWidgets.QListWidget()
        original_markers_list.setMaximumHeight(120)
        original_markers_list.setAlternatingRowColors(True)
        original_markers_layout.addWidget(original_markers_list)


        modified_markers_widget = QtWidgets.QWidget()
        modified_markers_layout = QtWidgets.QVBoxLayout(modified_markers_widget)

        modified_markers_header = QtWidgets.QLabel(self.tr("modified_markers"))
        modified_markers_header.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 2px;")
        modified_markers_layout.addWidget(modified_markers_header)

        modified_markers_list = QtWidgets.QListWidget()
        modified_markers_list.setMaximumHeight(120)
        modified_markers_list.setAlternatingRowColors(True)
        modified_markers_layout.addWidget(modified_markers_list)

        markers_comparison.addWidget(original_markers_widget)

 
        markers_separator = QtWidgets.QFrame()
        markers_separator.setFrameShape(QtWidgets.QFrame.VLine)
        markers_separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        markers_separator.setStyleSheet("QFrame { color: #cccccc; }")
        markers_comparison.addWidget(markers_separator)

        markers_comparison.addWidget(modified_markers_widget)

        markers_layout.addLayout(markers_comparison)
        info_layout.addWidget(markers_group)

        details_layout.addWidget(info_group)
        details_layout.addStretch()
        
        splitter.addWidget(details_panel)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        

        self.tab_widgets[lang] = {
            "filter_combo": filter_combo,
            "sort_combo": sort_combo,
            "tree": tree,
            "stats_label": stats_label,
            "subtitle_text": subtitle_text,
            "original_subtitle_label": original_subtitle_label,
            "info_labels": info_labels,
            "original_info_labels": original_info_labels,
            "modified_info_labels": modified_info_labels,
            "original_markers_list": original_markers_list,
            "modified_markers_list": modified_markers_list,
            "details_panel": details_panel,
            "audio_progress": audio_progress,
            "time_label": time_label,
            "play_btn": play_btn,
            "play_mod_btn": play_mod_btn,
            "stop_btn": stop_btn,
            "size_warning": size_warning
        }
        
        self.tabs.addTab(tab, f"{lang} ({len(self.entries_by_lang.get(lang, []))})")
    def get_wem_audio_info_with_markers(self, wem_path):
        """Get detailed audio information including markers from WEM file"""
        info = self.get_wem_audio_info(wem_path)
        
        if info is None:
            return None
        

        try:
            analyzer = WEMAnalyzer(wem_path)
            if analyzer.analyze():
                info['markers'] = analyzer.get_markers_info()
       
                if analyzer.sample_rate > 0:
                    info['sample_rate'] = analyzer.sample_rate
            else:
                info['markers'] = []
        except Exception as e:
            DEBUG.log(f"Error analyzing markers: {e}", "ERROR")
            info['markers'] = []
        
        return info

    def format_markers_for_display(self, markers):

        formatted_markers = []
        
        for marker in markers:
   
            if marker['position'] == 0:
                time_str = "Sample 0"
            else:
    
                time_seconds = marker['time_seconds']
                if time_seconds >= 1.0:

                    minutes = int(time_seconds // 60)
                    seconds = time_seconds % 60
                    time_str = f"{minutes:02d}:{seconds:06.3f}"
                else:

                    time_str = f"{time_seconds:.3f}s"
            

            label = marker['label']
            
    
            if label and label != "No label":
                display_text = f"#{marker['id']}: {time_str} - {label}"
            else:
                display_text = f"#{marker['id']}: {time_str}"
            
            formatted_markers.append(display_text)
        
        return formatted_markers
    def get_wem_audio_info(self, wem_path):
        """Get detailed audio information from WEM file"""
        try:
            result = subprocess.run(
                [self.vgmstream_path, "-m", wem_path],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                info = {
                    'sample_rate': 0,
                    'channels': 0,
                    'samples': 0,
                    'duration_ms': 0,
                    'bitrate': 0,
                    'format': 'Unknown'
                }
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if "sample rate:" in line:
                        try:
                            info['sample_rate'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "channels:" in line:
                        try:
                            info['channels'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "stream total samples:" in line:
                        try:
                            info['samples'] = int(line.split(':')[1].strip().split()[0])
                        except:
                            pass
                            
                    elif "encoding:" in line:
                        try:
                            info['format'] = line.split(':')[1].strip()
                        except:
                            pass
                

                if info['sample_rate'] > 0 and info['samples'] > 0:
                    info['duration_ms'] = int((info['samples'] / info['sample_rate']) * 1000)
                    

                    file_size = os.path.getsize(wem_path)
                    if info['duration_ms'] > 0:
                        info['bitrate'] = int((file_size * 8) / (info['duration_ms'] / 1000))
                
                return info
                
        except Exception as e:
            DEBUG.log(f"Error getting audio info: {e}", "ERROR")
            
        return None

    def format_audio_info(self, info, label_suffix=""):
        """Format audio info for display"""
        if not info:
            return {
                f'duration{label_suffix}': "N/A",
                f'size{label_suffix}': "N/A", 
                f'sample_rate{label_suffix}': "N/A",
                f'bitrate{label_suffix}': "N/A",
                f'channels{label_suffix}': "N/A"
            }
        
        # Format duration
        duration_ms = info.get('duration_ms', 0)
        if duration_ms > 0:
            minutes = int(duration_ms // 60000)
            seconds = (duration_ms % 60000) / 1000.0
            duration_str = f"{minutes:02d}:{seconds:05.2f}"
        else:
            duration_str = "Unknown"
        
        # Format sample rate
        sample_rate = info.get('sample_rate', 0)
        if sample_rate > 0:
            if sample_rate >= 1000:
                sample_rate_str = f"{sample_rate/1000:.1f} kHz"
            else:
                sample_rate_str = f"{sample_rate} Hz"
        else:
            sample_rate_str = "Unknown"
        
        # Format bitrate
        bitrate = info.get('bitrate', 0)
        if bitrate > 0:
            if bitrate >= 1000:
                bitrate_str = f"{bitrate/1000:.1f} kbps"
            else:
                bitrate_str = f"{bitrate} bps"
        else:
            bitrate_str = "Unknown"
        
        # Format channels
        channels = info.get('channels', 0)
        if channels == 1:
            channels_str = "Mono"
        elif channels == 2:
            channels_str = "Stereo"
        elif channels > 2:
            channels_str = f"{channels} channels"
        else:
            channels_str = "Unknown"
        
        return {
            f'duration{label_suffix}': duration_str,
            f'sample_rate{label_suffix}': sample_rate_str,
            f'bitrate{label_suffix}': bitrate_str,
            f'channels{label_suffix}': channels_str
        }
    def export_subtitles(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Subtitles", "subtitles_export.json", 
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if path:
            if path.endswith(".json"):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"Subtitles": self.subtitles}, f, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for key, subtitle in sorted(self.subtitles.items()):
                        f.write(f"{key}: {subtitle}\n")
                        
            self.status_bar.showMessage(f"Exported to {path}", 3000)

    def import_subtitles(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Subtitles", "", "JSON Files (*.json)"
        )
        
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                imported = data.get("Subtitles", {})
                count = len(imported)
                
                reply = QtWidgets.QMessageBox.question(
                    self, "Import Subtitles",
                    f"Import {count} subtitles?\nThis will overwrite existing subtitles.",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.subtitles.update(imported)
                    
                    for key, value in imported.items():
                        if key in self.original_subtitles and self.original_subtitles[key] != value:
                            self.modified_subtitles.add(key)
                        else:
                            self.modified_subtitles.discard(key)

                    current_lang = self.get_current_language()
                    if current_lang and current_lang in self.tab_widgets:
                        self.populate_tree(current_lang)
                        
                    self.status_bar.showMessage(f"Imported {count} subtitles", 3000)
                    self.update_status()
                    
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Import Error", str(e))

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = f"""
        <h2>{self.tr("keyboard_shortcuts")}</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
        <tr style="background-color: #f0f0f0;">
            <th>{self.tr("shortcuts_table_action")}</th>
            <th>{self.tr("shortcuts_table_shortcut")}</th>
            <th>{self.tr("shortcuts_table_description")}</th>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_edit_subtitle")}</b></td>
            <td>F2</td>
            <td>{self.tr("shortcut_edit_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_save_subtitles")}</b></td>
            <td>Ctrl+S</td>
            <td>{self.tr("shortcut_save_all_changes")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_export_audio")}</b></td>
            <td>Ctrl+E</td>
            <td>{self.tr("shortcut_export_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_revert_original")}</b></td>
            <td>Ctrl+R</td>
            <td>{self.tr("shortcut_revert_selected")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_deploy_run")}</b></td>
            <td>F5</td>
            <td>{self.tr("shortcut_deploy_launch")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_debug_console")}</b></td>
            <td>Ctrl+D</td>
            <td>{self.tr("shortcut_show_debug")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_settings")}</b></td>
            <td>Ctrl+,</td>
            <td>{self.tr("shortcut_open_settings")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_exit")}</b></td>
            <td>Ctrl+Q</td>
            <td>{self.tr("shortcut_close_app")}</td>
        </tr>
        </table>

        <h3>{self.tr("mouse_actions")}</h3>
        <ul>
            <li>{self.tr("mouse_double_subtitle")}</li>
            <li>{self.tr("mouse_double_file")}</li>
            <li>{self.tr("mouse_right_click")}</li>
        </ul>
        """
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(shortcuts_text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()
    def check_updates_on_startup(self):
        thread = threading.Thread(target=self._check_updates_thread, args=(True,))
        thread.daemon = True
        thread.start()

    def check_updates(self):
        self.statusBar().showMessage("Checking for updates...")
        
        thread = threading.Thread(target=self._check_updates_thread, args=(False,))
        thread.daemon = True
        thread.start()

    def _check_updates_thread(self, silent=False):
        try:
            repo_url = "https://api.github.com/repos/Bezna/OutlastTrials_AudioEditor/releases/latest"
            
            response = requests.get(repo_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            download_url = release_data['html_url']
            release_notes = release_data.get('body', 'No release notes available.')

            if version.parse(latest_version) > version.parse(current_version):
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_update_available",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, latest_version),
                    QtCore.Q_ARG(str, download_url),
                    QtCore.Q_ARG(str, release_notes),
                    QtCore.Q_ARG(bool, silent)
                )
            else:
                if not silent:
                    QtCore.QMetaObject.invokeMethod(
                        self, "_show_up_to_date",
                        QtCore.Qt.QueuedConnection
                    )
                else:

                    QtCore.QMetaObject.invokeMethod(
                        self, "_update_status_silent",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(str, "")
                    )
                    
        except requests.exceptions.RequestException as e:

            if not silent:
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_network_error",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, str(e))
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self, "_update_status_silent",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "")
                )
        except Exception as e:
 
            if not silent:
                QtCore.QMetaObject.invokeMethod(
                    self, "_show_error",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, str(e))
                )
            else:
                QtCore.QMetaObject.invokeMethod(
                    self, "_update_status_silent",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "")
                )
    @QtCore.pyqtSlot(str, str, str, bool)
    def _show_update_available(self, latest_version, download_url, release_notes, silent=False):
        """Show update available dialog"""
        self.statusBar().showMessage("Update available!")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        
        text = f"""New version available: v{latest_version}
    Current version: {current_version}

    Release Notes:
    {release_notes[:300]}{'...' if len(release_notes) > 300 else ''}

    Do you want to download the update?"""
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if msg.exec_() == QtWidgets.QMessageBox.Yes:
            import webbrowser
            webbrowser.open(download_url)
    @QtCore.pyqtSlot()
    def _show_up_to_date(self):
        """Show up to date message"""
        self.statusBar().showMessage("You are running the latest version.")
        
        QtWidgets.QMessageBox.information(
            self, "Check for Updates",
            "You are running OutlastTrials AudioEditor " + current_version + "\n\n"
            "This is the latest version!"
        )

    @QtCore.pyqtSlot(str)
    def _show_network_error(self, error):
        """Show network error"""
        self.statusBar().showMessage("Failed to check for updates.")
        
        QtWidgets.QMessageBox.warning(
            self, "Update Check Failed",
            f"Failed to check for updates.\n\n"
            f"Please check your internet connection and try again.\n\n"
            f"Error: {error}\n\n"
            f"You can manually check for updates at:\n"
            f"https://github.com/Bezna/OutlastTrials_AudioEditor"
        )

    @QtCore.pyqtSlot(str)
    def _show_error(self, error):
        """Show general error"""
        self.statusBar().showMessage("Error checking for updates.")
        
        QtWidgets.QMessageBox.critical(
            self, "Error",
            f"An error occurred while checking for updates:\n\n{error}"
        )
    @QtCore.pyqtSlot(str)
    def _update_status_silent(self, message):
        """Silently update status bar"""
        if message:
            self.statusBar().showMessage(message)
        else:
            self.statusBar().clearMessage()
    def report_bug(self):
        """Show bug report dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("report_bug"))
        dialog.setMinimumSize(500, 400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        info_label = QtWidgets.QLabel(self.tr("bug_report_info"))
        layout.addWidget(info_label)
        
        desc_label = QtWidgets.QLabel(f"{self.tr('description')}:")
        layout.addWidget(desc_label)
        
        desc_text = QtWidgets.QTextEdit()
        desc_text.setPlaceholderText(
            "Please describe:\n"
            "1. What you were trying to do\n"
            "2. What happened instead\n"
            "3. Steps to reproduce the issue"
        )
        layout.addWidget(desc_text)
        
        email_label = QtWidgets.QLabel(f"{self.tr('email_optional')}:")
        layout.addWidget(email_label)
        
        email_edit = QtWidgets.QLineEdit()
        email_edit.setPlaceholderText("your@email.com")
        layout.addWidget(email_edit)
        
        btn_layout = QtWidgets.QHBoxLayout()
        
        copy_btn = QtWidgets.QPushButton(self.tr("copy_report_clipboard"))
        send_btn = QtWidgets.QPushButton(self.tr("open_github_issues"))
        cancel_btn = QtWidgets.QPushButton("Cancel")
        
        def copy_report():
            report = f"""
    BUG REPORT - OutlastTrials AudioEditor {current_version}
    ==========================================
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Email: {email_edit.text() or 'Not provided'}

    Description:
    {desc_text.toPlainText()}

    System Info:
    - OS: {sys.platform}
    - Python: {sys.version.split()[0]}
    - PyQt5: {QtCore.PYQT_VERSION_STR}

    Debug Log (last 50 lines):
    {chr(10).join(DEBUG.logs[-50:])}
    """
            QtWidgets.QApplication.clipboard().setText(report)
            QtWidgets.QMessageBox.information(dialog, "Success", "Bug report copied to clipboard!")
        
        def open_github():
            import webbrowser
            webbrowser.open("https://github.com/Bezna/OutlastTrials_AudioEditor/issues")
        
        copy_btn.clicked.connect(copy_report)
        send_btn.clicked.connect(open_github)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def show_about(self):
        """Show about dialog with animations"""
        about_dialog = QtWidgets.QDialog(self)
        about_dialog.setWindowTitle(self.tr("about") + " OutlastTrials AudioEditor")
        about_dialog.setMinimumSize(600, 500)
        
        layout = QtWidgets.QVBoxLayout(about_dialog)

        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0078d4, stop:1 #106ebe);
                border-radius: 5px;
            }
        """)
        header_layout = QtWidgets.QVBoxLayout(header_widget)
        
        title_label = QtWidgets.QLabel("OutlastTrials AudioEditor")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
            QLabel:hover {
                color: #ffff99;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setCursor(QtCore.Qt.PointingHandCursor)
        
        title_label.mousePressEvent = lambda event: self.show_secret_easter_egg()
        
        version_label = QtWidgets.QLabel("Version " + current_version)
        version_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 16px;
                background: transparent;
            }
        """)
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(version_label)
        header_widget.setFixedHeight(120)
        
        layout.addWidget(header_widget)

        about_tabs = QtWidgets.QTabWidget()

        about_content = QtWidgets.QTextBrowser()
        about_content.setOpenExternalLinks(True)
        about_content.setHtml(f"""
        <div style="padding: 20px;">
        <p style="font-size: 14px; line-height: 1.6;">
        {self.tr("about_description")}
        </p>

        <h3>{self.tr("key_features")}</h3>
        <ul style="line-height: 1.8;">
            <li>{self.tr("audio_management")}</li>
            <li>{self.tr("subtitle_editing")}</li>
            <li>{self.tr("mod_creation")}</li>
            <li>{self.tr("multi_language")}</li>
            <li>{self.tr("modern_ui")}</li>
        </ul>

        <h3>{self.tr("technology_stack")}</h3>
        <p>{self.tr("built_with")}</p>
        <ul>
            <li>{self.tr("unreal_locres_tool")}</li>
            <li>{self.tr("vgmstream_tool")}</li>
            <li>{self.tr("repak_tool")}</li>
        </ul>
        </div>
        """)
        about_tabs.addTab(about_content, self.tr("about"))

        credits_content = QtWidgets.QTextBrowser()
        credits_content.setHtml(f"""
        <div style="padding: 20px;">
        <h3>{self.tr("development_team")}</h3>
        <p><b>Lead Developer:</b> Bezna</p>        
        <p>Tester/Polish Translator: Alaneg</p>
        
        <h3>Special Thanks</h3>
        <ul>
            <li>vgmstream team - For audio conversion tools</li>
            <li>UnrealLocres developers - For localization support</li>
            <li>hypermetric - For mod packaging</li>
            <li>Red Barrels - For creating Outlast Trials</li>
        </ul>
        
        <h3>Open Source Libraries</h3>
        <ul>
            <li>PyQt5 - GUI Framework</li>
            <li>Python Standard Library</li>
        </ul>
        
        <p style="margin-top: 30px; color: #666;">
        This software is provided "as is" without warranty of any kind.
        Use at your own risk.
        </p>
        </div>
        """)
        about_tabs.addTab(credits_content, self.tr("credits"))
        
        license_content = QtWidgets.QTextBrowser()
        license_content.setHtml(f"""
        <div style="padding: 20px;">
        <h3>{self.tr("license_agreement")}</h3>
        <p>Copyright (c) 2025 OutlastTrials AudioEditor</p>
        
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        </div>
        """)
        about_tabs.addTab(license_content, self.tr("license"))
        
        layout.addWidget(about_tabs)
        
        footer_widget = QtWidgets.QWidget()
        footer_layout = QtWidgets.QHBoxLayout(footer_widget)
        
        github_btn = QtWidgets.QPushButton("GitHub")
        discord_btn = QtWidgets.QPushButton("Discord")
        donate_btn = QtWidgets.QPushButton(self.tr("donate"))
        
        github_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "GitHub", "https://github.com/Bezna/OutlastTrials_AudioEditor"))
        discord_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Discord", "My Discord: Bezna"))
        donate_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Donate", "https://www.donationalerts.com/r/bezna_"))
        
        footer_layout.addWidget(github_btn)
        footer_layout.addWidget(discord_btn)
        footer_layout.addWidget(donate_btn)
        footer_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton(self.tr("close"))
        close_btn.clicked.connect(about_dialog.close)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer_widget)
        
        about_dialog.exec_()

    def show_secret_easter_egg(self):
        secret_dialog = QtWidgets.QDialog(self)
        secret_dialog.setWindowTitle("Cat")
        secret_dialog.setFixedSize(450, 500)
        secret_dialog.setModal(True)
        secret_dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        secret_dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff6b9d, stop:0.5 #c44569, stop:1 #f8b500);
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(secret_dialog)
        layout.setSpacing(15)
        
        title = QtWidgets.QLabel("You found cat!")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                text-align: center;
                background: transparent;
                padding: 10px;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        image_container = QtWidgets.QWidget()
        image_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 10px;
            }
        """)
        image_layout = QtWidgets.QVBoxLayout(image_container)
        
        cat_image_label = QtWidgets.QLabel()
        cat_image_label.setAlignment(QtCore.Qt.AlignCenter)
        cat_image_label.setMinimumSize(300, 300)
        cat_image_label.setText("Loading cat...")
        cat_image_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                text-align: center;
                padding: 20px;
            }
        """)
        
        message = QtWidgets.QLabel("Loading...")
        message.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                text-align: center;
                background: transparent;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        message.setAlignment(QtCore.Qt.AlignCenter)
        message.setWordWrap(True)
        
        self.easter_egg_loader = EasterEggLoader()
        
        def on_config_loaded(config):
            print(f"Config loaded: {config}")
            message.setText(f"{config.get('message', 'This little cat is watching over all your audio edits!')}")
            self.easter_egg_loader.load_image(config.get('easter_egg_image', ''))
            
        def on_image_loaded(pixmap):
            print("Setting pixmap to label...")
            scaled_pixmap = pixmap.scaled(280, 280, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            cat_image_label.setPixmap(scaled_pixmap)
            cat_image_label.setText("")
            print("Pixmap set successfully!")
            
        def on_loading_failed(error):
            print(f"Loading failed: {error}")
            cat_image_label.setText(f"Failed to load content\n\n{error[:50]}...")
            message.setText("This little cat is watching over all your audio edits!")
            cat_image_label.setStyleSheet("""
                QLabel {
                    color: #ffaaaa;
                    font-size: 14px;
                    text-align: center;
                    padding: 40px;
                }
            """)
        
        self.easter_egg_loader.config_loaded.connect(on_config_loaded)
        self.easter_egg_loader.image_loaded.connect(on_image_loaded)
        self.easter_egg_loader.loading_failed.connect(on_loading_failed)
        
        self.easter_egg_loader.load_config()
        
        image_layout.addWidget(cat_image_label)
        layout.addWidget(image_container)
        layout.addWidget(message)
        
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.9);
                color: #333;
                border: none;
                border-radius: 20px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background: white;
            }
            QPushButton:pressed {
                background: #f0f0f0;
            }
        """)
        
        close_btn.clicked.connect(secret_dialog.close)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.animate_easter_egg(secret_dialog)
        
        secret_dialog.exec_()
    def animate_easter_egg(self, dialog):
        dialog.setWindowOpacity(0.0)
        dialog.show()
        
        self.fade_animation = QtCore.QPropertyAnimation(dialog, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    def restore_window_state(self):
        if self.settings.data.get("window_geometry"):
            try:
                geometry = bytes.fromhex(self.settings.data["window_geometry"])
                self.restoreGeometry(geometry)
            except:
                self.resize(1400, 800)
        else:
            self.resize(1400, 800)

    def closeEvent(self, event):
        DEBUG.log("=== Application Closing ===")
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            DEBUG.log("Auto-save timer stopped on close")
        
        self.settings.data["window_geometry"] = self.saveGeometry().toHex().data().decode()
        self.settings.save()
        
        if self.modified_subtitles:
            reply = QtWidgets.QMessageBox.question(
                self, self.tr("save_changes_question"),
                self.tr("unsaved_changes_message"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QtWidgets.QMessageBox.Yes:
                self.save_subtitles_to_file()
                
        self.stop_audio()
        event.accept()
class EasterEggLoader(QObject):
    config_loaded = pyqtSignal(dict)    
    image_loaded = pyqtSignal(object)    
    loading_failed = pyqtSignal(str)    

    def load_config(self):
        import threading
        
        def download_config():
            try:
                import requests
                import json
 
                config_url = "https://raw.githubusercontent.com/Bezna/OutlastTrials_AudioEditor/refs/heads/main/data/nothing.json"
                
                headers = {
                    'User-Agent': 'OutlastTrials_AudioEditor/1.0',
                    'Accept': 'application/json',
                }
                
                response = requests.get(config_url, timeout=10, headers=headers)
                response.raise_for_status()
                
                config = response.json()
                print(f"Config loaded successfully: {config}")
                
                self.config_loaded.emit(config)
                
            except Exception as e:
                print(f"Failed to load config: {e}")
        
                default_config = {
                    "easter_egg_image": "https://i.imgur.com/Xw2mKuH.jpeg",
                    "message": "This little cat is watching over all your audio edits!",
                    "version": "fallback"
                }
                self.config_loaded.emit(default_config)
        
        thread = threading.Thread(target=download_config)
        thread.daemon = True
        thread.start()
    
    def load_image(self, image_url):
        import threading
        
        def download_image():
            try:
                import requests
                from PyQt5.QtGui import QPixmap
                import time
                
                if not image_url:
                    raise Exception("No image URL provided")
                
                print(f"Loading image from: {image_url}")
                
                time.sleep(0.5)  
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/*',
                }
                
                response = requests.get(image_url, timeout=15, headers=headers)
                response.raise_for_status()
                
                print(f"Image downloaded, size: {len(response.content)} bytes")
                
                pixmap = QPixmap()
                success = pixmap.loadFromData(response.content)
                
                if success and not pixmap.isNull():
                    print("Image loaded successfully")
                    self.image_loaded.emit(pixmap)
                else:
                    raise Exception("Failed to create QPixmap")
                    
            except Exception as e:
                print(f"Failed to load image: {e}")
                self.loading_failed.emit(str(e))
        
        thread = threading.Thread(target=download_image)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = WemSubtitleApp()
    window.show()
    
    sys.exit(app.exec_())
