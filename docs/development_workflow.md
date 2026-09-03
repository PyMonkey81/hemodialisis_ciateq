# Flujo de trabajo multiplataforma

La aplicación se desarrolla y se valida en Ubuntu Desktop, pero el ejecutable
oficial para los equipos actuales se genera en Windows. Ubuntu Server con Cage
ejecutará el artefacto Linux generado en Ubuntu.

## Plataformas soportadas

- Windows 10/11: operación actual y compilación del `.exe`.
- Ubuntu Desktop: desarrollo, pruebas y compilación Linux.
- Ubuntu Server + Cage/Wayland: operación final del HMI.
- Python soportado: `>=3.11,<3.13`.

Cada sistema operativo necesita su propio entorno virtual y sus propias
dependencias. No se debe copiar `.venv`, `build` o `dist` entre Windows y Linux.

## Preparar Ubuntu Desktop

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    build-essential libgl1 libegl1 libxkbcommon0 libfontconfig1 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Validar antes de trabajar:

```bash
python --version
QT_QPA_PLATFORM=offscreen CIATEQ_SMOKE_TEST_SECONDS=2 \
    python tests/smoke_startup.py
python -m unittest discover -s tests -p 'test*.py' -v
```

Para probar la ventana en el escritorio, ejecutar con la sesión gráfica
Wayland activa. El programa usa Wayland con fallback a XCB en Linux.

## Preparar Ubuntu Server + Cage

El usuario que ejecute Cage debe tener una sesión gráfica válida y acceso al
dispositivo DRM. La variable `XDG_RUNTIME_DIR` debe existir y Cage debe crear
el socket indicado por `WAYLAND_DISPLAY`.

Dar acceso a los adaptadores seriales:

```bash
sudo usermod -aG dialout "$USER"
```

Cerrar la sesión y volver a entrar después de cambiar el grupo. Validar:

```bash
id
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
python -c "import serial.tools.list_ports as p; print([x.device for x in p.comports()])"
```

Antes de arrancar Cage, comprobar el entorno Wayland:

```bash
test -n "$XDG_RUNTIME_DIR"
test -S "$XDG_RUNTIME_DIR/${WAYLAND_DISPLAY:-wayland-0}"
```

El ejecutable debe arrancarse dentro de Cage, no desde una consola SSH sin
sesión gráfica. Mantener una copia de `config/` junto al ejecutable para que
los puertos y feature flags sean editables sin recompilar.

## Cambios y releases Windows

1. Desarrollar y probar el cambio en Ubuntu Desktop.
2. Ejecutar el smoke test y las pruebas `unittest` antes de transferirlo.
3. Entrar a Windows, actualizar el mismo commit y activar `.venv`.
4. Ejecutar `build_exe.bat` desde una consola de Windows.
5. Conservar el `.exe` generado junto con su carpeta `config/`.
6. Probar el `.exe` en Windows antes de distribuirlo.

El script Windows ejecuta automáticamente el smoke test, PyInstaller y copia
`config/`. Para una compilación sin prueba previa, usar
`SKIP_SMOKE=1 build_exe.bat`.

## Cambios y releases Linux

Desde Ubuntu Desktop:

```bash
SKIP_SMOKE=0 bash compile_linux.sh
```

El script ejecuta el smoke test, compila el binario y copia `config/` dentro de
`dist/`. No compilar un ejecutable Linux desde Windows ni uno Windows desde
Linux: PyInstaller no es un compilador cruzado.

## Criterio mínimo antes de entregar

- El commit está identificado y el árbol de trabajo no contiene cambios
  accidentales.
- `python -m py_compile main.py` pasa.
- El smoke test de Qt pasa en modo `offscreen`.
- Las pruebas `unittest` pasan.
- Se prueba la pantalla de puertos y el botón `Aplicar Cambios`.
- Se valida detección de los puertos seriales disponibles en la plataforma.
- El build correspondiente genera el artefacto y conserva `config/`.
