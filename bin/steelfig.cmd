@echo off
rem steelfig command. Uses %STEELFIG_PYTHON%, else the interpreter recorded by setup.py in <repo>\.python, else python.
set "PY=%STEELFIG_PYTHON%"
if "%PY%"=="" if exist "%~dp0..\.python" set /p PY=<"%~dp0..\.python"
if "%PY%"=="" set "PY=python"
"%PY%" "%~dp0..\steelfig\cli.py" %*
