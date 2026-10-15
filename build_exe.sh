#!/bin/sh
python3 -m pip install pyinstaller
python3 -m PyInstaller --onefile --name CalculadoraDistribuciones --add-data "frontend:frontend" desktop.py
echo
echo "Listo. El ejecutable esta en: dist/CalculadoraDistribuciones"
