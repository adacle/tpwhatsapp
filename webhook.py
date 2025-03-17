from flask import Blueprint, request, Response
from twilio.request_validator import RequestValidator
from config import TWILIO_AUTH_TOKEN, WEBHOOK_SECRET_TOKEN, logger
from twilio_audio_handler import process_twilio_webhook

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route(f'/twilio/webhook/{WEBHOOK_SECRET_TOKEN}', methods=['POST'])
def twilio_webhook():
    logger.debug(f"Headers: {request.headers}")
    logger.debug(f"Raw Request Data: {request.data.decode('utf-8')}")

    # Log expected token for debugging
    logger.info(f"Expected WEBHOOK_SECRET_TOKEN: {WEBHOOK_SECRET_TOKEN}")
    logger.info(f"Loaded TWILIO_AUTH_TOKEN (masked): {TWILIO_AUTH_TOKEN[:4]}...{TWILIO_AUTH_TOKEN[-4:]}")

    # Twilio Signature Validation
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    twilio_signature = request.headers.get("X-Twilio-Signature")
    url = request.url  # Use the exact URL Twilio is sending

    logger.debug(f"Validating Twilio request for URL: {url}")

    if not twilio_signature:
        logger.error("Twilio Signature missing from headers.")
        return Response("Unauthorized", status=401)

    is_valid_signature = validator.validate(url, request.form, twilio_signature)

    if not is_valid_signature:
        logger.error(f"Twilio Signature validation failed! Signature: {twilio_signature}")
        return Response("Unauthorized", status=401)

    logger.info("✅ Twilio Signature validation successful.")

    return process_twilio_webhook()
