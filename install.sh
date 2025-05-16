#!/bin/bash
# GeminiTask Installation Script for macOS/Linux

set -e  # Exit on error

echo "==== Installing GeminiTask ===="

# Install dependencies
echo "Installing required Python packages..."
pip3 install --user click python-dateutil tabulate rich google-generativeai

# Make the script executable
echo "Making geminitask.py executable..."
chmod +x "$(pwd)/geminitask.py"

# Prompt for API key
echo ""
echo "To use the Gemini API features, you need to provide an API key."
read -p "Enter your Gemini API key (or press Enter to skip for now): " API_KEY

if [ ! -z "$API_KEY" ]; then
    echo "Setting up API key..."
    ./geminitask.py config --api-key "$API_KEY"
fi

# Ask about system-wide installation
echo ""
read -p "Do you want to install GeminiTask as a system-wide command? (y/n): " INSTALL_SYSTEM_WIDE

if [[ "$INSTALL_SYSTEM_WIDE" =~ ^[Yy]$ ]]; then
    # Determine the appropriate bin directory
    if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
        BIN_DIR="/usr/local/bin"
    elif [ -d "$HOME/.local/bin" ]; then
        BIN_DIR="$HOME/.local/bin"
        # Ensure ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
            echo "Added $HOME/.local/bin to your PATH"
        fi
    else
        mkdir -p "$HOME/.local/bin"
        BIN_DIR="$HOME/.local/bin"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
        echo "Created $HOME/.local/bin and added it to your PATH"
    fi

    # Create the symlink
    ln -sf "$(pwd)/geminitask.py" "$BIN_DIR/geminitask"
    echo "Created symlink in $BIN_DIR"
    echo "You can now use 'geminitask' from anywhere"
    
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo "To use it immediately, run: source ~/.zshrc"
    else
        echo "To use it immediately, run: source ~/.bashrc"
    fi
fi

echo ""
echo "==== Installation Complete ===="
echo "To get started, try: ./geminitask.py add \"My first task\" --priority high"
if [[ "$INSTALL_SYSTEM_WIDE" =~ ^[Yy]$ ]]; then
    echo "Or simply: geminitask add \"My first task\" --priority high (after restarting your terminal or sourcing your shell configuration)"
fi
echo ""
