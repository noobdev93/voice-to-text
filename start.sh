#!/bin/bash
# Voice-to-Text App Startup Script

echo "🎤 Starting Voice-to-Text Dictation System..."
echo "=" * 50

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
python -c "import pynput, pyaudio, speech_recognition" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed. Run install.sh first."
    exit 1
fi

echo "✅ Dependencies ready"
echo "✅ Starting voice-to-text app..."
echo ""
echo "🌐 Hold Globe/Fn key to dictate into any text field!"
echo "📝 Click in a text field, then hold Globe/Fn and speak"
echo ""

# Run the main app
python voice_to_text.py
