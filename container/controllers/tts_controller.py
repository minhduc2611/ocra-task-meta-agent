from flask import request, jsonify, g
from services.handle_tts import create_audio_stream_response, synthesize_text_to_base64, tts_service
from google.cloud import texttospeech
from __init__ import app, login_required
import logging

logger = logging.getLogger(__name__)

@app.route('/api/v1/tts/stream', methods=['OPTIONS'])
def tts_stream_options():
    """Handle OPTIONS request for TTS stream endpoint"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@app.route('/api/v1/tts/base64', methods=['OPTIONS'])
def tts_base64_options():
    """Handle OPTIONS request for TTS stream endpoint"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response


@app.route('/api/v1/tts/stream', methods=['POST'])
@login_required
def tts_stream_endpoint():
    """
    Stream text-to-speech audio.
    
    Request body:
    {
        "text": "Text to synthesize",
        "voice_name": "en-US-Standard-A",
        "language_code": "en-US",
        "audio_encoding": "MP3",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "volume_gain_db": 0.0,
        "chunked": true
    }
    """
    try:
        # if request.method == "OPTIONS":
        #     response = jsonify({})
        #     response.headers.add('Access-Control-Allow-Origin', '*')
        #     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        #     response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        #     return jsonify({"status": "ok"}), 200
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Extract parameters with defaults
        voice_name = data.get('voice_name', 'en-US-Standard-A')
        language_code = data.get('language_code', 'en-US')
        audio_encoding_str = data.get('audio_encoding', 'MP3')
        speaking_rate = data.get('speaking_rate', 1.0)
        pitch = data.get('pitch', 0.0)
        volume_gain_db = data.get('volume_gain_db', 0.0)
        chunked = data.get('chunked', True)
        
        # Convert audio encoding string to enum
        audio_encoding_map = {
            'MP3': texttospeech.AudioEncoding.MP3,
            'LINEAR16': texttospeech.AudioEncoding.LINEAR16,
            'OGG_OPUS': texttospeech.AudioEncoding.OGG_OPUS,
            'MULAW': texttospeech.AudioEncoding.MULAW,
            'ALAW': texttospeech.AudioEncoding.ALAW
        }
        
        audio_encoding = audio_encoding_map.get(audio_encoding_str.upper(), texttospeech.AudioEncoding.MP3)
        
        # Validate parameters
        if not (0.25 <= speaking_rate <= 4.0):
            return jsonify({"error": "Speaking rate must be between 0.25 and 4.0"}), 400
        
        if not (-20.0 <= pitch <= 20.0):
            return jsonify({"error": "Pitch must be between -20.0 and 20.0"}), 400
        
        if not (-96.0 <= volume_gain_db <= 16.0):
            return jsonify({"error": "Volume gain must be between -96.0 and 16.0"}), 400
        
        # Create streaming response
        response = create_audio_stream_response(
            text=text,
            voice_name=voice_name,
            language_code=language_code,
            audio_encoding=audio_encoding,
            chunked=chunked,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in TTS stream endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/tts/base64', methods=['POST', 'OPTIONS'])
@login_required
def tts_base64_endpoint():
    """
    Convert text to speech and return as base64 encoded audio.
    
    Request body:
    {
        "text": "Text to synthesize",
        "voice_name": "en-US-Standard-A",
        "language_code": "en-US",
        "audio_encoding": "MP3",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "volume_gain_db": 0.0
    }
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Text is required"}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Extract parameters with defaults
        voice_name = data.get('voice_name', 'en-US-Standard-A')
        language_code = data.get('language_code', 'en-US')
        audio_encoding_str = data.get('audio_encoding', 'MP3')
        speaking_rate = data.get('speaking_rate', 1.0)
        pitch = data.get('pitch', 0.0)
        volume_gain_db = data.get('volume_gain_db', 0.0)
        
        # Convert audio encoding string to enum
        audio_encoding_map = {
            'MP3': texttospeech.AudioEncoding.MP3,
            'LINEAR16': texttospeech.AudioEncoding.LINEAR16,
            'OGG_OPUS': texttospeech.AudioEncoding.OGG_OPUS,
            'MULAW': texttospeech.AudioEncoding.MULAW,
            'ALAW': texttospeech.AudioEncoding.ALAW
        }
        
        audio_encoding = audio_encoding_map.get(audio_encoding_str.upper(), texttospeech.AudioEncoding.MP3)
        
        # Validate parameters
        if not (0.25 <= speaking_rate <= 4.0):
            return jsonify({"error": "Speaking rate must be between 0.25 and 4.0"}), 400
        
        if not (-20.0 <= pitch <= 20.0):
            return jsonify({"error": "Pitch must be between -20.0 and 20.0"}), 400
        
        if not (-96.0 <= volume_gain_db <= 16.0):
            return jsonify({"error": "Volume gain must be between -96.0 and 16.0"}), 400
        
        # Synthesize to base64
        audio_base64 = synthesize_text_to_base64(
            text=text,
            voice_name=voice_name,
            language_code=language_code,
            audio_encoding=audio_encoding,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db
        )
        
        return jsonify({
            "audio_base64": audio_base64,
            "content_type": "audio/mpeg" if audio_encoding == texttospeech.AudioEncoding.MP3 else "audio/wav",
            "text_length": len(text)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in TTS base64 endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/tts/voices', methods=['GET'])
@login_required
def get_voices_endpoint():
    """
    Get available voices for a language.
    
    Query parameters:
    - language_code: Language code (e.g., 'en-US', 'vi-VN')
    """
    try:
        language_code = request.args.get('language_code', 'en-US')
        voices = tts_service.get_available_voices(language_code)
        
        return jsonify({
            "voices": voices,
            "language_code": language_code,
            "count": len(voices)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/tts/health', methods=['GET'])
@login_required
def tts_health_endpoint():
    """Check TTS service health"""
    try:
        # Try to get voices to test the service
        voices = tts_service.get_available_voices('en-US')
        
        return jsonify({
            "status": "healthy",
            "service": "Google Cloud Text-to-Speech",
            "available_voices_count": len(voices)
        }), 200
        
    except Exception as e:
        logger.error(f"TTS health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500 