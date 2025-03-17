# app_secrets.py
import os
import json
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app_secrets')

# Force Secret Manager usage - no fallbacks to environment variables
USE_SECRET_MANAGER = True
FORCE_SECRET_MANAGER = True

# The name of the secret in Secret Manager
SECRET_NAME = "whatsapp-app-credentials"

try:
    from google.cloud import secretmanager
    logger.info("Secret Manager support is enabled")
    secretmanager_available = True
except ImportError:
    logger.error("google-cloud-secretmanager not installed! This is required.")
    logger.error("Install it with: pip install google-cloud-secretmanager")
    sys.exit(1)

# Cache for secrets to avoid repeated API calls
_secrets_cache = {}

def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the payload for the given secret version if one exists.
    """
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()
    
    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    try:
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Return the decoded payload
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        error_msg = f"Error accessing secret {secret_id}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def get_credentials():
    """
    Get all credentials exclusively from Secret Manager.
    Returns a dictionary with all application credentials.
    """
    # Check if credentials are already cached
    if _secrets_cache.get('credentials'):
        return _secrets_cache['credentials']
    
    # Get project ID - required for Secret Manager
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        try:
            import google.auth
            _, project_id = google.auth.default()
            logger.info(f"Using default project ID: {project_id}")
        except Exception as e:
            error_msg = f"Error getting default project ID: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    if not project_id:
        error_msg = "No Google Cloud project ID available. Set GOOGLE_CLOUD_PROJECT environment variable."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Access the secret from Secret Manager
    logger.info(f"Accessing secret {SECRET_NAME} from project {project_id}")
    secret_data = access_secret_version(project_id, SECRET_NAME)
    
    # Parse the secret data
    try:
        credentials = json.loads(secret_data)
        logger.info(f"Successfully loaded credentials from Secret Manager")
        _secrets_cache['credentials'] = credentials
        return credentials
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing JSON credentials from Secret Manager: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def get_credential(path, default=None):
    """
    Get a specific credential using a dot-notation path.
    Example: get_credential("twilio.auth_token")
    """
    try:
        credentials = get_credentials()
        parts = path.split('.')
        
        # Navigate through the nested dictionary
        current = credentials
        for part in parts:
            if part in current:
                current = current[part]
            else:
                logger.warning(f"Credential path '{path}' not found, returning default value")
                return default
        
        # Additional check for None values to help with debugging
        if current is None:
            logger.warning(f"Credential at path '{path}' is None")
            
        return current
    except Exception as e:
        logger.error(f"Error retrieving credential at path '{path}': {str(e)}")
        raise  # Re-raise the exception to stop the application if credentials can't be accessed 