import os
import hashlib
import hmac
import base64
from flask import request
from twilio.request_validator import RequestValidator
from config import TWILIO_AUTH_TOKEN, logger

def validate_twilio_signature(url, params, signature):
    """Manually validate Twilio signature."""
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    return validator.validate(url, params, signature)

def cleanup_files(file_paths):
    """Delete temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
