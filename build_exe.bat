@echo off
setlocal EnableDelayedExpansion

echo ===============================================
echo       COMPILANDO HEMODIALISIS HD-2026 EXE
echo ===============================================

:: Activar entorno virtual local del proyecto
call ".venv\Scripts\activate.bat"

:: Limpiar builds anteriores (opcional pero recomendado)
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo Instalando/actualizando PyInstaller...
pip install --upgrade pyinstaller

echo.
echo Compilando ejecutable...
pyinstaller --noconfirm HemodialisisApp.spec

echo.
echo ===============================================
echo       COMPILACION FINALIZADA
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

pause