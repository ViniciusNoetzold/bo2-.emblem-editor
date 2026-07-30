# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\BO2 Emblem Studio\\src\\bo2_emblem\\gui\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\BO2 Emblem Studio\\research\\bo2-emblem-toolkit\\reference_shapes', 'bo2_emblem/reference_shapes')],
    hiddenimports=['aiohttp', 'requests'],
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
    name='BO2_Emblem_Studio',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BO2_Emblem_Studio',
)
