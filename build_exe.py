#!/usr/bin/env python3
"""
Build script for creating Windows executable of Autonomous Agent
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required build dependencies are installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("✅ PyInstaller installed")

def clean_build_dirs():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        'build_exe.spec'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build completed successfully!")
        
        exe_path = Path('dist/AutonomousAgent.exe')
        if exe_path.exists():
            size = exe_path.stat().st_size
            print(f"📦 Executable created: {exe_path} ({size:,} bytes)")
            return True
        else:
            print("❌ Executable not found in dist/")
            return False
    else:
        print("❌ Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

def main():
    """Main build function"""
    print("🚀 Building Autonomous Agent Executable")
    print("=" * 50)
    
    check_dependencies()
    clean_build_dirs()
    
    if build_executable():
        print("\n✅ Build process completed successfully!")
        print("📁 Executable location: dist/AutonomousAgent.exe")
        print("\nNext steps:")
        print("1. Test the executable: dist/AutonomousAgent.exe")
        print("2. Ensure .env file is in the same directory")
        print("3. Verify all API keys are configured")
    else:
        print("\n❌ Build process failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
