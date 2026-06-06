from flask import Flask, request
import json
import hmac
import hashlib
import os
from datetime import datetime, timedelta

# Import from payments.py (single source of truth)
from payments import verify_payment, get_roles, save_roles

app = Flask(__name__)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


# =========================
# WEBHOOK SIGNATURE VERIFICATION (SECURITY)
# =========================
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify that the webhook really came from Paystack"""
    if not PAYSTACK_SECRET_KEY or not signature:
        return False
    
    computed_sig = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(computed_sig, signature)


# =========================
# WEBHOOK ENDPOINT
# =========================
@app.route("/paystack-webhook", methods=["POST"])
def paystack_webhook():
    try:
        # Get raw payload for signature check
        raw_payload = request.get_data()
        signature = request.headers.get("x-paystack-signature")

        # Security Check
        if not verify_webhook_signature(raw_payload, signature):
            print("❌ Invalid webhook signature - Possible attack!")
            return "OK", 200

        event = request.get_json()
        print(f"🔥 WEBHOOK RECEIVED: {event.get('event')}")

        # Only process successful payments
        if event.get("event") != "charge.success":
            return "OK", 200

        data = event.get("data", {})
        reference = data.get("reference")

        # Use the improved verify_payment function
        success, message = verify_payment(reference)

        if success:
            metadata = data.get("metadata", {})
            telegram_id = str(metadata.get("telegram_id"))
            print(f"✅ WEBHOOK SUCCESS: User {telegram_id} upgraded")
        else:
            print(f"❌ WEBHOOK FAILED: {message}")

        return "OK", 200

    except Exception as e:
        print("❌ WEBHOOK ERROR:", str(e))
        return "OK", 200


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    print("🚀 Paystack Webhook Server Started on http://0.0.0.0:5000")
    print("📌 Endpoint: /paystack-webhook")
    app.run(host="0.0.0.0", port=5000, debug=False)   # ← Change to False in production