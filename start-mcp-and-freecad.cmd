@echo off
REM Start FreeCAD GUI with the Robust MCP Bridge auto-started (Windows).
REM
REM The MCP server itself (freecad-mcp) is launched by your MCP client (for
REM example Claude Code) from .mcp.json - this script only starts FreeCAD with
REM the bridge so the server has something to connect to on localhost:9875.
REM
REM No other tools are required: the script launches freecad.exe directly with
REM the bridge startup script (the same thing `just freecad::run-gui-custom` does).
REM
REM Override the FreeCAD location by setting FREECAD_EXE before running, e.g.:
REM   set FREECAD_EXE=D:\Apps\FreeCAD\bin\freecad.exe
REM   start-mcp-and-freecad.cmd

setlocal

if not "%FREECAD_EXE%"=="" goto :check
for %%D in ("C:\Program Files\FreeCAD 1.1" "C:\Program Files\FreeCAD 1.0" "%LOCALAPPDATA%\Programs\FreeCAD 1.1" "%LOCALAPPDATA%\Programs\FreeCAD 1.0") do (
    if exist "%%~D\bin\freecad.exe" (
        set "FREECAD_EXE=%%~D\bin\freecad.exe"
        goto :check
    )
)
set "FREECAD_EXE=C:\Program Files\FreeCAD 1.1\bin\freecad.exe"

:check
if not exist "%FREECAD_EXE%" (
    echo ERROR: FreeCAD not found at "%FREECAD_EXE%".
    echo Set the FREECAD_EXE environment variable to your freecad.exe path.
    exit /b 1
)

set "STARTUP_SCRIPT=%~dp0freecad\RobustMCPBridge\freecad_mcp_bridge\startup_bridge.py"
if not exist "%STARTUP_SCRIPT%" (
    echo ERROR: Bridge startup script not found: "%STARTUP_SCRIPT%"
    echo Run this script from the repository checkout.
    exit /b 1
)

echo Starting FreeCAD with MCP bridge...
echo   FreeCAD: %FREECAD_EXE%
echo   Bridge:  %STARTUP_SCRIPT%
start "" "%FREECAD_EXE%" "%STARTUP_SCRIPT%"
endlocal
