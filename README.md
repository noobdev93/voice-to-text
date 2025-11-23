# 🎤 Voice-to-Text Dictation System

A minimal, elegant voice dictation application for macOS that lets you speak into any text field using the Globe/Fn key. Hold the key, speak, and watch your words appear instantly in any application.

## ✨ Features

- **🌐 Globe/Fn Key Dictation** - Hold Globe/Fn key to record, release to transcribe
- **📝 Universal Text Input** - Works in any application (browsers, documents, chat apps, etc.)
- **🗣️ Real-time Speech Recognition** - Powered by Google Speech Recognition API (requires internet)
- **🎙️ macOS Integration** - Uses built-in microphone indicator (no custom animation needed)
- **🔒 Privacy** - Audio sent to Google servers for processing; by default, Google does not retain audio recordings (check your Google Account "Voice & Audio Activity" settings)
- **🌐 Internet Required** - Speech recognition requires active internet connection
- **⚡ Stable & Reliable** - Robust multi-use design that doesn't freeze or crash
- **🎯 Simple Workflow** - Click in text field → Hold Globe/Fn → Speak → Release → Text appears
- **📱 Background Operation** - Minimal UI that stays out of your way

## 🚀 Quick Start

### Prerequisites

- **macOS 10.15+** (optimized for Apple Silicon)
- **Python 3.9+** (Python 3.14 recommended)
- **Karabiner-Elements** (for Globe/Fn key remapping)
- **Homebrew** (for installing dependencies)
- **Internet Connection** (required for speech recognition)

### Step 1: Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python and Dependencies

```bash
# Install Python 3.14 (or latest Python 3.x)
brew install python@3.14

# Install Python Tkinter (required for UI)
brew install python-tk@3.14

# Install PortAudio (required for PyAudio)
brew install portaudio
```

### Step 3: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/voice-to-text.git
cd voice-to-text

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Install Karabiner-Elements

```bash
# Install Karabiner-Elements via Homebrew
brew install --cask karabiner-elements
```

**Or download manually:** [Karabiner-Elements](https://karabiner-elements.pqrs.org/)

### Step 5: Configure Karabiner-Elements

1. **Open Karabiner-Elements** (from Applications or Spotlight)
2. **Go to "Simple Modifications"** tab
3. **Select your keyboard** from the dropdown
4. **Click "Add item"** button
5. **Set the mapping:**
   - **From key:** `fn` (or `globe` if available)
   - **To key:** `f13`
6. **Enable the rule** (toggle should be ON)

**Alternative:** If you have a Globe key instead of Fn:
- **From key:** `globe`
- **To key:** `f13`

### Step 6: Grant macOS Permissions

The app needs several permissions to work:

#### A. Accessibility Permission

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Privacy & Security** → **Accessibility**
3. Click the **+** button and add:
   - **Terminal.app** (or your terminal app: iTerm2, Warp, etc.)
   - **Cursor** (if using Cursor IDE)
   - **Python Launcher** (if available)
   - **The specific Python executable** being used:
     - For Homebrew Python: `/opt/homebrew/opt/python@3.14/bin/python3.14`
     - Or: `/usr/local/bin/python3`
4. **Enable the toggle** for each added item

#### B. Input Monitoring Permission

1. In **System Settings** → **Privacy & Security** → **Input Monitoring**
2. Add the same applications as above
3. **Enable the toggle** for each

#### C. Microphone Permission

1. In **System Settings** → **Privacy & Security** → **Microphone**
2. Add **Terminal.app** (or your terminal app)
3. **Enable the toggle**

**💡 Tip:** If permissions don't work, try:
- Restarting your terminal/IDE
- Running the app once, then checking System Settings again
- Adding the specific Python executable path

### Step 7: Run the App

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the app
python voice_to_text.py
```

**Or use the convenience script:**
```bash
./start.sh
```

## 📖 Usage

1. **Start the app** (leave it running in the background)
2. **Click in any text field** (email, document, chat, browser, etc.)
3. **Hold the Globe/Fn key** (bottom-left corner of keyboard)
   - **Watch for macOS microphone indicator** in the menu bar (orange dot)
   - This confirms the app is recording
4. **Speak clearly** while holding the key
5. **Release the Globe/Fn key** when finished speaking
6. **Watch your words appear** automatically in the text field!

### Visual Feedback

- **🟢 Ready** - App is ready for dictation
- **🔴 Recording** - Currently recording (macOS mic indicator also shows)
- **🟡 Processing** - Transcribing your speech
- **✅ Done** - Text successfully injected

## 🛠 How It Works

```
Click text field → Hold Globe/Fn → Speak → Release → Text appears instantly
```

**Technical Stack:**
- **Karabiner-Elements** - Remaps Globe/Fn key to F13 for reliable detection
- **pynput** - Global hotkey detection and text injection
- **PyAudio** - Audio recording from microphone
- **SpeechRecognition** - Google Speech Recognition API for speech-to-text (requires internet)
- **Text Injection** - Types transcribed text into active application
- **macOS Integration** - Uses system microphone indicator

**Note:** This version requires an active internet connection for speech recognition. Audio is sent to Google's servers for processing. 

**Privacy:** By default, Google does not retain audio recordings from the Speech Recognition API. However, if you have "Voice & Audio Activity" enabled in your Google Account settings, Google may save audio data to improve services. You can manage this in your [Google Account settings](https://myaccount.google.com/activitycontrols). The transcribed text is returned to the app and is not stored by Google.

## ⚙️ Configuration

Edit `config/settings.json` to customize behavior:

```json
{
  "hotkey": {
    "combination": "f13",
    "hold_to_record": true,
    "toggle_mode": false
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1
  },
  "system": {
    "paste_mode": true,
    "typing_speed": 0
  }
}
```

**Key Settings:**
- `hold_to_record: true` - Hold key to record (recommended)
- `sample_rate: 16000` - Audio quality (16kHz is optimal for speech)
- `paste_mode: true` - Uses clipboard for faster injection

## 🏗 Project Structure

```
voice-to-text/
├── voice_to_text.py          # Main application
├── start.sh                   # Convenience startup script
├── requirements.txt           # Python dependencies
├── config/
│   └── settings.json          # Configuration file
├── src/
│   ├── hotkey_listener.py     # Global hotkey detection
│   ├── audio_recorder.py      # Audio recording system
│   ├── text_injector.py       # Text injection into apps
│   └── ui/                    # UI components
├── recordings/                # Temporary audio files (auto-deleted after 24hrs)
└── README.md                  # This file
```

## 🔧 Troubleshooting

### Globe/Fn Key Not Working

1. **Check Karabiner-Elements:**
   - Is it running? (check menu bar icon)
   - Is the rule enabled? (toggle should be ON)
   - Try restarting Karabiner-Elements

2. **Check Permissions:**
   - Verify Accessibility permission is granted
   - Verify Input Monitoring permission is granted
   - Try restarting terminal/app after granting permissions

3. **Test the key:**
   ```bash
   python -c "from pynput import keyboard; print('Press F13...'); keyboard.Listener(on_press=lambda k: print(f'Pressed: {k}')).start(); input()"
   ```

### Audio Not Recording

1. **Check Microphone Permission:**
   - System Settings → Privacy & Security → Microphone
   - Ensure Terminal (or your terminal app) is enabled

2. **Test Microphone:**
   ```bash
   python -c "import pyaudio; p = pyaudio.PyAudio(); print('Microphones:'); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
   ```

3. **Check Audio Levels:**
   - Speak louder
   - Check microphone isn't muted
   - Try a different microphone

### Text Not Injecting

1. **Click in the text field first** - The app needs focus on the target field
2. **Check Accessibility Permission** - Required for text injection
3. **Try different applications** - Some apps may have restrictions
4. **Check the app status** - Look for error messages in the app window

### "Could not understand audio" Errors

1. **Check internet connection** - Google API requires active internet connection
2. **Speak more clearly** - Enunciate words
3. **Hold key longer** - Recordings shorter than 0.5 seconds are rejected
4. **Speak louder** - Audio may be too quiet
5. **Reduce background noise** - Find a quieter environment

### App Freezes or Crashes

1. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.9+
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Check for conflicting apps** - Other apps using microphone/hotkeys

4. **Restart the app** - Close and reopen

### Permission Issues

If permissions keep getting denied:

1. **Add specific Python executable:**
   ```bash
   which python3  # Get the path
   ```
   Then add that exact path to Accessibility and Input Monitoring

2. **Try running from different terminal:**
   - Terminal.app
   - iTerm2
   - Cursor/VSCode integrated terminal

3. **Check System Integrity Protection (SIP):**
   - Usually not an issue, but can block some permissions
   - Check: `csrutil status`

## 🎯 Tips for Best Results

- **Speak clearly and at normal pace** - Not too fast, not too slow
- **Hold the key for at least 1 second** - Gives the app time to start recording
- **Click in text field first** - Ensures text goes to the right place
- **Use in quiet environment** - Reduces background noise
- **Keep app running in background** - Minimize window to top-right corner
- **Watch macOS mic indicator** - Orange dot confirms recording is active

## 🔄 Auto-Cleanup

The app automatically deletes audio recordings older than 24 hours to save disk space. Recordings are stored in the `recordings/` directory and are temporary files used only for transcription.

## 📄 License

Apache 2.0 License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- **Google Speech Recognition API** - Speech-to-text conversion
- **Karabiner-Elements** - Key remapping functionality
- **SpeechRecognition** - Python speech recognition library
- **pynput** - Global hotkey and input control

## 📝 Changelog

### Version 1.0.0
- Initial release
- Globe/Fn key hold-to-record functionality
- Google Speech Recognition integration
- Minimal UI with macOS integration
- Auto-cleanup of old recordings
- Universal text injection

---

**Built for seamless voice dictation into any application on macOS** 🚀

**Enjoy dictating!** 🎤✨
