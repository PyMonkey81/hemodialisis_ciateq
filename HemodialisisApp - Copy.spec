

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

BASE_DIR = Path(globals().get('SPEC', '.')).resolve().parent
ICON_FILE = BASE_DIR / 'src' / 'hemodialisis_ciateq' / 'resources' / 'images' / 'icon.ico'

a = Analysis(
    ['src/hemodialisis_ciateq/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/hemodialisis_ciateq/resources', 'resources'),
        ('src/hemodialisis_ciateq/config', 'config'),
    ],
    hiddenimports=['hemodialisis_ciateq', 'PySide6', 'pyqtgraph', 'serial', 'crcmod'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HemodialisisApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=str(ICON_FILE),
)
