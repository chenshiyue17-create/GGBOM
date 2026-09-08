@echo off
py -3 "%~dp0tools\dev.py" %*
exit /b %errorlevel%
