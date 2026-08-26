# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/database/MSI_database_basic_V1.2.xlsx', 'Resources/seed'),
        ('app/database/MSI_database_extensive_V1.2.xlsx', 'Resources/seed'),
        ('app/style.css', 'Resources'),
    ],
    hiddenimports=[
    'pkg_resources.extern',
    'scipy._lib.array_api_compat.numpy.fft',
    ],
    hookspath=['pyinstaller/'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LipidQMap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/icons/app.ico',
    onefile=True,
    runtime_tmpdir=None
)
