# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Hidden imports for complex dependencies
hidden_imports = [
    'playwright',
    'playwright.sync_api',
    'crewai',
    'elevenlabs',
    'elevenlabs.client',
    'googleapiclient',
    'googleapiclient.discovery',
    'googleapiclient.http',
    'google.auth.transport.requests',
    'google.oauth2.credentials',
    'google_auth_oauthlib.flow',
    'azure.ai.inference',
    'azure.ai.inference.models',
    'azure.core.credentials',
    'stem',
    'stem.control',
    'praw',
    'feedparser',
    'faker',
    'stripe',
    'flask',
    'apscheduler',
    'apscheduler.schedulers.background',
    'sqlite3',
    'multiprocessing',
    'threading',
    'queue'
]

# Data files to include
datas = [
    ('.env.example', '.'),
    ('utils', 'utils'),
    ('agents', 'agents'),
    ('config', 'config'),
    ('infra', 'infra')
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
