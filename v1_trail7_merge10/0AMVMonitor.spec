# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['band_monitor.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/peiyilu/AppData/Local/Programs/Python/Python312/Lib/site-packages/akshare/file_fold', 'akshare/file_fold'), ('0AMV.ico', '.')],
    hiddenimports=[],
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
    a.datas,
    [],
    name='0AMVMonitor',
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
    icon=['C:\\Users\\peiyilu\\AppData\\Local\\Temp\\0AMV_bmp.ico'],
)
