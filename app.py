from flask import Flask
from webhook import webhook_bp
from auth import generate_token
import uvicorn

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(webhook_bp)

@app.route('/login', methods=['POST'])
def login():
    """User authentication endpoint."""
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'error': 'Authentication required'}), 401

    if auth.username == "admin" and auth.password == "password":
        token, expiration = generate_token(auth.username)
        return jsonify({'token': token, 'expires_at': expiration.isoformat()})

    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
