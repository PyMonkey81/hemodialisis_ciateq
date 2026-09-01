@echo off
setlocal EnableDelayedExpansion

pushd "%~dp0"

set "SKIP_SMOKE=%SKIP_SMOKE%"
if "%SKIP_SMOKE%"=="" set "SKIP_SMOKE=0"
set "CI_MODE=%CI%"
if "%CI_MODE%"=="" set "CI_MODE=0"

echo ===============================================
echo COMPILANDO HEMODIALISIS HD-2026 EXE
echo ===============================================

:: Activar entorno virtual
set "PYTHON_EXE="
if exist ".venv-1\Scripts\activate.bat" (
    call ".venv-1\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

if defined VIRTUAL_ENV set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"

:: Limpiar todo (incluyendo caché de PyInstaller)
echo.
echo Limpiando builds anteriores y caché...
if exist "dist" (
    rmdir /s /q dist 2>nul
    if exist "dist" (
        echo ERROR: No se pudo limpiar dist\ porque hay archivos en uso.
        echo Cierra la aplicacion/Explorer que tenga abierto algun .exe en dist\ e intenta de nuevo.
        popd
        exit /b 1
    )
)
if exist "build" rmdir /s /q build
if exist "__pycache__" rmdir /s /q __pycache__
:: Borra caché global de PyInstaller (importante)
rmdir /s /q "%LOCALAPPDATA%\pyinstaller" 2>nul

echo.
echo Instalando/actualizando PyInstaller...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias.
    popd
    exit /b 1
)

if "%SKIP_SMOKE%"=="0" (
    echo.
    echo Ejecutando smoke test de arranque/cierre...
    set "CIATEQ_SMOKE_TEST_SECONDS=2"
    set "QT_QPA_PLATFORM=offscreen"
    if defined WINDIR set "QT_QPA_FONTDIR=%WINDIR%\Fonts"
    "%PYTHON_EXE%" tests\smoke_startup.py
    if errorlevel 1 (
        echo Smoke test falló. Cancelando build.
        popd
        exit /b 1
    )
)

echo.
echo Compilando ejecutable LIMPIO...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm HemodialisisApp.spec
if errorlevel 1 (
    echo ERROR: PyInstaller no pudo generar el ejecutable.
    popd
    exit /b 1
)

if exist "config" (
    xcopy "config" "dist\config" /E /I /Y /Q >nul
    if errorlevel 1 (
        echo ERROR: No se pudo copiar la configuracion a dist\config\.
        popd
        exit /b 1
    )
)

echo.
echo ===============================================
echo COMPILACION FINALIZADA
echo ===============================================

for %%F in (dist\*.exe) do set LAST_EXE=%%~nxF
if defined LAST_EXE (
    echo Ejecutable generado en: dist\!LAST_EXE!
) else (
    echo No se encontro ejecutable en dist\
)

if exist "build\build_history.csv" (
    echo Registro actualizado en: build\build_history.csv
)

echo.
if "%CI_MODE%"=="0" pause

popd

