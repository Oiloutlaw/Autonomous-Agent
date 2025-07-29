#!/usr/bin/env python3
"""
Simple test for the merged autonomous agent system
"""

import sys
import os

def test_merged_system():
    """Test the merged system"""
    print("🧪 Testing merged autonomous agent system...")
    
    try:
        print("📦 Testing imports...")
        import main
        print("✅ Main module imported successfully")
        print(f"✅ ElevenLabs available: {main.ELEVENLABS_AVAILABLE}")
        
        print("🗄️ Testing database initialization...")
        main.init_memory()
        main.init_video_db()
        
        if os.path.exists('agent_memory.db') and os.path.exists('video_logs.db'):
            print("✅ Databases initialized successfully")
        else:
            print("❌ Database files not created")
            return False
        
        print("🎭 Testing CrewAI functions...")
        main.create_stub_agents()
        print("✅ CrewAI stub agents created")
        
        print("🏗️ Testing infrastructure functions...")
        assert hasattr(main, 'load_secret'), "load_secret function missing"
        assert hasattr(main, 'monitor_rss'), "monitor_rss function missing"
        assert hasattr(main, 'discover_and_validate'), "discover_and_validate function missing"
        assert hasattr(main, 'run_pipeline'), "run_pipeline function missing"
        assert hasattr(main, 'run_pipeline_loop'), "run_pipeline_loop function missing"
        print("✅ All infrastructure functions available")
        
        print("🎉 All tests passed! Merged system is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_merged_system()
    sys.exit(0 if success else 1)
