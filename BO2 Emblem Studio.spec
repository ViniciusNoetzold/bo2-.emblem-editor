# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\bo2_emblem\\gui\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('database', 'database'), ('research/bo2-emblem-toolkit/reference_shapes', 'reference_shapes')],
    hiddenimports=['bo2_emblem.gui.editor', 'bo2_emblem.parser', 'bo2_emblem.serializer', 'bo2_emblem.renderer', 'bo2_emblem.importer', 'bo2_emblem.exporter', 'bo2_emblem.optimizer', 'bo2_emblem.ai', 'bo2_emblem.shape_map', 'PIL', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'numpy', 'scipy', 'cairosvg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['black', 'mypy', 'pytest', 'pylint', 'flake8', 'cairocffi', 'tinycss2', 'cssselect2', 'webencodings', 'defusedxml', 'ast_serialize', 'librt', 'platformdirs', 'pytokens', 'jaraco', 'more_itertools', 'zipp', 'backports', 'tomli'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BO2 Emblem Studio',
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
    icon=['src\\bo2_emblem\\gui\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BO2 Emblem Studio',
)
