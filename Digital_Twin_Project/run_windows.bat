@echo off
setlocal
cd /d "%~dp0"

set "PYTHON="
for %%P in (python.exe) do if exist "%%~$PATH:P" set "PYTHON=%%~$PATH:P"
if "%PYTHON%"=="" if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if "%PYTHON%"=="" (
    echo Python was not found. Please install Python 3.10 or newer and select Add Python to PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    "%PYTHON%" -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m streamlit run app.py
pause
