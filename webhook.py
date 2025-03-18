import os
from flask import Blueprint, request, Response
from twilio.request_validator import RequestValidator
from config import TWILIO_AUTH_TOKEN, WEBHOOK_SECRET_TOKEN, logger
from twilio_audio_handler import process_twilio_webhook

webhook_bp = Blueprint('webhook', __name__)

# Load public webhook URL from environment variable (set via Docker or Cloud Run)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

@webhook_bp.route(f'/twilio/webhook/{WEBHOOK_SECRET_TOKEN}', methods=['POST'])
def twilio_webhook():
    logger.debug(f"Headers: {dict(request.headers)}")  # Log all headers
    logger.debug(f"Raw Request Data: {request.data.decode('utf-8')}")

    logger.info(f"Expected WEBHOOK_SECRET_TOKEN: {WEBHOOK_SECRET_TOKEN}")
    logger.info(f"Loaded TWILIO_AUTH_TOKEN (masked): {TWILIO_AUTH_TOKEN[:4]}...{TWILIO_AUTH_TOKEN[-4:]}")

    # Twilio Signature Validation
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    twilio_signature = request.headers.get("X-Twilio-Signature")

    # Fix URL issues by reconstructing the correct Twilio-signed URL
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")  # Ensure correct protocol
    forwarded_host = request.headers.get("X-Forwarded-Host", request.host)  # Ensure correct domain
    full_url = f"{forwarded_proto}://{forwarded_host}{request.path}"

    logger.info(f"Reconstructed URL for Twilio Validation: {full_url}")

    if not twilio_signature:
        logger.error("Twilio Signature missing from headers.")
        return Response("Unauthorized", status=401)

    logger.info(f"Twilio Signature: {twilio_signature}")

    is_valid_signature = validator.validate(full_url, request.form, twilio_signature)

    if not is_valid_signature:
        logger.error(f"Twilio Signature validation failed! Signature: {twilio_signature}")
        return Response("Unauthorized", status=401)

    logger.info("✅ Twilio Signature validation successful.")

    return process_twilio_webhook()
