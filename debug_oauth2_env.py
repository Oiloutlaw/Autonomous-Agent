#!/usr/bin/env python3
"""Debug OAuth2 environment variable content"""

import os
import json

def debug_oauth2_env():
    """Debug the actual content of GoogleOAuth2 environment variable"""
    print("🔍 Debugging GoogleOAuth2 environment variable...")
    
    oauth_data = os.getenv('GoogleOAuth2')
    if not oauth_data:
        print("❌ GoogleOAuth2 environment variable not found")
        return
    
    print(f"✅ GoogleOAuth2 found, length: {len(oauth_data)} characters")
    print(f"📝 First 100 characters: {repr(oauth_data[:100])}")
    print(f"📝 Last 50 characters: {repr(oauth_data[-50:])}")
    
    try:
        client_config = json.loads(oauth_data)
        print("✅ JSON parsing successful!")
        print(f"📊 Keys: {list(client_config.keys())}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📍 Error position: {e.pos}")
        if e.pos < len(oauth_data):
            print(f"📝 Character at error position: {repr(oauth_data[e.pos])}")
            print(f"📝 Context around error: {repr(oauth_data[max(0, e.pos-10):e.pos+10])}")

if __name__ == "__main__":
    debug_oauth2_env()
