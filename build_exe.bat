@echo off
setlocal EnableDelayedExpansion

set "SKIP_SMOKE=%SKIP_SMOKE%"
if "%SKIP_SMOKE%"=="" set "SKIP_SMOKE=0"
set "CI_MODE=%CI%"
if "%CI_MODE%"=="" set "CI_MODE=0"

echo ===============================================
echo COMPILANDO HEMODIALISIS HD-2026 EXE
echo ===============================================

:: Activar entorno virtual
call ".venv\Scripts\activate.bat"

:: Limpiar todo (incluyendo caché de PyInstaller)
echo.
echo Limpiando builds anteriores y caché...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "__pycache__" rmdir /s /q __pycache__
:: Borra caché global de PyInstaller (importante)
rmdir /s /q "%LOCALAPPDATA%\pyinstaller" 2>nul

echo.
echo Instalando/actualizando PyInstaller...
pip install -r requirements.txt
pip install --upgrade pyinstaller

if "%SKIP_SMOKE%"=="0" (
    echo.
    echo Ejecutando smoke test de arranque/cierre...
    set "CIATEQ_SMOKE_TEST_SECONDS=2"
    set "QT_QPA_PLATFORM=offscreen"
    ".venv\Scripts\python.exe" tests\smoke_startup.py
    if errorlevel 1 (
        echo Smoke test falló. Cancelando build.
        exit /b 1
    )
)

echo.
echo Compilando ejecutable LIMPIO...
pyinstaller --clean --noconfirm HemodialisisApp.spec

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

