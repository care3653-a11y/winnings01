import os
import requests

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

print("="*70)
print("🔍 PAYSTACK DEBUG START")
print("="*70)
print(f"Key Loaded: {'✅ YES' if PAYSTACK_SECRET_KEY else '❌ NO'}")
if PAYSTACK_SECRET_KEY:
    print(f"Key Length: {len(PAYSTACK_SECRET_KEY)}")
    print(f"Starts with: {PAYSTACK_SECRET_KEY[:20]}...")
    print(f"Ends with: ...{PAYSTACK_SECRET_KEY[-10:]}")
else:
    print("❌ KEY IS EMPTY OR NOT FOUND!")
print("="*70)


def create_payment(email: str, telegram_id: int):
    if not PAYSTACK_SECRET_KEY:
        return None, "Payment service not configured (key missing)"

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": email,
        "amount": 3000,
        "currency": "GHS",
        "metadata": {
            "telegram_id": str(telegram_id),
            "plan": "weekly_pro"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        print(f"📡 Paystack Status Code: {response.status_code}")
        print(f"📡 Response Body: {response.text[:600]}...")

        data = response.json()

        if data.get("status") is True:
            print("✅ SUCCESS: Payment link created!")
            return data["data"]["authorization_url"], None
        else:
            error = data.get("message", "Unknown error")
            print(f"❌ Paystack Error: {error}")
            return None, error

    except Exception as e:
        print(f"❌ Exception: {type(e).__name__} | {e}")
        return None, f"Connection failed: {str(e)}"
