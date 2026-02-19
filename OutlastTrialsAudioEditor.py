import sys
import os
import json
import subprocess
import tempfile
import shutil
import threading
import csv
import traceback
import time
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
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import numpy as np
    import scipy.io.wavfile as wavfile
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    text = str(ImportError)
    MATPLOTLIB_AVAILABLE = False
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
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
current_version = "v1.1.2"

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
        "wav_to_wem_converter": "Audio to WEM Converter",
        "conversion_mode": "Conversion Mode (Only Size Matching Mode)",
        "strict_mode": "Strict Mode",
        "adaptive_mode": "Adaptive Mode",
        "strict_mode_desc": "❌ Fails if too large",
        "adaptive_mode_desc": "✅ Auto-adjusts quality",
        "path_configuration": "Path Configuration",
        "wwise_path": "Wwise:",
        "project_path": "Project:",
        "wav_path": "Audio:",
        "files_for_conversion": "Files for Conversion",
        "add_all_wav": "Add All Audio Files",
        "convert": "Convert",
        "files_ready": "Files ready:",
        "wav_file": "Audio File",
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
        "converter_instructions": "Audio to WEM Converter:\n1) Set Wwise path 2) Choose temp project folder 3) Select Audio folder 4) Add files 5) Convert",
        "converter_instructions2": "WEM Converter:\n1) Set Wwise project path 2) Convert to mod",
        
        # === ПУТИ И ПЛЕЙСХОЛДЕРЫ ===
        "wwise_path_placeholder": "Wwise installation path... (Example: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "New/Old Project path... (Example: D:/ExampleProjects/MyNewProject) P.S. Can be empty",
        "wav_folder_placeholder": "Audio files folder...",
        
        # === ПОИСК И ОБРАБОТКА ===
        "select_wav_folder": "Please select Audio folder first!",
        "wems_folder_not_found": "Wems folder not found",
        "no_wav_files": "No Audio files found in folder!",
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
        "wem_processor_recommendation": "Use 'Audio to WEM' for beginners.",
        
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
        "modern_ui": "🎨 <b>UI:</b> Clean interface with dark/light themes",
        "technology_stack": "Technology Stack",
        "built_with": "Built with Python 3 and PyQt5, utilizing:",
        "unreal_locres_tool": "UnrealLocres for .locres file handling",
        "vgmstream_tool": "vgmstream for audio conversion",
        "repak_tool": "repak for mod packaging",
        "ffmpeg_tool": "FFmpeg for audio processing",
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
        "copyright_notice": "Copyright (c) 2026 OutlastTrials AudioEditor",
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
        "mouse_right_click": "<b>Right-click:</b> Show context menu",
        "verify_mod_integrity": "Verify Mod Integrity",
        "rebuild_bnk_index": "Rebuild Mod BNK Index",
        "rebuild_bnk_tooltip": "Forcefully syncs all BNK files with the actual WEM files in your mod.",
        "verifying_mod_integrity": "Verifying Mod Integrity...",
        "bnk_verification_complete": "Verification Complete",
        "bnk_no_issues_found": "All modified audio files are consistent with their BNK entries. No issues found!",
        "bnk_issues_found_title": "Mod Integrity Issues Found",
        "bnk_issues_found_text": "Found {count} issues in your mod.\n\nThese problems can cause sounds to not play correctly in the game.\n\nDo you want to automatically fix these entries?",
        "fix_all_btn": "Fix All",
        "bnk_size_mismatch": "Size Mismatch",
        "bnk_entry_missing": "BNK Entry Missing",
        "bnk_report_size": "Type: {type} in {bnk_name}\n  Sound: {short_name} (ID: {source_id})\n  - BNK Size: {bnk_size} bytes\n  - WEM Size: {wem_size} bytes\n\n",
        "bnk_report_missing": "Type: {type}\n  Sound: {short_name} (ID: {source_id})\n  - A .wem file exists, but no corresponding entry was found in any modified .bnk file.\n\n",
        "fixing_mod_issues": "Fixing Mod Issues...",
        "fix_complete_no_issues": "No automatically fixable issues were found (e.g., 'BNK Entry Missing').",
        "fix_complete_title": "Fix Complete",
        "fix_complete_message": "Fixed {count} size mismatch issues.",
        "fix_complete_with_errors": "Fixed {fixed} size mismatch issues.\nFailed to fix {errors} entries. See debug console for details.",
        "verification_error": "Verification Error",
        "verification_error_message": "An error occurred during verification:\n\n{error}",
        "rebuild_bnk_confirm_title": "Rebuild BNK Index",
        "rebuild_bnk_confirm_text": "This will scan all modified audio (.wem) files and forcefully update the size records in your mod's .bnk files to match.\n\nThis is useful for fixing inconsistencies after manually adding, deleting, or editing WEM files.\n\nDo you want to proceed?",
        "rebuilding_mod_bnk": "Rebuilding Mod BNK Index...",
        "rebuild_complete_title": "Rebuild Complete",
        "rebuild_complete_message": "Rebuild complete!\n\n✅ Re-created {created} BNK file(s) in your mod from originals.\n🔄 Updated {updated} entries to match your WEM files.\n⚙️ Applied {reverted} custom 'In-Game Effects' settings.",
        "profiles": "Profiles",
        "profile_manager_tooltip": "Open the Mod Profile Manager",
        "edit_profile": "Edit Mod Profile",
        "create_profile": "Create New Mod Profile",
        "profile_name": "Profile Name:",
        "author": "Author:",
        "version": "Version:",
        "icon_png": "Icon (PNG):",
        "no_icon_selected": "No icon selected.",
        "select_icon": "Select Icon",
        "png_images": "PNG Images",
        "validation_error": "Validation Error",
        "profile_name_empty": "Profile Name cannot be empty.",
        "profile_manager_title": "Mod Profile Manager",
        "create_new_profile_btn": "➕ Create New...",
        "add_existing_profile_btn": "📁 Add Existing...",
        "remove_from_list_btn": "➖ Remove From List",
        "select_a_profile": "Select a profile",
        "author_label": "<b>Author:</b>",
        "version_label": "<b>Version:</b>",
        "no_description": "<i>No description.</i>",
        "edit_details_btn": "⚙️ Edit Details...",
        "active_profile_btn": "✓ Active",
        "activate_profile_btn": "Activate Profile",
        "error_reading_profile": "<i style='color:red;'>Could not read profile.json</i>",
        "error_author": "<i style='color:red;'>Error</i>",
        "select_folder_for_profile": "Select a Folder to Create the New Profile In",
        "profile_exists_error": "A profile with this name already exists.",
        "create_profile_error": "Could not create profile: {e}",
        "select_existing_profile": "Select Existing Profile Folder",
        "invalid_profile_folder": "The selected folder does not contain a required '{folder}' subfolder.",
        "profile_already_added": "A profile with this name has already been added.",
        "remove_profile_title": "Remove Profile",
        "remove_profile_text": "Are you sure you want to remove the profile '{name}' from the list?\n\nThis will NOT delete the files on your disk.",
        "profile_activated_title": "Profile Activated",
        "profile_activated_text": "Profile '{name}' is now active.",
        "no_active_profile_title": "No Active Profile",
        "no_active_profile_text": "No mod profile is currently active. Please create or activate a profile first.",
        "rebuild_complete_message_details": "Rebuild complete!\n\n"
                                  "✅ Re-created {created} BNK file(s) in your mod from originals.\n"
                                  "🔄 Updated {updated} entries to match your WEM files.\n"
                                  "⚙️ Applied {reverted} custom 'In-Game Effects' settings.",
        "select_version_title": "Select Version",
        "adjust_volume_for": "Adjust volume for: {filename}\n\nWhich version would you like to adjust?",
        "batch_adjust_volume_for": "Batch adjust volume for {count} files\n\nWhich version would you like to adjust?",
        "no_language_selected": "No Language Selected",
        "select_language_tab_first": "Please select a language tab first.",
        "no_files_selected": "No Files Selected",
        "select_files_for_volume": "Please select one or more audio files to adjust volume.",
        "quick_load_audio_title": "🎵 Quick Load Custom Audio...",
        "quick_load_audio_tooltip": "Replace this audio with your own file (any format)",
        "restore_from_backup_title": "🔄 Restore from Backup",
        "restore_from_backup_tooltip": "Restore previous version of modified audio",
        "adjust_original_volume_title": "🔊 Adjust Original Volume...",
        "trim_original_audio_title": "✂️ Trim Original Audio...",
        "adjust_mod_volume_title": "🔊 Adjust Mod Volume...",
        "trim_mod_audio_title": "✂️ Trim Mod Audio...",
        "toggle_ingame_effects_title": "✨ Toggle In-Game Effects",
        "marking_menu_title": "🖍 Marking",
        "set_color_menu_title": "🎨 Set Color",
        "set_tag_menu_title": "🏷 Set Tag",
        "color_green": "Green",
        "color_yellow": "Yellow",
        "color_red": "Red",
        "color_blue": "Blue",
        "color_none": "None",
        "tag_important": "Important",
        "tag_check": "Check",
        "tag_done": "Done",
        "tag_review": "Review",
        "tag_none": "None",
        "tag_custom": "Custom...",
        "custom_tag_title": "Custom Tag",
        "custom_tag_prompt": "Enter custom tag:",
        "select_folder_to_open_title": "Select Folder to Open",
        "which_folder_to_open": "Which folder would you like to open?",
        "voice_files_folder": "🎙 Voice Files\n{path}",
        "sfx_files_folder": "🔊 SFX Files\n{path}",
        "subtitles_folder": "📝 Subtitles\n{path}",
        "no_target_folders_found": "No target folders found!",
        "quick_load_mode_label": "Choose conversion mode for Quick Load Custom Audio:",
        "quick_load_strict": "Strict Mode - Fail if too large",
        "quick_load_adaptive": "Adaptive Mode - Auto-adjust quality",
        "audio_files_dialog_title": "Audio Files",
        "volume_editor_title": "Volume Editor - {shortname}",
        "volume_deps_missing": "⚠️ Volume editing requires NumPy and SciPy libraries.\n\nPlease install them using:\npip install numpy scipy",
        "audio_analysis_group": "Audio Analysis",
        "analyzing": "Analyzing...",
        "current_rms": "Current RMS:",
        "current_peak": "Current Peak:",
        "duration_label": "Duration:",
        "recommended_max": "Recommended max:",
        "no_limit": "No limit",
        "volume_control_group": "Volume Control",
        "volume_label_simple": "Volume:",
        "quick_presets": "Quick presets:",
        "waiting_for_analysis": "Waiting for analysis...",
        "preview_rms_peak": "Preview: RMS {new_rms:.1f}%, Peak {new_peak:.1f}%",
        "preview_clipping": " ⚠️ CLIPPING ({over:.1f}% over)",
        "preview_near_clipping": " ⚠️ Near clipping",
        "apply_volume_change_btn": "Apply Volume Change",
        "volume_no_change_msg": "Volume is set to 100% (no change).",
        "config_required": "Configuration Required",
        "wwise_config_required_msg": "Wwise is not configured.\n\nPlease check:\n1. Go to Converter tab and configure Wwise paths\n2. Make sure Wwise project exists\n3. Try converting at least one file in Converter tab first",
        "status_preparing": "Preparing...",
        "status_using_backup": "Using backup as source...",
        "status_backup_created": "Created backup and using as source...",
        "status_using_original": "Using original as source...",
        "status_converting_to_wav": "Converting WEM to WAV...",
        "status_adjusting_volume": "Adjusting volume...",
        "status_preparing_for_wem": "Preparing for WEM conversion...",
        "status_converting_to_wem": "Converting to WEM...",
        "status_deploying_to_mod": "Deploying to MOD_P...",
        "status_complete": "Complete!",
        "volume_change_success_msg": "Volume successfully changed to {volume}%\nActual change: {actual_change:.0f}%\n{clipping_info}\n{source_info}\n{backup_info}",
        "clipping_info_text": "\nClipping: {percent:.2f}% of samples",
        "backup_available_info": "\n\n💾 Backup available - you can restore the previous version if needed.",
        "source_info_backup": "\n📁 Source: Backup (preserving original quality)",
        "source_info_mod_backup_created": "\n📁 Source: Current mod (backup created)",
        "source_info_original": "\n📁 Source: Original file",
        "wem_conversion_failed_msg": "WEM conversion failed!\n\nPossible solutions:\n1. Check Wwise configuration in Converter tab\n2. Try converting a regular WAV file first to test setup\n3. Ensure Wwise project has correct audio settings\n4. Check if target file size is achievable\n\nTechnical error: {error_message}",
        "wwise_not_configured_msg": "Wwise is not properly configured!\n\nPlease:\n1. Go to Converter tab\n2. Set valid Wwise installation path\n3. Set project path\n4. Try converting at least one file to verify setup\n\nThen try volume adjustment again.",
        "required_file_not_found_msg": "Required file not found!\n\n{error_message}\n\nPlease check that:\n- The audio file exists\n- File permissions are correct\n- No other program is using the file",
        "volume_change_failed_title": "Volume change failed",
        
        # === РЕДАКТОР ГРОМКОСТИ (ПАКЕТНЫЙ) ===
        "batch_volume_editor_title": "Batch Volume Editor - {count} files",
        "wwise_configured_auto": "✅ Wwise configured automatically",
        "wwise_not_configured_warning": "⚠️ Wwise not configured - please configure in Converter tab first",
        "backups_stored_in": "Backups are stored in: {path}",
        "volume_control_all_files_group": "Volume Control (Applied to All Files)",
        "files_to_process_group": "Files to Process",
        "file_header": "File",
        "language_header": "Language",
        "current_rms_header": "Current RMS",
        "current_peak_header": "Current Peak",
        "new_preview_header": "New Preview",
        "status_header": "Status",
        "apply_to_all_btn": "Apply to All Files",
        "status_skipped_no_analysis": "✗ Skipped (no analysis)",
        "batch_process_complete_title": "Batch Processing Complete",
        "batch_process_complete_msg": "Batch volume change complete!\n\nVolume changed to: {volume}%\nSuccessful: {successful}\nFailed: {failed}",
        "batch_process_error_title": "Batch Processing Error",
        
        # === КОНСОЛЬ ОТЛАДКИ ===
        "debug_console_title": "Debug Console",
        "auto_scroll_check": "Auto-scroll",
        "save_log_btn": "Save Log",
        "save_debug_log_title": "Save Debug Log",
        "log_files_filter": "Log Files (*.log)",
        
        # === DRAG & DROP АУДИО ===
        "invalid_file_title": "Invalid File",
        "audio_only_drop_msg": "Only audio files are supported for drag & drop.",
        "drop_audio_title": "Drop Audio",
        "drop_on_file_msg": "Please drop onto a specific audio file.",
        "replace_audio_title": "Replace Audio",
        "replace_audio_confirm_msg": "Replace audio for:\n{shortname}\n\nwith file:\n{filename}?",
        
        # === ПОИСК ===
        "search_placeholder": "Search...",
        
        # === ЗАГРУЗЧИК СУБТИТРОВ ===
        "processing_file_status": "Processing {filename}...",
        "processing_additional_subs_status": "Processing additional subtitles...",
        "loaded_subs_from_files_status": "Loaded {count} subtitles from {processed_files} files",
        
        # === РЕДАКТОР СУБТИТРОВ (ГЛОБАЛЬНЫЙ) ===
        "subtitle_editor_tab_title": "Localization Editor",
        "subtitle_editor_header": "Localization Editor",
        "subtitle_editor_desc": "Edit localization directly. Use the global search bar above to filter results.",
        "without_audio_filter": "Without audio",
        "without_audio_filter_tooltip": "Show only subtitles that don't have corresponding audio files",
        "modified_only_filter": "Modified only",
        "modified_only_filter_tooltip": "Show only subtitles that have been modified",
        "with_audio_only_filter": "With audio only",
        "with_audio_only_filter_tooltip": "Show only subtitles that have corresponding audio files",
        "refresh_btn": "🔄 Refresh",
        "refresh_btn_tooltip": "Refresh subtitle data from files",
        "key_header": "Key",
        "original_header": "Original",
        "current_header": "Current",
        "audio_header": "Audio",
        "edit_selected_btn": "✏ Edit Selected",
        "save_all_changes_btn": "💾 Save All Changes",
        "subtitle_save_success": "All subtitle changes have been saved!",
        "go_to_audio_action": "🔊 Go to Audio File",
        "audio_not_found_for_key": "Could not find audio file for subtitle key: {key}",
        "tab_not_found_for_lang": "Could not find tab for language: {lang}",
        
        # === ОБРАБОТЧИК WEM (СТАРЫЙ) ===
        "wem_processor_tab_title": "WEM Processor (Old)",
        "process_wem_files_btn": "Process WEM Files",
        "open_target_folder_btn": "Open Target Folder",
        
        # === ОЧИСТКА СУБТИТРОВ ===
        "no_working_files_found": "No working subtitle files (_working.locres) found in Localization.",
        "cleanup_complete_msg": "Deleted {deleted} working subtitle files.",
        "cleanup_complete_with_errors_msg": "Deleted {deleted} working subtitle files.\nErrors: {errors}",
        
        # === РАЗНОЕ UI ===
        "quick_load_settings_group": "Quick Load Settings",
        "conversion_method_group": "Conversion Method",
        "bnk_overwrite_radio": "BNK Overwrite (Recommended)",
        "bnk_overwrite_tooltip": "Converts at max quality and overwrites file size in the .bnk file.",
        "adaptive_size_matching_radio": "Adaptive Size Matching",
        "adaptive_size_matching_tooltip": "Adjusts audio quality to match original WEM file size.",
        "rescan_orphans_action": "Rescan Orphaned Files",
        "rescan_orphans_tooltip": "Forces a new scan of the Wems folder to find files not in SoundbanksInfo",
        "in_progress_msg": "Already processing. Please wait.",
        "add_single_file_title": "Select Audio File",
        "audio_files_filter": "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus *.webm);;All Files (*.*)",
        "file_added_status": "Added: {filename}",
        "file_not_added_status": "File not added: {filename}",
        "error_adding_file_msg": "Error adding file:\n\n{error}",
        "update_file_q_title": "File Already Added",
        "update_file_q_msg": "File '{filename}' is already in the conversion list.\n\nDo you want to update its settings?",
        "update_btn": "Update",
        "skip_btn": "Skip",
        "duplicate_target_q_title": "Duplicate Target WEM",
        "duplicate_target_q_msg": "Target WEM '{file_id}.wem' is already assigned to:\n\nCurrent: {existing_name}\nNew: {new_name}\n\nDo you want to replace it?",
        "replace_btn": "Replace",
        "replace_all_btn": "Replace All",
        "skip_all_btn": "Skip All",
        "tags_group_filter": "--- Tags ---",
        "with_tag_filter": "With Tag: {tag}",
        "numeric_id_files_group": "Numeric ID Files",
        "voice_group_name": "VO (Voice)",
        "bnk_size_mismatch_tooltip": "BNK expects {expected_size:,} bytes, but file is {actual_size:,} bytes.\nClick to update the BNK record.",
        "bnk_size_missing_wem_tooltip": "BNK record was modified, but the WEM file is missing.\nClick to revert the BNK record to its original state.",
        "bnk_size_ok_tooltip": "OK: Actual file size matches the BNK record.",
        "bnk_size_mismatch_btn": "Mismatch! Click to fix",
        "bnk_size_missing_wem_btn": "Missing WEM! Click to revert",
        "bnk_fix_success_msg": "BNK file size has been successfully updated!",
        "bnk_fix_not_found_msg": "Could not find an entry for ID {file_id} in any modded BNK file to fix.",
        "bnk_fix_error_msg": "An unexpected error occurred while fixing the BNK file:\n{error}",
        "bnk_revert_success_msg": "BNK record reverted successfully to its original state.",
        "bnk_revert_fail_msg": "Failed to revert BNK record. The entry might already be correct.",
        "bnk_revert_error_msg": "An unexpected error occurred while reverting the BNK record:\n{error}",
        "select_folder_for_mods_title": "Select a Folder to Store Your Mods",
        "welcome_title": "Welcome!",
        "first_time_setup_msg": "It looks like this is your first time running the editor.\n\nPlease select a root folder where you want to store your mod profiles (e.g., 'My Documents\\OutlastTrialsMods').\n\nA 'Default' profile will be created for you there.",
        "setup_required_title": "Setup Required",
        "setup_required_msg": "A folder for mods is required to continue. The application will now close.",
        "setup_complete_title": "Setup Complete",
        "setup_complete_msg": "Your 'Default' profile has been created in:\n{mods_root}",
        "setup_failed_title": "Setup Failed",
        "setup_failed_msg": "An error occurred: {e}",
        "legacy_migration_title": "New Mod Profile System",
        "legacy_migration_msg": "This version uses a new system to manage multiple mods.\n\nYour existing 'MOD_P' folder can be migrated into a new profile named 'Default'.\n\nPlease select a root folder where you want to store your mod profiles (e.g., 'My Documents\\OutlastTrialsMods').",
        "migration_complete_title": "Migration Complete",
        "migration_complete_msg": "Your mod has been successfully migrated to the 'Default' profile inside:\n{mods_root}",
        "migration_failed_title": "Migration Failed",
        "migration_failed_msg": "An error occurred: {e}",
        "scan_progress_title": "Scanning for Additional Audio Files",
        "scan_progress_msg": "Preparing to scan...",
        "scan_complete_status": "Scan complete. Found and cached {count} additional audio files.",
        "no_new_files_found_status": "No new audio files found during scan.",
        "volume_adjust_tooltip_no_selection": "Adjust audio volume (select files first)",
        "volume_adjust_tooltip_single": "Adjust volume for: {filename}",
        "volume_adjust_tooltip_batch": "Batch adjust volume for {count} files",
        "easter_egg_title": "You found cat!",
        "easter_egg_loading": "Loading cat...",
        "easter_egg_message": "This little cat is watching over all your audio edits!",
        "crash_log_saved_msg": "\n\nCrash log saved to: {log_path}",
        "crash_log_failed_msg": "\n\nFailed to save crash log: {error}",
        "app_error_title": "Application Error",
        "app_error_msg": "The application has encountered an error and will close.",
        "app_error_info": "Please report this bug with the details below.",
        "copy_error_btn": "Copy Error to Clipboard",
        "stats_label_text": "Showing {filtered_count} of {total_count} files | Subtitles: {subtitle_count}",
        "shortcut_play_original_action": "Play Original Audio",
        "shortcut_play_original_desc": "Plays the original version of the selected audio file.",
        "shortcut_play_mod_action": "Play Mod Audio",
        "shortcut_play_mod_desc": "Plays the modified version of the selected audio file.",
        "shortcut_delete_mod_action": "Delete Mod Audio",
        "shortcut_delete_mod_desc": "Deletes the modified audio for the selected file(s).",
        "volume_toolbar_btn": "🔊 Volume",
        "show_scanned_files_check": "Show Scanned Files",
        "show_scanned_files_tooltip": "Show/hide audio files found by scanning the 'Wems' folder that are not in the main database.",
        "add_file_btn": "Add File...",

        # === ИНФО-ПАНЕЛЬ ===
        "bnk_size_label": "BNK Size:",
        "in_game_effects_label": "In Game Effects:",
        "last_modified_label": "Last Modified:",

        # === РЕДАКТОР ОБРЕЗКИ (TRIM) ===
        "trim_editor_title": "Audio Trimmer - {shortname}",
        "trim_deps_missing": "Trimming is not available.\n\nPlease ensure the following libraries are installed:\n'pip install numpy scipy matplotlib'",
        "trimming_audio_for": "Trimming audio for: {shortname}",
        "version_mod": " (MOD version)",
        "version_original": " (Original version)",
        "zoom_label": "Zoom:",
        "start_time_label": "Start Time:",
        "end_time_label": "End Time:",
        "new_duration_label": "New Duration:",
        "new_duration_format": "{duration_sec:.3f} s ({duration_ms} ms)",
        "play_pause_btn": "▶️ Play/Pause",
        "preview_trim_btn": "🎬 Preview Trim",
        "stop_btn": "⏹️ Stop",
        "apply_trim_btn": "Apply Trim",
        "preparing_audio_failed": "Failed to prepare audio: {e}",
        "trimming_with_ffmpeg": "Trimming audio with FFmpeg...",
        "trim_success_msg": "Audio trimmed and deployed successfully!",
        "trim_failed_title": "Trimming failed",
        "compiling_step_1": "Summoning code spirits...",
        "compiling_step_2": "Herding rogue pixels...",
        "compiling_step_3": "Teaching WEMs to sing in harmony...",
        "compiling_step_4": "Polishing the mod until it shines...",
        "compiling_step_5": "Waking up the game engine...",
        "compiling_step_6": "Hiding secrets from data miners...",
        "compiling_step_7": "Finalizing... (Promise!)",
        "splash_loading_app": "Loading application, please wait...",
        "splash_init_ui": "Initializing UI...",
        "splash_loading_profiles": "Loading profiles...",
        "app_already_running_title": "Application Already Running",
        "app_already_running_msg": "OutlastTrials AudioEditor is already running.",
        "project_statistics_title": "Project Statistics",
        "mod_profile_label": "Mod Profile:",
        "general_stats_group": "General Statistics",
        "total_audio_files": "Total Modified Audio Files:",
        "total_subtitle_files": "Total Modified Subtitle Files:",
        "total_mod_size": "Total Mod Size (unpacked):",
        "subtitle_stats_group": "Subtitle Statistics",
        "modified_subtitle_entries": "Modified Subtitle Entries:",
        "new_subtitle_entries": "New Subtitle Entries:",
        "total_languages_affected": "Languages Affected:",
        "modified_files_group": "List of Modified Files",
        "copy_list_btn": "Copy List",
        "list_copied_msg": "List of modified files copied to clipboard!",
        "no_profile_active_for_stats": "No active profile. Statistics are unavailable.",
        "calculating_stats": "Calculating...",
        "recalculate_btn": "🔄 Recalculate",
        "resource_updater_tab": "Resource Updater",
        "updater_header": "Update Game Resources",
        "updater_description": "Extract the latest audio (.wem) and localization (.locres) files directly from the game's .pak archives. This ensures you are always working with the most up-to-date files.",
        "select_pak_file_group": "Select Game Pak File",
        "pak_file_path_label": "Path to .pak file:",
        "pak_file_path_placeholder": "e.g., C:/.../The Outlast Trials/OPP/Content/Paks/OPP-WindowsClient.pak",
        "select_resources_group": "Select Resources to Update",
        "update_audio_check": "Update Audio Files (Wems)",
        "update_localization_check": "Update Localization Files",
        "start_update_btn": "Start Update",
        "update_process_group": "Update Process",
        "update_log_ready": "Ready to start the update process.",
        "update_confirm_title": "Confirm Resource Update",
        "update_confirm_msg": "This will replace your current local '{resource_folder}' folder(s) with files extracted from the game.\n\n- Your current files will be deleted.\n- This action cannot be undone.\n\nAre you sure you want to continue?",
        "pak_file_not_selected": "Please select a valid game .pak file first.",
        "no_resources_selected": "Please select at least one resource type to update (Audio or Localization).",
        "update_process_started": "Update process started...",
        "unpacking_files_from": "Unpacking files from {pak_name}...",
        "unpacking_path": "Unpacking '{path_to_unpack}'...",
        "unpack_failed": "Repak failed to unpack files. See details below.",
        "clearing_old_files": "Clearing old files in '{folder_name}'...",
        "moving_new_files": "Moving new files to '{folder_name}'...",
        "organizing_sfx": "Organizing SFX files...",
        "update_complete_title": "Update Complete",
        "update_complete_msg": "The following resources have been successfully updated:\n\n{updated_resources}\n\nIt is recommended to restart the application to apply all changes.",
        "update_failed_title": "Update Failed",
        "update_failed_msg": "The update process failed. Please check the log for details.",
        "restart_recommended": "Restart Recommended",
        "settings_saved_title": "Settings Saved",
        "close_required_message": "Language settings have changed.\n\nThe application must be closed for the changes to take full effect.",
        "close_now_button": "Close Now",
        "update_warning_title": "Update in Progress",
        "update_warning_msg": "The resource update process has started.\n\nPlease do not use or close the application until it is complete. This may take several minutes depending on your system.",
        "update_fun_status_1": "Brewing coffee for Coyle...",
        "update_fun_status_2": "Reticulating splines...",
        "update_fun_status_3": "Asking the FBI for file locations...",
        "update_fun_status_4": "Synchronizing with Murkoff's servers...",
        "update_fun_status_5": "Definitely not installing spyware...",
        "update_fun_status_6": "Unpacking screams and whispers...",
        "update_fun_status_7": "Recalibrating the Morphogenic Engine...",
        "update_step_unpacking": "Unpacking files from game archive...",
        "update_step_clearing": "Clearing old local files...",
        "update_step_moving": "Moving new files into place...",
        "update_step_organizing": "Organizing new files...",
        "update_unpacking_long_wait": "Unpacking process started. This may take several minutes depending on your system...",
        "update_cancelled_by_user": "Update cancelled by user",
        "update_step_finishing": "Finishing up...",
        "update_in_progress_title": "Update in Progress",
        "confirm_exit_during_update_message": "The resource update process is still running.\n\nAre you sure you want to exit? This will cancel the update.",
        "update_rescanning_orphans": "Update complete. Now rescanning the Wems folder for changes...",
        "initial_setup_title": "Initial Setup",
        "wems_folder_missing_message": "The 'Wems' folder with game audio files was not found.\n\nThis is required for the application to function correctly.\n\nWould you like to go to the 'Resource Updater' tab to extract them from the game now?",
        "localization_folder_missing_message": "The 'Localization' folder with game subtitle files was not found.\n\nThis is required for subtitle editing.\n\nWould you like to go to the 'Resource Updater' tab to extract them from the game now?",
        "go_to_updater_button": "Go to Updater",
        "import_mod_title": "Import Mod",
        "select_pak_to_import": "Select .pak file to import",
        "pak_files": "PAK files",
        "enter_profile_name_for_pak": "Enter a name for the new profile (derived from .pak name):",
        "importing_mod_progress": "Importing Mod...",
        "unpacking_pak_file": "Unpacking .pak file...",
        "creating_profile_structure": "Creating profile structure...",
        "moving_mod_files": "Moving mod files...",
        "cleaning_up": "Cleaning up...",
        "import_successful_title": "Import Successful",
        "import_successful_message": "Mod '{pak_name}' has been successfully imported as the '{profile_name}' profile.",
        "import_failed_title": "Import Failed",
        "import_mod_from_pak": "Import Mod from .pak...",
        "wems_folder_loose_files_title": "Misplaced Audio Files Found",
        "wems_folder_loose_files_message": "Found {count} audio files (.wem/.bnk) in the main 'Wems' folder.",
        "wems_folder_loose_files_details": "These files should typically be inside the 'Wems/SFX' subfolder. Moving them helps keep your project organized and ensures they are found correctly.\n\nDo you want to move them to the 'Wems/SFX' folder now?",
        "move_all_files_btn": "Move All Files",
        "ignore_btn": "Ignore",
        "move_complete_title": "Move Complete",
        "move_complete_message": "Successfully moved {count} file(s) to the 'Wems/SFX' folder.",
        "move_complete_errors": "Failed to move {count} file(s):\n{errors}",
        "soundbanksinfo_missing_title": "Database File Missing",
        "soundbanksinfo_missing_message": "The core audio database file (SoundbanksInfo.json) was not found.",
        "soundbanksinfo_missing_details": "This file is required to identify most audio files. Would you like to go to the 'Resource Updater' tab to extract the latest game files now?",
        "go_to_updater_btn": "Go to Updater",
        "later_btn": "Later",
        "critical_file_missing_title": "Critical File Missing",
        "critical_file_missing_message": "SoundbanksInfo.json is missing and the Resource Updater tab could not be found.",
        "move_complete_restart_note": "\n\nIt is recommended to restart the application for the changes to take full effect.",
        "outdated_mod_structure_title": "Outdated Mod Structure",
        "outdated_mod_structure_msg": "The mod you are importing uses the old file structure (pre-update).\n\nThe game now requires audio files to be in a 'Media' subfolder.\nDo you want to automatically reorganize the files to the new format?"

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
        "wav_to_wem_converter": "Конвертер Audio в WEM",
        "conversion_mode": "Режим конвертации (ТОЛЬКО Size matching mode)",
        "strict_mode": "Строгий режим",
        "adaptive_mode": "Адаптивный режим",
        "strict_mode_desc": "❌ Ошибка, если слишком большой",
        "adaptive_mode_desc": "✅ Авто-подстройка качества",
        "path_configuration": "Настройка путей",
        "wwise_path": "Wwise:",
        "project_path": "Проект:",
        "wav_path": "Audio:",
        "files_for_conversion": "Файлы для конвертации",
        "add_all_wav": "Добавить все Audio файлы",
        "convert": "Конвертировать",
        "files_ready": "Файлов готово:",
        "wav_file": "Audio файл",
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
        "converter_instructions": "Конвертер Audio в WEM:\n1) Укажите путь Wwise 2) Выберите папку для проекта 3) Выберите папку Audio 4) Добавьте файлы 5) Конвертируйте",
        "converter_instructions2": "Конвертер WEM:\n1) Укажите путь Wwise проекта 2) Конвертируйте в мод",
        
        # === ПУТИ И ПЛЕЙСХОЛДЕРЫ ===
        "wwise_path_placeholder": "Путь установки Wwise... (Пример: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "Путь нового/старого проекта... (Пример: D:/ExampleProjects/MyNewProject) P.S. Может быть пустым",
        "wav_folder_placeholder": "Папка с Audio файлами...",
        
        # === ПОИСК И ОБРАБОТКА ===
        "select_wav_folder": "Сначала выберите папку с Audio файлами!",
        "wems_folder_not_found": "Папка Wems не найдена",
        "no_wav_files": "В папке нет Audio файлов!",
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
        "wem_processor_recommendation": "Рекомендуется использовать 'Audio to WEM' для новичков.",
        
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
        "modern_ui": "🎨 <b>Интерфейс:</b> Чистый интерфейс с тёмной/светлой темами",
        "technology_stack": "Технологический стек",
        "built_with": "Создано с Python 3 и PyQt5, используя:",
        "unreal_locres_tool": "UnrealLocres для работы с .locres файлами",
        "vgmstream_tool": "vgmstream для конвертации аудио",
        "repak_tool": "repak для упаковки модов",
        "ffmpeg_tool": "FFmpeg для обработки аудио",
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
        "copyright_notice": "Copyright (c) 2026 OutlastTrials AudioEditor",
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
        "mouse_right_click": "<b>Правый клик:</b> Показать контекстное меню",
        "verify_mod_integrity": "Проверить целостность мода",
        "rebuild_bnk_index": "Пересобрать BNK мода",
        "rebuild_bnk_tooltip": "Принудительно синхронизирует все BNK-файлы с фактическими WEM-файлами в вашем моде.",
        "verifying_mod_integrity": "Проверка целостности мода...",
        "bnk_verification_complete": "Проверка завершена",
        "bnk_no_issues_found": "Все измененные аудиофайлы соответствуют записям в BNK. Проблем не найдено!",
        "bnk_issues_found_title": "Обнаружены проблемы с целостностью мода",
        "bnk_issues_found_text": "Найдено {count} проблем в вашем моде.\n\nЭти проблемы могут привести к некорректному воспроизведению звуков в игре.\n\nХотите автоматически исправить эти записи?",
        "fix_all_btn": "Исправить все",
        "bnk_size_mismatch": "Несоответствие размера",
        "bnk_entry_missing": "Отсутствует запись в BNK",
        "bnk_report_size": "Тип: {type} в {bnk_name}\n  Звук: {short_name} (ID: {source_id})\n  - Размер в BNK: {bnk_size} байт\n  - Размер WEM: {wem_size} байт\n\n",
        "bnk_report_missing": "Тип: {type}\n  Звук: {short_name} (ID: {source_id})\n  - Файл .wem существует, но соответствующая запись не найдена ни в одном измененном .bnk файле.\n\n",
        "fixing_mod_issues": "Исправление проблем мода...",
        "fix_complete_no_issues": "Автоматически исправляемых проблем не найдено (например, 'Отсутствует запись в BNK').",
        "fix_complete_title": "Исправление завершено",
        "fix_complete_message": "Исправлено {count} проблем с несоответствием размеров.",
        "fix_complete_with_errors": "Исправлено {fixed} проблем с несоответствием размеров.\nНе удалось исправить {errors} записей. Подробности в консоли отладки.",
        "verification_error": "Ошибка проверки",
        "verification_error_message": "Во время проверки произошла ошибка:\n\n{error}",
        "rebuild_bnk_confirm_title": "Пересобрать BNK",
        "rebuild_bnk_confirm_text": "Это действие просканирует все измененные аудиофайлы (.wem) и принудительно обновит записи о размерах в .bnk файлах вашего мода.\n\nЭто полезно для устранения несоответствий после ручного добавления, удаления или редактирования WEM-файлов.\n\nВы хотите продолжить?",
        "rebuilding_mod_bnk": "Пересборка BNK мода...",
        "rebuild_complete_title": "Пересборка завершена",
        "rebuild_complete_message": "Пересборка завершена!\n\n✅ Пересоздано {created} BNK-файлов в вашем моде из оригиналов.\n🔄 Обновлено {updated} записей в соответствии с вашими WEM-файлами.\n⚙️ Применено {reverted} пользовательских настроек 'Внутриигровых эффектов'.",
        "profiles": "Профили",
        "profile_manager_tooltip": "Открыть менеджер профилей модов",
        "edit_profile": "Редактировать профиль мода",
        "create_profile": "Создать новый профиль мода",
        "profile_name": "Имя профиля:",
        "author": "Автор:",
        "version": "Версия:",
        "icon_png": "Иконка (PNG):",
        "no_icon_selected": "Иконка не выбрана.",
        "select_icon": "Выбрать иконку",
        "png_images": "Изображения PNG",
        "validation_error": "Ошибка валидации",
        "profile_name_empty": "Имя профиля не может быть пустым.",
        "profile_manager_title": "Менеджер профилей модов",
        "create_new_profile_btn": "➕ Создать новый...",
        "add_existing_profile_btn": "📁 Добавить существующий...",
        "remove_from_list_btn": "➖ Убрать из списка",
        "select_a_profile": "Выберите профиль",
        "author_label": "<b>Автор:</b>",
        "version_label": "<b>Версия:</b>",
        "no_description": "<i>Нет описания.</i>",
        "edit_details_btn": "⚙️ Редактировать...",
        "active_profile_btn": "✓ Активен",
        "activate_profile_btn": "Активировать профиль",
        "error_reading_profile": "<i style='color:red;'>Не удалось прочитать profile.json</i>",
        "error_author": "<i style='color:red;'>Ошибка</i>",
        "select_folder_for_profile": "Выберите папку для создания нового профиля",
        "profile_exists_error": "Профиль с таким именем уже существует.",
        "create_profile_error": "Не удалось создать профиль: {e}",
        "select_existing_profile": "Выберите существующую папку профиля",
        "invalid_profile_folder": "Выбранная папка не содержит обязательную подпапку '{folder}'.",
        "profile_already_added": "Профиль с таким именем уже был добавлен.",
        "remove_profile_title": "Удалить профиль",
        "remove_profile_text": "Вы уверены, что хотите убрать профиль '{name}' из списка?\n\nЭто НЕ удалит файлы на вашем диске.",
        "profile_activated_title": "Профиль активирован",
        "profile_activated_text": "Профиль '{name}' теперь активен.",
        "no_active_profile_title": "Нет активного профиля",
        "no_active_profile_text": "В данный момент нет активного профиля. Пожалуйста, создайте или активируйте профиль.",
        "rebuild_complete_message_details": "Пересборка завершена!\n\n"
                                  "✅ Пересоздано {created} BNK-файлов в вашем моде из оригиналов.\n"
                                  "🔄 Обновлено {updated} записей в соответствии с вашими WEM-файлами.\n"
                                  "⚙️ Применено {reverted} пользовательских настроек 'Внутриигровых эффектов'.",
        "select_version_title": "Выберите версию",
        "adjust_volume_for": "Настроить громкость для: {filename}\n\nКакую версию вы хотите настроить?",
        "batch_adjust_volume_for": "Пакетная настройка громкости для {count} файлов\n\nКакую версию вы хотите настроить?",
        "no_language_selected": "Язык не выбран",
        "select_language_tab_first": "Пожалуйста, сначала выберите вкладку с языком.",
        "no_files_selected": "Файлы не выбраны",
        "select_files_for_volume": "Пожалуйста, выберите один или несколько аудиофайлов для настройки громкости.",
        "quick_load_audio_title": "🎵 Быстрая загрузка аудио...",
        "quick_load_audio_tooltip": "Заменить этот звук своим файлом (любой формат)",
        "restore_from_backup_title": "🔄 Восстановить из резервной копии",
        "restore_from_backup_tooltip": "Восстановить предыдущую версию измененного аудио",
        "adjust_original_volume_title": "🔊 Настроить громкость оригинала...",
        "trim_original_audio_title": "✂️ Обрезать оригинал...",
        "adjust_mod_volume_title": "🔊 Настроить громкость мода...",
        "trim_mod_audio_title": "✂️ Обрезать мод...",
        "toggle_ingame_effects_title": "✨ Переключить внутриигровые эффекты",
        "marking_menu_title": "🖍 Пометки",
        "set_color_menu_title": "🎨 Установить цвет",
        "set_tag_menu_title": "🏷 Установить тег",
        "color_green": "Зеленый",
        "color_yellow": "Желтый",
        "color_red": "Красный",
        "color_blue": "Синий",
        "color_none": "Нет",
        "tag_important": "Важное",
        "tag_check": "Проверить",
        "tag_done": "Готово",
        "tag_review": "На проверку",
        "tag_none": "Нет",
        "tag_custom": "Свой...",
        "custom_tag_title": "Пользовательский тег",
        "custom_tag_prompt": "Введите пользовательский тег:",
        "select_folder_to_open_title": "Выберите папку для открытия",
        "which_folder_to_open": "Какую папку вы хотели бы открыть?",
        "voice_files_folder": "🎙 Голосовые файлы\n{path}",
        "sfx_files_folder": "🔊 Звуковые эффекты\n{path}",
        "subtitles_folder": "📝 Субтитры\n{path}",
        "no_target_folders_found": "Целевые папки не найдены!",
        "quick_load_mode_label": "Выберите режим конвертации для быстрой загрузки аудио:",
        "quick_load_strict": "Строгий режим - Ошибка, если файл слишком большой",
        "quick_load_adaptive": "Адаптивный режим - Авто-подстройка качества",
        "audio_files_dialog_title": "Аудиофайлы",
        "volume_editor_title": "Редактор громкости - {shortname}",
        "volume_deps_missing": "⚠️ Для редактирования громкости требуются библиотеки NumPy и SciPy.\n\nПожалуйста, установите их, используя:\npip install numpy scipy",
        "audio_analysis_group": "Анализ аудио",
        "analyzing": "Анализ...",
        "current_rms": "Текущий RMS:",
        "current_peak": "Текущий пик:",
        "duration_label": "Длительность:",
        "recommended_max": "Рекомендуемый макс.:",
        "no_limit": "Нет ограничений",
        "volume_control_group": "Управление громкостью",
        "volume_label_simple": "Громкость:",
        "quick_presets": "Быстрые настройки:",
        "waiting_for_analysis": "Ожидание анализа...",
        "preview_rms_peak": "Предпросмотр: RMS {new_rms:.1f}%, Пик {new_peak:.1f}%",
        "preview_clipping": " ⚠️ КЛИППИНГ (превышение на {over:.1f}%)",
        "preview_near_clipping": " ⚠️ Близко к клиппингу",
        "apply_volume_change_btn": "Применить изменение громкости",
        "volume_no_change_msg": "Громкость установлена на 100% (без изменений).",
        "config_required": "Требуется настройка",
        "wwise_config_required_msg": "Wwise не настроен.\n\nПожалуйста, проверьте:\n1. Перейдите на вкладку 'Конвертер' и настройте пути Wwise\n2. Убедитесь, что проект Wwise существует\n3. Попробуйте сначала сконвертировать хотя бы один файл на вкладке 'Конвертер'",
        "status_preparing": "Подготовка...",
        "status_using_backup": "Используется бэкап как источник...",
        "status_backup_created": "Создан бэкап и используется как источник...",
        "status_using_original": "Используется оригинал как источник...",
        "status_converting_to_wav": "Конвертация WEM в WAV...",
        "status_adjusting_volume": "Настройка громкости...",
        "status_preparing_for_wem": "Подготовка к конвертации в WEM...",
        "status_converting_to_wem": "Конвертация в WEM...",
        "status_deploying_to_mod": "Размещение в MOD_P...",
        "status_complete": "Завершено!",
        "volume_change_success_msg": "Громкость успешно изменена на {volume}%\nФактическое изменение: {actual_change:.0f}%\n{clipping_info}\n{source_info}\n{backup_info}",
        "clipping_info_text": "\nКлиппинг: {percent:.2f}% сэмплов",
        "backup_available_info": "\n\n💾 Доступна резервная копия - при необходимости вы можете восстановить предыдущую версию.",
        "source_info_backup": "\n📁 Источник: Бэкап (сохранение оригинального качества)",
        "source_info_mod_backup_created": "\n📁 Источник: Текущий мод (создан бэкап)",
        "source_info_original": "\n📁 Источник: Оригинальный файл",
        "wem_conversion_failed_msg": "Конвертация в WEM не удалась!\n\nВозможные решения:\n1. Проверьте конфигурацию Wwise на вкладке 'Конвертер'\n2. Попробуйте сначала сконвертировать обычный WAV-файл для проверки настроек\n3. Убедитесь, что проект Wwise имеет правильные настройки аудио\n4. Проверьте, достижим ли целевой размер файла\n\nТехническая ошибка: {error_message}",
        "wwise_not_configured_msg": "Wwise не настроен должным образом!\n\nПожалуйста:\n1. Перейдите на вкладку 'Конвертер'\n2. Укажите действительный путь установки Wwise\n3. Укажите путь к проекту\n4. Попробуйте сконвертировать хотя бы один файл для проверки настроек\n\nЗатем попробуйте настроить громкость снова.",
        "required_file_not_found_msg": "Не найден требуемый файл!\n\n{error_message}\n\nПожалуйста, убедитесь, что:\n- Аудиофайл существует\n- Права доступа к файлу корректны\n- Никакая другая программа не использует файл",
        "volume_change_failed_title": "Не удалось изменить громкость",

        # === РЕДАКТОР ГРОМКОСТИ (ПАКЕТНЫЙ) ===
        "batch_volume_editor_title": "Пакетный редактор громкости ({count} файлов)",
        "wwise_configured_auto": "✅ Wwise настроен автоматически",
        "wwise_not_configured_warning": "⚠️ Wwise не настроен - пожалуйста, сначала настройте на вкладке 'Конвертер'",
        "backups_stored_in": "Резервные копии хранятся в: {path}",
        "volume_control_all_files_group": "Управление громкостью (для всех файлов)",
        "files_to_process_group": "Файлы для обработки",
        "file_header": "Файл",
        "language_header": "Язык",
        "current_rms_header": "Текущий RMS",
        "current_peak_header": "Текущий пик",
        "new_preview_header": "Предпросмотр",
        "status_header": "Статус",
        "apply_to_all_btn": "Применить ко всем файлам",
        "status_skipped_no_analysis": "✗ Пропущено (нет анализа)",
        "batch_process_complete_title": "Пакетная обработка завершена",
        "batch_process_complete_msg": "Пакетное изменение громкости завершено!\n\nГромкость изменена на: {volume}%\nУспешно: {successful}\nС ошибками: {failed}",
        "batch_process_error_title": "Ошибка пакетной обработки",

        # === КОНСОЛЬ ОТЛАДКИ ===
        "debug_console_title": "Консоль отладки",
        "auto_scroll_check": "Автопрокрутка",
        "save_log_btn": "Сохранить лог",
        "save_debug_log_title": "Сохранить лог отладки",
        "log_files_filter": "Файлы логов (*.log)",

        # === DRAG & DROP АУДИО ===
        "invalid_file_title": "Неверный файл",
        "audio_only_drop_msg": "Поддерживается перетаскивание только аудиофайлов.",
        "drop_audio_title": "Перетаскивание аудио",
        "drop_on_file_msg": "Пожалуйста, перетащите на конкретный аудиофайл.",
        "replace_audio_title": "Заменить аудио",
        "replace_audio_confirm_msg": "Заменить аудио для:\n{shortname}\n\nфайлом:\n{filename}?",

        # === ПОИСК ===
        "search_placeholder": "Поиск...",

        # === ЗАГРУЗЧИК СУБТИТРОВ ===
        "processing_file_status": "Обработка {filename}...",
        "processing_additional_subs_status": "Обработка дополнительных субтитров...",
        "loaded_subs_from_files_status": "Загружено {count} субтитров из {processed_files} файлов",
        
        # === РЕДАКТОР СУБТИТРОВ (ГЛОБАЛЬНЫЙ) ===
        "subtitle_editor_tab_title": "Редактор локализации",
        "subtitle_editor_header": "Редактор локализации",
        "subtitle_editor_desc": "Редактируйте локализацию напрямую. Используйте глобальную строку поиска для фильтрации.",
        "without_audio_filter": "Без аудио",
        "without_audio_filter_tooltip": "Показать только субтитры, у которых нет соответствующих аудиофайлов",
        "modified_only_filter": "Только изменённые",
        "modified_only_filter_tooltip": "Показать только изменённые субтитры",
        "with_audio_only_filter": "Только с аудио",
        "with_audio_only_filter_tooltip": "Показать только субтитры, у которых есть соответствующие аудиофайлы",
        "refresh_btn": "🔄 Обновить",
        "refresh_btn_tooltip": "Обновить данные субтитров из файлов",
        "key_header": "Ключ",
        "original_header": "Оригинал",
        "current_header": "Текущий",
        "audio_header": "Аудио",
        "edit_selected_btn": "✏ Редактировать",
        "save_all_changes_btn": "💾 Сохранить все изменения",
        "subtitle_save_success": "Все изменения субтитров сохранены!",
        "go_to_audio_action": "🔊 Перейти к аудиофайлу",
        "audio_not_found_for_key": "Не удалось найти аудиофайл для ключа субтитра: {key}",
        "tab_not_found_for_lang": "Не удалось найти вкладку для языка: {lang}",

        # === ОБРАБОТЧИК WEM (СТАРЫЙ) ===
        "wem_processor_tab_title": "Процессор WEM (Старый)",
        "process_wem_files_btn": "Обработать WEM файлы",
        "open_target_folder_btn": "Открыть целевую папку",

        # === ОЧИСТКА СУБТИТРОВ ===
        "no_working_files_found": "Рабочие файлы субтитров (_working.locres) не найдены в Localization.",
        "cleanup_complete_msg": "Удалено {deleted} рабочих файлов субтитров.",
        "cleanup_complete_with_errors_msg": "Удалено {deleted} рабочих файлов субтитров.\nОшибок: {errors}",

        # === РАЗНОЕ UI ===
        "quick_load_settings_group": "Настройки быстрой загрузки",
        "conversion_method_group": "Метод конвертации",
        "bnk_overwrite_radio": "Перезапись BNK (Рекомендуется)",
        "bnk_overwrite_tooltip": "Конвертирует с максимальным качеством и перезаписывает размер файла в .bnk файле.",
        "adaptive_size_matching_radio": "Адаптивное соответствие размера",
        "adaptive_size_matching_tooltip": "Подстраивает качество аудио, чтобы соответствовать размеру оригинального WEM файла.",
        "rescan_orphans_action": "Пересканировать файлы-сироты",
        "rescan_orphans_tooltip": "Принудительно запускает новое сканирование папки Wems для поиска файлов, отсутствующих в SoundbanksInfo",
        "in_progress_msg": "Уже в процессе. Пожалуйста, подождите.",
        "add_single_file_title": "Выберите аудиофайл",
        "audio_files_filter": "Аудиофайлы (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus *.webm);;Все файлы (*.*)",
        "file_added_status": "Добавлен: {filename}",
        "file_not_added_status": "Файл не добавлен: {filename}",
        "error_adding_file_msg": "Ошибка при добавлении файла:\n\n{error}",
        "update_file_q_title": "Файл уже добавлен",
        "update_file_q_msg": "Файл '{filename}' уже в списке на конвертацию.\n\nХотите обновить его настройки?",
        "update_btn": "Обновить",
        "skip_btn": "Пропустить",
        "duplicate_target_q_title": "Дубликат целевого WEM",
        "duplicate_target_q_msg": "Целевой WEM '{file_id}.wem' уже назначен для:\n\nТекущий: {existing_name}\nНовый: {new_name}\n\nХотите заменить?",
        "replace_btn": "Заменить",
        "replace_all_btn": "Заменить все",
        "skip_all_btn": "Пропустить все",
        "tags_group_filter": "--- Теги ---",
        "with_tag_filter": "С тегом: {tag}",
        "numeric_id_files_group": "Файлы с числовым ID",
        "voice_group_name": "VO (Озвучка)",
        "bnk_size_mismatch_tooltip": "BNK ожидает {expected_size:,} байт, но файл {actual_size:,} байт.\nНажмите, чтобы обновить запись в BNK.",
        "bnk_size_missing_wem_tooltip": "Запись в BNK была изменена, но WEM-файл отсутствует.\nНажмите, чтобы вернуть запись в BNK к исходному состоянию.",
        "bnk_size_ok_tooltip": "ОК: Фактический размер файла совпадает с записью в BNK.",
        "bnk_size_mismatch_btn": "Несовпадение! Нажмите для исправления",
        "bnk_size_missing_wem_btn": "Отсутствует WEM! Нажмите для отмены",
        "bnk_fix_success_msg": "Размер файла в BNK успешно обновлен!",
        "bnk_fix_not_found_msg": "Не удалось найти запись для ID {file_id} ни в одном измененном BNK файле для исправления.",
        "bnk_fix_error_msg": "Произошла непредвиденная ошибка при исправлении файла BNK:\n{error}",
        "bnk_revert_success_msg": "Запись в BNK успешно возвращена к исходному состоянию.",
        "bnk_revert_fail_msg": "Не удалось вернуть запись в BNK. Возможно, запись уже верна.",
        "bnk_revert_error_msg": "Произошла непредвиденная ошибка при возврате записи BNK:\n{error}",
        "select_folder_for_mods_title": "Выберите папку для хранения модов",
        "welcome_title": "Добро пожаловать!",
        "first_time_setup_msg": "Похоже, вы запускаете редактор в первый раз.\n\nПожалуйста, выберите корневую папку, где вы хотите хранить профили модов (например, 'Мои документы\\OutlastTrialsMods').\n\nТам будет создан профиль 'Default'.",
        "setup_required_title": "Требуется настройка",
        "setup_required_msg": "Для продолжения работы требуется папка для модов. Приложение будет закрыто.",
        "setup_complete_title": "Настройка завершена",
        "setup_complete_msg": "Ваш профиль 'Default' был создан в:\n{mods_root}",
        "setup_failed_title": "Ошибка настройки",
        "setup_failed_msg": "Произошла ошибка: {e}",
        "legacy_migration_title": "Новая система профилей модов",
        "legacy_migration_msg": "Эта версия использует новую систему для управления несколькими модами.\n\nВаша существующая папка 'MOD_P' может быть перенесена в новый профиль с именем 'Default'.\n\nПожалуйста, выберите корневую папку для хранения профилей модов (например, 'Мои документы\\OutlastTrialsMods').",
        "migration_complete_title": "Перенос завершен",
        "migration_complete_msg": "Ваш мод был успешно перенесен в профиль 'Default' внутри:\n{mods_root}",
        "migration_failed_title": "Ошибка переноса",
        "migration_failed_msg": "Произошла ошибка: {e}",
        "scan_progress_title": "Сканирование дополнительных аудиофайлов",
        "scan_progress_msg": "Подготовка к сканированию...",
        "scan_complete_status": "Сканирование завершено. Найдено и кэшировано {count} дополнительных аудиофайлов.",
        "no_new_files_found_status": "Новых аудиофайлов во время сканирования не найдено.",
        "volume_adjust_tooltip_no_selection": "Настроить громкость (сначала выберите файлы)",
        "volume_adjust_tooltip_single": "Настроить громкость для: {filename}",
        "volume_adjust_tooltip_batch": "Пакетная настройка громкости для {count} файлов",
        "easter_egg_title": "Вы нашли котика!",
        "easter_egg_loading": "Загрузка котика...",
        "easter_egg_message": "Этот маленький котик следит за всеми вашими аудио правками!",
        "crash_log_saved_msg": "\n\nЛог сбоя сохранен в: {log_path}",
        "crash_log_failed_msg": "\n\nНе удалось сохранить лог сбоя: {error}",
        "app_error_title": "Ошибка приложения",
        "app_error_msg": "В приложении произошла ошибка, и оно будет закрыто.",
        "app_error_info": "Пожалуйста, сообщите об этой ошибке с подробностями ниже.",
        "copy_error_btn": "Копировать ошибку в буфер обмена",
        "stats_label_text": "Показано {filtered_count} из {total_count} файлов | Субтитры: {subtitle_count}",
        "shortcut_play_original_action": "Воспроизвести оригинальное аудио",
        "shortcut_play_original_desc": "Воспроизводит оригинальную версию выбранного аудиофайла.",
        "shortcut_play_mod_action": "Воспроизвести мод аудио",
        "shortcut_play_mod_desc": "Воспроизводит измененную версию выбранного аудиофайла.",
        "shortcut_delete_mod_action": "Удалить мод аудио",
        "shortcut_delete_mod_desc": "Удаляет измененное аудио для выбранного файла(ов).",
        "volume_toolbar_btn": "🔊 Громкость",
        "show_scanned_files_check": "Показать отсканированные",
        "show_scanned_files_tooltip": "Показать/скрыть аудиофайлы, найденные при сканировании папки 'Wems', которых нет в основной базе данных.",
        "add_file_btn": "Добавить файл...",

        # === ИНФО-ПАНЕЛЬ ===
        "bnk_size_label": "Размер в BNK:",
        "in_game_effects_label": "Внутриигровые эффекты:",
        "last_modified_label": "Последнее изменение:",

        # === РЕДАКТОР ОБРЕЗКИ (TRIM) ===
        "trim_editor_title": "Обрезка аудио - {shortname}",
        "trim_deps_missing": "Обрезка недоступна.\n\nПожалуйста, убедитесь, что установлены следующие библиотеки:\n'pip install numpy scipy matplotlib'",
        "trimming_audio_for": "Обрезка аудио для: {shortname}",
        "version_mod": " (версия МОДа)",
        "version_original": " (оригинальная версия)",
        "zoom_label": "Масштаб:",
        "start_time_label": "Время начала:",
        "end_time_label": "Время конца:",
        "new_duration_label": "Новая длительность:",
        "new_duration_format": "{duration_sec:.3f} с ({duration_ms} мс)",
        "play_pause_btn": "▶️ Пуск/Пауза",
        "preview_trim_btn": "🎬 Предпросмотр",
        "stop_btn": "⏹️ Стоп",
        "apply_trim_btn": "Применить обрезку",
        "preparing_audio_failed": "Не удалось подготовить аудио: {e}",
        "trimming_with_ffmpeg": "Обрезка аудио с помощью FFmpeg...",
        "trim_success_msg": "Аудио успешно обрезано и установлено!",
        "trim_failed_title": "Ошибка обрезки",
        "compiling_step_1": "Вызываем духов кода...",
        "compiling_step_2": "Загоняем бродячие пиксели в стойло...",
        "compiling_step_3": "Учим WEM-файлы петь хором...",
        "compiling_step_4": "Полируем мод до блеска...",
        "compiling_step_5": "Будим игровой движок...",
        "compiling_step_6": "Прячем секреты от датамайнеров...",
        "compiling_step_7": "Завершаем... (Честно-честно!)",
        "splash_loading_app": "Загрузка приложения, пожалуйста, подождите...",
        "splash_init_ui": "Инициализация интерфейса...",
        "splash_loading_profiles": "Загрузка профилей...",
        "app_already_running_title": "Приложение уже запущено",
        "app_already_running_msg": "OutlastTrials AudioEditor уже запущен.",
        "project_statistics_title": "Статистика проекта",
        "mod_profile_label": "Профиль мода:",
        "general_stats_group": "Общая статистика",
        "total_audio_files": "Всего изменено аудиофайлов:",
        "total_subtitle_files": "Всего изменено файлов субтитров:",
        "total_mod_size": "Общий размер мода (распакованного):",
        "subtitle_stats_group": "Статистика по субтитрам",
        "modified_subtitle_entries": "Измененных записей в субтитрах:",
        "new_subtitle_entries": "Новых записей в субтитрах:",
        "total_languages_affected": "Затронуто языков:",
        "modified_files_group": "Список измененных файлов",
        "copy_list_btn": "Копировать список",
        "list_copied_msg": "Список измененных файлов скопирован в буфер обмена!",
        "no_profile_active_for_stats": "Нет активного профиля. Статистика недоступна.",
        "calculating_stats": "Подсчет...",
        "recalculate_btn": "🔄 Пересчитать",
        "resource_updater_tab": "Обновление ресурсов",
        "updater_header": "Обновить ресурсы игры",
        "updater_description": "Извлеките последние аудио (.wem) и файлы локализации (.locres) напрямую из .pak архивов игры. Это гарантирует, что вы всегда работаете с самыми актуальными файлами.",
        "select_pak_file_group": "Выберите .pak файл игры",
        "pak_file_path_label": "Путь к .pak файлу:",
        "pak_file_path_placeholder": "Напр., C:/.../The Outlast Trials/OPP/Content/Paks/OPP-WindowsClient.pak",
        "select_resources_group": "Выберите ресурсы для обновления",
        "update_audio_check": "Обновить аудиофайлы (Wems)",
        "update_localization_check": "Обновить файлы локализации",
        "start_update_btn": "Начать обновление",
        "update_process_group": "Процесс обновления",
        "update_log_ready": "Готов к началу процесса обновления.",
        "update_confirm_title": "Подтвердите обновление ресурсов",
        "update_confirm_msg": "Это действие заменит ваши текущие локальные папки '{resource_folder}' файлами, извлеченными из игры.\n\n- Ваши текущие файлы будут удалены.\n- Это действие нельзя отменить.\n\nВы уверены, что хотите продолжить?",
        "pak_file_not_selected": "Пожалуйста, сначала выберите действительный .pak файл игры.",
        "no_resources_selected": "Пожалуйста, выберите хотя бы один тип ресурсов для обновления (Аудио или Локализация).",
        "update_process_started": "Процесс обновления запущен...",
        "unpacking_files_from": "Распаковка файлов из {pak_name}...",
        "unpacking_path": "Распаковка '{path_to_unpack}'...",
        "unpack_failed": "Repak не смог распаковать файлы. Подробности ниже.",
        "clearing_old_files": "Очистка старых файлов в '{folder_name}'...",
        "moving_new_files": "Перемещение новых файлов в '{folder_name}'...",
        "organizing_sfx": "Организация SFX файлов...",
        "update_complete_title": "Обновление завершено",
        "update_complete_msg": "Следующие ресурсы были успешно обновлены:\n\n{updated_resources}\n\nРекомендуется перезапустить приложение, чтобы применить все изменения.",
        "update_failed_title": "Ошибка обновления",
        "update_failed_msg": "Процесс обновления не удался. Пожалуйста, проверьте лог для получения подробной информации.",
        "restart_recommended": "Рекомендуется перезапуск",
        "settings_saved_title": "Настройки сохранены",
        "close_required_message": "Настройки языка были изменены.\n\nПриложение необходимо закрыть, чтобы изменения вступили в силу.",
        "close_now_button": "Закрыть сейчас",
        "update_warning_title": "Идет обновление",
        "update_warning_msg": "Процесс обновления ресурсов запущен.\n\nПожалуйста, не используйте и не закрывайте приложение до его завершения. Это может занять несколько минут в зависимости от вашей системы.",
        "update_fun_status_1": "Завариваем кофе для Койла...",
        "update_fun_status_2": "Соединяем сплайны...",
        "update_fun_status_3": "Спрашиваем у КГБ, где лежат файлы...",
        "update_fun_status_4": "Синхронизация с серверами Мёркофф...",
        "update_fun_status_5": "Точно не устанавливаем шпионское ПО...",
        "update_fun_status_6": "Распаковываем крики и шёпот...",
        "update_fun_status_7": "Перекалибровка Морфогенетического движка...",
        "update_step_unpacking": "Распаковка файлов из архива игры...",
        "update_step_clearing": "Удаление старых локальных файлов...",
        "update_step_moving": "Перемещение новых файлов...",
        "update_step_organizing": "Организация новых файлов...",
        "update_unpacking_long_wait": "Начат процесс распаковки. Это может занять несколько минут в зависимости от вашей системы...",
        "update_cancelled_by_user": "Обновление отменено пользователем",
        "update_step_finishing": "Завершение...",
        "update_in_progress_title": "Идёт обновление",
        "confirm_exit_during_update_message": "Процесс обновления ресурсов всё ещё запущен.\n\nВы уверены, что хотите выйти? Это отменит обновление.",
        "update_rescanning_orphans": "Обновление завершено. Пересканирование папки Wems на наличие изменений...",
        "initial_setup_title": "Первоначальная настройка",
        "wems_folder_missing_message": "Папка 'Wems' с аудиофайлами игры не найдена.\n\nОна необходима для корректной работы приложения.\n\nХотите перейти на вкладку 'Обновление ресурсов', чтобы извлечь их из игры сейчас?",
        "localization_folder_missing_message": "Папка 'Localization' с файлами субтитров игры не найдена.\n\nОна необходима для редактирования субтитров.\n\nХотите перейти на вкладку 'Обновление ресурсов', чтобы извлечь их из игры сейчас?",
        "go_to_updater_button": "Перейти к обновлению",
        "import_mod_title": "Импорт мода",
        "select_pak_to_import": "Выберите .pak файл для импорта",
        "pak_files": "PAK файлы",
        "enter_profile_name_for_pak": "Введите имя для нового профиля (основано на имени .pak файла):",
        "importing_mod_progress": "Импорт мода...",
        "unpacking_pak_file": "Распаковка .pak файла...",
        "creating_profile_structure": "Создание структуры профиля...",
        "moving_mod_files": "Перемещение файлов мода...",
        "cleaning_up": "Очистка...",
        "import_successful_title": "Импорт успешно завершен",
        "import_successful_message": "Мод '{pak_name}' был успешно импортирован как профиль '{profile_name}'.",
        "import_failed_title": "Ошибка импорта",
        "import_mod_from_pak": "Импортировать мод из .pak...",
        "wems_folder_loose_files_title": "Обнаружены неуместные аудиофайлы",
        "wems_folder_loose_files_message": "Найдено {count} аудиофайлов (.wem/.bnk) в главной папке 'Wems'.",
        "wems_folder_loose_files_details": "Обычно эти файлы должны находиться в подпапке 'Wems/SFX'. Их перемещение поможет поддерживать порядок в проекте и обеспечит их правильное обнаружение.\n\nХотите переместить их в папку 'Wems/SFX' сейчас?",
        "move_all_files_btn": "Переместить все файлы",
        "ignore_btn": "Игнорировать",
        "move_complete_title": "Перемещение завершено",
        "move_complete_message": "Успешно перемещено {count} файл(ов) в папку 'Wems/SFX'.",
        "move_complete_errors": "Не удалось переместить {count} файл(ов):\n{errors}",
        "soundbanksinfo_missing_title": "Отсутствует файл базы данных",
        "soundbanksinfo_missing_message": "Основной файл базы данных аудио (SoundbanksInfo.json) не найден.",
        "soundbanksinfo_missing_details": "Этот файл необходим для идентификации большинства аудиофайлов. Хотите перейти на вкладку 'Обновление ресурсов', чтобы извлечь последние файлы игры сейчас?",
        "go_to_updater_btn": "Перейти к обновлению",
        "later_btn": "Позже",
        "critical_file_missing_title": "Отсутствует критический файл",
        "critical_file_missing_message": "SoundbanksInfo.json отсутствует, и вкладка 'Обновление ресурсов' не найдена.",
        "move_complete_restart_note": "\n\nРекомендуется перезапустить приложение, чтобы изменения вступили в силу.",
        "outdated_mod_structure_title": "Устаревшая структура мода",
        "outdated_mod_structure_msg": "Импортируемый мод использует старую структуру файлов (до обновления игры).\n\nТеперь игра требует, чтобы аудиофайлы находились в подпапке 'Media'.\nВы хотите автоматически перестроить файлы в новый формат?"
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
        "wav_to_wem_converter": "Konwerter Audio do WEM",
        "conversion_mode": "Tryb konwersji (Tylko Size matching mode)",
        "strict_mode": "Tryb ścisły",
        "adaptive_mode": "Tryb adaptacyjny",
        "strict_mode_desc": "❌ Zawodzi jeśli za duży",
        "adaptive_mode_desc": "✅ Auto-dostosowanie jakości",
        "path_configuration": "Konfiguracja ścieżek",
        "wwise_path": "Wwise:",
        "project_path": "Projekt:",
        "wav_path": "Audio:",
        "files_for_conversion": "Pliki do konwersji",
        "add_all_wav": "Dodaj wszystkie pliki Audio",
        "convert": "Konwertuj",
        "files_ready": "Pliki gotowe:",
        "wav_file": "Plik Audio",
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
        "converter_instructions": "Konwerter Audio do WEM:\n1) Ustaw ścieżkę Wwise 2) Wybierz folder tymczasowego projektu 3) Wybierz folder Audio 4) Dodaj pliki 5) Konwertuj",
        "converter_instructions2": "Konwerter WEM:\n1) Ustaw ścieżkę projektu Wwise 2) Konwertuj do moda",
        
        # === ŚCIEŻKI I PLACEHOLDERY ===
        "wwise_path_placeholder": "Ścieżka instalacji Wwise... (Przykład: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "Ścieżka nowego/starego projektu... (Przykład: D:/ExampleProjects/MyNewProject) P.S. Może być pusta",
        "wav_folder_placeholder": "Folder z plikami Audio...",
        
        # === WYSZUKIWANIE I PRZETWARZANIE ===
        "select_wav_folder": "Najpierw wybierz folder Audio!",
        "wems_folder_not_found": "Nie znaleziono folderu Wems",
        "no_wav_files": "Nie znaleziono plików Audio w folderze!",
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
        "wem_processor_recommendation": "Zaleca się używanie „Audio do WEM” dla nowych użytkowników.",
        
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
        "modern_ui": "🎨 <b>Interfejs:</b> Czysty interfejs z ciemnymi/jasnymi motywami",
        "technology_stack": "Stos technologiczny",
        "built_with": "Zbudowane z Python 3 i PyQt5, wykorzystując:",
        "unreal_locres_tool": "UnrealLocres do obsługi plików .locres",
        "vgmstream_tool": "vgmstream do konwersji audio",
        "repak_tool": "repak do pakowania modów",
        "ffmpeg_tool": "FFmpeg do obróbki audio",
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
        "copyright_notice": "Copyright (c) 2026 OutlastTrials AudioEditor",
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
        "mouse_right_click": "<b>Prawy klik:</b> Pokaż menu kontekstowe",
        "verify_mod_integrity": "Sprawdź spójność moda",
        "rebuild_bnk_index": "Przebuduj indeks BNK moda",
        "rebuild_bnk_tooltip": "Wymusza synchronizację wszystkich plików BNK z rzeczywistymi plikami WEM w twoim modzie.",
        "verifying_mod_integrity": "Sprawdzanie spójności moda...",
        "bnk_verification_complete": "Weryfikacja zakończona",
        "bnk_no_issues_found": "Wszystkie zmodyfikowane pliki audio są zgodne z wpisami BNK. Nie znaleziono problemów!",
        "bnk_issues_found_title": "Znaleziono problemy ze spójnością moda",
        "bnk_issues_found_text": "Znaleziono {count} problemów w twoim modzie.\n\nTe problemy mogą powodować nieprawidłowe odtwarzanie dźwięków w grze.\n\nCzy chcesz automatycznie naprawić te wpisy?",
        "fix_all_btn": "Napraw wszystko",
        "bnk_size_mismatch": "Niezgodność rozmiaru",
        "bnk_entry_missing": "Brak wpisu w BNK",
        "bnk_report_size": "Typ: {type} w {bnk_name}\n  Dźwięk: {short_name} (ID: {source_id})\n  - Rozmiar w BNK: {bnk_size} bajtów\n  - Rozmiar WEM: {wem_size} bajtów\n\n",
        "bnk_report_missing": "Typ: {type}\n  Dźwięk: {short_name} (ID: {source_id})\n  - Plik .wem istnieje, ale odpowiadający mu wpis nie został znaleziony w żadnym zmodyfikowanym pliku .bnk.\n\n",
        "fixing_mod_issues": "Naprawianie problemów z modem...",
        "fix_complete_no_issues": "Nie znaleziono problemów, które można naprawić automatycznie (np. 'Brak wpisu w BNK').",
        "fix_complete_title": "Naprawianie zakończone",
        "fix_complete_message": "Naprawiono {count} problemów z niezgodnością rozmiaru.",
        "fix_complete_with_errors": "Naprawiono {fixed} problemów z niezgodnością rozmiaru.\nNie udało się naprawić {errors} wpisów. Zobacz konsolę debugowania, aby uzyskać szczegóły.",
        "verification_error": "Błąd weryfikacji",
        "verification_error_message": "Wystąpił błąd podczas weryfikacji:\n\n{error}",
        "rebuild_bnk_confirm_title": "Przebuduj indeks BNK",
        "rebuild_bnk_confirm_text": "Ta operacja przeskanuje wszystkie zmodyfikowane pliki audio (.wem) i wymusi aktualizację rekordów rozmiaru w plikach .bnk twojego moda.\n\nJest to przydatne do naprawy niespójności po ręcznym dodawaniu, usuwaniu lub edytowaniu plików WEM.\n\nCzy chcesz kontynuować?",
        "rebuilding_mod_bnk": "Przebudowywanie indeksu BNK moda...",
        "rebuild_complete_title": "Przebudowa zakończona",
        "rebuild_complete_message": "Przebudowa zakończona!\n\n✅ Utworzono ponownie {created} plików BNK w twoim modzie z oryginałów.\n🔄 Zaktualizowano {updated} wpisów, aby pasowały do twoich plików WEM.\n⚙️ Zastosowano {reverted} niestandardowych ustawień 'Efektów w grze'.",
        "profiles": "Profile",
        "profile_manager_tooltip": "Otwórz menedżera profili modów",
        "edit_profile": "Edytuj profil moda",
        "create_profile": "Utwórz nowy profil moda",
        "profile_name": "Nazwa profilu:",
        "author": "Autor:",
        "version": "Wersja:",
        "icon_png": "Ikona (PNG):",
        "no_icon_selected": "Nie wybrano ikony.",
        "select_icon": "Wybierz ikonę",
        "png_images": "Obrazy PNG",
        "validation_error": "Błąd walidacji",
        "profile_name_empty": "Nazwa profilu nie może być pusta.",
        "profile_manager_title": "Menedżer profili modów",
        "create_new_profile_btn": "➕ Utwórz nowy...",
        "add_existing_profile_btn": "📁 Dodaj istniejący...",
        "remove_from_list_btn": "➖ Usuń z listy",
        "select_a_profile": "Wybierz profil",
        "author_label": "<b>Autor:</b>",
        "version_label": "<b>Wersja:</b>",
        "no_description": "<i>Brak opisu.</i>",
        "edit_details_btn": "⚙️ Edytuj...",
        "active_profile_btn": "✓ Aktywny",
        "activate_profile_btn": "Aktywuj profil",
        "error_reading_profile": "<i style='color:red;'>Nie można odczytać profile.json</i>",
        "error_author": "<i style='color:red;'>Błąd</i>",
        "select_folder_for_profile": "Wybierz folder do utworzenia nowego profilu",
        "profile_exists_error": "Profil o tej nazwie już istnieje.",
        "create_profile_error": "Nie można utworzyć profilu: {e}",
        "select_existing_profile": "Wybierz istniejący folder profilu",
        "invalid_profile_folder": "Wybrany folder nie zawiera wymaganego podfolderu '{folder}'.",
        "profile_already_added": "Profil o tej nazwie został już dodany.",
        "remove_profile_title": "Usuń profil",
        "remove_profile_text": "Czy na pewno chcesz usunąć profil '{name}' z listy?\n\nTo NIE usunie plików na dysku.",
        "profile_activated_title": "Profil aktywowany",
        "profile_activated_text": "Profil '{name}' jest teraz aktywny.",
        "no_active_profile_title": "Brak aktywnego profilu",
        "no_active_profile_text": "Obecnie nie ma aktywnego profilu. Proszę utworzyć lub aktywować profil.",
        "rebuild_complete_message_details": "Przebudowa zakończona!\n\n"
                                  "✅ Utworzono ponownie {created} plików BNK w twoim modzie z oryginałów.\n"
                                  "🔄 Zaktualizowano {updated} wpisów, aby pasowały do twoich plików WEM.\n"
                                  "⚙️ Zastosowano {reverted} niestandardowych ustawień 'Efektów w grze'.",
        "select_version_title": "Wybierz wersję",
        "adjust_volume_for": "Dostosuj głośność dla: {filename}\n\nKtórą wersję chcesz dostosować?",
        "batch_adjust_volume_for": "Zbiorcze dostosowywanie głośności dla {count} plików\n\nKtórą wersję chcesz dostosować?",
        "no_language_selected": "Nie wybrano języka",
        "select_language_tab_first": "Proszę najpierw wybrać zakładkę języka.",
        "no_files_selected": "Nie wybrano plików",
        "select_files_for_volume": "Proszę wybrać jeden lub więcej plików audio, aby dostosować głośność.",
        "quick_load_audio_title": "🎵 Szybkie ładowanie audio...",
        "quick_load_audio_tooltip": "Zastąp ten dźwięk własnym plikiem (dowolny format)",
        "restore_from_backup_title": "🔄 Przywróć z kopii zapasowej",
        "restore_from_backup_tooltip": "Przywróć poprzednią wersję zmodyfikowanego audio",
        "adjust_original_volume_title": "🔊 Dostosuj głośność oryginału...",
        "trim_original_audio_title": "✂️ Przytnij oryginał...",
        "adjust_mod_volume_title": "🔊 Dostosuj głośność moda...",
        "trim_mod_audio_title": "✂️ Przytnij mod...",
        "toggle_ingame_effects_title": "✨ Przełącz efekty w grze",
        "marking_menu_title": "🖍 Oznaczanie",
        "set_color_menu_title": "🎨 Ustaw kolor",
        "set_tag_menu_title": "🏷 Ustaw tag",
        "color_green": "Zielony",
        "color_yellow": "Żółty",
        "color_red": "Czerwony",
        "color_blue": "Niebieski",
        "color_none": "Brak",
        "tag_important": "Ważne",
        "tag_check": "Do sprawdzenia",
        "tag_done": "Gotowe",
        "tag_review": "Do przeglądu",
        "tag_none": "Brak",
        "tag_custom": "Niestandardowy...",
        "custom_tag_title": "Tag niestandardowy",
        "custom_tag_prompt": "Wprowadź tag niestandardowy:",
        "select_folder_to_open_title": "Wybierz folder do otwarcia",
        "which_folder_to_open": "Który folder chcesz otworzyć?",
        "voice_files_folder": "🎙 Pliki głosowe\n{path}",
        "sfx_files_folder": "🔊 Efekty dźwiękowe\n{path}",
        "subtitles_folder": "📝 Napisy\n{path}",
        "no_target_folders_found": "Nie znaleziono folderów docelowych!",
        "quick_load_mode_label": "Wybierz tryb konwersji dla Szybkiego ładowania audio:",
        "quick_load_strict": "Tryb ścisły - Błąd, jeśli plik jest za duży",
        "quick_load_adaptive": "Tryb adaptacyjny - Automatyczne dostosowanie jakości",
        "audio_files_dialog_title": "Pliki audio",
        "volume_editor_title": "Edytor głośności - {shortname}",
        "volume_deps_missing": "⚠️ Edycja głośności wymaga bibliotek NumPy i SciPy.\n\nZainstaluj je za pomocą:\npip install numpy scipy",
        "audio_analysis_group": "Analiza audio",
        "analyzing": "Analizowanie...",
        "current_rms": "Aktualne RMS:",
        "current_peak": "Aktualny szczyt:",
        "duration_label": "Czas trwania:",
        "recommended_max": "Zalecane maks.:",
        "no_limit": "Brak limitu",
        "volume_control_group": "Kontrola głośności",
        "volume_label_simple": "Głośność:",
        "quick_presets": "Szybkie ustawienia:",
        "waiting_for_analysis": "Oczekiwanie na analizę...",
        "preview_rms_peak": "Podgląd: RMS {new_rms:.1f}%, Szczyt {new_peak:.1f}%",
        "preview_clipping": " ⚠️ PRZESTEROWANIE (ponad {over:.1f}%)",
        "preview_near_clipping": " ⚠️ Blisko przesterowania",
        "apply_volume_change_btn": "Zastosuj zmianę głośności",
        "volume_no_change_msg": "Głośność ustawiona na 100% (bez zmian).",
        "config_required": "Wymagana konfiguracja",
        "wwise_config_required_msg": "Wwise nie jest skonfigurowany.\n\nSprawdź:\n1. Przejdź do zakładki 'Konwerter' i skonfiguruj ścieżki Wwise\n2. Upewnij się, że projekt Wwise istnieje\n3. Spróbuj najpierw przekonwertować przynajmniej jeden plik w zakładce 'Konwerter'",
        "status_preparing": "Przygotowywanie...",
        "status_using_backup": "Używanie kopii zapasowej jako źródła...",
        "status_backup_created": "Utworzono kopię zapasową i użyto jako źródła...",
        "status_using_original": "Używanie oryginału jako źródła...",
        "status_converting_to_wav": "Konwertowanie WEM na WAV...",
        "status_adjusting_volume": "Dostosowywanie głośności...",
        "status_preparing_for_wem": "Przygotowywanie do konwersji na WEM...",
        "status_converting_to_wem": "Konwertowanie na WEM...",
        "status_deploying_to_mod": "Wdrażanie do MOD_P...",
        "status_complete": "Zakończono!",
        "volume_change_success_msg": "Głośność pomyślnie zmieniona na {volume}%\nRzeczywista zmiana: {actual_change:.0f}%\n{clipping_info}\n{source_info}\n{backup_info}",
        "clipping_info_text": "\nPrzesterowanie: {percent:.2f}% próbek",
        "backup_available_info": "\n\n💾 Dostępna kopia zapasowa - w razie potrzeby możesz przywrócić poprzednią wersję.",
        "source_info_backup": "\n📁 Źródło: Kopia zapasowa (zachowanie oryginalnej jakości)",
        "source_info_mod_backup_created": "\n📁 Źródło: Aktualny mod (utworzono kopię zapasową)",
        "source_info_original": "\n📁 Źródło: Oryginalny plik",
        "wem_conversion_failed_msg": "Konwersja na WEM nie powiodła się!\n\nMożliwe rozwiązania:\n1. Sprawdź konfigurację Wwise w zakładce 'Konwerter'\n2. Spróbuj najpierw przekonwertować zwykły plik WAV, aby przetestować konfigurację\n3. Upewnij się, że projekt Wwise ma prawidłowe ustawienia audio\n4. Sprawdź, czy docelowy rozmiar pliku jest osiągalny\n\nBłąd techniczny: {error_message}",
        "wwise_not_configured_msg": "Wwise nie jest prawidłowo skonfigurowany!\n\nProszę:\n1. Przejdź do zakładki 'Konwerter'\n2. Ustaw prawidłową ścieżkę instalacji Wwise\n3. Ustaw ścieżkę projektu\n4. Spróbuj przekonwertować przynajmniej jeden plik, aby zweryfikować konfigurację\n\nNastępnie spróbuj ponownie dostosować głośność.",
        "required_file_not_found_msg": "Nie znaleziono wymaganego pliku!\n\n{error_message}\n\nSprawdź, czy:\n- Plik audio istnieje\n- Uprawnienia do pliku są prawidłowe\n- Żaden inny program nie używa pliku",
        "volume_change_failed_title": "Zmiana głośności nie powiodła się",

        # === EDYTOR GŁOŚNOŚCI (WSADOWY) ===
        "batch_volume_editor_title": "Wsadowy edytor głośności ({count} plików)",
        "wwise_configured_auto": "✅ Wwise skonfigurowany automatycznie",
        "wwise_not_configured_warning": "⚠️ Wwise nie jest skonfigurowany - skonfiguruj w zakładce 'Konwerter'",
        "backups_stored_in": "Kopie zapasowe są przechowywane w: {path}",
        "volume_control_all_files_group": "Kontrola głośności (dla wszystkich plików)",
        "files_to_process_group": "Pliki do przetworzenia",
        "file_header": "Plik",
        "language_header": "Język",
        "current_rms_header": "Aktualne RMS",
        "current_peak_header": "Aktualny szczyt",
        "new_preview_header": "Nowy podgląd",
        "status_header": "Status",
        "apply_to_all_btn": "Zastosuj do wszystkich plików",
        "status_skipped_no_analysis": "✗ Pominięto (brak analizy)",
        "batch_process_complete_title": "Przetwarzanie wsadowe zakończone",
        "batch_process_complete_msg": "Wsadowa zmiana głośności zakończona!\n\nGłośność zmieniona na: {volume}%\nUdane: {successful}\nNieudane: {failed}",
        "batch_process_error_title": "Błąd przetwarzania wsadowego",

        # === KONSOLA DEBUGOWANIA ===
        "debug_console_title": "Konsola debugowania",
        "auto_scroll_check": "Automatyczne przewijanie",
        "save_log_btn": "Zapisz log",
        "save_debug_log_title": "Zapisz log debugowania",
        "log_files_filter": "Pliki log (*.log)",

        # === PRZECIĄGNIJ I UPUŚĆ AUDIO ===
        "invalid_file_title": "Nieprawidłowy plik",
        "audio_only_drop_msg": "Obsługiwane jest tylko przeciąganie plików audio.",
        "drop_audio_title": "Upuszczanie audio",
        "drop_on_file_msg": "Proszę upuścić na konkretny plik audio.",
        "replace_audio_title": "Zamień audio",
        "replace_audio_confirm_msg": "Zamienić audio dla:\n{shortname}\n\nplikiem:\n{filename}?",

        # === WYSZUKIWANIE ===
        "search_placeholder": "Szukaj...",

        # === ŁADOWARKA NAPISÓW ===
        "processing_file_status": "Przetwarzanie {filename}...",
        "processing_additional_subs_status": "Przetwarzanie dodatkowych napisów...",
        "loaded_subs_from_files_status": "Załadowano {count} napisów z {processed_files} plików",
        
        # === EDYTOR NAPISÓW (GLOBALNY) ===
        "subtitle_editor_tab_title": "Edytor lokalizacji",
        "subtitle_editor_header": "Edytor lokalizacji",
        "subtitle_editor_desc": "Edytuj lokalizację bezpośrednio. Użyj globalnego paska wyszukiwania, aby filtrować.",
        "without_audio_filter": "Bez audio",
        "without_audio_filter_tooltip": "Pokaż tylko napisy, które nie mają odpowiadających im plików audio",
        "modified_only_filter": "Tylko zmodyfikowane",
        "modified_only_filter_tooltip": "Pokaż tylko zmodyfikowane napisy",
        "with_audio_only_filter": "Tylko z audio",
        "with_audio_only_filter_tooltip": "Pokaż tylko napisy, które mają odpowiadające im pliki audio",
        "refresh_btn": "🔄 Odśwież",
        "refresh_btn_tooltip": "Odśwież dane napisów z plików",
        "key_header": "Klucz",
        "original_header": "Oryginał",
        "current_header": "Aktualny",
        "audio_header": "Audio",
        "edit_selected_btn": "✏ Edytuj zaznaczone",
        "save_all_changes_btn": "💾 Zapisz wszystkie zmiany",
        "subtitle_save_success": "Wszystkie zmiany w napisach zostały zapisane!",
        "go_to_audio_action": "🔊 Przejdź do pliku audio",
        "audio_not_found_for_key": "Nie można znaleźć pliku audio dla klucza napisu: {key}",
        "tab_not_found_for_lang": "Nie można znaleźć zakładki dla języka: {lang}",

        # === PROCESOR WEM (STARY) ===
        "wem_processor_tab_title": "Procesor WEM (Stary)",
        "process_wem_files_btn": "Przetwórz pliki WEM",
        "open_target_folder_btn": "Otwórz folder docelowy",

        # === CZYSZCZENIE NAPISÓW ===
        "no_working_files_found": "Nie znaleziono roboczych plików napisów (_working.locres) w folderze Localization.",
        "cleanup_complete_msg": "Usunięto {deleted} roboczych plików napisów.",
        "cleanup_complete_with_errors_msg": "Usunięto {deleted} roboczych plików napisów.\nBłędy: {errors}",

        # === RÓŻNE UI ===
        "quick_load_settings_group": "Ustawienia szybkiego ładowania",
        "conversion_method_group": "Metoda konwersji",
        "bnk_overwrite_radio": "Nadpisanie BNK (Zalecane)",
        "bnk_overwrite_tooltip": "Konwertuje z maksymalną jakością i nadpisuje rozmiar pliku w pliku .bnk.",
        "adaptive_size_matching_radio": "Adaptacyjne dopasowanie rozmiaru",
        "adaptive_size_matching_tooltip": "Dostosowuje jakość audio, aby dopasować rozmiar oryginalnego pliku WEM.",
        "rescan_orphans_action": "Przeskanuj osierocone pliki",
        "rescan_orphans_tooltip": "Wymusza ponowne skanowanie folderu Wems w celu znalezienia plików, których nie ma w SoundbanksInfo",
        "in_progress_msg": "Już w toku. Proszę czekać.",
        "add_single_file_title": "Wybierz plik audio",
        "audio_files_filter": "Pliki audio (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus *.webm);;Wszystkie pliki (*.*)",
        "file_added_status": "Dodano: {filename}",
        "file_not_added_status": "Plik nie został dodany: {filename}",
        "error_adding_file_msg": "Błąd podczas dodawania pliku:\n\n{error}",
        "update_file_q_title": "Plik już dodany",
        "update_file_q_msg": "Plik '{filename}' jest już na liście konwersji.\n\nCzy chcesz zaktualizować jego ustawienia?",
        "update_btn": "Aktualizuj",
        "skip_btn": "Pomiń",
        "duplicate_target_q_title": "Zduplikowany docelowy WEM",
        "duplicate_target_q_msg": "Docelowy WEM '{file_id}.wem' jest już przypisany do:\n\nObecny: {existing_name}\nNowy: {new_name}\n\nCzy chcesz go zastąpić?",
        "replace_btn": "Zastąp",
        "replace_all_btn": "Zastąp wszystkie",
        "skip_all_btn": "Pomiń wszystkie",
        "tags_group_filter": "--- Tagi ---",
        "with_tag_filter": "Z tagiem: {tag}",
        "numeric_id_files_group": "Pliki z numerycznym ID",
        "voice_group_name": "VO (Głos)",
        "bnk_size_mismatch_tooltip": "BNK oczekuje {expected_size:,} bajtów, ale plik ma {actual_size:,} bajtów.\nKliknij, aby zaktualizować wpis w BNK.",
        "bnk_size_missing_wem_tooltip": "Wpis w BNK został zmodyfikowany, ale brakuje pliku WEM.\nKliknij, aby przywrócić wpis w BNK do stanu pierwotnego.",
        "bnk_size_ok_tooltip": "OK: Rzeczywisty rozmiar pliku zgadza się z wpisem w BNK.",
        "bnk_size_mismatch_btn": "Niezgodność! Kliknij, aby naprawić",
        "bnk_size_missing_wem_btn": "Brak WEM! Kliknij, aby przywrócić",
        "bnk_fix_success_msg": "Rozmiar pliku w BNK został pomyślnie zaktualizowany!",
        "bnk_fix_not_found_msg": "Nie można znaleźć wpisu dla ID {file_id} w żadnym zmodyfikowanym pliku BNK do naprawy.",
        "bnk_fix_error_msg": "Wystąpił nieoczekiwany błąd podczas naprawiania pliku BNK:\n{error}",
        "bnk_revert_success_msg": "Wpis w BNK został pomyślnie przywrócony do stanu pierwotnego.",
        "bnk_revert_fail_msg": "Nie udało się przywrócić wpisu w BNK. Wpis może być już poprawny.",
        "bnk_revert_error_msg": "Wystąpił nieoczekiwany błąd podczas przywracania wpisu BNK:\n{error}",
        "select_folder_for_mods_title": "Wybierz folder do przechowywania modów",
        "welcome_title": "Witaj!",
        "first_time_setup_msg": "Wygląda na to, że uruchamiasz edytor po raz pierwszy.\n\nWybierz folder główny, w którym chcesz przechowywać profile modów (np. 'Moje dokumenty\\OutlastTrialsMods').\n\nZostanie tam utworzony profil 'Default'.",
        "setup_required_title": "Wymagana konfiguracja",
        "setup_required_msg": "Do kontynuacji wymagany jest folder na mody. Aplikacja zostanie zamknięta.",
        "setup_complete_title": "Konfiguracja zakończona",
        "setup_complete_msg": "Twój profil 'Default' został utworzony w:\n{mods_root}",
        "setup_failed_title": "Błąd konfiguracji",
        "setup_failed_msg": "Wystąpił błąd: {e}",
        "legacy_migration_title": "Nowy system profili modów",
        "legacy_migration_msg": "Ta wersja używa nowego systemu do zarządzania wieloma modami.\n\nTwój istniejący folder 'MOD_P' może zostać przeniesiony do nowego profilu o nazwie 'Default'.\n\nWybierz folder główny, w którym chcesz przechowywać swoje profile modów (np. 'Moje dokumenty\\OutlastTrialsMods').",
        "migration_complete_title": "Migracja zakończona",
        "migration_complete_msg": "Twój mod został pomyślnie przeniesiony do profilu 'Default' wewnątrz:\n{mods_root}",
        "migration_failed_title": "Błąd migracji",
        "migration_failed_msg": "Wystąpił błąd: {e}",
        "scan_progress_title": "Skanowanie w poszukiwaniu dodatkowych plików audio",
        "scan_progress_msg": "Przygotowywanie do skanowania...",
        "scan_complete_status": "Skanowanie zakończone. Znaleziono i zapisano w pamięci podręcznej {count} dodatkowych plików audio.",
        "no_new_files_found_status": "Podczas skanowania nie znaleziono nowych plików audio.",
        "volume_adjust_tooltip_no_selection": "Dostosuj głośność (najpierw wybierz pliki)",
        "volume_adjust_tooltip_single": "Dostosuj głośność dla: {filename}",
        "volume_adjust_tooltip_batch": "Wsadowe dostosowywanie głośności dla {count} plików",
        "easter_egg_title": "Znalazłeś kotka!",
        "easter_egg_loading": "Ładowanie kotka...",
        "easter_egg_message": "Ten mały kotek czuwa nad wszystkimi twoimi edycjami audio!",
        "crash_log_saved_msg": "\n\nLog awarii zapisany w: {log_path}",
        "crash_log_failed_msg": "\n\nNie udało się zapisać logu awarii: {error}",
        "app_error_title": "Błąd aplikacji",
        "app_error_msg": "Wystąpił błąd aplikacji, która zostanie zamknięta.",
        "app_error_info": "Zgłoś ten błąd z poniższymi szczegółami.",
        "copy_error_btn": "Kopiuj błąd do schowka",
        "stats_label_text": "Wyświetlanie {filtered_count} z {total_count} plików | Napisy: {subtitle_count}",
        "shortcut_play_original_action": "Odtwórz oryginalne audio",
        "shortcut_play_original_desc": "Odtwarza oryginalną wersję wybranego pliku audio.",
        "shortcut_play_mod_action": "Odtwórz audio moda",
        "shortcut_play_mod_desc": "Odtwarza zmodyfikowaną wersję wybranego pliku audio.",
        "shortcut_delete_mod_action": "Usuń audio moda",
        "shortcut_delete_mod_desc": "Usuwa zmodyfikowane audio dla wybranego pliku (plików).",
        "volume_toolbar_btn": "🔊 Głośność",
        "show_scanned_files_check": "Pokaż zeskanowane pliki",
        "show_scanned_files_tooltip": "Pokaż/ukryj pliki audio znalezione podczas skanowania folderu 'Wems', których nie ma w głównej bazie danych.",
        "add_file_btn": "Dodaj plik...",

        # === PANEL INFORMACYJNY ===
        "bnk_size_label": "Rozmiar w BNK:",
        "in_game_effects_label": "Efekty w grze:",
        "last_modified_label": "Ostatnia modyfikacja:",

        # === EDYTOR PRZYCINANIA (TRIM) ===
        "trim_editor_title": "Przycinanie audio - {shortname}",
        "trim_deps_missing": "Przycinanie nie jest dostępne.\n\nUpewnij się, że zainstalowane są następujące biblioteki:\n'pip install numpy scipy matplotlib'",
        "trimming_audio_for": "Przycinanie audio dla: {shortname}",
        "version_mod": " (wersja MOD)",
        "version_original": " (wersja oryginalna)",
        "zoom_label": "Powiększenie:",
        "start_time_label": "Czas rozpoczęcia:",
        "end_time_label": "Czas zakończenia:",
        "new_duration_label": "Nowy czas trwania:",
        "new_duration_format": "{duration_sec:.3f} s ({duration_ms} ms)",
        "play_pause_btn": "▶️ Odtwarzaj/Pauza",
        "preview_trim_btn": "🎬 Podgląd przycięcia",
        "stop_btn": "⏹️ Zatrzymaj",
        "apply_trim_btn": "Zastosuj przycięcie",
        "preparing_audio_failed": "Nie udało się przygotować audio: {e}",
        "trimming_with_ffmpeg": "Przycinanie audio za pomocą FFmpeg...",
        "trim_success_msg": "Audio pomyślnie przycięte i wdrożone!",
        "trim_failed_title": "Błąd przycinania",
        "compiling_step_1": "Przywoływanie duchów kodu...",
        "compiling_step_2": "Zaganianie zbuntowanych pikseli...",
        "compiling_step_3": "Uczenie WEMów śpiewu w harmonii...",
        "compiling_step_4": "Polerowanie moda na wysoki połysk...",
        "compiling_step_5": "Budzenie silnika gry...",
        "compiling_step_6": "Ukrywanie sekretów przed data minerami...",
        "compiling_step_7": "Finalizowanie... (Obiecuję!)",
        "splash_loading_app": "Ładowanie aplikacji, proszę czekać...",
        "splash_init_ui": "Inicjalizacja interfejsu...",
        "splash_loading_profiles": "Ładowanie profili...",
        "app_already_running_title": "Aplikacja jest już uruchomiona",
        "app_already_running_msg": "OutlastTrials AudioEditor jest już uruchomiony.",
        "project_statistics_title": "Statystyki projektu",
        "mod_profile_label": "Profil moda:",
        "general_stats_group": "Statystyki ogólne",
        "total_audio_files": "Całkowita liczba zmodyfikowanych plików audio:",
        "total_subtitle_files": "Całkowita liczba zmodyfikowanych plików napisów:",
        "total_mod_size": "Całkowity rozmiar moda (rozpakowany):",
        "subtitle_stats_group": "Statystyki napisów",
        "modified_subtitle_entries": "Zmodyfikowane wpisy w napisach:",
        "new_subtitle_entries": "Nowe wpisy w napisach:",
        "total_languages_affected": "Języki, których dotyczy zmiana:",
        "modified_files_group": "Lista zmodyfikowanych plików",
        "copy_list_btn": "Kopiuj listę",
        "list_copied_msg": "Lista zmodyfikowanych plików została skopiowana do schowka!",
        "no_profile_active_for_stats": "Brak aktywnego profilu. Statystyki są niedostępne.",
        "calculating_stats": "Obliczanie...",
        "recalculate_btn": "🔄 Przelicz ponownie",
        "resource_updater_tab": "Aktualizator zasobów",
        "updater_header": "Aktualizuj zasoby gry",
        "updater_description": "Wyodrębnij najnowsze pliki audio (.wem) i lokalizacyjne (.locres) bezpośrednio z archiwów .pak gry. Zapewnia to, że zawsze pracujesz z najbardziej aktualnymi plikami.",
        "select_pak_file_group": "Wybierz plik .pak gry",
        "pak_file_path_label": "Ścieżka do pliku .pak:",
        "pak_file_path_placeholder": "np. C:/.../The Outlast Trials/OPP/Content/Paks/OPP-WindowsClient.pak",
        "select_resources_group": "Wybierz zasoby do aktualizacji",
        "update_audio_check": "Aktualizuj pliki audio (Wems)",
        "update_localization_check": "Aktualizuj pliki lokalizacyjne",
        "start_update_btn": "Rozpocznij aktualizację",
        "update_process_group": "Proces aktualizacji",
        "update_log_ready": "Gotowy do rozpoczęcia procesu aktualizacji.",
        "update_confirm_title": "Potwierdź aktualizację zasobów",
        "update_confirm_msg": "Ta operacja zastąpi Twoje obecne lokalne foldery '{resource_folder}' plikami wyodrębnionymi z gry.\n\n- Twoje obecne pliki zostaną usunięte.\n- Tej operacji nie można cofnąć.\n\nCzy na pewno chcesz kontynuować?",
        "pak_file_not_selected": "Najpierw wybierz prawidłowy plik .pak gry.",
        "no_resources_selected": "Wybierz co najmniej jeden typ zasobów do aktualizacji (Audio lub Lokalizacja).",
        "update_process_started": "Rozpoczęto proces aktualizacji...",
        "unpacking_files_from": "Rozpakowywanie plików z {pak_name}...",
        "unpacking_path": "Rozpakowywanie '{path_to_unpack}'...",
        "unpack_failed": "Repak nie zdołał rozpakować plików. Szczegóły poniżej.",
        "clearing_old_files": "Usuwanie starych plików w '{folder_name}'...",
        "moving_new_files": "Przenoszenie nowych plików do '{folder_name}'...",
        "organizing_sfx": "Organizowanie plików SFX...",
        "update_complete_title": "Aktualizacja zakończona",
        "update_complete_msg": "Następujące zasoby zostały pomyślnie zaktualizowane:\n\n{updated_resources}\n\nZaleca się ponowne uruchomienie aplikacji, aby zastosować wszystkie zmiany.",
        "update_failed_title": "Aktualizacja nie powiodła się",
        "update_failed_msg": "Proces aktualizacji nie powiódł się. Sprawdź log, aby uzyskać szczegółowe informacje.",
        "restart_recommended": "Zalecane ponowne uruchomienie",
        "settings_saved_title": "Ustawienia Zapisane",
        "close_required_message": "Ustawienia języka zostały zmienione.\n\nAplikacja musi zostać zamknięta, aby zmiany w pełni zaczęły obowiązywać.",
        "close_now_button": "Zamknij teraz",
        "update_warning_title": "Aktualizacja w toku",
        "update_warning_msg": "Rozpoczęto proces aktualizacji zasobów.\n\nProszę nie używać ani nie zamykać aplikacji, dopóki nie zostanie ukończony. Może to potrwać kilka minut, w zależności od systemu.",
        "update_fun_status_1": "Przygotowanie kawy dla Koyla...",
        "update_fun_status_2": "Reticulating splines...",
        "update_fun_status_3": "Pytanie FBI o lokalizację plików...",
        "update_fun_status_4": "Synchronizacja z serwerami Murkoffa...",
        "update_fun_status_5": "Zdecydowanie nie instalujemy oprogramowania szpiegującego...",
        "update_fun_status_6": "Rozpakowywanie krzyków i szeptów...",
        "update_fun_status_7": "Ponowna kalibracja Silnika Morfogenicznego...",
        "update_step_unpacking": "Rozpakowywanie plików z archiwum gry...",
        "update_step_clearing": "Usuwanie starych plików lokalnych...",
        "update_step_moving": "Przenoszenie nowych plików na miejsce...",
        "update_step_organizing": "Organizowanie nowych plików...",
        "update_unpacking_long_wait": "Rozpoczęto proces rozpakowywania. Może to potrwać kilka minut w zależności od systemu...",
        "update_cancelled_by_user": "Aktualizacja anulowana przez użytkownika",
        "update_step_finishing": "Kończenie...",
        "update_in_progress_title": "Aktualizacja w toku",
        "confirm_exit_during_update_message": "Proces aktualizacji zasobów jest wciąż w toku.\n\nCzy na pewno chcesz wyjść? Spowoduje to anulowanie aktualizacji.",
        "update_rescanning_orphans": "Aktualizacja zakończona. Ponowne skanowanie folderu Wems w poszukiwaniu zmian...",
        "initial_setup_title": "Konfiguracja początkowa",
        "wems_folder_missing_message": "Nie znaleziono folderu 'Wems' z plikami audio gry.\n\nJest on wymagany do poprawnego działania aplikacji.\n\nCzy chcesz przejść do zakładki 'Aktualizator zasobów', aby teraz wypakować je z gry?",
        "localization_folder_missing_message": "Nie znaleziono folderu 'Localization' z plikami napisów gry.\n\nJest on wymagany do edycji napisów.\n\nCzy chcesz przejść do zakładki 'Aktualizator zasobów', aby teraz wypakować je z gry?",
        "go_to_updater_button": "Przejdź do aktualizatora",
        "import_mod_from_pak": "Importuj mod z .pak...",
        "wems_folder_loose_files_title": "Znaleziono nieprawidłowo umieszczone pliki audio",
        "wems_folder_loose_files_message": "Znaleziono {count} plików audio (.wem/.bnk) w głównym folderze 'Wems'.",
        "wems_folder_loose_files_details": "Te pliki zazwyczaj powinny znajdować się w podfolderze 'Wems/SFX'. Przeniesienie ich pomoże w utrzymaniu porządku w projekcie i zapewni ich prawidłowe odnalezienie.\n\nCzy chcesz przenieść je teraz do folderu 'Wems/SFX'?",
        "move_all_files_btn": "Przenieś wszystkie pliki",
        "ignore_btn": "Ignoruj",
        "move_complete_title": "Przenoszenie zakończone",
        "move_complete_message": "Pomyślnie przeniesiono {count} plików do folderu 'Wems/SFX'.",
        "move_complete_errors": "Nie udało się przenieść {count} plików:\n{errors}",
        "soundbanksinfo_missing_title": "Brak pliku bazy danych",
        "soundbanksinfo_missing_message": "Nie znaleziono podstawowego pliku bazy danych audio (SoundbanksInfo.json).",
        "soundbanksinfo_missing_details": "Ten plik jest wymagany do identyfikacji większości plików audio. Czy chcesz przejść do zakładki 'Aktualizator zasobów', aby teraz wypakować najnowsze pliki gry?",
        "go_to_updater_btn": "Przejdź do aktualizatora",
        "later_btn": "Później",
        "critical_file_missing_title": "Brak krytycznego pliku",
        "critical_file_missing_message": "Brak pliku SoundbanksInfo.json, a zakładka 'Aktualizator zasobów' nie została znaleziona.",
        "move_complete_restart_note": "\n\nZaleca się ponowne uruchomienie aplikacji, aby zmiany w pełni zaczęły obowiązywać.",
        "outdated_mod_structure_title": "Przestarzała struktura moda",
        "outdated_mod_structure_msg": "Importowany mod używa starej struktury plików (sprzed aktualizacji).\n\nGra wymaga teraz, aby pliki audio znajdowały się w podfolderze 'Media'.\nCzy chcesz automatycznie zreorganizować pliki do nowego formatu?"
    },
    "es-MX": {
        # === ELEMENTOS PRINCIPALES DE LA INTERFAZ ===
        "app_title": "Editor de Audio de Outlast Trials",
        "file_menu": "Archivo",
        "edit_menu": "Editar",
        "tools_menu": "Herramientas",
        "help_menu": "Ayuda",
        "save_subtitles": "Guardar Subtítulos",
        "export_subtitles": "Exportar Subtítulos...",
        "import_subtitles": "Importar Subtítulos...",
        "import_custom_subtitles": "Importar Subtítulos Personalizados (Beta)...",
        "exit": "Salir",
        "revert_to_original": "Revertir a Original",
        "find_replace": "Buscar y Reemplazar...",
        "compile_mod": "Compilar Mod",
        "deploy_and_run": "Desplegar Mod y Ejecutar Juego",
        "show_debug": "Mostrar Consola de Depuración",
        "settings": "Configuración...",
        "about": "Acerca de",
        
        # === FILTROS Y ORDENAMIENTO ===
        "filter": "Filtro:",
        "sort": "Ordenar:",
        "all_files": "Todos los Archivos",
        "with_subtitles": "Con Subtítulos",
        "without_subtitles": "Sin Subtítulos",
        "modified": "Modificado",
        "modded": "Modificado (Audio)",
        "name_a_z": "Nombre (A-Z)",
        "name_z_a": "Nombre (Z-A)",
        "id_asc": "ID ↑",
        "id_desc": "ID ↓",
        "recent_first": "Más Recientes Primero",
        
        # === PALABRAS BÁSICAS ===
        "name": "Nombre",
        "id": "ID",
        "subtitle": "Subtítulo",
        "status": "Estado",
        "mod": "MOD",
        "path": "Ruta",
        "source": "Fuente",
        "original": "Original",
        "save": "Guardar",
        "cancel": "Cancelar",
        "browse": "Examinar...",
        "confirmation": "Confirmación",
        "error": "Error",
        "warning": "Advertencia",
        "success": "Éxito",
        "info": "Información",
        "close": "Cerrar",
        "ready": "Listo",
        "waiting": "Esperando...",
        "done": "Completado",
        "error_status": "Error",
        "size_warning": "Advertencia de Tamaño",
        "loading": "Cargando...",
        "processing": "Procesando...",
        "converting": "Convirtiendo...",
        "complete": "Completo",
        "stop": "Detener",
        "clear": "Limpiar",
        "language": "Idioma",
        
        # === DIÁLOGOS Y MENSAJES ===
        "edit_subtitle": "Editar Subtítulo",
        "subtitle_preview": "Vista Previa de Subtítulo",
        "file_info": "Información del Archivo",
        "select_game_path": "Seleccionar carpeta raíz del juego",
        "game_path_saved": "Ruta del juego guardada",
        "mod_deployed": "¡Mod desplegado exitosamente!",
        "game_launching": "Iniciando juego...",
        "no_game_path": "Por favor establece la ruta del juego en configuración primero",
        "no_changes": "Sin Cambios",
        "no_modified_subtitles": "No hay subtítulos modificados para exportar",
        "import_error": "Error de Importación",
        "export_error": "Error de Exportación",
        "save_error": "Error al Guardar",
        "file_not_found": "Archivo no encontrado",
        "conversion_stopped": "Conversión detenida",
        "deployment_complete": "Despliegue completo",
        "characters": "Caracteres:",
        
        # === CONFLICTOS DE SUBTÍTULOS ===
        "conflict_detected": "Conflicto de Subtítulos Detectado",
        "conflict_message": "Las siguientes claves ya tienen subtítulos:\n\n{conflicts}\n\n¿Qué subtítulos te gustaría conservar?",
        "use_existing": "Mantener Existentes",
        "use_new": "Usar Nuevos",
        "merge_all": "Combinar Todos (Mantener Existentes)",
        
        # === CONVERTIDOR WAV TO WEM ===
        "wav_to_wem_converter": "Convertidor de Audio a WEM",
        "conversion_mode": "Modo de Conversión (Solo Modo de Coincidencia de Tamaño)",
        "strict_mode": "Modo Estricto",
        "adaptive_mode": "Modo Adaptativo",
        "strict_mode_desc": "❌ Falla si es demasiado grande",
        "adaptive_mode_desc": "✅ Ajusta calidad automáticamente",
        "path_configuration": "Configuración de Rutas",
        "wwise_path": "Wwise:",
        "project_path": "Proyecto:",
        "wav_path": "Audio:",
        "files_for_conversion": "Archivos para Conversión",
        "add_all_wav": "Agregar Todos los Archivos de Audio",
        "convert": "Convertir",
        "files_ready": "Archivos listos:",
        "wav_file": "Archivo de Audio",
        "target_wem": "WEM Objetivo",
        "target_size": "Tamaño Objetivo",
        "files_ready_count": "Archivos listos: {count}",
        "confirm_clear": "¿Limpiar todos los archivos?",
        
        # === CONVERSIÓN Y REGISTROS ===
        "conversion_complete": "Conversión Completa",
        "conversion_logs": "Registros de Conversión",
        "clear_logs": "Limpiar Registros",
        "save_logs": "Guardar Registros",
        "logs_cleared": "Registros limpiados...",
        "logs_saved": "Registros guardados",
        "error_saving_logs": "Error al guardar registros",
        "starting_conversion": "Iniciando conversión en modo {mode}...",
        "file_status": "Archivo {current}/{total}: {name}",
        "attempting": "intento {attempts} (Conversión={value})",
        "testing_sample_rate": "Probando {rate}Hz...",
        "resampled_to": "Remuestreado a {rate}Hz",
        "results_summary": "✅ ¡Conversión y despliegue completos!\n\nExitosos: {successful}\nErrores: {failed}\nAdvertencias de tamaño: {warnings}\n\nArchivos desplegados a MOD_P\nVer pestaña 'Registros' para resultados detallados",
        "add_files_warning": "¡Por favor agrega archivos para conversión primero!",
        
        # === INSTRUCCIONES ===
        "converter_instructions": "Convertidor de Audio a WEM:\n1) Establece ruta de Wwise 2) Elige carpeta temporal del proyecto 3) Selecciona carpeta de Audio 4) Agrega archivos 5) Convierte",
        "converter_instructions2": "Convertidor WEM:\n1) Establece ruta del proyecto Wwise 2) Convierte a mod",
        
        # === RUTAS Y MARCADORES DE POSICIÓN ===
        "wwise_path_placeholder": "Ruta de instalación de Wwise... (Ejemplo: D:/Audiokinetic/Wwise2019.1.6.7110)",
        "project_path_placeholder": "Ruta de Proyecto Nuevo/Viejo... (Ejemplo: D:/ProyectosEjemplo/MiNuevoProyecto) P.D. Puede estar vacío",
        "wav_folder_placeholder": "Carpeta de archivos de audio...",
        
        # === BÚSQUEDA Y PROCESAMIENTO ===
        "select_wav_folder": "¡Por favor selecciona la carpeta de Audio primero!",
        "wems_folder_not_found": "Carpeta Wems no encontrada",
        "no_wav_files": "¡No se encontraron archivos de Audio en la carpeta!",
        "search_complete": "Búsqueda completa",
        "auto_search_result": "Coincidencias encontradas automáticamente: {matched} de {total}",
        "target_language": "Idioma objetivo para archivos de voz",
        "no_matches_found": "No se encontraron coincidencias para",
        
        # === EXPORTACIÓN DE SUBTÍTULOS ===
        "cleanup_mod_subtitles": "Limpiar Subtítulos de MOD_P",
        "export_subtitles_for_game": "Exportar Subtítulos para el Juego",
        "subtitle_export_ready": "Listo para exportar subtítulos...",
        "deploying_files": "Desplegando archivos a la estructura del juego...",
        "deployment_error": "Error de despliegue",
        "conversion_failed": "Conversión fallida",
        "all_files_failed": "Todos los archivos fallaron",
        "see_logs_for_details": "Ver pestaña 'Registros' para detalles",
        "localization_editor": "Editor de Localización",
        
        # === PROCESADOR WEM ===
        "wem_processor_warning": "⚠️ Procesador WEM (No Recomendado)",
        "wem_processor_desc": "Herramienta heredada para procesar archivos WEM listos.",
        "wem_processor_recommendation": "Usa 'Audio a WEM' para principiantes.",
        
        # === EXPORTADOR DE LOCALIZACIÓN ===
        "localization_exporter": "Exportador de Localización",
        "export_modified_subtitles": "Exportar Subtítulos Modificados",
        "localization_editor_desc": "Edita localización directamente. Usa la barra de búsqueda global arriba para filtrar resultados.",
        
        # === LIMPIEZA DE SUBTÍTULOS ===
        "cleanup_subtitles_found": "Se encontraron {count} archivos de subtítulos en MOD_P",
        "select_files_to_delete": "Por favor selecciona archivos para eliminar",
        "confirm_deletion": "Confirmar Eliminación",
        "delete_files_warning": "¿Estás seguro de que quieres eliminar {count} archivos de subtítulos?\n\n¡Esta acción no se puede deshacer!",
        "cleanup_complete": "Limpieza Completa",
        "cleanup_with_errors": "Limpieza Completa con Errores",
        "files_deleted_successfully": "Se eliminaron exitosamente {count} archivos de subtítulos de MOD_P",
        "files_deleted_with_errors": "Se eliminaron {count} archivos exitosamente\n{errors} archivos tuvieron errores\n\nRevisa el registro de estado para detalles",
        "no_localization_found": "No se Encontraron Archivos",
        "no_localization_message": "No se encontró carpeta de localización en:\n{path}",
        "no_subtitle_files": "No se encontraron archivos de subtítulos en:\n{path}",
        "select_all": "Seleccionar Todo",
        "select_none": "Deseleccionar Todo",
        "quick_select": "Selección rápida:",
        "select_by_language": "Seleccionar por idioma...",
        "delete_selected": "Eliminar Seleccionados",
        "no_selection": "Sin Selección",
        
        # === INFORMACIÓN DE AUDIO ===
        "audio_comparison": "Comparación de Audio",
        "original_audio": "Audio Original",
        "modified_audio": "Audio Modificado",
        "duration": "Duración",
        "size": "Tamaño",
        "sample_rate": "Tasa de Muestreo",
        "bitrate": "Tasa de Bits",
        "channels": "Canales",
        "audio_markers": "Marcadores de Audio",
        "original_markers": "Marcadores Originales",
        "modified_markers": "Marcadores Modificados",
        "bnk_size_label": "Tamaño BNK",
        "in_game_effects_label": "Efectos en Juego",
        "last_modified_label": "Última Modificación",
        "fix_bnk_size_btn": "🔧 Arreglar Tamaño BNK",
        
        # === ACCIONES DE AUDIO ===
        "play_original": "▶️ Reproducir Original",
        "play_modified": "▶️ Reproducir Modificado",
        "replace_audio": "🔄 Reemplazar Audio...",
        "trim_audio": "✂️ Recortar Audio...",
        "adjust_volume": "🔊 Ajustar Volumen...",
        "delete_mod_audio": "🗑️ Eliminar Audio Modificado",
        "restore_from_backup": "🔄 Restaurar desde Respaldo",
        
        # === TOOLTIPS DE AUDIO ===
        "play_original_tooltip": "Reproducir audio original del juego",
        "play_modified_tooltip": "Reproducir audio modificado",
        "replace_audio_tooltip": "Reemplazar con nuevo archivo de audio",
        "trim_audio_tooltip": "Recortar audio a duración específica",
        "adjust_volume_tooltip": "Ajustar volumen del audio",
        "delete_mod_audio_tooltip": "Eliminar audio modificado y revertir a original",
        "restore_from_backup_tooltip": "Restaurar versión anterior del audio modificado",
        "trim_original_audio_title": "✂️ Recortar Audio Original...",
        
        # === AJUSTE DE VOLUMEN ===
        "adjust_volume_title": "Ajustar Volumen",
        "volume_adjustment": "Ajuste de Volumen:",
        "preview_volume": "Vista Previa",
        "current_volume": "Volumen Actual:",
        "new_volume": "Nuevo Volumen:",
        "volume_db": "{value} dB",
        "applying_volume": "Aplicando ajuste de volumen...",
        "volume_applied": "Volumen ajustado exitosamente",
        "volume_error": "Error al ajustar volumen",
        
        # === RECORTE DE AUDIO ===
        "trim_audio_title": "Recortar Audio",
        "start_time": "Tiempo de Inicio:",
        "end_time": "Tiempo Final:",
        "total_duration": "Duración Total:",
        "new_duration": "Nueva Duración:",
        "trim_and_save": "Recortar y Guardar",
        "invalid_times": "Tiempos de recorte inválidos",
        "trimming_audio": "Recortando audio...",
        "trim_successful": "Audio recortado exitosamente",
        "trim_error": "Error al recortar audio",
        
        # === COMPILACIÓN DE MOD ===
        "compile_mod_title": "Compilar Mod",
        "compile_mod_message": "¿Compilar mod actual en archivo .pak?",
        "compiling": "Compilando...",
        "compile_success": "Mod compilado exitosamente",
        "compile_error": "Error al compilar mod",
        
        # === DESPLIEGUE DE MOD ===
        "deploy_mod_title": "Desplegar Mod",
        "deploy_and_run_title": "Desplegar y Ejecutar",
        "deploying_mod": "Desplegando mod...",
        "mod_deployed_success": "¡Mod desplegado exitosamente!",
        "deploy_error": "Error al desplegar mod",
        
        # === ACTUALIZADOR DE RECURSOS ===
        "resource_updater": "Actualizador de Recursos",
        "update_resources": "Actualizar Recursos del Juego",
        "select_pak_file": "Seleccionar Archivo .pak del Juego",
        "extract_audio": "Extraer Audio",
        "extract_localization": "Extraer Localización",
        "start_extraction": "Iniciar Extracción",
        "extraction_complete": "Extracción completa",
        "extraction_error": "Error de extracción",
        "updater_description": "Extrae los archivos de audio (.wem) y localización (.locres) más recientes directamente de los archivos .pak del juego. Esto asegura que siempre estés trabajando con los archivos más actualizados.",
        
        # === ACTUALIZACIONES DE APLICACIÓN ===
        "check_updates": "🔄 Buscar Actualizaciones",
        "update_available": "Actualización Disponible",
        "update_message": "Una nueva versión está disponible:\nVersión Actual: {current}\nÚltima Versión: {latest}\n\n¿Quieres descargar la actualización?",
        "no_updates": "Sin Actualizaciones",
        "up_to_date": "Ya estás usando la versión más reciente.",
        "update_error": "Error al buscar actualizaciones",
        "checking_updates": "Buscando actualizaciones...",
        
        # === CONFIGURACIÓN ===
        "settings_title": "Configuración",
        "general_settings": "General",
        "paths_settings": "Rutas",
        "advanced_settings": "Avanzado",
        "game_path": "Ruta del Juego:",
        "wwise_path_setting": "Ruta de Wwise:",
        "auto_save": "Guardado Automático:",
        "auto_save_interval": "Intervalo de Guardado Automático (minutos):",
        "interface_language": "Idioma de la Interfaz:",
        "theme": "Tema:",
        "dark_theme": "Tema Oscuro",
        "light_theme": "Tema Claro",
        
        # === PERFILES ===
        "profiles": "Perfiles",
        "create_profile": "Crear Perfil Nuevo",
        "delete_profile": "Eliminar Perfil",
        "rename_profile": "Renombrar Perfil",
        "profile_name": "Nombre del Perfil:",
        "active_profile": "Perfil Activo:",
        "switch_profile": "Cambiar Perfil",
        "profile_created": "Perfil creado",
        "profile_deleted": "Perfil eliminado",
        "profile_renamed": "Perfil renombrado",
        "profile_error": "Error de perfil",
        "confirm_delete_profile": "¿Estás seguro de que quieres eliminar este perfil?",
        
        # === DEPURACIÓN ===
        "debug_console": "Consola de Depuración",
        "debug_log": "Registro de Depuración",
        "clear_log": "Limpiar Registro",
        "save_log": "Guardar Registro",
        "copy_log": "Copiar Registro",
        
        # === ACERCA DE ===
        "about_title": "Acerca de",
        "version": "Versión",
        "created_by": "Creado por",
        "contributors": "Colaboradores",
        "license": "Licencia",
        "github": "GitHub",
        
        # === MENSAJES DE ERROR COMUNES ===
        "file_access_error": "Error de acceso al archivo",
        "permission_denied": "Permiso denegado",
        "disk_space_error": "Espacio insuficiente en disco",
        "invalid_file_format": "Formato de archivo inválido",
        "corrupted_file": "Archivo corrupto",
        
        # === MENSAJES DE ESTADO DE SPLASH ===
        "splash_loading_app": "Despertando a Osa...",
        "splash_init_ui": "Iniciando interfaz de usuario...",
        "splash_loading_profiles": "Cargando perfiles...",
        
        # === BÚSQUEDA Y REEMPLAZO ===
        "find_replace_title": "Buscar y Reemplazar",
        "find_what": "Buscar:",
        "replace_with": "Reemplazar con:",
        "match_case": "Coincidir mayúsculas/minúsculas",
        "find_next": "Buscar Siguiente",
        "replace": "Reemplazar",
        "replace_all": "Reemplazar Todo",
        "search_results": "{count} resultados encontrados",
        
        # === MENSAJES DE REBUILD BNK ===
        "rebuild_bnk_index": "Reconstruir Índice BNK del Mod",
        "rebuild_bnk_confirm_title": "Confirmar Reconstrucción",
        "rebuild_bnk_confirm_text": "¿Reconstruir índices BNK del mod basándose en archivos de audio modificados?",
        "rebuilding_mod_bnk": "Reconstruyendo BNK del Mod...",
        "rebuild_complete_title": "Reconstrucción Completa",
        "rebuild_complete_message_details": "¡Reconstrucción completa!\n\nBNKs creados: {created}\nSonidos actualizados: {updated}\nRevertidos: {reverted}",
        
        # === HERRAMIENTAS DIVERSAS ===
        "batch_operations": "Operaciones en Lote",
        "import_audio_batch": "Importar Múltiples Audios...",
        "export_audio_batch": "Exportar Múltiples Audios...",
        "backup_manager": "Administrador de Respaldos",
        "view_backups": "Ver Respaldos",
        "restore_backup": "Restaurar Respaldo",
        "delete_backup": "Eliminar Respaldo",
        
        # === ESTADOS DE CONVERSIÓN ===
        "update_fun_status_1": "Pidiendo pizza de anchoas para la víctima...",
        "update_fun_status_2": "Usando teléfono regurgitado más reciente para robar ahorros bancarios...",
        "update_fun_status_3": "Afilando cuchillos con esponja de última víctima...",
        "update_fun_status_4": "Robando identidades de prisioneros pasados...",
        "update_fun_status_5": "Suplantando identidad de última víctima y troleando sus contactos...",
        "update_fun_status_6": "Tragando bocadillo más reciente... (¡Ñam!)",
        "update_fun_status_7": "Ajustando disfraz de víctima anterior...",
        
        # === INFORMACIÓN DETALLADA DE SOUNDBANKSINFO ===
        "soundbanksinfo_missing_title": "Falta SoundbanksInfo.json",
        "soundbanksinfo_missing_details": "Este archivo es necesario para identificar la mayoría de los archivos de audio. ¿Te gustaría ir a la pestaña 'Actualizador de Recursos' para extraer los archivos más recientes del juego ahora?",
        "go_to_updater": "Ir al Actualizador",
        "continue_anyway": "Continuar de Todas Formas",
        
        # === NOMBRES DE PESTAÑAS ===
        "tab_audio_editor": "Editor de Audio",
        "tab_subtitle_editor": "Editor de Subtítulos",
        "tab_wav_converter": "Convertidor Audio → WEM",
        "tab_wem_processor": "Procesador WEM",
        "tab_resource_updater": "Actualizador de Recursos",
        "tab_localization": "Localización",
        "tab_debug": "Depuración",
        
        # === BOTONES Y TOOLTIPS FALTANTES ===
        "edit_button": "✏ Editar",
        "export_button": "💾 Exportar",
        "delete_mod_button": "🗑 Eliminar Audio de MOD",
        "volume_toolbar_btn": "🔊 Volumen",
        "delete_mod_button": "🗑️ Eliminar",
        "expand_all": "Expandir Todo",
        "collapse_all": "Colapsar Todo",
        "search_placeholder": "Buscar...",
        "show_scanned_files_check": "Mostrar archivos escaneados",
        "stats_label_text": "Estadísticas",
        
        # === ADMINISTRADOR DE PERFILES ===
        "profile_manager_title": "Administrador de Perfiles de Mods",
        "profile_manager_tooltip": "Abrir el Administrador de Perfiles de Mods",
        "edit_profile": "Editar Perfil de Mod",
        "create_profile": "Crear Nuevo Perfil de Mod",
        "create_new_profile_btn": "➕ Crear Nuevo...",
        "add_existing_profile_btn": "📁 Agregar Existente...",
        "import_mod_from_pak": "Importar Mod desde .pak",
        "remove_from_list_btn": "➖ Quitar de la Lista",
        "select_a_profile": "Selecciona un perfil",
        "author_label": "<b>Autor:</b>",
        "version_label": "<b>Versión:</b>",
        "no_description": "<i>Sin descripción.</i>",
        "edit_details_btn": "⚙️ Editar Detalles...",
        "active_profile_btn": "✓ Activo",
        "activate_profile_btn": "Activar Perfil",
        "error_reading_profile": "<i style='color:red;'>No se pudo leer profile.json</i>",
        "error_author": "<i style='color:red;'>Error</i>",
        "error_version": "<i style='color:red;'>Error</i>",
        "profile_name": "Nombre del Perfil:",
        "author": "Autor:",
        "icon_png": "Icono (PNG):",
        "no_icon_selected": "No se seleccionó icono.",
        "select_icon": "Seleccionar Icono",
        "png_images": "Imágenes PNG",
        "validation_error": "Error de Validación",
        "profile_name_empty": "El Nombre del Perfil no puede estar vacío.",
        "project_statistics_title": "Estadísticas del Proyecto",
        
        # === REBUILD BNK ===
        "rebuild_bnk_index": "Reconstruir Índice BNK del Mod",
        "rebuild_bnk_confirm_title": "Reconstruir Índice BNK",
        "rebuild_bnk_confirm_text": "Esto escaneará todos los archivos de audio modificados (.wem) y actualizará forzosamente los registros de tamaño en los archivos .bnk de tu mod para que coincidan.\n\nEsto es útil para corregir inconsistencias después de agregar, eliminar o editar archivos WEM manualmente.\n\n¿Deseas continuar?",
        "rebuilding_mod_bnk": "Reconstruyendo Índice BNK del Mod...",
        "rebuild_complete_title": "Reconstrucción Completa",
        "rebuild_complete_message": "¡Reconstrucción completa!\n\n✅ Re-creados {created} archivo(s) BNK en tu mod desde originales.\n🔄 Actualizadas {updated} entradas para coincidir con tus archivos WEM.\n⚙️ Aplicadas {reverted} configuraciones personalizadas de 'Efectos en Juego'.",
        
        # === EDITOR DE SUBTÍTULOS ===
        "subtitle_editor_tab_title": "Editor de Localización",
        "subtitle_editor_header": "Editor de Localización",
        "subtitle_editor_desc": "Edita localización directamente. Usa la barra de búsqueda global arriba para filtrar resultados.",
        "without_audio_filter": "Sin audio",
        "without_audio_filter_tooltip": "Mostrar solo subtítulos que no tienen archivos de audio correspondientes",
        "modified_only_filter": "Solo modificados",
        "modified_only_filter_tooltip": "Mostrar solo subtítulos que han sido modificados",
        "with_audio_only_filter": "Solo con audio",
        "with_audio_only_filter_tooltip": "Mostrar solo subtítulos que tienen archivos de audio correspondientes",
        "refresh_btn": "🔄 Actualizar",
        "refresh_btn_tooltip": "Actualizar datos de subtítulos desde archivos",
        "key_header": "Clave",
        "original_header": "Original",
        "current_header": "Actual",
        "audio_header": "Audio",
        "edit_selected_btn": "✏ Editar Seleccionado",
        "save_all_changes_btn": "💾 Guardar Todos los Cambios",
        "subtitle_save_success": "¡Todos los cambios de subtítulos han sido guardados!",
        
        # === EXPORTACIÓN DE AUDIO ===
        "export_audio": "Exportar Audio",
        "which_version_export": "¿Qué versión te gustaría exportar?",
        "save_as_wav": "Guardar como WAV",
        "wav_files": "Archivos WAV",
        "batch_export": "Exportación por Lotes",
        "select_output_directory": "Seleccionar Directorio de Salida",
        "exporting_files": "Exportando {count} archivos...",
        "export_results": "Se exportaron {successful} archivos exitosamente.\nOcurrieron {errors} errores.",
        "export_complete": "Exportación Completa",
        
        # === DIÁLOGOS DE GUARDADO ===
        "save_changes_question": "¿Guardar Cambios?",
        "unsaved_changes_message": "Tienes cambios de subtítulos sin guardar. ¿Guardar antes de cerrar?",
        
        # === COMPILACIÓN DE MODS ===
        "mod_not_found_compile": "Archivo de mod no encontrado. ¿Compilarlo primero?",
        "mod_compilation_failed": "Compilación de mod fallida",
        "repak_not_found": "¡repak.exe no encontrado!",
        "compiling_mod": "Compilando Mod",
        "running_repak": "Ejecutando repak...",
        "mod_compiled_successfully": "¡Mod compilado exitosamente!",
        "wemprocces_desc": "Selecciona idioma para renombrar y colocar archivos WEM durante el procesamiento",
        
        # === ARRASTRAR Y SOLTAR ===
        "drop_on_file_msg": "Por favor suelta sobre un archivo de audio específico.",
        "replace_audio_title": "Reemplazar Audio",
        "replace_audio_confirm_msg": "¿Reemplazar audio para:\n{shortname}\n\ncon archivo:\n{filename}?",
        
        # === PROCESAMIENTO ===
        "processing_file_status": "Procesando {filename}...",
        "processing_additional_subs_status": "Procesando subtítulos adicionales...",
        "loaded_subs_from_files_status": "Se cargaron {count} subtítulos de {processed_files} archivos",
        
        # === WEM PROCESSOR ===
        "wem_process_language": "Idioma de Proceso WEM:",
        
        # === MENÚ CONTEXTUAL (Right-click menu) ===
        "quick_load_audio_title": "🎵 Cargar Audio Personalizado Rápido...",
        "quick_load_audio_tooltip": "Reemplaza este audio con tu propio archivo (cualquier formato)",
        "adjust_original_volume_title": "🔊 Ajustar Volumen Original...",
        "adjust_original_volume_tooltip": "Cambia el volumen del audio original antes de reemplazar",
        "toggle_ingame_effects_title": "✨ Alternar Efectos en Juego",
        "toggle_ingame_effects_tooltip": "Habilitar/deshabilitar efectos de audio en el juego para este sonido",
        "marking_menu_title": "🖍 Marcar",
        "export_as_wav": "💾 Exportar como WAV",
        
        # === ACERCA DE (About Dialog) ===
        "about_description": "Una herramienta para gestionar archivos de audio WEM y subtítulos del juego para Outlast Trials, diseñada para modders y equipos de localización.",
        "key_features": "Características Principales",
        "audio_management": "🎵 <b>Gestión de Audio:</b> Reproduce, convierte y organiza archivos WEM",
        "subtitle_editing": "📝 <b>Edición de Subtítulos:</b> Edición fácil con resolución de conflictos",
        "mod_creation": "📦 <b>Creación de Mods:</b> Compilación y despliegue de mods con un clic",
        "multi_language": "🌍 <b>Multiidioma:</b> Soporte para más de 14 idiomas",
        "modern_ui": "🎨 <b>Interfaz:</b> Interfaz limpia con temas oscuro/claro",
        "technology_stack": "Stack Tecnológico",
        "built_with": "Construido con Python 3 y PyQt5, utilizando:",
        "unreal_locres_tool": "UnrealLocres - para editar archivos .locres",
        "vgmstream_tool": "vgmstream - para reproducir audio WEM",
        "repak_tool": "repak - para empaquetar archivos .pak",
        "ffmpeg_tool": "FFmpeg - para conversión de audio",
        "credits_tab": "Créditos",
        "license_tab": "Licencia",
        "original_author": "Autor",
        "original_author_desc": "Bezna",
        "developers_label": "Desarrolladores:",
        "developers_names": "Bezna",
        "polish_translator_label": "Probador/Traductor Polaco:",
        "polish_translator_name": "Alaneg",
        "spanish_translator_label": "Traductora Española:",
        "spanish_translator_name": "Mercedes",
        "special_thanks": "Agradecimientos Especiales",
        "contributors": "A todos los contribuidores y la comunidad de modding",
        "credits": "Créditos",
        "license": "Licencia",
        "open_source": "Proyecto de Código Abierto",
        "mit_license": "Licencia MIT - Libre de usar, modificar y distribuir",
        "development_team": "Equipo de Desarrollo",
        "lead_developer": "<b>Desarrolladores Principales:</b> Bezna",
        "vgmstream_thanks": "Equipo de vgmstream - Por las herramientas de conversión de audio",
        "unreal_locres_thanks": "Desarrolladores de UnrealLocres - Por el soporte de localización",
        "hypermetric_thanks": "hypermetric - Por el empaquetado de mods",
        "red_barrels_thanks": "Red Barrels - Por crear Outlast Trials",
        "open_source_libraries": "Bibliotecas de Código Abierto",
        "pyqt5_lib": "PyQt5 - Framework de GUI",
        "python_lib": "Biblioteca Estándar de Python",
        "software_disclaimer": "Este software se proporciona \"tal cual\" sin garantía de ningún tipo. Úselo bajo su propio riesgo.",
        "license_agreement": "Acuerdo de Licencia",
        "copyright_notice": "Copyright (c) 2026 Editor de Audio de Outlast Trials",
        "mit_license_text": "Por la presente se concede permiso, libre de cargos, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados (el \"Software\"), a utilizar el Software sin restricción, incluyendo sin limitación los derechos a usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar, y/o vender copias del Software, y a permitir a las personas a las que se les proporcione el Software a hacer lo mismo, sujeto a las siguientes condiciones:\n\nEl aviso de copyright anterior y este aviso de permiso se incluirán en todas las copias o partes sustanciales del Software.\n\nEL SOFTWARE SE PROPORCIONA \"COMO ESTÁ\", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A GARANTÍAS DE COMERCIALIZACIÓN, IDONEIDAD PARA UN PROPÓSITO PARTICULAR E INCUMPLIMIENTO. EN NINGÚN CASO LOS AUTORES O PROPIETARIOS DE DERECHOS DE AUTOR SERÁN RESPONSABLES DE NINGUNA RECLAMACIÓN, DAÑOS U OTRAS RESPONSABILIDADES, YA SEA EN UNA ACCIÓN DE CONTRATO, AGRAVIO O CUALQUIER OTRO MOTIVO, DERIVADAS DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE O SU USO U OTRO TIPO DE ACCIONES EN EL SOFTWARE.",
        
        # === DIÁLOGO DE ACTUALIZACIÓN (Update Dialog) ===
        "new_version_available": "Nueva Versión Disponible",
        "current_version": "Versión Actual",
        "latest_version": "Última Versión",
        "release_notes": "Notas de la Versión",
        "download": "Descargar",
        "skip_version": "Omitir Esta Versión",
        "remind_later": "Recordar Después",
        
        # === AJUSTE DE VOLUMEN (Volume Adjustment) ===
        "volume_adjustment_title": "Ajustar Volumen de Audio",
        "volume_adjustment_desc": "Ajusta el volumen del audio antes de guardarlo",
        "preview": "Vista Previa",
        "apply": "Aplicar",
        "volume_change": "Cambio de Volumen:",
        
        # === ACTUALIZADOR DE RECURSOS (Resource Updater) ===
        "resource_updater_tab": "Actualizador de Recursos",
        "pak_file_path": "Ruta del Archivo .pak:",
        "browse_pak": "Examinar .pak",
        "extract_audio_files": "Extraer Archivos de Audio",
        "extract_localization_files": "Extraer Archivos de Localización",
        "start_update": "Iniciar Actualización",
        "cancel_update": "Cancelar",
        "extracting": "Extrayendo...",
        "extraction_progress": "Progreso de Extracción:",
        "select_pak_file": "Seleccionar archivo .pak del juego",
        "pak_files": "Archivos PAK",
        "extraction_cancelled": "Extracción cancelada",
        "extraction_failed": "Extracción fallida",
        "extraction_success": "¡Extracción exitosa!",
        "files_extracted": "Archivos extraídos exitosamente",
        
        # === PROCESO DE REBUILD (Rebuild Process Messages) ===
        "scanning_modified_files": "Escaneando archivos modificados...",
        "found_modified_files": "Se encontraron {count} archivos WEM modificados",
        "mapping_to_bnk": "Mapeando archivos a BNKs padre...",
        "updating_bnk_file": "Actualizando {filename}...",
        "rebuild_progress": "Progreso de Reconstrucción: {percent}%",
        "checking_size_mismatches": "Verificando discrepancias de tamaño...",
        "fixing_mismatches": "Corrigiendo discrepancias...",
        "auto_fixed": "Se corrigieron automáticamente {count} discrepancias de tamaño",
        
        # === WEM PROCESSOR (Old Tool) ===
        "wem_processor_tab": "Procesador WEM",
        "select_wem_files": "Seleccionar Archivos WEM",
        "wem_files": "Archivos WEM",
        "add_wem_files": "Agregar Archivos WEM",
        "remove_selected": "Quitar Seleccionados",
        "process_files": "Procesar Archivos",
        "processing": "Procesando...",
        "wem_process_complete": "Procesamiento WEM Completo",
        
        # === BOTONES COMUNES (Common Buttons) ===
        "ok": "Aceptar",
        "yes": "Sí",
        "no": "No",
        "apply": "Aplicar",
        "reset": "Restablecer",
        "default": "Predeterminado",
        "advanced": "Avanzado",
        "basic": "Básico",
        
        # === TEMAS (Themes) ===
        "light": "Claro",
        "dark": "Oscuro",
        "theme_changed": "Tema cambiado. Reinicia la aplicación para ver los cambios completos.",
        
        # === ETIQUETAS DE INFORMACIÓN ===
        "information": "Información",
        "details": "Detalles",
        "options": "Opciones",
        "preferences": "Preferencias",
        "general": "General",
        "appearance": "Apariencia",
        
        # === MENÚ CONTEXTUAL - FALTANTES ===
        "play_mod": "▶ Reproducir Mod",
        "restore_from_backup_title": "🔄 Restaurar desde Respaldo",
        "adjust_mod_volume_title": "🔊 Ajustar Volumen del Mod...",
        "trim_mod_audio_title": "✂️ Recortar Audio del Mod...",
        
        # === ACTUALIZADOR DE RECURSOS - COMPLETO ===
        "updater_header": "Actualizar Recursos del Juego",
        "pak_file_path_label": "1. Ruta del archivo .pak:",
        "select_resources_group": "2. Selecciona Recursos a Actualizar",
        "update_audio_check": "Actualizar Archivos de Audio (Wems)",
        "update_localization_check": "Actualizar Archivos de Localización",
        "start_update_btn": "Iniciar Actualización",
        "update_process_group": "3. Proceso de Actualización",
        "update_log_ready": "Listo para iniciar el proceso de actualización.",
        "unpacking_files_from": "Desempaquetando archivos de {pak_name}...",
        "update_step_unpacking": "Desempaquetando archivos del archivo del juego...",
        "extracting_audio": "Extrayendo archivos de audio...",
        "extracting_localization": "Extrayendo archivos de localización...",
        "copying_files": "Copiando archivos a carpetas de destino...",
        "update_audio_success": "Archivos de audio actualizados exitosamente",
        "update_localization_success": "Archivos de localización actualizados exitosamente",
        "update_complete_msg": "Actualización completa. Los recursos del juego se han actualizado.",
        "update_error_msg": "Error durante la actualización: {error}",
        
        # === PROCESO DE COMPILACIÓN ===
        "compiling_mod_pak": "Compilando mod a .pak...",
        "packing_files": "Empaquetando archivos...",
        "creating_pak": "Creando archivo .pak...",
        "mod_pak_created": "Archivo .pak del mod creado exitosamente",
        "preparing_files": "Preparando archivos para compilación...",
        "compiling_progress": "Progreso de Compilación: {percent}%",
        "compression_step": "Comprimiendo archivos...",
        "finalizing_pak": "Finalizando archivo .pak...",
        
        # === ATAJOS DE TECLADO ===
        "shortcut_play_mod_action": "Reproducir Audio del Mod",
        "shortcut_play_mod_desc": "Reproduce la versión modificada del archivo de audio seleccionado.",
        "shortcut_play_original_action": "Reproducir Audio Original",
        "shortcut_play_original_desc": "Reproduce la versión original del archivo de audio seleccionado.",
        
        # === CONFIGURACIÓN - FALTANTES ===
        "subtitle_language": "Idioma de Subtítulos:",
        "quick_load_settings_group": "Configuración de Carga Rápida",
        "quick_load_mode_label": "Elige modo de conversión para Cargar Audio Personalizado Rápido:",
        "quick_load_strict": "Modo Estricto - Falla si es demasiado grande",
        "quick_load_adaptive": "Modo Adaptativo - Ajusta calidad automáticamente",
        "conversion_method_group": "Método de Conversión",
        "bnk_overwrite_radio": "Sobreescritura BNK (Recomendado)",
        "bnk_overwrite_tooltip": "Convierte con calidad máxima y sobreescribe el tamaño del archivo en el archivo .bnk.",
        "adaptive_size_matching_radio": "Coincidencia Adaptativa de Tamaño",
        "adaptive_size_matching_tooltip": "Ajusta la calidad del audio para coincidir con el tamaño del archivo WEM original.",
        
        # === MENSAJES DE COMPILACIÓN DIVERTIDOS ===
        "compiling_step_1": "Limpiando desorden técnico...",
        "compiling_step_2": "Hackeando archivos del juego... (En realidad solo usando FModel)",
        "compiling_step_3": "Organizando nueva estructura de audio...",
        "compiling_step_4": "Pidiéndole ayuda a Kitty...",
        "compiling_step_5": "Ayudando a Amelia a planear un nuevo escape...",
        "compiling_step_6": "Diciéndole a Maddie por #97 vez que un ladrillo no es comida...",
        "compiling_step_7": "Relajándose con Neil mientras Easterman pierde la cabeza...",
        
        # === MENSAJES DE ACTUALIZACIÓN DIVERTIDOS ===
        "update_fun_status_1": "Viendo a Avellanos darle una lección a Easterman...",
        "update_fun_status_2": "Intentando cortar los barrotes de la sala de sueño...",
        "update_fun_status_3": "Preparando la lanzadera para las próximas pruebas...",
        "update_fun_status_4": "Entrenando nuevos impostores para la invasión...",
        "update_fun_status_5": "Conteniendo los activos principales antes de que se aviven...",
        "update_fun_status_6": "Advirtiendo a los reactivos sobre los cambios más recientes...",
        "update_fun_status_7": "Finalizando proceso de actualización...",
        
        # === EASTER EGG ===
        "easter_egg_title": "¡Fuiste asustado por Mooneon!",
        "easter_egg_loading": "Cargando susto...",
        "easter_egg_message": "Te advertí que Mooneon te asustaría.",
    }
}
class ResourceUpdaterThread(QtCore.QThread):

    major_step_update = QtCore.pyqtSignal(str)
    log_update = QtCore.pyqtSignal(str)

    finished = QtCore.pyqtSignal(str, str)

    def __init__(self, parent_app, pak_path, update_audio, update_loc):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.tr = self.parent_app.tr
        self.pak_path = pak_path
        self.update_audio = update_audio
        self.update_loc = update_loc
        self.aes_key = "0x613E92E0F3CE880FC652EC86254E2581126AE86D63BA46550FB2CE0EC2EDA439"
        self.temp_extract_path = os.path.join(self.parent_app.base_path, "temp_extracted_resources")
        self._is_cancelled = False
        self.repak_process = None

    def cancel(self):
        self._is_cancelled = True
        if self.repak_process and self.repak_process.poll() is None:
            self.log_update.emit(f"--- {self.tr('update_cancelled_by_user')} ---")
            self.repak_process.terminate()
            DEBUG.log("repak.exe process terminated by user.")

    def run(self):
        status = "failure"
        message = "An unknown error occurred."
        try:
            self._cleanup_previous_session()
            if self._is_cancelled: return

            updated_resources = []

            if self.update_audio:
                if not self._unpack_and_process_audio():
                    if not self._is_cancelled: message = self.tr("unpack_failed")
                    return
                updated_resources.append("Audio (Wems)")
            
            if self._is_cancelled: return

            if self.update_loc:
                if not self._unpack_and_process_loc():
                    if not self._is_cancelled: message = self.tr("unpack_failed")
                    return
                updated_resources.append("Localization")

            if self._is_cancelled: return

            self.major_step_update.emit(self.tr("update_step_finishing"))
            self.log_update.emit(f"\n--- {self.tr('done')} ---")
            status = "success"
            message = self.tr("update_complete_msg").format(updated_resources="\n- ".join(updated_resources))

        except Exception as e:
            status = "failure"
            message = str(e)
        finally:
            if self._is_cancelled:
                status = "cancelled"
                message = self.tr("update_cancelled_by_user")
            
            self._cleanup_previous_session()
            self.finished.emit(status, message)

    def _cleanup_previous_session(self):
        self.log_update.emit("Preparing workspace...")
        if PSUTIL_AVAILABLE:
            for proc in psutil.process_iter(['name', 'exe', 'pid']):
                try:
                    if proc.info['name'].lower() == 'repak.exe' and os.path.normpath(proc.info['exe']) == os.path.normpath(self.parent_app.repak_path):
                        self.log_update.emit(f"Terminating lingering repak.exe (PID: {proc.pid})...")
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        if os.path.exists(self.temp_extract_path):
            self.log_update.emit("Cleaning up temporary directory...")
            try:
                shutil.rmtree(self.temp_extract_path)
                time.sleep(0.1)
            except Exception as e:
                self.log_update.emit(f"Warning: Could not clean temp directory: {e}")

    def _run_repak(self, path_to_unpack):
        self.log_update.emit(self.tr("unpacking_path").format(path_to_unpack=path_to_unpack))
        command = [self.parent_app.repak_path, "-a", self.aes_key, "unpack", self.pak_path, "-i", path_to_unpack, "-o", self.temp_extract_path]
        
        self.log_update.emit(f"\n-> {self.tr('update_unpacking_long_wait')}")

        try:
            self.repak_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore'
            )
            stdout, stderr = self.repak_process.communicate()
            
            full_output = (stdout.strip() + "\n" + stderr.strip()).strip()
            if full_output:
                self.log_update.emit(full_output)

            if self._is_cancelled:
                self.log_update.emit("Repak process was cancelled.")
                return False

            if self.repak_process.returncode != 0:
                self.log_update.emit(self.tr("unpack_failed"))
                return False
            
            return True
        finally:
            self.repak_process = None

    def _unpack_and_process_audio(self):
        self.major_step_update.emit(self.tr("update_step_unpacking"))
        source_path_in_pak = "OPP/Content/WwiseAudio/Windows"
        if not self._run_repak(source_path_in_pak): return False
        if self._is_cancelled: return False
        
        extracted_content_path = os.path.join(self.temp_extract_path, "OPP", "Content", "WwiseAudio", "Windows")
        
        self.major_step_update.emit(self.tr("update_step_clearing"))
        if os.path.exists(self.parent_app.wem_root): shutil.rmtree(self.parent_app.wem_root)
        os.makedirs(self.parent_app.wem_root)
        
        self.major_step_update.emit(self.tr("update_step_moving"))

        sfx_path = os.path.join(self.parent_app.wem_root, "SFX")
        os.makedirs(sfx_path, exist_ok=True)

        for root, dirs, files in os.walk(extracted_content_path):
            if self._is_cancelled: return False
            
            rel_path = os.path.relpath(root, extracted_content_path)
            
            for file in files:
                src_file_path = os.path.join(root, file)
                dest_folder = ""

                if rel_path == ".": 
 
                    dest_folder = sfx_path
                elif rel_path == "Media":
             
                    dest_folder = sfx_path
                elif rel_path.startswith("Media"):
               
                    lang_name = os.path.basename(rel_path)
                    dest_folder = os.path.join(self.parent_app.wem_root, lang_name)
                else:
              
                    lang_name = rel_path
                    dest_folder = os.path.join(self.parent_app.wem_root, lang_name)

                os.makedirs(dest_folder, exist_ok=True)
                
                try:
                    shutil.move(src_file_path, os.path.join(dest_folder, file))
                except shutil.Error:
                    pass 
        return True
    def _unpack_and_process_loc(self):
        self.major_step_update.emit(self.tr("update_step_unpacking"))
        if not self._run_repak("OPP/Content/Localization"): return False
        if self._is_cancelled: return False

        extracted_content_path = os.path.join(self.temp_extract_path, "OPP", "Content", "Localization")
        loc_root = os.path.join(self.parent_app.base_path, "Localization")
        
        self.major_step_update.emit(self.tr("update_step_clearing"))
        if os.path.exists(loc_root): shutil.rmtree(loc_root)

        self.major_step_update.emit(self.tr("update_step_moving"))
        shutil.move(extracted_content_path, loc_root)
        return True
class StatisticsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        
        self.setWindowTitle(self.tr("project_statistics_title"))
        self.setMinimumSize(600, 500)

        self.layout = QtWidgets.QVBoxLayout(self)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(QtWidgets.QLabel(f"<b>{self.tr('mod_profile_label')}</b>"))
        self.profile_name_label = QtWidgets.QLabel("...")
        self.profile_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.profile_name_label)
        header_layout.addStretch()
        self.recalculate_btn = QtWidgets.QPushButton(self.tr("recalculate_btn"))
        self.recalculate_btn.clicked.connect(self.calculate_statistics)
        header_layout.addWidget(self.recalculate_btn)
        self.layout.addLayout(header_layout)
        
        general_group = QtWidgets.QGroupBox(self.tr("general_stats_group"))
        general_layout = QtWidgets.QFormLayout(general_group)
        self.audio_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.subtitle_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.mod_size_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        general_layout.addRow(self.tr("total_audio_files"), self.audio_files_label)
        general_layout.addRow(self.tr("total_subtitle_files"), self.subtitle_files_label)
        general_layout.addRow(self.tr("total_mod_size"), self.mod_size_label)
        self.layout.addWidget(general_group)
        
        subtitle_group = QtWidgets.QGroupBox(self.tr("subtitle_stats_group"))
        subtitle_layout = QtWidgets.QFormLayout(subtitle_group)
        self.modified_subs_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.new_subs_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.affected_langs_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        subtitle_layout.addRow(self.tr("modified_subtitle_entries"), self.modified_subs_label)
        subtitle_layout.addRow(self.tr("new_subtitle_entries"), self.new_subs_label)
        subtitle_layout.addRow(self.tr("total_languages_affected"), self.affected_langs_label)
        self.layout.addWidget(subtitle_group)
        
        files_group = QtWidgets.QGroupBox(self.tr("modified_files_group"))
        files_layout = QtWidgets.QVBoxLayout(files_group)
        self.files_list_widget = QtWidgets.QTextEdit()
        self.files_list_widget.setReadOnly(True)
        files_layout.addWidget(self.files_list_widget)
        
        copy_btn = QtWidgets.QPushButton(self.tr("copy_list_btn"))
        copy_btn.clicked.connect(self.copy_file_list)
        files_layout.addWidget(copy_btn, 0, QtCore.Qt.AlignRight)
        self.layout.addWidget(files_group)
        
        QtCore.QTimer.singleShot(100, self.calculate_statistics)

    def calculate_statistics(self):
        self.recalculate_btn.setEnabled(False)
        self.profile_name_label.setText(self.parent_app.active_profile_name or "N/A")
        
        if not self.parent_app.mod_p_path or not self.parent_app.active_profile_name:
            error_msg = self.tr("no_profile_active_for_stats")
            self.audio_files_label.setText(error_msg)
            self.subtitle_files_label.setText(error_msg)
            self.mod_size_label.setText(error_msg)
            self.modified_subs_label.setText(error_msg)
            self.new_subs_label.setText(error_msg)
            self.affected_langs_label.setText(error_msg)
            self.files_list_widget.setText(error_msg)
            return

        mod_audio_path = os.path.join(self.parent_app.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
        mod_loc_path = os.path.join(self.parent_app.mod_p_path, "OPP", "Content", "Localization")
        
        audio_files = []
        subtitle_files = []
        total_size = 0

        if os.path.exists(self.parent_app.mod_p_path):
            for root, dirs, files in os.walk(self.parent_app.mod_p_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    
                    rel_path = os.path.relpath(file_path, self.parent_app.mod_p_path)
                    if file.endswith(".wem"):
                        audio_files.append(rel_path)
                    elif file.endswith(".locres"):
                        subtitle_files.append(rel_path)
        
        self.audio_files_label.setText(str(len(audio_files)))
        self.subtitle_files_label.setText(str(len(subtitle_files)))
        
        if total_size > 1024 * 1024:
            self.mod_size_label.setText(f"{total_size / (1024*1024):.2f} MB")
        else:
            self.mod_size_label.setText(f"{total_size / 1024:.2f} KB")

        modified_count = len(self.parent_app.modified_subtitles)
        new_count = sum(1 for key in self.parent_app.modified_subtitles if key not in self.parent_app.original_subtitles)
        self.modified_subs_label.setText(f"{modified_count} ({modified_count - new_count} existing)")
        self.new_subs_label.setText(str(new_count))
        
        affected_langs = set()
        lang_to_check = self.parent_app.settings.data.get("subtitle_lang")
        if self.parent_app.modified_subtitles:
             affected_langs.add(lang_to_check)
        self.affected_langs_label.setText(", ".join(sorted(affected_langs)) if affected_langs else "0")

        all_files = sorted(audio_files) + sorted(subtitle_files)
        self.files_list_widget.setText("\n".join(all_files))
        
        self.recalculate_btn.setEnabled(True)

    def copy_file_list(self):
        QtWidgets.QApplication.clipboard().setText(self.files_list_widget.toPlainText())
        self.parent_app.statusBar().showMessage(self.tr("list_copied_msg"), 2000)
class DebugLogger:
    def __init__(self):
        self.logs_in_memory = []
        self.callbacks = []
        self.log_file_path = None

    def setup_logging(self, base_path):
        try:
            data_path = os.path.join(base_path, "data")
            os.makedirs(data_path, exist_ok=True)
            
            self.log_file_path = os.path.join(data_path, "session_log.txt")
            previous_log_path = os.path.join(data_path, "previous_session_log.txt")
            
            if os.path.exists(self.log_file_path):
                if os.path.exists(previous_log_path):
                    os.remove(previous_log_path)
                os.rename(self.log_file_path, previous_log_path)

            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

        except Exception as e:
            print(f"FATAL: Could not set up file logging: {e}")
            self.log_file_path = None

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.logs_in_memory.append(log_entry)
        print(log_entry)
        
        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
            except Exception as e:
                print(f"ERROR: Could not write to log file: {e}")
        
        for callback in self.callbacks:
            callback(log_entry)
            
    def add_callback(self, callback):
        self.callbacks.append(callback)
        
    def get_logs(self):
        return "\n".join(self.logs_in_memory)

DEBUG = DebugLogger()
@dataclass
class SoundEntry:
    offset: int
    sound_id: int
    source_id: int
    file_size: int
    override_fx: bool
class BNKEditor:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        self.data = None
        self._sound_map = None
        self.load_file()

    def _build_sound_map(self):

        if self._sound_map is not None:
            return

        DEBUG.log(f"Building sound map for {self.file_path.name}...")
        self._sound_map = {}

        search_pattern = b'\x01\x00\x04\x00\x00'
        offset = 0
        while True:
            try:
                offset = self.data.index(search_pattern, offset)
                
                id_offset = offset + 5
                if id_offset + 4 <= len(self.data):
                    source_id = struct.unpack('<I', self.data[id_offset:id_offset+4])[0]
                    
                    entry_start_offset = offset - 4 
                    
                    if source_id not in self._sound_map:
                        self._sound_map[source_id] = []
                    self._sound_map[source_id].append(entry_start_offset)

                offset += len(search_pattern)
            except ValueError:
                break 
        DEBUG.log(f"Sound map for {self.file_path.name} built. Found {len(self._sound_map)} unique sound IDs.")

    def load_file(self):
        with open(self.file_path, 'rb') as f:
            self.data = bytearray(f.read())

    def save_file(self, output_path: Optional[str] = None):
        if output_path is None:
            output_path = self.file_path
            
        with open(output_path, 'wb') as f:
            f.write(self.data)

    def find_sound_by_source_id(self, source_id: int, expected_size: Optional[int] = None) -> List[SoundEntry]:
        self._build_sound_map() 
        
        offsets = self._sound_map.get(source_id)
        if not offsets:
            return []
        
        found_entries = []
        for offset in offsets:
            entry = self._parse_sound_entry(offset)
            if entry:
                if expected_size is None or entry.file_size == expected_size:
                    found_entries.append(entry)
        return found_entries
        
    def find_all_sounds(self) -> List[SoundEntry]:
     
        self._build_sound_map()
        all_entries = []
        for source_id, offsets in self._sound_map.items():
            for offset in offsets:
                entry = self._parse_sound_entry(offset)
                if entry:
                    all_entries.append(entry)
        return all_entries

    def _parse_sound_entry(self, offset: int) -> Optional[SoundEntry]:
        try:
            if offset + 19 > len(self.data):
                return None
            
            sound_id = struct.unpack('<I', self.data[offset:offset+4])[0]

            source_id_offset = offset + 9
            source_id = struct.unpack('<I', self.data[source_id_offset:source_id_offset+4])[0]
            
            file_size_offset = source_id_offset + 4
            file_size = struct.unpack('<I', self.data[file_size_offset:file_size_offset+4])[0]
            
            fx_flag_offset = file_size_offset + 5 
            override_fx = self.data[fx_flag_offset] == 0x01
            
            return SoundEntry(
                offset=offset,
                sound_id=sound_id,
                source_id=source_id,
                file_size=file_size,
                override_fx=override_fx
            )
        except (struct.error, IndexError):
            return None
            
    def modify_sound(self, source_id: int, override_fx: Optional[bool] = None, 
                     new_size: Optional[int] = None, find_by_size: Optional[int] = None):
        entries = self.find_sound_by_source_id(source_id, find_by_size)
        
        if not entries:
            # DEBUG.log(f"Sound with Source ID {source_id} (and size {find_by_size}) not found in BNK", "WARNING")
            return False
            
        modified = False
        for entry in entries:
            # DEBUG.log(f"Modifying entry in BNK at offset 0x{entry.offset:08X} (ID: {entry.source_id}, current size: {entry.file_size})")

            if override_fx is not None:
                fx_flag_offset = entry.offset + 18
                new_byte = 0x01 if override_fx else 0x00
                self.data[fx_flag_offset] = new_byte
                # DEBUG.log(f"  Override FX changed to: {override_fx}")
                modified = True
                
            if new_size is not None:
                if new_size > 0xFFFFFFFF:
                    # DEBUG.log(f"  Size {new_size} is too large", "ERROR")
                    continue
                    
                file_size_offset = entry.offset + 13
                struct.pack_into('<I', self.data, file_size_offset, new_size)
                # DEBUG.log(f"  File size changed from {entry.file_size} to: {new_size}")
                modified = True
                
        return modified    
class BnkInfoLoader(QtCore.QThread):
    info_loaded = QtCore.pyqtSignal(int, object, object)  # source_id, original_info, modified_info

    def __init__(self, parent, source_id, bnk_files_info, mod_p_path, wems_base_path):
        super().__init__(parent)
        self.source_id = source_id
        self.bnk_files_info = bnk_files_info 
        self.mod_p_path = mod_p_path
        self.wems_base_path = wems_base_path
        self.parent_app = parent
        
    def run(self):
        original_bnk_info, original_bnk_path = self.find_info_in_bnks(self.bnk_files_info, self.source_id, is_mod=False)
        if original_bnk_info:
            DEBUG.log(f"Original information for ID {self.source_id} found in BNK: {os.path.basename(original_bnk_path)}")
        else:
            DEBUG.log(f"Original information for ID {self.source_id} not found in any BNK.")

        mod_bnk_paths_info = []
        for bnk_path, bnk_type in self.bnk_files_info:
            if bnk_type == 'sfx':
                base_for_relpath = os.path.join(self.wems_base_path, "SFX")
                rel_path = os.path.relpath(bnk_path, base_for_relpath)
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                base_for_relpath = self.wems_base_path
                rel_path = os.path.relpath(bnk_path, base_for_relpath)
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            
            if os.path.exists(mod_bnk_path):
                mod_bnk_paths_info.append((mod_bnk_path, bnk_type))
        
        modified_bnk_info, modified_bnk_path = self.find_info_in_bnks(mod_bnk_paths_info, self.source_id, is_mod=True)
        if modified_bnk_info:
            DEBUG.log(f"Modified information for ID {self.source_id} found in BNK: {os.path.basename(modified_bnk_path)}")
        else:
            if mod_bnk_paths_info:
                 DEBUG.log(f"Modified information for ID {self.source_id} not found.")

        self.info_loaded.emit(self.source_id, original_bnk_info, modified_bnk_info)

    def find_info_in_bnks(self, bnk_paths_info, source_id, is_mod=False):
        cache_name = 'bnk_cache_mod' if is_mod else 'bnk_cache_orig'
        cache = getattr(self.parent_app, cache_name, {})
        
        for bnk_path, bnk_type in bnk_paths_info:
            if bnk_path in cache and source_id in cache[bnk_path]:
                return cache[bnk_path][source_id], bnk_path

            try:
                editor = BNKEditor(bnk_path)
                entries = editor.find_sound_by_source_id(source_id)
                if entries:
                    entry = entries[0]
                    
                    if bnk_path not in cache:
                        cache[bnk_path] = {}
                    cache[bnk_path][source_id] = entry
                    setattr(self.parent_app, cache_name, cache)
                    
                    return entry, bnk_path
            except Exception as e:
                DEBUG.log(f"Error reading BNK {bnk_path}: {e}", "WARNING")
                continue
        
        return None, None    
class AudioToWavConverter:
    
    SUPPORTED_FORMATS = ['.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.webm']
    
    def __init__(self, ffmpeg_path=None):
        self.ffmpeg_path = ffmpeg_path or self.find_ffmpeg()
        
    def find_ffmpeg(self):
       
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        ffmpeg_paths = [
            os.path.join(base_path, "data", "ffmpeg.exe"),
            os.path.join(base_path, "libs", "ffmpeg.exe"),
            "ffmpeg.exe",  
            "ffmpeg"
        ]
        
        for path in ffmpeg_paths:
            if os.path.exists(path) or shutil.which(path):
                return path
                
        return None
        
    def is_available(self):
        return self.ffmpeg_path is not None
        
    def is_supported_format(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
        
    def convert_to_wav(self, input_file, output_wav=None, sample_rate=48000):
        if not self.is_available():
            return False, "FFmpeg not found"
            
        if output_wav is None:
            output_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-acodec', 'pcm_s16le',
                '-ar', str(sample_rate),
                '-ac', '2',  # Stereo
                '-y',  # Overwrite
                output_wav
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return True, output_wav
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
class VolumeProcessor:
    def __init__(self):
        self.has_numpy = False
        self.has_scipy = False
        self.np = None
        self.wavfile = None
        try:
            DEBUG.log("VolumeProcessor: trying to import numpy...", "INFO")
            import numpy as np
            DEBUG.log("VolumeProcessor: numpy imported successfully", "INFO")
            self.np = np
        except Exception as e:
            import traceback
            DEBUG.log(f"VolumeProcessor: NumPy import error: {e}", "ERROR")
            DEBUG.log(traceback.format_exc(), "ERROR")
            self.np = None

        try:
            DEBUG.log("VolumeProcessor: trying to import scipy.io.wavfile...", "INFO")
            import scipy.io.wavfile
            DEBUG.log("VolumeProcessor: scipy.io.wavfile imported successfully", "INFO")
            self.wavfile = scipy.io.wavfile
        except Exception as e:
            import traceback
            DEBUG.log(f"VolumeProcessor: SciPy import error: {e}", "ERROR")
            DEBUG.log(traceback.format_exc(), "ERROR")
            self.wavfile = None

        if self.np is not None:
            self.has_numpy = True
        if self.wavfile is not None:
            self.has_scipy = True

        DEBUG.log(f"VolumeProcessor: has_numpy={self.has_numpy}, has_scipy={self.has_scipy}", "INFO")

    def is_available(self):
        DEBUG.log(f"VolumeProcessor.is_available: {self.has_numpy=}, {self.has_scipy=}", "INFO")
        return self.has_numpy and self.has_scipy

    def analyze_audio(self, wav_path):
        DEBUG.log(f"VolumeProcessor.analyze_audio: {wav_path=}", "INFO")
        if not self.is_available():
            DEBUG.log("VolumeProcessor.analyze_audio: not available", "WARNING")
            return None
        try:
            sample_rate, data = self.wavfile.read(wav_path)
            DEBUG.log(f"VolumeProcessor.analyze_audio: sample_rate={sample_rate}, dtype={data.dtype}", "INFO")
            if data.dtype == self.np.int16:
                max_amp = 32767
            elif data.dtype == self.np.int32:
                max_amp = 2147483647
            elif data.dtype == self.np.uint8:
                max_amp = 255
            else:
                max_amp = 1.0
            data_float = data.astype(self.np.float64)
            rms = self.np.sqrt(self.np.mean(data_float**2))
            rms_percent = (rms / max_amp) * 100
            peak = self.np.max(self.np.abs(data_float))
            peak_percent = (peak / max_amp) * 100
            max_increase_without_clipping = (max_amp / peak) * 100 if peak > 0 else 100
            DEBUG.log(f"VolumeProcessor.analyze_audio: rms={rms}, peak={peak}", "INFO")
            return {
                'sample_rate': sample_rate,
                'duration_seconds': len(data) / sample_rate,
                'rms': rms,
                'rms_percent': rms_percent,
                'peak': peak,
                'peak_percent': peak_percent,
                'max_amp': max_amp,
                'dtype': data.dtype,
                'max_increase': max_increase_without_clipping
            }
        except Exception as e:
            import traceback
            DEBUG.log(f"Error analyzing audio: {e}", "ERROR")
            DEBUG.log(traceback.format_exc(), "ERROR")
            return None

    def change_volume(self, input_wav, output_wav, volume_percent):
        DEBUG.log(f"VolumeProcessor.change_volume: {input_wav=}, {output_wav=}, {volume_percent=}", "INFO")
        if not self.is_available():
            DEBUG.log("VolumeProcessor.change_volume: not available", "WARNING")
            return False, "NumPy/SciPy not installed"
        try:
            sample_rate, data = self.wavfile.read(input_wav)
            original_dtype = data.dtype
            if data.dtype == self.np.int16:
                max_amp = 32767
            elif data.dtype == self.np.int32:
                max_amp = 2147483647
            elif data.dtype == self.np.uint8:
                max_amp = 255
            else:
                max_amp = 1.0
            data_float = data.astype(self.np.float64)
            current_rms = self.np.sqrt(self.np.mean(data_float**2))
            current_peak = self.np.max(self.np.abs(data_float))
            scale = volume_percent / 100.0
            new_data = data_float * scale
            clipped_samples = self.np.sum(self.np.abs(new_data) > max_amp)
            clipped_percent = 0
            if clipped_samples > 0:
                clipped_percent = (clipped_samples / len(new_data)) * 100
            new_data = self.np.clip(new_data, -max_amp, max_amp - 1)
            final_rms = self.np.sqrt(self.np.mean(new_data**2))
            actual_change = (final_rms / current_rms) * 100 if current_rms > 0 else 100
            new_data = new_data.astype(original_dtype)
            self.wavfile.write(output_wav, sample_rate, new_data)
            result_info = {
                'actual_change': actual_change,
                'clipped_percent': clipped_percent,
                'final_rms': final_rms,
                'final_peak': self.np.max(self.np.abs(new_data))
            }
            DEBUG.log(f"VolumeProcessor.change_volume: result_info={result_info}", "INFO")
            return True, result_info
        except Exception as e:
            import traceback
            DEBUG.log(f"Error changing volume: {e}", "ERROR")
            DEBUG.log(traceback.format_exc(), "ERROR")
            return False, str(e)
class WemVolumeEditDialog(QtWidgets.QDialog):
    """Dialog for editing WEM file volume"""
    
    def __init__(self, parent, entry, lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entry = entry
        self.lang = lang
        self.is_mod = is_mod
        self.volume_processor = VolumeProcessor()
        self.temp_files = []
        self.current_analysis = None
        
        self.setWindowTitle(self.tr("volume_editor_title").format(shortname=entry.get('ShortName', '')))
        self.setMinimumSize(600, 500)
        
        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()
        
        self.create_ui()
        QtCore.QTimer.singleShot(100, self.analyze_wem_file)

    def auto_configure_converter(self):
        """Automatically configure converter from parent settings"""
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    DEBUG.log(f"Auto-configured Wwise: {wwise_path}")
                    return True
            
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                DEBUG.log(f"Auto-configured Wwise from settings: {wwise_path}")
                return True
                
            DEBUG.log("Could not auto-configure Wwise - no valid paths found", "WARNING")
            return False
            
        except Exception as e:
            DEBUG.log(f"Error auto-configuring Wwise: {e}", "ERROR")
            return False    

    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = f"Adjusting volume for: {self.entry.get('ShortName', '')}"
        if self.is_mod:
            header_text += " (MOD version)"
        else:
            header_text += " (Original version)"
            
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        if not self.volume_processor.is_available():
            error_widget = QtWidgets.QWidget()
            error_layout = QtWidgets.QVBoxLayout(error_widget)
            error_layout.setContentsMargins(20, 20, 20, 20)
            
            error_label = QtWidgets.QLabel(self.tr("volume_deps_missing"))
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_layout.addWidget(error_label)
            
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            error_layout.addWidget(close_btn)
            
            layout.addWidget(error_widget)
            return
        
        analysis_group = QtWidgets.QGroupBox(self.tr("audio_analysis_group"))
        analysis_layout = QtWidgets.QFormLayout(analysis_group)
        
        self.current_rms_label = QtWidgets.QLabel(self.tr("analyzing"))
        self.current_peak_label = QtWidgets.QLabel(self.tr("analyzing"))
        self.duration_label = QtWidgets.QLabel(self.tr("analyzing"))

        self.max_safe_label = QtWidgets.QLabel(self.tr("no_limit"))
        
        analysis_layout.addRow(self.tr("current_rms"), self.current_rms_label)
        analysis_layout.addRow(self.tr("current_peak"), self.current_peak_label)
        analysis_layout.addRow(self.tr("duration_label"), self.duration_label)
        analysis_layout.addRow(self.tr("recommended_max"), self.max_safe_label)
        
        layout.addWidget(analysis_group)
        
        control_group = QtWidgets.QGroupBox(self.tr("volume_control_group"))
        control_layout = QtWidgets.QVBoxLayout(control_group)
        
        slider_widget = QtWidgets.QWidget()
        slider_layout = QtWidgets.QHBoxLayout(slider_widget)
        
        slider_layout.addWidget(QtWidgets.QLabel(self.tr("volume_label_simple")))
        
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(1000) 
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volume_slider.setTickInterval(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        slider_layout.addWidget(self.volume_slider, 1)
        
        self.volume_label = QtWidgets.QLabel("100%")
        self.volume_label.setMinimumWidth(80)
        self.volume_label.setAlignment(QtCore.Qt.AlignCenter)
        self.volume_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        slider_layout.addWidget(self.volume_label)
        
        self.volume_spin = QtWidgets.QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)  
        self.volume_spin.setValue(100)
        self.volume_spin.setSuffix("%")
        self.volume_spin.valueChanged.connect(self.on_spin_changed)
        slider_layout.addWidget(self.volume_spin)
        
        control_layout.addWidget(slider_widget)
        
        presets_widget = QtWidgets.QWidget()
        presets_layout = QtWidgets.QHBoxLayout(presets_widget)
        presets_layout.addWidget(QtWidgets.QLabel(self.tr("quick_presets")))
        
        preset_buttons = [
            ("25%", 25),
            ("50%", 50),
            ("75%", 75),
            ("100%", 100),
            ("150%", 150),
            ("200%", 200),
            ("300%", 300),
            ("500%", 500),
            ("1000%", 1000)
        ]
        
        for text, value in preset_buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.set_volume(v))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        control_layout.addWidget(presets_widget)
        
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setStyleSheet("padding: 10px; border: 1px solid #5a5d5f; border-radius: 5px;")
        control_layout.addWidget(self.preview_label)
        self.update_preview()
        
        layout.addWidget(control_group)
        
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        
        self.progress_label = QtWidgets.QLabel("Processing...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        layout.addWidget(self.progress_widget)
        
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
        buttons_layout.addStretch()
        
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_volume_change_btn"))
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.process_btn.clicked.connect(self.process_volume_change)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_widget)
    
    def analyze_wem_file(self):
        """Analyze the WEM file"""
        if not self.volume_processor.is_available():
            return 
        
        try:
            file_id = self.entry.get("Id", "")
            if self.is_mod:
  
                wem_path = self.parent.get_mod_path(file_id, self.lang)
                if not wem_path or not os.path.exists(wem_path):
                 
                    if self.lang != "SFX":
                        wem_path = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", self.lang, f"{file_id}.wem"
                        )
                    else:
                        wem_path = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", f"{file_id}.wem"
                        )
            else:
                wem_path = self.parent.get_original_path(file_id, self.lang)
            
            if not wem_path or not os.path.exists(wem_path):
                self.current_rms_label.setText("File not found")
                DEBUG.log(f"WemVolumeEditDialog: File not found at {wem_path}", "WARNING")
                return
            
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            self.temp_files.append(temp_wav)
            
            ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
            if not ok:
                self.current_rms_label.setText("Conversion error")
                return
            
            self.current_analysis = self.volume_processor.analyze_audio(temp_wav)
            if self.current_analysis:
                self.current_rms_label.setText(f"{self.current_analysis['rms_percent']:.1f}%")
                self.current_peak_label.setText(f"{self.current_analysis['peak_percent']:.1f}%")
                self.duration_label.setText(f"{self.current_analysis['duration_seconds']:.2f} seconds")
                
                safe_max = int(self.current_analysis['max_increase'])
                self.max_safe_label.setText(f"{safe_max}% (for no clipping)")
                
            else:
                self.current_rms_label.setText("Analysis failed")
                
        except Exception as e:
            DEBUG.log(f"Error analyzing WEM: {e}", "ERROR")
            self.current_rms_label.setText("Error")
    
    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.volume_spin.blockSignals(True)
        self.volume_spin.setValue(value)
        self.volume_spin.blockSignals(False)
        self.update_preview()
    
    def on_spin_changed(self, value):
        self.volume_slider.blockSignals(True)
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(f"{value}%")
        self.update_preview()
    
    def set_volume(self, value):
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
    
    def update_preview(self):
        if not self.current_analysis:
            self.preview_label.setText(self.tr("waiting_for_analysis"))
            return
            
        volume = self.volume_slider.value()
        
        new_rms = self.current_analysis['rms_percent'] * (volume / 100)
        new_peak = self.current_analysis['peak_percent'] * (volume / 100)
        
        preview_text = self.tr("preview_rms_peak").format(new_rms=new_rms, new_peak=new_peak)
        is_dark_theme = self.parent.settings.data.get("theme", "light") == "dark"

        base_style = "padding: 10px; border-radius: 5px;"
        if new_peak > 100:
            preview_text += self.tr("preview_clipping").format(over=new_peak - 100)
            bg_color = "#5a1d1d" if is_dark_theme else "#ffcccc"
            text_color = "#ff8a80" if is_dark_theme else "red"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")
        elif new_peak > 95:
            preview_text += self.tr("preview_near_clipping")
            bg_color = "#6b4f1b" if is_dark_theme else "#fff0cc"
            text_color = "#ffd54f" if is_dark_theme else "orange"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")
        else:
            bg_color = "#1e4e24" if is_dark_theme else "#ccffcc"
            text_color = "#a5d6a7" if is_dark_theme else "green"
            self.preview_label.setStyleSheet(f"{base_style} background-color: {bg_color}; color: {text_color};")

        self.preview_label.setText(preview_text)
    
    def process_volume_change(self):
        volume = self.volume_slider.value()
        
        if volume == 100:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_change"),
                self.tr("volume_no_change_msg")
            )
            return
        
        if not self.wav_converter.wwise_path or not self.wav_converter.project_path:
            QtWidgets.QMessageBox.warning(
                self, self.tr("config_required"),
                self.tr("wwise_config_required_msg")
            )
            return
        
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_thread, args=(volume,))
        thread.daemon = True
        thread.start()

    def _process_thread(self, volume):
        """Process volume change in thread"""
        try:
            self.update_progress(10, self.tr("status_preparing"))
            
            file_id = self.entry.get("Id", "")
            shortname = self.entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            if self.is_mod:
                # FIX: Use get_mod_path helper to correctly locate the source file
                current_mod_path = self.parent.get_mod_path(file_id, self.lang)
                
                if not current_mod_path or not os.path.exists(current_mod_path):
                    raise Exception("Modified audio file not found. Try reverting to original first.")
                
                backup_path = self.parent.get_backup_path(file_id, self.lang)
                
                if os.path.exists(backup_path):
                    source_wem_path = backup_path
                    self.update_progress(15, self.tr("status_using_backup"))
                    DEBUG.log(f"Using backup as source: {backup_path}")
                else:
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(current_mod_path, backup_path)
                    source_wem_path = backup_path
                    self.update_progress(15, self.tr("status_backup_created"))
                    DEBUG.log(f"Created backup from current mod: {backup_path}")
            else:
                source_wem_path = self.parent.get_original_path(file_id, self.lang)
                if not os.path.exists(source_wem_path):
                    raise Exception(f"Original WEM file not found: {source_wem_path}")
                self.update_progress(15, self.tr("status_using_original"))
            
            self.update_progress(20, self.tr("status_converting_to_wav"))
            
            temp_wav_original = tempfile.NamedTemporaryFile(
                suffix=f'_{original_filename}_source.wav', 
                delete=False
            ).name
            self.temp_files.append(temp_wav_original)
            
            ok, err = self.parent.wem_to_wav_vgmstream(source_wem_path, temp_wav_original)
            if not ok:
                raise Exception(f"WEM to WAV conversion failed: {err}")
            
            self.update_progress(40, self.tr("status_adjusting_volume"))
            
            temp_wav_adjusted = tempfile.NamedTemporaryFile(
                suffix=f'_{original_filename}_vol{volume}.wav', 
                delete=False
            ).name
            self.temp_files.append(temp_wav_adjusted)
            
            success, result = self.volume_processor.change_volume(
                temp_wav_original,
                temp_wav_adjusted,
                volume
            )
            
            if not success:
                raise Exception(f"Volume adjustment failed: {result}")
            
            self.update_progress(60, self.tr("status_preparing_for_wem"))
            
            temp_dir = tempfile.mkdtemp(prefix="volume_adjust_")
            self.temp_files.append(temp_dir)
            
            final_wav_for_wwise = os.path.join(temp_dir, f"{original_filename}.wav")
            shutil.copy2(temp_wav_adjusted, final_wav_for_wwise)
            
            # Use source size as target if we are editing original, or if preserving mod size
            target_size = os.path.getsize(source_wem_path)
            
            file_pair = {
                "wav_file": final_wav_for_wwise,
                "target_wem": source_wem_path,
                "wav_name": f"{original_filename}.wav",
                "target_name": f"{original_filename}.wem",
                "target_size": target_size,
                "language": self.lang,
                "file_id": file_id
            }
            
            if not self.wav_converter.wwise_path:
                raise Exception("Wwise not configured. Please check configuration.")
            
            temp_output = os.path.join(temp_dir, "output")
            os.makedirs(temp_output, exist_ok=True)
            self.wav_converter.output_folder = temp_output
            
            self.update_progress(70, self.tr("status_converting_to_wem"))
            
            conversion_result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)
            
            if not conversion_result.get('success'):
                error_msg = conversion_result.get('error', 'Unknown error')
                raise Exception(f"WEM conversion failed: {error_msg}")
            
            self.update_progress(85, self.tr("status_deploying_to_mod"))
            
            # FIX: Use correct deployment path with Media folder
            if self.lang != "SFX":
                target_dir = os.path.join(
                    self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media", self.lang
                )
            else:
                target_dir = os.path.join(
                    self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media"
                )
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, f"{file_id}.wem")
            
            output_wem = conversion_result['output_path']
            shutil.copy2(output_wem, target_path)
            
            try:
                if os.path.exists(temp_output):
                    shutil.rmtree(temp_output)
            except Exception as e:
                DEBUG.log(f"Warning: Failed to cleanup temp output: {e}", "WARNING")
            
            self.update_progress(100, self.tr("status_complete"))
            
            clipping_info = ""
            if result.get('clipped_percent', 0) > 0:
                clipping_info = self.tr("clipping_info_text").format(percent=result['clipped_percent'])

            backup_info = ""
            if self.parent.has_backup(file_id, self.lang):
                backup_info = self.tr("backup_available_info")

            source_info = ""
            if self.is_mod:
                if os.path.exists(self.parent.get_backup_path(file_id, self.lang)):
                    source_info = self.tr("source_info_backup")
                else:
                    source_info = self.tr("source_info_mod_backup_created")
            else:
                source_info = self.tr("source_info_original")

            success_message = self.tr("volume_change_success_msg").format(
                volume=volume,
                actual_change=result.get('actual_change', volume),
                clipping_info=clipping_info,
                source_info=source_info,
                backup_info=backup_info
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "show_success",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, success_message)
            )
            
        except Exception as e:
            error_message = str(e)
            
            if "Failed to create WEM file" in error_message or "No acceptable result found" in error_message:
                error_message = self.tr("wem_conversion_failed_msg").format(error_message=error_message)
            elif "Wwise not configured" in error_message:
                error_message = self.tr("wwise_not_configured_msg")
            elif "not found" in error_message.lower():
                error_message = self.tr("required_file_not_found_msg").format(error_message=error_message)
            
            QtCore.QMetaObject.invokeMethod(
                self, "show_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, error_message)
            )
        
        finally:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        if os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                        else:
                            os.remove(temp_file)
                except Exception as e:
                    DEBUG.log(f"Warning: Failed to cleanup temp file {temp_file}: {e}", "WARNING")  

    def update_progress(self, value, text):
        QtCore.QMetaObject.invokeMethod(
            self.progress_bar, "setValue",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(int, value)
        )
        QtCore.QMetaObject.invokeMethod(
            self.progress_label, "setText",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, text)
        )
        QtCore.QMetaObject.invokeMethod(
            self.status_text, "append",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, f"[{value}%] {text}")
        )
    
    @QtCore.pyqtSlot(str)
    def show_success(self, message):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        QtWidgets.QMessageBox.information(self, "Success", message)
        if hasattr(self.parent, 'populate_tree'):
            self.parent.populate_tree(self.lang)
        self.accept()
    
    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        QtWidgets.QMessageBox.critical(self, self.tr("error"), f"{self.tr('volume_change_failed_title')}:\n\n{error}")
class BatchVolumeEditDialog(QtWidgets.QDialog):
    """Dialog for batch editing volume of multiple files"""
    
    def __init__(self, parent, entries_and_lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entries_and_lang = entries_and_lang
        self.is_mod = is_mod
        self.volume_processor = VolumeProcessor()
        self.temp_files = []
        
        self.setWindowTitle(self.tr("batch_volume_editor_title").format(count=len(entries_and_lang)))
        self.setMinimumSize(800, 700)
        
        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()
        
        self.create_ui()
        QtCore.QTimer.singleShot(100, self.analyze_files)
    
    def auto_configure_converter(self):
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    return True
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                return True
            return False
        except:
            return False
    
    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = f"Batch Volume Editor - {len(self.entries_and_lang)} files"
        if self.is_mod:
            header_text += " (MOD versions)"
        else:
            header_text += " (Original versions)"
            
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        if not self.volume_processor.is_available():
            error_label = QtWidgets.QLabel(self.tr("volume_deps_missing"))
            error_label.setStyleSheet("color: red; padding: 20px; font-size: 14px;")
            layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton(self.tr("close"))
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return
        
        if self.wav_converter.wwise_path and self.wav_converter.project_path:
            config_status = QtWidgets.QLabel(self.tr("wwise_configured_auto"))
            config_status.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        else:
            config_status = QtWidgets.QLabel(self.tr("wwise_not_configured_warning"))
            config_status.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
        layout.addWidget(config_status)
        backup_info_widget = QtWidgets.QWidget()
        backup_info_layout = QtWidgets.QHBoxLayout(backup_info_widget)

        backup_icon = QtWidgets.QLabel("💾")
        backup_text = QtWidgets.QLabel(self.tr("backups_stored_in").format(path=os.path.join(self.parent.base_path, '.backups', 'audio')))
        backup_text.setStyleSheet("color: #666; font-size: 11px;")

        backup_info_layout.addWidget(backup_icon)
        backup_info_layout.addWidget(backup_text)
        backup_info_layout.addStretch()

        layout.addWidget(backup_info_widget)

        control_group = QtWidgets.QGroupBox(self.tr("volume_control_all_files_group"))

        control_layout = QtWidgets.QVBoxLayout(control_group)
        
        slider_widget = QtWidgets.QWidget()
        slider_layout = QtWidgets.QHBoxLayout(slider_widget)
        
        slider_layout.addWidget(QtWidgets.QLabel(self.tr("volume_label_simple")))
        
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(1000)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volume_slider.setTickInterval(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        slider_layout.addWidget(self.volume_slider, 1)
        
        self.volume_label = QtWidgets.QLabel("100%")
        self.volume_label.setMinimumWidth(80)
        self.volume_label.setAlignment(QtCore.Qt.AlignCenter)
        self.volume_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        slider_layout.addWidget(self.volume_label)
        
        self.volume_spin = QtWidgets.QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(9999)
        self.volume_spin.setValue(100)
        self.volume_spin.setSuffix("%")
        self.volume_spin.valueChanged.connect(self.on_spin_changed)
        slider_layout.addWidget(self.volume_spin)
        
        control_layout.addWidget(slider_widget)
        
        presets_widget = QtWidgets.QWidget()
        presets_layout = QtWidgets.QHBoxLayout(presets_widget)
        presets_layout.addWidget(QtWidgets.QLabel(self.tr("quick_presets")))
        
        preset_buttons = [
            ("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100),
            ("150%", 150), ("200%", 200), ("300%", 300), ("500%", 500)
        ]
        
        for text, value in preset_buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.set_volume(v))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        control_layout.addWidget(presets_widget)
        
        layout.addWidget(control_group)
        
        files_group = QtWidgets.QGroupBox(self.tr("files_to_process_group"))
        files_layout = QtWidgets.QVBoxLayout(files_group)
        
        self.files_table = QtWidgets.QTableWidget()
        self.files_table.setColumnCount(6)
        self.files_table.setHorizontalHeaderLabels([
            self.tr("file_header"), self.tr("language_header"), self.tr("current_rms_header"), 
            self.tr("current_peak_header"), self.tr("new_preview_header"), self.tr("status_header")
        ])

        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)
        
        layout.addWidget(files_group)
        
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        
        self.progress_label = QtWidgets.QLabel("Processing...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.current_file_label = QtWidgets.QLabel("")
        progress_layout.addWidget(self.current_file_label)
        
        layout.addWidget(self.progress_widget)
        
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        
        buttons_layout.addStretch()
        
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_to_all_btn"))
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.process_btn.clicked.connect(self.process_all_files)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_widget)
        
        self.file_analyses = []
    
    def analyze_files(self):
        """Analyze all files"""
        self.files_table.setRowCount(len(self.entries_and_lang))
        self.file_analyses = []
        
        for i, (entry, lang) in enumerate(self.entries_and_lang):
            self.files_table.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.get('ShortName', '')))
            self.files_table.setItem(i, 1, QtWidgets.QTableWidgetItem(lang))
            self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Analyzing..."))
            
            try:
                file_id = entry.get("Id", "")
                if self.is_mod:
                   
                    wem_path = self.parent.get_mod_path(file_id, lang)
                    if not wem_path or not os.path.exists(wem_path):
                       
                        if lang != "SFX":
                            wem_path = os.path.join(
                                self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                                "Windows", "Media", lang, f"{file_id}.wem"
                            )
                        else:
                            wem_path = os.path.join(
                                self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                                "Windows", "Media", f"{file_id}.wem"
                            )
                else:
                    wem_path = self.parent.get_original_path(file_id, lang)
                
                if wem_path and os.path.exists(wem_path):
                    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                    self.temp_files.append(temp_wav)
                    
                    ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
                    if ok:
                        analysis = self.volume_processor.analyze_audio(temp_wav)
                        if analysis:
                            self.file_analyses.append(analysis)
                            self.files_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{analysis['rms_percent']:.1f}%"))
                            self.files_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{analysis['peak_percent']:.1f}%"))
                            self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Ready"))
                            continue
                
                self.file_analyses.append(None)
                self.files_table.setItem(i, 2, QtWidgets.QTableWidgetItem("N/A"))
                self.files_table.setItem(i, 3, QtWidgets.QTableWidgetItem("N/A"))
                self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Error"))
                
            except Exception as e:
                self.file_analyses.append(None)
                self.files_table.setItem(i, 5, QtWidgets.QTableWidgetItem("Error"))
        
        self.update_preview_all()
    
    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.volume_spin.blockSignals(True)
        self.volume_spin.setValue(value)
        self.volume_spin.blockSignals(False)
        self.update_preview_all()
    
    def on_spin_changed(self, value):
        self.volume_slider.blockSignals(True)
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)
        self.volume_label.setText(f"{value}%")
        self.update_preview_all()
    
    def set_volume(self, value):
        if value > self.volume_slider.maximum():
            self.volume_slider.setMaximum(value + 100)
        self.volume_slider.setValue(value)
    
    def update_preview_all(self):
        volume = self.volume_slider.value()
        
        for i, analysis in enumerate(self.file_analyses):
            if analysis:
                new_rms = analysis['rms_percent'] * (volume / 100)
                new_peak = analysis['peak_percent'] * (volume / 100)
                
                preview_text = f"RMS {new_rms:.1f}%, Peak {new_peak:.1f}%"
                if new_peak > 100:
                    preview_text += " ⚠️"
                
                preview_item = QtWidgets.QTableWidgetItem(preview_text)
                if new_peak > 100:
                    preview_item.setBackground(QtGui.QColor(255, 200, 200))
                elif new_peak > 95:
                    preview_item.setBackground(QtGui.QColor(255, 240, 200))
                else:
                    preview_item.setBackground(QtGui.QColor(200, 255, 200))
                
                self.files_table.setItem(i, 4, preview_item)
            else:
                self.files_table.setItem(i, 4, QtWidgets.QTableWidgetItem("N/A"))
    
    def process_all_files(self):
        volume = self.volume_slider.value()
        
        if volume == 100:
            QtWidgets.QMessageBox.information(self, "No Change", "Volume is set to 100% (no change).")
            return
        
        if not self.wav_converter.wwise_path or not self.wav_converter.project_path:
            QtWidgets.QMessageBox.warning(self, "Configuration Required", self.tr("wwise_config_required_msg"))
            return
        
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_all_thread, args=(volume,))
        thread.daemon = True
        thread.start()
    
    def _process_all_thread(self, volume):
        """Process all files in thread"""
        try:
            total_files = len(self.entries_and_lang)
            successful = 0
            failed = 0
            
            for i, (entry, lang) in enumerate(self.entries_and_lang):
                if self.file_analyses[i] is None:
                    failed += 1
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, self.tr("status_skipped_no_analysis"))
                    )
                    continue
                
                progress = int((i / total_files) * 100)
                file_name = entry.get('ShortName', f'File {i+1}')
                shortname = entry.get("ShortName", "")
                original_filename = os.path.splitext(shortname)[0]
                file_id = entry.get("Id", "")
                
                QtCore.QMetaObject.invokeMethod(
                    self, "update_progress",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(int, progress),
                    QtCore.Q_ARG(str, f"Processing {i+1}/{total_files}"),
                    QtCore.Q_ARG(str, file_name)
                )
                
                try:
                    if self.is_mod:
                        
                        current_mod_path = self.parent.get_mod_path(file_id, lang)
                        
                        if not current_mod_path or not os.path.exists(current_mod_path):
                            raise Exception(f"Modified audio file not found for {file_name}")
                        
                        backup_path = self.parent.get_backup_path(file_id, lang)
                        
                        if os.path.exists(backup_path):
                            source_wem_path = backup_path
                        else:
                            backup_dir = os.path.dirname(backup_path)
                            os.makedirs(backup_dir, exist_ok=True)
                            shutil.copy2(current_mod_path, backup_path)
                            source_wem_path = backup_path
                    else:
                        source_wem_path = self.parent.get_original_path(file_id, lang)
                        
                        if not os.path.exists(source_wem_path):
                            raise Exception(f"Original WEM file not found: {source_wem_path}")
                    
                    temp_wav_original = tempfile.NamedTemporaryFile(suffix=f'_{original_filename}_original.wav', delete=False).name
                    self.temp_files.append(temp_wav_original)
                    
                    ok, err = self.parent.wem_to_wav_vgmstream(source_wem_path, temp_wav_original)
                    if not ok:
                        raise Exception(f"WEM to WAV conversion failed: {err}")
                    
                    temp_wav_adjusted = tempfile.NamedTemporaryFile(suffix=f'_{original_filename}_adjusted.wav', delete=False).name
                    self.temp_files.append(temp_wav_adjusted)
                    
                    success, result = self.volume_processor.change_volume(
                        temp_wav_original,
                        temp_wav_adjusted,
                        volume
                    )
                    
                    if not success:
                        raise Exception(f"Volume adjustment failed: {result}")
                    
                    temp_dir = tempfile.mkdtemp(prefix=f"batch_volume_{i}_")
                    self.temp_files.append(temp_dir)
                    
                    final_wav_for_wwise = os.path.join(temp_dir, f"{original_filename}.wav")
                    shutil.copy2(temp_wav_adjusted, final_wav_for_wwise)
                    
                    original_wem_size = os.path.getsize(source_wem_path)
                    
                    file_pair = {
                        "wav_file": final_wav_for_wwise,
                        "target_wem": source_wem_path,
                        "wav_name": f"{original_filename}.wav",
                        "target_name": f"{original_filename}.wem",
                        "target_size": original_wem_size,
                        "language": lang,
                        "file_id": file_id
                    }
                    
                    temp_output = os.path.join(temp_dir, "output")
                    os.makedirs(temp_output, exist_ok=True)
                    self.wav_converter.output_folder = temp_output
                    
                    conversion_result = self.wav_converter.convert_single_file_main(file_pair, i+1, total_files)
                    
                    if not conversion_result.get('success'):
                        raise Exception(f"WEM conversion failed: {conversion_result.get('error', 'Unknown error')}")
                    
                    output_wem = conversion_result['output_path']
                    
                    if lang != "SFX":
                        target_dir = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media", lang
                        )
                    else:
                        target_dir = os.path.join(
                            self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", 
                            "Windows", "Media"
                        )
                    
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, f"{file_id}.wem")
                    
                    shutil.copy2(output_wem, target_path)
                    successful += 1
                    
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, f"✓ {volume}%")
                    )
                    
                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    if len(error_msg) > 50:
                        error_msg = error_msg[:47] + "..."
                    
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_file_status",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(int, i),
                        QtCore.Q_ARG(str, f"✗ {error_msg}")
                    )
                    DEBUG.log(f"Error processing {file_name}: {str(e)}", "ERROR")
            
            QtCore.QMetaObject.invokeMethod(
                self, "processing_complete",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, successful),
                QtCore.Q_ARG(int, failed),
                QtCore.Q_ARG(int, volume)
            )
            
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self, "show_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, str(e))
            )

    @QtCore.pyqtSlot(int, str, str)
    def update_progress(self, progress, main_text, current_file):
        self.progress_bar.setValue(progress)
        self.progress_label.setText(main_text)
        self.current_file_label.setText(current_file)

    @QtCore.pyqtSlot(int, str)
    def update_file_status(self, row, status):
        if row < self.files_table.rowCount():
            self.files_table.setItem(row, 5, QtWidgets.QTableWidgetItem(status))

    @QtCore.pyqtSlot(int, int, int)
    def processing_complete(self, successful, failed, volume):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    if os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                    else:
                        os.remove(temp_file)
            except Exception as e:
                DEBUG.log(f"Failed to clean up temp file {temp_file}: {e}", "WARNING")
        
        message = self.tr("batch_process_complete_msg").format(volume=volume, successful=successful, failed=failed)
        QtWidgets.QMessageBox.information(self, self.tr("batch_process_complete_title"), message)
        
        for lang in set(lang for _, lang in self.entries_and_lang):
            if hasattr(self.parent, 'populate_tree'):
                self.parent.populate_tree(lang)
        
        self.accept()

    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, self.tr("batch_process_error_title"), error)
class DebugWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tr = parent.tr if parent and hasattr(parent, 'tr') else lambda key: key 
        self.setWindowTitle(self.tr("debug_console_title"))
        self.setMinimumSize(800, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        
        self.auto_scroll = QtWidgets.QCheckBox(self.tr("auto_scroll_check"))
        self.auto_scroll.setChecked(True)
        
        clear_btn = QtWidgets.QPushButton(self.tr("clear"))
        clear_btn.clicked.connect(self.clear_logs)
        
        save_btn = QtWidgets.QPushButton(self.tr("save_log_btn"))
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
            self, self.tr("save_debug_log_title"), 
            f"wem_subtitle_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            self.tr("log_files_filter")
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
class AudioTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None, wem_app=None, lang=None):
        super().__init__(parent)
        self.wem_app = wem_app
        self.lang = lang
        self._highlighted_item = None
        self._highlighted_brush = QtGui.QBrush(QtGui.QColor(255, 255, 180))
    def keyPressEvent(self, event):
        """Handle key presses for audio playback and other actions."""
        key = event.key()
        modifiers = event.modifiers()

        if key == QtCore.Qt.Key_Space and modifiers == QtCore.Qt.NoModifier:
            if self.wem_app:
                self.wem_app.play_current(play_mod=False)
            event.accept()

        elif key == QtCore.Qt.Key_Space and modifiers == QtCore.Qt.ControlModifier:
            if self.wem_app:
                self.wem_app.play_current(play_mod=True)
            event.accept()

        elif key == QtCore.Qt.Key_Delete and modifiers == QtCore.Qt.NoModifier:
            if self.wem_app:
                self.wem_app.delete_current_mod_audio() 
            event.accept()
        else:
            super().keyPressEvent(event)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
           
            pos = event.pos()
            item = self.itemAt(pos)
            self._set_highlighted_item(item)
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self._set_highlighted_item(None)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_highlighted_item(None)
        if not event.mimeData().hasUrls():
            return super().dropEvent(event)
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.webm')):
            QtWidgets.QMessageBox.warning(self, self.tr("invalid_file_title"), self.tr("audio_only_drop_msg"))
            return
        pos = event.pos()
        item = self.itemAt(pos)
        if not item or item.childCount() > 0:
            QtWidgets.QMessageBox.information(self, self.tr("drop_audio_title"), self.tr("drop_on_file_msg"))
            return
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
        shortname = entry.get("ShortName", "")
        reply = QtWidgets.QMessageBox.question(
            self, self.tr("replace_audio_title"),
            self.tr("replace_audio_confirm_msg").format(shortname=shortname, filename=os.path.basename(file_path)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if self.wem_app:
                self.wem_app.quick_load_custom_audio(entry, self.lang, custom_file=file_path)
        event.acceptProposedAction()

    def _set_highlighted_item(self, item):
   
        if self._highlighted_item is not None:
            for col in range(self.columnCount()):
                self._highlighted_item.setBackground(col, QtGui.QBrush())
    
        self._highlighted_item = item
        if item is not None:
            for col in range(self.columnCount()):
                item.setBackground(col, self._highlighted_brush)
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
        
        return markers
class SearchBar(QtWidgets.QWidget):
    searchChanged = QtCore.pyqtSignal(str)
    
    def __init__(self, placeholder_text=""):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_icon = QtWidgets.QLabel("🔍")
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText(placeholder_text)
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
    details_updated = QtCore.pyqtSignal(str)
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
        self.details_updated.connect(self.append_details)
    @QtCore.pyqtSlot(int, str)
    def set_progress(self, value, text=""):
        self.progress.setValue(value)
        if text:
            self.label.setText(text)
    
    @QtCore.pyqtSlot(str)        
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
                self.statusUpdate.emit(self.tr("processing_file_status").format(filename=file_info['filename']))
                
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
            self.statusUpdate.emit(self.tr("processing_additional_subs_status"))

      
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
            self.statusUpdate.emit(self.tr("loaded_subs_from_files_status").format(count=len(subtitles_to_show), processed_files=files_processed))
            
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
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
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
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
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
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
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
            "wem_process_language": "english",
            "conversion_method": "bnk",
            "active_profile": "",
            "mod_profiles": {},
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
        self.player.setNotifyInterval(10)
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
class ClickableProgressBar(QtWidgets.QProgressBar):
    """A progress bar that allows seeking by clicking on it."""
    clicked = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse press events to calculate the seek position."""
        if event.button() == QtCore.Qt.LeftButton:
            percent = event.pos().x() / self.width()
            
            target_position = int(self.maximum() * percent)
            
            self.clicked.emit(target_position)
            
            self.setValue(target_position)    
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
        
        self.conversion_cache.clear()
        DEBUG.log("Conversion cache cleared")
        
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
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(script_dir, "temp_conversion")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                DEBUG.log("Cleaned up temp_conversion directory")
            except Exception as e:
                DEBUG.log(f"Error cleaning temp_conversion: {e}", "WARNING")
    def convert_and_update_bnk(self, file_pair):
        try:
            wav_file = file_pair['wav_file']
            source_id = int(file_pair['file_id'])

            self.parent.append_conversion_log(f"Converting {os.path.basename(wav_file)} with maximum quality...")
            result_data = self.convert_with_quality(wav_file, 10)
            
            if not result_data:
                raise Exception("Failed to create WEM file with quality 10")

            new_wem_path = result_data['file']
            new_wem_size = result_data['size']
            self.parent.append_conversion_log(f"  ✓ Created WEM: {new_wem_size:,} bytes")

            self.parent.append_conversion_log("Searching and modifying BNK files...")
            bnk_files_info = self.parent.find_relevant_bnk_files()
            
            if not bnk_files_info:
                raise Exception("BNK Files for modifications not found in Wems")

            bnk_modified = False
            for bnk_path, bnk_type in bnk_files_info:

                original_editor = BNKEditor(bnk_path)
                if not original_editor.find_sound_by_source_id(source_id):
                    continue

                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.parent.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else: # 'lang'
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.parent.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.parent.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

                source_bnk_for_edit = mod_bnk_path
                if not os.path.exists(source_bnk_for_edit):
                    os.makedirs(os.path.dirname(source_bnk_for_edit), exist_ok=True)
                    shutil.copy2(bnk_path, source_bnk_for_edit)
                
                editor = BNKEditor(source_bnk_for_edit)
                
                if editor.modify_sound(source_id, new_size=new_wem_size, find_by_size=None):
                    editor.save_file()
                    self.parent.invalidate_bnk_cache(source_id)
                    self.parent.append_conversion_log(f"  ✓ Updated {os.path.basename(mod_bnk_path)}: ID {source_id} -> {new_wem_size} bytes")
                    bnk_modified = True
                    break

            if not bnk_modified:
                self.parent.append_conversion_log(f"  ✗ Warning: ID {source_id} not found in any BNK. Size not updated.", "WARNING")

            return {
                'success': True,
                'output_path': new_wem_path,
                'final_size': new_wem_size,
                'attempts': 1,
                'conversion': 'BNK Overwrite (Quality 10)',
                'size_diff_percent': 0
            }

        except Exception as e:
            DEBUG.log(f"Error converting and updating BNK: {e}", "ERROR")
            self.parent.append_conversion_log(f"  ✗ Error: {e}")
            return {'success': False, 'error': str(e)}
    def set_adaptive_mode(self, enabled):
        self.adaptive_mode = enabled
        
    def set_paths(self, wwise_path, project_path, output_folder):
        self.wwise_path = wwise_path
        self.project_path = project_path
        self.output_folder = output_folder
        self.conversion_cache.clear()
    def add_file_pair(self, audio_file, target_wem):
        if not os.path.exists(audio_file) or not os.path.exists(target_wem):
            return False

        audio_ext = os.path.splitext(audio_file)[1].lower()
        
        needs_conversion = audio_ext != '.wav'
        
        file_pair = {
            "audio_file": audio_file,
            "original_format": audio_ext,
            "needs_conversion": needs_conversion,
            "target_wem": target_wem,
            "audio_name": os.path.basename(audio_file),
            "target_name": os.path.basename(target_wem),
            "target_size": os.path.getsize(target_wem),
            "language": "",
            "file_id": os.path.splitext(os.path.basename(target_wem))[0]
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
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False, creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore')

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

        result = subprocess.run(cmd, capture_output=True, text=True, shell=False, creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore')

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
        if self.should_stop:
            return {'success': False, 'stopped': True, 'error': 'Conversion stopped by user'}

        try:
            audio_file = file_pair.get('audio_file') or file_pair.get('wav_file')
            if not audio_file:
                return {'success': False, 'error': 'Audio file not specified in file_pair'}
            
            audio_ext = os.path.splitext(audio_file)[1].lower()
            needs_conversion = file_pair.get('needs_conversion', False) or (audio_ext != '.wav')

            audio_name = file_pair.get('audio_name') or file_pair.get('wav_name', '')
            
            original_filename = os.path.splitext(audio_name)[0] if audio_name else os.path.splitext(os.path.basename(audio_file))[0]
            
            file_id = file_pair.get('file_id', '')
            is_id_name = original_filename.isdigit() and file_id and original_filename == file_id
            
            if is_id_name:
                found_entry = next((entry for entry in self.parent.all_files if entry.get("Id", "") == file_id), None)
                if found_entry:
                    shortname = found_entry.get("ShortName", "")
                    original_filename = os.path.splitext(shortname)[0]
                    DEBUG.log(f"Found original name for ID {file_id}: {original_filename}")

            DEBUG.log(f"Original name for Wwise: {original_filename}")
            DEBUG.log(f"AudioFile: {audio_file}")
            
            if needs_conversion:
                self.status_updated.emit(f"Converting {original_filename} to WAV...", "blue")
                audio_converter = getattr(self.parent, 'audio_to_wav_converter', AudioToWavConverter())
                
                if not audio_converter.is_available():
                    return {'success': False, 'error': 'FFmpeg not found. Please install FFmpeg to convert audio formats.'}
                
                temp_dir = tempfile.mkdtemp(prefix="audio_convert_")
                temp_wav = os.path.join(temp_dir, f"{original_filename}.wav")
                success, result = audio_converter.convert_to_wav(audio_file, temp_wav)
                
                if not success:
                    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
                    return {'success': False, 'error': f'Error converting to WAV: {result}'}
                
                wav_file = temp_wav
                file_pair['temp_wav'] = temp_wav
                file_pair['temp_dir'] = temp_dir
                DEBUG.log(f"Converted {original_filename} from {audio_ext} to WAV: {temp_wav}")
            else:
                current_wav_name = os.path.basename(audio_file)
                expected_wav_name = f"{original_filename}.wav"
                
                if current_wav_name != expected_wav_name:
                    temp_dir = tempfile.mkdtemp(prefix="wav_rename_")
                    temp_wav = os.path.join(temp_dir, expected_wav_name)
                    shutil.copy2(audio_file, temp_wav)
                    wav_file = temp_wav
                    file_pair['temp_wav'] = temp_wav
                    file_pair['temp_dir'] = temp_dir
                    DEBUG.log(f"WAV renamed for Wwise: {current_wav_name} -> {expected_wav_name}")
                else:
                    wav_file = audio_file
            
            updated_file_pair = file_pair.copy()
            updated_file_pair['wav_file'] = wav_file
            updated_file_pair['wav_name'] = f"{original_filename}.wav"
            
            conversion_method = self.parent.settings.data.get("conversion_method", "adaptive")
            
            if conversion_method == "bnk":
                DEBUG.log(f"Using method: BNK overwrite for {original_filename}")
                result = self.convert_and_update_bnk(updated_file_pair)
            else: # "adaptive"
                DEBUG.log(f"Using method: Adaptive Conversion for {original_filename}")
                if self.adaptive_mode:
                    result = self.convert_single_file_adaptive(updated_file_pair, file_index, total_files)
                else:
                    target_size = file_pair['target_size']
                    result = self.try_conversion_with_binary_search(wav_file, target_size, file_index, total_files, original_filename)
            
            if result.get('success') and is_id_name:
                output_path = result['output_path']
                id_output_path = os.path.join(os.path.dirname(output_path), f"{file_id}.wem")
                if os.path.exists(output_path) and output_path != id_output_path:
                    shutil.move(output_path, id_output_path)
                    result['output_path'] = id_output_path
                    DEBUG.log(f"Final WEM renamed back to ID: {output_path} -> {id_output_path}")

            return result
                
        except Exception as e:
            DEBUG.log(f"Error in convert_single_file_main: {e}", "ERROR")
            return {'success': False, 'error': f'Error while converting: {str(e)}'}
        finally:
            if 'temp_dir' in file_pair and os.path.exists(file_pair['temp_dir']):
                try:
                    shutil.rmtree(file_pair['temp_dir'])
                    DEBUG.log(f"Cleared temp directory: {file_pair['temp_dir']}")
                except Exception as e:
                    DEBUG.log(f"Failed to clean up temporary directory: {e}", "WARNING")

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
    def try_conversion_with_binary_search(self, wav_file, target_size, file_index, total_files, original_filename):
        """Binary search with file copy to prevent cache corruption"""
        left, right = -2, 10
        best_result = None
        attempts = 0
        
        DEBUG.log(f"\n=== BINARY SEARCH START for {original_filename} ===")
        DEBUG.log(f"Target size: {target_size:,} bytes")
        DEBUG.log(f"Search range: [{left}, {right}]")
        DEBUG.log(f"WAV file: {wav_file}")
        
        if hasattr(self.parent, 'append_conversion_log'):
            self.parent.append_conversion_log(f"\n📊 Binary search for {original_filename}:")
            self.parent.append_conversion_log(f"   Target size: {target_size:,} bytes")
        
        all_attempts = []
        
        while left <= right:
            mid = (left + right) // 2
            attempts += 1
            
            DEBUG.log(f"\nAttempt {attempts}: Testing Conversion={mid} (range: [{left}, {right}])")
            
            self.status_updated.emit(
                f"File {file_index}/{total_files}: {original_filename} - attempt {attempts} (Conversion={mid})", 
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
                    
                    temp_best_file = os.path.join(self.output_folder, f"best_{original_filename}_{mid}.wem")
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
                
                output_filename = f"{original_filename}.wem"
                output_path = os.path.join(self.output_folder, output_filename)
                
                counter = 1
                while os.path.exists(output_path) and output_path != best_result['file']:
                    output_filename = f"{original_filename}_{counter}.wem"
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
                            'error': f'Cannot achieve target size. Minimum: {min_size:,} bytes, Target: {target_size:,} bytes ({size_diff:.1f}% over). Try reducing WAV quality or using adaptive mode.',
                            'size_warning': True
                        }
            except Exception as e:
                DEBUG.log(f"Error testing minimum quality: {e}", "ERROR")

            return {'success': False, 'error': 'Failed to create WEM file. Please check your WAV file and Wwise configuration. Try choosing a different Wwise project folder.'}
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
                        'file_pair': {'audio_name': 'Project Setup'},
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
                    self.status_updated.emit(f"Converting {i+1}/{total_files}: {file_pair['audio_name']}", "blue")
                    
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
            is_dark_theme = self.parent() and self.parent().settings.data.get("theme", "light") == "dark"
            if is_dark_theme:
                original_text.setStyleSheet("background-color: #3c3f41; color: #a9b7c6;")
            else:
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
class ClickableLabel(QtWidgets.QLabel):
    """A QLabel that emits a clicked signal."""
    clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()

class AudioTrimDialog(QtWidgets.QDialog):
    
    def __init__(self, parent, entry, lang, is_mod=False):
        super().__init__(parent)
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        self.parent = parent
        self.entry = entry
        self.lang = lang
        self.is_mod = is_mod
        self.temp_files = []
        self.source_wav = None
        self.start_ms = 0
        self.end_ms = 0
        
        self.setWindowTitle(self.tr("trim_editor_title").format(shortname=entry.get('ShortName', ''))) 
        self.setMinimumSize(800, 450)
        
        self.ffmpeg_path = AudioToWavConverter().find_ffmpeg()
        if not self.ffmpeg_path or not MATPLOTLIB_AVAILABLE:
            msg = self.tr("trim_deps_missing")
            QtWidgets.QMessageBox.critical(self, self.tr("error"), msg)

        self.wav_converter = WavToWemConverter(parent)
        self.auto_configure_converter()

        self.player = QtMultimedia.QMediaPlayer()
        self.player.setNotifyInterval(10)

        self.create_ui()
        QtCore.QTimer.singleShot(100, self.prepare_audio)

    def auto_configure_converter(self):
        try:
            if hasattr(self.parent, 'wwise_path_edit') and hasattr(self.parent, 'converter_project_path_edit'):
                wwise_path = self.parent.wwise_path_edit.text()
                project_path = self.parent.converter_project_path_edit.text()
                if wwise_path and project_path and os.path.exists(wwise_path):
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                    return True
            wwise_path = self.parent.settings.data.get("wav_wwise_path", "")
            project_path = self.parent.settings.data.get("wav_project_path", "")
            if wwise_path and project_path and os.path.exists(wwise_path):
                self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
                return True
            return False
        except:
            return False

    def create_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        header_text = self.tr("trimming_audio_for").format(shortname=self.entry.get('ShortName', ''))
        header_text += self.tr("version_mod") if self.is_mod else self.tr("version_original")
        header = QtWidgets.QLabel(header_text)
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        self.waveform_widget = WaveformWidget()
        self.waveform_widget.rangeChanged.connect(self.update_times_from_waveform)
        self.waveform_widget.zoomRequested.connect(self.on_wheel_zoom)
        self.waveform_widget.seekRequested.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.waveform_widget.set_playhead)
        layout.addWidget(self.waveform_widget)

        self.scroll_bar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.scroll_bar.valueChanged.connect(self.on_scroll)
        layout.addWidget(self.scroll_bar)

        zoom_widget = QtWidgets.QWidget()
        zoom_layout = QtWidgets.QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.valueChanged.connect(self.on_zoom)
        zoom_layout.addWidget(QtWidgets.QLabel(self.tr("zoom_label")))
        zoom_layout.addWidget(self.zoom_slider)
        layout.addWidget(zoom_widget)

        time_widget = QtWidgets.QWidget()
        time_layout = QtWidgets.QFormLayout(time_widget)
        self.start_time_edit = QtWidgets.QSpinBox()
        self.start_time_edit.setSuffix(" ms")
        self.start_time_edit.editingFinished.connect(self.update_waveform_from_times)
        self.end_time_edit = QtWidgets.QSpinBox()
        self.end_time_edit.setSuffix(" ms")
        self.end_time_edit.editingFinished.connect(self.update_waveform_from_times)
        self.duration_label = QtWidgets.QLabel("New Duration: 0.000 s")
        self.duration_label.setStyleSheet("font-weight: bold;")
        time_layout.addRow(self.tr("start_time_label"), self.start_time_edit)
        time_layout.addRow(self.tr("end_time_label"), self.end_time_edit)
        time_layout.addRow(self.tr("new_duration_label"), self.duration_label)
        layout.addWidget(time_widget)

        playback_layout = QtWidgets.QHBoxLayout()
        self.play_btn = QtWidgets.QPushButton(self.tr("play_pause_btn"))
        self.play_btn.clicked.connect(self.toggle_playback)
        self.preview_btn = QtWidgets.QPushButton(self.tr("preview_trim_btn"))
        self.preview_btn.clicked.connect(self.preview_trim)
        self.stop_btn = QtWidgets.QPushButton(self.tr("stop_btn"))
        self.stop_btn.clicked.connect(self.stop_playback)
        playback_layout.addWidget(self.play_btn)
        playback_layout.addWidget(self.preview_btn)
        playback_layout.addWidget(self.stop_btn)
        layout.addLayout(playback_layout)
        self.progress_widget = QtWidgets.QWidget()
        self.progress_widget.hide()
        progress_layout = QtWidgets.QVBoxLayout(self.progress_widget)
        self.progress_label = QtWidgets.QLabel("Processing...")
        self.progress_bar = QtWidgets.QProgressBar()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_widget)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        self.process_btn = QtWidgets.QPushButton(self.tr("apply_trim_btn"))
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.process_btn.clicked.connect(self.process_trim)
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def prepare_audio(self):
        try:
            file_id = self.entry.get("Id", "")
            wem_path = self.parent.get_mod_path(file_id, self.lang) if self.is_mod else self.parent.get_original_path(file_id, self.lang)
            if not os.path.exists(wem_path): raise FileNotFoundError("Audio file not found!")

            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            self.temp_files.append(temp_wav)
            
            ok, err = self.parent.wem_to_wav_vgmstream(wem_path, temp_wav)
            if not ok: raise Exception(f"WEM to WAV conversion failed: {err}")

            self.source_wav = temp_wav
            self.waveform_widget.set_waveform(self.source_wav)
            
            url = QtCore.QUrl.fromLocalFile(self.source_wav)
            self.player.setMedia(QtMultimedia.QMediaContent(url))
            self.player.durationChanged.connect(self.on_duration_changed)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, self.tr("error"), self.tr("preparing_audio_failed").format(e=e))
            self.reject()

    def on_duration_changed(self, duration):
        self.waveform_widget.set_duration(duration)
        self.start_time_edit.setRange(0, duration)
        self.end_time_edit.setRange(0, duration)
        self.end_time_edit.setValue(duration)
        self.update_times_from_waveform(0, duration)
        self.on_zoom(0)
    def on_zoom(self, value):
        if self.waveform_widget.duration_ms <= 0: return

        min_view_ms = 50
        max_view_ms = self.waveform_widget.duration_ms
        
        zoom_factor = value / 100.0
        view_duration = int(max_view_ms / (1 + 99 * zoom_factor))
        view_duration = max(min_view_ms, view_duration)

        self.scroll_bar.setPageStep(view_duration)
        self.scroll_bar.setRange(0, self.waveform_widget.duration_ms - view_duration)
        
        current_center = self.waveform_widget.view_start_ms + (self.waveform_widget.view_end_ms - self.waveform_widget.view_start_ms) / 2
        new_start = int(current_center - view_duration / 2)
        
        self.scroll_bar.setValue(new_start)
        self.on_scroll(new_start)

    def on_scroll(self, value):
        view_duration = self.scroll_bar.pageStep()
        self.waveform_widget.set_view_range(value, value + view_duration)
    def on_wheel_zoom(self, delta, mouse_x):
        """Handles zooming with the mouse wheel with smooth, centered scaling."""
        if self.waveform_widget.duration_ms <= 0: return

        zoom_factor = 1.15 if delta > 0 else 1 / 1.15

        current_view_start = self.waveform_widget.view_start_ms
        current_view_end = self.waveform_widget.view_end_ms
        current_view_duration = current_view_end - current_view_start

        time_at_cursor = self.waveform_widget._x_to_ms(mouse_x, current_view_start, current_view_end)

        new_view_duration = current_view_duration / zoom_factor
        
        min_view_ms = 20
        new_view_duration = max(min_view_ms, min(self.waveform_widget.duration_ms, new_view_duration))

        cursor_ratio = (time_at_cursor - current_view_start) / current_view_duration
        new_view_start = time_at_cursor - (new_view_duration * cursor_ratio)
        new_view_end = new_view_start + new_view_duration

        if new_view_start < 0:
            new_view_start = 0
            new_view_end = new_view_duration
        if new_view_end > self.waveform_widget.duration_ms:
            new_view_end = self.waveform_widget.duration_ms
            new_view_start = new_view_end - new_view_duration
        
        self.scroll_bar.setPageStep(int(new_view_duration))
        self.scroll_bar.setRange(0, self.waveform_widget.duration_ms - int(new_view_duration))
        self.scroll_bar.setValue(int(new_view_start))
        
        if new_view_duration >= self.waveform_widget.duration_ms:
            zoom_slider_value = 0
        elif new_view_duration <= min_view_ms:
            zoom_slider_value = 100
        else:
            max_view_ms = self.waveform_widget.duration_ms
            factor = (max_view_ms / new_view_duration - 1) / 99
            zoom_slider_value = int(factor * 100)
            
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom_slider_value)
        self.zoom_slider.blockSignals(False)
    def update_times_from_waveform(self, start_ms, end_ms):
        self.start_ms, self.end_ms = start_ms, end_ms
        self.start_time_edit.blockSignals(True)
        self.end_time_edit.blockSignals(True)
        self.start_time_edit.setValue(start_ms)
        self.end_time_edit.setValue(end_ms)
        self.start_time_edit.blockSignals(False)
        self.end_time_edit.blockSignals(False)
        self.update_duration_label()

    def update_waveform_from_times(self):
        start_ms = self.start_time_edit.value()
        end_ms = self.end_time_edit.value()
        self.waveform_widget.set_selection_range(start_ms, end_ms)
        self.update_times_from_waveform(start_ms, end_ms)
        
    def update_duration_label(self):
        new_duration = self.end_ms - self.start_ms
        self.duration_label.setText(self.tr("new_duration_format").format(duration_sec=new_duration/1000, duration_ms=new_duration))

    def toggle_playback(self):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop_playback(self):
        self.player.stop()
        self.waveform_widget.set_playhead(0)

    def preview_trim(self):
        self.player.setPosition(self.start_ms)
        self.player.play()
        
        def check_position(position):
            if position >= self.end_ms:
                self.player.stop()
                try: self.player.positionChanged.disconnect(check_position)
                except TypeError: pass
        
        try: self.player.positionChanged.disconnect()
        except TypeError: pass
        finally:
            self.player.positionChanged.connect(check_position)
            self.player.positionChanged.connect(self.waveform_widget.set_playhead)

    def process_trim(self):
        self.progress_widget.show()
        self.process_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()

    def _process_thread(self):
        try:
            self.update_progress(10, "Preparing...")

            self.update_progress(20, self.tr("trimming_with_ffmpeg"))
            trimmed_wav = tempfile.NamedTemporaryFile(suffix='_trimmed.wav', delete=False).name
            self.temp_files.append(trimmed_wav)
            
            start_sec = self.start_ms / 1000.0
            duration_sec = (self.end_ms - self.start_ms) / 1000.0
            
            cmd = [
                self.ffmpeg_path, '-i', self.source_wav,
                '-ss', str(start_sec), '-t', str(duration_sec),
                '-acodec', 'pcm_s16le',
                '-ar', str(self.waveform_widget.sample_rate), 
                trimmed_wav, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW)
            if result.returncode != 0:
                raise Exception(f"FFmpeg trimming failed: {result.stderr}")
            file_id = self.entry.get("Id", "")
            shortname = self.entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            if self.is_mod:
                current_mod_path = self.parent.get_mod_path(file_id, self.lang)
                if not os.path.exists(current_mod_path):
                     raise Exception("Modified audio file not found")
                
                backup_path = self.parent.get_backup_path(file_id, self.lang)
                if not os.path.exists(backup_path):
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(current_mod_path, backup_path)
            
            source_wem_path = self.parent.get_original_path(file_id, self.lang)
            target_size = os.path.getsize(source_wem_path)

            file_pair = {
                "wav_file": trimmed_wav, "target_wem": source_wem_path,
                "wav_name": f"{original_filename}.wav", "target_name": f"{original_filename}.wem",
                "target_size": target_size, "language": self.lang, "file_id": file_id
            }

            self.update_progress(60, "Converting to WEM...")
            conversion_result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)

            if not conversion_result.get('success'):
                raise Exception(f"WEM conversion failed: {conversion_result.get('error', 'Unknown error')}")

            self.update_progress(85, "Deploying to MOD_P...")
            target_path = self.parent.get_mod_path(file_id, self.lang)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(conversion_result['output_path'], target_path)

            self.update_progress(100, self.tr("status_complete"))
            QtCore.QMetaObject.invokeMethod(self, "show_success", QtCore.Qt.QueuedConnection)

        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "show_error", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, str(e)))
    def cleanup_before_exit(self):
        if hasattr(self, 'player'):
            self.player.stop()
        
        for f in self.temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except PermissionError:
                    DEBUG.log(f"Could not delete temp file (in use?): {f}", "WARNING")
                except Exception as e:
                    DEBUG.log(f"Error deleting temp file {f}: {e}", "ERROR")
        self.temp_files = []
    def update_progress(self, value, text):
        QtCore.QMetaObject.invokeMethod(self.progress_bar, "setValue", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, value))
        QtCore.QMetaObject.invokeMethod(self.progress_label, "setText", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, text))

    @QtCore.pyqtSlot()
    def show_success(self):
        self.progress_widget.hide()
        QtWidgets.QMessageBox.information(self, self.tr("success"), self.tr("trim_success_msg"))
        self.parent.populate_tree(self.lang)
        self.accept()
        
    @QtCore.pyqtSlot(str)
    def show_error(self, error):
        self.progress_widget.hide()
        self.process_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, self.tr("error"), f"{self.tr('trim_failed_title')}:\n\n{error}")
    def accept(self):
        self.cleanup_before_exit()
        super().accept()

    def reject(self):
        self.cleanup_before_exit()
        super().reject()
    def closeEvent(self, event):
        self.cleanup_before_exit()
        super().closeEvent(event)
class WaveformWidget(QtWidgets.QWidget):
    rangeChanged = QtCore.pyqtSignal(int, int)
    viewChanged = QtCore.pyqtSignal(int, int)
    zoomRequested = QtCore.pyqtSignal(int, int)
    seekRequested = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        
        self.audio_data = None
        self.resampled_data = None
        self.sample_rate = 0
        
        self.duration_ms = 0
        self.selection_start_ms = 0
        self.selection_end_ms = 0
        self.view_start_ms = 0
        self.view_end_ms = 0
        self.playhead_ms = 0
        
        self.is_selecting = False
        
        self.selection_color = QtGui.QColor(0, 120, 215, 70)
        self.playhead_color = QtGui.QColor(255, 0, 0)
        self.background_color = QtGui.QColor(25, 25, 26)
        self.waveform_color = QtGui.QColor(150, 180, 210)
        
        self.setMouseTracking(True)
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            self.zoomRequested.emit(delta, event.pos().x())
        event.accept()
    def set_duration(self, duration_ms):
        self.duration_ms = duration_ms
        self.selection_end_ms = duration_ms
        self.view_end_ms = duration_ms
        self.viewChanged.emit(0, self.duration_ms)

    def set_waveform(self, wav_path):
        if not MATPLOTLIB_AVAILABLE:
            self.audio_data = None
            self.update()
            return
        
        try:
            import wave
            
            with wave.open(wav_path, 'rb') as wf:
                self.sample_rate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                nframes = wf.getnframes()
                channels = wf.getnchannels()
                
                frames = wf.readframes(nframes)
            
            if sampwidth == 1:
                dtype = np.uint8
                max_val = 2**8 / 2
            elif sampwidth == 2:
                dtype = np.int16
                max_val = 2**15
            elif sampwidth == 3:
                data = np.empty((nframes, channels, 4), dtype=np.uint8)
                data[:, :, :sampwidth] = np.frombuffer(frames, dtype=np.uint8).reshape(-1, channels, sampwidth)
                data[:, :, sampwidth:] = (data[:, :, sampwidth - 1:sampwidth] >> 7) * 255
                data = data.view(np.int32)
                max_val = 2**23
            elif sampwidth == 4:
                try:
                    data = np.frombuffer(frames, dtype=np.float32)
                    max_val = 1.0 
                except (TypeError, ValueError):
                    data = np.frombuffer(frames, dtype=np.int32)
                    max_val = 2**31
            else:
                raise ValueError(f"Unsupported sample width: {sampwidth}")

            if sampwidth != 4 or max_val != 1.0:
                 data = np.frombuffer(frames, dtype=dtype)
            
            if channels > 1:
                data = data.reshape(-1, channels)
                data = data.mean(axis=1)

            self.audio_data = data.astype(np.float32) / max_val
            
            DEBUG.log(f"Waveform data loaded: {len(self.audio_data)} samples, sample rate: {self.sample_rate}, sampwidth: {sampwidth}")
        
        except Exception as e:
            DEBUG.log(f"Error loading waveform data: {e}", "ERROR")
            self.audio_data = None
        
        self.update()

    def set_selection_range(self, start_ms, end_ms):
        self.selection_start_ms = max(0, start_ms)
        self.selection_end_ms = min(self.duration_ms, end_ms)
        self.update()

    def set_view_range(self, start_ms, end_ms):
        self.view_start_ms = max(0, start_ms)
        self.view_end_ms = min(self.duration_ms, end_ms)
        self.update()

    def set_playhead(self, position_ms):
        self.playhead_ms = position_ms
        self.update()
        
    def _ms_to_sample(self, ms):
        return int(ms / 1000.0 * self.sample_rate)

    def _sample_to_ms(self, sample_index):
        return int(sample_index / self.sample_rate * 1000.0)

    def _ms_to_x(self, ms):
        view_duration = self.view_end_ms - self.view_start_ms
        if view_duration <= 0: return 0
        return ((ms - self.view_start_ms) / view_duration) * self.width()

    def _x_to_ms(self, x, view_start=None, view_end=None):
        start = view_start if view_start is not None else self.view_start_ms
        end = view_end if view_end is not None else self.view_end_ms
        
        view_duration = end - start
        if view_duration <= 0: return 0
        return start + int((x / self.width()) * view_duration)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), self.background_color)

        if self.audio_data is not None and self.duration_ms > 0:
            view_duration = self.view_end_ms - self.view_start_ms
            if view_duration <= 0:
                painter.end()
                return

            start_sample = self._ms_to_sample(self.view_start_ms)
            end_sample = self._ms_to_sample(self.view_end_ms)
            visible_data = self.audio_data[start_sample:end_sample]

            if len(visible_data) > 0:
        
                path = QtGui.QPainterPath()
                h = self.height()
                half_h = h / 2
                
                samples_per_pixel = len(visible_data) / self.width()
                
                if samples_per_pixel < 1: 
              
                    path.moveTo(0, half_h - visible_data[0] * half_h)
                    for i, sample in enumerate(visible_data):
                        x = i * (self.width() / len(visible_data))
                        y = half_h - sample * half_h
                        path.lineTo(x, y)
                else:
                    step = int(samples_per_pixel)
                    path.moveTo(0, half_h)
                    for i in range(self.width()):
                        start = i * step
                        end = start + step
                        if start >= len(visible_data): break
                        
                        chunk = visible_data[start:end]
                        min_val = np.min(chunk)
                        max_val = np.max(chunk)
                        
                        y_max = half_h - max_val * half_h
                        y_min = half_h - min_val * half_h
                        
                        painter.setPen(QtGui.QPen(self.waveform_color, 1))
                        painter.drawLine(i, int(y_min), i, int(y_max))
                
                if not path.isEmpty():
                    painter.setPen(QtGui.QPen(self.waveform_color, 1))
                    painter.drawPath(path)

        start_x = self._ms_to_x(self.selection_start_ms)
        end_x = self._ms_to_x(self.selection_end_ms)
        painter.fillRect(QtCore.QRectF(start_x, 0, end_x - start_x, self.height()), self.selection_color)
        
        if self.view_start_ms <= self.playhead_ms <= self.view_end_ms:
            playhead_x = self._ms_to_x(self.playhead_ms)
            painter.setPen(self.playhead_color)
            painter.drawLine(int(playhead_x), 0, int(playhead_x), self.height())
        
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.duration_ms > 0:
            seek_ms = self._x_to_ms(event.pos().x())
            
            self.seekRequested.emit(seek_ms)
            
            self.is_selecting = True
            self.selection_start_ms = seek_ms
            self.selection_end_ms = seek_ms
            
            self.set_playhead(seek_ms) 
            self.rangeChanged.emit(self.selection_start_ms, self.selection_end_ms)
            self.update()

    def mouseMoveEvent(self, event):
        current_ms = self._x_to_ms(event.pos().x())
        self.setToolTip(f"{current_ms / 1000:.3f} s")

        if self.is_selecting and self.duration_ms > 0:
            start = min(self.selection_start_ms, current_ms)
            end = max(self.selection_start_ms, current_ms)
            if self.selection_start_ms != start or self.selection_end_ms != end:
                self.set_selection_range(start, end)
                self.rangeChanged.emit(start, end)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_selecting = False     
class WemScannerThread(QtCore.QThread):
    """A thread to scan for orphaned WEM files and return them as a list."""
    scan_finished = QtCore.pyqtSignal(list)

    def __init__(self, wem_root, known_ids, parent=None):
        super().__init__(parent)
        self.wem_root = wem_root
        self.known_ids = known_ids
        self._is_running = True

    def run(self):
        orphaned_entries = []
        if not os.path.exists(self.wem_root):
            self.scan_finished.emit([])
            return

        for root, _, files in os.walk(self.wem_root):
            if not self._is_running:
                break
                
            rel_path = os.path.relpath(root, self.wem_root)
            parts = rel_path.split(os.sep)
            
            lang = "SFX"
            if rel_path == '.' or rel_path == "SFX":
                lang = "SFX"
            elif parts[0] == "Media":
                if len(parts) > 1:
                    lang = parts[1] 
                else:
                    lang = "SFX"
            else:
                lang = rel_path

            for file in files:
                if not self._is_running:
                    break
                if not file.lower().endswith('.wem'):
                    continue

                file_id = os.path.splitext(file)[0]
                if file_id in self.known_ids:
                    continue

                full_path = os.path.join(root, file)
                
                short_name = f"{file_id}.wav"
                try:
                    analyzer = WEMAnalyzer(full_path)
                    if analyzer.analyze():
                        markers = analyzer.get_markers_info()
                        if markers and markers[0]['label']:
                            short_name = f"{markers[0]['label']}.wav"
                except Exception:
                    pass

                new_entry = {
                    "Id": file_id,
                    "Language": lang,
                    "ShortName": short_name, 
                    "Path": file, 
                    "Source": "ScannedFromFileSystem"
                }
                orphaned_entries.append(new_entry)
        
        self.scan_finished.emit(orphaned_entries)

    def stop(self):
        self._is_running = False       
class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, existing_data=None, translator=None):
        super().__init__(parent)
        self.parent_app = parent
        self.is_edit_mode = existing_data is not None
        self.tr = translator if translator else lambda key: key
        self.setWindowTitle(self.tr("edit_profile") if self.is_edit_mode else self.tr("create_profile"))
        self.setMinimumWidth(400)

        self.layout = QtWidgets.QFormLayout(self)
        
        self.name_edit = QtWidgets.QLineEdit()
        self.author_edit = QtWidgets.QLineEdit()
        self.version_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setFixedHeight(80)
        
        self.icon_path = ""
        self.icon_preview = QtWidgets.QLabel(self.tr("no_icon_selected"))
        self.icon_preview.setFixedSize(64, 64)
        self.icon_preview.setStyleSheet("border: 1px solid #ccc; text-align: center;")
        self.icon_preview.setAlignment(QtCore.Qt.AlignCenter)
        
        icon_button = QtWidgets.QPushButton(self.tr("browse"))
        icon_button.clicked.connect(self.select_icon)
        
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.icon_preview)
        icon_layout.addWidget(icon_button)
        icon_layout.addStretch()

        if self.is_edit_mode:
            profile_name = os.path.basename(existing_data["path"])
            self.name_edit.setText(profile_name)
            self.name_edit.setReadOnly(True) 
            
            info = existing_data["data"]
            self.author_edit.setText(info.get("author", ""))
            self.version_edit.setText(info.get("version", "1.0"))
            self.description_edit.setPlainText(info.get("description", ""))
            
            self.icon_path = existing_data["icon"]
            if os.path.exists(self.icon_path):
                pixmap = QtGui.QPixmap(self.icon_path)
                self.icon_preview.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))

        self.layout.addRow(self.tr("profile_name"), self.name_edit)
        self.layout.addRow(self.tr("author"), self.author_edit)
        self.layout.addRow(self.tr("version"), self.version_edit)
        self.layout.addRow(self.tr("description"), self.description_edit)
        self.layout.addRow(self.tr("icon_png"), icon_layout)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def select_icon(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("select_icon"), "", f"{self.tr('png_images')} (*.png)")
        if path:
            self.icon_path = path
            pixmap = QtGui.QPixmap(path)
            self.icon_preview.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "icon_path": self.icon_path,
            "info": {
                "author": self.author_edit.text().strip(),
                "version": self.version_edit.text().strip(),
                "description": self.description_edit.toPlainText().strip()
            }
        }
    
    def accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, self.tr("validation_error"), self.tr("profile_name_empty"))
            return
        super().accept()         
class ProfileManagerDialog(QtWidgets.QDialog):
    profile_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.settings = parent.settings
        self.tr = parent.tr if hasattr(parent, 'tr') else lambda key: key
        
        self.setWindowTitle(self.tr("profile_manager_title"))
        self.setMinimumSize(850, 550) 

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        left_panel = QtWidgets.QFrame()
        left_panel.setFrameShape(QtWidgets.QFrame.StyledPanel)
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        self.profile_list = QtWidgets.QListWidget()
        self.profile_list.currentItemChanged.connect(self.display_profile_info)
        self.profile_list.setSpacing(3)
        self.profile_list.setIconSize(QtCore.QSize(32, 32)) 
        left_layout.addWidget(self.profile_list)

        left_button_layout = QtWidgets.QGridLayout()
        add_new_btn = QtWidgets.QPushButton(self.tr("create_new_profile_btn"))
        add_existing_btn = QtWidgets.QPushButton(self.tr("add_existing_profile_btn"))
        import_pak_btn = QtWidgets.QPushButton(self.tr("import_mod_from_pak"))
        remove_btn = QtWidgets.QPushButton(self.tr("remove_from_list_btn"))
        
        add_new_btn.clicked.connect(self.create_new_profile)
        add_existing_btn.clicked.connect(self.add_existing_profile)
        import_pak_btn.clicked.connect(self.import_mod_from_pak)
        remove_btn.clicked.connect(self.remove_selected_profile)

        left_button_layout.addWidget(add_new_btn, 0, 0)
        left_button_layout.addWidget(add_existing_btn, 0, 1)
        left_button_layout.addWidget(import_pak_btn, 1, 0, 1, 2)
        left_button_layout.addWidget(remove_btn, 2, 0, 1, 2)
        left_layout.addLayout(left_button_layout)
        
        main_layout.addWidget(left_panel, 2)

        right_panel = QtWidgets.QGroupBox()
        right_panel.setStyleSheet("QGroupBox { padding-top: 10px; }")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        header_layout = QtWidgets.QHBoxLayout()
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("border: 1px solid #888; border-radius: 5px;")
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        
        title_layout = QtWidgets.QVBoxLayout()
        self.name_label = QtWidgets.QLabel(self.tr("select_a_profile"))
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.path_label = QtWidgets.QLabel()
        self.path_label.setStyleSheet("color: #888;")
        self.path_label.setWordWrap(True)
        title_layout.addWidget(self.name_label)
        title_layout.addWidget(self.path_label)
        
        header_layout.addWidget(self.icon_label)
        header_layout.addLayout(title_layout)
        right_layout.addLayout(header_layout)

        self.details_tabs = QtWidgets.QTabWidget()
        right_layout.addWidget(self.details_tabs)

        info_tab = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_tab)
        
        details_layout = QtWidgets.QFormLayout()
        details_layout.setContentsMargins(10, 15, 10, 15)
        details_layout.setSpacing(10)
        self.author_label = QtWidgets.QLabel()
        self.version_label = QtWidgets.QLabel()
        details_layout.addRow(f"<b>{self.tr('author')}:</b>", self.author_label)
        details_layout.addRow(f"<b>{self.tr('version')}:</b>", self.version_label)
        info_layout.addLayout(details_layout)
        
        self.description_text = QtWidgets.QTextBrowser()
        self.description_text.setOpenExternalLinks(True)
        info_layout.addWidget(self.description_text)
        self.details_tabs.addTab(info_tab, self.tr("info"))
        
        stats_tab = QtWidgets.QWidget()
        stats_layout = QtWidgets.QVBoxLayout(stats_tab)
        
        general_group = QtWidgets.QGroupBox(self.tr("general_stats_group"))
        general_layout = QtWidgets.QFormLayout(general_group)
        self.audio_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.subtitle_files_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        self.mod_size_label = QtWidgets.QLabel(self.tr("calculating_stats"))
        general_layout.addRow(self.tr("total_audio_files"), self.audio_files_label)
        general_layout.addRow(self.tr("total_subtitle_files"), self.subtitle_files_label)
        general_layout.addRow(self.tr("total_mod_size"), self.mod_size_label)
        stats_layout.addWidget(general_group)
        
        subtitle_group = QtWidgets.QGroupBox(self.tr("subtitle_stats_group"))
        subtitle_layout = QtWidgets.QFormLayout(subtitle_group)
        self.modified_subs_label = QtWidgets.QLabel()
        subtitle_layout.addRow(self.tr("modified_subtitle_entries"), self.modified_subs_label)
        stats_layout.addWidget(subtitle_group)
        
        stats_layout.addStretch()
        self.details_tabs.addTab(stats_tab, self.tr("project_statistics_title"))

        self.activate_btn = QtWidgets.QPushButton()
        self.edit_btn = QtWidgets.QPushButton(f"{self.tr('edit_details_btn')}")
        self.edit_btn.clicked.connect(self.edit_profile)
        
        bottom_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout.addWidget(self.edit_btn)
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.activate_btn)
        right_layout.addLayout(bottom_button_layout)

        main_layout.addWidget(right_panel, 3)

        self.populate_profile_list()
    def import_mod_from_pak(self):
        pak_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("select_pak_to_import"),
            self.settings.data.get("game_path", ""),
            f"{self.tr('pak_files')} (*.pak)"
        )

        if not pak_path:
            return

        default_profile_name = os.path.splitext(os.path.basename(pak_path))[0]
        if default_profile_name.upper().endswith("_P"):
            default_profile_name = default_profile_name[:-2]

        profile_name, ok = QtWidgets.QInputDialog.getText(
            self,
            self.tr("import_mod_title"),
            self.tr("enter_profile_name_for_pak"),
            QtWidgets.QLineEdit.Normal,
            default_profile_name
        )

        if not ok or not profile_name.strip():
            return
            
        profile_name = profile_name.strip()

        if profile_name in self.settings.data.get("mod_profiles", {}):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("profile_exists_error"))
            return
        self.profile_name_for_import = profile_name
        self.progress_dialog = ProgressDialog(self.parent_app, self.tr("importing_mod_progress"))
        self.progress_dialog.progress.setRange(0, 0)
        self.progress_dialog.show()

        self.import_thread = ImportModThread(self.parent_app, pak_path, profile_name)
        self.import_thread.finished.connect(self.on_import_mod_finished)
        self.import_thread.start()

    def on_import_mod_finished(self, success, message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if success:
            profile_name = getattr(self, 'profile_name_for_import', None)
            
            if profile_name:

                profiles_root = self.settings.data.get("mods_root_path")
                if not profiles_root:
                    
                    profiles_root = os.path.join(self.parent_app.base_path, "Profiles")

                new_profile_path = os.path.join(profiles_root, profile_name)
                new_mod_p_path = os.path.join(new_profile_path, f"{profile_name}_P")

                if not hasattr(self.parent_app, 'profiles'):
                    self.parent_app.profiles = {}
                
                self.parent_app.profiles[profile_name] = {
                    "path": new_profile_path,
                    "mod_p_path": new_mod_p_path,
                    "icon": os.path.join(new_profile_path, "icon.png"),
                    "data": {"author": "Imported", "version": "1.0", "description": "Imported from .pak"}
                }

                self.settings.data.get("mod_profiles", {})[profile_name] = new_profile_path
                
                self.parent_app.set_active_profile(profile_name)
                
                if self.parent_app.active_profile_name != profile_name:
                    self.parent_app.active_profile_name = profile_name
                    self.parent_app.mod_p_path = new_mod_p_path
                    self.parent_app.setWindowTitle(f"{self.parent_app.tr('app_title')} - [{profile_name}]")
                    self.settings.data["active_profile"] = profile_name
                    self.settings.save()
                    
                    if hasattr(self.parent_app, 'update_profile_ui'):
                        self.parent_app.update_profile_ui()

            self.populate_profile_list()
            self.profile_changed.emit()

            reply = QtWidgets.QMessageBox.question(
                self,
                self.tr("import_successful_title"),
                f"{message}\n\n"
                f"It is highly recommended to rebuild the BNK index for imported mods.\n"
                f"Do you want to proceed with the rebuild now?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                self.close() 
                QtCore.QTimer.singleShot(300, lambda: self.parent_app.rebuild_bnk_index(confirm=False))
            
        else:
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("import_failed_title"),
                message
            )
            DEBUG.log(f"Mod import failed: {message}", "ERROR")
    def populate_profile_list(self):
        self.profile_list.clear()
        profiles = self.settings.data.get("mod_profiles", {})
        active_profile = self.settings.data.get("active_profile", "")

        for name, path in sorted(profiles.items()):
            item = QtWidgets.QListWidgetItem(name)
            
            icon_path = os.path.join(path, "icon.png")
            if os.path.exists(icon_path):
                item.setIcon(QtGui.QIcon(icon_path))
            else:
           
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))

            if name == active_profile:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))

            self.profile_list.addItem(item)
        
        if self.profile_list.count() > 0:
            self.profile_list.setCurrentRow(0)

    def display_profile_info(self, current, previous):
        if not current:
            self.name_label.setText(self.parent_app.tr("select_a_profile"))
            self.icon_label.clear()
            self.author_label.clear()
            self.version_label.clear()
            self.path_label.clear()
            self.description_text.clear()
            self.activate_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            return

        self.activate_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        profile_name = current.text()
        active_profile = self.settings.data.get("active_profile", "")
        
     
        try:
            self.activate_btn.clicked.disconnect()
        except TypeError:
            pass

        if profile_name == active_profile:
            self.activate_btn.setText(self.parent_app.tr("active_profile_btn"))
            self.activate_btn.setEnabled(False)
            self.activate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        else:
            self.activate_btn.setText(self.parent_app.tr("activate_profile_btn"))
            self.activate_btn.setEnabled(True)
            self.activate_btn.setStyleSheet("") 
            self.activate_btn.clicked.connect(self.activate_profile)

        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)

        self.name_label.setText(profile_name)
        self.path_label.setText(profile_path)
        
        icon_path = os.path.join(profile_path, "icon.png")
        if os.path.exists(icon_path):
            pixmap = QtGui.QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self.icon_label.setText(self.parent_app.tr("no_icon_selected").replace(" ", "\n"))
            self.icon_label.setPixmap(QtGui.QPixmap())

        json_path = os.path.join(profile_path, "profile.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
                self.author_label.setText(data.get("author", "N/A"))
                self.version_label.setText(data.get("version", "N/A"))
                self.description_text.setMarkdown(data.get("description", "<i>No description.</i>"))
            except Exception:
                self.author_label.setText(self.parent_app.tr("error_author"))
                self.description_text.setText(self.parent_app.tr("error_reading_profile"))
        self.calculate_statistics_for_profile(profile_name)
    def calculate_statistics_for_profile(self, profile_name):
        self.clear_stats_labels() 
        
        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)
        if not profile_path: return
        
        mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
        if not os.path.isdir(mod_p_path): return
        
        self.stats_thread = threading.Thread(target=self._calculate_stats_thread, args=(mod_p_path, profile_name))
        self.stats_thread.daemon = True
        self.stats_thread.start()

    def _calculate_stats_thread(self, mod_p_path, profile_name):
        audio_files = 0
        subtitle_files = 0
        total_size = 0

        for root, dirs, files in os.walk(mod_p_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    if file.endswith(".wem"):
                        audio_files += 1
                    elif file.endswith(".locres"):
                        subtitle_files += 1
                except OSError:
                    continue
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024*1024):.2f} MB"
        else:
            size_str = f"{total_size / 1024:.2f} KB"
            
        QtCore.QMetaObject.invokeMethod(self, "update_stats_labels", QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(int, audio_files),
                                        QtCore.Q_ARG(int, subtitle_files),
                                        QtCore.Q_ARG(str, size_str),
                                        QtCore.Q_ARG(str, profile_name))
    
    @QtCore.pyqtSlot(int, int, str, str)
    def update_stats_labels(self, audio_count, subtitle_count, size_str, profile_name):

        current_item = self.profile_list.currentItem()
        if not current_item or current_item.text() != profile_name:
            return

        self.audio_files_label.setText(str(audio_count))
        self.subtitle_files_label.setText(str(subtitle_count))
        self.mod_size_label.setText(size_str)
        
        if self.parent_app.active_profile_name == profile_name:
            modified_count = len(self.parent_app.modified_subtitles)
            self.modified_subs_label.setText(str(modified_count))
        else:
            self.modified_subs_label.setText("N/A (profile not active)")

    def clear_stats_labels(self):
        self.audio_files_label.setText(self.tr("calculating_stats"))
        self.subtitle_files_label.setText(self.tr("calculating_stats"))
        self.mod_size_label.setText(self.tr("calculating_stats"))
        self.modified_subs_label.setText(self.tr("calculating_stats"))
    def edit_profile(self):
        current = self.profile_list.currentItem()
        if not current: return
        
        profile_name = current.text()
        profiles = self.settings.data.get("mod_profiles", {})
        profile_path = profiles.get(profile_name)
        
        existing_data = {
            "path": profile_path,
            "icon": os.path.join(profile_path, "icon.png")
        }
        try:
            with open(os.path.join(profile_path, "profile.json"), 'r', encoding='utf-8') as f:
                existing_data["data"] = json.load(f)
        except:
             existing_data["data"] = {}
        
        dialog = ProfileDialog(self, existing_data=existing_data, translator=self.parent_app.tr)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            
            with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            icon_dest_path = os.path.join(profile_path, "icon.png")
            if profile_data["icon_path"] and os.path.exists(profile_data["icon_path"]):
                shutil.copy(profile_data["icon_path"], icon_dest_path)
            elif not profile_data["icon_path"] and os.path.exists(icon_dest_path):

                os.remove(icon_dest_path)

            self.display_profile_info(current, None)
            self.profile_changed.emit()

    def create_new_profile(self):
        dialog = ProfileDialog(self, translator=self.parent_app.tr)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            name = data["name"]

            if name in self.settings.data.get("mod_profiles", {}):
                QtWidgets.QMessageBox.warning(self, self.parent_app.tr("error"), self.parent_app.tr("profile_exists_error"))
                return

            profiles_root = os.path.join(self.parent_app.base_path, "Profiles")
            profile_path = os.path.join(profiles_root, name)
            mod_p_path = os.path.join(profile_path, f"{name}_P")
            
            try:
                os.makedirs(profiles_root, exist_ok=True)
                
                os.makedirs(mod_p_path, exist_ok=True)
                if data["icon_path"]:
                    shutil.copy(data["icon_path"], os.path.join(profile_path, "icon.png"))
                
                with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                    json.dump(data["info"], f, indent=2)

                self.settings.data["mod_profiles"][name] = profile_path
                self.settings.save()
                self.populate_profile_list()
                self.profile_changed.emit()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, self.parent_app.tr("error"), self.parent_app.tr("create_profile_error").format(e=e))

    def add_existing_profile(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.parent_app.tr("select_existing_profile"))
        if not folder:
            return
        
        profile_name = os.path.basename(folder)
        mod_p_folder = f"{profile_name}_P"
        
        if not os.path.exists(os.path.join(folder, mod_p_folder)):
            QtWidgets.QMessageBox.warning(self, self.parent_app.tr("invalid_profile_folder"), self.parent_app.tr("invalid_profile_folder").format(folder=mod_p_folder))
            return

        if profile_name in self.settings.data.get("mod_profiles", {}):
            QtWidgets.QMessageBox.warning(self, self.parent_app.tr("error"), self.parent_app.tr("profile_already_added"))
            return

        self.settings.data["mod_profiles"][profile_name] = folder
        self.settings.save()
        self.populate_profile_list()
        self.profile_changed.emit()

    def remove_selected_profile(self):
        current = self.profile_list.currentItem()
        if not current:
            return

        name = current.text()
        reply = QtWidgets.QMessageBox.question(self, self.parent_app.tr("remove_profile_title"), self.parent_app.tr("remove_profile_text").format(name=name), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            if self.settings.data["active_profile"] == name:
                self.settings.data["active_profile"] = ""
            
            del self.settings.data["mod_profiles"][name]
            self.settings.save()
            self.populate_profile_list()
            self.profile_changed.emit()

    def activate_profile(self):
        current = self.profile_list.currentItem()
        if not current:
            return
        
        name = current.text()
        self.settings.data["active_profile"] = name
        self.settings.save()
        self.populate_profile_list()
        self.profile_changed.emit()
        QtWidgets.QMessageBox.information(self, self.parent_app.tr("profile_activated_title"), self.parent_app.tr("profile_activated_text").format(name=name))
class ImportModThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(bool, str) # success, message

    def __init__(self, parent_app, pak_path, profile_name):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.tr = parent_app.tr
        self.pak_path = pak_path
        self.profile_name = profile_name
        self.temp_extract_path = os.path.join(tempfile.gettempdir(), f"mod_import_{profile_name}")

    def run(self):
        try:
           
            if os.path.exists(self.temp_extract_path):
                shutil.rmtree(self.temp_extract_path)
            os.makedirs(self.temp_extract_path, exist_ok=True)
            
            command = [self.parent_app.repak_path, "unpack", self.pak_path, "-o", self.temp_extract_path]
            result = subprocess.run(
                command, capture_output=True, text=True, startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                raise Exception(f"Repak failed to unpack: {result.stderr}")

            profiles_root = os.path.join(self.parent_app.base_path, "Profiles")
            profile_path = os.path.join(profiles_root, self.profile_name)
            mod_p_path = os.path.join(profile_path, f"{self.profile_name}_P")
            os.makedirs(mod_p_path, exist_ok=True)

            unpacked_opp_path = os.path.join(self.temp_extract_path, "OPP")
            if not os.path.exists(unpacked_opp_path):
                raise Exception("Unpacked mod does not contain an 'OPP' folder.")
            
            windows_audio_path = os.path.join(unpacked_opp_path, "Content", "WwiseAudio", "Windows")
            
            if os.path.exists(windows_audio_path):
                needs_conversion = False
                
                for item in os.listdir(windows_audio_path):
                    item_path = os.path.join(windows_audio_path, item)
                    if os.path.isfile(item_path) and item.lower().endswith(".wem"):
                        needs_conversion = True
                        break
                
                if not needs_conversion:
                    for item in os.listdir(windows_audio_path):
                        item_path = os.path.join(windows_audio_path, item)
                        if os.path.isdir(item_path) and item != "Media":
                            for sub_item in os.listdir(item_path):
                                if sub_item.lower().endswith(".wem"):
                                    needs_conversion = True
                                    break
                        if needs_conversion: break

                if needs_conversion:
                   
                    should_convert = QtCore.QMetaObject.invokeMethod(
                        self.parent_app, 
                        "_ask_convert_old_mod_structure", 
                        QtCore.Qt.BlockingQueuedConnection,
                        QtCore.Q_RETURN_ARG(bool)
                    )
                    
                    if should_convert:
                        self.convert_structure_to_media(windows_audio_path)
                    else:
                        DEBUG.log("User declined structure conversion.")

            destination_opp_path = os.path.join(mod_p_path, "OPP")
            if os.path.exists(destination_opp_path):
                shutil.rmtree(destination_opp_path)
            shutil.copytree(unpacked_opp_path, destination_opp_path)

            bnk_deleted_count = 0
            for root, dirs, files in os.walk(destination_opp_path):
                for file in files:
                    if file.lower().endswith(".bnk"):
                        os.remove(os.path.join(root, file))
                        bnk_deleted_count += 1
            if bnk_deleted_count > 0:
                DEBUG.log(f"Removed {bnk_deleted_count} outdated BNK files from imported mod to prevent conflicts.")

            watermark_path = os.path.join(destination_opp_path, "CreatedByAudioEditor.txt")
            if os.path.exists(watermark_path):
                os.remove(watermark_path)

            profile_info = {
                "author": "Imported",
                "version": "1.0",
                "description": f"This profile was imported from '{os.path.basename(self.pak_path)}'."
            }
            with open(os.path.join(profile_path, "profile.json"), 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)
            
            self.parent_app.settings.data["mod_profiles"][self.profile_name] = profile_path
            self.parent_app.settings.save()
            
            self.finished.emit(True, self.tr("import_successful_message").format(
                pak_name=os.path.basename(self.pak_path),
                profile_name=self.profile_name
            ))

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if os.path.exists(self.temp_extract_path):
                shutil.rmtree(self.temp_extract_path)

    def convert_structure_to_media(self, windows_path):
        """Moves .wem files into a 'Media' subfolder structure."""
        DEBUG.log("Converting old mod structure to new 'Media' format...")
        
        media_root = os.path.join(windows_path, "Media")
        os.makedirs(media_root, exist_ok=True)
        
        items = list(os.listdir(windows_path))
        
        for item in items:
            item_path = os.path.join(windows_path, item)
            
            if item == "Media":
                continue
                
            if os.path.isfile(item_path) and item.lower().endswith(".wem"):
                dest_path = os.path.join(media_root, item)
                try:
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    shutil.move(item_path, dest_path)
                    DEBUG.log(f"Moved {item} to Media root")
                except Exception as e:
                    DEBUG.log(f"Failed to move {item}: {e}", "ERROR")
                
            elif os.path.isdir(item_path):
                lang_folder_name = item
                lang_source_path = item_path
                
                has_wems = any(f.lower().endswith(".wem") for f in os.listdir(lang_source_path))
                
                if has_wems:
                    lang_media_dest = os.path.join(media_root, lang_folder_name)
                    os.makedirs(lang_media_dest, exist_ok=True)
                    
                    for sub_item in os.listdir(lang_source_path):
                        sub_item_path = os.path.join(lang_source_path, sub_item)
                        if os.path.isfile(sub_item_path) and sub_item.lower().endswith(".wem"):
                            dest_sub_path = os.path.join(lang_media_dest, sub_item)
                            try:
                                if os.path.exists(dest_sub_path):
                                    os.remove(dest_sub_path)
                                shutil.move(sub_item_path, dest_sub_path)
                                DEBUG.log(f"Moved {sub_item} to Media/{lang_folder_name}")
                            except Exception as e:
                                DEBUG.log(f"Failed to move {sub_item}: {e}", "ERROR")
                    
                    if not os.listdir(lang_source_path):
                        try:
                            os.rmdir(lang_source_path)
                        except OSError:
                            pass 
                    
        DEBUG.log("Structure conversion complete.")  
class SaveSubtitlesThread(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(int, str)
    finished = QtCore.pyqtSignal(int, list) # count, errors_list

    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.tr = parent_app.tr
        
        self.mod_p_path = self.parent_app.mod_p_path
        self.subtitles = self.parent_app.subtitles.copy()
        self.original_subtitles = self.parent_app.original_subtitles.copy()
        self.all_subtitle_files = self.parent_app.all_subtitle_files.copy()
        self.dirty_files = list(self.parent_app.dirty_subtitle_files)
        self.locres_manager = self.parent_app.locres_manager

    def run(self):
        saved_files_count = 0
        errors = []
        
        try:
            total_files = len(self.dirty_files)
            if total_files == 0:
                self.finished.emit(0, [])
                return

            for i, original_path in enumerate(self.dirty_files):
                QtCore.QThread.msleep(1)
                
                file_info = self.find_file_info_by_path(original_path)
                if not file_info:
                    errors.append(f"Could not find file info for path: {original_path}")
                    continue

                progress = int(((i + 1) / total_files) * 100)
                self.progress_updated.emit(progress, self.tr("Saving") + f" {file_info['filename']}...")
                
                target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization", file_info['category'], file_info['language'])
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file_info['filename'])

                try:
                    subtitles_to_write = self.locres_manager.export_locres(original_path)
                    
                    for key in subtitles_to_write.keys():
                        if key in self.subtitles:
                            subtitles_to_write[key] = self.subtitles[key]
                    
                    shutil.copy2(original_path, target_path)

                    if not self.locres_manager.import_locres(target_path, subtitles_to_write):
                        raise Exception("UnrealLocresManager failed to import data.")
                    
                    saved_files_count += 1
                except Exception as e:
                    msg = f"Failed to save {file_info['filename']}: {e}"
                    errors.append(msg)
                    DEBUG.log(msg, "ERROR")

            self.finished.emit(saved_files_count, errors)

        except Exception as e:
            errors.append(f"A critical error occurred during saving: {e}")
            self.finished.emit(saved_files_count, errors)

    def find_file_info_by_path(self, path_to_find):
        for info in self.all_subtitle_files.values():
            if info['path'] == path_to_find:
                return info
        return None
class WemSubtitleApp(QtWidgets.QMainWindow):
    log_signal = QtCore.pyqtSignal(str, str)
    def __init__(self):
        super().__init__()
        DEBUG.log("=== OutlastTrials AudioEditor Starting ===")
        if getattr(sys, 'frozen', False):

            self.base_path = os.path.dirname(sys.executable)
        else:

            self.base_path = os.path.dirname(os.path.abspath(__file__))
        DEBUG.setup_logging(self.base_path)
        self.wem_index = None
        self.settings = AppSettings()
        self.translations = TRANSLATIONS
        self.current_lang = self.settings.data["ui_language"]
        
        self.setWindowTitle(self.tr("app_title"))
        icon_path = os.path.join(self.base_path, "data", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            DEBUG.log(f"Application icon not found at {icon_path}, using default.", "WARNING")
        
        
        
        DEBUG.log(f"Base path: {self.base_path}")
        
        self.data_path = os.path.join(self.base_path, "data")
        self.libs_path = os.path.join(self.base_path, "libs")   
        
        self.unreal_locres_path = os.path.join(self.data_path, "UnrealLocres.exe")
        self.repak_path = os.path.join(self.data_path, "repak.exe")
        self.vgmstream_path = os.path.join(self.data_path, "vgmstream", "vgmstream-cli.exe")
        
        
        self.wem_root = os.path.join(self.base_path, "Wems")
        json_path = os.path.join(self.wem_root, "SFX", "SoundbanksInfo.json")
        xml_path = os.path.join(self.wem_root, "SFX", "SoundbanksInfo.xml")
        if os.path.exists(json_path):
            self.soundbanks_path = json_path
        elif os.path.exists(xml_path):
            self.soundbanks_path = xml_path
        else:
            self.soundbanks_path = json_path 
        self.active_profile_name = None
        self.mod_p_path = None
        self.orphaned_cache_path = os.path.join(self.base_path, "orphaned_files_cache.json")
        self.check_required_files()
        self.orphaned_files_cache = []
        DEBUG.log(f"Paths configured:")
        DEBUG.log(f"  data_path: {self.data_path}")
        DEBUG.log(f"  unreal_locres_path: {self.unreal_locres_path}")
        DEBUG.log(f"  repak_path: {self.repak_path}")
        DEBUG.log(f"  vgmstream_path: {self.vgmstream_path}")

        self.locres_manager = UnrealLocresManager(self.unreal_locres_path)
        self.subtitles = {}
        self.original_subtitles = {}
        self.all_subtitle_files = {}
        self.key_to_file_map = {}
        self.all_files = self.load_all_soundbank_files(self.soundbanks_path)
        self.entries_by_lang = self.group_by_language()
        self.show_orphans_checkbox = QtWidgets.QCheckBox("Show Scanned Files")
        self.show_orphans_checkbox.setToolTip("Show/hide audio files found by scanning the 'Wems' folder that are not in the main database.")
        self.show_orphans_checkbox.setChecked(self.settings.data.get("show_orphaned_files", False))
        self.show_orphans_checkbox.stateChanged.connect(self.on_show_orphans_toggled)
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
        self.dirty_subtitle_files = set()
        self.marked_items = {}
        if "marked_items" in self.settings.data:
            for key, data in self.settings.data["marked_items"].items():
                self.marked_items[key] = {
                    'color': QtGui.QColor(data['color']) if 'color' in data else None,
                    'tag': data.get('tag', '')
                }
        self.current_file_duration = 0

        self.debug_window = None
        self.updater_thread = None
        self.first_show_check_done = False
        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_subtitles)
        self.auto_save_enabled = False  
        self.bnk_cache_orig = {}
        self.bnk_cache_mod = {}
        self.bnk_loader_thread = None
        self.first_show_check_done = False
        self.current_bnk_request_id = 0
        self.search_timer = QtCore.QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(400) 
        self.search_timer.timeout.connect(self.perform_delayed_search)
        self.tree_loader_timer = QtCore.QTimer()
        self.tree_loader_timer.setInterval(0) 
        self.tree_loader_timer.timeout.connect(self._process_tree_batch)
        self.tree_loader_generator = None
        self.current_loading_lang = None
        self.create_ui()
        # QtCore.QTimer.singleShot(100, self.load_orphans_from_cache_or_scan) 
        self.apply_settings()
        self.restore_window_state()


        self.update_auto_save_timer()
        
        self.log_signal.connect(self.append_to_log_widget)
        DEBUG.log("=== OutlastTrials AudioEditor Started Successfully ===")
    def check_soundbanks_info(self):
        sfx_folder = os.path.join(self.wem_root, "SFX")
        
        json_path = os.path.join(sfx_folder, "SoundbanksInfo.json")
        xml_path = os.path.join(sfx_folder, "SoundbanksInfo.xml")

        if os.path.exists(json_path) or os.path.exists(xml_path):
            return 
        DEBUG.log("Neither SoundbanksInfo.json nor .xml found. Prompting user.", "WARNING")
        
        updater_tab_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.tr("resource_updater_tab"):
                updater_tab_index = i
                break

        if updater_tab_index == -1:
            QtWidgets.QMessageBox.critical(self,
                                        self.tr("critical_file_missing_title"),
                                        self.tr("critical_file_missing_message"))
            return

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(self.tr("soundbanksinfo_missing_title"))
        msg_box.setText(self.tr("soundbanksinfo_missing_message")) 
        msg_box.setInformativeText(self.tr("soundbanksinfo_missing_details"))
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        
        go_btn = msg_box.addButton(self.tr("go_to_updater_btn"), QtWidgets.QMessageBox.AcceptRole)
        later_btn = msg_box.addButton(self.tr("later_btn"), QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == go_btn:
            self.tabs.setCurrentIndex(updater_tab_index)
    def check_for_loose_wems(self):
        if not os.path.isdir(self.wem_root):
            return False

        loose_files = []
        for item in os.listdir(self.wem_root):
            item_path = os.path.join(self.wem_root, item)
            if os.path.isfile(item_path):
                loose_files.append(item)

        if not loose_files:
            return False

        DEBUG.log(f"Found {len(loose_files)} loose files in the Wems root directory.", "WARNING")

        sfx_path = os.path.join(self.wem_root, "SFX")
        os.makedirs(sfx_path, exist_ok=True)

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(self.tr("wems_folder_loose_files_title"))

        msg_box.setText(self.tr("wems_folder_loose_files_message").format(count=len(loose_files)).replace(" (.wem/.bnk)", ""))
        msg_box.setInformativeText(self.tr("wems_folder_loose_files_details"))
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        
        move_btn = msg_box.addButton(self.tr("move_all_files_btn"), QtWidgets.QMessageBox.AcceptRole)
        ignore_btn = msg_box.addButton(self.tr("ignore_btn"), QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()

        if msg_box.clickedButton() == move_btn:
            moved_count = 0
            errors = []
            for filename in loose_files:
                source_path = os.path.join(self.wem_root, filename)
                dest_path = os.path.join(sfx_path, filename)
                try:

                    if os.path.exists(dest_path):
                        errors.append(f"{filename}: File already exists in SFX folder.")
                        DEBUG.log(f"Skipped moving '{filename}', it already exists in SFX.", "WARNING")
                        continue
                    shutil.move(source_path, dest_path)
                    moved_count += 1
                    DEBUG.log(f"Moved '{filename}' to SFX folder.")
                except Exception as e:
                    error_text = str(e)
                    errors.append(f"{filename}: {error_text}")
                    DEBUG.log(f"Error moving '{filename}': {error_text}", "ERROR")
            
            result_message = self.tr("move_complete_message").format(count=moved_count)
            if errors:
                result_message += "\n\n" + self.tr("move_complete_errors").format(count=len(errors), errors="\n".join(errors))
            
            result_message += self.tr("move_complete_restart_note")
            
            QtWidgets.QMessageBox.information(self, self.tr("move_complete_title"), result_message)

        return True
    def check_initial_resources(self):
        updater_tab_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == self.tr("resource_updater_tab"):
                updater_tab_index = i
                break
        
        if updater_tab_index == -1:
            return False

        wems_path = os.path.join(self.base_path, "Wems")
        wems_exist = self._wems_folder_is_valid(wems_path)
        
        if not wems_exist:
            DEBUG.log("Wems folder is missing or invalid on startup.", "INFO")
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle(self.tr("initial_setup_title"))
            msg_box.setText(self.tr("wems_folder_missing_message"))
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            go_btn = msg_box.addButton(self.tr("go_to_updater_button"), QtWidgets.QMessageBox.AcceptRole)
            msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
            msg_box.exec_()
            if msg_box.clickedButton() == go_btn:
                self.tabs.setCurrentIndex(updater_tab_index)
            return True 
        loc_path = os.path.join(self.base_path, "Localization")
        if not os.path.isdir(loc_path) or not any(f.endswith('.locres') for f in os.listdir(loc_path) if os.path.isdir(os.path.join(loc_path, f)) for f in os.listdir(os.path.join(loc_path, f))):
            loc_files_exist = False
            if os.path.exists(loc_path):
                for root, _, files in os.walk(loc_path):
                    if any(f.endswith('.locres') for f in files):
                        loc_files_exist = True
                        break
            
            if not loc_files_exist:
                DEBUG.log("Localization folder has no .locres files on startup.", "INFO")
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle(self.tr("initial_setup_title"))
                msg_box.setText(self.tr("localization_folder_missing_message"))
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                go_btn = msg_box.addButton(self.tr("go_to_updater_button"), QtWidgets.QMessageBox.AcceptRole)
                msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
                msg_box.exec_()
                if msg_box.clickedButton() == go_btn:
                    self.tabs.setCurrentIndex(updater_tab_index)
                return True

        return False
    def _wems_folder_is_valid(self, directory):

        if not os.path.isdir(directory):
            return False
            
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.wem'):

                    return True
                    
        return False
    def showEvent(self, event):
        super().showEvent(event)
        
        if not self.first_show_check_done:
            self.first_show_check_done = True
            DEBUG.log("Application window shown for the first time. Scheduling initial checks.")
            
            def run_all_startup_checks():
    
                if self.check_initial_resources():
                    return
                
                loose_files_found = self.check_for_loose_wems()
            
                if not loose_files_found:
                    self.check_soundbanks_info()

                QtCore.QTimer.singleShot(1500, self.check_updates_on_startup)

            QtCore.QTimer.singleShot(100, run_all_startup_checks)
    def verify_bnk_sizes(self):
        if not self.ensure_active_profile():
            return

        progress = ProgressDialog(self, "Verifying Mod Integrity...")
        progress.show()
        
        self.verification_thread = threading.Thread(target=self._verify_mod_integrity_thread, args=(progress,))
        self.verification_thread.daemon = True
        self.verification_thread.start()

    
    def _verify_batch(self, wem_files, id_to_entry_map, bnk_files_info):
        mismatches = []
        bnk_editor_cache = {} 
        
        for wem_path in wem_files:
            wem_name = os.path.basename(wem_path)
            
            try:
                file_id = os.path.splitext(wem_name)[0]
                source_id = int(file_id)
            except ValueError:
                continue

            entry = id_to_entry_map.get(file_id)
            if not entry:
                continue
            
            real_wem_size = os.path.getsize(wem_path)
            
            bnk_info, mod_bnk_path = self._find_bnk_for_entry_with_cache(
                entry, bnk_files_info, bnk_editor_cache
            )

            if bnk_info:
                if bnk_info.file_size != real_wem_size:
                    mismatches.append({
                        "type": "Size Mismatch",
                        "bnk_path": mod_bnk_path,
                        "source_id": source_id,
                        "short_name": entry.get("ShortName", wem_name),
                        "bnk_size": bnk_info.file_size,
                        "wem_size": real_wem_size
                    })
            else:
                source_type = entry.get("Source", "")
                if source_type not in ["StreamedFiles", "MediaFilesNotInAnyBank"]:
                    mismatches.append({
                        "type": "BNK Entry Missing",
                        "bnk_path": "N/A",
                        "source_id": source_id,
                        "short_name": entry.get("ShortName", wem_name),
                        "bnk_size": "N/A",
                        "wem_size": real_wem_size
                    })
        
        return mismatches, len(wem_files)

    def _find_bnk_for_entry_with_cache(self, entry, bnk_files_info, cache):
        source_id = int(entry.get("Id"))
        
        for bnk_path, bnk_type in bnk_files_info:
            if bnk_path not in cache:
                try:
                    cache[bnk_path] = BNKEditor(bnk_path)
                except Exception:
                    continue
            
            original_bnk = cache[bnk_path]
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if bnk_type == 'sfx':
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

            if os.path.exists(mod_bnk_path):
                if mod_bnk_path not in cache:
                    try:
                        cache[mod_bnk_path] = BNKEditor(mod_bnk_path)
                    except Exception:
                        continue
                
                mod_editor = cache[mod_bnk_path]
                entries = mod_editor.find_sound_by_source_id(source_id)
                if entries:
                    return entries[0], mod_bnk_path
        
        return None, None

    def _find_bnk_for_entry_optimized(self, entry, modified_bnks, bnk_editor_cache):
        source_id = int(entry.get("Id"))
        
        for bnk_path, (mod_bnk_path, bnk_type) in modified_bnks.items():

            if bnk_path not in bnk_editor_cache:
                try:
                    bnk_editor_cache[bnk_path] = BNKEditor(bnk_path)
                except Exception:
                    continue
            
            original_bnk = bnk_editor_cache[bnk_path]
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if mod_bnk_path not in bnk_editor_cache:
                try:
                    bnk_editor_cache[mod_bnk_path] = BNKEditor(mod_bnk_path)
                except Exception:
                    continue
            
            mod_editor = bnk_editor_cache[mod_bnk_path]
            entries = mod_editor.find_sound_by_source_id(source_id)
            if entries:
                return entries[0], mod_bnk_path
        
        return None, None

    def _find_bnk_for_entry(self, entry):
        source_id = int(entry.get("Id"))
        
        bnk_files_info = self.find_relevant_bnk_files()

        for bnk_path, bnk_type in bnk_files_info:
            original_bnk = BNKEditor(bnk_path)
            if not original_bnk.find_sound_by_source_id(source_id):
                continue
            
            if bnk_type == 'sfx':
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

            if os.path.exists(mod_bnk_path):
                mod_editor = BNKEditor(mod_bnk_path)
                entries = mod_editor.find_sound_by_source_id(source_id)
                if entries:
                    return entries[0], mod_bnk_path
        
        return None, None
    def rebuild_bnk_index(self, confirm=True):
        if not self.ensure_active_profile():
            return

        if confirm:
            reply = QtWidgets.QMessageBox.question(
                self, 
                self.tr("rebuild_bnk_confirm_title"), 
                self.tr("rebuild_bnk_confirm_text"), 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        progress = ProgressDialog(self, self.tr("rebuilding_mod_bnk"))
        progress.show()
        
        self.rebuild_thread = threading.Thread(target=self._rebuild_bnk_thread, args=(progress,))
        self.rebuild_thread.daemon = True
        self.rebuild_thread.start()
    def find_all_original_bnks(self):
        all_bnks = []
        wems_root = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_root):
            return []
        for root, _, files in os.walk(wems_root):
            for file in files:
                if file.lower().endswith('.bnk'):
                    bnk_type = 'sfx' if os.path.basename(root) == "SFX" else 'lang'
                    all_bnks.append((os.path.join(root, file), bnk_type))
        return all_bnks
    def _rebuild_bnk_thread(self, progress):
        try:
            DEBUG.log("--- Starting BNK Rebuild (Robust Mode) ---")
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, 5), QtCore.Q_ARG(str, "Scanning modified audio files..."))

            mod_audio_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows")
            modified_wem_files = {}
            
            if os.path.exists(mod_audio_path):
                for root, _, files in os.walk(mod_audio_path):
                    for file in files:
                        if file.lower().endswith('.wem'):
                            file_id = os.path.splitext(file)[0]
                           
                            if file_id.isdigit():
                                full_path = os.path.join(root, file)
                                modified_wem_files[file_id] = os.path.getsize(full_path)

            if not modified_wem_files:
                raise FileNotFoundError("No modified audio files (IDs) found in MOD_P to rebuild.")

            total_wems = len(modified_wem_files)
            progress.details_updated.emit(f"Found {total_wems} modified WEM files.")
            
            all_original_bnks = self.find_all_original_bnks()
            
            bnk_update_map = {}
            
            bnk_editor_cache = {}

            for i, (file_id, new_size) in enumerate(modified_wem_files.items()):
                progress_percent = 10 + int((i / total_wems) * 30)
                if i % 10 == 0:
                    QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(int, progress_percent),
                                                    QtCore.Q_ARG(str, f"Mapping ID {file_id}..."))
                
                found_parent = False
                source_id_int = int(file_id)

                for original_bnk_path, bnk_type in all_original_bnks:
                    try:
                        if original_bnk_path not in bnk_editor_cache:
                           bnk_editor_cache[original_bnk_path] = BNKEditor(original_bnk_path)
                        
                        editor = bnk_editor_cache[original_bnk_path]
                        
                        if editor.find_sound_by_source_id(source_id_int):
                            if original_bnk_path not in bnk_update_map:
                                bnk_update_map[original_bnk_path] = {'type': bnk_type, 'wems': {}}
                            
                            bnk_update_map[original_bnk_path]['wems'][file_id] = new_size
                            found_parent = True
                       
                            break 
                    except Exception as e:
                        DEBUG.log(f"Error reading BNK {os.path.basename(original_bnk_path)}: {e}", "WARNING")
                
                if not found_parent:
                    DEBUG.log(f"Warning: ID {file_id} not found in any known SoundBank.", "WARNING")

            updated_count = 0
            created_count = 0
            total_bnks = len(bnk_update_map)
            
            for i, (original_bnk_path, data) in enumerate(bnk_update_map.items()):
                bnk_type = data['type']
                wems_to_update = data['wems'] # {id_str: size}
                
                progress_percent = 40 + int((i / total_bnks) * 60)
                bnk_name = os.path.basename(original_bnk_path)
                QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(int, progress_percent),
                                                QtCore.Q_ARG(str, f"Updating {bnk_name}..."))

                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(original_bnk_path, os.path.join(self.wem_root, "SFX"))
               
                    if rel_path.startswith(".."): rel_path = os.path.basename(original_bnk_path)
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(original_bnk_path, self.wem_root)
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

                old_fx_flags = {}
                if os.path.exists(mod_bnk_path):
                    try:
                        old_mod_editor = BNKEditor(mod_bnk_path)
                        for entry in old_mod_editor.find_all_sounds():
                            old_fx_flags[str(entry.source_id)] = entry.override_fx
                        os.remove(mod_bnk_path) 
                    except Exception: 
                        pass
                
                os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                shutil.copy2(original_bnk_path, mod_bnk_path)
                created_count += 1

                new_mod_editor = BNKEditor(mod_bnk_path)
                
                file_modified = False
                
                for file_id_str, new_size in wems_to_update.items():
                    source_id = int(file_id_str)
                    
                    fx_flag = old_fx_flags.get(file_id_str) 
                    
                    if new_mod_editor.modify_sound(source_id, new_size=new_size, override_fx=fx_flag):
                        updated_count += 1
                        file_modified = True
                        DEBUG.log(f"Updated {bnk_name}: ID {source_id} -> {new_size} bytes")
                    else:
                        DEBUG.log(f"FAILED to update {bnk_name}: ID {source_id} not found in binary scan!", "ERROR")

                if file_modified:
                    new_mod_editor.save_file()
                    
                    for file_id_str in wems_to_update.keys():
                        self.invalidate_bnk_cache(int(file_id_str))
                else:
                    DEBUG.log(f"No changes made to {bnk_name}, keeping original copy.", "WARNING")

            self.bnk_cache_mod.clear()
            
            QtCore.QMetaObject.invokeMethod(progress, "close", QtCore.Qt.QueuedConnection)
            
            final_message = (f"Rebuild Complete!\n\n"
                             f"Processed {len(modified_wem_files)} modified audio files.\n"
                             f"Re-created {created_count} BNK files.\n"
                             f"Updated {updated_count} size entries.")

            QtCore.QMetaObject.invokeMethod(self, "show_message_box", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, QtWidgets.QMessageBox.Information),
                                            QtCore.Q_ARG(str, self.tr("rebuild_complete_title")),
                                            QtCore.Q_ARG(str, final_message))
            
            current_lang = self.get_current_language()
            if current_lang:
                QtCore.QMetaObject.invokeMethod(self, "populate_tree", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(str, current_lang))

        except Exception as e:
            import traceback
            DEBUG.log(f"BNK Rebuild Critical Error: {e}\n{traceback.format_exc()}", "ERROR")
            QtCore.QMetaObject.invokeMethod(progress, "close", QtCore.Qt.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(self, "_show_bnk_verification_error", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, str(e)))
    @QtCore.pyqtSlot(list)
    def _show_bnk_verification_report(self, mismatches):

        if not mismatches:
            QtWidgets.QMessageBox.information(self, "Verification Complete", "All modified audio files are consistent with their BNK entries. No issues found!")
            return

        report_text = f"Found {len(mismatches)} issues in your mod.\n\n"
        report_text += "These problems can cause sounds to not play correctly in the game.\n\n"
        report_text += "Do you want to automatically fix these entries?"

        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("Mod Integrity Issues Found")
        dialog.setText(report_text)
        
        detailed_report = ""
        for item in mismatches:
            if item['type'] == 'Size Mismatch':
                bnk_name = os.path.basename(item['bnk_path'])
                detailed_report += (
                    f"Type: {item['type']} in {bnk_name}\n"
                    f"  Sound: {item['short_name']} (ID: {item['source_id']})\n"
                    f"  - BNK Size: {item['bnk_size']} bytes\n"
                    f"  - WEM Size: {item['wem_size']} bytes\n\n"
                )
            elif item['type'] == 'BNK Entry Missing':
                 detailed_report += (
                    f"Type: {item['type']}\n"
                    f"  Sound: {item['short_name']} (ID: {item['source_id']})\n"
                    f"  - A .wem file exists, but no corresponding entry was found in any modified .bnk file.\n\n"
                )
        dialog.setDetailedText(detailed_report)
        
        fix_btn = dialog.addButton("Fix All", QtWidgets.QMessageBox.AcceptRole)
        cancel_btn = dialog.addButton(QtWidgets.QMessageBox.Cancel)
        dialog.setDefaultButton(fix_btn)
        
        self.show_dialog(dialog)
        
        if dialog.clickedButton() == fix_btn:
            self.fix_bnk_mismatches(mismatches)

    @QtCore.pyqtSlot(str)
    def _show_bnk_verification_error(self, error_message):

        QtWidgets.QMessageBox.critical(self, "Verification Error", f"An error occurred during verification:\n\n{error_message}")

    def fix_bnk_mismatches(self, mismatches):

        progress = ProgressDialog(self, "Fixing Mod Issues...")
        progress.show()
        
        fixable_mismatches = [item for item in mismatches if item['type'] == 'Size Mismatch']

        if not fixable_mismatches:
            progress.close()
            QtWidgets.QMessageBox.information(self, "Fix Complete", "No automatically fixable issues were found (e.g., 'BNK Entry Missing').")
            return
        
        fixed_count = 0
        error_count = 0
        
        fixes_by_bnk = {}
        for item in fixable_mismatches:
            bnk_path = item['bnk_path']
            if bnk_path not in fixes_by_bnk:
                fixes_by_bnk[bnk_path] = []
            fixes_by_bnk[bnk_path].append(item)
            
        total_bnks_to_fix = len(fixes_by_bnk)
        
        for i, (bnk_path, items_to_fix) in enumerate(fixes_by_bnk.items()):
            bnk_name = os.path.basename(bnk_path)
            progress_percent = int((i / total_bnks_to_fix) * 100)
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, progress_percent), QtCore.Q_ARG(str, f"Fixing {bnk_name}..."))
            
            try:
                editor = BNKEditor(bnk_path)
                modified = False
                for item in items_to_fix:
                    if editor.modify_sound(item['source_id'], new_size=item['wem_size']):
                        fixed_count += 1
                        modified = True
                
                if modified:
                    editor.save_file()
   
                    for item in items_to_fix:
                        self.invalidate_bnk_cache(item['source_id'])

            except Exception as e:
                error_count += len(items_to_fix)
                DEBUG.log(f"Error fixing {bnk_name}: {e}", "ERROR")

        progress.close()
        
        message = f"Fixed {fixed_count} size mismatch issues."
        if error_count > 0:
            message += f"\nFailed to fix {error_count} entries. See debug console for details."
            
        QtWidgets.QMessageBox.information(self, "Fix Complete", message)    
    @QtCore.pyqtSlot(int, str, str)    
    def show_message_box(self, icon, title, text, informative_text="", detailed_text="", buttons=QtWidgets.QMessageBox.Ok):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        if informative_text:
            msg.setInformativeText(informative_text)
        if detailed_text:
            msg.setDetailedText(detailed_text)
        msg.setStandardButtons(buttons)
        msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint) 
        msg.show() 
        msg.raise_() 
        msg.activateWindow() 
        return msg.exec_() 

    def show_dialog(self, dialog):
        dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog.exec_()
    def get_mod_path(self, file_id, lang):
        if not self.mod_p_path:
            return None
            
        if lang != "SFX":
            new_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", lang, f"{file_id}.wem")
        else:
            new_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{file_id}.wem")
            
        if os.path.exists(new_path):
            return new_path
       
        if lang != "SFX":
            old_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            old_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            
        if os.path.exists(old_path):
            return old_path

        return new_path

    @QtCore.pyqtSlot(dict)
    def _add_orphaned_entry(self, entry):

        self.all_files.append(entry)
        lang = entry.get("Language", "SFX")
        self.entries_by_lang.setdefault(lang, []).append(entry)

        if lang in self.tab_widgets:
            widgets = self.tab_widgets[lang]
            tree = widgets["tree"]
            
            scanned_group_name = "Scanned From Filesystem"
            items = tree.findItems(scanned_group_name, QtCore.Qt.MatchStartsWith, 0)
            group_item = items[0] if items else None
            
            if not group_item:
                group_item = QtWidgets.QTreeWidgetItem(tree, [scanned_group_name, "", "", "", ""])
                group_item.setExpanded(True)
            
            self.add_tree_item(group_item, entry, lang)
            group_item.setText(0, f"{scanned_group_name} ({group_item.childCount()})")
            
            current_tab_index = self.tabs.indexOf(widgets["tree"].parent().parent())
            if current_tab_index != -1:
                total_count = len(self.entries_by_lang.get(lang, []))
                self.tabs.setTabText(current_tab_index, f"{lang} ({total_count})")

    def initialize_profiles_and_ui(self):

        profiles_root = os.path.join(self.base_path, "Profiles")
        legacy_mod_p_path = os.path.join(self.base_path, "MOD_P")
        
        if not os.path.isdir(profiles_root):
            DEBUG.log("Root 'Profiles' folder not found. Running first-time setup or migration.")
            
            if os.path.isdir(legacy_mod_p_path):
                self.handle_legacy_mod_p_migration(legacy_mod_p_path, profiles_root)
            else: 
                self.handle_new_user_setup(profiles_root)
        
        self.load_profiles_from_settings()
        return True

    def handle_new_user_setup(self, profiles_root):
        DEBUG.log("Performing automatic new user setup.")
        try:

            os.makedirs(profiles_root, exist_ok=True)
            
            default_profile_name = "Default"
            profile_path = os.path.join(profiles_root, default_profile_name)
            new_mod_p_path = os.path.join(profile_path, f"{default_profile_name}_P")
            
            os.makedirs(new_mod_p_path, exist_ok=True)
            
            profile_json_path = os.path.join(profile_path, "profile.json")
            profile_info = {
                "author": "New User", "version": "1.0",
                "description": "Default profile created on first launch."
            }
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)

            self.settings.data["mod_profiles"] = {default_profile_name: profile_path}
            self.settings.data["active_profile"] = default_profile_name
            self.settings.save()

            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("setup_complete_title"),
                self.tr("setup_complete_msg").format(mods_root=profiles_root)
            )
            return True

        except Exception as e:
            self.show_message_box(
                QtWidgets.QMessageBox.Critical,
                self.tr("setup_failed_title"),
                self.tr("setup_failed_msg").format(e=e)
            )
            return False
    def handle_legacy_mod_p_migration(self, legacy_mod_p_path, profiles_root):
        DEBUG.log(f"Performing automatic migration of '{legacy_mod_p_path}'")
        try:
            os.makedirs(profiles_root, exist_ok=True)
            
            default_profile_name = "Default"
            profile_path = os.path.join(profiles_root, default_profile_name)
            new_mod_p_path = os.path.join(profile_path, f"{default_profile_name}_P")
            
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)
            
            shutil.move(legacy_mod_p_path, new_mod_p_path)
            
            profile_json_path = os.path.join(profile_path, "profile.json")
            profile_info = {
                "author": "Migrated", "version": "1.0",
                "description": "This profile was automatically migrated from the legacy MOD_P folder."
            }
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, indent=2)

            self.settings.data["mod_profiles"] = {default_profile_name: profile_path}
            self.settings.data["active_profile"] = default_profile_name
            self.settings.save()

            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("migration_complete_title"),
                self.tr("migration_complete_msg").format(mods_root=profiles_root)
            )

        except Exception as e:
            self.show_message_box(
                QtWidgets.QMessageBox.Critical,
                self.tr("migration_failed_title"),
                self.tr("migration_failed_msg").format(e=e)
            )
            if os.path.exists(new_mod_p_path):
                 shutil.move(new_mod_p_path, legacy_mod_p_path)

    def ensure_active_profile(self):
        if self.active_profile_name and self.mod_p_path:
            return True

        reply = self.show_message_box(
            QtWidgets.QMessageBox.Information,
            "No Active Profile",
            "No mod profile is currently active. Please create or activate a profile first.",
            buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Ok:
            self.show_profile_manager()
        
        return self.active_profile_name and self.mod_p_path is not None
    @QtCore.pyqtSlot(int)
    def _on_scan_finished(self, count):

        DEBUG.log(f"Orphan scan finished. Found {count} additional files.")
        self.status_bar.showMessage(f"Scan complete. Found {count} additional audio files.", 5000)
    def get_original_path(self, file_id, lang):
        standard_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        if os.path.exists(standard_path):
            return standard_path
            
        if lang == "SFX":
            media_path = os.path.join(self.wem_root, "Media", f"{file_id}.wem")
        else:
            media_path = os.path.join(self.wem_root, "Media", lang, f"{file_id}.wem")
            
        if os.path.exists(media_path):
            return media_path
            
        if lang == "SFX":
            sfx_path = os.path.join(self.wem_root, "SFX", f"{file_id}.wem")
            if os.path.exists(sfx_path):
                return sfx_path 
                
        return standard_path
    def find_relevant_bnk_files(self, force_all=False):

        bnk_files_info = []
        bnk_paths_set = set()
        wems_root = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_root):
            return []

        scan_folders = []
        
        if force_all:
            DEBUG.log("Force all BNKs: Scanning all subdirectories in Wems folder.")
            for item in os.listdir(wems_root):
                path = os.path.join(wems_root, item)
                if os.path.isdir(path):
                    scan_folders.append(path)

        else:
            sfx_path = os.path.join(wems_root, "SFX")
            if os.path.exists(sfx_path):
                scan_folders.append(sfx_path)

            lang_setting = self.settings.data.get("wem_process_language", "english")
            lang_folder_name = "English(US)" if lang_setting == "english" else "Francais"
            lang_path = os.path.join(wems_root, lang_folder_name)
            if os.path.exists(lang_path):
                scan_folders.append(lang_path)
            DEBUG.log(f"Standard scan: looking for BNKs for language '{lang_setting}'.")

        for folder_path in scan_folders:
            bnk_type = 'sfx' if os.path.basename(folder_path) == "SFX" else 'lang'
            try:
                for file in os.listdir(folder_path):
                    if file.lower().endswith('.bnk'):
                        full_path = os.path.join(folder_path, file)
                        if full_path not in bnk_paths_set:
                            bnk_files_info.append((full_path, bnk_type))
                            bnk_paths_set.add(full_path)
            except OSError as e:
                DEBUG.log(f"Can't read folder {folder_path}: {e}", "WARNING")

        mode_str = "FORCE ALL" if force_all else "STANDARD"
        DEBUG.log(f"Found {len(bnk_files_info)} relevant BNK files (Mode: {mode_str}).")
        return bnk_files_info
    def _build_wem_index(self):
        if self.wem_index is not None:
            return 

        DEBUG.log("Building WEM file index (scanning Wems folder)...")
        self.wem_index = {}

        wems_folder = os.path.join(self.base_path, "Wems")
        if not os.path.exists(wems_folder):
            DEBUG.log("Wems folder not found")
            return

        for root, dirs, files in os.walk(wems_folder):
       
            
            for file in files:
                if file.lower().endswith('.wem'):
                    file_id = os.path.splitext(file)[0]
                    file_path = os.path.join(root, file)

                    rel_path = os.path.relpath(root, wems_folder)
                    parts = rel_path.split(os.sep)
                   
                    folder_name = "SFX"
                    
                    if rel_path == ".":
                        folder_name = "SFX"
                    elif parts[0] == "Media":
                        if len(parts) > 1:
                            folder_name = parts[1] # Media/English(US) -> English(US)
                        else:
                            folder_name = "SFX" # Media -> SFX
                    elif parts[0] == "SFX":
                        folder_name = "SFX"
                    else:
                        folder_name = parts[0] # English(US) -> English(US)

                    if file_id not in self.wem_index:
                        self.wem_index[file_id] = {}

                    self.wem_index[file_id][folder_name] = {
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    }

        DEBUG.log(f"WEM index built: {len(self.wem_index)} unique IDs found.")
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
        """Delete modified audio file(s) and revert BNK changes"""
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
                    entry_data = item.data(0, QtCore.Qt.UserRole)
                    if entry_data:
                        file_id = entry_data.get("Id", "")
                        mod_path = self.get_mod_path(file_id, lang) 
                        if mod_path and os.path.exists(mod_path):
                            file_list.append(entry_data)
            
            if not file_list:
                return
                
            reply = QtWidgets.QMessageBox.question(
                self, "Delete Multiple Mod Audio",
                f"Delete modified audio for {len(file_list)} files?\nThis will also revert changes in BNK files.\n\nThis action cannot be undone.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                deleted_count = 0
                for entry_to_delete in file_list:
                    self._perform_single_delete(entry_to_delete, lang)
                    deleted_count += 1
                
                QtCore.QTimer.singleShot(0, lambda: self.populate_tree(lang))
                self.status_bar.showMessage(f"Deleted {deleted_count} mod audio files", 3000)
            return

        if not items or items[0].childCount() > 0:
            return
            
        entry_to_delete = items[0].data(0, QtCore.Qt.UserRole)
        if not entry_to_delete:
            return
        
        file_id = entry_to_delete.get("Id", "")
        shortname = entry_to_delete.get("ShortName", "")
        
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        if not mod_wem_path or not os.path.exists(mod_wem_path):
            QtWidgets.QMessageBox.information(self, "Info", f"No modified audio found for {shortname}")
            return
            
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Mod Audio",
            f"Delete modified audio for:\n{shortname}\nThis will also revert changes in BNK files.\n\nThis action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self._perform_single_delete(entry_to_delete, lang)
            QtCore.QTimer.singleShot(0, lambda: self.populate_tree(lang))
    def _perform_single_delete(self, entry, lang):
        file_id = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        source_id = int(file_id)

        mod_wem_path = self.get_mod_path(file_id, lang)

        try:
          
            if mod_wem_path and os.path.exists(mod_wem_path):
                os.remove(mod_wem_path)
                DEBUG.log(f"Deleted wem audio: {mod_wem_path}")
            
            old_paths = [
                os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem"),
                os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            ]
            for p in old_paths:
                if os.path.exists(p):
                    os.remove(p)
                    DEBUG.log(f"Deleted legacy wem audio: {p}")

            bnk_reverted_count = 0
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if not os.path.exists(mod_bnk_path):
                    continue

                original_bnk = BNKEditor(bnk_path)
                original_entries = original_bnk.find_sound_by_source_id(source_id)
                
                if not original_entries:
                    continue
                
                original_entry = original_entries[0]

                mod_bnk_editor = BNKEditor(mod_bnk_path)
               
                if mod_bnk_editor.modify_sound(source_id, 
                                            new_size=original_entry.file_size, 
                                            override_fx=original_entry.override_fx,
                                            find_by_size=None):
                    mod_bnk_editor.save_file()
                    self.invalidate_bnk_cache(source_id)
                    DEBUG.log(f"BNK {os.path.basename(mod_bnk_path)} restored to original values.")
                    bnk_reverted_count += 1
         
            
            if bnk_reverted_count > 0:
                self.status_bar.showMessage(f"Deleted mod audio and restored {bnk_reverted_count} BNK entries for {shortname}", 3000)
            else:
                self.status_bar.showMessage(f"Deleted mod audio for {shortname} (No BNK changes found)", 3000)

        except Exception as e:
            DEBUG.log(f"Error deleting {shortname}: {e}", "ERROR")
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to process deletion for {shortname}: {str(e)}")
    def invalidate_bnk_cache(self, source_id: int):
        source_id_to_invalidate = int(source_id)
        DEBUG.log(f"Invalidating BNK cache for Source ID: {source_id_to_invalidate}")

        for bnk_path in list(self.bnk_cache_mod.keys()):
            if source_id_to_invalidate in self.bnk_cache_mod[bnk_path]:
                del self.bnk_cache_mod[bnk_path][source_id_to_invalidate]
                DEBUG.log(f"  > Removed ID {source_id_to_invalidate} from mod cache for {os.path.basename(bnk_path)}")

        for bnk_path in list(self.bnk_cache_orig.keys()):
            if source_id_to_invalidate in self.bnk_cache_orig[bnk_path]:
                del self.bnk_cache_orig[bnk_path][source_id_to_invalidate]
                DEBUG.log(f"  > Removed ID {source_id_to_invalidate} from original cache for {os.path.basename(bnk_path)}")        
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
        DEBUG.log("=== Loading Subtitles (Profile-aware) ===")
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

            elif key not in self.original_subtitles:
                self.modified_subtitles.add(key)
        
        DEBUG.log(f"Found {len(self.modified_subtitles)} modified subtitles after comparing with originals.")
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
        """Create an empty locres file using a two-step process."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                pass 
            DEBUG.log(f"Created empty placeholder locres file at: {path}")

            csv_path = path.replace('.locres', '.csv')
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)

                writer.writerow(["Key", "Source", "Translation"])
            
            if os.path.exists(self.unreal_locres_path):
                result = subprocess.run(
                    [self.unreal_locres_path, "import", path, csv_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.unreal_locres_path) or ".",
                    startupinfo=startupinfo,
                    creationflags=CREATE_NO_WINDOW,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode != 0:

                    DEBUG.log(f"UnrealLocres.exe failed during import for {path}: {result.stderr}", "WARNING")

            if os.path.exists(csv_path):
                os.remove(csv_path)
                
        except Exception as e:
            DEBUG.log(f"Error creating empty locres file at {path}: {e}", "ERROR")

    def load_subtitles_for_language(self, language):
        DEBUG.log(f"Loading subtitles for language: {language}")
        
        self.subtitles = {}
        self.original_subtitles = {}
        self.key_to_file_map = {}

        DEBUG.log("--- Loading original subtitles and building key map ---")
        for key, file_info in self.all_subtitle_files.items():
            if file_info['language'] == language:
                try:
                    original_data = self.locres_manager.export_locres(file_info['path'])
                    self.original_subtitles.update(original_data)

                    for sub_key in original_data:
                        self.key_to_file_map[sub_key] = file_info
                except Exception as e:
                    DEBUG.log(f"Failed to load original subtitles from {file_info['path']}: {e}", "ERROR")

        self.subtitles = self.original_subtitles.copy()
        DEBUG.log(f"Loaded {len(self.original_subtitles)} original subtitle entries and mapped them to files.")

        if self.mod_p_path and os.path.exists(self.mod_p_path):
            DEBUG.log(f"--- Loading modded subtitles from profile: {self.active_profile_name} ---")
            mod_loc_path = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
            
            if os.path.exists(mod_loc_path):
                for key, file_info in self.all_subtitle_files.items():
                    if file_info['language'] == language:
                        mod_file_path = os.path.join(mod_loc_path, file_info['category'], file_info['language'], file_info['filename'])
                        
                        if os.path.exists(mod_file_path):
                            DEBUG.log(f"Found modded subtitle file: {mod_file_path}")
                            try:
                                mod_data = self.locres_manager.export_locres(mod_file_path)
                                self.subtitles.update(mod_data)
                                DEBUG.log(f"Applied {len(mod_data)} subtitle entries from mod file.")
                            except Exception as e:
                                DEBUG.log(f"Failed to load mod subtitles from {mod_file_path}: {e}", "ERROR")
            else:
                DEBUG.log("No Localization folder in active mod profile.")
        else:
            DEBUG.log("No active mod profile to load modded subtitles from.")
    def create_resource_updater_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(5)
        header_layout.addWidget(QtWidgets.QLabel(f"<h2>{self.tr('updater_header')}</h2>"))
        desc_label = QtWidgets.QLabel(self.tr("updater_description"))
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)

        pak_group_layout = QtWidgets.QFormLayout()
        pak_group_layout.setSpacing(10)
        pak_group_layout.setContentsMargins(0, 10, 0, 0)
        
        self.pak_path_edit = QtWidgets.QLineEdit()
        self.pak_path_edit.setPlaceholderText(self.tr("pak_file_path_placeholder"))
        if self.settings.data.get("game_path"):
            potential_pak = os.path.join(self.settings.data.get("game_path"), "OPP", "Content", "Paks", "OPP-WindowsClient.pak")
            if os.path.exists(potential_pak):
                self.pak_path_edit.setText(potential_pak)
        
        pak_browse_btn = QtWidgets.QPushButton(self.tr("browse"))
        pak_browse_btn.clicked.connect(self.browse_for_pak)
        
        pak_widget = QtWidgets.QWidget()
        pak_widget_layout = QtWidgets.QHBoxLayout(pak_widget)
        pak_widget_layout.setContentsMargins(0,0,0,0)
        pak_widget_layout.addWidget(self.pak_path_edit)
        pak_widget_layout.addWidget(pak_browse_btn)

        pak_group_layout.addRow(f"<b>1. {self.tr('pak_file_path_label')}</b>", pak_widget)
        layout.addLayout(pak_group_layout)
        
        res_group_layout = QtWidgets.QFormLayout()
        res_group_layout.setSpacing(10)

        res_widget = QtWidgets.QWidget()
        res_layout = QtWidgets.QHBoxLayout(res_widget)
        res_layout.setContentsMargins(0,0,0,0)
        self.update_audio_check = QtWidgets.QCheckBox(self.tr("update_audio_check"))
        self.update_audio_check.setChecked(True)
        self.update_loc_check = QtWidgets.QCheckBox(self.tr("update_localization_check"))
        self.update_loc_check.setChecked(True)
        res_layout.addWidget(self.update_audio_check)
        res_layout.addWidget(self.update_loc_check)
        res_layout.addStretch()
        
        res_group_layout.addRow(f"<b>2. {self.tr('select_resources_group')}:</b>", res_widget)
        layout.addLayout(res_group_layout)
        
        button_layout = QtWidgets.QHBoxLayout()
        self.start_update_btn = QtWidgets.QPushButton(self.tr("start_update_btn"))
        self.start_update_btn.setMinimumHeight(20)
        self.start_update_btn.clicked.connect(self.start_update_process)
        
        self.cancel_update_btn = QtWidgets.QPushButton(self.tr("cancel"))
        self.cancel_update_btn.setMinimumHeight(20)
        self.cancel_update_btn.clicked.connect(self.cancel_update_process)
        self.cancel_update_btn.hide() 

        button_layout.addWidget(self.start_update_btn)
        button_layout.addWidget(self.cancel_update_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.update_progress_group = QtWidgets.QGroupBox(f"3. {self.tr('update_process_group')}")
        progress_layout = QtWidgets.QVBoxLayout(self.update_progress_group)

        self.update_progress_bar = QtWidgets.QProgressBar()
        self.update_status_label = QtWidgets.QLabel(self.tr("update_log_ready"))
        self.update_status_label.setStyleSheet("font-weight: bold;")
        self.update_fun_status_label = QtWidgets.QLabel("") 
        self.update_fun_status_label.setStyleSheet("color: #888; font-style: italic;")
        self.update_log_widget = QtWidgets.QTextEdit()
        self.update_log_widget.setReadOnly(True)
        self.update_log_widget.setFont(QtGui.QFont("Consolas", 9))
        self.update_log_widget.setMaximumHeight(250)

        progress_layout.addWidget(self.update_status_label)
        progress_layout.addWidget(self.update_fun_status_label)
        progress_layout.addWidget(self.update_progress_bar)
        progress_layout.addWidget(self.update_log_widget)
        
        layout.addWidget(self.update_progress_group)
        layout.addStretch()

        self.tabs.addTab(tab, self.tr("resource_updater_tab"))

    def browse_for_pak(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Game Pak file", self.settings.data.get("game_path", ""), "Pak files (*.pak)")
        if path:
            self.pak_path_edit.setText(path)


    def on_major_step_update(self, message, progress):
        self.update_status_label.setText(message)
        self.update_progress_bar.setValue(progress)

    def update_animation_text(self):

        if hasattr(self, 'animation_texts') and self.animation_texts:
            text = self.animation_texts[self.animation_index]
            self.update_fun_status_label.setText(f"-> {text}")
            self.animation_index = (self.animation_index + 1) % len(self.animation_texts)

    
    def start_update_process(self):
        pak_path = self.pak_path_edit.text()
        update_audio = self.update_audio_check.isChecked()
        update_loc = self.update_loc_check.isChecked()

        if not pak_path or not os.path.exists(pak_path):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("pak_file_not_selected"))
            return

        if not update_audio and not update_loc:
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_resources_selected"))
            return

        folders_to_replace = []
        if update_audio: folders_to_replace.append("Wems")
        if update_loc: folders_to_replace.append("Localization")

        reply = QtWidgets.QMessageBox.question(self, self.tr("update_confirm_title"),
                                    self.tr("update_confirm_msg").format(resource_folder=", ".join(folders_to_replace)),
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        self.start_update_btn.hide()
        self.cancel_update_btn.show()
        self.pak_path_edit.setEnabled(False)
        self.update_audio_check.setEnabled(False)
        self.update_loc_check.setEnabled(False)
        
        self.update_log_widget.clear()
        self.update_status_label.setText(self.tr("update_process_started"))
        self.update_fun_status_label.show()
        self.update_progress_bar.setRange(0, 0)
        self.update_start_time = time.time()
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.timeout.connect(self.update_elapsed_time)
        self.update_timer.start(1000) 
        self.update_elapsed_time()

        self.animation_timer = QtCore.QTimer(self)
        self.animation_texts = [
            self.tr("update_fun_status_1"), self.tr("update_fun_status_2"),
            self.tr("update_fun_status_3"), self.tr("update_fun_status_4"),
            self.tr("update_fun_status_5"), self.tr("update_fun_status_6"),
            self.tr("update_fun_status_7"),
        ]
        import random
        random.shuffle(self.animation_texts)
        self.animation_index = 0
        self.animation_timer.timeout.connect(self.update_animation_text)
        self.animation_timer.start(3000)
        self.update_animation_text()

        self.updater_thread = ResourceUpdaterThread(self, pak_path, update_audio, update_loc)
        self.updater_thread.major_step_update.connect(self.update_status_label.setText)
        self.updater_thread.log_update.connect(self.update_log_widget.append)
        self.updater_thread.finished.connect(self.on_update_finished)
        self.updater_thread.start()

    def cancel_update_process(self):
        if hasattr(self, 'updater_thread') and self.updater_thread.isRunning():
            self.updater_thread.cancel()

    def update_elapsed_time(self):
        if not hasattr(self, 'update_start_time'):
            return

        elapsed_seconds = int(time.time() - self.update_start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f"({minutes:02d}:{seconds:02d})"
        
      
        current_status = self.update_status_label.text().split(" (")[0]
        self.update_status_label.setText(f"{current_status} {time_str}")
    def on_update_finished(self, status, message):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        self.start_update_btn.show()
        self.cancel_update_btn.hide()
        self.pak_path_edit.setEnabled(True)
        self.update_audio_check.setEnabled(True)
        self.update_loc_check.setEnabled(True)
        
        self.update_fun_status_label.hide()
        
        self.update_progress_bar.setRange(0, 100)
        
        if status == "success":
            self.update_status_label.setText(self.tr('done'))
            self.update_progress_bar.setValue(100)
            
            audio_was_updated = self.update_audio_check.isChecked()
            if audio_was_updated:

                self.update_log_widget.append(f"\n--- {self.tr('update_rescanning_orphans')} ---")
                self.status_bar.showMessage(self.tr("update_rescanning_orphans"), 0)
                QtWidgets.QApplication.processEvents() 
                
                self.perform_blocking_orphan_scan()
            QtWidgets.QMessageBox.information(self, self.tr("update_complete_title"), f"{message}\n\n{self.tr('restart_recommended')}")

        elif status == "failure":
            self.update_status_label.setText(self.tr('error_status'))
            self.update_progress_bar.setValue(0)
            QtWidgets.QMessageBox.critical(self, self.tr("update_failed_title"), f"{self.tr('update_failed_msg')}\n\n{message}")
        
        elif status == "cancelled":
            self.update_status_label.setText(self.tr('update_cancelled_by_user'))
            self.update_progress_bar.setValue(0)
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

        self.global_search = SearchBar(placeholder_text=self.tr("search_placeholder"))
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
        self.load_converter_file_list()
        self.create_subtitle_editor_tab()
        self.create_resource_updater_tab()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_widget)

        # if self.entries_by_lang:
        #     first_lang = sorted(self.entries_by_lang.keys())[0]
        #     self.populate_tree(first_lang)
        #     self.populated_tabs.add(first_lang)
            
        def delayed_init():
            if hasattr(self, 'subtitle_lang_combo'):
                self.populate_subtitle_editor_controls()
            
            for lang in self.tab_widgets.keys():
                self.update_filter_combo(lang)

        QtCore.QTimer.singleShot(500, delayed_init)

    def refresh_subtitle_editor(self):
        """Refresh subtitle editor data"""
        DEBUG.log("Refreshing subtitle editor")
        self.scan_localization_folder()
        self.populate_subtitle_editor_controls()
        self.status_bar.showMessage("Localization editor refreshed", 2000)

    def on_global_search_changed_for_subtitles(self, text):
        if hasattr(self, 'subtitle_editor_tab_widget') and self.tabs.currentWidget() == self.subtitle_editor_tab_widget:
            self.on_subtitle_filter_changed()

    def get_global_search_text(self):
        """Get text from global search bar"""
        return self.global_search.text() if hasattr(self, 'global_search') else ""

    def create_subtitle_editor_tab(self):
        """Create tab for editing subtitles without audio files"""
        tab = QtWidgets.QWidget()
        self.subtitle_editor_tab_widget = tab
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
        
        self.subtitle_cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
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
        
        self.orphaned_only_checkbox = QtWidgets.QCheckBox(self.tr("without_audio_filter"))
        self.orphaned_only_checkbox.setToolTip(self.tr("without_audio_filter_tooltip"))
        
        self.modified_only_checkbox = QtWidgets.QCheckBox(self.tr("modified_only_filter"))
        self.modified_only_checkbox.setToolTip(self.tr("modified_only_filter_tooltip"))
        
        self.with_audio_only_checkbox = QtWidgets.QCheckBox(self.tr("with_audio_only_filter"))
        self.with_audio_only_checkbox.setToolTip(self.tr("with_audio_only_filter_tooltip"))
        
        refresh_btn = QtWidgets.QPushButton(self.tr("refresh_btn"))
        refresh_btn.setToolTip(self.tr("refresh_btn_tooltip"))
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
        self.subtitle_table.setHorizontalHeaderLabels([self.tr("key_header"), self.tr("original_header"), self.tr("current_header"), self.tr("audio_header")])
        
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
        
        edit_btn = QtWidgets.QPushButton(self.tr("edit_selected_btn"))
        edit_btn.clicked.connect(self.edit_selected_subtitle)
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        
        save_all_btn = QtWidgets.QPushButton(self.tr("save_all_changes_btn"))
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
                highlight_color = QtGui.QColor(85, 72, 35) if self.settings.data.get("theme", "light") == "dark" else QtGui.QColor(255, 255, 200)
                for col in range(4):
                    item = self.subtitle_table.item(row, col)
                    if item:
                        item.setBackground(highlight_color)
            
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
                if key in self.key_to_file_map:
                    file_info = self.key_to_file_map[key]
                    self.dirty_subtitle_files.add(file_info['path'])
                    DEBUG.log(f"Marked file as dirty due to edit: {file_info['path']}")
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
                 
                                highlight_color = QtGui.QColor(85, 72, 35) if self.settings.data.get("theme", "light") == "dark" else QtGui.QColor(255, 255, 200)
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(highlight_color)
                    
                            else:
      
                                base_color = self.palette().color(QtGui.QPalette.Base)
                                for col in range(4):
                                    cell_item = self.subtitle_table.item(target_row, col)
                                    if cell_item:
                                        cell_item.setBackground(base_color)
                                        
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
        """Save all subtitle changes to working files in a separate thread."""
        if not self.ensure_active_profile():
            return
            
        if not self.modified_subtitles:
            QtWidgets.QMessageBox.information(self, self.tr("no_changes"), self.tr("no_modified_subtitles"))
            return

        self.progress_dialog = ProgressDialog(self, self.tr("Saving Subtitles..."))
        self.progress_dialog.show()

        self.save_thread = SaveSubtitlesThread(self)
        self.save_thread.progress_updated.connect(self.progress_dialog.set_progress)
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.start()

    def on_save_finished(self, count, errors):
        """Handles the completion of the subtitle saving thread."""
        self.progress_dialog.close()
        
        self.update_status()
        for lang in self.populated_tabs:
            self.populate_tree(lang)
        
        if not errors:
            self.dirty_subtitle_files.clear()
            QtWidgets.QMessageBox.information(self, self.tr("success"), 
                f"{self.tr('subtitle_save_success')}\n\nUpdated {count} file(s) in your mod profile.")
            self.status_bar.showMessage(self.tr("subtitle_save_success"), 3000)
        else:
            error_details = "\n".join(errors)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle(self.tr("save_error"))
            msg_box.setText(f"Completed with {len(errors)} error(s).")
            msg_box.setDetailedText(error_details)
            msg_box.exec_()
            self.status_bar.showMessage(f"Save completed with {len(errors)} error(s)", 5000)

    def show_subtitle_table_context_menu(self, pos):
        selected_items = self.subtitle_table.selectedItems()
        if not selected_items:
            return
        
        selected_rows = sorted(list(set(item.row() for item in selected_items)))
        
        first_row = selected_rows[0]
        key = self.subtitle_table.item(first_row, 0).text()
        has_audio = self.subtitle_table.item(first_row, 3).text() == "🔊"

        menu = QtWidgets.QMenu()
        if self.settings.data["theme"] == "dark":
            menu.setStyleSheet(self.get_dark_menu_style())
        
        if len(selected_rows) > 1:
            edit_action = menu.addAction(f"✏️ {self.tr('edit_subtitle')} ({len(selected_rows)} items)")
            edit_action.setEnabled(False) 
            
            revert_action = menu.addAction(f"↩️ {self.tr('revert_to_original')} ({len(selected_rows)} items)")
        else:
            edit_action = menu.addAction(f"✏️ {self.tr('edit_subtitle')}")
            revert_action = menu.addAction(f"↩️ {self.tr('revert_to_original')}")

        edit_action.triggered.connect(lambda: self.edit_subtitle_from_table(self.subtitle_table.item(first_row, 0)))
        revert_action.triggered.connect(lambda: self.revert_subtitle_from_table(selected_rows))
        
        menu.addSeparator()
        
        if len(selected_rows) == 1 and has_audio:
            goto_audio_action = menu.addAction(f"🔊 {self.tr('go_to_audio_action')}")
            goto_audio_action.triggered.connect(lambda: self.go_to_audio_file(key))
            menu.addSeparator()
        
        copy_key_action = menu.addAction(f"{self.tr('copy_key')}")
        copy_key_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(key))
        
        copy_text_action = menu.addAction(f"{self.tr('copy_text')}")
        current_text = self.subtitle_table.item(first_row, 2).toolTip() or self.subtitle_table.item(first_row, 2).text()
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
                self, self.tr("info"), 
                self.tr("tab_not_found_for_lang").format(lang=target_lang)
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
            self, self.tr("audio_not_found"), 
            self.tr("audio_not_found_for_key").format(key=subtitle_key)
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

    def revert_subtitle_from_table(self, rows_to_revert):
        """Revert subtitle(s) to original from table for a list of row indices."""
        if not rows_to_revert:
            return

        reverted_count = 0
        for row in rows_to_revert:
            try:
                key_item = self.subtitle_table.item(row, 0)
                if not key_item:
                    continue
                
                key = key_item.text()
                
                if key in self.original_subtitles:
                    original_text = self.original_subtitles[key]
                    
                    self.subtitles[key] = original_text
                    self.modified_subtitles.discard(key)
                    if key in self.key_to_file_map:
                        file_info = self.key_to_file_map[key]
                        self.dirty_subtitle_files.add(file_info['path'])
                        DEBUG.log(f"Marked file as dirty due to revert: {file_info['path']}")

                    current_item = self.subtitle_table.item(row, 2)
                    current_item.setText(self.truncate_text(original_text, 150))
                    current_item.setToolTip(original_text)
                    
                    base_color = self.palette().color(QtGui.QPalette.Base)
                    for col in range(4):
                        item = self.subtitle_table.item(row, col)
                        if item:
                            item.setBackground(base_color)

                    reverted_count += 1
            except Exception as e:
                DEBUG.log(f"Error reverting subtitle at row {row}: {e}", "ERROR")

        if reverted_count > 0:
            self.update_status()
            self.status_bar.showMessage(f"Reverted {reverted_count} subtitle(s) to original", 3000)

 
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
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "English(US)")
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "Francais")
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "English(US)")
            voice_lang_filter = ["English(US)"]
        
        target_dir_sfx = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
        
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
        
        self.converter_status_old.clear()
        self.converter_status_old.append(f"=== Processing WEM Files for {selected_language.capitalize()} ===")
        self.converter_status_old.append(f"Voice target: {target_dir_voice}")
        self.converter_status_old.append(f"SFX target: {target_dir_sfx}")
        self.converter_status_old.append("")
        self.converter_status_old.append(f"Analysis Results:")
        self.converter_status_old.append(f"  WEM files on disk: {len(all_wem_files)} total, {len(vo_wem_files)} VO files")
        self.converter_status_old.append(f"  Voice files in database for {selected_language}: {len(voice_files_in_db)}")
        self.converter_status_old.append(f"    - From StreamedFiles: {vo_from_streamed}")
        self.converter_status_old.append(f"    - From MediaFilesNotInAnyBank: {vo_from_media_files}")
        self.converter_status_old.append(f"    - Skipped (wrong language): {vo_skipped_wrong_lang}")
        self.converter_status_old.append(f"  Exact matches: {len(exact_matches)}")
        self.converter_status_old.append(f"  Potential matches (hex removal): {len(potential_matches)}")
        self.converter_status_old.append(f"  Total mappable files: {len(exact_matches) + len(potential_matches)}")
        self.converter_status_old.append("")
        
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
        
        self.converter_status_old.append("")
        self.converter_status_old.append("=== Processing Complete ===")
        self.converter_status_old.append(f"Total files processed: {processed}")
        self.converter_status_old.append(f"Voice files ({selected_language}): {voice_processed}")
        self.converter_status_old.append(f"SFX files: {sfx_processed}")
        self.converter_status_old.append(f"Files renamed to ID: {renamed_count}")
        self.converter_status_old.append(f"Files kept original name: {processed - renamed_count}")
        self.converter_status_old.append(f"Voice rename success rate: {success_rate:.1f}%")
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
    def cleanup_working_locres(self):
        DEBUG.log("=== Cleanup Working Locres Files ===")
        localization_path = os.path.join(self.base_path, "Localization")
        if not os.path.exists(localization_path):
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                self.tr("no_localization_message").format(path=localization_path)
            )
            return

        working_files = []
        for root, dirs, files in os.walk(localization_path):
            for file in files:
                if file.endswith('_working.locres'):
                    file_path = os.path.join(root, file)
                    working_files.append(file_path)

        if not working_files:
            QtWidgets.QMessageBox.information(
                self, self.tr("no_localization_found"), 
                "No working subtitle files (_working.locres) found in Localization."
            )
            return

        deleted = 0
        errors = 0
        for file_path in working_files:
            try:
                os.remove(file_path)
                DEBUG.log(f"Deleted: {file_path}")
                deleted += 1

                parent = os.path.dirname(file_path)
                while parent != localization_path and os.path.isdir(parent) and not os.listdir(parent):
                    os.rmdir(parent)
                    parent = os.path.dirname(parent)
            except Exception as e:
                DEBUG.log(f"Error deleting {file_path}: {e}", "ERROR")
                errors += 1

        msg = f"Deleted {deleted} working subtitle files."
        if errors:
            msg += f"\nErrors: {errors}"
        QtWidgets.QMessageBox.information(self, "Cleanup Complete", msg)
    def save_subtitles_to_file(self):

        if not self.dirty_subtitle_files:
            return True

        DEBUG.log(f"=== Performing Blocking Save for {len(self.dirty_subtitle_files)} files ===")
        try:
            for original_path in list(self.dirty_subtitle_files):
                file_info = None
                for info in self.all_subtitle_files.values():
                    if info['path'] == original_path:
                        file_info = info
                        break
                
                if not file_info:
                    DEBUG.log(f"Could not find file info for dirty path: {original_path}", "WARNING")
                    continue
                
                target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization", file_info['category'], file_info['language'])
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file_info['filename'])

                subtitles_to_write = self.locres_manager.export_locres(original_path)
                
                for key in subtitles_to_write.keys():
                    if key in self.subtitles:
                        subtitles_to_write[key] = self.subtitles[key]

                shutil.copy2(original_path, target_path)

                if not self.locres_manager.import_locres(target_path, subtitles_to_write):
                    raise Exception(f"Failed to write to {target_path}")

            self.dirty_subtitle_files.clear()
            DEBUG.log("Blocking save successful, dirty files cleared.")
            return True
        except Exception as e:
            DEBUG.log(f"Blocking save error: {e}", "ERROR")
            return False
    def show_settings_dialog(self):
        dialog = QtWidgets.QDialog(self)    
        dialog.setWindowTitle(self.tr("settings"))
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        lang_combo = QtWidgets.QComboBox()
        lang_map = [("English", "en"), ("Русский", "ru"), ("Polski", "pl"), ("Español (México)", "es-MX")]
        for name, code in lang_map:
            lang_combo.addItem(name, code)
        
        current_lang_code = self.settings.data["ui_language"]
        index = next((i for i, (name, code) in enumerate(lang_map) if code == current_lang_code), 0)
        lang_combo.setCurrentIndex(index)
        
        theme_combo = QtWidgets.QComboBox()
        theme_combo.addItem(self.tr("light"), "light")
        theme_combo.addItem(self.tr("dark"), "dark")
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

        layout.addRow(self.tr("interface_language"), lang_combo)
        layout.addRow(self.tr("theme"), theme_combo)
        layout.addRow(self.tr("subtitle_language"), subtitle_combo)
        layout.addRow(self.tr("game_path"), game_path_widget)
        
        quick_load_group = QtWidgets.QGroupBox(self.tr("quick_load_settings_group"))
        quick_load_layout = QtWidgets.QVBoxLayout(quick_load_group)
        
        quick_load_label = QtWidgets.QLabel(self.tr("quick_load_mode_label"))
        quick_load_layout.addWidget(quick_load_label)
        
        quick_load_strict = QtWidgets.QRadioButton(self.tr("quick_load_strict"))
        quick_load_adaptive = QtWidgets.QRadioButton(self.tr("quick_load_adaptive"))
        
        current_quick_mode = self.settings.data.get("quick_load_mode", "strict")
        if current_quick_mode == "adaptive":
            quick_load_adaptive.setChecked(True)
        else:
            quick_load_strict.setChecked(True)
        
        quick_load_layout.addWidget(quick_load_strict)
        quick_load_layout.addWidget(quick_load_adaptive)
        
        layout.addRow(quick_load_group)
        layout.addRow(auto_save_check)
        wem_lang_combo = QtWidgets.QComboBox()
        wem_lang_combo.addItem("English (US)", "english")
        wem_lang_combo.addItem("Francais (France)", "french")
        current_wem_lang = self.settings.data.get("wem_process_language", "english")
        wem_lang_combo.setCurrentIndex(0 if current_wem_lang == "english" else 1)
        wem_lang_combo.setToolTip(self.tr("wemprocces_desc"))

        layout.addRow(self.tr("wem_process_language"), wem_lang_combo)
        conversion_method_group = QtWidgets.QGroupBox(self.tr("conversion_method_group"))
        conversion_method_layout = QtWidgets.QVBoxLayout(conversion_method_group)
        
        self.bnk_overwrite_radio = QtWidgets.QRadioButton(self.tr("bnk_overwrite_radio"))
        self.bnk_overwrite_radio.setToolTip(self.tr("bnk_overwrite_tooltip"))
        self.adaptive_radio = QtWidgets.QRadioButton(self.tr("adaptive_size_matching_radio"))
        self.adaptive_radio.setToolTip(self.tr("adaptive_size_matching_tooltip"))
        
        current_method = self.settings.data.get("conversion_method", "adaptive")
        if current_method == "bnk":
            self.bnk_overwrite_radio.setChecked(True)
        else:
            self.adaptive_radio.setChecked(True)
            
        conversion_method_layout.addWidget(self.adaptive_radio)
        conversion_method_layout.addWidget(self.bnk_overwrite_radio)
        
        layout.addRow(conversion_method_group)
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addRow(btn_box)
        
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            old_subtitle_lang = self.settings.data["subtitle_lang"]
            old_ui_lang = self.settings.data["ui_language"]
            
            new_ui_lang = lang_combo.currentData()
            new_subtitle_lang = subtitle_combo.currentText()

            self.settings.data["ui_language"] = new_ui_lang
            self.settings.data["theme"] = theme_combo.currentData()
            self.settings.data["subtitle_lang"] = new_subtitle_lang
            self.settings.data["game_path"] = game_path_edit.text()
            self.settings.data["auto_save"] = auto_save_check.isChecked()
            self.settings.data["wem_process_language"] = wem_lang_combo.currentData() 
            if self.bnk_overwrite_radio.isChecked():
                self.settings.data["conversion_method"] = "bnk"
            else:
                self.settings.data["conversion_method"] = "adaptive"
            
            if quick_load_adaptive.isChecked():
                self.settings.data["quick_load_mode"] = "adaptive"
            else:
                self.settings.data["quick_load_mode"] = "strict"
            
            self.settings.save()

            self.apply_settings()

            if new_ui_lang != old_ui_lang:
                self.current_lang = new_ui_lang
                
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle(self.tr("settings_saved_title"))
                msg_box.setText(self.tr("close_required_message"))
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                
                close_btn = msg_box.addButton(self.tr("close_now_button"), QtWidgets.QMessageBox.AcceptRole)
                later_btn = msg_box.addButton(self.tr("cancel"), QtWidgets.QMessageBox.RejectRole)
                
                msg_box.exec_()

                if msg_box.clickedButton() == close_btn:
                    self.close()
                else:
                    self.current_lang = old_ui_lang

            if new_subtitle_lang != old_subtitle_lang:
                DEBUG.log(f"Subtitle language changed from {old_subtitle_lang} to {new_subtitle_lang}")
                self.load_subtitles()
                self.modified_subtitles.clear()
                for key, value in self.subtitles.items():
                    if key in self.original_subtitles and self.original_subtitles[key] != value:
                        self.modified_subtitles.add(key)
                    elif key not in self.original_subtitles:
                        self.modified_subtitles.add(key)
                DEBUG.log(f"Recalculated modified subtitles for {new_subtitle_lang}: {len(self.modified_subtitles)} found.")
                for lang in list(self.populated_tabs):
                    self.populate_tree(lang)
                self.update_status()

                if hasattr(self, 'subtitle_table'):
                    self.load_subtitle_editor_data()
           
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
    def load_all_soundbank_files(self, path=None):
        DEBUG.log(f"Loading soundbank files from: {path}")
        all_files = []
        
        if not path or not os.path.exists(path):
            DEBUG.log("SoundbanksInfo file not found.", "WARNING")
            return []

        try:
            ext = os.path.splitext(path)[1].lower()
            
            if ext == '.json':
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                soundbanks_info = data.get("SoundBanksInfo") or data.get("SoundbanksInfo") or data
                
                if not soundbanks_info:
                    DEBUG.log("ERROR: Could not find SoundBanksInfo block.", "ERROR")
                    return []
                
                streamed_files = soundbanks_info.get("StreamedFiles", [])
                for file_entry in streamed_files:
                    file_entry["Source"] = "StreamedFiles"
                    if "Path" in file_entry:
                        file_entry["Path"] = file_entry["Path"].replace("Media/", "").replace("Media\\", "")
                all_files.extend(streamed_files)
                
                media_not_in_bank = soundbanks_info.get("MediaFilesNotInAnyBank", [])
                for file_entry in media_not_in_bank:
                    file_entry["Source"] = "MediaFilesNotInAnyBank"
                    if "Path" in file_entry:
                        file_entry["Path"] = file_entry["Path"].replace("Media/", "").replace("Media\\", "")
                all_files.extend(media_not_in_bank)

                soundbanks_list = soundbanks_info.get("SoundBanks", [])
                
                unique_files_map = {f["Id"]: f for f in all_files}
                
                for sb in soundbanks_list:
                 
                    bnk_name = sb.get("ShortName", "UnknownBank")
                    
                    media_list = sb.get("Media", [])
                    for media_entry in media_list:
                        file_id = media_entry.get("Id")
                        
                        if file_id and file_id not in unique_files_map:
                      
                            if "Path" in media_entry:
                                media_entry["Path"] = media_entry["Path"].replace("Media/", "").replace("Media\\", "")
                            
                            media_entry["Source"] = f"Bank: {bnk_name}"
                            
                            unique_files_map[file_id] = media_entry
                            all_files.append(media_entry)
                
                DEBUG.log(f"Loaded {len(streamed_files)} StreamedFiles, {len(media_not_in_bank)} LooseMedia, and {len(all_files) - len(streamed_files) - len(media_not_in_bank)} files from SoundBanks Media.")

            elif ext == '.xml':
          
                tree = ET.parse(path)
                root = tree.getroot()
                
                streamed_files_elem = root.find("StreamedFiles")
                if streamed_files_elem is not None:
                    for file_elem in streamed_files_elem.findall("File"):
                        raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                        clean_path = raw_path.replace("Media/", "").replace("Media\\", "")
                        
                        file_entry = { 
                            "Id": file_elem.get("Id"), 
                            "Language": file_elem.get("Language"), 
                            "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "", 
                            "Path": clean_path, 
                            "Source": "StreamedFiles" 
                        }
                        all_files.append(file_entry)
                
                media_files_elem = root.find("MediaFilesNotInAnyBank")
                if media_files_elem is not None:
                    for file_elem in media_files_elem.findall("File"):
                        raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                        clean_path = raw_path.replace("Media/", "").replace("Media\\", "")

                        file_entry = { 
                            "Id": file_elem.get("Id"), 
                            "Language": file_elem.get("Language"), 
                            "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "", 
                            "Path": clean_path, 
                            "Source": "MediaFilesNotInAnyBank" 
                        }
                        all_files.append(file_entry)
                        
                soundbanks_elem = root.find("SoundBanks")
                if soundbanks_elem is not None:
                    for sb_elem in soundbanks_elem.findall("SoundBank"):
                        bnk_name = sb_elem.find("ShortName").text if sb_elem.find("ShortName") is not None else "Unknown"
                        media_elem = sb_elem.find("Media")
                        if media_elem is not None:
                            for file_elem in media_elem.findall("File"):
                                file_id = file_elem.get("Id")
                       
                                raw_path = file_elem.find("Path").text if file_elem.find("Path") is not None else ""
                                clean_path = raw_path.replace("Media/", "").replace("Media\\", "")
                                
                                file_entry = {
                                    "Id": file_id,
                                    "Language": file_elem.get("Language"),
                                    "ShortName": file_elem.find("ShortName").text if file_elem.find("ShortName") is not None else "",
                                    "Path": clean_path,
                                    "Source": f"Bank: {bnk_name}"
                                }
                                all_files.append(file_entry)

            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            unique_files = {}
            for f in all_files:
                fid = f.get("Id")
                if fid and fid not in unique_files:
                    unique_files[fid] = f
            
            final_list = list(unique_files.values())
            DEBUG.log(f"Total unique files loaded from SoundbanksInfo: {len(final_list)}")
            return final_list
            
        except Exception as e:
            DEBUG.log(f"Error loading soundbank: {e}", "ERROR")
            import traceback
            DEBUG.log(traceback.format_exc(), "ERROR")
            return []
    def _scan_and_add_orphaned_wems(self, known_ids):
        """Scans the Wems directory to find and add files not listed in SoundbanksInfo."""
        orphaned_entries = []
        if not os.path.exists(self.wem_root):
            DEBUG.log(f"Wems directory not found at {self.wem_root}, skipping scan.", "WARNING")
            return orphaned_entries

        for root, _, files in os.walk(self.wem_root):
            for file in files:
                if not file.lower().endswith('.wem'):
                    continue

                file_id = os.path.splitext(file)[0]
                if file_id in known_ids:
                    continue

                full_path = os.path.join(root, file)
                
                rel_path = os.path.relpath(root, self.wem_root)
                lang = "SFX" if rel_path == '.' else rel_path

                short_name = f"{file_id}.wav"
                try:
                    analyzer = WEMAnalyzer(full_path)
                    if analyzer.analyze():
                        markers = analyzer.get_markers_info()
                        if markers and markers[0]['label']:
                            short_name = f"{markers[0]['label']}.wav"
                            DEBUG.log(f"Orphaned file '{file}' named from marker: '{short_name}'")
                except Exception as e:
                    DEBUG.log(f"Could not analyze markers for orphaned file {file}: {e}", "WARNING")

                new_entry = {
                    "Id": file_id,
                    "Language": lang,
                    "ShortName": short_name,
                    "Path": file, 
                    "Source": "ScannedFromFileSystem"
                }
                orphaned_entries.append(new_entry)

        if orphaned_entries:
            DEBUG.log(f"Added {len(orphaned_entries)} orphaned WEM files found on disk.")
        else:
            DEBUG.log("No orphaned WEM files found on disk.")
            
        return orphaned_entries
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
    def _tree_populate_generator(self, tree, filtered_wrappers, lang, is_flat_view, selected_keys):

        
        root_groups = {}
        id_only_category = "Numeric ID Files"
        id_only_item = None
        
        
        for i, wrapper in enumerate(filtered_wrappers):
            entry = wrapper['_orig']
            has_mod = wrapper['has_mod_audio']
            
            if is_flat_view:
        
                parent_item = tree.invisibleRootItem()
                item = self.add_tree_item(parent_item, entry, lang, has_mod)
            else:
             
                shortname = entry.get("ShortName", "")
                name_without_ext = shortname.rsplit('.', 1)[0]
                
                if name_without_ext.isdigit():
                    if id_only_item is None:
                        id_only_item = QtWidgets.QTreeWidgetItem(tree, [f"{id_only_category}"])
                    
                    self.add_tree_item(id_only_item, entry, lang, has_mod)
                else:
                    parts = name_without_ext.split("_")[:3]
                    
                    if not parts:
                        self.add_tree_item(tree.invisibleRootItem(), entry, lang, has_mod)
                        continue

                    current_parent_dict = root_groups
                    current_parent_item = tree.invisibleRootItem()

                    for level_idx, part in enumerate(parts):
                        if part not in current_parent_dict:
                            display_name = "VO (Voice)" if level_idx == 0 and part.upper() == "VO" else part
                            new_item = QtWidgets.QTreeWidgetItem(current_parent_item, [display_name])
                            
                            if level_idx == 0 and part.upper() == "VO":
                                new_item.setExpanded(True)
                            
                            current_parent_dict[part] = {"__item__": new_item, "__children__": {}}
                        
                        current_parent_item = current_parent_dict[part]["__item__"]
                        current_parent_dict = current_parent_dict[part]["__children__"]

                    self.add_tree_item(current_parent_item, entry, lang, has_mod)

            if selected_keys:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                if key in selected_keys:

                    pass 

            if i % 50 == 0:
                yield

        if not is_flat_view:
            self._update_group_counts_recursive(tree.invisibleRootItem(), id_only_category)
            if id_only_item:
                id_only_item.setText(0, f"{id_only_category} ({id_only_item.childCount()})")

        if selected_keys:
            self.restore_tree_selection(tree, selected_keys)
        
        yield

    def _process_tree_batch(self):
      
        if not self.tree_loader_generator or not self.current_loading_lang:
            self.tree_loader_timer.stop()
            return

        widgets = self.tab_widgets.get(self.current_loading_lang)
        if not widgets:
            self.tree_loader_timer.stop()
            return
            
        tree = widgets["tree"]
        
        tree.setUpdatesEnabled(False)
        
        start_time = time.time()
        try:
          
            while (time.time() - start_time) < 0.015:
                next(self.tree_loader_generator)
                
        except StopIteration:
            
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
            tree.setUpdatesEnabled(True)
            # DEBUG.log("Tree population complete")
        except Exception as e:
            DEBUG.log(f"Error in tree population: {e}", "ERROR")
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
            tree.setUpdatesEnabled(True)
        finally:
        
            tree.setUpdatesEnabled(True)

    def _update_group_counts_recursive(self, item, id_category_name):
       
        count = 0
        for i in range(item.childCount()):
            child = item.child(i)
           
            if child.text(0).startswith(id_category_name):
                continue
                
            if child.childCount() > 0:
                count += self._update_group_counts_recursive(child, id_category_name)
            else:
                count += 1
        
        if item.parent() is not None and item.childCount() > 0:
            current_text = item.text(0)
            if "(" not in current_text:
                item.setText(0, f"{current_text} ({count})")
        
        return count
    @QtCore.pyqtSlot(str)
    def populate_tree(self, lang):
        DEBUG.log(f"Populating tree for language: {lang}")
        
        if lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        
        if self.tree_loader_timer.isActive():
            self.tree_loader_timer.stop()
            self.tree_loader_generator = None
   
            if self.current_loading_lang and self.current_loading_lang in self.tab_widgets:
                self.tab_widgets[self.current_loading_lang]["tree"].setUpdatesEnabled(True)

        selected_keys = []
        try:
            for item in tree.selectedItems():
                if item.childCount() == 0:
                    entry = item.data(0, QtCore.Qt.UserRole)
                    if entry:
                        shortname = entry.get("ShortName", "")
                        key = os.path.splitext(shortname)[0]
                        selected_keys.append(key)
        except RuntimeError:
            pass
        
        tree.clear()
        
        filter_text = widgets["filter_combo"].currentText()
        filter_type = widgets["filter_combo"].currentIndex()
        sort_type = widgets["sort_combo"].currentIndex() 
        search_text = self.global_search.text().lower()
        
        filtered_entries = []
        source_entries = self.entries_by_lang.get(lang, [])
        
        search_terms = []
        if search_text:
           
            search_terms = [term.strip() for term in search_text.split() if term.strip()]
        
        if filter_text.startswith("With Tag: "):
            selected_tag = filter_text.split(": ", 1)[1]
            for entry in source_entries:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                
                if self.marked_items.get(key, {}).get('tag') != selected_tag:
                    continue
                    
                if search_terms:
                    
                    content_to_search = f"{entry.get('Id', '')} {entry.get('ShortName', '')} {self.subtitles.get(key, '')}".lower()
                    
                    if not all(term in content_to_search for term in search_terms):
                        continue
                        
                filtered_entries.append({'_orig': entry, 'has_mod_audio': False})
        else:
            for entry in source_entries:
                key = os.path.splitext(entry.get("ShortName", ""))[0]
                subtitle = self.subtitles.get(key, "")
                
                has_mod_audio = False
                if filter_type == 4: 
                    mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                    has_mod_audio = os.path.exists(mod_path) if mod_path else False
                
                if filter_type == 1 and not subtitle: continue          # With Subtitles
                elif filter_type == 2 and subtitle: continue            # Without Subtitles
                elif filter_type == 3 and key not in self.modified_subtitles: continue # Modified
                elif filter_type == 4 and not has_mod_audio: continue   # Modded (Audio)
                
                if search_terms:
                    content_to_search = f"{entry.get('Id', '')} {entry.get('ShortName', '')} {subtitle}".lower()
                    
                    match = True
                    for term in search_terms:
                        if term not in content_to_search:
                            match = False
                            break
                    if not match:
                        continue
                
                if filter_type != 4:
                     mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                     has_mod_audio = os.path.exists(mod_path) if mod_path else False

                entry_wrapper = {'_orig': entry, 'has_mod_audio': has_mod_audio}
                filtered_entries.append(entry_wrapper)

        if sort_type == 4: # Recent First
            mod_times_cache = {}
            for wrapper in filtered_entries:
                entry = wrapper['_orig']
                file_id = entry.get("Id", "")
                mod_wem_path = self.get_mod_path(file_id, lang)
                if os.path.exists(mod_wem_path):
                    try: mod_times_cache[file_id] = os.path.getmtime(mod_wem_path)
                    except OSError: mod_times_cache[file_id] = 0
                else: mod_times_cache[file_id] = 0
            
            filtered_entries.sort(key=lambda x: mod_times_cache.get(x['_orig'].get("Id", ""), 0), reverse=True)
        elif sort_type == 0: filtered_entries.sort(key=lambda x: x['_orig'].get("ShortName", "").lower())
        elif sort_type == 1: filtered_entries.sort(key=lambda x: x['_orig'].get("ShortName", "").lower(), reverse=True)
        elif sort_type == 2: filtered_entries.sort(key=lambda x: int(x['_orig'].get("Id", "0")))
        elif sort_type == 3: filtered_entries.sort(key=lambda x: int(x['_orig'].get("Id", "0")), reverse=True)

        subtitle_count = sum(1 for w in filtered_entries if self.subtitles.get(os.path.splitext(w['_orig'].get("ShortName", ""))[0], ""))
        total_lang_entries = len(source_entries)
        stats_text = self.tr("stats_label_text").format(
            filtered_count=len(filtered_entries),
            total_count=total_lang_entries,
            subtitle_count=subtitle_count
        )
        widgets["stats_label"].setText(stats_text)

        self.current_loading_lang = lang
        is_flat_view = bool(search_text or sort_type == 4)
        
        self.tree_loader_generator = self._tree_populate_generator(
            tree, filtered_entries, lang, is_flat_view, selected_keys
        )
        
        self.tree_loader_timer.start()
    def add_tree_item(self, parent_item, entry, lang, has_mod_audio):
        """Adds a single entry as an item to the tree."""
        shortname = entry.get("ShortName", "")
        key = os.path.splitext(shortname)[0]
        subtitle = self.subtitles.get(key, "")
        
        mod_status = ""
        if has_mod_audio:
            mod_status = "♪"
        
        item = QtWidgets.QTreeWidgetItem(parent_item, [
            shortname,
            entry.get("Id", ""),
            subtitle,
            "✓" + mod_status if key in self.modified_subtitles else mod_status,
            ""  
        ])

        marking = self.marked_items.get(key, {})
        if 'color' in marking and marking['color'] is not None:
            for col in range(5):
                item.setBackground(col, marking['color'])
        
        if 'tag' in marking:
            item.setText(4, marking['tag'])
        
        item.setData(0, QtCore.Qt.UserRole, entry)
        
        if not subtitle:
            item.setForeground(2, QtGui.QBrush(QtGui.QColor(128, 128, 128)))
            
        if entry.get("Source") == "MediaFilesNotInAnyBank":
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(100, 100, 200)))
            
        return item 
    def restore_tree_selection(self, tree, target_keys):
        """Restore tree selection after refresh"""
        def search_and_select(parent_item):
            for i in range(parent_item.childCount()):
                try:
                    item = parent_item.child(i)
                    if item.childCount() == 0:
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
        if not self.mod_p_path:
            return

        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        if hasattr(self, 'volume_adjust_action'):
            if len(file_items) == 0:
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_no_selection"))
                self.volume_adjust_action.setEnabled(False)
            elif len(file_items) == 1:
                entry = file_items[0].data(0, QtCore.Qt.UserRole)
                filename = entry.get('ShortName', 'file') if entry else 'file'
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_single").format(filename=filename))
                self.volume_adjust_action.setEnabled(True)
            else:
                self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_batch").format(count=len(file_items)))
                self.volume_adjust_action.setEnabled(True)
        if not items:
            widgets["play_mod_btn"].hide()
            return
            
        item = items[0]
        if item.childCount() > 0:
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
        marking = self.marked_items.get(key, {})
        tag = marking.get('tag', 'None')
        widgets["info_labels"]["tag"].setText(tag)
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
        
        file_id = entry.get("Id", "")
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        has_mod = os.path.exists(mod_wem_path) if mod_wem_path else False
        widgets["play_mod_btn"].setVisible(has_mod)
        
        self.load_audio_comparison_info(file_id, lang, widgets)
    def load_audio_comparison_info(self, file_id, lang, widgets):
        self.current_bnk_request_id += 1
        request_id = self.current_bnk_request_id

        original_wem_path = self.get_original_path(file_id, lang)
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        date_format = "%Y-%m-%d %H:%M:%S"

        original_info = self.get_wem_audio_info_with_markers(original_wem_path) if os.path.exists(original_wem_path) else None
        if original_info:
            original_info['file_size'] = os.path.getsize(original_wem_path)

        modified_info = self.get_wem_audio_info_with_markers(mod_wem_path) if os.path.exists(mod_wem_path) else None

        if modified_info:
            modified_info['file_size'] = os.path.getsize(mod_wem_path)
            try:
                mtime = os.path.getmtime(mod_wem_path)
                modified_info['modified_date'] = datetime.fromtimestamp(mtime).strftime(date_format)
            except OSError:
                modified_info['modified_date'] = "N/A"
        
        if original_info:
            formatted_original = self.format_audio_info(original_info)
            for key, label in widgets["original_info_labels"].items():
                if key in formatted_original: label.setText(formatted_original[key])
            size_kb = original_info['file_size'] / 1024
            widgets["original_info_labels"]["size"].setText(f"{size_kb/1024:.1f} KB" if size_kb >= 1024 else f"{size_kb:.1f} KB")
            widgets["original_info_labels"]["modified_date"].setText(original_info.get('modified_date', 'N/A'))
            widgets["original_markers_list"].clear()
            original_markers = self.format_markers_for_display(original_info.get('markers', []))
            widgets["original_markers_list"].addItems(original_markers or ["No markers found"])
        else:
            for label_key in ["duration", "size", "sample_rate", "bitrate", "channels", "modified_date"]: 
                widgets["original_info_labels"][label_key].setText("N/A")
            widgets["original_markers_list"].clear()
            widgets["original_markers_list"].addItem("File not available")

        if modified_info:
            formatted_modified = self.format_audio_info(modified_info)
            for key, label in widgets["modified_info_labels"].items():
                if key in formatted_modified: label.setText(formatted_modified[key])
            size_kb = modified_info['file_size'] / 1024
            size_text = f"{size_kb/1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.1f} KB"
            widgets["modified_info_labels"]["size"].setStyleSheet("")
            widgets["modified_info_labels"]["size"].setText(size_text)
            widgets["modified_info_labels"]["modified_date"].setText(modified_info.get('modified_date', 'N/A'))
            widgets["modified_markers_list"].clear()
            modified_markers = self.format_markers_for_display(modified_info.get('markers', []))
            widgets["modified_markers_list"].addItems(modified_markers or ["No markers found"])
        else:
            for label_key in ["duration", "size", "sample_rate", "bitrate", "channels", "modified_date"]:
                widgets["modified_info_labels"][label_key].setText("N/A")
                widgets["modified_info_labels"][label_key].setStyleSheet("")
            widgets["modified_markers_list"].clear()
            widgets["modified_markers_list"].addItem("No modified audio")

        for label in ["bnk_size", "override_fx"]:
            widgets["original_info_labels"][label].setText("<i>Loading...</i>")
            widgets["modified_info_labels"][label].setText("<i>Loading...</i>")
        
        if self.bnk_loader_thread and self.bnk_loader_thread.isRunning():
            self.bnk_loader_thread.terminate()
            self.bnk_loader_thread.wait()

        try:
            source_id = int(file_id)
        except (ValueError, TypeError):
            DEBUG.log(f"Invalid file_id for BNK search: {file_id}", "ERROR")
            for label in ["bnk_size", "override_fx"]:
                widgets["original_info_labels"][label].setText("<span style='color:red;'>Error</span>")
                widgets["modified_info_labels"][label].setText("<span style='color:red;'>Error</span>")
            return
            
        bnk_files_info = self.find_relevant_bnk_files() 
        
        self.bnk_loader_thread = BnkInfoLoader(self, source_id, bnk_files_info, self.mod_p_path, os.path.join(self.base_path, "Wems"))
        
        real_original_wem_size = original_info['file_size'] if original_info else 0
        real_modified_wem_size = modified_info['file_size'] if modified_info else 0

        self.bnk_loader_thread.info_loaded.connect(
            lambda sid, orig_info, mod_info: self.update_bnk_info_ui(
                request_id, sid, widgets, orig_info, mod_info, 
                real_original_wem_size, real_modified_wem_size
            )
        )

        self.bnk_loader_thread.start()

    def fix_bnk_size(self, file_id, lang, new_size):
        """Updates the BNK file with the correct WEM file size."""
        DEBUG.log(f"Attempting to fix BNK size for ID {file_id} in lang {lang} to new size {new_size}")
        
        try:
            source_id = int(file_id)
            bnk_fixed = False
            
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if not os.path.exists(mod_bnk_path):
                    continue
                
                editor = BNKEditor(mod_bnk_path)
                
                if editor.modify_sound(source_id, new_size=new_size, find_by_size=None):
                    editor.save_file()
                    self.invalidate_bnk_cache(source_id)
                    
                    DEBUG.log(f"Successfully fixed size in {os.path.basename(mod_bnk_path)}.")
                    bnk_fixed = True
                    break

            if bnk_fixed:
                QtWidgets.QMessageBox.information(self, "Success", "BNK file size has been successfully updated!")
                self.on_selection_changed(lang)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not find an entry for ID {file_id} in any modded BNK file to fix.")
        
        except Exception as e:
            DEBUG.log(f"Error fixing BNK size: {e}", "ERROR")
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred while fixing the BNK file:\n{str(e)}")
    def update_bnk_info_ui(self, request_id, source_id, widgets, original_bnk_info, modified_bnk_info, real_original_wem_size, real_modified_wem_size):
        if request_id != self.current_bnk_request_id:
            return

        try:
            widgets["original_info_labels"]["bnk_size"].isVisible()
        except RuntimeError:
            DEBUG.log("Widgets were deleted, BNK UI update cancelled.", "WARNING")
            return

        bnk_size_button = widgets["modified_info_labels"]["bnk_size"]
        
        try:
            bnk_size_button.clicked.disconnect()
        except TypeError:
            pass
        bnk_size_button.setEnabled(False)
        bnk_size_button.setCursor(QtCore.Qt.ArrowCursor)

        is_dark = self.settings.data.get("theme", "light") == "dark"
        text_color = "#d4d4d4" if is_dark else "#000000"  

        bnk_size_button.setStyleSheet(f"QPushButton {{ text-align: left; padding: 0; border: none; background: transparent; color: {text_color}; }}")

        if original_bnk_info:
            widgets["original_info_labels"]["bnk_size"].setText(f"{original_bnk_info.file_size / 1024:.1f} KB")
            fx_status = "Disabled" if original_bnk_info.override_fx else "Enabled"
            fx_color = "#F44336" if original_bnk_info.override_fx else "#4CAF50"
            widgets["original_info_labels"]["override_fx"].setText(f"<b style='color:{fx_color};'>{fx_status}</b>")
        else:
            widgets["original_info_labels"]["bnk_size"].setText("N/A")
            widgets["original_info_labels"]["override_fx"].setText("N/A")
            
        file_id = str(source_id)
        current_lang = self.get_current_language()
        
        mod_wem_exists = real_modified_wem_size > 0

        if modified_bnk_info:
            expected_bnk_size = modified_bnk_info.file_size
            
            if mod_wem_exists:
                actual_wem_size = real_modified_wem_size 
                
                if actual_wem_size == expected_bnk_size:
                    bnk_size_button.setText(f"{expected_bnk_size / 1024:.1f} KB")
                    bnk_size_button.setToolTip("OK: Actual file size matches the BNK record.")
            
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: green; font-weight: bold; background: transparent; }")
                else:
                    bnk_size_button.setText(f"Mismatch! Click to fix")
                    bnk_size_button.setToolTip(f"BNK expects {expected_bnk_size:,} bytes, but file is {actual_wem_size:,} bytes.\nClick to update the BNK record.")
               
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: red; font-weight: bold; text-decoration: underline; background: transparent; }")
                    bnk_size_button.setCursor(QtCore.Qt.PointingHandCursor)
                    bnk_size_button.setEnabled(True)
                    bnk_size_button.clicked.connect(lambda: self.fix_bnk_size(file_id, current_lang, actual_wem_size))
            else:
                if original_bnk_info and expected_bnk_size != original_bnk_info.file_size:
                    bnk_size_button.setText("Missing WEM! Click to revert")
                    bnk_size_button.setToolTip(f"BNK record was modified, but the WEM file is missing.\nClick to revert the BNK record to its original state.")
                 
                    bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; border: none; color: red; font-weight: bold; text-decoration: underline; background: transparent; }")
                    bnk_size_button.setCursor(QtCore.Qt.PointingHandCursor)
                    bnk_size_button.setEnabled(True)
                    bnk_size_button.clicked.connect(lambda: self.revert_single_bnk_entry(file_id, current_lang))
                else:
            
                    bnk_size_button.setText(f"{expected_bnk_size / 1024:.1f} KB")
                    bnk_size_button.setStyleSheet(f"QPushButton {{ text-align: left; padding: 0; border: none; color: {text_color}; background: transparent; }}")

            fx_status = "Disabled" if modified_bnk_info.override_fx else "Enabled"
            fx_color = "#F44336" if modified_bnk_info.override_fx else "#4CAF50"
            widgets["modified_info_labels"]["override_fx"].setText(f"<b style='color:{fx_color};'>{fx_status}</b>")
        
        else:
            bnk_size_button.setText("N/A")
            widgets["modified_info_labels"]["override_fx"].setText("N/A")
    def revert_single_bnk_entry(self, file_id, lang):
        """Reverts BNK entry to original values in ALL matching BNK files."""
        DEBUG.log(f"Reverting BNK entries for ID {file_id}")
        try:
            source_id = int(file_id)
            reverted_count = 0
            
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
               
                original_bnk = BNKEditor(bnk_path)
                original_entries = original_bnk.find_sound_by_source_id(source_id)
                if not original_entries:
                    continue
                
                original_entry = original_entries[0]

                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if os.path.exists(mod_bnk_path):
                    mod_editor = BNKEditor(mod_bnk_path)
                    
                    if mod_editor.modify_sound(source_id, 
                                               new_size=original_entry.file_size, 
                                               override_fx=original_entry.override_fx):
                        mod_editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        reverted_count += 1
                        DEBUG.log(f"Reverted entry in {os.path.basename(mod_bnk_path)}")

            if reverted_count > 0:
                QtWidgets.QMessageBox.information(self, "Success", f"Reverted {reverted_count} BNK entries.")
                self.on_selection_changed(lang)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "No BNK entries needed reverting.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
    def get_file_durations(self, file_id, lang, widgets):

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
            

        mod_wem_path = self.get_mod_path(file_id, lang)
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

        try:
            result = subprocess.run(
                [self.vgmstream_path, "-m", wem_path],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                samples = None
                sample_rate = 48000 
                
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
   
        wem_path = os.path.join(self.wem_root, lang, f"{file_id}.wem")
        if os.path.exists(wem_path):
            self.original_size = os.path.getsize(wem_path)
            widgets["info_labels"]["size"].setText(f"{self.original_size / 1024:.1f} KB")
        else:
            self.original_size = 0
            widgets["info_labels"]["size"].setText("N/A")
            
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        if os.path.exists(mod_wem_path):
            self.mod_size = os.path.getsize(mod_wem_path)
            widgets["info_labels"]["mod_size"].setText(f"{self.mod_size / 1024:.1f} KB")
            
            
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
        self.stop_audio()    
        item = items[0]
        entry = item.data(0, QtCore.Qt.UserRole)
        if not entry:
            return
            
        id_ = entry.get("Id", "")
        
        if play_mod:

            if current_lang != "SFX":
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", current_lang, f"{id_}.wem")
            else:
                wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{id_}.wem")
          
            
            if not os.path.exists(wem_path):
             
                old_wem_path_lang = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", current_lang, f"{id_}.wem")
                old_wem_path_sfx = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{id_}.wem")
                
                if os.path.exists(old_wem_path_lang):
                    wem_path = old_wem_path_lang
                elif os.path.exists(old_wem_path_sfx):
                    wem_path = old_wem_path_sfx
                else:
                    self.status_bar.showMessage(f"Mod audio not found: {wem_path}", 3000)
                    DEBUG.log(f"Mod audio not found at: {wem_path}", "WARNING")
                    return
            self.is_playing_mod = True
        else:
      
            wem_path = self.get_original_path(id_, current_lang)
            
            if not os.path.exists(wem_path):
                self.status_bar.showMessage(f"File not found: {wem_path}", 3000)
                return
            self.is_playing_mod = False
            
        source_type = "MOD" if play_mod else "Original"
        self.status_bar.showMessage(f"Converting {source_type} to WAV...")
        QtWidgets.QApplication.processEvents()
        
        try:
            temp_file_handle = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav = temp_file_handle.name
            temp_file_handle.close()
            DEBUG.log(f"Generated unique temp WAV path: {temp_wav}")
        except Exception as e:
            DEBUG.log(f"Failed to create temp file: {e}", "ERROR")
            self.status_bar.showMessage("Error creating temporary file", 3000)
            return
        
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
        pos_sec = (position % 60000) / 1000
        pos_str = f"{pos_min:02d}:{pos_sec:06.3f}" 

        dur_min = duration // 60000
        dur_sec = (duration % 60000) / 1000
        dur_str = f"{dur_min:02d}:{dur_sec:06.3f}"

        source_type = " [MOD]" if self.is_playing_mod else ""
        
        time_text = f"{pos_str} / {dur_str} {source_type}"
        
        widgets["time_label"].setText(time_text)

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
        
        DEBUG.log(f"Editing subtitle for: {key} from main audio tab")
        
        editor = SubtitleEditor(self, key, current_subtitle, original_subtitle)
        if editor.exec_() == QtWidgets.QDialog.Accepted:
            new_subtitle = editor.get_text()
            self.subtitles[key] = new_subtitle
        
            if key in self.key_to_file_map:
                file_info = self.key_to_file_map[key]
                self.dirty_subtitle_files.add(file_info['path'])
                DEBUG.log(f"Marked file as dirty from main tab edit: {file_info['path']}")

            if new_subtitle != original_subtitle:
                self.modified_subtitles.add(key)
            else:
                self.modified_subtitles.discard(key)
            
            try:
                if not self.is_item_deleted(item):
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
            except RuntimeError:
                DEBUG.log("Item was deleted during update from main tab, refreshing tree.", "WARNING")
                self.populate_tree(current_lang)

            self.status_bar.showMessage("Subtitle updated", 2000)
            self.update_status()

    def find_tree_item_by_key(self, tree, target_key, target_entry):

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

            for i, (file_path, data) in enumerate(subtitle_files_to_update.items()):
                file_info = data['file_info']
                all_subtitles = data['all_subtitles']
                
                progress.set_progress(
                    int((i / len(subtitle_files_to_update)) * 100),
                    f"Processing {file_info['filename']} ({current_language})..."
                )
                
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

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(self.tr("export_audio"))
        msg.setText(self.tr("which_version_export"))
        
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        mod_btn = None
        
        mod_wem_path = self.get_mod_path(id_, current_lang)
        if mod_wem_path and os.path.exists(mod_wem_path):
            mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
            
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        self.show_dialog(msg)
        
        clicked_button = msg.clickedButton()
        wem_path = None

        if clicked_button == original_btn:
            wem_path = self.get_original_path(id_, current_lang)
        elif mod_btn and clicked_button == mod_btn:
            wem_path = mod_wem_path
        else:
            return
            
        if not wem_path or not os.path.exists(wem_path):
            self.status_bar.showMessage(f"Source file not found: {wem_path}", 3000)
            return
            
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr("save_as_wav"), shortname, 
            f"{self.tr('wav_files')} (*.wav)"
        )
        
        if save_path:
            if os.path.exists(save_path):
                reply = self.show_message_box(
                    QtWidgets.QMessageBox.Question,
                    "File Exists",
                    f"The file '{os.path.basename(save_path)}' already exists.",
                    "Do you want to overwrite it?",
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    return

            progress = ProgressDialog(self, f"Exporting {shortname}...")
            progress.show()
            progress.raise_()
            progress.activateWindow()

            thread = threading.Thread(
                target=self._export_single_wav_thread, 
                args=(wem_path, save_path, progress)
            )
            thread.daemon = True
            thread.start()
    def _export_single_wav_thread(self, wem_path, save_path, progress_dialog):
        try:
            ok, err = self.wem_to_wav_vgmstream(wem_path, save_path)
            
            QtCore.QMetaObject.invokeMethod(
                self, "_on_single_export_finished", QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, ok),
                QtCore.Q_ARG(str, save_path),
                QtCore.Q_ARG(str, err),
                QtCore.Q_ARG(object, progress_dialog)
            )
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self, "_on_single_export_finished", QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False),
                QtCore.Q_ARG(str, save_path),
                QtCore.Q_ARG(str, str(e)),
                QtCore.Q_ARG(object, progress_dialog)
            )
    @QtCore.pyqtSlot(bool, str, str, object)
    def _on_single_export_finished(self, ok, save_path, error_message, progress_dialog):
        progress_dialog.close() 

        if ok:
            self.status_bar.showMessage(f"Saved: {save_path}", 3000)
            self.show_message_box(
                QtWidgets.QMessageBox.Information,
                self.tr("export_complete"),
                f"File successfully exported to:\n{save_path}"
            )
        else:
            self.show_message_box(
                QtWidgets.QMessageBox.Warning,
                "Error",
                f"Conversion failed: {error_message}"
            )
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
    def toggle_ingame_effects(self):
        current_lang = self.get_current_language()
        if not current_lang:
            return

        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        file_items = [item for item in tree.selectedItems() if item.childCount() == 0]

        if not file_items:
            return

        bnk_files = self.find_relevant_bnk_files()
        if not bnk_files:
            QtWidgets.QMessageBox.warning(self, "Error", "No BNK files found for modification.")
            return
            
        modified_count = 0
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if not entry:
                continue

            source_id = int(entry.get("Id", ""))
            shortname = entry.get("ShortName", "")
            
            bnk_files_info = self.find_relevant_bnk_files()
            for bnk_path, bnk_type in bnk_files_info:
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else: # 'lang'
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)

                original_editor = BNKEditor(bnk_path)
                if not original_editor.find_sound_by_source_id(source_id):
                    continue 

                if not os.path.exists(mod_bnk_path):
                    os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                    shutil.copy2(bnk_path, mod_bnk_path)
                
                editor = BNKEditor(mod_bnk_path)
                current_entries = editor.find_sound_by_source_id(source_id)

                if current_entries:
                    current_state = current_entries[0].override_fx
                    new_state = not current_state
                    
                    if editor.modify_sound(source_id, override_fx=new_state, find_by_size=None):
                        editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        DEBUG.log(f"FX for {shortname} (ID: {source_id}) changed from {current_state} to {new_state} in {os.path.basename(mod_bnk_path)}")
                        modified_count += 1
                        bnk_found_and_modified = True
                        break 
            
            if not bnk_found_and_modified:
                DEBUG.log(f"Could not find or modify record for {shortname} (ID: {source_id}) in any BNK file.", "WARNING")

        self.populate_tree(current_lang)
        self.status_bar.showMessage(f"In-Game Effects changed for {modified_count} files.", 3000)
    def create_menu_bar(self):
        menubar = self.menuBar()
        
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

        self.rebuild_bnk_action = tools_menu.addAction(self.tr("rebuild_bnk_index"))
        self.rebuild_bnk_action.setToolTip(self.tr("rebuild_bnk_tooltip"))
        self.rebuild_bnk_action.triggered.connect(self.rebuild_bnk_index)
        tools_menu.addSeparator()
        self.rescan_orphans_action = tools_menu.addAction(self.tr("rescan_orphans_action"))
        self.rescan_orphans_action.setToolTip(self.tr("rescan_orphans_tooltip"))
        self.rescan_orphans_action.triggered.connect(self.perform_blocking_orphan_scan)
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
    def load_orphans_from_cache_or_scan(self):
        """Loads orphaned files from cache or performs a synchronous scan with a progress dialog."""
        if os.path.exists(self.orphaned_cache_path):
            DEBUG.log(f"Loading orphaned files from cache: {self.orphaned_cache_path}")
            try:
                with open(self.orphaned_cache_path, 'r', encoding='utf-8') as f:
                    self.orphaned_files_cache = json.load(f)
                DEBUG.log(f"Loaded {len(self.orphaned_files_cache)} orphans from cache.")
                self.rebuild_file_list_with_orphans()
            except Exception as e:
                DEBUG.log(f"Error loading orphan cache: {e}. Starting a new scan.", "ERROR")
                self.perform_blocking_orphan_scan()
        else:
            DEBUG.log("Orphan cache not found. Starting initial scan.")
            self.perform_blocking_orphan_scan()
    def perform_blocking_orphan_scan(self):
        """Performs a synchronous scan of the Wems folder with a progress dialog, blocking the UI."""
        self.all_files = [f for f in self.all_files if f.get("Source") != "ScannedFromFileSystem"]
        self.orphaned_files_cache = []
        DEBUG.log("Cleared existing orphan files to perform a full rescan.")

        progress = ProgressDialog(self, self.tr("scan_progress_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.set_progress(0, "Preparing to scan...")
        progress.show()
        QtWidgets.QApplication.processEvents()

        known_ids = {entry.get("Id") for entry in self.load_all_soundbank_files(self.soundbanks_path) if entry.get("Id")}
        
        orphaned_entries = []
        if not os.path.exists(self.wem_root):
            progress.close()
            self.rebuild_file_list_with_orphans()
            return

        all_wem_paths = []
        for root, _, files in os.walk(self.wem_root):
            for file in files:
                if file.lower().endswith('.wem'):
                    all_wem_paths.append(os.path.join(root, file))

        wem_files_to_scan = [
            path for path in all_wem_paths 
            if os.path.splitext(os.path.basename(path))[0] not in known_ids
        ]
        
        total_files = len(wem_files_to_scan)
        if total_files == 0:
            DEBUG.log("No new orphan files found.")
            progress.close()
            self.rebuild_file_list_with_orphans() 
            self.status_bar.showMessage("No new audio files found during scan.", 5000)
            return
            
        progress.set_progress(5, f"Scanning {total_files} new files...")
        QtWidgets.QApplication.processEvents()

        for i, full_path in enumerate(wem_files_to_scan):
            if i % 20 == 0:
                QtWidgets.QApplication.processEvents()
                progress.set_progress(int((i / total_files) * 100), f"Scanning {os.path.basename(full_path)}")

            file_id = os.path.splitext(os.path.basename(full_path))[0]
      
            rel_path = os.path.relpath(os.path.dirname(full_path), self.wem_root)
            parts = rel_path.split(os.sep)
            
            lang = "SFX"
            if rel_path == '.' or rel_path == "SFX":
                lang = "SFX"
            elif parts[0] == "Media":
                if len(parts) > 1:
                    lang = parts[1]
                else:
                    lang = "SFX"
            else:
                lang = rel_path

            short_name = f"{file_id}.wav"
            try:
                analyzer = WEMAnalyzer(full_path)
                if analyzer.analyze():
                    markers = analyzer.get_markers_info()
                    if markers and markers[0]['label']:
                        short_name = f"{markers[0]['label']}.wav"
            except Exception:
                pass

            new_entry = {
                "Id": file_id, "Language": lang, "ShortName": short_name, 
                "Path": os.path.basename(full_path), "Source": "ScannedFromFileSystem"
            }
            orphaned_entries.append(new_entry)

        progress.set_progress(100, "Finalizing...")
        
        self.orphaned_files_cache = orphaned_entries
        try:
            with open(self.orphaned_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.orphaned_files_cache, f, indent=2)
            DEBUG.log(f"Saved {len(orphaned_entries)} orphaned files to cache.")
        except Exception as e:
            DEBUG.log(f"Failed to save orphan cache: {e}", "ERROR")

        progress.close()
        self.rebuild_file_list_with_orphans()
        self.status_bar.showMessage(f"Rescan complete. Found and cached {len(orphaned_entries)} additional audio files.", 5000)
    def start_orphan_scan(self, force=False):
        """Starts the background thread to scan for orphaned WEM files."""
        if self.scanner_thread and self.scanner_thread.isRunning():
            DEBUG.log("Scan is already in progress.", "WARNING")
            if not force:
                return
            else:
                self.scanner_thread.stop()
                self.scanner_thread.wait()

        is_first_scan = not os.path.exists(self.orphaned_cache_path)
        if is_first_scan or force:
            if self.scan_message_box:
                self.scan_message_box.close()

            title = "Initial File Scan" if is_first_scan else "Rescanning Files"
            message = ("The app is scanning your 'Wems' folder to find all available audio files.\n\n"
                       "This may take a moment. You can continue using the main window while this is in progress.")

            self.scan_message_box = QtWidgets.QMessageBox(self)
            self.scan_message_box.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
            self.scan_message_box.setIcon(QtWidgets.QMessageBox.Information)
            self.scan_message_box.setWindowTitle(title)
            self.scan_message_box.setText("<b>Scanning in Background...</b>")
            self.scan_message_box.setInformativeText(message)
            
            hide_button = self.scan_message_box.addButton("Hide", QtWidgets.QMessageBox.ActionRole)
            hide_button.clicked.connect(self.hide_scan_notification)
            
            self.scan_message_box.setModal(False)
            self.scan_message_box.show()

        if force:
            self.all_files = [f for f in self.all_files if f.get("Source") != "ScannedFromFileSystem"]
            self.entries_by_lang = self.group_by_language()
            for lang in self.tab_widgets.keys():
                self.populate_tree(lang)
            self.status_bar.showMessage("Forced rescan started... You can continue working.", 0)
        else:
            self.status_bar.showMessage("Scanning for additional audio files... You can continue working.", 0)

        known_ids = {entry.get("Id") for entry in self.load_all_soundbank_files(self.soundbanks_path) if entry.get("Id")}
        self.scanner_thread = WemScannerThread(self.wem_root, known_ids, self)
        self.scanner_thread.scan_finished.connect(self._on_scan_finished)
        self.scanner_thread.start()
    def hide_scan_notification(self):
        """Safely closes the scanning notification message box if it exists."""
        if self.scan_message_box:
            self.scan_message_box.close()
            self.scan_message_box = None
    @QtCore.pyqtSlot(list)
    def _on_scan_finished(self, orphaned_files):
        """Handles the completion of the background WEM scan."""
        self.hide_scan_notification()

        count = len(orphaned_files)
        DEBUG.log(f"Orphan scan finished. Found {count} additional files.")
        
        self.orphaned_files_cache = orphaned_files
        try:
            with open(self.orphaned_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.orphaned_files_cache, f, indent=2)
            DEBUG.log(f"Saved {count} orphaned files to cache.")
        except Exception as e:
            DEBUG.log(f"Failed to save orphan cache: {e}", "ERROR")

        self.rebuild_file_list_with_orphans()
        
        self.status_bar.showMessage(f"Scan complete. Found and cached {count} additional audio files.", 5000)

    def rebuild_file_list_with_orphans(self):
  
        base_files = self.load_all_soundbank_files(self.soundbanks_path)
        self._build_wem_index()

        filtered_base_files = []
        for entry in base_files:
            file_id = entry.get("Id")
      
            if file_id and file_id in self.wem_index:
                filtered_base_files.append(entry)
        
        DEBUG.log(f"Filtered SoundbanksInfo: {len(filtered_base_files)} entries have a physical .wem file (out of {len(base_files)} loaded from JSON).")

        show_orphans = self.settings.data.get("show_orphaned_files", False)
        
       
        if not filtered_base_files and self.orphaned_files_cache:
            DEBUG.log("Main database matched 0 files. Forcing display of scanned orphans.")
            self.all_files = self.orphaned_files_cache
        elif show_orphans and self.orphaned_files_cache:
         
            existing_ids = {entry["Id"] for entry in filtered_base_files}
            unique_orphans = [o for o in self.orphaned_files_cache if o["Id"] not in existing_ids]
            
            DEBUG.log(f"Adding {len(unique_orphans)} unique orphans to the main list.")
            self.all_files = filtered_base_files + unique_orphans
        else:
            self.all_files = filtered_base_files

        DEBUG.log(f"Total files to display: {len(self.all_files)}")

        self.entries_by_lang = self.group_by_language()
        
        active_tabs_to_update = list(self.populated_tabs) 
        for lang in active_tabs_to_update:
             if lang in self.tab_widgets:
                self.populate_tree(lang)
        
        for lang, widgets in self.tab_widgets.items():
            try:
                if widgets["tree"].parent() and widgets["tree"].parent().parent():
                    current_tab_index = self.tabs.indexOf(widgets["tree"].parent().parent())
                    if current_tab_index != -1:
                        total_count = len(self.entries_by_lang.get(lang, []))
                        self.tabs.setTabText(current_tab_index, f"{lang} ({total_count})")
            except:
                pass
        
        self.update_status()
    def show_debug_console(self):
        if self.debug_window is None:
            self.debug_window = DebugWindow(self)
        self.debug_window.show()
        self.debug_window.raise_()
    def get_mods_root_path(self, prompt_if_missing=False):

        mods_root = self.settings.data.get("mods_root_path", "")
        if (not mods_root or not os.path.isdir(mods_root)) and prompt_if_missing:
            QtWidgets.QMessageBox.information(self, "Setup Mods Folder", "Please select a folder where you want to store your mod profiles.")
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a Folder to Store Your Mods")
            if folder:
                self.settings.data["mods_root_path"] = folder
                self.settings.save()
                return folder
            else:
                return None
        return mods_root

    def migrate_or_load_profiles(self):
        mods_root = self.get_mods_root_path()
        legacy_mod_p_path = os.path.join(self.base_path, "MOD_P")

        if not mods_root and os.path.exists(legacy_mod_p_path):
            DEBUG.log("Legacy MOD_P folder found. Initiating migration process.")
            self.handle_legacy_mod_p_migration(legacy_mod_p_path)
        
        self.load_profiles()

    def load_profiles(self):
        self.profiles = {}
        mods_root = self.get_mods_root_path()
        if not mods_root:
            self.update_profile_ui()
            self.set_active_profile(None)
            return

        for profile_name in os.listdir(mods_root):
            profile_path = os.path.join(mods_root, profile_name)
            profile_json_path = os.path.join(profile_path, "profile.json")
            mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
            if os.path.isdir(profile_path) and os.path.exists(profile_json_path) and os.path.isdir(mod_p_path):
                try:
                    with open(profile_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.profiles[profile_name] = {
                        "path": profile_path,
                        "mod_p_path": mod_p_path,
                        "icon": os.path.join(profile_path, "icon.png"),
                        "data": data
                    }
                except Exception as e:
                    DEBUG.log(f"Failed to load profile '{profile_name}': {e}", "WARNING")

        last_active = self.settings.data.get("active_profile")
        if last_active and last_active in self.profiles:
            self.set_active_profile(last_active)
        elif self.profiles:
            first_profile = sorted(self.profiles.keys())[0]
            self.set_active_profile(first_profile)
        else:

            self.set_active_profile(None)

        self.update_profile_ui()
    def show_profile_manager(self):
        dialog = ProfileManagerDialog(self)
        dialog.profile_changed.connect(self.on_profile_system_changed)
        dialog.exec_()
    
    def on_profile_system_changed(self):

        self.load_profiles_from_settings()
        self.load_subtitles()

    def load_profiles_from_settings(self):
        profiles = self.settings.data.get("mod_profiles", {})
        active_name = self.settings.data.get("active_profile", "")

        if active_name and active_name in profiles:
            profile_path = profiles[active_name]
            mod_p_path = os.path.join(profile_path, f"{active_name}_P")
            
            if os.path.isdir(mod_p_path):
                self.active_profile_name = active_name
                self.mod_p_path = mod_p_path
                self.setWindowTitle(f"{self.tr('app_title')} - [{active_name}]")
                DEBUG.log(f"Loaded active profile: {active_name}")
            else:
                self.reset_active_profile()
        else:
            self.reset_active_profile()

        self.load_subtitles()

        current_lang = self.get_current_language()
        if current_lang:
            self.populate_tree(current_lang)

    def reset_active_profile(self):
        self.active_profile_name = None
        self.mod_p_path = None
        self.settings.data["active_profile"] = ""
        self.settings.save()
        self.setWindowTitle(self.tr("app_title"))
        DEBUG.log("Active profile was invalid or not set. Resetting.")
        
    def update_profile_ui(self):
        
        if not hasattr(self, 'profile_combo'):
            if self.active_profile_name:
                self.setWindowTitle(f"{self.tr('app_title')} - [{self.active_profile_name}]")
            else:
                self.setWindowTitle(self.tr("app_title"))
            return

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        
        if not self.profiles:
            self.profile_combo.addItem("No Profiles Found")
            self.profile_combo.setEnabled(False)
            self.profile_combo.blockSignals(False)
            return

        self.profile_combo.setEnabled(True)
        for profile_name in sorted(self.profiles.keys()):
            icon_path = self.profiles[profile_name]["icon"]
            icon = QtGui.QIcon(icon_path) if os.path.exists(icon_path) else QtGui.QIcon()
            self.profile_combo.addItem(icon, profile_name)
        
        if self.active_profile_name:
            self.profile_combo.setCurrentText(self.active_profile_name)

        self.profile_combo.blockSignals(False)

    def set_active_profile(self, profile_name):
        if profile_name and profile_name in self.profiles:
            self.active_profile_name = profile_name
            self.mod_p_path = self.profiles[profile_name]["mod_p_path"]
            self.settings.data["active_profile"] = profile_name
            self.setWindowTitle(f"{self.tr('app_title')} - [{profile_name}]")
            DEBUG.log(f"Switched to profile: {profile_name}. MOD_P path: {self.mod_p_path}")
        else:
            self.active_profile_name = None
            self.mod_p_path = None
            self.settings.data["active_profile"] = ""
            self.setWindowTitle(self.tr("app_title"))
            DEBUG.log("No active profile.")
        
        self.settings.save()
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            if current_lang not in self.populated_tabs:
                 self.populated_tabs.add(current_lang)
            self.populate_tree(current_lang)

    def switch_profile_by_index(self, index):
        profile_name = self.profile_combo.itemText(index)
        if profile_name in self.profiles:
            self.set_active_profile(profile_name)
    
    def create_new_profile(self):
        mods_root = self.get_mods_root_path(prompt_if_missing=True)
        if not mods_root:
            return

        dialog = ProfileDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            profile_name = profile_data["name"]
            
            if profile_name in self.profiles:
                QtWidgets.QMessageBox.warning(self, "Error", "A profile with this name already exists.")
                return

            profile_path = os.path.join(mods_root, profile_name)
            mod_p_path = os.path.join(profile_path, f"{profile_name}_P")
            os.makedirs(mod_p_path, exist_ok=True)
            
            if profile_data["icon_path"] and os.path.exists(profile_data["icon_path"]):
                shutil.copy(profile_data["icon_path"], os.path.join(profile_path, "icon.png"))

            profile_json_path = os.path.join(profile_path, "profile.json")
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            self.load_profiles()
            self.set_active_profile(profile_name) 
            self.update_profile_ui()

    def edit_current_profile(self):
        if not self.active_profile_name or not self.mod_p_path:
            QtWidgets.QMessageBox.warning(self, "No Profile Selected", "Please select or create a profile to edit.")
            return

        current_profile = self.profiles[self.active_profile_name]
        dialog = ProfileDialog(self, existing_data=current_profile)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile_data = dialog.get_data()
            
            profile_path = current_profile["path"]
            profile_json_path = os.path.join(profile_path, "profile.json")
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data["info"], f, indent=2)

            icon_dest_path = os.path.join(profile_path, "icon.png")
            if profile_data["icon_path"]:
                 if not os.path.exists(profile_data["icon_path"]):
                     if os.path.exists(icon_dest_path):
                         os.remove(icon_dest_path)
                 else:
                     shutil.copy(profile_data["icon_path"], icon_dest_path)
            
            self.load_profiles()
    def create_toolbar(self):
        toolbar = QtWidgets.QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        self.profile_action = toolbar.addAction(f"👤 {self.tr('profiles')}")
        self.profile_action.setToolTip(self.tr("profile_manager_tooltip"))
        self.profile_action.triggered.connect(self.show_profile_manager)
        
        toolbar.addSeparator()
        self.edit_subtitle_action = toolbar.addAction(self.tr("edit_button"))
        self.edit_subtitle_action.setShortcut("F2")
        self.edit_subtitle_action.triggered.connect(self.edit_current_subtitle)
        
        self.save_wav_action = toolbar.addAction(self.tr("export_button"))
        self.save_wav_action.setShortcut("Ctrl+E")
        self.save_wav_action.triggered.connect(self.save_current_wav)
        self.volume_adjust_action = toolbar.addAction(self.tr("volume_toolbar_btn"))
        self.volume_adjust_action.setToolTip(self.tr("volume_adjust_tooltip_no_selection"))
        self.volume_adjust_action.triggered.connect(self.adjust_selected_volume)
        self.delete_mod_action = toolbar.addAction(self.tr("delete_mod_button"))
        self.delete_mod_action.setToolTip("Delete modified audio for selected file")
        self.delete_mod_action.triggered.connect(self.delete_current_mod_audio)
        toolbar.addSeparator()
        
        self.expand_all_action = toolbar.addAction(self.tr("expand_all"))
        self.expand_all_action.triggered.connect(self.expand_all_trees)
        
        self.collapse_all_action = toolbar.addAction(self.tr("collapse_all"))
        self.collapse_all_action.triggered.connect(self.collapse_all_trees)
    def adjust_selected_volume(self):
        """Adjust volume for selected file(s) - works for single or multiple selection"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            QtWidgets.QMessageBox.information(self, self.tr("no_language_selected"), self.tr("select_language_tab_first"))
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        
        if not file_items:
            QtWidgets.QMessageBox.information(self, self.tr("no_files_selected"), self.tr("select_files_for_volume"))
            return
        
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
        
        if len(file_items) == 1:
            entry = file_items[0].data(0, QtCore.Qt.UserRole)
            self.adjust_single_file_volume(entry, current_lang)
        else:
            self.adjust_multiple_files_volume(file_items, current_lang)

    def adjust_single_file_volume(self, entry, lang):
        """Adjust volume for single file"""
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText(self.tr("adjust_volume_for").format(filename=entry.get('ShortName', '')))
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        
        file_id = entry.get("Id", "")
        
        mod_wem_path = self.get_mod_path(file_id, lang)
        
        mod_btn = None
        if os.path.exists(mod_wem_path):
            mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
        
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        
        if msg.clickedButton() == original_btn:
            dialog = WemVolumeEditDialog(self, entry, lang, False)
            dialog.exec_()
        elif mod_btn and msg.clickedButton() == mod_btn:
            dialog = WemVolumeEditDialog(self, entry, lang, True)
            dialog.exec_()

    def adjust_multiple_files_volume(self, file_items, lang):
        """Adjust volume for multiple files"""

        entries_and_lang = []
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry:
                entries_and_lang.append((entry, lang))
        
        if not entries_and_lang:
            return
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText(self.tr("batch_adjust_volume_for").format(count=len(entries_and_lang)))

        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)

        has_mod_files = False
        for entry, _ in entries_and_lang:
            file_id = entry.get("Id", "")
            if lang != "SFX":
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
            else:
                mod_wem_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
            
            if os.path.exists(mod_wem_path):
                has_mod_files = True
                break
        
        mod_btn = None
        if has_mod_files:
            mod_btn = msg.addButton("Mod", QtWidgets.QMessageBox.ActionRole)
        
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        
        if msg.clickedButton() == original_btn:
            dialog = BatchVolumeEditDialog(self, entries_and_lang, False)
            dialog.exec_()
        elif mod_btn and msg.clickedButton() == mod_btn:
            dialog = BatchVolumeEditDialog(self, entries_and_lang, True)
            dialog.exec_()    
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
    def get_backup_path(self, file_id, lang):
        backup_root = os.path.join(self.base_path, ".backups", "audio")
        
        if lang != "SFX":
            backup_dir = os.path.join(backup_root, lang)
        else:
            backup_dir = os.path.join(backup_root, "SFX")
        
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"{file_id}.wem")
        
        DEBUG.log(f"Backup path for {file_id} ({lang}): {backup_path}")
        return backup_path

    def create_backup_if_needed(self, file_id, lang):
        if lang != "SFX":
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", lang, f"{file_id}.wem")
        else:
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", f"{file_id}.wem")
        
        backup_path = self.get_backup_path(file_id, lang)
        
        if os.path.exists(mod_path) and not os.path.exists(backup_path):
            shutil.copy2(mod_path, backup_path)
            DEBUG.log(f"Created backup: {backup_path}")
            return True
        
        DEBUG.log(f"Backup not created: mod_exists={os.path.exists(mod_path)}, backup_exists={os.path.exists(backup_path)}")
        return False

    def restore_from_backup(self, file_id, lang):
        backup_path = self.get_backup_path(file_id, lang)
        
        if not os.path.exists(backup_path):
            return False, "No backup found"
        
        try:
            backup_wem_size = os.path.getsize(backup_path)
        except Exception as e:
            return False, f"Could not read backup file: {e}"

        if lang != "SFX":
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", lang, f"{file_id}.wem")
        else:
            mod_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", f"{file_id}.wem")
        
        try:
            os.makedirs(os.path.dirname(mod_path), exist_ok=True)
            shutil.copy2(backup_path, mod_path)
            DEBUG.log(f"Restored WEM: {mod_path} (Size: {backup_wem_size})")
        except Exception as e:
            return False, str(e)
            
        try:
            source_id = int(file_id)
            bnk_updated_count = 0
            
            bnk_files_info = self.find_relevant_bnk_files()

            for bnk_path, bnk_type in bnk_files_info:
    
                if bnk_type == 'sfx':
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems", "SFX"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                else:
                    rel_path = os.path.relpath(bnk_path, os.path.join(self.base_path, "Wems"))
                    mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
                
                if not os.path.exists(mod_bnk_path):
                    os.makedirs(os.path.dirname(mod_bnk_path), exist_ok=True)
                    shutil.copy2(bnk_path, mod_bnk_path)
                    DEBUG.log(f"Created new mod BNK for restoration: {os.path.basename(mod_bnk_path)}")

                if os.path.exists(mod_bnk_path):
                    mod_editor = BNKEditor(mod_bnk_path)

                    if mod_editor.modify_sound(source_id, new_size=backup_wem_size):
                        mod_editor.save_file()
                        self.invalidate_bnk_cache(source_id)
                        bnk_updated_count += 1

            return True, f"Restored WEM and updated {bnk_updated_count} BNK files."
        
        except Exception as e:
            return False, f"WEM restored but BNK update failed: {str(e)}"
    def has_backup(self, file_id, lang):
        backup_path = self.get_backup_path(file_id, lang)
        exists = os.path.exists(backup_path)
        DEBUG.log(f"Checking backup for {file_id} ({lang}): {backup_path} - exists: {exists}")
        return exists
    def get_dark_menu_style(self):
        return """
            QMenu {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 2px; 
            }
            QMenu::item {
                padding: 4px 20px 4px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #555555;
                margin: 4px 0px 4px 0px;
            }
        """
    def show_context_menu(self, lang, pos):
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        if not items:
            return
            
        menu = QtWidgets.QMenu()
        if self.settings.data["theme"] == "dark":
            menu.setStyleSheet(self.get_dark_menu_style())
            
        file_items = [item for item in items if item.childCount() == 0 and item.data(0, QtCore.Qt.UserRole)]
        
        if file_items:
            play_action = menu.addAction(self.tr("play_original"))
            play_action.triggered.connect(self.play_current)
            menu.addSeparator()
        
            entry = items[0].data(0, QtCore.Qt.UserRole)
            mod_wem_path = None 

            if entry:
                file_id = entry.get('Id', '')
  
                mod_wem_path = self.get_mod_path(file_id, lang)
                
                if mod_wem_path and os.path.exists(mod_wem_path):
                    play_mod_action = menu.addAction(self.tr("play_mod"))
                    play_mod_action.triggered.connect(lambda: self.play_current(play_mod=True))
                    
                    delete_mod_action = menu.addAction(f" {self.tr('delete_mod_audio')}")
                    delete_mod_action.triggered.connect(lambda: self.delete_mod_audio(entry, lang))
                    menu.addSeparator()
                    
                if len(items) == 1 and items[0].childCount() == 0:
                    entry = items[0].data(0, QtCore.Qt.UserRole)
                    if entry:
                        file_id = entry.get("Id", "")    
                        menu.addSeparator()
                        quick_load_action = menu.addAction(self.tr("quick_load_audio_title"))
                        quick_load_action.setToolTip(self.tr("quick_load_audio_tooltip"))
                        quick_load_action.triggered.connect(
                            lambda: self.quick_load_custom_audio(entry, lang)
                        )
                        if self.has_backup(file_id, lang):
                            menu.addSeparator()
                            restore_action = menu.addAction(self.tr("restore_from_backup_title"))
                            restore_action.setToolTip(self.tr("restore_from_backup_tooltip"))
                            restore_action.triggered.connect(
                                lambda: self.restore_audio_from_backup(entry, lang)
                            )
                volume_original_action = menu.addAction(self.tr("adjust_original_volume_title"))
                volume_original_action.triggered.connect(lambda: self.adjust_wem_volume(entry, lang, False))    
                trim_original_action = menu.addAction(self.tr("trim_original_audio_title"))
                trim_original_action.triggered.connect(lambda: self.trim_audio(entry, lang, False))
                if os.path.exists(mod_wem_path):             
                    if os.path.exists(mod_wem_path):
                        volume_mod_action = menu.addAction(self.tr("adjust_mod_volume_title"))
                        volume_mod_action.triggered.connect(lambda: self.adjust_wem_volume(entry, lang, True))
                        trim_mod_action = menu.addAction(self.tr("trim_mod_audio_title"))
                        trim_mod_action.triggered.connect(lambda: self.trim_audio(entry, lang, True))
                    menu.addSeparator()

            toggle_fx_action = menu.addAction(self.tr("toggle_ingame_effects_title"))
            toggle_fx_action.triggered.connect(self.toggle_ingame_effects)
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
            menu.addSeparator()
            marking_menu = menu.addMenu(self.tr("marking_menu_title"))
    
            color_menu = marking_menu.addMenu(self.tr("set_color_menu_title"))
            colors = {
                self.tr("color_green"): QtGui.QColor(200, 255, 200),
                self.tr("color_yellow"): QtGui.QColor(255, 255, 200),
                self.tr("color_red"): QtGui.QColor(255, 200, 200),
                self.tr("color_blue"): QtGui.QColor(200, 200, 255),
                self.tr("color_none"): None
            }
            for color_name, color in colors.items():
                action = color_menu.addAction(color_name)
                action.triggered.connect(lambda checked, c=color: self.set_item_color(items, c))
            
            tag_menu = marking_menu.addMenu(self.tr("set_tag_menu_title"))
            tags = [self.tr("tag_important"), self.tr("tag_check"), self.tr("tag_done"), self.tr("tag_review"), "None"]
            for tag in tags:
                action = tag_menu.addAction(tag)
                action.triggered.connect(lambda checked, t=tag: self.set_item_tag(items, t if t != "None" else ""))
            custom_action = tag_menu.addAction(self.tr("tag_custom"))
            custom_action.triggered.connect(lambda: self.set_custom_tag(items))
            
        menu.exec_(tree.viewport().mapToGlobal(pos))
    def trim_audio(self, entry, lang, is_mod=False):
        dialog = AudioTrimDialog(self, entry, lang, is_mod)
        dialog.exec_()    
    def set_custom_tag(self, items):
        tag, ok = QtWidgets.QInputDialog.getText(self, self.tr("custom_tag_title"), self.tr("custom_tag_prompt"))
        if ok and tag.strip():
            self.set_item_tag(items, tag.strip())
    def set_item_color(self, items, color):
        for item in items:
            if item.childCount() == 0:
                entry = item.data(0, QtCore.Qt.UserRole)
                if entry:
                    shortname = entry.get("ShortName", "")
                    key = os.path.splitext(shortname)[0]
                    
                    if color is None:
                        self.marked_items.pop(key, None)
                    else:
                        if key not in self.marked_items:
                            self.marked_items[key] = {}
                        self.marked_items[key]['color'] = color
                    
                    for col in range(5):
                        item.setBackground(col, color if color else QtGui.QColor(255, 255, 255))
        
        self.settings.save()

    def set_item_tag(self, items, tag):
        for item in items:
            if item.childCount() == 0: 
                entry = item.data(0, QtCore.Qt.UserRole)
                if entry:
                    shortname = entry.get("ShortName", "")
                    key = os.path.splitext(shortname)[0]
                    if tag == "":
                        if key in self.marked_items and 'tag' in self.marked_items[key]:
                            del self.marked_items[key]['tag']
                            if not self.marked_items[key]:
                                del self.marked_items[key]
                    else:
                        if key not in self.marked_items:
                            self.marked_items[key] = {}
                        self.marked_items[key]['tag'] = tag
                    item.setText(4, tag)
        current_lang = self.get_current_language()
        if current_lang:
            self.update_filter_combo(current_lang)
            self.populate_tree(current_lang)
    def restore_audio_from_backup(self, entry, lang):
        file_id = entry.get("Id", "")
        shortname = entry.get("ShortName", "")
        
        if not self.has_backup(file_id, lang):
            QtWidgets.QMessageBox.information(
                self, "No Backup",
                f"No backup found for {shortname}"
            )
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Restore from Backup",
            f"Restore previous version of modified audio for:\n{shortname}\n\n"
            f"This will replace the current modified audio with the backup version.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            success, message = self.restore_from_backup(file_id, lang)
            
            if success:
                self.populate_tree(lang)
                self.status_bar.showMessage(f"Restored {shortname} from backup", 3000)
                QtWidgets.QMessageBox.information(
                    self, "Restored",
                    f"Successfully restored {shortname} from backup!"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Restore Failed",
                    f"Failed to restore {shortname}:\n{message}"
                )
    def quick_load_custom_audio(self, entry, lang, custom_file=None):
        if custom_file:
            audio_file = custom_file
        else:
            audio_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                "Select Audio File",
                "",
                "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus);;All Files (*.*)"
            )
        
        if not audio_file:
            return
        
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
        
        wwise_path = None
        project_path = None
        
        if hasattr(self, 'wwise_path_edit') and hasattr(self, 'converter_project_path_edit'):
            wwise_path = self.wwise_path_edit.text()
            project_path = self.converter_project_path_edit.text()
        
        if not wwise_path or not project_path:
            wwise_path = self.settings.data.get("wav_wwise_path", "")
            project_path = self.settings.data.get("wav_project_path", "")
        
        if not wwise_path or not os.path.exists(wwise_path):
            QtWidgets.QMessageBox.warning(
                self, "Configuration Required",
                "Wwise path not found or invalid.\n\n"
                "Please go to Converter tab and set valid Wwise installation path."
            )
            return
        
        if not project_path:
            QtWidgets.QMessageBox.warning(
                self, "Configuration Required",
                "Project path not set.\n\n"
                "Please go to Converter tab and set project path."
            )
            return
        
        temp_output = tempfile.mkdtemp(prefix="quick_load_")
        
        self.wav_converter.set_paths(wwise_path, project_path, temp_output)
        
        progress = ProgressDialog(self, self.tr("quick_load_audio_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        thread = threading.Thread(
            target=self._quick_load_audio_thread,
            args=(audio_file, entry, lang, progress, temp_output)
        )
        thread.daemon = True
        thread.start()
    def batch_adjust_volume(self, lang, is_mod=False):
        """Batch adjust volume for multiple files"""
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
        
        widgets = self.tab_widgets[lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        file_items = [item for item in items if item.childCount() == 0]
        
        if len(file_items) < 2:
            QtWidgets.QMessageBox.information(
                self, "Not Enough Files",
                "Please select at least 2 files for batch processing."
            )
            return
        
        entries_and_lang = []
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry:
                entries_and_lang.append((entry, lang))
        
        if not entries_and_lang:
            return
        
        dialog = BatchVolumeEditDialog(self, entries_and_lang, is_mod)
        dialog.exec_()    
    def adjust_wem_volume(self, entry, lang, is_mod=False):
        if not hasattr(self, 'wav_converter'):
            self.wav_converter = WavToWemConverter(self)
            
            if hasattr(self, 'wwise_path_edit') and hasattr(self, 'converter_project_path_edit'):
                wwise_path = self.wwise_path_edit.text()
                project_path = self.converter_project_path_edit.text()
                
                if wwise_path and project_path:
                    self.wav_converter.set_paths(wwise_path, project_path, tempfile.gettempdir())
        
        dialog = WemVolumeEditDialog(self, entry, lang, is_mod)
        dialog.exec_()
    def _quick_load_audio_thread(self, audio_file, entry, lang, progress, temp_output):
        try:
            file_id = entry.get("Id", "")
            shortname = entry.get("ShortName", "")
            original_filename = os.path.splitext(shortname)[0]
            
            audio_ext = os.path.splitext(audio_file)[1].lower()
            if audio_ext != '.wav':
                QtCore.QMetaObject.invokeMethod(
                    progress, "set_progress",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(int, 20),
                    QtCore.Q_ARG(str, "Converting to WAV...")
                )
                
                audio_converter = AudioToWavConverter()
                if not audio_converter.is_available():
                    raise Exception("FFmpeg not found. Please install FFmpeg for non-WAV file support.")
                
                temp_wav = os.path.join(temp_output, f"{original_filename}.wav")
                success, result = audio_converter.convert_to_wav(audio_file, temp_wav)
                
                if not success:
                    raise Exception(f"Audio conversion failed: {result}")
                    
                wav_file = temp_wav
                needs_cleanup = True
            else:
                wav_file = os.path.join(temp_output, f"{original_filename}.wav")
                shutil.copy2(audio_file, wav_file)
                needs_cleanup = True
            
            original_wem = os.path.join(self.wem_root, lang, f"{file_id}.wem")
            if not os.path.exists(original_wem):
                raise Exception(f"Original WEM not found: {original_wem}")
                
            target_size = os.path.getsize(original_wem)
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 50),
                QtCore.Q_ARG(str, "Converting to WEM...")
            )
            
            file_pair = {
                "wav_file": wav_file,
                "target_wem": original_wem,
                "wav_name": f"{original_filename}.wav",
                "target_name": f"{original_filename}.wem",
                "target_size": target_size,
                "language": lang,
                "file_id": file_id
            }
            
            quick_mode = self.settings.data.get("quick_load_mode", "strict")
            self.wav_converter.set_adaptive_mode(quick_mode == "adaptive")
            
            if not self.wav_converter.wwise_path:
                raise Exception("Wwise converter not properly configured")
            
            result = self.wav_converter.convert_single_file_main(file_pair, 1, 1)
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Conversion failed'))
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 80),
                QtCore.Q_ARG(str, "Deploying to MOD_P...")
            )
            
            source_wem = result['output_path']
            
            if lang != "SFX":
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media", lang
                )
            else:
                target_dir = os.path.join(
                    self.mod_p_path, "OPP", "Content", "WwiseAudio", 
                    "Windows", "Media"
                )
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, f"{file_id}.wem")
            
            if os.path.exists(target_path):
                backup_path = self.get_backup_path(file_id, lang)

                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    DEBUG.log(f"Removed old backup: {backup_path}")
                
                shutil.copy2(source_wem, backup_path)
                DEBUG.log(f"Created new backup from loaded audio: {backup_path}")
            
            shutil.copy2(source_wem, target_path)
            
            QtCore.QMetaObject.invokeMethod(
                progress, "set_progress",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(int, 100),
                QtCore.Q_ARG(str, "Complete!")
            )
            
            if needs_cleanup and os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                except:
                    pass
                    
            if os.path.exists(source_wem) and source_wem != target_path:
                try:
                    os.remove(source_wem)
                except:
                    pass
                    
            if temp_output and os.path.exists(temp_output):
                try:
                    shutil.rmtree(temp_output)
                except:
                    pass
            
            QtCore.QMetaObject.invokeMethod(
                progress, "close",
                QtCore.Qt.QueuedConnection
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "_quick_load_complete",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, lang),
                QtCore.Q_ARG(str, shortname)
            )
            
        except Exception as e:
  
            QtCore.QMetaObject.invokeMethod(
                progress, "close",
                QtCore.Qt.QueuedConnection
            )
            
            QtCore.QMetaObject.invokeMethod(
                self, "_quick_load_error",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, str(e))
            )
    @QtCore.pyqtSlot(str, str)
    def _quick_load_complete(self, lang, shortname):
        self.populate_tree(lang)
        self.status_bar.showMessage(f"Successfully imported custom audio for {shortname}", 3000)
        QtWidgets.QMessageBox.information(
            self, "Success",
            f"Custom audio imported successfully!\n\nFile: {shortname}\n\nThe mod audio is now in MOD_P"
        )

    @QtCore.pyqtSlot(str)
    def _quick_load_error(self, error):
        QtWidgets.QMessageBox.critical(
            self, "Import Error",
            f"Failed to import custom audio:\n\n{error}"
        )
    def batch_adjust_volume(self):
        """Batch adjust volume for multiple selected files"""
        current_lang = self.get_current_language()
        if not current_lang or current_lang not in self.tab_widgets:
            return
            
        widgets = self.tab_widgets[current_lang]
        tree = widgets["tree"]
        items = tree.selectedItems()
        
        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            QtWidgets.QMessageBox.information(
                self, "No Files Selected",
                "Please select audio files to adjust volume."
            )
            return
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.tr("select_version_title"))
        msg.setText("Which version would you like to adjust?")
        
        original_btn = msg.addButton("Original", QtWidgets.QMessageBox.ActionRole)
        mod_btn = msg.addButton("Mod", QtWidgets.QMessageBox.ActionRole)
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        
        msg.exec_()
        
        is_mod = False
        if msg.clickedButton() == mod_btn:
            is_mod = True
        elif msg.clickedButton() != original_btn:
            return
    def _batch_export_wav_thread(self, file_items, lang, export_mod, directory, progress):
        errors = []
        successful_count = 0
        overwrite_all = False

        for i, item in enumerate(file_items):
            entry = item.data(0, QtCore.Qt.UserRole)
            if not entry:
                continue
                
            id_ = entry.get("Id", "")
            shortname = entry.get("ShortName", "")
            
            QtCore.QMetaObject.invokeMethod(progress, "set_progress", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, int((i / len(file_items)) * 100)),
                                            QtCore.Q_ARG(str, f"Converting {shortname}..."))
            
            wem_path = None
            if export_mod:
                mod_wem_path = self.get_mod_path(id_, lang)
                if mod_wem_path and os.path.exists(mod_wem_path):
                    wem_path = mod_wem_path
                else:
                    wem_path = self.get_original_path(id_, lang)
            else:
                wem_path = self.get_original_path(id_, lang)
            
            wav_path = os.path.join(directory, shortname)
            
            if os.path.exists(wav_path) and not overwrite_all:
     
                result = QtCore.QMetaObject.invokeMethod(self, "_ask_overwrite", QtCore.Qt.BlockingQueuedConnection,
                                                         QtCore.Q_ARG(str, shortname))
                
                if result == "No":
                    errors.append(f"{shortname}: Skipped by user")
                    continue
                elif result == "No to All":
                    errors.append(f"{shortname}: Skipped by user (cancelled all)")
                    break 
                elif result == "Yes to All":
                    overwrite_all = True
            
            if wem_path and os.path.exists(wem_path):
                ok, err = self.wem_to_wav_vgmstream(wem_path, wav_path)
                if not ok:
                    errors.append(f"{shortname}: {err}")
                    QtCore.QMetaObject.invokeMethod(progress, "append_details", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, f"Failed: {shortname}"))
                else:
                    successful_count += 1
            else:
                errors.append(f"{shortname}: Source WEM file not found")

        QtCore.QMetaObject.invokeMethod(self, "_on_batch_export_finished", QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(object, progress),
                                        QtCore.Q_ARG(int, successful_count),
                                        QtCore.Q_ARG(list, errors))
    @QtCore.pyqtSlot(str, result=str)
    def _ask_overwrite(self, shortname):
        reply_box = QtWidgets.QMessageBox(self)
        reply_box.setWindowTitle("File Exists")
        reply_box.setText(f"The file '{shortname}' already exists in the destination folder.")
        reply_box.setInformativeText("Do you want to overwrite it?")
        yes_btn = reply_box.addButton("Yes", QtWidgets.QMessageBox.YesRole)
        no_btn = reply_box.addButton("No", QtWidgets.QMessageBox.NoRole)
        yes_all_btn = reply_box.addButton("Yes to All", QtWidgets.QMessageBox.YesRole)
        no_all_btn = reply_box.addButton("No to All", QtWidgets.QMessageBox.NoRole)
        
        self.show_dialog(reply_box)
        clicked = reply_box.clickedButton()

        if clicked == yes_btn: return "Yes"
        if clicked == no_btn: return "No"
        if clicked == yes_all_btn: return "Yes to All"
        if clicked == no_all_btn: return "No to All"
        return "No"
    @QtCore.pyqtSlot(result=bool)
    def _ask_convert_old_mod_structure(self):
        """Asks the user if they want to convert old mod structure to new Media/ format."""
        title = self.translations.get(self.current_lang, {}).get(
            "outdated_mod_structure_title", "Outdated Mod Structure"
        )
        
        msg = self.translations.get(self.current_lang, {}).get(
            "outdated_mod_structure_msg", 
            "The mod you are importing uses the old file structure (pre-update).\n\n"
            "The game now requires audio files to be in a 'Media' subfolder.\n"
            "Do you want to automatically reorganize the files to the new format?"
        )

        reply = QtWidgets.QMessageBox.question(
            self,
            title,
            msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return reply == QtWidgets.QMessageBox.Yes
    @QtCore.pyqtSlot(object, int, list)
    def _on_batch_export_finished(self, progress, successful_count, errors):
        progress.close()
        
        self.show_message_box(
            QtWidgets.QMessageBox.Information,
            self.tr("export_complete"),
            self.tr("export_results").format(
                successful=successful_count,
                errors=len(errors)
            ),
            informative_text="\n".join(errors) if errors else ""
        )
        
        if successful_count > 0:
            self.status_bar.showMessage(f"Exported {successful_count} files successfully", 3000)
    def batch_export_wav(self, items, lang):
        file_items = [item for item in items if item.childCount() == 0]
        
        if not file_items:
            return
            
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(self.tr("batch_export"))
        msg.setText(self.tr("which_version_export") + f"\n\n({len(file_items)} files selected)")
        
        original_btn = msg.addButton(self.tr("original"), QtWidgets.QMessageBox.ActionRole)
        mod_btn = msg.addButton(self.tr("mod"), QtWidgets.QMessageBox.ActionRole)
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        
        has_any_mod = False
        for item in file_items:
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry:
                mod_path = self.get_mod_path(entry.get("Id", ""), lang)
                if mod_path and os.path.exists(mod_path):
                    has_any_mod = True
                    break
        
        if not has_any_mod:
            mod_btn.setEnabled(False)
            mod_btn.setToolTip("No modified audio files found in selection.")
        
        self.show_dialog(msg)
        
        clicked_button = msg.clickedButton()
        export_mod = False
        
        if clicked_button == original_btn:
            export_mod = False
        elif clicked_button == mod_btn:
            export_mod = True
        else:
            return
            
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("select_output_directory"))
        if not directory:
            return
            
        progress = ProgressDialog(self, self.tr("exporting_files").format(count=len(file_items)))
        progress.show()
        progress.raise_()
        progress.activateWindow()

        thread = threading.Thread(target=self._batch_export_wav_thread, args=(file_items, lang, export_mod, directory, progress))
        thread.daemon = True
        thread.start()

    def on_global_search(self, text):
        self.search_timer.start()
    def perform_delayed_search(self):
        current_lang = self.get_current_language()
        if current_lang and current_lang in self.tab_widgets:
            self.populate_tree(current_lang)    

    def on_tab_changed(self, index):

        if index >= len(self.tab_widgets):
            return
            
        lang = self.get_current_language()
        if lang and lang in self.tab_widgets: 
            self.update_filter_combo(lang)
            if lang not in self.populated_tabs:
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
        QMainWindow, QDialog, QWidget {
            background-color: #2b2b2b;
            color: #d4d4d4;
            border: none;
        }

        QMenuBar {
            background-color: #3c3f41;
            border-bottom: 1px solid #4a4d4f;
        }
        QMenuBar::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #4a4d4f;
        }
        QMenu::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }

        QToolBar {
            background-color: #3c3f41;
            spacing: 3px;
            padding: 3px;
        }
        QToolButton {
            background-color: transparent;
            padding: 4px;
            border-radius: 3px;
        }
        QToolButton:hover {
            background-color: #4a4d4f;
        }
        QToolButton:pressed, QToolButton:checked {
            background-color: #007acc;
        }

        QTabWidget::pane {
            border-top: 1px solid #4a4d4f;
        }
        QTabBar {
            qproperty-drawBase: 0;
            border: 0;
        }
        QTabBar::tab {
            background-color: #3c3f41;
            color: #d4d4d4;
            padding: 6px 12px;
            margin-right: 1px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:hover {
            background-color: #4a4d4f;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b; 
            border-bottom: 2px solid #007acc;
        }

        QTreeWidget, QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #3c3f41; 
            border: 1px solid #4a4d4f;
            selection-background-color: #007acc; 
            selection-color: #ffffff; 
            gridline-color: #4a4d4f; 
        }
        QTreeWidget::item:hover, QTableWidget::item:hover {
            background-color: #45494a;
        }
        QHeaderView::section {
            background-color: #3c3f41;
            color: #d4d4d4;
            border: none;
            border-right: 1px solid #4a4d4f;
            border-bottom: 1px solid #4a4d4f;
            padding: 4px;
        }

        QPushButton {
            background-color: #4a4d4f;
            color: #d4d4d4;
            border: 1px solid #5a5d5f;
            padding: 5px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #5a5d5f;
            border-color: #6a6d6f;
        }
        QPushButton:pressed {
            background-color: #3c3f41;
        }
        QPushButton[primary="true"], QPushButton:default {
            background-color: #007acc;
            color: white;
            border: 1px solid #007acc;
        }
        QPushButton[primary="true"]:hover {
            background-color: #1185cf;
        }
        QLabel {
            background-color: transparent;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #3c3f41;
            border: 1px solid #4a4d4f;
            padding: 4px;
            border-radius: 4px;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #007acc;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: url(./path/to/your/dark-arrow.png); 
        }

        QGroupBox {
            border: 1px solid #4a4d4f;
            margin-top: 8px;
            padding: 8px;
            border-radius: 4px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding-left: 5px;
            padding-right: 5px;
        }

        QProgressBar {
            background-color: #3c3f41;
            border: 1px solid #4a4d4f;
            border-radius: 4px;
            text-align: center;
            color: #d4d4d4;
        }
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 4px;
        }
        QStatusBar {
            background-color: #007acc;
            color: white;
        }
        QSplitter::handle {
            background: #3c3f41;
        }
        QScrollBar:vertical {
            border: none;
            background: #2b2b2b;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #4a4d4f;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #2b2b2b;
            height: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: #4a4d4f;
            min-width: 20px;
            border-radius: 5px;
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
        
        self.progress_dialog = ProgressDialog(self, self.tr("compiling_mod"))
        self.progress_dialog.progress.setRange(0, 0)
        self.progress_dialog.details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {self.tr('running_repak')}")

        self.animation_timer = QtCore.QTimer()

        self.animation_texts = [
            self.tr("compiling_step_1"),
            self.tr("compiling_step_2"),
            self.tr("compiling_step_3"),
            self.tr("compiling_step_4"),
            self.tr("compiling_step_5"),
            self.tr("compiling_step_6"),
            self.tr("compiling_step_7"),
        ]

        import random
        random.shuffle(self.animation_texts) 
        self.animation_index = 0

        def update_animation():
            if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():

                current_text = self.animation_texts[self.animation_index]
                self.progress_dialog.label.setText(current_text)

                self.progress_dialog.details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {current_text}")

                self.animation_index = (self.animation_index + 1) % len(self.animation_texts)
            else:
                self.animation_timer.stop() 
                
        self.animation_timer.timeout.connect(update_animation)

        self.animation_timer.start(2500) 
        self.progress_dialog.label.setText(self.tr("running_repak"))


        self.progress_dialog.show()

        opp_path = os.path.join(self.mod_p_path, "OPP")
        os.makedirs(opp_path, exist_ok=True)
        watermark_path = os.path.join(opp_path, "CreatedByAudioEditor.txt")
        watermark_content = f"This mod was created using OutlastTrials AudioEditor {current_version}\nCreated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            with open(watermark_path, 'w', encoding='utf-8') as f:
                f.write(watermark_content)
        except Exception:
            pass
        
        self.compile_thread = CompileModThread(self.repak_path, self.mod_p_path)

        self.compile_thread.finished.connect(self.on_compilation_finished)
        self.compile_thread.start()

    def on_compilation_finished(self, success, output):

        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        watermark_path = os.path.join(self.mod_p_path, "OPP", "CreatedByAudioEditor.txt")
        if os.path.exists(watermark_path):
            try:
                os.remove(watermark_path)
            except Exception:
                pass
                
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if success:
            QtWidgets.QMessageBox.information(
                self, 
                self.tr("success"), 
                self.tr("mod_compiled_successfully")
            )
            DEBUG.log(f"Mod compilation successful:\n{output}")
        else:
            error_msg = QtWidgets.QMessageBox(self)
            error_msg.setIcon(QtWidgets.QMessageBox.Warning)
            error_msg.setWindowTitle(self.tr("error"))
            error_msg.setText(self.tr("compilation_failed"))
            error_msg.setInformativeText("See details for the output from repak.exe.")
            error_msg.setDetailedText(output)
            error_msg.exec_()
            DEBUG.log(f"Mod compilation failed:\n{output}", "ERROR")
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
        voice_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", "English(US)")
        sfx_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
        loc_dir = os.path.join(self.mod_p_path, "OPP", "Content", "Localization")
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("select_folder_to_open_title"))
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        label = QtWidgets.QLabel(self.tr("which_folder_to_open"))
        layout.addWidget(label)
        
        btn_layout = QtWidgets.QVBoxLayout()
        
        if os.path.exists(voice_dir):
            voice_btn = QtWidgets.QPushButton(self.tr("voice_files_folder").format(path=voice_dir))
            voice_btn.clicked.connect(lambda: (os.startfile(voice_dir), dialog.accept()))
            btn_layout.addWidget(voice_btn)
        
        if os.path.exists(sfx_dir) and sfx_dir != voice_dir:
            sfx_btn = QtWidgets.QPushButton(self.tr("sfx_files_folder").format(path=sfx_dir))
            sfx_btn.clicked.connect(lambda: (os.startfile(sfx_dir), dialog.accept()))
            btn_layout.addWidget(sfx_btn)
        
        if os.path.exists(loc_dir):
            loc_btn = QtWidgets.QPushButton(self.tr("subtitles_folder").format(path=loc_dir))
            loc_btn.clicked.connect(lambda: (os.startfile(loc_dir), dialog.accept()))
            btn_layout.addWidget(loc_btn)
        
        layout.addLayout(btn_layout)
        
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        if not any(os.path.exists(d) for d in [voice_dir, sfx_dir, loc_dir]):
            QtWidgets.QMessageBox.warning(self, self.tr("error"), self.tr("no_target_folders_found"))
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
        mode_group.setMinimumWidth(240)
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
        self.wwise_path_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_wwise_path": self.wwise_path_edit.text()}))
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
        self.converter_project_path_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_project_path": self.converter_project_path_edit.text()}))
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
        self.wav_folder_edit.editingFinished.connect(lambda: self.settings.data.update({"wav_folder_path": self.wav_folder_edit.text()})) 
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
        add_all_wav_btn.clicked.connect(self.add_all_audio_files_auto)
        
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
        
        self.convert_btn.clicked.connect(self.toggle_conversion)
        
        self.is_converting = False
        self.conversion_thread = None
        
        self.files_count_label = QtWidgets.QLabel(self.tr("files_ready_count").format(count=0))
        self.files_count_label.setStyleSheet("font-weight: bold; color: #666;")
        
        controls_layout.addWidget(add_all_wav_btn)
        add_single_file_btn = QtWidgets.QPushButton(self.tr("add_file_btn"))
        add_single_file_btn.clicked.connect(self.add_single_audio_file)
        
        controls_layout.addWidget(add_all_wav_btn)
        controls_layout.addWidget(add_single_file_btn) 
        controls_layout.addWidget(clear_files_btn)
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
        self.conversion_files_table.setAcceptDrops(True)
        self.conversion_files_table.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.conversion_files_table.viewport().setAcceptDrops(True)

        self.conversion_files_table.dragEnterEvent = self.table_dragEnterEvent
        self.conversion_files_table.dragMoveEvent = self.table_dragMoveEvent
        self.conversion_files_table.dropEvent = self.table_dropEvent
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
    def table_dragEnterEvent(self, event):
        """Handle drag enter event for conversion table"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def table_dragMoveEvent(self, event):
        """Handle drag move event for conversion table"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_single_audio_file(self):
        if hasattr(self, 'add_single_thread') and self.add_single_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "In Progress", "Already processing a file. Please wait.")
            return
            
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            self.settings.data.get("last_audio_dir", ""),
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.opus *.webm);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        self.settings.data["last_audio_dir"] = os.path.dirname(file_path)
        self.settings.save()
        
        progress = ProgressDialog(self, self.tr("add_single_file_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        self.add_single_thread = AddSingleFileThread(self, file_path)
        self.add_single_thread.progress_updated.connect(progress.set_progress)
        self.add_single_thread.details_updated.connect(progress.append_details)
        self.add_single_thread.finished.connect(lambda success: self.on_add_single_finished(progress, success, file_path))
        self.add_single_thread.error_occurred.connect(lambda e: self.on_add_single_error(progress, e))
        
        self.add_single_thread.start()
    def on_add_single_finished(self, progress, success, file_path):
        progress.close()
        
        self.update_conversion_files_table()
        
        filename = os.path.basename(file_path)
        
        if success:
            self.status_bar.showMessage(f"Added: {filename}", 3000)
            self.append_conversion_log(f"✓ Added {filename}")
        else:
            self.status_bar.showMessage(f"File not added: {filename}", 3000)
            self.append_conversion_log(f"✗ Not added: {filename}")

    def on_add_single_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error adding file:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")
    def find_matching_wem_for_audio(self, audio_path, auto_mode=False, replace_all=False, skip_all=False):
        """Find matching WEM for audio file and add to conversion list"""
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        audio_ext = os.path.splitext(audio_path)[1].lower()
        
        selected_language = self.settings.data.get("wem_process_language", "english")
        DEBUG.log(f"Using language from settings: {selected_language}")
        
        if selected_language == "english":
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        elif selected_language == "french":
            target_dir_voice = "Francais"
            voice_lang_filter = ["French(France)", "Francais"]
        else:
            target_dir_voice = "English(US)"
            voice_lang_filter = ["English(US)"]
        
        existing_file_index = None

        file_pairs_copy = list(self.wav_converter.file_pairs)
        for i, pair in enumerate(file_pairs_copy):
            if pair.get('audio_file') == audio_path:
                existing_file_index = i
                break
        
        if existing_file_index is not None:
            if skip_all:
                self.append_conversion_log(f"✗ Skipped {os.path.basename(audio_path)}: Already in list")
                return False
            
            if replace_all:
                self.append_conversion_log(f"ℹ {os.path.basename(audio_path)}: Already in list (no changes)")
                return False
            
            response = QtCore.QMetaObject.invokeMethod(
                self, "_ask_for_update", QtCore.Qt.BlockingQueuedConnection,
                QtCore.Q_ARG(str, os.path.basename(audio_path))
            )

            if response == "Skip":
                self.append_conversion_log(f"✗ Skipped {os.path.basename(audio_path)}: Already in list")
                return False

        self._build_wem_index()
        
        found_entry = None
        file_id = None
        
        if audio_name.isdigit():
            file_id = audio_name

            if file_id in self.wem_index:

                for entry in self.all_files:
                    if entry.get("Id", "") == file_id:
                        found_entry = entry
                        break
                
                if not found_entry and file_id in self.wem_index:

                    available_langs = list(self.wem_index[file_id].keys())
                    language = available_langs[0] if available_langs else "SFX"
                    
                    found_entry = {
                        "Id": file_id,
                        "Language": language,
                        "ShortName": f"{file_id}.wav" 
                    }
            else:
                self.append_conversion_log(f"✗ {audio_name}: ID not found in WEM files")
                return None
        else:

            if audio_name.startswith("VO_"):
                for entry in self.all_files:
                    shortname = entry.get("ShortName", "")
                    base_shortname = os.path.splitext(shortname)[0]
                    language = entry.get("Language", "")
                    
                    if base_shortname == audio_name and language in voice_lang_filter:
                        found_entry = entry
                        file_id = entry.get("Id", "")
                        break
                
                if not found_entry and '_' in audio_name:
                    parts = audio_name.split('_')
                    if len(parts) > 1 and len(parts[-1]) == 8:
                        try:
                            int(parts[-1], 16)
                            audio_name_no_hex = '_'.join(parts[:-1])
                            for entry in self.all_files:
                                shortname = entry.get("ShortName", "")
                                base_shortname = os.path.splitext(shortname)[0]
                                language = entry.get("Language", "")
                                
                                if base_shortname == audio_name_no_hex and language in voice_lang_filter:
                                    found_entry = entry
                                    file_id = entry.get("Id", "")
                                    break
                        except ValueError:
                            pass
                
                if not found_entry:
                    self.append_conversion_log(f"✗ {audio_name}: Not found in SoundbanksInfo for language {selected_language}")
                    return None
            else:
 
                for entry in self.all_files:
                    shortname = entry.get("ShortName", "")
                    base_shortname = os.path.splitext(shortname)[0]
                    language = entry.get("Language", "")
                    
                    if base_shortname == audio_name and language == "SFX":
                        found_entry = entry
                        file_id = entry.get("Id", "")
                        break
                
                if not found_entry:
                    self.append_conversion_log(f"✗ {audio_name}: Not found in SoundbanksInfo (SFX)")
                    return None
        
        if not found_entry or not file_id:
            self.append_conversion_log(f"✗ {audio_name}: Not found in database")
            return None
        
        if file_id not in self.wem_index:
            self.append_conversion_log(f"✗ {audio_name}: WEM file for ID {file_id} not found in Wems folder")
            return None
        language_from_db = found_entry.get("Language", "SFX")
        if language_from_db in voice_lang_filter:
            language = target_dir_voice
            if target_dir_voice in self.wem_index[file_id]:
                wem_path = self.wem_index[file_id][target_dir_voice]['path']
            else:
                available_langs = list(self.wem_index[file_id].keys())
                self.append_conversion_log(f"✗ {audio_name}: WEM for voice file not found in {target_dir_voice} (available: {', '.join(available_langs)})")
                return None
        else:
            language = "SFX"
            if "SFX" in self.wem_index[file_id]:
                wem_path = self.wem_index[file_id]["SFX"]['path']
            else:
                available_langs = list(self.wem_index[file_id].keys())
                if available_langs:
                    self.append_conversion_log(f"⚠ {audio_name}: WEM for SFX not found in SFX folder, using backup from '{available_langs[0]}'")
                else:
                    self.append_conversion_log(f"✗ {audio_name}: WEM for SFX file not found in any folder")
                    return None
        
        if not wem_path or not os.path.exists(wem_path):
            self.append_conversion_log(f"✗ {audio_name}: WEM file path not valid")
            return None
        
        existing_pair_index = None
        file_pairs_copy = list(self.wav_converter.file_pairs)
        for i, pair in enumerate(file_pairs_copy):
            if pair.get('target_wem') == wem_path and i != existing_file_index:
                existing_pair_index = i
                break
        
        if existing_pair_index is not None:
            existing_pair = self.wav_converter.file_pairs[existing_pair_index]
            
            if skip_all:
                self.append_conversion_log(
                    f"✗ Skipped {os.path.basename(audio_path)}: "
                    f"Target WEM already used by {existing_pair['audio_name']}"
                )
                return False
            
            if replace_all:
                self.wav_converter.file_pairs[existing_pair_index] = {
                    "audio_file": audio_path,
                    "original_format": audio_ext,
                    "needs_conversion": audio_ext != '.wav',
                    "target_wem": wem_path,
                    "audio_name": os.path.basename(audio_path),
                    "wav_name": os.path.basename(audio_path),
                    "target_name": f"{file_id}.wem",
                    "target_size": os.path.getsize(wem_path),
                    "language": language,
                    "file_id": file_id
                }
                if existing_file_index is not None and existing_file_index != existing_pair_index:
                    del self.wav_converter.file_pairs[existing_file_index]
                self.append_conversion_log(
                    f"✓ Replaced {existing_pair['audio_name']} with {os.path.basename(audio_path)} -> {file_id}.wem"
                )
                return True
            
            response = QtCore.QMetaObject.invokeMethod(
                self, "_ask_for_replace", QtCore.Qt.BlockingQueuedConnection,
                QtCore.Q_ARG(str, file_id),
                QtCore.Q_ARG(str, existing_pair['audio_name']),
                QtCore.Q_ARG(str, os.path.basename(audio_path)),
                QtCore.Q_ARG(bool, auto_mode)
            )

            if response == "Replace":
                self.wav_converter.file_pairs[existing_pair_index] = {
                    "audio_file": audio_path,
                    "original_format": audio_ext,
                    "needs_conversion": audio_ext != '.wav',
                    "target_wem": wem_path,
                    "audio_name": os.path.basename(audio_path),
                    "wav_name": os.path.basename(audio_path),
                    "target_name": f"{file_id}.wem",
                    "target_size": os.path.getsize(wem_path),
                    "language": language,
                    "file_id": file_id
                }
                if existing_file_index is not None and existing_file_index != existing_pair_index:
                    del self.wav_converter.file_pairs[existing_file_index]
                self.append_conversion_log(
                    f"✓ Replaced {existing_pair['audio_name']} with {os.path.basename(audio_path)} -> {file_id}.wem"
                )
                return True
            elif response == "Replace All":
                return 'replace_all'
            elif response == "Skip All":
                return 'skip_all'
            else:  # Skip
                self.append_conversion_log(
                    f"✗ Skipped {os.path.basename(audio_path)}: User chose to keep {existing_pair['audio_name']}"
                )
                return False
        
        new_file_pair = {
            "audio_file": audio_path,
            "original_format": audio_ext,
            "needs_conversion": audio_ext != '.wav',
            "target_wem": wem_path,
            "audio_name": os.path.basename(audio_path),
            "wav_name": os.path.basename(audio_path),
            "target_name": f"{file_id}.wem",
            "target_size": os.path.getsize(wem_path),
            "language": language,
            "file_id": file_id
        }

        if existing_file_index is not None:
            self.wav_converter.file_pairs[existing_file_index] = new_file_pair
            self.append_conversion_log(f"✓ Updated {os.path.basename(audio_path)} -> {file_id}.wem ({language})")
        else:
            self.wav_converter.file_pairs.append(new_file_pair)
            self.append_conversion_log(f"✓ Added {os.path.basename(audio_path)} -> {file_id}.wem ({language})")
        
        return True    
    def toggle_conversion(self):
        """Toggle between start and stop conversion"""
        self.settings.save()
        if not self.is_converting:
            self.start_wav_conversion()
        else:
            self.stop_wav_conversion()
    def load_converter_file_list(self):
        path = os.path.join(self.base_path, "converter_file_list.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_list = json.load(f)
            self.wav_converter.file_pairs.clear()
            for pair in file_list:

                audio_name = pair.get("audio_name") or pair.get("wav_name") or pair.get("target_name") or ""
                wav_name = pair.get("wav_name") or pair.get("audio_name") or pair.get("target_name") or ""
                new_pair = dict(pair)
                new_pair["audio_name"] = audio_name
                new_pair["wav_name"] = wav_name

                if new_pair.get("audio_file") and new_pair.get("target_wem"):
                    self.wav_converter.file_pairs.append(new_pair)
            self.update_conversion_files_table()
        except Exception as e:
            DEBUG.log(f"Failed to load converter file list: {e}", "ERROR")
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
        
        selected_rows = set()
        for selected_item in self.conversion_files_table.selectedItems():
            selected_rows.add(selected_item.row())
        
        menu = QtWidgets.QMenu()

        if len(selected_rows) == 1:
            row = item.row()
            if row >= 0 and row < len(self.wav_converter.file_pairs):
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
        
        if len(selected_rows) > 1:
            remove_action = menu.addAction(f"❌ Remove {len(selected_rows)} Files")
        else:
            remove_action = menu.addAction("❌ Remove")
        
        remove_action.triggered.connect(lambda: self.remove_conversion_file())
        
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

    def remove_conversion_file(self, row=None):
        """Remove file(s) from conversion list"""
        if row is None:
            selected_rows = set()
            for item in self.conversion_files_table.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                return
            
            selected_rows = sorted(selected_rows, reverse=True)
            
            if len(selected_rows) > 1:
                reply = QtWidgets.QMessageBox.question(
                    self, "Confirm Removal",
                    f"Remove {len(selected_rows)} selected files?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return
            
            removed_names = []
            for row_idx in selected_rows:
                if row_idx < len(self.wav_converter.file_pairs):
                    removed_names.append(self.wav_converter.file_pairs[row_idx]['audio_name'])
                    del self.wav_converter.file_pairs[row_idx]
            
            self.update_conversion_files_table()
            
            if len(removed_names) == 1:
                self.append_conversion_log(f"Removed {removed_names[0]} from conversion list")
            else:
                self.append_conversion_log(f"Removed {len(removed_names)} files from conversion list")
                
        else:
            if row < 0 or row >= len(self.wav_converter.file_pairs):
                return
            
            file_pair = self.wav_converter.file_pairs[row]
            wav_name = file_pair['audio_name']
            
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

    def append_conversion_log(self, message, level="INFO"):
        self.log_signal.emit(message, level)
    @QtCore.pyqtSlot(str, str)
    def append_to_log_widget(self, message, level):

        if hasattr(self, 'conversion_logs'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}"
            color_map = {
                "INFO": "#d4d4d4" if self.settings.data["theme"] == "dark" else "#1e1e1e",
                "WARNING": "#FFC107",
                "ERROR": "#F44336",
                "SUCCESS": "#4CAF50"
            }
            color = color_map.get(level.upper(), color_map["INFO"])
            html_entry = f"<span style='color:{color};'>{log_entry}</span>"
            self.conversion_logs.append(html_entry)
            scrollbar = self.conversion_logs.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    @QtCore.pyqtSlot(str, result=str)
    def _ask_for_update(self, filename):

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("File Already Added")
        msg.setText(f"File '{filename}' is already in the conversion list.\n\nDo you want to update its settings?")
        update_btn = msg.addButton("Update", QtWidgets.QMessageBox.YesRole)
        skip_btn = msg.addButton("Skip", QtWidgets.QMessageBox.NoRole)
        msg.setDefaultButton(skip_btn)
        self.show_dialog(msg)
        return "Update" if msg.clickedButton() == update_btn else "Skip"

    @QtCore.pyqtSlot(str, str, str, bool, result=str)
    def _ask_for_replace(self, file_id, existing_name, new_name, auto_mode):

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Duplicate Target WEM")
        msg.setText(f"Target WEM '{file_id}.wem' is already assigned to:\n\nCurrent: {existing_name}\nNew: {new_name}\n\nDo you want to replace it?")
        replace_btn = msg.addButton("Replace", QtWidgets.QMessageBox.YesRole)
        skip_btn = msg.addButton("Skip", QtWidgets.QMessageBox.NoRole)
        if auto_mode:
            msg.addButton("Replace All", QtWidgets.QMessageBox.YesRole)
            msg.addButton("Skip All", QtWidgets.QMessageBox.NoRole)
        msg.setDefaultButton(skip_btn)
        self.show_dialog(msg)
        return msg.clickedButton().text()
    def add_all_audio_files_auto(self):
        if hasattr(self, 'add_files_thread') and self.add_files_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "In Progress", "A file search is already in progress. Please wait.")
            return

        audio_folder = self.wav_folder_edit.text()

        if not audio_folder or not os.path.exists(audio_folder):
            QtWidgets.QMessageBox.warning(
                self, self.tr("error"), 
                "Please select folder with audio files"
            )
            return
        self.settings.save()
        progress = ProgressDialog(self, "Adding Files")
        progress.show()
        
        self.add_files_thread = AddFilesThread(self, audio_folder)
        self.add_files_thread.progress_updated.connect(progress.set_progress)
        self.add_files_thread.details_updated.connect(progress.append_details)
        self.add_files_thread.finished.connect(lambda a, r, s, n: self.on_add_files_finished(progress, a, r, s, n))
        self.add_files_thread.error_occurred.connect(lambda e: self.on_add_files_error(progress, e))
        
        self.add_files_thread.start()

    def table_dropEvent(self, event):

        if not event.mimeData().hasUrls():
            event.ignore()
            return
        
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                file_paths.append(file_path)
        
        if not file_paths:
            event.ignore()
            return
        
        progress = ProgressDialog(self, self.tr("drop_audio_title"))
        progress.setWindowFlags(progress.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        progress.setWindowFlags(progress.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        progress.show()
        
        self.drop_files_thread = DropFilesThread(self, file_paths)
        self.drop_files_thread.progress_updated.connect(progress.set_progress)
        self.drop_files_thread.details_updated.connect(progress.append_details)
        self.drop_files_thread.finished.connect(lambda a, r, s, n: self.on_drop_files_finished(progress, a, r, s, n))
        self.drop_files_thread.error_occurred.connect(lambda e: self.on_drop_files_error(progress, e))
        
        self.drop_files_thread.start()
        
        event.acceptProposedAction()

    def on_drop_files_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error during file drop:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")    
    def save_converter_file_list(self):
        file_list = []
        for pair in self.wav_converter.file_pairs:
            audio_name = pair.get("audio_name") or pair.get("wav_name") or pair.get("target_name") or ""
            wav_name = pair.get("wav_name") or pair.get("audio_name") or pair.get("target_name") or ""
            file_list.append({
                "audio_file": pair.get("audio_file") or pair.get("wav_file"),
                "target_wem": pair.get("target_wem"),
                "audio_name": audio_name,
                "wav_name": wav_name,
                "target_name": pair.get("target_name"),
                "target_size": pair.get("target_size"),
                "language": pair.get("language"),
                "file_id": pair.get("file_id")
            })
        try:
            with open(os.path.join(self.base_path, "converter_file_list.json"), "w", encoding="utf-8") as f:
                json.dump(file_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            DEBUG.log(f"Failed to save converter file list: {e}", "ERROR")  
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
            audio_name = pair.get('audio_name') or pair.get('wav_name', 'Unknown')
            audio_file = pair.get('audio_file') or pair.get('wav_file', '')
            
            format_info = ""
            if pair.get('original_format') and pair['original_format'] != '.wav':
                format_info = f" [{pair['original_format']}]"
            
            audio_item = QtWidgets.QTableWidgetItem(audio_name + format_info)
            audio_item.setFlags(audio_item.flags() & ~QtCore.Qt.ItemIsEditable)
            audio_item.setToolTip(f"Path: {audio_file}")
            
            if pair.get('needs_conversion', False):
                audio_item.setBackground(QtGui.QColor(255, 245, 220))
            
            self.conversion_files_table.setItem(i, 0, audio_item)
            
            wem_display = f"{pair['file_id']}.wem"
            wem_item = QtWidgets.QTableWidgetItem(wem_display)
            wem_item.setFlags(wem_item.flags() & ~QtCore.Qt.ItemIsEditable)
            wem_item.setToolTip(f"Source: {pair['target_wem']}")
            self.conversion_files_table.setItem(i, 1, wem_item)

            lang_item = QtWidgets.QTableWidgetItem(pair['language'])
            lang_item.setFlags(lang_item.flags() & ~QtCore.Qt.ItemIsEditable)
            
            if self.settings.data["theme"] == "dark":
                if pair['language'] == 'English(US)':
                    lang_item.setBackground(QtGui.QColor(30, 60, 30)) 
                elif pair['language'] == 'Francais':
                    lang_item.setBackground(QtGui.QColor(30, 30, 60))
            else:
                if pair['language'] == 'English(US)':
                    lang_item.setBackground(QtGui.QColor(230, 255, 230)) 
                elif pair['language'] == 'Francais':
                    lang_item.setBackground(QtGui.QColor(230, 230, 255)) 
                
            self.conversion_files_table.setItem(i, 2, lang_item)
            
            size_kb = pair['target_size'] / 1024
            size_item = QtWidgets.QTableWidgetItem(f"{size_kb:.1f} KB")
            size_item.setFlags(size_item.flags() & ~QtCore.Qt.ItemIsEditable)
            size_item.setToolTip(f"Exact size: {pair['target_size']:,} bytes")
            self.conversion_files_table.setItem(i, 3, size_item)
            
            status_text = self.tr("ready")
            if pair.get('needs_conversion', False):
                status_text += " (conversion needed)"
            
            status_item = QtWidgets.QTableWidgetItem(status_text)
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
    def on_add_files_finished(self, progress, added, replaced, skipped, not_found):
        progress.close()
        
        self.update_conversion_files_table()
        
        message = f"Added {added} files"
        if replaced > 0:
            message += f"\nReplaced {replaced} files"
        if skipped > 0:
            message += f"\nSkipped {skipped} files"
        if not_found > 0:
            message += f"\n{not_found} files not found in database"
        
        self.append_conversion_log(f"\nResults:\n{message}")
        
        if skipped > 0 or not_found > 0:
            message += "\n\nDetails (see Logs tab for full report):"
            message += "\n- Skipped files: Check Logs for reasons (duplicates, user choice, etc.)"
            message += "\n- Not found: Files without matching WEM/ID in database"
        
        self.save_converter_file_list()
        QtWidgets.QMessageBox.information(self, self.tr("search_complete"), message)

    def on_drop_files_finished(self, progress, added, replaced, skipped, not_found):
        progress.close()
        
        self.update_conversion_files_table()
        
        message = f"Added {added} files"
        if replaced > 0:
            message += f"\nReplaced {replaced} files"
        if skipped > 0:
            message += f"\nSkipped {skipped} files"
        if not_found > 0:
            message += f"\n{not_found} files not found in database"
        
        self.append_conversion_log(f"\nDrop Results:\n{message}")
        
        if skipped > 0 or not_found > 0:
            message += "\n\nDetails (see Logs tab for full report):"
            message += "\n- Skipped files: Check Logs for reasons (duplicates, user choice, etc.)"
            message += "\n- Not found: Files without matching WEM/ID in database"
        
        self.save_converter_file_list()
        QtWidgets.QMessageBox.information(self, self.tr("search_complete"), message)

    def on_add_files_error(self, progress, error):
        progress.close()
        
        QtWidgets.QMessageBox.warning(
            self, "Error",
            f"Error during file addition:\n\n{error}"
        )
        
        self.append_conversion_log(f"✗ Error: {error}")
    def on_conversion_finished(self, results):
        """Handle conversion completion with logging"""
        try:
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
                    wav_name = result_item['file_pair']['audio_name']
                    
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
        finally:
            self.set_conversion_state(False)
    def auto_deploy_converted_files_by_language(self, successful_conversions):
        deployed_count = 0
        
        for conversion in successful_conversions:
            try:
                source_path = conversion['result']['output_path']
                file_pair = conversion['file_pair']
                language = file_pair['language']
                file_id = file_pair['file_id']
                
                # UPDATE: Deploy to 'Media' subfolder
                if language == "SFX":
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media")
                else:
                    target_dir = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", "Media", language)
                
                os.makedirs(target_dir, exist_ok=True)
                
                dest_filename = f"{file_id}.wem"
                dest_path = os.path.join(target_dir, dest_filename)
                
                shutil.copy2(source_path, dest_path)
                deployed_count += 1
                
                DEBUG.log(f"Deployed: {file_pair['audio_name']} -> {dest_filename} in {language} (Media folder)")
                
            except Exception as e:
                DEBUG.log(f"Error deploying {file_pair['audio_name']}: {e}", "ERROR")
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
        
        self.converter_tabs.addTab(wem_tab, self.tr("wem_processor_tab_title"))
    def show_cleanup_dialog(self, subtitle_files, localization_path):
        
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
                self, self.tr("cleanup_complete"),
                self.tr("files_deleted_successfully").format(count=deleted_count)
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, self.tr("cleanup_with_errors"),
                self.tr("files_deleted_with_errors").format(count=deleted_count, errors=error_count)
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
        
        # self.converter_tabs.addTab(tab, self.tr("localization_exporter"))
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
        
        self.process_btn = ModernButton(self.tr("process_wem_files_btn"), primary=True)
        self.process_btn.clicked.connect(self.process_wem_files)
        layout.addWidget(self.process_btn)
        
    
        self.open_target_btn = ModernButton(self.tr("open_target_folder_btn"))
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
            
            if hasattr(self, 'wav_converter'):
                project_path = self.converter_project_path_edit.text()
                if project_path:
                    self.wav_converter.set_paths(folder, project_path, self.wav_converter.output_folder or tempfile.gettempdir())

    def browse_converter_project_path(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose path for Wwise project",
            self.converter_project_path_edit.text() or ""
        )
        if folder:
            self.converter_project_path_edit.setText(folder)
            self.settings.data["wav_project_path"] = folder
            self.settings.save()
  
            if hasattr(self, 'wav_converter'):
                wwise_path = self.wwise_path_edit.text()
                if wwise_path:
                    self.wav_converter.set_paths(wwise_path, folder, self.wav_converter.output_folder or tempfile.gettempdir())

    def browse_wav_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose folder with Audio files",
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
        self.save_converter_file_list()

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
    def update_filter_combo(self, lang):
        widgets = self.tab_widgets[lang]
        filter_combo = widgets["filter_combo"]
        try:
            filter_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        current_text = filter_combo.currentText()
        filter_combo.clear()
        filter_combo.addItems([
            self.tr("all_files"), 
            self.tr("with_subtitles"), 
            self.tr("without_subtitles"), 
            self.tr("modified"),
            self.tr("modded")
        ])
        unique_tags = set()
        for entry in self.entries_by_lang.get(lang, []):
            key = os.path.splitext(entry.get("ShortName", ""))[0]
            marking = self.marked_items.get(key, {})
            tag = marking.get('tag')
            if tag:
                unique_tags.add(tag)

        if unique_tags:
            filter_combo.addItem("--- Tags ---")
            for tag in sorted(unique_tags):
                filter_combo.addItem(f"With Tag: {tag}")

        new_index = filter_combo.findText(current_text)
        if new_index >= 0:
            filter_combo.setCurrentIndex(new_index)
        else:
            filter_combo.setCurrentIndex(0)

        filter_combo.currentIndexChanged.connect(lambda: self.populate_tree(lang))
        
   
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
        show_orphans_checkbox = QtWidgets.QCheckBox(self.tr("show_scanned_files_check"))
        show_orphans_checkbox.setToolTip(self.tr("show_scanned_files_tooltip"))
        show_orphans_checkbox.setChecked(self.settings.data.get("show_orphaned_files", False))
        show_orphans_checkbox.stateChanged.connect(self.on_show_orphans_toggled)
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("filter")))
        controls_layout.addWidget(filter_combo)
        controls_layout.addWidget(QtWidgets.QLabel(self.tr("sort")))
        controls_layout.addWidget(sort_combo)
        controls_layout.addWidget(show_orphans_checkbox)
        controls_layout.addStretch()

        stats_label = QtWidgets.QLabel()
        controls_layout.addWidget(stats_label)
        
        layout.addWidget(controls)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        tree = AudioTreeWidget(wem_app=self, lang=lang)
        tree.setUniformRowHeights(True)
        tree.setAcceptDrops(True)
        tree.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        tree.viewport().setAcceptDrops(True)
        tree.setColumnCount(5) 
        tree.setHeaderLabels([self.tr("name"), self.tr("id"), self.tr("subtitle"), self.tr("status"), "Tag"])
        tree.setColumnWidth(0, 350)
        tree.setColumnWidth(1, 100)
        tree.setColumnWidth(2, 400)
        tree.setColumnWidth(3, 80)
        tree.setColumnWidth(4, 100)
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
        

        audio_progress = ClickableProgressBar()
        audio_progress.setTextVisible(False)
        audio_progress.setMaximumHeight(10)
        player_layout.addWidget(audio_progress)
        

        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        

        play_btn = QtWidgets.QPushButton("▶")
        play_btn.setMaximumWidth(40)
        play_btn.clicked.connect(lambda: self.play_current())
        audio_progress.clicked.connect(self.audio_player.set_position)
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
        subtitle_group.setMaximumHeight(150)
        subtitle_group.setMaximumWidth(800)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(80) 
        scroll_area.setMaximumHeight(150) 

        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)

        subtitle_text = QtWidgets.QTextEdit()
        subtitle_text.setReadOnly(True)
        subtitle_text.setMinimumHeight(60)
        scroll_layout.addWidget(subtitle_text)

        original_subtitle_label = QtWidgets.QLabel()
        original_subtitle_label.setWordWrap(True)
        original_subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        original_subtitle_label.hide()
        scroll_layout.addWidget(original_subtitle_label)

        scroll_layout.addStretch() 

        scroll_area.setWidget(scroll_content)
        subtitle_layout.addWidget(scroll_area)
        

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
            "source": QtWidgets.QLabel(),
            "tag": QtWidgets.QLabel()
        }

        basic_info_layout.addRow(f"{self.tr('id')}:", info_labels["id"])
        basic_info_layout.addRow(f"{self.tr('name')}:", info_labels["name"])
        basic_info_layout.addRow(f"{self.tr('path')}:", info_labels["path"])
        basic_info_layout.addRow(f"{self.tr('source')}:", info_labels["source"])
        info_layout.addWidget(basic_info_widget)


        comparison_group = QtWidgets.QGroupBox(self.tr("audio_comparison"))
        comparison_group.setMaximumHeight(220) 
        comparison_group.setMinimumHeight(220) 
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
            "channels": QtWidgets.QLabel(),
            "bnk_size": QtWidgets.QLabel(),
            "override_fx": QtWidgets.QLabel(),
            "modified_date": QtWidgets.QLabel()
        }

        original_info_layout.addRow(self.tr("duration"), original_info_labels["duration"])
        original_info_layout.addRow(self.tr("size"), original_info_labels["size"])
        original_info_layout.addRow(self.tr("sample_rate"), original_info_labels["sample_rate"])
        original_info_layout.addRow(self.tr("bitrate"), original_info_labels["bitrate"])
        original_info_layout.addRow(self.tr("channels"), original_info_labels["channels"])
        original_info_layout.addRow(self.tr("bnk_size_label"), original_info_labels["bnk_size"])
        original_info_layout.addRow(self.tr("in_game_effects_label"), original_info_labels["override_fx"])
        original_info_layout.addRow(" ", QtWidgets.QWidget())
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
            "channels": QtWidgets.QLabel(), 
            "bnk_size": QtWidgets.QPushButton("N/A"),
            "override_fx": QtWidgets.QLabel(),
            "modified_date": QtWidgets.QLabel()
        }

        modified_info_layout.addRow(f"{self.tr("duration")}", modified_info_labels["duration"])
        modified_info_layout.addRow(f"{self.tr("size")}", modified_info_labels["size"])
        modified_info_layout.addRow(f"{self.tr("sample_rate")}", modified_info_labels["sample_rate"])
        modified_info_layout.addRow(f"{self.tr("bitrate")}", modified_info_labels["bitrate"])
        modified_info_layout.addRow(f"{self.tr("channels")}", modified_info_labels["channels"])
        modified_info_layout.addRow(self.tr("bnk_size_label"), modified_info_labels["bnk_size"])
        modified_info_layout.addRow(self.tr("in_game_effects_label"), modified_info_labels["override_fx"]),
        modified_info_layout.addRow(self.tr("last_modified_label"), modified_info_labels["modified_date"])
        modified_layout.addLayout(modified_info_layout)
        bnk_size_button = modified_info_labels["bnk_size"]
        bnk_size_button.setFlat(True)
        bnk_size_button.setStyleSheet("QPushButton { text-align: left; padding: 0; color: #000; border: none; background: transparent; }")
        bnk_size_button.setCursor(QtCore.Qt.ArrowCursor)
        bnk_size_button.setEnabled(False)
     
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
            "show_orphans_checkbox": show_orphans_checkbox,
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
        basic_info_layout.addRow("Tag:", info_labels["tag"])
    def on_show_orphans_toggled(self, state):
        """Handles toggling the 'Show Scanned Files' checkbox."""
        is_checked = (state == QtCore.Qt.Checked)
        
        if self.settings.data.get("show_orphaned_files", True) == is_checked:
            return
        
        self.settings.data["show_orphaned_files"] = is_checked
        self.settings.save()
        DEBUG.log(f"Show orphaned files setting changed to: {is_checked}")

        for lang, widgets in self.tab_widgets.items():
            checkbox = widgets.get("show_orphans_checkbox")
            if checkbox:
                checkbox.blockSignals(True)
                checkbox.setChecked(is_checked)
                checkbox.blockSignals(False)

        self.rebuild_file_list_with_orphans()
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
                creationflags=CREATE_NO_WINDOW,
                encoding='utf-8',
                errors='ignore'
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
        <tr>
            <td><b>{self.tr("shortcut_play_original_action")}</b></td>
            <td>Space</td>
            <td>{self.tr("shortcut_play_original_desc")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_play_mod_action")}</b></td>
            <td>Ctrl+Space</td>
            <td>{self.tr("shortcut_play_mod_desc")}</td>
        </tr>
        <tr>
            <td><b>{self.tr("shortcut_delete_mod_action")}</b></td>
            <td>Delete</td>
            <td>{self.tr("shortcut_delete_mod_desc")}</td>
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
        cancel_btn = QtWidgets.QPushButton(self.tr("cancel"))
        
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
            <li>{self.tr("ffmpeg_tool")}</li>
        </ul>
        </div>
        """)
        about_tabs.addTab(about_content, self.tr("about"))

        credits_content = QtWidgets.QTextBrowser()
        credits_content.setHtml(f"""
        <div style="padding: 20px;">
        <h3>{self.tr("development_team")}</h3>
        <p><b>Developer:</b> Bezna</p>        
        <p>Tester/Polish Translator: Alaneg</p>
        <p>Tester/Mexican Spanish Translator: Mercedes</p>
        
        <h3>Special Thanks</h3>
        <ul>
            <li>vgmstream team - For audio conversion tools</li>
            <li>UnrealLocres developers - For localization support</li>
            <li>hypermetric - For mod packaging</li>
            <li>FFmpeg - For audio processing</li>
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
        <p>Copyright (c) 2026 OutlastTrials AudioEditor</p>
        
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
        
        title = QtWidgets.QLabel(self.tr("easter_egg_title"))
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
        cat_image_label.setText(self.tr("easter_egg_loading"))
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
        
        self.easter_egg_loader = EasterEggLoader(self)
        
        def on_config_loaded(config):
            print(f"Config loaded: {config}")
            message.setText(f"{config.get('message', self.tr('easter_egg_message'))}")
            self.easter_egg_loader.load_image(config.get('easter_egg_image', ''))
            
        def on_image_loaded(pixmap):
            print("Setting pixmap to label...")
            scaled_pixmap = pixmap.scaled(280, 280, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            cat_image_label.setPixmap(scaled_pixmap)
            cat_image_label.setText("")
            print("Pixmap set successfully!")
            
        def on_loading_failed(error):
            print(f"Loading failed: {error}")
            message.setText(f"{self.tr('easter_egg_message')}")
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

        if hasattr(self, 'updater_thread') and self.updater_thread and self.updater_thread.isRunning():
            reply = QtWidgets.QMessageBox.question(
                self, 
                self.tr("update_in_progress_title"),
                self.tr("confirm_exit_during_update_message"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                event.ignore()
                return
            else:
                self.updater_thread.cancel()
                self.updater_thread.wait(5000)
                DEBUG.log("Update process cancelled due to application exit.")
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            DEBUG.log("Auto-save timer stopped on close")
        
        self.settings.data["window_geometry"] = self.saveGeometry().toHex().data().decode()
        saved_markings = {}
        for key, data in self.marked_items.items():
            saved_data = {}
            if 'color' in data and data['color']:
                saved_data['color'] = data['color'].name()
            if 'tag' in data:
                saved_data['tag'] = data['tag']
            if saved_data:
                saved_markings[key] = saved_data
        self.settings.data["marked_items"] = saved_markings
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
        self.save_converter_file_list()        
        self.stop_audio()
        self.audio_player.stop()
        if hasattr(self, 'wav_converter'):
             self.wav_converter.stop_conversion()

        for f in getattr(self, 'temp_files_to_cleanup', []):
            try: os.remove(f)
            except: pass
        event.accept()
class EasterEggLoader(QObject):
    config_loaded = pyqtSignal(dict)    
    image_loaded = pyqtSignal(object)    
    loading_failed = pyqtSignal(str)    
    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.parent_app = parent_app
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
                    "easter_egg_image": "https://i.imgur.com/VeWWVDN.png",
                    "message": self.parent_app.tr('easter_egg_message'),
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
def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    full_error_msg = f"An unexpected error occurred:\n\n{error_details}"
    
    DEBUG.log("="*20 + " CRITICAL ERROR " + "="*20, "ERROR")
    DEBUG.log(full_error_msg, "ERROR")
    
    log_filename = f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_path, "data", log_filename)
    
    try:
        with open(log_path, 'w', encoding='utf-8') as crash_file:
            crash_file.write("=== CRASH REPORT ===\n")
            crash_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            crash_file.write(f"Version: {current_version}\n\n")
            crash_file.write(f"OS: {sys.platform}\n")
            crash_file.write("--- Error Details ---\n")
            crash_file.write(full_error_msg + "\n\n")
            crash_file.write("--- Full Session Log ---\n")
            crash_file.write(DEBUG.get_logs())
        
        final_message_for_user = f"{full_error_msg}\n\nA detailed crash log has been saved to:\n{log_path}"
    except Exception as save_error:
        final_message_for_user = f"{full_error_msg}\n\nFailed to save detailed crash log: {str(save_error)}"
    
    app = QtWidgets.QApplication.instance()
    if app:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("The application has encountered a critical error and will close.")
        msg.setInformativeText("Please report this bug with the details from the log files found in the 'data' folder.")
        msg.setDetailedText(final_message_for_user)
        
        copy_btn = msg.addButton("Copy Error to Clipboard", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == copy_btn:
            QtWidgets.QApplication.clipboard().setText(final_message_for_user)
    
    print("CRITICAL ERROR:", final_message_for_user)
    sys.exit(1)

sys.excepthook = global_exception_handler

def thread_exception_handler(args):
    global_exception_handler(args.exc_type, args.exc_value, args.exc_traceback)
threading.excepthook = thread_exception_handler
class CompileModThread(QtCore.QThread):

    finished = QtCore.pyqtSignal(bool, str) 

    def __init__(self, repak_path, mod_p_path, parent=None):
        super().__init__(parent)
        self.repak_path = repak_path
        self.mod_p_path = mod_p_path

    def run(self):
        command = [self.repak_path, "pack", "--version", "V11", "--compression", "Zlib", self.mod_p_path]
        try:
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = 0x08000000
            else:
                startupinfo = None
                creationflags = 0

            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode == 0:
                output = result.stderr if result.stderr else result.stdout
                self.finished.emit(True, output)
            else:
                self.finished.emit(False, result.stderr)
        except Exception as e:
            self.finished.emit(False, str(e))
class AddFilesThread(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(int, str) 
    details_updated = QtCore.pyqtSignal(str) 
    finished = QtCore.pyqtSignal(int, int, int, int)  
    error_occurred = QtCore.pyqtSignal(str)       
    
    def __init__(self, parent, audio_folder):
        super().__init__(parent)
        self.audio_folder = audio_folder
        self.parent = parent
        self.should_stop = False
        self.replace_all = False
        self.skip_all = False
    
    def run(self):
        try:
            audio_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.webm']
            
            audio_files = []
            for file in os.listdir(self.audio_folder):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(file)
            
            if not audio_files:
                self.finished.emit(0, 0, 0, 0)
                return
            
            self.details_updated.emit(f"Found {len(audio_files)} audio files")
            
            added_count = 0
            replaced_count = 0
            skipped_count = 0
            not_found = 0
            
            for i, audio_file in enumerate(audio_files):
                if self.should_stop:
                    break
                
                audio_path = os.path.join(self.audio_folder, audio_file)
                
                percent = int((i / len(audio_files)) * 100)
                self.progress_updated.emit(percent, f"Processing {audio_file} ({i+1}/{len(audio_files)})...")
                
                result = self.parent.find_matching_wem_for_audio(
                    audio_path, 
                    auto_mode=True, 
                    replace_all=self.replace_all, 
                    skip_all=self.skip_all
                )
                
                if result == 'replace_all':
                    self.replace_all = True
           
                    result = self.parent.find_matching_wem_for_audio(
                        audio_path, 
                        auto_mode=True, 
                        replace_all=True, 
                        skip_all=False
                    )
                elif result == 'skip_all':
                    self.skip_all = True
            
                    result = self.parent.find_matching_wem_for_audio(
                        audio_path, 
                        auto_mode=True, 
                        replace_all=False, 
                        skip_all=True
                    )
                
                if result is True:
                    if self.replace_all:
                        replaced_count += 1
                    else:
                        added_count += 1
                elif result is False:
                    skipped_count += 1
                elif result is None:
                    not_found += 1
            
            self.progress_updated.emit(100, "Complete!")
            self.finished.emit(added_count, replaced_count, skipped_count, not_found)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
class AddSingleFileThread(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(int, str) 
    details_updated = QtCore.pyqtSignal(str)   
    finished = QtCore.pyqtSignal(bool)           
    error_occurred = QtCore.pyqtSignal(str)   
    
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.file_path = file_path
        self.parent = parent
        self.should_stop = False
    
    def run(self):
        try:
            self.progress_updated.emit(0, "Processing file...")
            
            result = self.parent.find_matching_wem_for_audio(self.file_path, auto_mode=False)
            if result is True:
        
                self.details_updated.emit("File processed successfully.")
                self.progress_updated.emit(100, "Complete!")
                self.finished.emit(True)
            elif result is False:
    
                self.details_updated.emit("File was skipped (already in list or user choice).")
                self.progress_updated.emit(100, "Complete!")
                self.finished.emit(False)
            elif result is None:
      
                self.details_updated.emit("No matching WEM file found in the database.")
                self.progress_updated.emit(100, "Complete!")
                self.finished.emit(False)
            else:
        
                self.details_updated.emit(f"File processed with result: {result}")
                self.progress_updated.emit(100, "Complete!")
                self.finished.emit(True) 
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error_occurred.emit(error_details)
class DropFilesThread(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(int, str)
    details_updated = QtCore.pyqtSignal(str)     
    finished = QtCore.pyqtSignal(int, int, int, int) 
    error_occurred = QtCore.pyqtSignal(str)    
    
    def __init__(self, parent, file_paths):
        super().__init__(parent)
        self.file_paths = file_paths
        self.parent = parent
        self.should_stop = False
        self.replace_all = False
        self.skip_all = False
    
    def run(self):
        try:
            self.details_updated.emit(f"Processing {len(self.file_paths)} dropped files...")
            
            added_count = 0
            replaced_count = 0
            skipped_count = 0
            not_found = 0
            
            for i, file_path in enumerate(self.file_paths):
                if self.should_stop:
                    break
                
                percent = int((i / len(self.file_paths)) * 100)
                self.progress_updated.emit(percent, f"Processing {os.path.basename(file_path)} ({i+1}/{len(self.file_paths)})...")
                
                file_ext = os.path.splitext(file_path)[1].lower()
                supported_formats = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.webm']
                
                if file_ext not in supported_formats:
                    self.details_updated.emit(f"✗ {os.path.basename(file_path)} - unsupported format")
                    skipped_count += 1
                    continue
                
                auto_mode = len(self.file_paths) > 1  
                
                result = self.parent.find_matching_wem_for_audio(
                    file_path, 
                    auto_mode=auto_mode, 
                    replace_all=self.replace_all, 
                    skip_all=self.skip_all
                )
                
                if result == 'replace_all':
                    self.replace_all = True
                    result = self.parent.find_matching_wem_for_audio(
                        file_path, 
                        auto_mode=auto_mode, 
                        replace_all=True, 
                        skip_all=False
                    )
                elif result == 'skip_all':
                    self.skip_all = True
                    result = self.parent.find_matching_wem_for_audio(
                        file_path, 
                        auto_mode=auto_mode, 
                        replace_all=False, 
                        skip_all=True
                    )
                
                if result is True:
                    if self.replace_all:
                        replaced_count += 1
                    else:
                        added_count += 1
                elif result is False:
                    skipped_count += 1
                elif result is None:
                    not_found += 1
            
            self.progress_updated.emit(100, "Complete!")
            self.finished.emit(added_count, replaced_count, skipped_count, not_found)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
if __name__ == "__main__":
    from PyQt5.QtCore import QSharedMemory
    from PyQt5.QtWidgets import QMessageBox

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    shared_memory_key = "DAA73E5A-A93B-4264-8263-6901E788C946-OutlastTrialsAudioEditor"
    shared_memory = QSharedMemory(shared_memory_key)
    
    temp_settings = AppSettings()
    lang = temp_settings.data.get("ui_language", "en")
    temp_tr = lambda key: TRANSLATIONS.get(lang, {}).get(key, key)
    
    if not shared_memory.create(1):
        QMessageBox.warning(
            None, 
            temp_tr("app_already_running_title"), 
            temp_tr("app_already_running_msg")
        )
        sys.exit(0)

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    splash_path = os.path.join(base_path, "data", "splash.png")
    splash = None

    if os.path.exists(splash_path):
        original_pixmap = QtGui.QPixmap(splash_path)
        splash = QtWidgets.QSplashScreen(original_pixmap, QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(original_pixmap.mask())

        def show_splash_message(message_key):
            pixmap_with_text = original_pixmap.copy()
            painter = QtGui.QPainter(pixmap_with_text)
            
            font = QtGui.QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(220, 220, 220))

            rect = pixmap_with_text.rect()
            text_rect = QtCore.QRect(rect.x(), rect.y() + rect.height() - 40, rect.width(), 30)

            painter.drawText(text_rect, QtCore.Qt.AlignCenter, temp_tr(message_key))
            painter.end()
            
            splash.setPixmap(pixmap_with_text)
            app.processEvents()

        show_splash_message("splash_loading_app")
        splash.show()
        app.processEvents()
    
    try:
        if splash: show_splash_message("splash_init_ui")
        window = WemSubtitleApp()

        if splash: show_splash_message("splash_loading_profiles")
        if not window.initialize_profiles_and_ui():
            sys.exit(0)
        
        if splash:
            splash.finish(window)
        
        window.show()
        
        QtCore.QTimer.singleShot(100, window.load_orphans_from_cache_or_scan)
        
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"An unexpected error occurred:\n\n{str(e)}\n\n"
        error_msg += "Traceback:\n" + traceback.format_exc()
        
        log_filename = f"crash_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), log_filename)
        
        try:
            with open(log_path, 'w', encoding='utf-8') as log_file:
                log_file.write("=== CRASH LOG ===\n")
                log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"Version: {current_version}\n")
                log_file.write(f"OS: {sys.platform}\n")
                log_file.write(f"Python: {sys.version}\n")
                log_file.write(f"PyQt5: {QtCore.PYQT_VERSION_STR}\n\n")
                
                log_file.write("Debug Logs:\n")
                log_file.write(DEBUG.get_logs() + "\n\n")
                
                log_file.write("Error Details:\n")
                log_file.write(error_msg)

            error_msg += f"\n\nCrash log saved to: {log_path}"
        except Exception as save_error:
            error_msg += f"\n\nFailed to save crash log: {str(save_error)}"
        
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("The application has encountered an error and will close.")
        msg.setInformativeText("Please report this bug with the details below.")
        msg.setDetailedText(error_msg)
        
        copy_btn = msg.addButton("Copy Error to Clipboard", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == copy_btn:
            QtWidgets.QApplication.clipboard().setText(error_msg)
            print("Error copied to clipboard")
        
        if 'DEBUG' in globals():
            DEBUG.log(f"Critical error: {str(e)}\n{traceback.format_exc()}", "ERROR")
        
        sys.exit(1) 
