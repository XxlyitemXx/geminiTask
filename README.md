# GeminiTask

A command-line interface application built with Python that allows users to efficiently manage tasks with standard features and intelligent enhancements powered by the Gemini API.

┏━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ ID ┃ Description ┃ Priority ┃ Due Date           ┃ Context ┃ Project ┃ Status  ┃
┡━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ 1  │ sleep       │ high     │ Monday at 11:59 PM │         │         │ Pending │
└────┴─────────────┴──────────┴────────────────────┴─────────┴─────────┴─────────┘

## Features

- **Core Task Management**:
  - Add tasks with optional priority, due date, context, and project
  - List tasks with various filtering options
  - Mark tasks as complete
  - Edit existing tasks
  - Delete tasks

- **Intelligent Features (Gemini API)**:
  - Natural language date/time processing
  - Smart due date suggestions
  - Context and project suggestions

- **Context and Project Management**:
  - Add and list contexts
  - Add and list projects

## Installation

### Automated Installation Scripts

For convenience, GeminiTask comes with installation scripts for both platforms:

#### macOS/Linux
```bash
# Make the script executable and run it
chmod +x install.sh
./install.sh
```

#### Windows
```cmd
# Run the installation script
install.bat
```

These scripts will install the required dependencies, prompt you for your Gemini API key, and offer to set up GeminiTask as a system-wide command.

### Manual Installation

#### macOS

```bash
# Clone the repository
git clone https://github.com/xxlyitemxx/geminiTask.git
cd geminiTask

# Install dependencies (with --user flag to avoid system package conflicts)
pip3 install --user click python-dateutil tabulate rich google-generativeai

# Make the script executable
chmod +x geminitask.py

# Set your Gemini API key
./geminitask.py config --api-key YOUR_GEMINI_API_KEY
```

### Windows

```cmd
# Clone the repository
git clone https://github.com/xxlyitemxx/geminiTask.git
cd geminiTask

# Install dependencies
pip install click python-dateutil tabulate rich google-generativeai

# Set your Gemini API key
python geminitask.py config --api-key YOUR_GEMINI_API_KEY
```

### Alternative: Using as a System-Wide Command (macOS/Linux)

```bash
# Create a symlink to make the command available system-wide
sudo ln -s "$(pwd)/geminitask.py" /usr/local/bin/geminitask

# Now you can use it from anywhere
geminitask add "My new task" --priority high
```

### Alternative: Using as a System-Wide Command (Windows)

Create a batch file named `geminitask.bat` in a directory that's in your PATH (e.g., `C:\Windows`):

```batch
@echo off
python "C:\path\to\geminiTask\geminitask.py" %*
```

## Usage

```bash
# Add a new task
geminitask add "Write a blog post" --priority high --due "next Monday morning" --project "Content Creation"

# List tasks
geminitask list --project "Content Creation" --due "next week"

# Mark a task as done
geminitask done 3

# Edit a task
geminitask edit 1 --description "Finalize blog post"

# Delete a task
geminitask delete 2

# Manage contexts and projects
geminitask add-context "work"
geminitask list-contexts
geminitask add-project "Content Creation"
geminitask list-projects
```

## Configuration

Configuration is stored in a local file. You can also set the Gemini API key as an environment variable:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

## License

MIT
