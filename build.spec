# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/bo2_emblem/gui/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('database/shapes.json', 'database'),
        ('src/bo2_emblem/gui', 'bo2_emblem/gui'),
        ('research/bo2-emblem-toolkit/reference_shapes', 'reference_shapes'),
    ],
    hiddenimports=[
        'bo2_emblem.parser',
        'bo2_emblem.serializer',
        'bo2_emblem.renderer',
        'bo2_emblem.importer',
        'bo2_emblem.exporter',
        'bo2_emblem.optimizer',
        'bo2_emblem.ai',
        'bo2_emblem.shape_map',
        'bo2_emblem.gui.editor',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PIL',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scipy', 'distutils', 'distutils.util', 'setuptools', 'setuptools._vendor.jaraco', 'jaraco', 'packaging'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BO2 Emblem Studio',
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
    icon='assets/icons/emblem.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BO2 Emblem Studio',
)