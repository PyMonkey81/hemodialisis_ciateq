#!/bin/bash
set -euo pipefail

SKIP_SMOKE="${SKIP_SMOKE:-0}"

echo "==============================================="
echo "COMPILANDO HEMODIALISIS HD-2026 (LINUX)"
echo "==============================================="

# Activar entorno virtual (ajustado a la ruta de Linux)
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Error: No se encontró el entorno virtual .venv"
    exit 1
fi

# Limpiar todo
echo -e "\nLimpiando builds anteriores y caché..."
rm -rf dist build __pycache__
rm -rf ~/.cache/pyinstaller

echo -e "\nInstalando/actualizando PyInstaller..."
pip install -r requirements.txt
pip install --upgrade pyinstaller

if [[ "$SKIP_SMOKE" == "0" ]]; then
    echo -e "\nEjecutando smoke test de arranque/cierre..."
    export CIATEQ_SMOKE_TEST_SECONDS="2"
    export QT_QPA_PLATFORM="offscreen"
    .venv/bin/python tests/smoke_startup.py
fi

echo -e "\nCompilando ejecutable LIMPIO..."
# Usamos el archivo .spec que ya tienes
pyinstaller --clean --noconfirm HemodialisisApp.spec

echo -e "\n==============================================="
echo "COMPILACION FINALIZADA"
echo "==============================================="

# Buscar el binario generado (en Linux no tiene extensión .exe)
LAST_BIN=$(find dist/ -maxdepth 1 -type f -not -name "*.spec" | head -n 1)

if [ -n "$LAST_BIN" ]; then
    echo "Ejecutable generado en: $LAST_BIN"
    # Dar permisos de ejecución automáticamente
    chmod +x "$LAST_BIN"
else
    echo "No se encontró el ejecutable en dist/"
fi

if [ -f "build/build_history.csv" ]; then
    echo "Registro actualizado en: build/build_history.csv"
fi
    