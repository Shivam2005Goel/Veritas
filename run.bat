@echo off
TITLE Veritas - Fact Knowledge Layer
echo =================================================================
echo           VERITAS - Multi-Document Fact Knowledge Layer
echo       Grounding * Evidence Highlighting * Cross-Doc Reconciler
echo =================================================================
echo.

echo Starting backend on port 8000 and frontend on port 3000...
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause
