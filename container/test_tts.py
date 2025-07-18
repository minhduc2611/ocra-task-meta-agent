#!/usr/bin/env python3
"""
Simple test script for TTS endpoints
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:5000"
TOKEN = "your_jwt_token_here"  # Replace with actual token

def test_tts_health():
    """Test TTS health endpoint"""
    print("Testing TTS health endpoint...")
    
    url = f"{BASE_URL}/api/v1/tts/health"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tts_voices():
    """Test TTS voices endpoint"""
    print("\nTesting TTS voices endpoint...")
    
    url = f"{BASE_URL}/api/v1/tts/voices"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    params = {"language_code": "en-US"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tts_base64():
    """Test TTS base64 endpoint"""
    print("\nTesting TTS base64 endpoint...")
    
    url = f"{BASE_URL}/api/v1/tts/base64"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "text": "Hello, this is a test of text-to-speech!",
        "voice_name": "en-US-Standard-A",
        "language_code": "en-US"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Audio base64 length: {len(result.get('audio_base64', ''))}")
            print(f"Content type: {result.get('content_type')}")
            print(f"Text length: {result.get('text_length')}")
        else:
            print(f"Error response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tts_stream():
    """Test TTS stream endpoint"""
    print("\nTesting TTS stream endpoint...")
    
    url = f"{BASE_URL}/api/v1/tts/stream"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "text": "Hello, this is a test of streaming text-to-speech!",
        "voice_name": "en-US-Standard-A",
        "language_code": "en-US",
        "audio_encoding": "MP3",
        "chunked": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            # Read the first chunk to verify it's working
            audio_data = b""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_data += chunk
                    if len(audio_data) > 1000:  # Just read first 1KB for testing
                        break
            
            print(f"Audio data received: {len(audio_data)} bytes")
            print("Stream test successful!")
        else:
            print(f"Error response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all TTS tests"""
    print("=== TTS Endpoint Tests ===\n")
    
    tests = [
        test_tts_health,
        test_tts_voices,
        test_tts_base64,
        test_tts_stream
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Health: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Voices: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Base64: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"Stream: {'✅ PASS' if results[3] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 All tests passed! TTS endpoints are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main() 