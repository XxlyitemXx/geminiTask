@echo off
REM GeminiTask Installation Script for Windows

echo ==== Installing GeminiTask ====

REM Install dependencies
echo Installing required Python packages...
pip install click python-dateutil tabulate rich google-generativeai

REM Prompt for API key
echo.
echo To use the Gemini API features, you need to provide an API key.
set /p API_KEY="Enter your Gemini API key (or press Enter to skip for now): "

if not "%API_KEY%"=="" (
    echo Setting up API key...
    python geminitask.py config --api-key "%API_KEY%"
)

REM Ask about system-wide installation
echo.
set /p INSTALL_SYSTEM_WIDE="Do you want to install GeminiTask as a system-wide command? (y/n): "

if /i "%INSTALL_SYSTEM_WIDE%"=="y" (
    REM Create batch file
    echo Creating system-wide command...
    
    REM Get current directory (with proper escaping for batch file)
    set CURRENT_DIR=%CD%
    set CURRENT_DIR=%CURRENT_DIR:\=\\%
    
    REM Create batch file content
    echo @echo off > "%TEMP%\geminitask.bat"
    echo python "%CURRENT_DIR%\geminitask.py" %%* >> "%TEMP%\geminitask.bat"
    
    REM Determine if we can write to Windows directory
    if exist "%WINDIR%\System32\cmd.exe" (
        echo Attempting to install to system path...
        copy "%TEMP%\geminitask.bat" "%WINDIR%\geminitask.bat" > nul 2>&1
        if errorlevel 1 (
            echo Administrator access required to install system-wide.
            echo Installing to user directory instead.
            if not exist "%USERPROFILE%\bin" mkdir "%USERPROFILE%\bin"
            copy "%TEMP%\geminitask.bat" "%USERPROFILE%\bin\geminitask.bat" > nul
            echo Created command in %USERPROFILE%\bin
            echo Please add %USERPROFILE%\bin to your PATH if it isn't already.
        ) else (
            echo Created system-wide command successfully.
        )
    ) else (
        if not exist "%USERPROFILE%\bin" mkdir "%USERPROFILE%\bin"
        copy "%TEMP%\geminitask.bat" "%USERPROFILE%\bin\geminitask.bat" > nul
        echo Created command in %USERPROFILE%\bin
        echo Please add %USERPROFILE%\bin to your PATH if it isn't already.
    )
    
    del "%TEMP%\geminitask.bat"
)

echo.
echo ==== Installation Complete ====
echo To get started, try: python geminitask.py add "My first task" --priority high
if /i "%INSTALL_SYSTEM_WIDE%"=="y" (
    echo Or simply: geminitask add "My first task" --priority high ^(if the installation directory is in your PATH^)
)
echo.
