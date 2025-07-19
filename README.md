# 🎮 OutlastTrials AudioEditor

<div align="center">


**🔊 Audio & Subtitle Editor for Outlast Trials 🔊**

[![Version](https://img.shields.io/badge/version-0.4.beta-brightgreen?style=for-the-badge&logo=semantic-release)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge&logo=opensourceinitiative)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow?style=for-the-badge&logo=python)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightblue?style=for-the-badge&logo=windows)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)

[![Downloads](https://img.shields.io/github/downloads/Bezna/OutlastTrials_AudioEditor/total?style=for-the-badge&logo=download&color=success)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)
[![Stars](https://img.shields.io/github/stars/Bezna/OutlastTrials_AudioEditor?style=for-the-badge&logo=github&color=orange)](https://github.com/Bezna/OutlastTrials_AudioEditor)
[![Discord](https://img.shields.io/badge/Discord-Bezna-7289da?style=for-the-badge&logo=discord)](https://discord.com)

[🚀 Quick Start](#-quick-start) • [✨ Features](#-features) • [📖 Documentation](#-documentation) • [💬 Support](#-support--contact)

</div>

---

## 🌟 Overview

<div align="center">
  <img src="https://i.imgur.com/qo6DNnA.png" alt="Application Screenshot" width="750" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"/>
</div>

<br>

**OutlastTrials AudioEditor** is the **ultimate modding suite** for Outlast Trials enthusiasts! Whether you're a content creator, voice actor, translator, or just want to add your personal touch to the game, this tool provides everything you need to create professional-quality audio and subtitle modifications.

---

## ✨ Features

### 🎵 **Advanced Audio Management**
<details>
<summary><b>🔧 Click to expand audio features</b></summary>

- **🎧 WEM File Support** - Native handling of Wwise audio files used in Outlast Trials
- **▶️ Real-time Playback** - Built-in audio player with timeline scrubbing and controls
- **⚡ Batch Processing** - Convert and process multiple audio files simultaneously
- **📊 Duration Analysis** - Smart comparison tools to prevent audio cutoffs in-game
- **🔄 Format Conversion** - Seamless bidirectional conversion between WEM ↔ WAV

</details>

### 📝 **Professional Subtitle Editing**
<details>
<summary><b>🌍 Click to expand subtitle features</b></summary>

- **🌐 Multi-language Support** - Full support for EN, RU, FR, DE, ES, JP, KR, CN, and more
- **📄 Locres File Handling** - Native support for Unreal Engine localization files
- **📦 Batch Export** - Export all subtitle modifications with one command

</details>

### 🛠️ **Complete Modding Toolkit**
<details>
<summary><b>⚙️ Click to expand modding tools</b></summary>

- **🎯 One-Click Compilation** - Build game-ready .pak files instantly
- **🚀 Auto-deployment** - Deploy mods directly to Outlast Trials with F5
- **📁 Project Management** - Organize multiple mods and track changes

</details>

---

## 🚀 Quick Start

### ⚡ **Option 1: Instant Setup (Recommended)**

<div align="center">

[![Download Latest](https://img.shields.io/badge/📥_Download_Latest_Release-success?style=for-the-badge&logo=download)](https://github.com/Bezna/OutlastTrials_AudioEditor/releases)

</div>

```bash
1. 📥 Download the latest release ZIP file + Wems (Recomended)
2. 📂 Extract to any folder on your computer  
3. ▶️ Run OutlastTrials_AudioEditor.exe
4. 🎉 Start modding immediately!
```

### 🔧 **Option 2: Developer Setup**

<details>
<summary><b>🛠️ Advanced installation from source</b></summary>

```bash
# 📋 Clone the repository
git clone https://github.com/Bezna/OutlastTrials_AudioEditor.git
cd OutlastTrials_AudioEditor

# 🐍 Install Python dependencies
pip install -r requirements.txt

# ▶️ Launch the application
python outlasttrials_audioeditor.py
```

</details>

### 📋 **System Requirements**

<table>
<tr>
<td><b>Operating System</b></td>
<td>Windows 10/11 (64-bit recommended)</td>
</tr>
<tr>
<td><b>Game Version</b></td>
<td>Outlast Trials (Steam version)</td>
</tr>
<tr>
<td><b>Audio Editor</b></td>
<td><a href="https://www.audacityteam.org/download/">Audacity</a> (free)</td>
</tr>
<tr>
<td><b>Audio Engine</b></td>
<td><a href="https://www.audiokinetic.com/download/">Wwise 2019.1.6.7110</a> (free registration required)</td>
</tr>
</table>

---

## 📚 Complete Usage Guide

### 🎯 **Subtitle Editing Workflow**

<div align="center">

</div>

#### **Step 1: Open the Editor** 
```
🌍 Choose your subtitles language in settings
🎵 Select any audio file from the main list
⌨️ Press F2 or double-click to open subtitle editor
```

#### **Step 2: Edit Content**
```
✏️ Type your new subtitle text in the editor
```

#### **Step 3: Export & Deploy**
```
💾 Save changes with Ctrl+S
📦 Go to Tools → Export Subtitles for Game
🚀 Use Tools → Compile Mod to create the final .pak file
🎮 Deploy with Tools → Deploy & Run (F5) and test in-game
```

### 🎵 **Professional Audio Editing Pipeline**

<div align="center">

</div>

#### **🎧 Phase 1: Audio Preparation in Audacity**

<div align="center">
<table>
<tr>
<td align="center">
<h4>⚠️ CRITICAL RULE</h4>
<b>Each new audio file must be created in different Audacity projects.</i>
</tr>
</table>
</div>

**Audacity Setup & Editing:**
```bash
🎵 Import your source audio file into Audacity
⏱️ Check original Outlast Trials audio duration first
✂️ Edit, trim, and perfect your audio content
🔊 Adjust volume levels to match game standards
🔇 Apply noise reduction and enhancement filters
📐 Ensure final length ≤ original duration
```

**Critical Export Settings:**
```yaml
File Format: WAV (Microsoft)
Sample Rate: 48000 Hz ⚡ REQUIRED
Encoding: Signed 16-bit PCM
Channels: Mono ⚡ REQUIRED  
Filename: EXACT match to original ⚡ CASE-SENSITIVE
```

**Example Filenames:**
```
✅ VO_Scripted_Avellanos_Lobby_Motivation06.wav
✅ VO_Scripted_Hendrick_Tutorial_Introduction01.wav  
✅ VO_Scripted_Easterman_Briefing_Mission02.wav
✅ VO_Player_Male_Pain_Hit01.wav
✅ VO_Player_Female_Scream_Death03.wav
```

#### **🎛️ Phase 2: Wwise Conversion Process**

**Project Setup:**
```bash
🔧 Launch Wwise 2019.1.6.7110
📁 Create new project or open existing
🎵 Import your prepared WAV file
```

**Conversion Configuration:**
```yaml
Conversion Method: Mono 48000
Format: Vorbis ⚡ REQUIRED
Quality: 3 (optimal balance) 
Options: ✅ Insert filename marker ⚡ CRITICAL
```
<img src="https://i.imgur.com/5QXSoQU.png" width="750" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"/>

**Generate WEM File:**
```
🔄 Click "Convert" to process audio
📁 Locate WEM file in project folder
✅ Verify successful generation
```

#### **⚙️ Phase 3: AudioEditor Integration**

**Import & Process:**
```bash
📂 Open "Convert" tab in AudioEditor
🔍 Browse to your Wwise project folder
⚡ Click "Process WEM files"
⏳ Wait for completion
✅ Verify in processing log
```

#### **🚀 Phase 4: Final Deployment**

**Compile Mod:**
```bash
🛠️ Tools → Compile Mod
📦 Creates game-ready .pak file
✅ Verify compilation success
```

**Deploy & Test:**
```bash
🎮 Press F5 or Tools → Deploy & Run
📁 Auto-copies to Outlast Trials folder
▶️ Launches game automatically
🎧 Test your custom audio in-game!
```

---

## ⌨️ Keyboard Shortcuts

<div align="center">

**🚀 Master these shortcuts for lightning-fast workflow!**

</div>

<table align="center">
<tr>
<th width="25%">🎯 Action</th>
<th width="20%">⌨️ Shortcut</th>
<th width="55%">📝 Description</th>
</tr>
<tr>
<td><b>Edit Subtitle</b></td>
<td><code>F2</code></td>
<td>Open subtitle editor for selected file</td>
</tr>
<tr>
<td><b>Save All Changes</b></td>
<td><code>Ctrl+S</code></td>
<td>Save all modifications to files</td>
</tr>
<tr>
<td><b>Export Audio</b></td>
<td><code>Ctrl+E</code></td>
<td>Export selected audio as WAV format</td>
</tr>
<tr>
<td><b>Deploy & Launch</b></td>
<td><code>F5</code></td>
<td>Deploy mod and launch Outlast Trials</td>
</tr>
<tr>
<td><b>Debug Console</b></td>
<td><code>Ctrl+D</code></td>
<td>Show debug information and error logs</td>
</tr>
<tr>
<td><b>Settings Panel</b></td>
<td><code>Ctrl+,</code></td>
<td>Open application preferences</td>
</tr>

</table>

---

## ⚠️ Important Notes & Best Practices

<div align="center">

</div>

<table align="center">
<tr>
<td align="center" width="50%">
<h4>⏱️ Duration Constraints</h4>
<b>New audio MUST be ≤ original length</b><br>
Longer audio will be cut off mid-sentence in-game
</td>
<td align="center" width="50%">
<h4>📝 Filename Accuracy</h4>
<b>Exact case-sensitive matching required</b><br>
Any typo will prevent the mod from working
</td>
</tr>
<tr>
<td align="center">
<h4>🎵 Audio Quality</h4>
<b>Use new Audacity projects for each audio</b><br>
Prevents cross-contamination and ensures clean output
</td>
<td align="center">
<h4>🔧 Wwise Version</h4>
<b>Must use Wwise 2019.1.6.7110</b><br>
Other versions may produce incompatible files
</td>
</tr>
</table>

---

## 🛠️ Troubleshooting Center

<div align="center">
</div>

<details>
<summary><b>🔊 Audio Issues</b></summary>

| ❌ **Problem** | 🔍 **Cause** | ✅ **Solution** |
|---|---|---|
| Audio cuts off in-game | New audio too long | Reduce duration in Audacity to match original |
| No sound plays at all | Filename mismatch | Check exact spelling and case sensitivity |
| Poor/distorted quality | Low Vorbis quality setting | Increase quality to 3-5 in Wwise conversion |
| Audio crackling/static | Sample rate mismatch | Ensure 48000 Hz in both Audacity and Wwise |
| Some audio work, others don't | Previous Audacity Projects | Try to remake wav audio |
</details>

<details>
<summary><b>🎮 Game Integration Issues</b></summary>

| ❌ **Problem** | 🔍 **Cause** | ✅ **Solution** |
|---|---|---|
| Mod doesn't load | Incorrect file structure | Verify .pak contents match expected folders |
| Game crashes on startup | Corrupted WEM file | Re-export from Wwise with proper settings |


</details>

<details>
<summary><b>⚙️ Application Issues</b></summary>

| ❌ **Problem** | 🔍 **Cause** | ✅ **Solution** |
|---|---|---|
| Can't find game folder | Incorrect path settings | Update game path in Settings (Ctrl+,) |
| Wwise conversion fails | Missing or wrong Wwise version | Install Wwise 2019.1.6.7110 exactly |
| Subtitle editor won't open | Corrupted localization file | Reset subtitle files or reinstall |
| F5 deploy doesn't work | Missing game permissions | Run as administrator if needed |

</details>

---

## 🤝 Contributing & Community

<div align="center">

[![Contributors](https://img.shields.io/badge/👥_Join_Contributors-orange?style=for-the-badge)](https://github.com/Bezna/OutlastTrials_AudioEditor/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/Bezna/OutlastTrials_AudioEditor?style=for-the-badge&logo=github)](https://github.com/Bezna/OutlastTrials_AudioEditor/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/Bezna/OutlastTrials_AudioEditor?style=for-the-badge&logo=github)](https://github.com/Bezna/OutlastTrials_AudioEditor/pulls)

</div>

<table align="center">
<tr>
<td align="center" width="25%">
<h4>🐛 Bug Reports</h4>
Found an issue?<br>
<a href="https://github.com/Bezna/OutlastTrials_AudioEditor/issues">Report it here</a>
</td>
<td align="center" width="25%">
<h4>💡 Feature Ideas</h4>
Have a suggestion?<br>
<a href="https://github.com/Bezna/OutlastTrials_AudioEditor/issues">Share your idea</a>
</td>
<td align="center" width="25%">
<h4>📖 Documentation</h4>
Improve guides<br>
Submit a pull request
</td>
<td align="center" width="25%">
<h4>💻 Code</h4>
Fix bugs or add features<br>
Fork and contribute
</td>
</tr>
</table>

---

## 💬 Support & Contact

<div align="center">

### **🆘 Need Help? We're Here for You!**

<table>
<tr>
<td align="center" width="33%">
<h4>💬 Discord Support</h4>
<img src="https://img.shields.io/badge/Discord-Bezna-7289da?style=for-the-badge&logo=discord" alt="Discord Badge"/><br>
<b>Discord: Bezna</b><br>
</td>
<td align="center" width="33%">
<h4>🐛 Bug Reports</h4>
<a href="https://github.com/Bezna/OutlastTrials_AudioEditor/issues">
<img src="https://img.shields.io/badge/GitHub-Issues-red?style=for-the-badge&logo=github" alt="GitHub Issues"/>
</a><br>
<i>Technical issues & bugs</i>
</td>
<td align="center" width="33%">
<h4>💖 Donations</h4>
<a href="https://www.donationalerts.com/r/bezna_">
<img src="https://img.shields.io/badge/Donate-Support_Project-green?style=for-the-badge&logo=paypal" alt="Donate"/>
</a><br>
<i>Support development</i>
</td>
</tr>
</table>

</div>

### **📋 When Reporting Issues, Please Include:**

```
🔍 Detailed description of the problem
📝 Step-by-step reproduction instructions  
⚡ Expected vs actual behavior
🐛 Debug log (from Ctrl+D in the app)
💻 System info (Windows version, game version)
📸 Screenshots if applicable
🎵 Audio files causing issues (if relevant)
```

---



---

## 📝 License

<div align="center">

**📜 Open Source Under MIT License**

[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&logo=opensourceinitiative)](LICENSE)

</div>

<details>
<summary><b>📖 View Full License</b></summary>

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

</details>

---
## 🙏 Acknowledgments

Special thanks to the tools and communities that made this project possible:

- **Red Barrels** - For creating the amazing Outlast Trials game
- **vgmstream Team** - For excellent audio conversion tools
- **UnrealLocres Contributors** - For localization file handling
- **repak by hypermetric** - For PAK file creation (BIG THANKS!)
- **Audiokinetic** - For the Wwise audio engine
- **PyQt5 Team** - For the GUI framework

## 💰 Support the Project

[Support](https://www.donationalerts.com/r/bezna_)

If you would like to support the project in another way:
- ⭐ Star this repository
- 🐛 Report bugs and issues
- 📢 Share with other modders
- 🤝 Contribute code or documentation


---

<div align="center">
  
  **Made with ❤️ for the Outlast Trials modding community**
  
  *Happy Modding!* 🎮
  
  [⬆ Back to Top](#-outlasttrials-audioeditor)
  
</div>
