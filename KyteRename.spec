# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets')]
binaries = []
hiddenimports = [
    'PIL',
    'PIL.ExifTags',
    'mutagen',
    'mutagen.mp3',
    'mutagen.id3',
    'mutagen.flac',
    'pypinyin',
    'PySide6.QtNetwork',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets'
]

# 收集 mutagen 與 pypinyin 內部動態資源
tmp_pypinyin = collect_all('pypinyin')
datas += tmp_pypinyin[0]; binaries += tmp_pypinyin[1]; hiddenimports += tmp_pypinyin[2]

tmp_mutagen = collect_all('mutagen')
datas += tmp_mutagen[0]; binaries += tmp_mutagen[1]; hiddenimports += tmp_mutagen[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='KyteRename',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KyteRename',
)
