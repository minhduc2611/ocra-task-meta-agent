# Text-to-Speech Streaming API

This implementation provides streaming text-to-speech functionality using Google Cloud Text-to-Speech API, allowing users to hear audio as it's being generated for the best user experience.

## 🚀 Features

- **Real-time Audio Streaming**: Audio plays as it's being generated
- **Multiple Audio Formats**: MP3, WAV, OGG, MULAW, ALAW
- **Voice Customization**: Speaking rate, pitch, volume control
- **Multi-language Support**: All Google TTS supported languages
- **Chunked Processing**: Better streaming for long texts
- **Base64 Alternative**: For non-streaming use cases

## 📋 API Endpoints

### 1. Stream Audio
```bash
POST /api/v1/tts/stream
```

**Request Body:**
```json
{
  "text": "Hello, this is a test of streaming text-to-speech!",
  "voice_name": "en-US-Standard-A",
  "language_code": "en-US",
  "audio_encoding": "MP3",
  "speaking_rate": 1.0,
  "pitch": 0.0,
  "volume_gain_db": 0.0,
  "chunked": true
}
```

**Response:** Streaming audio data

### 2. Base64 Audio
```bash
POST /api/v1/tts/base64
```

**Response:**
```json
{
  "audio_base64": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT...",
  "content_type": "audio/mpeg",
  "text_length": 45
}
```

### 3. Get Available Voices
```bash
GET /api/v1/tts/voices?language_code=en-US
```

**Response:**
```json
{
  "voices": [
    "en-US-Standard-A",
    "en-US-Standard-B",
    "en-US-Standard-C",
    "en-US-Standard-D"
  ],
  "language_code": "en-US",
  "count": 4
}
```

### 4. Health Check
```bash
GET /api/v1/tts/health
```

## 🔧 Setup

### 1. Install Dependencies
```bash
pip install google-cloud-texttospeech
```

### 2. Google Cloud Setup
```bash
# Set up authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"

# Or use gcloud CLI
gcloud auth application-default login
```

### 3. Add to requirements.txt
```
google-cloud-texttospeech==2.16.3
```

## 💻 Frontend Implementation

### JavaScript/HTML5 Audio Streaming
```javascript
async function streamTTS(text) {
  try {
    const response = await fetch('/api/v1/tts/stream', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        voice_name: 'en-US-Standard-A',
        language_code: 'en-US',
        audio_encoding: 'MP3',
        chunked: true
      })
    });

    if (!response.ok) {
      throw new Error('TTS request failed');
    }

    // Create audio blob from stream
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    
    // Play audio
    const audio = new Audio(audioUrl);
    audio.play();
    
  } catch (error) {
    console.error('TTS Error:', error);
  }
}
```

### React Hook Example
```javascript
import { useState, useRef } from 'react';

function useTTSStreaming() {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const playTTS = async (text, options = {}) => {
    try {
      setIsPlaying(true);
      
      const response = await fetch('/api/v1/tts/stream', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text,
          voice_name: options.voice || 'en-US-Standard-A',
          language_code: options.language || 'en-US',
          audio_encoding: 'MP3',
          chunked: true,
          ...options
        })
      });

      if (!response.ok) {
        throw new Error('TTS request failed');
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
      
    } catch (error) {
      console.error('TTS Error:', error);
    } finally {
      setIsPlaying(false);
    }
  };

  return { playTTS, isPlaying, audioRef };
}
```

### Base64 Audio (Alternative)
```javascript
async function playTTSBase64(text) {
  try {
    const response = await fetch('/api/v1/tts/base64', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        voice_name: 'en-US-Standard-A'
      })
    });

    const data = await response.json();
    
    // Convert base64 to audio
    const audioData = atob(data.audio_base64);
    const audioArray = new Uint8Array(audioData.length);
    for (let i = 0; i < audioData.length; i++) {
      audioArray[i] = audioData.charCodeAt(i);
    }
    
    const audioBlob = new Blob([audioArray], { type: data.content_type });
    const audioUrl = URL.createObjectURL(audioBlob);
    
    const audio = new Audio(audioUrl);
    audio.play();
    
  } catch (error) {
    console.error('TTS Error:', error);
  }
}
```

## 🎯 cURL Examples

### Stream Audio
```bash
curl -X POST http://localhost:5000/api/v1/tts/stream \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is streaming text-to-speech!",
    "voice_name": "en-US-Standard-A",
    "language_code": "en-US",
    "audio_encoding": "MP3",
    "chunked": true
  }' \
  --output audio.mp3
```

### Get Voices
```bash
curl -X GET "http://localhost:5000/api/v1/tts/voices?language_code=en-US" \
  -H "Authorization: Bearer your_jwt_token"
```

### Health Check
```bash
curl -X GET http://localhost:5000/api/v1/tts/health \
  -H "Authorization: Bearer your_jwt_token"
```

## 🌍 Supported Languages & Voices

### Popular Languages
- **English (US)**: `en-US`
- **Vietnamese**: `vi-VN`
- **Spanish**: `es-ES`
- **French**: `fr-FR`
- **German**: `de-DE`
- **Japanese**: `ja-JP`
- **Korean**: `ko-KR`
- **Chinese**: `zh-CN`

### Voice Examples
- `en-US-Standard-A` (Female)
- `en-US-Standard-B` (Male)
- `en-US-Wavenet-A` (High quality female)
- `en-US-Wavenet-B` (High quality male)
- `vi-VN-Standard-A` (Vietnamese female)
- `vi-VN-Wavenet-A` (Vietnamese high quality)

## ⚙️ Configuration Options

### Audio Encoding
- `MP3`: Most compatible, smaller files
- `LINEAR16`: Uncompressed, high quality
- `OGG_OPUS`: Good compression, web-friendly
- `MULAW`: Telephony quality
- `ALAW`: Telephony quality

### Voice Parameters
- `speaking_rate`: 0.25 to 4.0 (default: 1.0)
- `pitch`: -20.0 to 20.0 (default: 0.0)
- `volume_gain_db`: -96.0 to 16.0 (default: 0.0)

## 🔒 Security & Performance

### Authentication
- All endpoints require JWT authentication
- Rate limiting recommended
- Input validation for all parameters

### Performance Tips
- Use chunked processing for long texts
- Cache frequently used audio
- Implement client-side buffering
- Consider CDN for static audio files

## 🐛 Troubleshooting

### Common Issues
1. **Authentication Error**: Check Google Cloud credentials
2. **Audio Not Playing**: Verify content-type headers
3. **Streaming Issues**: Check nginx/proxy buffering settings
4. **Voice Not Found**: Verify voice name and language code

### Debug Headers
```bash
# Disable nginx buffering
proxy_buffering off;
proxy_cache off;

# Add CORS headers if needed
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
```

This implementation provides a complete streaming TTS solution with excellent user experience! 