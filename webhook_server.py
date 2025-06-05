from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# App config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app, origins=["https://maxeng-wallet-signing.onrender.com"])  # Allow requests from sign.html

BOT_TOKEN = os.getenv("BOT_TOKEN")

# DB Model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128))
    wallet_address = db.Column(db.String(128))
    to_address = db.Column(db.String(128))
    amount = db.Column(db.String(64))
    usd = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    return "<h3>✅ MaxEng Webhook is Live</h3>"

@app.route('/ton-webhook', methods=['POST'])
def ton_webhook():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "Invalid JSON"}), 400

        user_id = data.get("user_id", "anonymous")
        wallet = data.get("user")
        to_address = data.get("to")
        amount_nano = data.get("amount")
        usd = data.get("usd", "~$2")

        # Validate required fields
        if not all([wallet, to_address, amount_nano]):
            logger.error(f"Missing fields: {data}")
            return jsonify({"error": "Missing required fields"}), 400

        # Convert and validate amount
        try:
            amount_nano = int(amount_nano)
            amount_ton = round(amount_nano / 1e9, 6)
        except (ValueError, TypeError):
            logger.error(f"Invalid amount: {amount_nano}")
            return jsonify({"error": "Invalid amount"}), 400

        # Save to DB
        new_tx = Transaction(
            user_id=user_id,
            wallet_address=wallet,
            to_address=to_address,
            amount=str(amount_ton),
            usd=usd
        )
        db.session.add(new_tx)
        db.session.commit()
        logger.info(f"Transaction saved: user_id={user_id}, wallet={wallet}, amount={amount_ton}")

        # Notify user on Telegram
        if BOT_TOKEN and user_id != "anonymous":
            text = f"User {user_id} sent {amount_ton} TON from {wallet}"
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            response = requests.post(telegram_url, json={
                "chat_id": user_id,
                "text": text,
                "parse_mode": "Markdown"
            })
            if not response.ok:
                logger.error(f"Telegram notification failed: {response.text}")

        return jsonify({"status": "success", "message": "Transaction saved"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Run locally
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
