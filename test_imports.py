#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
import traceback


def test_import(module_name, description):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"✅ {description}: Import successful")
        return True
    except Exception as e:
        print(f"❌ {description}: Import failed - {e}")
        traceback.print_exc()
        return False


def main():
    print("🧪 Testing Enhanced Autonomous Agent Imports...")
    print("=" * 50)

    success_count = 0
    total_tests = 0

    tests = [
        ("openai", "OpenAI API"),
        ("flask", "Flask web framework"),
        ("redis", "Redis client"),
        ("docker", "Docker client"),
        ("crewai", "CrewAI framework"),
        ("sqlite3", "SQLite database"),
        ("threading", "Threading support"),
        ("multiprocessing", "Multiprocessing support"),
        ("json", "JSON handling"),
        ("datetime", "DateTime utilities"),
        ("logging", "Logging framework"),
    ]

    for module, description in tests:
        total_tests += 1
        if test_import(module, description):
            success_count += 1

    print("=" * 50)

    custom_tests = [
        ("replication_manager", "Replication Manager"),
        ("revenue_engines", "Revenue Engines"),
        ("enhanced_launcher", "Enhanced Launcher"),
    ]

    for module, description in custom_tests:
        total_tests += 1
        if test_import(module, description):
            success_count += 1

    print("=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} imports successful")

    if success_count == total_tests:
        print("🎉 All imports working correctly!")
        return 0
    else:
        print("⚠️ Some imports failed - check dependencies")
        return 1


if __name__ == "__main__":
    sys.exit(main())
