# Despliegue Linux (Ubuntu/CachyOS)

## 1. Requisitos

- Python 3.11+
- Entorno virtual `.venv`
- Acceso a puertos seriales USB (`/dev/ttyUSB*`, `/dev/ttyACM*`)

## 2. Permisos serial

Agregar usuario a grupo serial y volver a iniciar sesión:

```bash
sudo usermod -aG dialout "$USER"
# En algunas distros puede ser uucp en lugar de dialout
sudo usermod -aG uucp "$USER"
```

Verificar grupos actuales:

```bash
id
```

## 3. Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Smoke test de arranque/cierre

```bash
export QT_QPA_PLATFORM=offscreen
export CIATEQ_SMOKE_TEST_SECONDS=2
.venv/bin/python tests/smoke_startup.py
```

## 5. Build

```bash
bash compile_linux.sh
```

## 6. Diagnóstico rápido serial

```bash
python - <<'PY'
import serial.tools.list_ports as p
for x in p.comports():
    print(x.device, x.description, x.manufacturer)
PY
```

Si aparece `Permission denied`, revisar grupos (`dialout`/`uucp`) y reglas udev.
