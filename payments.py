import json
import os
import requests
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

if not PAYSTACK_SECRET_KEY:
    print("❌ CRITICAL ERROR: PAYSTACK_SECRET_KEY is not set in environment variables!")
else:
    print(f"✅ PAYSTACK_KEY loaded (starts with: {PAYSTACK_SECRET_KEY[:15]}...)")


# =========================
# ROLES HELPER
# =========================
def get_roles():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {
            "admins": [int(os.getenv("ADMIN_ID", 0))],
            "experts": {}
        }


def save_roles(data):
    try:
        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"❌ Failed to save roles file: {e}")
        return False


# =========================
# CREATE PAYMENT LINK
# =========================
def create_payment(email: str, telegram_id: int):
    """Create Paystack payment link"""
    if not PAYSTACK_SECRET_KEY:
        return None, "Payment service not configured (missing secret key)"

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": email,
        "amount": 3000,                    # GH₵30.00
        "currency": "GHS",
        "metadata": {
            "telegram_id": str(telegram_id),
            "plan": "weekly_pro"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"📡 Paystack Status: {response.status_code}")

        data = response.json()

        if data.get("status") is True:
            print("✅ Payment link created successfully!")
            return data["data"]["authorization_url"], None
        else:
            error_msg = data.get("message", "Unknown error from Paystack")
            print(f"❌ Paystack Error: {error_msg}")
            return None, error_msg

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None, "Network connection error to Paystack"
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None, "Failed to create payment link"


# =========================
# VERIFY PAYMENT + AUTO UPGRADE
# =========================
def verify_payment(reference: str):
    """
    Verify payment and upgrade user to Pro
    Returns: (success: bool, message: str)
    """
    if not PAYSTACK_SECRET_KEY:
        return False, "Payment service not configured"

    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        data = response.json()

        if not data.get("status"):
            return False, data.get("message", "Verification failed")

        transaction = data.get("data", {})
        
        if transaction.get("status") != "success":
            return False, "Payment was not successful"

        metadata = transaction.get("metadata", {})
        telegram_id = str(metadata.get("telegram_id"))

        if not telegram_id:
            return False, "Missing telegram_id in metadata"

        # Upgrade user to Pro
        roles = get_roles()
        expiry_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        roles.setdefault("experts", {})
        roles["experts"][telegram_id] = {"expires": expiry_date}

        save_roles(roles)

        print(f"✅ PRO UPGRADE SUCCESS → User {telegram_id} until {expiry_date}")
        return True, f"✅ Pro membership activated until {expiry_date}"

    except Exception as e:
        print(f"❌ Verify payment exception: {e}")
        return False, "Internal error while verifying payment"
