#!/usr/bin/env python3
"""Test script to verify platform_utils functionality"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_platform_utils():
    """Test platform utilities import and basic functionality"""
    try:
        from utils.platform_utils import (
            get_platform, is_windows, is_linux, is_macos,
            get_secrets_dir, get_home_dir, get_repo_dir,
            normalize_path, ensure_directory
        )
        
        print("✅ Platform utils import successful")
        print(f"Platform: {get_platform()}")
        print(f"Windows: {is_windows()}")
        print(f"Linux: {is_linux()}")
        print(f"macOS: {is_macos()}")
        print(f"Secrets dir: {get_secrets_dir()}")
        print(f"Home dir: {get_home_dir()}")
        print(f"Repo dir: {get_repo_dir()}")
        
        test_path = normalize_path("test/path")
        print(f"Normalized path: {test_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Platform utils test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_platform_utils()
    sys.exit(0 if success else 1)
