#!/bin/sh
# Se trabaja desde la carpeta del proyecto (la de arriba de "ejecutable")
cd "$(dirname "$0")/.."
python3 -m pip install pyinstaller
python3 -m PyInstaller --onefile --name CalculadoraDistribuciones --distpath ejecutable/dist --workpath ejecutable/build --specpath ejecutable --add-data "$PWD/frontend:frontend" "$PWD/backend/desktop.py"
echo
echo "Listo. El ejecutable esta en: ejecutable/dist/CalculadoraDistribuciones"
