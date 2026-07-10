# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('app/database/MSI_database_V1.0.xlsx', 'Resources/seed'),
        ('app/style.css', 'Resources')],
    hiddenimports=['pkg_resources.extern',
    'scipy._lib.array_api_compat.numpy.fft'],
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
    [],
    exclude_binaries=True,
    name='LipidQMap',
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
    name='LipidQMap',
)
app = BUNDLE(
    coll,
    name='LipidQMap.app',
    icon='resources/icons/app.icns',
    bundle_identifier='com.swinnenlab.lipidqmap',
)
