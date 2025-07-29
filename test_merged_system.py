#!/usr/bin/env python3
"""
Test script for the merged autonomous agent system
"""

import sys
import os
import time
import requests
import sqlite3

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    try:
        sys.path.append('.')
        import main
        print("✅ All imports successful")
        print(f"✅ ElevenLabs available: {main.ELEVENLABS_AVAILABLE}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_initialization():
    """Test database initialization"""
    print("🧪 Testing database initialization...")
    try:
        from main import init_memory, init_video_db
        init_memory()
        init_video_db()
        
        if os.path.exists('agent_memory.db') and os.path.exists('video_logs.db'):
            print("✅ Databases initialized successfully")
            return True
        else:
            print("❌ Database files not created")
            return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_crewai_functions():
    """Test CrewAI functions exist"""
    print("🧪 Testing CrewAI functions...")
    try:
        import main
        main.create_stub_agents()
        print("✅ CrewAI functions available")
        return True
    except Exception as e:
        print(f"❌ CrewAI functions failed: {e}")
        return False

def test_infrastructure_functions():
    """Test infrastructure functions exist"""
    print("🧪 Testing infrastructure functions...")
    try:
        import main
        assert hasattr(main, 'load_secret')
        assert hasattr(main, 'monitor_rss')
        assert hasattr(main, 'discover_and_validate')
        print("✅ Infrastructure functions available")
        return True
    except Exception as e:
        print(f"❌ Infrastructure functions failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Merged Autonomous Agent System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_initialization,
        test_crewai_functions,
        test_infrastructure_functions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! Merged system is ready.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
