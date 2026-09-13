@echo off
REM Start FreeCAD GUI with the Robust MCP Bridge auto-started (Windows).
REM
REM The MCP server itself (freecad-mcp) is launched by your MCP client (for
REM example Claude Code) from .mcp.json - this script only starts FreeCAD with
REM the bridge so the server has something to connect to on localhost:9875.
REM
REM Requirements: `just` on PATH (winget install Casey.Just) and Git Bash
REM (the justfile uses Git Bash as its Windows shell).
REM
REM Override the FreeCAD location by setting FREECAD_EXE before running, e.g.:
REM   set FREECAD_EXE=D:\Apps\FreeCAD\bin\freecad.exe
REM   start-mcp-and-freecad.cmd

setlocal
if "%FREECAD_EXE%"=="" set "FREECAD_EXE=C:\Program Files\FreeCAD 1.1\bin\freecad.exe"

if not exist "%FREECAD_EXE%" (
    echo ERROR: FreeCAD not found at "%FREECAD_EXE%".
    echo Set the FREECAD_EXE environment variable to your freecad.exe path.
    exit /b 1
)

cd /d "%~dp0"
just freecad::run-gui-custom "%FREECAD_EXE%"
endlocal
