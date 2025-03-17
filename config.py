import logging
import os
import sys
from app_secrets import get_credential, get_credentials
from twilio.rest import Client

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

try:
    logger.info("Loading credentials from Secret Manager...")
    credentials = get_credentials()

    # Twilio Credentials
    TWILIO_ACCOUNT_SID = get_credential("twilio.account_sid")
    TWILIO_AUTH_TOKEN = get_credential("twilio.auth_token")
    TWILIO_PHONE_NUMBER = get_credential("twilio.phone_number")

    # Other credentials
    AUTHORIZED_WHATSAPP_NUMBER = get_credential("whatsapp.authorized_number")
    WEBHOOK_SECRET_TOKEN = get_credential("webhook.secret_token")

    # JWT Settings
    SECRET_KEY = get_credential("auth.jwt_secret")
    JWT_EXPIRATION_SECONDS = get_credential("auth.jwt_expiration_seconds", 3600)

    # Initialize Twilio Client
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Successfully initialized application with Secret Manager credentials")
except Exception as e:
    logger.error(f"FATAL ERROR: Could not initialize application with Secret Manager: {str(e)}")
    sys.exit(1)
