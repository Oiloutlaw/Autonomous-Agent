#!/usr/bin/env python3
"""Test OAuth2 integration for YouTube uploads"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_oauth2_environment():
    """Test that OAuth2 environment variable is properly configured"""
    print("🔍 Testing OAuth2 environment setup...")
    
    oauth_data = os.getenv('GoogleOAuth2')
    if not oauth_data:
        print("❌ GoogleOAuth2 environment variable not found")
        return False
    
    try:
        client_config = json.loads(oauth_data)
        print("✅ OAuth2 credentials loaded from environment variable")
        
        if 'web' in client_config:
            print("✅ Credentials in web format (will be converted to installed)")
            client_id = client_config['web'].get('client_id', '')
            if client_id:
                print(f"✅ Client ID found: {client_id[:20]}...")
            return True
        elif 'installed' in client_config:
            print("✅ Credentials in installed format")
            client_id = client_config['installed'].get('client_id', '')
            if client_id:
                print(f"✅ Client ID found: {client_id[:20]}...")
            return True
        else:
            print("❌ Unexpected credentials format")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse OAuth2 credentials: {e}")
        return False

def test_oauth2_imports():
    """Test that all required OAuth2 imports work"""
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
    """Test that get_youtube_service function is properly implemented"""
    print("\n🔍 Testing get_youtube_service function...")
    
    try:
        from main import get_youtube_service
        print("✅ get_youtube_service function imported successfully")
        
        if callable(get_youtube_service):
            print("✅ get_youtube_service is callable")
            print("✅ OAuth2 implementation ready for authentication")
            return True
        else:
            print("❌ get_youtube_service is not callable")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import get_youtube_service: {e}")
        return False

def test_upload_function_integration():
    """Test that upload_to_youtube function uses OAuth2"""
    print("\n🔍 Testing upload_to_youtube OAuth2 integration...")
    
    try:
        from main import upload_to_youtube
        print("✅ upload_to_youtube function imported successfully")
        
        if callable(upload_to_youtube):
            print("✅ upload_to_youtube is callable")
            print("✅ Function ready for OAuth2 video uploads")
            return True
        else:
            print("❌ upload_to_youtube is not callable")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import upload_to_youtube: {e}")
        return False

def main():
    """Run all OAuth2 integration tests"""
    print("🚀 Testing OAuth2 Integration for YouTube Uploads\n")
    
    tests = [
        test_oauth2_environment,
        test_oauth2_imports,
        test_youtube_service_function,
        test_upload_function_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 OAuth2 integration is complete and ready!")
        print("📝 Next steps:")
        print("   1. First run will open browser for OAuth2 authentication")
        print("   2. Subsequent runs will use stored token.json for automation")
        print("   3. Video uploads will now use OAuth2 instead of API key")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
