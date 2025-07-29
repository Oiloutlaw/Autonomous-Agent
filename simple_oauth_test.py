#!/usr/bin/env python3
"""Simple test to verify OAuth2 implementation works"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔍 Testing OAuth2 Implementation")
    
    if not os.path.exists('client_secrets.json'):
        print("❌ client_secrets.json not found")
        return False
    
    try:
        with open('client_secrets.json', 'r') as f:
            creds = json.load(f)
        
        if 'web' in creds:
            print("⚠️  Converting web format to installed format...")
            web_creds = creds['web']
            installed_creds = {
                'installed': {
                    'client_id': web_creds['client_id'],
                    'client_secret': web_creds['client_secret'],
                    'auth_uri': web_creds['auth_uri'],
                    'token_uri': web_creds['token_uri'],
                    'auth_provider_x509_cert_url': web_creds.get('auth_provider_x509_cert_url'),
                    'redirect_uris': ['http://localhost']
                }
            }
            with open('client_secrets.json', 'w') as f:
                json.dump(installed_creds, f, indent=2)
            print("✅ Converted to installed format")
        elif 'installed' in creds:
            print("✅ Already in installed format")
        else:
            print("❌ Unknown format")
            return False
            
    except Exception as e:
        print(f"❌ Error processing credentials: {e}")
        return False
    
    try:
        from main import get_youtube_service
        print("✅ get_youtube_service imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("✅ OAuth2 implementation ready for testing")
    print("Note: First run will require browser authentication")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
