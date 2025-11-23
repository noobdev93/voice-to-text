#!/bin/bash

# Voice-to-Text Installation Script
# Installs dependencies and sets up the application for macOS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This installer is designed for macOS. For other platforms, please install manually."
        exit 1
    fi
    log_info "Detected macOS - proceeding with installation"
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            log_success "Python version is compatible"
            PYTHON_CMD="python3"
        else
            log_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
            log_info "Please install Python 3.8+ from https://python.org"
            exit 1
        fi
    else
        log_error "Python 3 is not installed"
        log_info "Please install Python 3.8+ from https://python.org"
        exit 1
    fi
}

# Check and install Homebrew if needed
check_homebrew() {
    log_info "Checking Homebrew installation..."
    
    if command -v brew &> /dev/null; then
        log_success "Homebrew is installed"
    else
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        log_success "Homebrew installed successfully"
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Install PortAudio for PyAudio
    if brew list portaudio &> /dev/null; then
        log_info "PortAudio already installed"
    else
        log_info "Installing PortAudio..."
        brew install portaudio
        log_success "PortAudio installed"
    fi
    
    # Install other audio dependencies
    if brew list ffmpeg &> /dev/null; then
        log_info "FFmpeg already installed"
    else
        log_info "Installing FFmpeg..."
        brew install ffmpeg
        log_success "FFmpeg installed"
    fi
}

# Create virtual environment
create_venv() {
    log_info "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        log_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install PyAudio with proper flags for macOS
    log_info "Installing PyAudio..."
    pip install --global-option='build_ext' --global-option='-I/opt/homebrew/include' --global-option='-L/opt/homebrew/lib' pyaudio || {
        # Fallback for Intel Macs
        pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio
    }
    
    # Install other dependencies
    log_info "Installing other Python packages..."
    pip install -r requirements.txt
    
    log_success "Python dependencies installed"
}

# Install pyperclip dependency
install_clipboard_deps() {
    log_info "Installing clipboard dependencies..."
    
    # pyperclip requires pbcopy/pbpaste on macOS (usually pre-installed)
    if command -v pbcopy &> /dev/null && command -v pbpaste &> /dev/null; then
        log_success "Clipboard tools are available"
    else
        log_warning "Clipboard tools not found. Some features may not work."
    fi
}

# Setup application directories
setup_directories() {
    log_info "Setting up application directories..."
    
    # Create recordings directory
    mkdir -p recordings
    touch recordings/.gitkeep
    
    log_success "Application directories created"
}

# Check accessibility permissions
check_accessibility() {
    log_info "Checking accessibility permissions..."
    
    # Try to detect if accessibility permissions are granted
    # This is a heuristic check
    if $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.text_injector import AccessibilityChecker
    if AccessibilityChecker.check_accessibility_permissions():
        print('GRANTED')
    else:
        print('DENIED')
except Exception:
    print('UNKNOWN')
" 2>/dev/null | grep -q "GRANTED"; then
        log_success "Accessibility permissions are granted"
    else
        log_warning "Accessibility permissions may not be granted"
        log_info "The app will guide you through granting permissions when you first run it"
    fi
}

# Create launch script
create_launch_script() {
    log_info "Creating launch script..."
    
    cat > run.sh << 'EOF'
#!/bin/bash

# Voice-to-Text Launch Script
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the application
python voice_to_text.py "$@"
EOF

    chmod +x run.sh
    
    log_success "Launch script created: ./run.sh"
}

# Create desktop shortcut (optional)
create_desktop_shortcut() {
    log_info "Would you like to create a desktop shortcut? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        DESKTOP_PATH="$HOME/Desktop"
        APP_PATH="$(pwd)"
        
        cat > "$DESKTOP_PATH/Voice-to-Text.command" << EOF
#!/bin/bash
cd "$APP_PATH"
./run.sh
EOF
        
        chmod +x "$DESKTOP_PATH/Voice-to-Text.command"
        log_success "Desktop shortcut created"
    fi
}

# Run tests
run_tests() {
    log_info "Running basic tests..."
    
    source venv/bin/activate
    
    # Test Python imports
    if $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.hotkey_listener import HotkeyListener
from src.audio_recorder import AudioRecorder
from src.text_injector import TextInjector
import speech_recognition
import pynput
import pyaudio
print('All imports successful')
"; then
        log_success "All core modules import successfully"
    else
        log_error "Some modules failed to import"
        return 1
    fi
    
    # Test audio devices
    if $PYTHON_CMD -c "
import pyaudio
p = pyaudio.PyAudio()
device_count = p.get_device_count()
print(f'Found {device_count} audio devices')
for i in range(min(3, device_count)):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  Input: {info[\"name\"]}')
p.terminate()
"; then
        log_success "Audio system is working"
    else
        log_warning "Audio system test failed - check microphone permissions"
    fi
}

# Main installation function
main() {
    echo "============================================"
    echo "    Voice-to-Text Installation Script"
    echo "============================================"
    echo ""
    
    # Check system requirements
    check_macos
    check_python
    
    # Install system dependencies
    check_homebrew
    install_system_deps
    
    # Setup Python environment
    create_venv
    install_python_deps
    install_clipboard_deps
    
    # Setup application
    setup_directories
    check_accessibility
    
    # Create launch scripts
    create_launch_script
    create_desktop_shortcut
    
    # Run tests
    run_tests
    
    echo ""
    echo "============================================"
    log_success "Installation completed successfully!"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "1. Run the application: ./run.sh"
    echo "2. Grant accessibility permissions when prompted"
    echo "3. Configure your hotkey in settings"
    echo "4. Start voice dictation!"
    echo ""
    echo "For help and documentation:"
    echo "- README.md - Full documentation"
    echo "- docs/ - Additional guides"
    echo "- GitHub: https://github.com/noobdev93/voice-to-text"
    echo ""
    
    # Ask if user wants to run the app now
    log_info "Would you like to run the application now? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Starting Voice-to-Text..."
        ./run.sh
    else
        log_info "You can start the application later with: ./run.sh"
    fi
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main installation
main "$@"
