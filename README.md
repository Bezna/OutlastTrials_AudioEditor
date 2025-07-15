# 🎮 OutlastTrials AudioEditor

<div align="center">
  
  ![Logo](https://img.shields.io/badge/Outlast_Trials-Audio_Editor-red?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEISURBVCiRY/z//z8DOmBhYGBgYGBgYPj//z8jAwMDw79//xhQBZmQBf79+8fw9+9fhj9//jAwMjIyMDMzM7CwsDBgBf/+/WP48+cPw+/fvxkYGRkZWFhYGNjY2BhYWVkZGBkZGbACIHD//n2GP3/+MDAzMzNwcnIysLOzM7CxsTEgW4UMfv/+zfDnzx8GJiYmBnZ2dgZ2dnYGdnZ2BmZmZgZGRkYGBgYGBkYmJiYGBgYGBmZmZgZWVlYGdnZ2BnZ2dgY2NjYGZmZmBqx++vfvH8Pfv38Zfv/+zcDExMTAysrKwMrKysDCwsKA1U+g6kDVgqoHVQ+qHhQAKH4EqQ5ULah6UPUgAAAAM7lEU7XYVysAAAAASUVORK5CYII=)
  
  **Professional Audio & Subtitle Editor for Outlast Trials**
  
  [![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/yourusername/OutlastTrials_AudioEditor/releases)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/downloads/)
  [![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange.svg)](https://pypi.org/project/PyQt5/)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/yourusername/OutlastTrials_AudioEditor/releases)
  
  [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

**OutlastTrials AudioEditor** is a powerful, user-friendly tool designed specifically for modding audio files and subtitles in Outlast Trials. Built with Python and PyQt5, it provides a comprehensive solution for content creators, modders, and localization teams.

<div align="center">
  <img src="https://imgur.com/8RmFUpx" alt="Screenshot" width="800">
</div>

## ✨ Features

### 🎵 Audio Management
- **WEM File Support** - Native support for Wwise audio files
- **Audio Playback** - Built-in player with timeline and controls
- **Batch Processing** - Convert multiple files at once
- **Duration Analysis** - Compare original vs modified audio lengths
- **Format Conversion** - Convert WEM to WAV and back

### 📝 Subtitle Editing
- **Multi-language Support** - 14+ languages including EN, RU, FR, DE, ES, JP, KR, CN
- **Real-time Preview** - See subtitles while playing audio

### 🛠️ Modding Tools
- **One-Click Compilation** - Build game-ready .pak files
- **Auto-deployment** - Deploy mods directly to game folder
- **Debug Console** - Built-in debugging for troubleshooting

### 🎨 Modern Interface
- **Dark/Light Themes** - Choose your preferred appearance
- **Multi-language UI** - Interface in English and Russian

## 🚀 Installation

### Option 1: Portable Version (Recommended)
1. Download the latest release from [Releases](https://github.com/Bezna/OutlastTrials_AudioEditer/releases)
2. Extract the ZIP file to any location
3. Run `OutlastTrials_AudioEditor.exe`

### Option 2: From Source
```bash
# Clone the repository
git clone https://github.com/yourusername/OutlastTrials_AudioEditor.git
cd OutlastTrials_AudioEditor

# Install dependencies
pip install -r requirements.txt

# Run the application
python outlasttrials_audioeditor.py
```


## 📚 Usage

### Quick Start Guide of Editing Subtitles

1. **Initial Setup**
   ```
   📁 OutlastTrials_AudioEditor/
   ├── 📄 OutlastTrials_AudioEditor.exe
   ├── 📄 UnrealLocres.exe
   ├── 📄 repak.exe
   ├── 📁 vgstream/
   │   └── 📄 vgmstream-cli.exe
   ├── 📄 SoundbanksInfo.json
   ├── 📁 Wems/
   └── 📁 Localization/
   ```

2. **Edit Subtitles**
   - Select an audio file from the list
   - Press `F2` or double-click to edit subtitle
   - Save changes with `Ctrl+S`

3. **Create Mod**
   - Go to `Tools → Export Subtitles for Game`
   - Use `Tools → Compile Mod` to create .pak file
   - Deploy with `Tools → Deploy & Run` (F5)

### Quick Start Guide of Editing Audio

Sorry soon

### Advanced Features

<details>
<summary><b>🎯 Keyboard Shortcuts</b></summary>

| Action | Shortcut | Description |
|--------|----------|-------------|
| Edit Subtitle | `F2` | Open subtitle editor |
| Save | `Ctrl+S` | Save all changes |
| Export Audio | `Ctrl+E` | Export as WAV |
| Deploy & Run | `F5` | Deploy mod and launch game |
| Debug Console | `Ctrl+D` | Show debug information |
| Settings | `Ctrl+,` | Open settings dialog |

</details>

<details>
<summary><b>🔧 Configuration</b></summary>

Edit `settings.json` to customize:
```json
{
  "ui_language": "en",
  "theme": "dark",
  "subtitle_lang": "en",
  "game_path": "C:\\Games\\Outlast Trials",
  "auto_save": true
}
```
</details>

## 📖 Documentation

### File Structure
```
Outlast Trials Mod Structure:
MOD_P/
└── OPP/
    └── Content/
        ├── WwiseAudio/
        │   └── Windows/
        │       └── English(US)/
        │           └── [Modified .wem files]
        └── Localization/
            └── OPP_Subtitles/
                └── [Language]/
                    └── OPP_Subtitles.locres
```

### Supported File Types
- **Audio**: `.wem` (Wwise audio)
- **Subtitles**: `.locres` (Unreal Engine localization)
- **Export**: `.wav`, `.json`, `.txt`
- **Mod Package**: `.pak`

## 🐛 Bug Reports

Found a bug? Please open an issue with:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Debug log (from Debug Console)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 OutlastTrials AudioEditor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

## 🙏 Acknowledgments

- **Red Barrels** - For creating Outlast Trials
- **vgmstream** - Audio conversion tools
- **UnrealLocres** - Localization file handling
- **repak** - PAK file creation BIG THANKS hypermetric
- **PyQt5** - GUI framework
- **WWise** - Wem Files

## 💰 Donation

No

## 📊 Stats

<div align="center">
  
  ![Downloads](https://img.shields.io/github/downloads/Bezna/OutlastTrials_AudioEditor/total?style=for-the-badge)
  ![Stars](https://img.shields.io/github/stars/Bezna/OutlastTrials_AudioEditor?style=for-the-badge)
  ![Issues](https://img.shields.io/github/issues/Bezna/OutlastTrials_AudioEditor?style=for-the-badge)
  
</div>

---

<div align="center">
  
  **Made with ❤️ for the Outlast Trials modding community**
  
  [⬆ Back to Top](#-outlasttrials-audioeditor)
  
</div>
