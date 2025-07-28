# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Minimal hidden imports for testing - excluding CrewAI for now
hidden_imports = [
    'flask',
    'sqlite3',
    'threading',
    'multiprocessing',
    'queue',
    'requests',
    'json',
    'os',
    'sys'
]

a = Analysis(
    ['main_simple.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.env.example', '.'),
        ('/home/ubuntu/.pyenv/versions/3.12.8/lib/python3.12/site-packages/crewai/translations', 'crewai/utilities/../translations'),
        ('utils', 'utils'),
        ('agents', 'agents'),
        ('config', 'config'),
        ('infra', 'infra')
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='AutonomousAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
