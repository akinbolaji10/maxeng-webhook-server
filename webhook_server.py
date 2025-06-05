from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") or "sqlite:///local.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(128))
    user_id = db.Column(db.String(128))
    amount = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return "🟢 MaxEng Webhook is live!"

@app.route('/ton-webhook', methods=['POST'])
def ton_webhook():
    data = request.json
    try:
        new_tx = Transaction(
            wallet_address=data.get("wallet_address"),
            user_id=data.get("user_id", "anonymous"),
            amount=data.get("amount")
        )
        db.session.add(new_tx)
        db.session.commit()
        return jsonify({"status": "✅ transaction logged"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
