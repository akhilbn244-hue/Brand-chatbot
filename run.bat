@echo off
REM ================================================================
REM  run.bat - double-click to start the app.
REM  It opens in Google Chrome (or your default browser if Chrome isn't
REM  installed). Keep this black window open while you use the app;
REM  close it when you're done.
REM ================================================================
cd /d "%~dp0"
title Brand Knowledge Chatbot - running (close this window to stop)

if not exist ".venv\Scripts\activate.bat" (
    echo  Please double-click setup.bat first.
    pause
    exit /b 1
)

REM Streamlit asks for an email the very first time it runs, and waits.
REM Creating this small settings file answers "no thanks" in advance.
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
    > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
    >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

REM Find Chrome in the usual places it gets installed.
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

REM BROWSER tells Python (and so Streamlit) which browser to open.
REM If Chrome wasn't found, this stays empty and your default browser is used.
if defined CHROME set "BROWSER=%CHROME%"

call ".venv\Scripts\activate.bat"
echo  Starting the app... it will open in your browser in a few seconds.
echo  If it doesn't, open Chrome and go to http://localhost:8501
streamlit run app.py
pause
