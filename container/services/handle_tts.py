import os
import io
import logging
from typing import Generator, Optional
from google.cloud import texttospeech
from google.cloud.texttospeech_v1 import SynthesizeSpeechRequest
from flask import Response, stream_template
import base64

logger = logging.getLogger(__name__)

class TTSStreamingService:
    def __init__(self):
        """Initialize TTS service with Google Cloud credentials"""
        try:
            # Initialize the TTS client
            self.client = texttospeech.TextToSpeechClient()
            logger.info("TTS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {str(e)}")
            raise

    def synthesize_speech_stream(
        self, 
        text: str, 
        voice_name: str = "en-US-Standard-A",
        language_code: str = "en-US",
        audio_encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0
    ) -> Generator[bytes, None, None]:
        """
        Stream synthesized speech audio chunks.
        
        Args:
            text: Text to synthesize
            voice_name: Google TTS voice name
            language_code: Language code (e.g., 'en-US', 'vi-VN')
            audio_encoding: Audio format (MP3, LINEAR16, etc.)
            speaking_rate: Speed of speech (0.25 to 4.0)
            pitch: Pitch adjustment (-20.0 to 20.0)
            volume_gain_db: Volume adjustment (-96.0 to 16.0)
        
        Yields:
            Audio data chunks as bytes
        """
        try:
            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )

            # Configure the audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=audio_encoding,
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db
            )

            # Create the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Stream the audio data
            audio_content = response.audio_content
            
            # For now, we'll yield the entire audio content
            # In a more advanced implementation, you could chunk it
            yield audio_content

        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise

    def synthesize_speech_chunked(
        self, 
        text: str, 
        chunk_size: int = 1000,  # Characters per chunk
        **kwargs
    ) -> Generator[bytes, None, None]:
        """
        Synthesize speech in chunks for better streaming experience.
        
        Args:
            text: Text to synthesize
            chunk_size: Number of characters per chunk
            **kwargs: Other TTS parameters
        
        Yields:
            Audio data chunks as bytes
        """
        try:
            # Split text into chunks
            text_chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
            
            for chunk in text_chunks:
                if chunk.strip():  # Skip empty chunks
                    # Synthesize each chunk
                    for audio_chunk in self.synthesize_speech_stream(chunk, **kwargs):
                        yield audio_chunk
                        
        except Exception as e:
            logger.error(f"Error in chunked speech synthesis: {str(e)}")
            raise

    def get_available_voices(self, language_code: str = "en-US") -> list:
        """
        Get available voices for a language.
        
        Args:
            language_code: Language code to filter voices
        
        Returns:
            List of available voice names
        """
        try:
            voices = self.client.list_voices(language_code=language_code)
            return [voice.name for voice in voices.voices]
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return []


# Global TTS service instance
tts_service = TTSStreamingService()


def create_audio_stream_response(
    text: str,
    voice_name: str = "en-US-Standard-A",
    language_code: str = "en-US",
    audio_encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3,
    chunked: bool = True,
    **kwargs
) -> Response:
    """
    Create a Flask streaming response for TTS audio.
    
    Args:
        text: Text to synthesize
        voice_name: Google TTS voice name
        language_code: Language code
        audio_encoding: Audio format
        chunked: Whether to use chunked synthesis
        **kwargs: Other TTS parameters
    
    Returns:
        Flask Response object with streaming audio
    """
    try:
        # Determine content type based on encoding
        content_type_map = {
            texttospeech.AudioEncoding.MP3: "audio/mpeg",
            texttospeech.AudioEncoding.LINEAR16: "audio/wav",
            texttospeech.AudioEncoding.OGG_OPUS: "audio/ogg",
            texttospeech.AudioEncoding.MULAW: "audio/wav",
            texttospeech.AudioEncoding.ALAW: "audio/wav"
        }
        
        content_type = content_type_map.get(audio_encoding, "audio/mpeg")
        
        def generate_audio():
            try:
                if chunked:
                    for audio_chunk in tts_service.synthesize_speech_chunked(
                        text, voice_name=voice_name, language_code=language_code, 
                        audio_encoding=audio_encoding, **kwargs
                    ):
                        yield audio_chunk
                else:
                    for audio_chunk in tts_service.synthesize_speech_stream(
                        text, voice_name=voice_name, language_code=language_code,
                        audio_encoding=audio_encoding, **kwargs
                    ):
                        yield audio_chunk
            except Exception as e:
                logger.error(f"Error generating audio stream: {str(e)}")
                yield b""  # Return empty bytes on error
        
        return Response(
            generate_audio(),
            content_type=content_type,
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Transfer-Encoding": "chunked"
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating audio stream response: {str(e)}")
        raise


def synthesize_text_to_base64(
    text: str,
    voice_name: str = "en-US-Standard-A",
    language_code: str = "en-US",
    audio_encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3,
    **kwargs
) -> str:
    """
    Synthesize text to speech and return as base64 encoded string.
    
    Args:
        text: Text to synthesize
        voice_name: Google TTS voice name
        language_code: Language code
        audio_encoding: Audio format
        **kwargs: Other TTS parameters
    
    Returns:
        Base64 encoded audio data
    """
    try:
        audio_content = b""
        for chunk in tts_service.synthesize_speech_stream(
            text, voice_name=voice_name, language_code=language_code,
            audio_encoding=audio_encoding, **kwargs
        ):
            audio_content += chunk
        
        return base64.b64encode(audio_content).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error synthesizing text to base64: {str(e)}")
        raise 