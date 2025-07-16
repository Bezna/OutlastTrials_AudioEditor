# 🎮 OutlastTrials AudioEditor

<div align="center">
  
  ![Logo](https://img.shields.io/badge/Outlast_Trials-Audio_Editor-red?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEISURBVCiRY/z//z8DOmBhYGBgYGBgYPj//z8jAwMDw79//xhQBZmQBf79+8fw9+9fhj9//jAwMjIyMDMzM7CwsDBgBf/+/WP48+cPw+/fvxkYGRkZWFhYGNjY2BhYWVkZGBkZGbACIHD//n2GP3/+MDAzMzNwcnIysLOzM7CxsTEgW4UMfv/+zfDnzx8GJiYmBnZ2dgZ2dnYGdnZ2BmZmZgZGRkYGBgYGBkYmJiYGBgYGBmZmZgZWVlYGdnZ2BnZ2dgY2NjYGZmZmBqx++vfvH8Pfv38Zfv/+zcDExMTAysrKwMrKysDCwsKA1U+g6kDVgqoHVQ+qHhQAKH4EqQ5ULah6UPUgAAAAM7lEU7XYVysAAAAASUVORK5CYII=)
  
  **Audio & Subtitle Editor for Outlast Trials**
  
  [![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/downloads/)
  [![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-orange.svg)](https://pypi.org/project/PyQt5/)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)
  
  [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

**OutlastTrials AudioEditor** is a powerful, user-friendly tool designed specifically for modding audio files and subtitles in Outlast Trials. Built with Python and PyQt5, it provides a comprehensive solution for content creators, modders, and localization teams who want to create custom audio content and subtitle modifications for the game.

<div align="center">
  <img src="https://i.imgur.com/qo6DNnA.png" alt="Screenshot" width="800">
</div>

## ✨ Features

### 🎵 Audio Management
- **WEM File Support** - Native support for Wwise audio files used in Outlast Trials
- **Audio Playback** - Built-in player with timeline and controls for preview
- **Batch Processing** - Convert multiple audio files at once
- **Duration Analysis** - Compare original vs modified audio lengths to prevent in-game cutoffs
- **Format Conversion** - Seamless conversion between WEM and WAV formats
- **Wwise Integration** - Direct support for Audiokinetic Wwise projects

### 📝 Subtitle Editing
- **Multi-language Support** - Support for 14+ languages including EN, RU, FR, DE, ES, JP, KR, CN
- **Real-time Preview** - See subtitles while playing audio for perfect synchronization
- **Locres File Handling** - Native support for Unreal Engine localization files
- **Batch Subtitle Export** - Export all subtitle modifications at once

### 🛠️ Modding Tools
- **One-Click Compilation** - Build game-ready .pak files with a single button
- **Auto-deployment** - Deploy mods directly to Outlast Trials game folder
- **Debug Console** - Built-in debugging tools for troubleshooting mod issues
- **Project Management** - Organize your mods and keep track of changes

### 🎨 Modern Interface
- **Dark/Light Themes** - Choose your preferred appearance for comfortable editing
- **Multi-language UI** - Interface available in English and Russian
- **Intuitive Design** - Easy-to-use interface designed for both beginners and professionals
- **Keyboard Shortcuts** - Speed up your workflow with comprehensive hotkey support

## 🚀 Installation

### Option 1: Portable Version (Recommended)
1. Download the latest release from [Releases](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)
2. Extract the ZIP file to any location on your computer
3. Run `OutlastTrials_AudioEditor.exe` - no additional installation required!

### Option 2: From Source
```bash
# Clone the repository
git clone https://github.com/Bezna/OutlastTrials_AudioEditor.git
cd OutlastTrials_AudioEditor

# Install dependencies
pip install -r requirements.txt

# Run the application
python outlasttrials_audioeditor.py
```

### Requirements
- **Windows 10/11** (64-bit recommended)
- **Outlast Trials** (Steam version)
- **Audacity** (for audio editing) - [Download here](https://www.audacityteam.org/download/)
- **Wwise 2019.1.6.7110** (for audio conversion) - [Download here](https://www.audiokinetic.com/download/)

## 📚 Usage
### Quick Start Guide: Editing Subtitles

1. **Open Subtitle Editor**
   - Select an audio file from the list in the main window
   - Press `F2` or double-click the file to open subtitle editor
   - Choose your target language from the dropdown

2. **Edit Subtitles**
   - Type your new subtitle text in the editor
   - Use the audio preview to sync your text with the audio
   - Check character limits and formatting

3. **Save and Export**
   - Save changes with `Ctrl+S`
   - Go to `Tools → Export Subtitles for Game` to prepare files
   - Use `Tools → Compile Mod` to create the final .pak file

4. **Deploy Your Mod**
   - Use `Tools → Deploy & Run` (F5) to install and launch the game
   - Test your subtitles in-game

### Complete Guide: Editing Audio

#### Prerequisites Setup
- **Audacity** - Free audio editing software for preparing your audio
- **Wwise 2019.1.6.7110** - Audiokinetic's audio engine (free with registration)
- **OutlastTrials AudioEditor** - This application for final processing

#### Step 1: Prepare Your Audio in Audacity

1. **Import and Edit Your Audio**
   ```
   🎵 Open Audacity and import your new audio file
   ⏱️ Check the duration of the original Outlast Trials audio you want to replace
   ✂️ Edit your audio to NOT EXCEED the original duration
   ⚠️ CRITICAL: If your audio is longer, it will be cut off in-game!
   ```

2. **Audio Editing Tips**
   - Trim silence at the beginning and end
   - Adjust volume levels to match the original
   - Apply noise reduction if needed
   - Ensure the audio fits within the original timeframe

#### Step 2: Export with Correct Settings

Export your audio from Audacity with these exact specifications:

- **File Format**: WAV (Microsoft)
- **Sample Rate**: `48000 Hz`
- **Encoding**: `Signed 16-bit PCM`
- **Channels**: `Mono`
- **Filename**: Use the exact name of the original audio file

```
Example filenames:
• VO_Scripted_Avellanos_Lobby_Motivation06.wav
• VO_Scripted_Hendrick_Tutorial_Introduction01.wav
• VO_Scripted_Easterman_Briefing_Mission02.wav
```

#### Step 3: Convert to WEM using Wwise

1. **Setup Wwise Project**
   ```
   🔧 Open Wwise 2019.1.6.7110
   📁 Create a new project or open existing one
   🎵 Import your prepared WAV file into the project
   ```

2. **Configure Conversion Settings**
   ```
   ⚙️ Set these exact conversion settings:
      • Conversion Method: Mono 48000
      • Format: Vorbis
      • Quality: 3 (balance between size and quality)
      • Options: ✅ Insert filename marker (IMPORTANT!)
   ```

3. **Generate WEM File**
   ```
   🔄 Click "Convert" to generate the WEM file
   📁 Wwise will create the WEM file in your project folder
   ✅ Verify the file was created successfully
   ```

#### Step 4: Process in AudioEditor

1. **Import WEM Files**
   ```
   📂 In OutlastTrials AudioEditor:
      • Go to the "Convert" tab
      • Click "Browse"
      • Navigate to your Wwise project folder
      • Click "Process WEM files"
   ```

2. **Verify Processing**
   ```
   ⏳ Wait for processing to complete
   ✅ Check the log for any errors
   🎵 Your WEM files are now ready for the game
   ```

#### Step 5: Compile and Deploy Your Mod

1. **Create Mod Package**
   ```
   🛠️ Use Tools → Compile Mod to create .pak file
   📦 The mod will be packaged with proper folder structure
   ✅ Verify compilation completed without errors
   ```

2. **Deploy and Test**
   ```
   🎮 Use Tools → Deploy & Run (F5) to:
      • Copy mod to Outlast Trials folder
      • Launch the game automatically
      • Test your custom audio in-game
   ```

### Advanced Features and Tips

<details>
<summary><b>🎯 Keyboard Shortcuts</b></summary>

| Action | Shortcut | Description |
|--------|----------|-------------|
| Edit Subtitle | `F2` | Open subtitle editor for selected file |
| Save All | `Ctrl+S` | Save all changes to files |
| Export Audio | `Ctrl+E` | Export selected audio as WAV |
| Deploy & Run | `F5` | Deploy mod and launch Outlast Trials |
| Debug Console | `Ctrl+D` | Show debug information and logs |
| Settings | `Ctrl+,` | Open application settings |
| Refresh Files | `F5` | Refresh file list |
| Find Files | `Ctrl+F` | Search through audio files |

</details>

<details>
<summary><b>🔧 Configuration Options</b></summary>

Edit `settings.json` to customize your experience:
```json
{
  "ui_language": "en",
  "theme": "dark",
  "subtitle_lang": "en",
  "game_path": "C:\\Games\\Outlast Trials",
  "auto_save": true,
  "wwise_path": "C:\\Program Files (x86)\\Audiokinetic\\Wwise 2019.1.6.7110",
  "audacity_path": "C:\\Program Files\\Audacity\\audacity.exe"
}
```
</details>

<details>
<summary><b>📋 Common Audio File Examples</b></summary>

```
Voice Lines:
• VO_Scripted_Avellanos_Lobby_Motivation06
• VO_Scripted_Hendrick_Tutorial_Introduction01
• VO_Scripted_Easterman_Briefing_Mission02
• VO_Player_Male_Pain_Hit01
• VO_Player_Female_Scream_Death03

Sound Effects:
• SFX_Ambience_Facility_General_Loop
• SFX_UI_Button_Click
• SFX_Door_Metal_Open
• SFX_Footsteps_Concrete_Walk

Music:
• MUS_Menu_MainTheme_Loop
• MUS_Gameplay_Tension_Build
• MUS_Credits_EndTheme
```
</details>

## 📖 Documentation

### File Structure and Mod Organization
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
- **Audio Input**: `.wav` (from Audacity)
- **Audio Game**: `.wem` (Wwise audio format)
- **Subtitles**: `.locres` (Unreal Engine localization)
- **Export Formats**: `.wav`, `.json`, `.txt`
- **Mod Package**: `.pak` (Unreal Engine package)

### Technical Specifications
- **Audio Sample Rate**: 48000 Hz (required)
- **Audio Bit Depth**: 16-bit (signed PCM)
- **Audio Channels**: Mono (required for voice)
- **Compression**: Vorbis Quality 3 (optimal balance)
- **File Naming**: Case-sensitive, exact match required

## ⚠️ Important Notes and Limitations

### Audio Editing Constraints
- **Duration Limit**: New audio MUST be shorter or equal to original duration
- **File Naming**: Filenames must match exactly (case-sensitive)
- **Wwise Version**: Must use Wwise 2019.1.6.7110 for compatibility
- **Quality vs Size**: Higher Vorbis quality = larger file size

### Troubleshooting Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Audio cuts off in-game | New audio too long | Reduce duration in Audacity |
| No sound plays | Filename mismatch | Check exact filename spelling |
| Poor audio quality | Low Vorbis quality | Increase quality setting in Wwise |
| Mod doesn't load | Incorrect file structure | Verify .pak contents |
| Game crashes | Corrupted WEM file | Re-export from Wwise |

## 🤝 Contributing

We welcome contributions to make this tool even better! Here's how you can help:

### Ways to Contribute
- **Bug Reports**: Found an issue? Open a detailed bug report
- **Feature Requests**: Suggest new features for the editor
- **Documentation**: Improve this README or create video tutorials
- **Code**: Submit pull requests with improvements

## 🐛 Bug Reports and Support

Found a bug or need help? Please open an issue with:

- **Detailed description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Debug log** (from Debug Console in the app)
- **System information** (Windows version, game version)
- **Screenshots** if applicable

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 OutlastTrials AudioEditor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

Special thanks to the tools and communities that made this project possible:

- **Red Barrels** - For creating the amazing Outlast Trials game
- **vgmstream Team** - For excellent audio conversion tools
- **UnrealLocres Contributors** - For localization file handling
- **repak by hypermetric** - For PAK file creation (BIG THANKS!)
- **Audiokinetic** - For the Wwise audio engine
- **PyQt5 Team** - For the fantastic GUI framework

## 💰 Support the Project

This project is completely free and open-source. No donations needed - just enjoy modding Outlast Trials!

If you want to support the project:
- ⭐ Star this repository
- 🐛 Report bugs and issues
- 📢 Share with other modders
- 🤝 Contribute code or documentation

## 📊 Project Statistics

<div align="center">
  
  ![Downloads](https://img.shields.io/github/downloads/Bezna/OutlastTrials_AudioEditor/total?style=for-the-badge)
  ![Stars](https://img.shields.io/github/stars/Bezna/OutlastTrials_AudioEditor?style=for-the-badge)
  ![Issues](https://img.shields.io/github/issues/Bezna/OutlastTrials_AudioEditor?style=for-the-badge)
  ![Last Commit](https://img.shields.io/github/last-commit/Bezna/OutlastTrials_AudioEditor?style=for-the-badge)
  
</div>

---

<div align="center">
  
  **Made with ❤️ for the Outlast Trials modding community**
  
  *Happy Modding!* 🎮
  
  [⬆ Back to Top](#-outlasttrials-audioeditor)
  
</div>
