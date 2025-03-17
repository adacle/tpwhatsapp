def token_required(f):
    """Decorator to verify JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        # Allow Twilio webhook without JWT
        if "/twilio/webhook/" in request.path:
            return f(*args, **kwargs)

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]

        if not token:
            logger.warning("Missing JWT token in request.")
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            kwargs['current_user'] = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated_function

def generate_token(username):
    """Generate JWT token for authentication."""
    import jwt
    import datetime
    from config import SECRET_KEY

    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({'username': username, 'exp': expiration}, SECRET_KEY, algorithm="HS256")
    return token, expiration
