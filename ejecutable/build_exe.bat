@echo off
rem Se trabaja desde la carpeta del proyecto (la de arriba de "ejecutable")
cd /d "%~dp0.."

set PYTHON_CMD=
where py >nul 2>nul && set PYTHON_CMD=py
if defined PYTHON_CMD goto have_python
where python >nul 2>nul && set PYTHON_CMD=python
if defined PYTHON_CMD goto have_python

echo No se encontro Python.
echo Instalalo desde https://www.python.org/downloads/ y marca la casilla "Add python.exe to PATH".
pause
exit /b 1

:have_python
echo Usando: %PYTHON_CMD%
%PYTHON_CMD% -m pip install pyinstaller
if errorlevel 1 goto failed

rem El .exe y los archivos de trabajo de PyInstaller quedan dentro de "ejecutable"
%PYTHON_CMD% -m PyInstaller --onefile --name CalculadoraDistribuciones --distpath ejecutable\dist --workpath ejecutable\build --specpath ejecutable --add-data "%CD%\frontend;frontend" "%CD%\backend\desktop.py"
if errorlevel 1 goto failed

if not exist "ejecutable\dist\CalculadoraDistribuciones.exe" goto failed

echo.
echo Listo. El ejecutable esta en la carpeta "dist", junto a este archivo.
explorer "ejecutable\dist"
pause
exit /b 0

:failed
echo.
echo Algo fallo. Copia el mensaje de arriba para revisarlo.
pause
exit /b 1