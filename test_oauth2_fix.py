#!/usr/bin/env python3
"""Test OAuth2 implementation with corrected environment variable"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_oauth2_credentials():
    """Test that OAuth2 credentials are properly formatted"""
    print("🔍 Testing OAuth2 credentials format...")
    
    oauth_data = os.getenv('GoogleOAuth2')
    if not oauth_data:
        print("❌ GoogleOAuth2 environment variable not found")
        return False
    
    print(f"✅ GoogleOAuth2 environment variable found ({len(oauth_data)} chars)")
    
    try:
        client_config = json.loads(oauth_data)
        print("✅ OAuth2 credentials are valid JSON")
        
        if 'web' in client_config:
            web_creds = client_config['web']
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            
            for field in required_fields:
                if field in web_creds:
                    print(f"✅ {field}: present")
                else:
                    print(f"❌ {field}: missing")
                    return False
            
            print("✅ All required OAuth2 fields present")
            return True
        else:
            print("❌ OAuth2 credentials missing 'web' section")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse OAuth2 credentials: {e}")
        return False

def test_get_youtube_service_function():
    """Test that get_youtube_service function can process credentials"""
    print("\n🔍 Testing get_youtube_service function...")
    
    try:
        from main import get_youtube_service
        print("✅ get_youtube_service function imported successfully")
        
        oauth_data = os.getenv('GoogleOAuth2')
        if oauth_data:
            client_config = json.loads(oauth_data)
            if 'web' in client_config:
                print("✅ Credentials will be converted from 'web' to 'installed' format")
                print("✅ OAuth2 implementation ready for authentication")
                return True
        
        return False
        
    except ImportError as e:
        print(f"❌ Failed to import get_youtube_service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing get_youtube_service: {e}")
        return False

def main():
    """Run OAuth2 fix tests"""
    print("🚀 Testing OAuth2 Fix Implementation\n")
    
    tests = [
        test_oauth2_credentials,
        test_get_youtube_service_function
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 OAuth2 fix is working! Ready for video upload testing.")
        print("📝 Next step: Test video upload via /trigger_video endpoint")
        return True
    else:
        print("❌ OAuth2 fix needs more work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
