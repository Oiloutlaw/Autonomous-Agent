#!/usr/bin/env python3
"""Test script to verify environment variable access in daemon threads"""

import os
import threading
import time

def test_env_in_regular_thread():
    """Test environment variable access in regular thread"""
    print("🔍 Testing environment variable in regular thread...")
    oauth_data = os.getenv('GoogleOAuth2')
    if oauth_data:
        print(f"✅ Regular thread: Found GoogleOAuth2 ({len(oauth_data)} chars)")
        return True
    else:
        print("❌ Regular thread: GoogleOAuth2 not found")
        return False

def test_env_in_daemon_thread():
    """Test environment variable access in daemon thread"""
    print("🔍 Testing environment variable in daemon thread...")
    oauth_data = os.getenv('GoogleOAuth2')
    if oauth_data:
        print(f"✅ Daemon thread: Found GoogleOAuth2 ({len(oauth_data)} chars)")
        return True
    else:
        print("❌ Daemon thread: GoogleOAuth2 not found")
        return False

def test_load_secret_in_daemon_thread():
    """Test load_secret function in daemon thread"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from main import load_secret
    
    print("🔍 Testing load_secret function in daemon thread...")
    oauth_data = load_secret('GoogleOAuth2')
    if oauth_data:
        print(f"✅ Daemon thread load_secret: Found GoogleOAuth2 ({len(oauth_data)} chars)")
        return True
    else:
        print("❌ Daemon thread load_secret: GoogleOAuth2 not found")
        return False

def main():
    print("🚀 Testing Environment Variable Access in Threads\n")
    
    print("1. Testing in main thread:")
    main_result = test_env_in_regular_thread()
    print()
    
    print("2. Testing in regular thread:")
    regular_result = [False]
    def regular_thread_test():
        regular_result[0] = test_env_in_regular_thread()
    
    thread = threading.Thread(target=regular_thread_test)
    thread.start()
    thread.join()
    print()
    
    print("3. Testing in daemon thread:")
    daemon_result = [False]
    def daemon_thread_test():
        daemon_result[0] = test_env_in_daemon_thread()
    
    daemon_thread = threading.Thread(target=daemon_thread_test, daemon=True)
    daemon_thread.start()
    daemon_thread.join()
    print()
    
    print("4. Testing load_secret in daemon thread:")
    load_secret_result = [False]
    def load_secret_daemon_test():
        load_secret_result[0] = test_load_secret_in_daemon_thread()
    
    load_secret_thread = threading.Thread(target=load_secret_daemon_test, daemon=True)
    load_secret_thread.start()
    load_secret_thread.join()
    print()
    
    print("📊 Results Summary:")
    print(f"   Main thread: {'✅' if main_result else '❌'}")
    print(f"   Regular thread: {'✅' if regular_result[0] else '❌'}")
    print(f"   Daemon thread (os.getenv): {'✅' if daemon_result[0] else '❌'}")
    print(f"   Daemon thread (load_secret): {'✅' if load_secret_result[0] else '❌'}")
    
    if load_secret_result[0]:
        print("\n🎉 load_secret function works in daemon threads!")
        print("✅ Fix should resolve the OAuth2 environment variable issue")
    else:
        print("\n❌ load_secret function also fails in daemon threads")
        print("⚠️  May need alternative solution")

if __name__ == "__main__":
    main()
