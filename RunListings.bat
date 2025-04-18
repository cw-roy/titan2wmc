@echo off
SETLOCAL ENABLEEXTENSIONS

cd /d %~dp0

set VENV_DIR=venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
set SCRIPT=main.py
set MXF_FILE=data\listings.mxf
set LOADMXF_EXE=%SystemRoot%\ehome\loadmxf.exe
set STORE=mcepg3-0.db

REM Check for virtual environment
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment not found. Please set it up first.
    pause
    exit /b 1
)

REM Run Python script
echo [INFO] Running Python script...
"%PYTHON_EXE%" "%SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Python script failed.
    pause
    exit /b 1
)

REM Confirm MXF file was created
if not exist "%MXF_FILE%" (
    echo [ERROR] MXF file was not generated: %MXF_FILE%
    pause
    exit /b 1
)

REM Stop WMC services
REM echo [INFO] Stopping Windows Media Center services...
REM net stop ehrecvr >nul 2>&1
REM net stop ehsched >nul 2>&1
REM taskkill /IM ehshell.exe /F >nul 2>&1

REM Import MXF into WMC
echo [INFO] Importing MXF into Windows Media Center...
"%LOADMXF_EXE%" -i "%MXF_FILE%" -s "%STORE%"
if errorlevel 1 (
    echo [ERROR] loadmxf.exe failed to import the MXF file.
    pause
    exit /b 1
)

echo [SUCCESS] MXF import completed successfully.
pause
ENDLOCAL
