import sys
import os
import json
import subprocess
import tempfile
import shutil
import threading
import csv
import traceback
from functools import partial
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
if sys.platform == "win32":
    import subprocess
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    CREATE_NO_WINDOW = 0x08000000
else:
    startupinfo = None
    CREATE_NO_WINDOW = 0
TRANSLATIONS = {
    "en": {
        "app_title": "OutlastTrials AudioEditer",
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
        "filter": "Filter:",
        "sort": "Sort:",
        "all_files": "All Files",
        "with_subtitles": "With Subtitles",
        "without_subtitles": "Without Subtitles",
        "modified": "Modified",
        "modded": "Modded (Audio)",
        "edit_subtitle": "Edit Subtitle",
        "subtitle_preview": "Subtitle Preview",
        "file_info": "File Information",
        "original": "Original",
        "save": "Save",
        "cancel": "Cancel",
        "browse": "Browse...",
        "select_game_path": "Select game root folder",
        "game_path_saved": "Game path saved",
        "mod_deployed": "Mod deployed successfully!",
        "game_launching": "Launching game...",
        "no_game_path": "Please set game path in settings first",
        "conflict_detected": "Subtitle Conflict Detected",
        "conflict_message": "The following keys already have subtitles:\n\n{conflicts}\n\nWhich subtitles would you like to keep?",
        "use_existing": "Keep Existing",
        "use_new": "Use New",
        "merge_all": "Merge All (Keep Existing)"
    },
    "ru": {
        "app_title": "OutlastTrials AudioEditer",
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
        "filter": "Фильтр:",
        "sort": "Сортировка:",
        "all_files": "Все файлы",
        "with_subtitles": "С субтитрами",
        "without_subtitles": "Без субтитров",
        "modified": "Изменённые",
        "modded": "С модиф. аудио",
        "edit_subtitle": "Редактировать субтитр",
        "subtitle_preview": "Предпросмотр субтитров",
        "file_info": "Информация о файле",
        "original": "Оригинал",
        "save": "Сохранить",
        "cancel": "Отмена",
        "browse": "Обзор...",
        "select_game_path": "Выберите корневую папку игры",
        "game_path_saved": "Путь к игре сохранён",
        "mod_deployed": "Мод успешно установлен!",
        "game_launching": "Запуск игры...",
        "no_game_path": "Сначала укажите путь к игре в настройках",
        "conflict_detected": "Обнаружен конфликт субтитров",
        "conflict_message": "Следующие ключи уже имеют субтитры:\n\n{conflicts}\n\nКакие субтитры использовать?",
        "use_existing": "Оставить существующие",
        "use_new": "Использовать новые",
        "merge_all": "Объединить все (оставить существующие)"
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
                
                for row in reader:
                    row_count += 1
                    if len(row) >= 2:
                        key = row[0].strip()
                        value = row[1].strip()

                        if row_count <= 5:
                            DEBUG.log(f"CSV Row {row_count}: key='{key}', value='{value[:50]}...'")

                        if key.startswith('Subtitles/VO_'):

                            key = key[10:]
                            subtitles[key] = value
                            subtitle_count += 1

                            if subtitle_count <= 3:
                                DEBUG.log(f"Found subtitle: {key} = {value[:50]}...")
                                
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
                    if len(row) >= 2 and 'VO_' in row[0]:
                        key = row[0].strip()
                        if key.startswith('Subtitles/VO_'):
                            clean_key = key.replace('Subtitles/', '')
                        elif key.startswith('/VO_'):
                            clean_key = key[1:]
                        elif key.startswith('VO_'):
                            clean_key = key
                        else:
                            continue

                        key_to_original[clean_key] = row[1] if len(row) >= 2 else ""
                        
            DEBUG.log(f"Found {len(key_to_original)} VO entries in original CSV")

            rows = []
            translated_count = 0
            
            for row in original_rows:
                if len(row) >= 2 and 'VO_' in row[0]:
                    key = row[0].strip()

                    clean_key = None
                    if key.startswith('Subtitles/VO_'):
                        clean_key = key.replace('Subtitles/', '')
                    elif key.startswith('/VO_'):
                        clean_key = key[1:]
                    elif key.startswith('VO_'):
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
                if key.startswith('VO_') and key not in key_to_original:
                    if rows and len(rows) > 0:
                        sample_key = None
                        for row in rows:
                            if len(row) >= 1 and 'VO_' in row[0]:
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
                            formatted_key = f"Subtitles/{key}" 
                    else:
                        formatted_key = f"Subtitles/{key}"  

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
                if len(row) >= 3 and 'VO_' in row[0] and row[2]:  # Has translation
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
        # Determine config path
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
            "game_path": ""
        }
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.data.update(loaded_data)
        except Exception as e:
            # Create default config if not exists
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
        
        # Connections
        self.text_edit.textChanged.connect(self.update_char_count)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def update_char_count(self):
        count = len(self.text_edit.toPlainText())
        self.char_count.setText(f"Characters: {count}")
        
    def get_text(self):
        return self.text_edit.toPlainText()

class WemSubtitleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        DEBUG.log("=== WEM Subtitle Studio Starting ===")
        
        self.settings = AppSettings()
        self.translations = TRANSLATIONS
        self.current_lang = self.settings.data["ui_language"]
        
        self.setWindowTitle(self.tr("app_title"))
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        
        # Determine base path (for both dev and compiled versions)
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        DEBUG.log(f"Base path: {self.base_path}")
        
        # Configure paths with new structure
        self.data_path = os.path.join(self.base_path, "data")
        self.libs_path = os.path.join(self.base_path, "libs")
        
        # Tool paths in data folder
        self.unreal_locres_path = os.path.join(self.data_path, "UnrealLocres.exe")
        self.repak_path = os.path.join(self.data_path, "repak.exe")
        self.vgmstream_path = os.path.join(self.data_path, "vgstream", "vgmstream-cli.exe")
        
        # Working directories
        self.soundbanks_path = os.path.join(self.base_path, "SoundbanksInfo.json")
        self.wem_root = os.path.join(self.base_path, "Wems")
        self.mod_p_path = os.path.join(self.base_path, "MOD_P")
        
        # Check for required tools
        self.check_required_files()
        
        DEBUG.log(f"Paths configured:")
        DEBUG.log(f"  data_path: {self.data_path}")
        DEBUG.log(f"  unreal_locres_path: {self.unreal_locres_path}")
        DEBUG.log(f"  repak_path: {self.repak_path}")
        DEBUG.log(f"  vgmstream_path: {self.vgmstream_path}")

        self.locres_manager = UnrealLocresManager(self.unreal_locres_path)
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_files = self.load_all_soundbank_files(self.soundbanks_path)
        self.entries_by_lang = self.group_by_language()

        self.audio_player = AudioPlayer()
        self.temp_wav = None
        self.currently_playing_item = None
        self.is_playing_mod = False
        self.original_duration = 0
        self.mod_duration = 0

        self.populated_tabs = set()
        self.modified_subtitles = set()
        self.current_file_duration = 0

        self.debug_window = None
        
        self.create_ui()
        self.apply_settings()
        self.restore_window_state()

        self.load_subtitles()

        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_subtitles)
        if self.settings.data.get("auto_save", True):
            self.auto_save_timer.start(300000)  # 5 minutes
            
        DEBUG.log("=== WEM Subtitle Studio Started Successfully ===")
    def delete_mod_audio(self, entry, lang):
        """Delete modified audio file"""
        id_ = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{id_}.wem")
        
        if not os.path.exists(mod_wem_path):
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

                widgets = self.tab_widgets[lang]

                widgets["play_mod_btn"].hide()

                widgets["info_labels"]["mod_duration"].setText("N/A")
                widgets["duration_warning"].hide()

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
        """Load subtitles from locres file using UnrealLocres"""
        DEBUG.log("=== Loading Subtitles ===")
        self.subtitles = {}
        self.original_subtitles = {}
        
        subtitle_lang = self.settings.data["subtitle_lang"]
        DEBUG.log(f"Subtitle language: {subtitle_lang}")

        working_locres_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles_working.locres")
        working_locres_path = os.path.abspath(working_locres_path)
        
        original_locres_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles.locres")
        original_locres_path = os.path.abspath(original_locres_path)

        if os.path.exists(original_locres_path):
            DEBUG.log(f"Loading original subtitles from: {original_locres_path}")
            self.original_subtitles = self.locres_manager.export_locres(original_locres_path)
            DEBUG.log(f"Loaded {len(self.original_subtitles)} original subtitles")

        if os.path.exists(working_locres_path):
            DEBUG.log(f"Loading working copy from: {working_locres_path}")
            self.subtitles = self.locres_manager.export_locres(working_locres_path)
            DEBUG.log(f"Loaded {len(self.subtitles)} subtitles from working copy")
        elif os.path.exists(original_locres_path):
            DEBUG.log("Working copy not found, creating from original")
            try:
                shutil.copy2(original_locres_path, working_locres_path)
                self.subtitles = self.locres_manager.export_locres(working_locres_path)
                DEBUG.log(f"Created working copy and loaded {len(self.subtitles)} subtitles")
            except Exception as e:
                DEBUG.log(f"Error creating working copy: {e}", "ERROR")
                self.subtitles = self.original_subtitles.copy()
        else:
            DEBUG.log("No locres files found", "WARNING")

            json_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles.json")
            json_path = os.path.abspath(json_path)
            DEBUG.log(f"Trying JSON fallback at: {json_path}")
            
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.subtitles = data.get("Subtitles", {})
                    self.original_subtitles = self.subtitles.copy()
                    DEBUG.log(f"Loaded {len(self.subtitles)} subtitles from JSON")
                except Exception as e:
                    DEBUG.log(f"Error loading JSON subtitles: {e}", "ERROR")

        self.modified_subtitles.clear()
        for key, value in self.subtitles.items():
            if key in self.original_subtitles and self.original_subtitles[key] != value:
                self.modified_subtitles.add(key)
        
        DEBUG.log(f"Found {len(self.modified_subtitles)} modified subtitles")

        current_lang = self.get_current_language()
        if current_lang and current_lang in self.populated_tabs:
            DEBUG.log(f"Refreshing tab: {current_lang}")
            self.populate_tree(current_lang)
            
        DEBUG.log("=== Subtitle Loading Complete ===")

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
                languages = languages  # Keep as is
                
        if "SFX" not in languages:
            self.entries_by_lang["SFX"] = []
            languages.append("SFX")
            
        for lang in sorted(languages):
            self.create_language_tab(lang)

        self.create_converter_tab()

        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)

        if self.entries_by_lang:
            first_lang = sorted(self.entries_by_lang.keys())[0]
            self.populate_tree(first_lang)
            self.populated_tabs.add(first_lang)

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
        sort_combo.addItems(["Name (A-Z)", "Name (Z-A)", "ID ↑", "ID ↓", "Recent First"])
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
        tree.setHeaderLabels(["Name", "ID", "Subtitle", "Status"])
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
        
        play_mod_btn = QtWidgets.QPushButton("▶ MOD")
        play_mod_btn.setMaximumWidth(60)
        play_mod_btn.setToolTip("Play modified audio if available")
        play_mod_btn.clicked.connect(lambda: self.play_current(play_mod=True))
        play_mod_btn.hide()  
        
        stop_btn = QtWidgets.QPushButton("■")
        stop_btn.setMaximumWidth(40)
        stop_btn.clicked.connect(self.stop_audio)
        

        time_label = QtWidgets.QLabel("00:00 / 00:00")
        time_label.setAlignment(QtCore.Qt.AlignCenter)
        

        duration_warning = QtWidgets.QLabel()
        duration_warning.setStyleSheet("color: red; font-weight: bold;")
        duration_warning.hide()
        
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(play_mod_btn)
        controls_layout.addWidget(stop_btn)
        controls_layout.addWidget(time_label)
        controls_layout.addWidget(duration_warning)
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
        info_layout = QtWidgets.QFormLayout(info_group)
        
        info_labels = {
            "id": QtWidgets.QLabel(),
            "name": QtWidgets.QLabel(),
            "path": QtWidgets.QLabel(),
            "source": QtWidgets.QLabel(),
            "duration": QtWidgets.QLabel(),
            "mod_duration": QtWidgets.QLabel()
        }
        
        info_layout.addRow("ID:", info_labels["id"])
        info_layout.addRow("Name:", info_labels["name"]) 
        info_layout.addRow("Path:", info_labels["path"])
        info_layout.addRow("Source:", info_labels["source"])
        info_layout.addRow("Original Duration:", info_labels["duration"])
        info_layout.addRow("Mod Duration:", info_labels["mod_duration"])
        
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
            "details_panel": details_panel,
            "audio_progress": audio_progress,
            "time_label": time_label,
            "play_btn": play_btn,
            "play_mod_btn": play_mod_btn,
            "stop_btn": stop_btn,
            "duration_warning": duration_warning
        }
        
        self.tabs.addTab(tab, f"{lang} ({len(self.entries_by_lang.get(lang, []))})")

    def create_converter_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        header = QtWidgets.QLabel("WEM File Converter & Subtitle Exporter")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        card = QtWidgets.QGroupBox("Instructions")
        card_layout = QtWidgets.QVBoxLayout(card)
        
        instructions = QtWidgets.QLabel(
            "WEM Converter:\n"
            "1. Select the root WWISE folder containing .cache/Windows/SFX subfolders\n"
            "2. Files will be renamed to their ID from SoundbanksInfo.json\n"
            "3. Converted files will be moved to MOD_P/OPP/Content/WwiseAudio/Windows/English(US)\n\n"
            "THIS WILL CHANGE ONLY ENGLISH AUDIO\n\n"
            
            "Subtitle Exporter:\n"
            "1. Modified subtitles will be exported to MOD_P/OPP/Content/Localization/OPP_Subtitles\n"
            "2. Each language will have its own folder (ru-RU, en, fr-FR, etc.)\n"
            "3. Use 'Export Subtitles for Game' to import new subtitles\n\n\n"
            
            "Конвертер WEM:\n"
            "1. Выберите корневую папку WWISE, содержащую подпапки .cache/Windows/SFX\n"
            "2. Файлы будут переименованы в соответствии с их ID из SoundbanksInfo.json\n"
            "3. Конвертированные файлы будут перемещены в MOD_P/OPP/Content/WwiseAudio/Windows/English(US)\n\n"
            "ИЗМЕНЯЕТСЯ ТОЛЬКО АНГЛИЙСКОЕ АУДИО\n\n"
            
            "Экспортер субтитров:\n"
            "1. Изменённые субтитры будут экспортированы в MOD_P/OPP/Content/Localization/OPP_Subtitles\n"
            "2. Для каждого языка будет создана отдельная папка (ru-RU, en, fr-FR и т.д.)\n"
            "3. Используйте 'Экспорт субтитров для игры' для импорта новых субтитр"
            
            
        )
        instructions.setWordWrap(True)
        card_layout.addWidget(instructions)
        
        layout.addWidget(card)
        
        path_group = QtWidgets.QGroupBox("Source Path")
        path_layout = QtWidgets.QHBoxLayout(path_group)
        
        self.wwise_path_edit = QtWidgets.QLineEdit()
        self.wwise_path_edit.setPlaceholderText("Select WWISE folder...")
        
        browse_btn = ModernButton(self.tr("browse"), primary=True)
        browse_btn.clicked.connect(self.select_wwise_folder)
        
        path_layout.addWidget(self.wwise_path_edit)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_widget)
        
        self.process_btn = ModernButton("Process WEM Files", primary=True)
        self.process_btn.clicked.connect(self.process_wem_files)
        
        self.export_subtitles_btn = ModernButton("Export Subtitles for Game", primary=True)
        self.export_subtitles_btn.clicked.connect(self.export_subtitles_for_game)
        
        self.open_target_btn = ModernButton("Open Target Folder")
        self.open_target_btn.clicked.connect(self.open_target_folder)
        
        btn_layout.addWidget(self.process_btn)
        btn_layout.addWidget(self.export_subtitles_btn)
        btn_layout.addWidget(self.open_target_btn)
        btn_layout.addStretch()
        
        layout.addWidget(btn_widget)
        
        self.converter_status = QtWidgets.QTextEdit()
        self.converter_status.setReadOnly(True)
        layout.addWidget(self.converter_status)
        
        self.tabs.addTab(tab, "Converter")

    def load_all_soundbank_files(self, path):
        DEBUG.log(f"Loading soundbank files from: {path}")
        all_files = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            soundbanks_info = data.get("SoundBanksInfo", {})
            
            # StreamedFiles
            streamed_files = soundbanks_info.get("StreamedFiles", [])
            for file_entry in streamed_files:
                file_entry["Source"] = "StreamedFiles"
            all_files.extend(streamed_files)
            DEBUG.log(f"Loaded {len(streamed_files)} StreamedFiles")
            
            # MediaFilesNotInAnyBank
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
        """Get the current language from the active tab"""
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
        filter_type = widgets["filter_combo"].currentIndex()
        sort_type = widgets["sort_combo"].currentIndex()
        search_text = self.global_search.text().lower()
        
        tree.clear()
        
        filtered_entries = []
        for entry in self.entries_by_lang.get(lang, []):
            shortname = entry.get("ShortName", "")
            key = os.path.splitext(shortname)[0]
            subtitle = self.subtitles.get(key, "")
            
            mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{entry.get('Id', '')}.wem")
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
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{entry.get('Id', '')}.wem")
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
        

        subtitle_count = sum(1 for entry in filtered_entries if self.subtitles.get(os.path.splitext(entry.get("ShortName", ""))[0], ""))
        widgets["stats_label"].setText(f"Showing {len(filtered_entries)} of {len(self.entries_by_lang.get(lang, []))} files | Subtitles: {subtitle_count}")
    def show_documentation(self):
        """Show comprehensive documentation"""
        doc_dialog = QtWidgets.QDialog(self)
        doc_dialog.setWindowTitle("Documentation")
        doc_dialog.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(doc_dialog)
        

        tabs = QtWidgets.QTabWidget()
        

        getting_started = QtWidgets.QTextBrowser()
        getting_started.setOpenExternalLinks(True)
        getting_started.setHtml("""
        <h2>Getting Started</h2>
        <h3>1. Initial Setup</h3>
        <p>Before using OutlastTrials AudioEditer, ensure you have:</p>
        <ul>
            <li><b>SoundbanksInfo.json</b> - Contains metadata for all audio files</li>
            <li><b>Wems folder</b> - Contains WEM audio files organized by language</li>
            <li><b>Localization folder</b> - Contains subtitle files (.locres)</li>
            <li><b>UnrealLocres.exe</b> - For reading/writing .locres files</li>
            <li><b>vgmstream-cli.exe</b> - For audio conversion</li>
            <li><b>repak.exe</b> - For creating game mods</li>
        </ul>
        
        <h3>2. Workflow Overview</h3>
        <ol>
            <li><b>Load Files:</b> The app automatically loads all audio files from SoundbanksInfo.json</li>
            <li><b>Edit Subtitles:</b> Double-click or press F2 to edit subtitles</li>
            <li><b>Preview Audio:</b> Select a file and click Play to hear the audio</li>
            <li><b>Save Changes:</b> Press Ctrl+S to save subtitle changes</li>
            <li><b>Export Mod:</b> Use Tools → Compile Mod to create a game mod</li>
        </ol>
        
        """)
        tabs.addTab(getting_started, "Getting Started")
        
        features = QtWidgets.QTextBrowser()
        features.setHtml("""
        <h2>Features Guide</h2>
        
        <h3>Audio Playback</h3>
        <ul>
            <li><b>Play Original:</b> Plays the original game audio file</li>
            <li><b>Play MOD:</b> Plays modified audio if available</li>
            <li><b>Duration Warning:</b> Shows when mod audio exceeds original duration</li>
        </ul>
        
        <h3>Subtitle Editing</h3>
        <ul>
            <li><b>Edit Dialog:</b> Shows current and original subtitle side-by-side</li>
            <li><b>Character Count:</b> Displays real-time character count</li>
            <li><b>Revert Option:</b> Quickly restore original subtitle</li>
        </ul>
        
        <h3>Filtering & Search</h3>
        <ul>
            <li><b>All Files:</b> Show all audio files</li>
            <li><b>With Subtitles:</b> Show only files that have subtitles</li>
            <li><b>Without Subtitles:</b> Show files missing subtitles</li>
            <li><b>Modified:</b> Show only edited subtitles</li>
            <li><b>Modded:</b> Show files with custom audio</li>
        </ul>
        
        <h3>Import/Export</h3>
        <ul>
            <li><b>Import Custom Subtitles:</b> Import from other .locres files with conflict resolution</li>
            <li><b>Export for Game:</b> Creates proper mod structure for the game</li>
        </ul>
        """)
        tabs.addTab(features, "Features")
        
        # File Structure tab
        file_structure = QtWidgets.QTextBrowser()
        file_structure.setHtml("""
        <h2>File Structure</h2>
        <pre>
        Project Root/
        ├── SoundbanksInfo.json       # Audio metadata
        ├── Wems/                     # Original WEM files
        │   ├── English(US)/
        │   ├── French(France)/
        │   └── ...
        ├── Localization/             # Subtitle files
        │   ├── en/
        │   │   ├── OPP_Subtitles.locres         # Original
        │   │   └── OPP_Subtitles_working.locres # Working copy
        │   └── ...
        ├── MOD_P/                    # Mod output folder
        │   └── OPP/
        │       └── Content/
        │           ├── WwiseAudio/   # Modified audio
        │           └── Localization/ # Modified subtitles
        ├── UnrealLocres.exe          # Locres tool
        ├── vgmstream-cli.exe         # Audio converter
        └── repak.exe                 # Mod packer
        </pre>
        
        <h3>Important Files</h3>
        <ul>
            <li><b>*.locres</b> - Unreal Engine localization files containing subtitles</li>
            <li><b>*.wem</b> - Wwise audio files used by the game</li>
            <li><b>*.pak</b> - Packaged mod files for the game</li>
        </ul>
        """)
        tabs.addTab(file_structure, "File Structure")
        
        layout.addWidget(tabs)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(doc_dialog.close)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignRight)
        
        doc_dialog.exec_()

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """
        <h2>Keyboard Shortcuts</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
        <tr style="background-color: #f0f0f0;">
            <th>Action</th>
            <th>Shortcut</th>
            <th>Description</th>
        </tr>
        <tr>
            <td><b>Edit Subtitle</b></td>
            <td>F2</td>
            <td>Edit selected subtitle</td>
        </tr>
        <tr>
            <td><b>Save Subtitles</b></td>
            <td>Ctrl+S</td>
            <td>Save all subtitle changes</td>
        </tr>
        <tr>
            <td><b>Export Audio</b></td>
            <td>Ctrl+E</td>
            <td>Export selected audio as WAV</td>
        </tr>
        <tr>
            <td><b>Revert to Original</b></td>
            <td>Ctrl+R</td>
            <td>Revert selected subtitle to original</td>
        </tr>
        <tr>
            <td><b>Deploy & Run</b></td>
            <td>F5</td>
            <td>Deploy mod and launch game</td>
        </tr>
        <tr>
            <td><b>Debug Console</b></td>
            <td>Ctrl+D</td>
            <td>Show debug console</td>
        </tr>
        <tr>
            <td><b>Settings</b></td>
            <td>Ctrl+,</td>
            <td>Open settings dialog</td>
        </tr>
        <tr>
            <td><b>Documentation</b></td>
            <td>F1</td>
            <td>Show documentation</td>
        </tr>
        <tr>
            <td><b>Exit</b></td>
            <td>Ctrl+Q</td>
            <td>Close application</td>
        </tr>
        </table>
        
        <h3>Mouse Actions</h3>
        <ul>
            <li><b>Double-click subtitle:</b> Edit subtitle</li>
            <li><b>Double-click file:</b> Play audio</li>
            <li><b>Right-click:</b> Show context menu</li>
        </ul>
        """
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(shortcuts_text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    # def show_tutorial(self):
    #     """Show quick tutorial"""
    #     tutorial_dialog = QtWidgets.QDialog(self)
    #     tutorial_dialog.setWindowTitle("Quick Tutorial")
    #     tutorial_dialog.setMinimumSize(700, 500)
        
    #     layout = QtWidgets.QVBoxLayout(tutorial_dialog)
        
    #     # Create wizard-style pages
    #     stack = QtWidgets.QStackedWidget()
        
    #     # Page 1
    #     page1 = QtWidgets.QWidget()
    #     page1_layout = QtWidgets.QVBoxLayout(page1)
    #     page1_content = QtWidgets.QLabel("""
    #     <h2>Welcome to WEM Subtitle Studio!</h2>
    #     <p style="font-size: 14px;">This tutorial will guide you through the basic workflow.</p>
        
    #     <h3>Step 1: Understanding the Interface</h3>
    #     <p>The main window consists of:</p>
    #     <ul>
    #         <li><b>Language Tabs:</b> Each tab shows audio files for that language</li>
    #         <li><b>File Tree:</b> Organized list of audio files</li>
    #         <li><b>Details Panel:</b> Shows subtitle and file information</li>
    #         <li><b>Audio Player:</b> Preview audio files</li>
    #     </ul>
        
    #     <p><i>Click Next to continue...</i></p>
    #     """)
    #     page1_content.setWordWrap(True)
    #     page1_layout.addWidget(page1_content)
    #     stack.addWidget(page1)
        
    #     # Page 2
    #     page2 = QtWidgets.QWidget()
    #     page2_layout = QtWidgets.QVBoxLayout(page2)
    #     page2_content = QtWidgets.QLabel("""
    #     <h3>Step 2: Editing Subtitles</h3>
    #     <ol>
    #         <li><b>Select a file</b> from the tree (look for VO_ files)</li>
    #         <li><b>Press F2</b> or double-click the subtitle column</li>
    #         <li><b>Edit the text</b> in the dialog</li>
    #         <li><b>Click Save</b> to apply changes</li>
    #     </ol>
        
    #     <p><b>Tips:</b></p>
    #     <ul>
    #         <li>Modified subtitles show a ✓ checkmark</li>
    #         <li>Original subtitle is displayed for reference</li>
    #         <li>Use Ctrl+R to revert to original</li>
    #     </ul>
        
    #     <p><i>Your changes are saved to a working copy, preserving the original files.</i></p>
    #     """)
    #     page2_content.setWordWrap(True)
    #     page2_layout.addWidget(page2_content)
    #     stack.addWidget(page2)
        
    #     # Page 3
    #     page3 = QtWidgets.QWidget()
    #     page3_layout = QtWidgets.QVBoxLayout(page3)
    #     page3_content = QtWidgets.QLabel("""
    #     <h3>Step 3: Creating a Game Mod</h3>
    #     <ol>
    #         <li><b>Save your subtitles</b> (Ctrl+S)</li>
    #         <li>Go to <b>Tools → Export Subtitles for Game</b></li>
    #         <li>Use <b>Tools → Compile Mod</b> to create the .pak file</li>
    #         <li>Use <b>Tools → Deploy & Run</b> (F5) to test in-game</li>
    #     </ol>
        
    #     <p><b>The mod will include:</b></p>
    #     <ul>
    #         <li>All modified subtitles</li>
    #         <li>Any custom audio files in MOD_P folder</li>
    #     </ul>
        
    #     <p><b>Ready to start!</b> Check the Documentation (F1) for more details.</p>
    #     """)
    #     page3_content.setWordWrap(True)
    #     page3_layout.addWidget(page3_content)
    #     stack.addWidget(page3)
        
    #     layout.addWidget(stack)
        
    #     # Navigation buttons
    #     nav_widget = QtWidgets.QWidget()
    #     nav_layout = QtWidgets.QHBoxLayout(nav_widget)
        
    #     prev_btn = QtWidgets.QPushButton("← Previous")
    #     next_btn = QtWidgets.QPushButton("Next →")
    #     close_btn = QtWidgets.QPushButton("Close")
        
    #     prev_btn.clicked.connect(lambda: stack.setCurrentIndex(max(0, stack.currentIndex() - 1)))
    #     next_btn.clicked.connect(lambda: stack.setCurrentIndex(min(stack.count() - 1, stack.currentIndex() + 1)))
    #     close_btn.clicked.connect(tutorial_dialog.close)
        
    #     nav_layout.addWidget(prev_btn)
    #     nav_layout.addStretch()
    #     nav_layout.addWidget(close_btn)
    #     nav_layout.addWidget(next_btn)
        
    #     layout.addWidget(nav_widget)
        
    #     # Update button states
    #     def update_nav_buttons():
    #         prev_btn.setEnabled(stack.currentIndex() > 0)
    #         next_btn.setEnabled(stack.currentIndex() < stack.count() - 1)
            
    #     stack.currentChanged.connect(update_nav_buttons)
    #     update_nav_buttons()
        
    #     tutorial_dialog.exec_()

    # def show_tips(self):
    #     """Show tips and tricks"""
    #     tips_text = """
    #     <h2>Tips & Tricks</h2>
        
    #     <h3>🚀 Productivity Tips</h3>
    #     <ul>
    #         <li><b>Multi-select:</b> Hold Ctrl to select multiple files for batch export</li>
    #         <li><b>Quick search:</b> Start typing to filter files instantly</li>
    #         <li><b>Tab navigation:</b> Use Ctrl+Tab to switch between languages</li>
    #         <li><b>Auto-save:</b> Enable in settings for peace of mind</li>
    #     </ul>
        
    #     <h3>🎯 Best Practices</h3>
    #     <ul>
    #         <li><b>Test audio duration:</b> Always check if mod audio fits original timing</li>
    #         <li><b>Backup regularly:</b> Export subtitles to JSON for safekeeping</li>
    #         <li><b>Use working copies:</b> Never modify original .locres files directly</li>
    #         <li><b>Check context:</b> Play audio before editing to understand context</li>
    #     </ul>
        
    #     <h3>⚡ Advanced Features</h3>
    #     <ul>
    #         <li><b>Debug Console:</b> Press Ctrl+D to see detailed operations</li>
    #         <li><b>Custom imports:</b> Import subtitles from other .locres files</li>
    #         <li><b>Conflict resolution:</b> Smart handling when importing duplicates</li>
    #         <li><b>Mod structure:</b> Converter tab helps organize custom audio</li>
    #     </ul>
        
    #     <h3>🔧 Troubleshooting</h3>
    #     <ul>
    #         <li><b>Audio won't play:</b> Check if vgmstream-cli.exe is present</li>
    #         <li><b>Can't save subtitles:</b> Ensure UnrealLocres.exe is in the folder</li>
    #         <li><b>Mod not working:</b> Verify game path in settings</li>
    #         <li><b>Missing subtitles:</b> Check subtitle language matches game</li>
    #     </ul>
    #     """
        
    #     msg = QtWidgets.QMessageBox()
    #     msg.setWindowTitle("Tips & Tricks")
    #     msg.setTextFormat(QtCore.Qt.RichText)
    #     msg.setText(tips_text)
    #     msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    #     msg.exec_()

    def check_updates(self):
        """Check for updates"""
        QtWidgets.QMessageBox.information(
            self, "Check for Updates", 
            "You are running OutlastTrials AudioEditer v1.0 \n\n"
            "This is the latest version.\n\n"
            "Check GitHub for updates:\n"
            "https://github.com/Bezna/OutlastTrials_AudioEditer"
        )

    def report_bug(self):
        """Show bug report dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Report Bug")
        dialog.setMinimumSize(500, 400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        info_label = QtWidgets.QLabel(
            "Found a bug? Please provide details below.\n"
            "Debug logs will be automatically included."
        )
        layout.addWidget(info_label)
        
        # Bug description
        desc_label = QtWidgets.QLabel("Description:")
        layout.addWidget(desc_label)
        
        desc_text = QtWidgets.QTextEdit()
        desc_text.setPlaceholderText(
            "Please describe:\n"
            "1. What you were trying to do\n"
            "2. What happened instead\n"
            "3. Steps to reproduce the issue"
        )
        layout.addWidget(desc_text)
        
        # Email
        email_label = QtWidgets.QLabel("Email (optional):")
        layout.addWidget(email_label)
        
        email_edit = QtWidgets.QLineEdit()
        email_edit.setPlaceholderText("your@email.com")
        layout.addWidget(email_edit)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        copy_btn = QtWidgets.QPushButton("Copy Report to Clipboard")
        send_btn = QtWidgets.QPushButton("Open GitHub Issues")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        
        def copy_report():
            report = f"""
    BUG REPORT - WEM Subtitle Studio v2.4 DEBUG
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
            webbrowser.open("https://github.com/Bezna/OutlastTrials_AudioEditer/issues")
        
        copy_btn.clicked.connect(copy_report)
        send_btn.clicked.connect(open_github)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

        
    def on_selection_changed(self, lang):
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
        
        DEBUG.log(f"Selected: {shortname} (key: {key})")
        DEBUG.log(f"Subtitle: {subtitle[:50] if subtitle else 'None'}...")
        
        widgets["subtitle_text"].setPlainText(subtitle)
        

        if original_subtitle and original_subtitle != subtitle:
            widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
            widgets["original_subtitle_label"].show()
        else:
            widgets["original_subtitle_label"].hide()
        
        widgets["info_labels"]["id"].setText(entry.get("Id", ""))
        widgets["info_labels"]["name"].setText(shortname)
        widgets["info_labels"]["path"].setText(entry.get("Path", ""))
        widgets["info_labels"]["source"].setText(entry.get("Source", ""))
        widgets["info_labels"]["duration"].setText("Loading...")
        widgets["info_labels"]["mod_duration"].setText("Loading...")
        widgets["duration_warning"].hide()
        

        mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{entry.get('Id', '')}.wem")
        if os.path.exists(mod_wem_path):
            widgets["play_mod_btn"].show()
        else:
            widgets["play_mod_btn"].hide()
        

        self.get_file_durations(entry.get("Id", ""), lang, widgets)

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
            

        mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{file_id}.wem")
        self.mod_duration = 0
        
        if os.path.exists(mod_wem_path):
            duration = self.get_wem_duration(mod_wem_path)
            if duration > 0:
                self.mod_duration = duration
                minutes = int(duration // 60000)
                seconds = (duration % 60000) / 1000.0
                widgets["info_labels"]["mod_duration"].setText(f"{minutes:02d}:{seconds:05.2f}")
                
                if self.original_duration > 0 and self.mod_duration > self.original_duration:
                    widgets["duration_warning"].setText("⚠ MOD DURATION EXCEEDS ORIGINAL!")
                    widgets["duration_warning"].show()
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

                for line in result.stdout.split('\n'):
                    if "stream total samples:" in line:
                        samples = int(line.split(':')[1].strip().split()[0])

                        duration_ms = int((samples / 48000) * 1000)
                        return duration_ms
                        
        except Exception as e:
            DEBUG.log(f"Error getting duration: {e}", "ERROR")
            
        return 0

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
            # Try to play mod file
            wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{id_}.wem")
            if not os.path.exists(wem_path):
                self.status_bar.showMessage("Mod audio not found", 3000)
                return
            self.is_playing_mod = True
        else:
            # Play original file
            wem_path = os.path.join(self.wem_root, current_lang, f"{id_}.wem")
            if not os.path.exists(wem_path):
                self.status_bar.showMessage(f"File not found: {wem_path}", 3000)
                return
            self.is_playing_mod = False
            

        source_type = "MOD" if play_mod else "Original"
        self.status_bar.showMessage(f"Converting {source_type} to WAV...")
        QtWidgets.QApplication.processEvents()
        
        temp_wav = os.path.join(tempfile.gettempdir(), f"wem_temp_{id_}_{source_type}.wav")
        
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
            

            item.setText(2, new_subtitle)
            current_status = item.text(3).replace("✓", "") 
            if key in self.modified_subtitles:
                item.setText(3, "✓" + current_status)
            else:
                item.setText(3, current_status)
            

            widgets["subtitle_text"].setPlainText(new_subtitle)
            if original_subtitle and original_subtitle != new_subtitle:
                widgets["original_subtitle_label"].setText(f"{self.tr('original')}: {original_subtitle}")
                widgets["original_subtitle_label"].show()
            else:
                widgets["original_subtitle_label"].hide()
            
            self.status_bar.showMessage("Subtitle updated", 2000)
            self.update_status()

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
            QtWidgets.QMessageBox.warning(self, "Error", self.tr("no_game_path"))
            return
            
        mod_file = f"{self.mod_p_path}.pak"
        
        if not os.path.exists(mod_file):
            reply = QtWidgets.QMessageBox.question(
                self, "Compile Mod", 
                "Mod file not found. Compile it first?",
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
                    QtWidgets.QMessageBox.warning(self, "Error", "Mod compilation failed")
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
        """Export modified subtitles to game mod structure"""
        DEBUG.log("=== Export Subtitles for Game ===")
        
        if not self.modified_subtitles:
            QtWidgets.QMessageBox.information(self, "No Changes", "No modified subtitles to export")
            return
            
        progress = ProgressDialog(self, "Exporting Subtitles for Game")
        progress.show()
        
        try:

            base_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization", "OPP_Subtitles")
            os.makedirs(base_dir, exist_ok=True)
            DEBUG.log(f"Created base directory: {base_dir}")
            

            current_lang = self.settings.data["subtitle_lang"]
            lang_dir = os.path.join(base_dir, current_lang)
            os.makedirs(lang_dir, exist_ok=True)
            DEBUG.log(f"Created language directory: {lang_dir}")
            

            locres_path = os.path.join(lang_dir, "OPP_Subtitles.locres")
            progress.set_progress(50, f"Writing {current_lang}/OPP_Subtitles.locres...")

            original_locres = os.path.join(".", "Localization", current_lang, "OPP_Subtitles.locres")
            if os.path.exists(original_locres):
                DEBUG.log(f"Copying original locres from: {original_locres}")
                shutil.copy2(original_locres, locres_path)

                DEBUG.log(f"Updating locres with {len(self.modified_subtitles)} modified subtitles")
                success = self.locres_manager.import_locres(locres_path, self.subtitles)
                
                if success:
                    progress.append_details(f"✓ Created {locres_path}")
                    progress.set_progress(100, "Export complete!")
                    
                    QtWidgets.QMessageBox.information(
                        self, "Success", 
                        f"Subtitles exported successfully!\n\n"
                        f"Location: {base_dir}\n\n"
                        f"Modified subtitles: {len(self.modified_subtitles)}"
                    )
                else:
                    raise Exception("Failed to import subtitles to locres file")
            else:
                raise Exception(f"Original locres file not found: {original_locres}")
                
        except Exception as e:
            DEBUG.log(f"Export error: {str(e)}", "ERROR")
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
        msg.setWindowTitle("Export Audio")
        msg.setText("Which version would you like to export?")
        
        original_btn = msg.addButton("Original", QtWidgets.QMessageBox.ActionRole)
        mod_btn = None
        
        mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{id_}.wem")
        if os.path.exists(mod_wem_path):
            mod_btn = msg.addButton("Mod", QtWidgets.QMessageBox.ActionRole)
            
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
            self, "Save as WAV", f"{base_name}{suffix}.wav", "WAV Files (*.wav)"
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
        
        self.export_action = file_menu.addAction(self.tr("export_subtitles"))
        self.export_action.triggered.connect(self.export_subtitles)
        
        self.import_action = file_menu.addAction(self.tr("import_subtitles"))
        self.import_action.triggered.connect(self.import_subtitles)
        
        self.import_custom_action = file_menu.addAction(self.tr("import_custom_subtitles"))
        self.import_custom_action.triggered.connect(self.import_custom_subtitles)
        
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

        self.documentation_action = help_menu.addAction("📖 Documentation")
        self.documentation_action.setShortcut("F1")
        self.documentation_action.triggered.connect(self.show_documentation)

        self.shortcuts_action = help_menu.addAction("⌨ Keyboard Shortcuts")
        self.shortcuts_action.triggered.connect(self.show_shortcuts)

        # help_menu.addSeparator()

        # self.tutorial_action = help_menu.addAction("🎓 Quick Tutorial")
        # self.tutorial_action.triggered.connect(self.show_tutorial)

        # self.tips_action = help_menu.addAction("💡 Tips & Tricks")
        # self.tips_action.triggered.connect(self.show_tips)

        help_menu.addSeparator()

        self.check_updates_action = help_menu.addAction("🔄 Check for Updates")
        self.check_updates_action.triggered.connect(self.check_updates)

        self.report_bug_action = help_menu.addAction("🐛 Report Bug")
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
        
        self.edit_subtitle_action = toolbar.addAction("✏ Edit")
        self.edit_subtitle_action.setShortcut("F2")
        self.edit_subtitle_action.triggered.connect(self.edit_current_subtitle)
        
        self.save_wav_action = toolbar.addAction("💾 Export")
        self.save_wav_action.setShortcut("Ctrl+E")
        self.save_wav_action.triggered.connect(self.save_current_wav)
        self.delete_mod_action = toolbar.addAction("🗑 Delete Mod AUDIO")
        self.delete_mod_action.setToolTip("Delete modified audio for selected file")
        self.delete_mod_action.triggered.connect(self.delete_current_mod_audio)
        toolbar.addSeparator()
        
        self.expand_all_action = toolbar.addAction("📂 Expand All")
        self.expand_all_action.triggered.connect(self.expand_all_trees)
        
        self.collapse_all_action = toolbar.addAction("📁 Collapse All")
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
            play_action = menu.addAction("▶ Play Original")
            play_action.triggered.connect(self.play_current)
            
        
            entry = items[0].data(0, QtCore.Qt.UserRole)
            if entry:
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)", f"{entry.get('Id', '')}.wem")
                if os.path.exists(mod_wem_path):
                    play_mod_action = menu.addAction("▶ Play Mod")
                    play_mod_action.triggered.connect(lambda: self.play_current(play_mod=True))

                    menu.addSeparator()
                    delete_mod_action = menu.addAction("🗑 Delete Mod Audio")
                    delete_mod_action.triggered.connect(lambda: self.delete_mod_audio(entry, lang))

            
            edit_action = menu.addAction(f"✏ {self.tr('edit_subtitle')}")
            edit_action.triggered.connect(self.edit_current_subtitle)

            shortname = entry.get("ShortName", "")
            key = os.path.splitext(shortname)[0]
            if key in self.modified_subtitles:
                revert_action = menu.addAction(f"↩ {self.tr('revert_to_original')}")
                revert_action.triggered.connect(self.revert_subtitle)
            
            menu.addSeparator()
            
            export_action = menu.addAction("💾 Export as WAV")
            export_action.triggered.connect(self.save_current_wav)
            
        menu.exec_(tree.viewport().mapToGlobal(pos))

    def batch_export_wav(self, items, lang):

        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            return
            
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Batch Export")
        msg.setText("Which version would you like to export?")
        msg.addButton("Original", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        msg.exec_()
        
        if msg.result() != 0:
            return
            
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not directory:
            return
            
        progress = ProgressDialog(self, f"Exporting {len(file_items)} files...")
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
                self, "Export Complete", 
                f"Exported {len(file_items) - len(errors)} files successfully.\n"
                f"{len(errors)} errors occurred."
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
            QtWidgets.QMessageBox.warning(self, "Error", "repak.exe not found!")
            return
            
        progress = ProgressDialog(self, "Compiling Mod")
        progress.show()
        progress.set_progress(50, "Running repak...")
        
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
                QtWidgets.QMessageBox.information(self, "Success", "Mod compiled successfully!")
            else:
                progress.append_details(result.stderr)
                QtWidgets.QMessageBox.warning(self, "Error", "Compilation failed!")
                
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
        target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
        if os.path.exists(target_dir):
            os.startfile(target_dir)
        else:

            loc_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization", "OPP_Subtitles")
            if os.path.exists(loc_dir):
                os.startfile(loc_dir)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Target folder not found!")

    def process_wem_files(self):
        wwise_root = self.wwise_path_edit.text()
        if not wwise_root or not os.path.exists(wwise_root):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid WWISE folder path!")
            return
            
        progress = ProgressDialog(self, "Processing WEM Files")
        progress.show()

        sfx_paths = []
        for root, dirs, files in os.walk(wwise_root):
            if root.endswith(".cache\\Windows\\SFX"):
                sfx_paths.append(root)
                
        if not sfx_paths:
            progress.close()
            QtWidgets.QMessageBox.warning(self, "Error", "No .cache/Windows/SFX/ folders found!")
            return
            
        target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
        os.makedirs(target_dir, exist_ok=True)

        name_to_id = {}
        for entry in self.entries_by_lang.get("English(US)", []):
            base_shortname = os.path.splitext(entry.get("ShortName", ""))[0]
            name_to_id[base_shortname] = entry.get("Id", "")
            
        processed = 0
        total_files = sum(len([f for f in os.listdir(p) if f.endswith(".wem")]) for p in sfx_paths)
        
        self.converter_status.clear()
        
        for sfx_path in sfx_paths:
            for filename in os.listdir(sfx_path):
                if filename.endswith(".wem"):
                    src_path = os.path.join(sfx_path, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    if "_" in base_name:
                        base_name = base_name.rsplit("_", 1)[0]
                        
                    id_ = name_to_id.get(base_name)
                    dest_filename = f"{id_}.wem" if id_ else filename
                    dest_path = os.path.join(target_dir, dest_filename)
                    
                    try:
                        shutil.move(src_path, dest_path)
                        processed += 1
                        
                        progress.set_progress(
                            int((processed / total_files) * 100),
                            f"Processing {filename}..."
                        )
                        
                        self.converter_status.append(f"✓ {filename} → {dest_filename}")
                        QtWidgets.QApplication.processEvents()
                        
                    except Exception as e:
                        self.converter_status.append(f"✗ {filename}: {str(e)}")
                        
        progress.close()
        self.converter_status.append(f"\nProcessed {processed} files successfully")

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

    def show_settings_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("settings"))
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QFormLayout(dialog)
        

        lang_combo = QtWidgets.QComboBox()
        lang_combo.addItem("English", "en")
        lang_combo.addItem("Русский", "ru")
        lang_combo.setCurrentIndex(0 if self.settings.data["ui_language"] == "en" else 1)
        

        theme_combo = QtWidgets.QComboBox()
        theme_combo.addItem("Light", "light")
        theme_combo.addItem("Dark", "dark")
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

        auto_save_check = QtWidgets.QCheckBox("Auto-save subtitles every 5 minutes")
        auto_save_check.setChecked(self.settings.data.get("auto_save", True))
        
        layout.addRow("Interface Language (APP WILL CLOSE):", lang_combo)
        layout.addRow("Theme:", theme_combo)
        layout.addRow("Subtitle Language:", subtitle_combo)
        layout.addRow("Game Path:", game_path_widget)
        layout.addRow(auto_save_check)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addRow(btn_box)
        
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:

            old_lang = self.settings.data["subtitle_lang"]
            old_ui_lang = self.settings.data["ui_language"]
            
            self.settings.data["ui_language"] = lang_combo.currentData()
            self.settings.data["theme"] = theme_combo.currentData()
            self.settings.data["subtitle_lang"] = subtitle_combo.currentText()
            self.settings.data["game_path"] = game_path_edit.text()
            self.settings.data["auto_save"] = auto_save_check.isChecked()
            self.settings.save()

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
        """Update all UI elements with new language"""
        self.setWindowTitle(self.tr("app_title"))

        self.menuBar().clear()
        self.create_menu_bar()
        
        for i, (lang, widgets) in enumerate(self.tab_widgets.items()):
            if i < self.tabs.count() - 1:  # Skip converter tab
                # Update filter combo
                widgets["filter_combo"].clear()
                widgets["filter_combo"].addItems([
                    self.tr("all_files"), 
                    self.tr("with_subtitles"), 
                    self.tr("without_subtitles"), 
                    self.tr("modified"),
                    self.tr("modded")
                ])
                

                subtitle_group = widgets["subtitle_text"].parent().parent()
                if subtitle_group:
                    subtitle_group.setTitle(self.tr("subtitle_preview"))
                    
                info_group = widgets["info_labels"]["id"].parent().parent()
                if info_group:
                    info_group.setTitle(self.tr("file_info"))

    def update_status(self):
        total_files = len(self.all_files)
        total_subtitles = len(self.subtitles)
        modified = len(self.modified_subtitles)
        
        status_text = f"Files: {total_files} | Subtitles: {total_subtitles}"
        if modified > 0:
            status_text += f" | Modified: {modified}"
            
        self.status_bar.showMessage(status_text)

    def save_subtitles_to_file(self):
        """Save subtitles to working copy of locres file"""
        DEBUG.log("=== Saving Subtitles ===")
        
        try:
            subtitle_lang = self.settings.data["subtitle_lang"]
            working_locres_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles_working.locres")
            working_locres_path = os.path.abspath(working_locres_path)
            
            DEBUG.log(f"Saving to working copy: {working_locres_path}")

            os.makedirs(os.path.dirname(working_locres_path), exist_ok=True)

            if not os.path.exists(working_locres_path):
                original_locres_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles.locres")
                if os.path.exists(original_locres_path):
                    DEBUG.log("Creating working copy from original")
                    shutil.copy2(original_locres_path, working_locres_path)
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "No original locres file found to create working copy")
                    return

            DEBUG.log(f"Saving {len(self.modified_subtitles)} modified subtitles")
            success = self.locres_manager.import_locres(working_locres_path, self.subtitles)
            
            if success:

                json_path = os.path.join(".", "Localization", subtitle_lang, "OPP_Subtitles_working.json")
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({"Subtitles": self.subtitles}, f, ensure_ascii=False, indent=2)
                
                DEBUG.log(f"Saved JSON backup to: {json_path}")
                
                self.modified_subtitles.clear()

                for key, value in self.subtitles.items():
                    if key in self.original_subtitles and self.original_subtitles[key] != value:
                        self.modified_subtitles.add(key)
                
                self.update_status()
                self.status_bar.showMessage("Subtitles saved to working copy", 3000)

                for lang in self.populated_tabs:
                    self.populate_tree(lang)
            else:
                QtWidgets.QMessageBox.warning(self, "Save Error", "Failed to save subtitles to locres file")
                
        except Exception as e:
            DEBUG.log(f"Save error: {str(e)}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Save Error", str(e))
            
        DEBUG.log("=== Save Complete ===")

    def auto_save_subtitles(self):
        if self.modified_subtitles:
            DEBUG.log("Auto-saving subtitles...")
            self.save_subtitles_to_file()

    def show_about(self):
        """Show about dialog with animations"""
        about_dialog = QtWidgets.QDialog(self)
        about_dialog.setWindowTitle("About WEM Subtitle Studio")
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
        
        title_label = QtWidgets.QLabel("OutlastTrials AudioEditer")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        
        version_label = QtWidgets.QLabel("Version 1.0 Release")
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
        about_content.setHtml("""
        <div style="padding: 20px;">
        <p style="font-size: 14px; line-height: 1.6;">
        A tool for managing WEM audio files and game subtitles for Outlast Trials, 
        designed for modders and localization teams.
        </p>
        
        <h3>Key Features</h3>
        <ul style="line-height: 1.8;">
            <li>🎵 <b>Audio Management:</b> Play, convert, and organize WEM files</li>
            <li>📝 <b>Subtitle Editing:</b> Easy editing</li>
            <li>📦 <b>Mod Creation:</b> One-click mod compilation and deployment</li>
            <li>🌍 <b>Multi-language:</b> Support for 14+ languages</li>
            <li>🎨 <b>Modern UI:</b> Clean interface with dark/light themes</li>
        </ul>
        
        <h3>Technology Stack</h3>
        <p>Built with Python 3 and PyQt5, utilizing:</p>
        <ul>
            <li>UnrealLocres for .locres file handling</li>
            <li>vgmstream for audio conversion</li>
            <li>repak for mod packaging</li>
        </ul>
        </div>
        """)
        about_tabs.addTab(about_content, "About")

        credits_content = QtWidgets.QTextBrowser()
        credits_content.setHtml("""
        <div style="padding: 20px;">
        <h3>Development Team</h3>
        <p><b>Lead Developer:</b> Bezna</p>
        
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
        about_tabs.addTab(credits_content, "Credits")
        
        # License tab
        license_content = QtWidgets.QTextBrowser()
        license_content.setHtml("""
        <div style="padding: 20px;">
        <h3>License Agreement</h3>
        <p>Copyright (c) 2024 WEM Subtitle Studio</p>
        
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
        about_tabs.addTab(license_content, "License")
        
        layout.addWidget(about_tabs)
        
        # Footer with links
        footer_widget = QtWidgets.QWidget()
        footer_layout = QtWidgets.QHBoxLayout(footer_widget)
        
        github_btn = QtWidgets.QPushButton("GitHub")
        discord_btn = QtWidgets.QPushButton("Discord")
        donate_btn = QtWidgets.QPushButton("Donate")
        
        github_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "GitHub", "https://github.com/Bezna/OutlastTrials_AudioEditer"))
        discord_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Discord", "My Discord: Bezna"))
        donate_btn.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Donate", "No donation link available yet"))
        
        footer_layout.addWidget(github_btn)
        footer_layout.addWidget(discord_btn)
        footer_layout.addWidget(donate_btn)
        footer_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(about_dialog.close)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer_widget)
        
        about_dialog.exec_()


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
        
        # Save window state
        self.settings.data["window_geometry"] = self.saveGeometry().toHex().data().decode()
        self.settings.save()
        
        # Check for unsaved changes
        if self.modified_subtitles:
            reply = QtWidgets.QMessageBox.question(
                self, "Save Changes?",
                "You have unsaved subtitle changes. Save before closing?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QtWidgets.QMessageBox.Yes:
                self.save_subtitles_to_file()
                
        # Clean up
        self.stop_audio()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = WemSubtitleApp()
    window.show()
    
    sys.exit(app.exec_())
