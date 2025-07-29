#!/usr/bin/env python3
"""Test accessing GoogleOAuth2 secret through different methods"""

import os
import json

def test_env_var_access():
    """Test accessing GoogleOAuth2 via environment variable"""
    print("🔍 Testing environment variable access...")
    oauth_data = os.getenv('GoogleOAuth2')
    if oauth_data:
        print(f"✅ Environment variable found: {len(oauth_data)} chars")
        print(f"📝 Content preview: {oauth_data[:50]}...")
        try:
            json.loads(oauth_data)
            print("✅ Environment variable contains valid JSON")
            return True
        except json.JSONDecodeError:
            print("❌ Environment variable contains invalid JSON")
            return False
    else:
        print("❌ Environment variable not found")
        return False

def test_load_secret_access():
    """Test accessing GoogleOAuth2 via load_secret function"""
    print("\n🔍 Testing load_secret function access...")
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from main import load_secret
        
        oauth_data = load_secret('GoogleOAuth2')
        if oauth_data:
            print(f"✅ load_secret found data: {len(oauth_data)} chars")
            print(f"📝 Content preview: {oauth_data[:50]}...")
            try:
                json.loads(oauth_data)
                print("✅ load_secret data contains valid JSON")
                return True
            except json.JSONDecodeError:
                print("❌ load_secret data contains invalid JSON")
                return False
        else:
            print("❌ load_secret returned None")
            return False
    except Exception as e:
        print(f"❌ Error with load_secret: {e}")
        return False

def main():
    print("🚀 Testing Secret Access Methods\n")
    
    env_success = test_env_var_access()
    load_secret_success = test_load_secret_access()
    
    print(f"\n📊 Results:")
    print(f"   Environment variable: {'✅' if env_success else '❌'}")
    print(f"   load_secret function: {'✅' if load_secret_success else '❌'}")
    
    if load_secret_success:
        print("\n🎉 load_secret function has access to valid JSON credentials!")
        print("✅ OAuth2 implementation should work with load_secret")
    elif env_success:
        print("\n🎉 Environment variable has valid JSON credentials!")
        print("✅ OAuth2 implementation should work with os.getenv")
    else:
        print("\n❌ Neither method has valid JSON credentials")
        print("⚠️  Need to wait for user to restart application with correct environment variable")

if __name__ == "__main__":
    main()
