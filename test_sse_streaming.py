"""
Test script for SSE streaming functionality
Verifies that the chatbot service is working correctly with SSE
"""

import requests
import json
import time

SERVICE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        data = response.json()
        
        print(f"  Status: {data.get('status')}")
        print(f"  Chatbot Initialized: {data.get('chatbot_initialized')}")
        print(f"  Pipeline Warmed: {data.get('pipeline_warmed')}")
        
        if data.get('status') == 'ok' and data.get('pipeline_warmed'):
            print("✅ Health check passed\n")
            return True
        else:
            print("⚠️  Service not fully ready\n")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_sse_streaming():
    """Test SSE streaming endpoint"""
    print("🔍 Testing SSE streaming...")
    
    try:
        # Send query
        response = requests.post(
            f"{SERVICE_URL}/query",
            json={
                "user_id": "test_user",
                "session_id": "test_session",
                "query": "What is an internship?"
            },
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}\n")
            return False
        
        print("  Receiving SSE stream...\n")
        
        chunks_received = 0
        full_text = ""
        start_time = time.time()
        first_chunk_time = None
        
        # Read SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        
                        if data.get('type') == 'start':
                            print("  📡 Stream started")
                            
                        elif data.get('type') == 'chunk':
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                print(f"  ⚡ First chunk received in {first_chunk_time - start_time:.2f}s")
                            
                            chunks_received += 1
                            content = data.get('content', '')
                            full_text += content
                            print(f"  📦 Chunk {chunks_received}: {content}")
                            
                        elif data.get('type') == 'done':
                            end_time = time.time()
                            print(f"\n  ✅ Stream complete")
                            print(f"  Total time: {end_time - start_time:.2f}s")
                            print(f"  Chunks received: {chunks_received}")
                            print(f"  Full response length: {len(full_text)} characters")
                            print(f"\n  Full response:\n  {full_text}\n")
                            return True
                            
                        elif data.get('type') == 'error':
                            print(f"  ❌ Error: {data.get('error')}\n")
                            return False
                            
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️  Failed to parse SSE message: {e}")
        
        print("❌ Stream ended unexpectedly\n")
        return False
        
    except Exception as e:
        print(f"❌ SSE streaming test failed: {e}\n")
        return False

def test_clear_session():
    """Test session clearing"""
    print("🔍 Testing session clearing...")
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/clear",
            json={
                "user_id": "test_user",
                "session_id": "test_session"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Session cleared successfully\n")
                return True
        
        print(f"❌ Failed to clear session: {response.status_code}\n")
        return False
        
    except Exception as e:
        print(f"❌ Session clear test failed: {e}\n")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SSE STREAMING TEST SUITE")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    health_ok = test_health()
    if not health_ok:
        print("⚠️  Service not ready. Please start the SSE service first:")
        print("   python chatbot_service_sse.py")
        return
    
    # Test 2: SSE streaming
    streaming_ok = test_sse_streaming()
    
    # Test 3: Session clearing
    clear_ok = test_clear_session()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Health Check:     {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"SSE Streaming:    {'✅ PASS' if streaming_ok else '❌ FAIL'}")
    print(f"Session Clearing: {'✅ PASS' if clear_ok else '❌ FAIL'}")
    print()
    
    if health_ok and streaming_ok and clear_ok:
        print("🎉 All tests passed! SSE streaming is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main()
