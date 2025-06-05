from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

# App config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
        user_id = data.get("user_id")
        wallet = data.get("user")
        to = data.get("to")
        amount_nano = int(data.get("amount", 0))
        amount_ton = round(amount_nano / 1e9, 4)
        usd = data.get("usd", "~$2")

        # Save to DB
        new_tx = Transaction(
            user_id=user_id,
            wallet_address=wallet,
            to_address=to,
            amount=str(amount_ton),
            usd=usd
        )
        db.session.add(new_tx)
        db.session.commit()

        # Notify user on Telegram
        if BOT_TOKEN and user_id:
            text = (
                f"✅ *TON Transaction Signed!*\n\n"
                f"💼 Wallet: `{wallet}`\n"
                f"💸 Amount: `{amount_ton} TON` (~{usd})\n"
                f"📥 To: `{to}`\n"
                f"🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(telegram_url, json={
                "chat_id": user_id,
                "text": text,
                "parse_mode": "Markdown"
            })

        return jsonify({"status": "success", "message": "Transaction saved"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run locally
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
