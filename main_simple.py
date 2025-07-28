#!/usr/bin/env python3
"""
Simplified main entry point for testing PyInstaller build without CrewAI dependencies
"""

import os
import sys
import json
import threading
import multiprocessing
from flask import Flask, jsonify

def create_flask_app():
    """Create a simple Flask app for testing"""
    app = Flask(__name__)
    
    @app.route('/status')
    def status():
        return jsonify({
            'status': 'running',
            'message': 'Autonomous Agent executable is working!',
            'python_version': sys.version,
            'platform': sys.platform
        })
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'Autonomous Agent Test Server',
            'endpoints': ['/status', '/']
        })
    
    return app

def main():
    """Main entry point for simplified autonomous agent"""
    print("🚀 Starting Autonomous Agent (Simplified Version)")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    app = create_flask_app()
    
    print("\n✅ Flask server starting on http://localhost:8000")
    print("📊 Status endpoint: http://localhost:8000/status")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=8000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
