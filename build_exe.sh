#!/bin/sh
pip install pyinstaller
pyinstaller --onefile --name CalculadoraDistribuciones --add-data "frontend:frontend" desktop.py
echo
echo "Listo. El ejecutable esta en: dist/CalculadoraDistribuciones"
