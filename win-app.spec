# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/database/MSI_database_V1.0.xlsx', 'Resources/seed'),
        ('app/style.css', 'Resources'),
    ],
    hiddenimports=['pkg_resources.extern'],
    hookspath=['pyinstaller/'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# One-folder build:
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LipidQMap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/icons/app.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LipidQMap'
)
