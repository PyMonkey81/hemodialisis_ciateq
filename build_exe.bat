@echo off
setlocal EnableDelayedExpansion

echo ===============================================
echo       COMPILANDO HEMODIALISIS HD-2000 EXE
echo ===============================================

:: Activar entorno virtual (ajusta la ruta si es necesario)
call "C:\Users\miguel.espinoza\Documents\Hemodialisis_Python\venv\Scripts\activate.bat"

:: Limpiar builds anteriores (opcional pero recomendado)
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec

echo.
echo Instalando/actualizando PyInstaller...
pip install --upgrade pyinstaller

echo.
echo Compilando ejecutable...
pyinstaller --onefile ^
  --windowed ^
  --icon=resources/icons/hemodialisis.ico ^
  --add-data "resources;resources" ^
  --add-data "gui;gui" ^
  --add-data "core;core" ^
  --add-data "connection;connection" ^
  --add-data "logic;logic" ^
  --name "Hemodialisis_HD2000" ^
  --hidden-import PySide6.QtWidgets ^
  --hidden-import PySide6.QtCore ^
  --hidden-import PySide6.QtGui ^
  --hidden-import PySide6.QtCharts ^
  main.py

echo.
echo ===============================================
echo       COMPILACION FINALIZADA
echo ===============================================
echo Ejecutable generado en: dist\Hemodialisis_HD2000.exe
echo.

pause