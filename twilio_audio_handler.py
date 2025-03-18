from flask import request
from twilio.twiml.messaging_response import MessagingResponse
import logging
import requests
import tempfile
import time
from pydub import AudioSegment
from google.cloud import speech
import mutagen
from mutagen.mp3 import MP3
import os
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, AUTHORIZED_WHATSAPP_NUMBER

# Initialize logger
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Speech-to-Text configuration
LANGUAGE_CODE = "mr-IN"  # Marathi Language Code

# Initialize Google Speech-to-Text client
try:
    speech_client = speech.SpeechClient()
    logger.info("Google Speech-to-Text client initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Google Speech-to-Text client: {str(e)}")
    raise

def download_audio(media_url):
    """Download the OGG audio file from Twilio with retry mechanism."""
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info(f"Attempting to download audio from: {media_url}")
    
    retries = 3
    delay = 5  # Wait time in seconds before retrying

    for attempt in range(retries):
        try:
            response = requests.get(media_url, auth=auth, timeout=10)
            response.raise_for_status()
            temp_ogg_path = tempfile.mktemp(suffix=".ogg")
            with open(temp_ogg_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Audio file downloaded successfully: {temp_ogg_path}")
            return temp_ogg_path
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}: Failed to download audio ({str(e)}). Retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Failed to download audio after multiple attempts.")

def convert_ogg_to_mp3(ogg_path):
    """Convert OGG audio to MP3 format."""
    try:
        mp3_path = ogg_path.replace(".ogg", ".mp3")
        audio = AudioSegment.from_file(ogg_path, format="ogg")
        audio.export(mp3_path, format="mp3")
        logger.info(f"Converted OGG to MP3: {mp3_path}")
        return mp3_path
    except Exception as e:
        raise Exception(f"FFmpeg error: {str(e)} - Ensure FFmpeg is installed.")


def transcribe_audio(mp3_path):
    """Transcribe the MP3 audio file with a 30-second limit."""
    try:
        # Check audio duration using mutagen
        audio_info = MP3(mp3_path)
        duration = audio_info.info.length  # Get duration in seconds

        if duration > 30:
            raise ValueError(f"Audio is too long ({duration:.2f}s). Maximum allowed length is 30 seconds.")

        with open(mp3_path, "rb") as audio_file:
            audio_content = audio_file.read()

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code=LANGUAGE_CODE,
        )
        audio = speech.RecognitionAudio(content=audio_content)
        response = speech_client.recognize(config=config, audio=audio)

        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
        logger.info(f"Transcription result: {transcript}")
        return transcript

    except mutagen.MutagenError:
        raise Exception("Error reading audio file. Please ensure it's a valid MP3.")
    except Exception as e:
        raise Exception(f"Error in transcription: {str(e)}")

def cleanup_files(file_paths):
    """Delete temporary files to free space."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")

def process_twilio_webhook():
    resp = MessagingResponse()
    form_data = request.form
    from_number = form_data.get("From", "")
    message_body = form_data.get("Body", "").strip()  # Capture user message
    media_url = form_data.get("MediaUrl0", "")  # Check for media attachments
    media_content_type = form_data.get("MediaContentType0", "")

    # Log received message
    logger.info(f"Received Message | From: {from_number} | Message: {message_body} | Media: {media_url}")
    
    # Check if sender is authorized
    if from_number in [AUTHORIZED_WHATSAPP_NUMBER, f"whatsapp:{AUTHORIZED_WHATSAPP_NUMBER}"]:
        if media_url and "audio" in media_content_type:
            try:
                ogg_path = download_audio(media_url)
                mp3_path = convert_ogg_to_mp3(ogg_path)
                transcription = transcribe_audio(mp3_path)
                logger.info(f"Final transcription output: {transcription}")
                resp.message(f"{transcription}")
                cleanup_files([ogg_path, mp3_path])
            except Exception as e:
                logger.error(f"Audio processing error: {str(e)}")
                resp.message("Sorry, I couldn't process the audio file.")
        else:
            logger.info("No valid audio file found in the request.")
            resp.message("Please send an audio file for transcription.")
    else:
        logger.warning(f"Unauthorized sender: {from_number}")
        resp.message("Unauthorized sender.")

    return str(resp)
