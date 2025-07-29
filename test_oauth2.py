#!/usr/bin/env python3
"""Test script to verify OAuth2 implementation for YouTube uploads"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_oauth2_setup():
    """Test that OAuth2 credentials are properly configured"""
    print("🔍 Testing OAuth2 setup...")
    
    oauth_creds = os.getenv('GoogleOAuth2')
    if not oauth_creds:
        print("❌ GoogleOAuth2 environment variable not found")
        return False
    
    try:
        creds_data = json.loads(oauth_creds)
        print("✅ OAuth2 credentials loaded from environment variable")
        
        if 'installed' in creds_data:
            print("✅ Credentials have 'installed' format (Desktop Application)")
            client_id = creds_data['installed'].get('client_id', '')
            if client_id:
                print(f"✅ Client ID found: {client_id[:20]}...")
            return True
        elif 'web' in creds_data:
            print("⚠️  Credentials have 'web' format - may need conversion")
            return True
        else:
            print("❌ Unexpected credentials format")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse OAuth2 credentials: {e}")
        return False

def test_oauth2_imports():
    """Test that all required OAuth2 imports are available"""
    print("\n🔍 Testing OAuth2 imports...")
    
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        print("✅ All OAuth2 imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_youtube_service_function():
    """Test that get_youtube_service function exists and is callable"""
    print("\n🔍 Testing get_youtube_service function...")
    
    try:
        from main import get_youtube_service
        print("✅ get_youtube_service function imported successfully")
        
        if callable(get_youtube_service):
            print("✅ get_youtube_service is callable")
            return True
        else:
            print("❌ get_youtube_service is not callable")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import get_youtube_service: {e}")
        return False

def main():
    """Run all OAuth2 tests"""
    print("🚀 Starting OAuth2 Implementation Tests\n")
    
    tests = [
        test_oauth2_setup,
        test_oauth2_imports,
        test_youtube_service_function
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OAuth2 tests passed! Implementation is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
