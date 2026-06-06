import json
from datetime import datetime, timedelta
import asyncio

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import TOKEN, ADMIN_ID
from payments import create_payment, verify_payment

# =========================
# STATES
# =========================
FREE_TIP_STATE = 1
PRO_TIP_STATE = 2
ADD_EXPERT_TIP_STATE = 10
WAITING_EXPERT_TIP = 11
ADD_PREMIUM_STATE = 20
REMOVE_PREMIUM_STATE = 21

# =========================
# MENUS
# =========================

ADMIN_MENU = ReplyKeyboardMarkup([
    ["📊 Dashboard"],
    ["➕ Add Premium"],
    ["➖ Remove Premium"],
    ["📝 Add Free Tip"],
    ["💎 Add Pro Tip"],
    ["📢 Broadcast"],
    ["👥 Members"],
    ["📈 Statistics"]
], resize_keyboard=True)

FREE_MENU = ReplyKeyboardMarkup([
    ["📊 Free Tips"],
    ["📜 Free History"],
    ["⭐ Bet With Pros"],
    ["📞 Support"]
], resize_keyboard=True)

PRO_MENU = ReplyKeyboardMarkup([
    ["📊 Free Tips"],
    ["📜 Free History"],
    ["💎 Pro Tips"],
    ["📜 Pro History"],
    ["📞 Support"]
], resize_keyboard=True)

EXPERT_MENU = ReplyKeyboardMarkup([
    ["👤 ShadowPicks01"],
    ["👻 GhostPL"],
    ["♠️ Blackjack"],
    ["🇪🇺 EuropePicks"],
    ["🔴 Exclusive Live Betting"],
    ["🔙 Back to Pro Menu"]
], resize_keyboard=True)

# =========================
# DATA HELPERS
# =========================

def get_users():
    try:
        with open("users_list.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open("users_list.json", "w") as f:
        json.dump(users, f, indent=4)

def register_user(user):
    users = get_users()
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        })
        save_users(users)

def get_roles():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {"admins": [ADMIN_ID], "experts": {}}

def save_roles(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

def get_tips():
    try:
        with open("tips.json", "r") as f:
            return json.load(f)
    except:
        return {"free_tip": "No free tip yet.", "free_history": []}

def save_tips(data):
    with open("tips.json", "w") as f:
        json.dump(data, f, indent=4)

def get_expert_tips():
    try:
        with open("experts_tips.json", "r") as f:
            return json.load(f)
    except:
        default = {"shadowpicks01": "", "ghostpl": "", "blackjack": "", "europepicks": "", "live": ""}
        with open("experts_tips.json", "w") as f:
            json.dump(default, f, indent=4)
        return default

def save_expert_tip(expert_key: str, tip: str):
    tips = get_expert_tips()
    tips[expert_key] = tip.strip()
    with open("experts_tips.json", "w") as f:
        json.dump(tips, f, indent=4)

def get_user_role(user_id: int) -> str:
    data = get_roles()
    if user_id in data.get("admins", []):
        return "admin"
    experts = data.get("experts", {})
    uid = str(user_id)
    if uid in experts:
        try:
            expiry = datetime.strptime(experts[uid]["expires"], "%Y-%m-%d")
            if datetime.now() <= expiry:
                return "expert"
        except:
            pass
    return "free"

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    role = get_user_role(update.effective_user.id)

    if role == "admin":
        await update.message.reply_text("👑 ADMIN PANEL", reply_markup=ADMIN_MENU)
    elif role == "expert":
        await update.message.reply_text("💎 PRO PANEL", reply_markup=PRO_MENU)
    else:
        await update.message.reply_text("🏆 WELCOME TO WINNINGS01", reply_markup=FREE_MENU)

# =========================
# ADMIN DASHBOARD
# =========================
async def show_dashboard(update: Update):
    roles = get_roles()
    users = get_users()
    pros = len(roles.get("experts", {}))
    await update.message.reply_text(
        f"📊 **ADMIN DASHBOARD**\n\n"
        f"👥 Total Users: {len(users)}\n"
        f"💎 Active Pro Members: {pros}\n"
        f"✅ Bot is running smoothly",
        parse_mode="Markdown"
    )

# =========================
# VERIFY COMMAND
# =========================
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only")
        return
    if not context.args:
        await update.message.reply_text("Usage: /verify <reference>")
        return
    success, message = verify_payment(context.args[0])
    await update.message.reply_text(f"Verification Result:\n{message}")

# =========================
# BUTTONS HANDLER - FULL
# =========================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    state = context.user_data.get("state")

    # Payment Flow
    if context.user_data.get("waiting_email"):
        email = text.strip()
        if "@" not in email:
            await update.message.reply_text("❌ Please send a valid email address.")
            return
        payment_url, error = create_payment(email, user_id)
        context.user_data["waiting_email"] = False
        if payment_url:
            await update.message.reply_text(f"💎 Payment Link Generated!\n\n🔗 {payment_url}")
        else:
            await update.message.reply_text("❌ Failed to generate payment link.")
        return

    # ADMIN SECTION
    if user_id == ADMIN_ID:
        if text == "📊 Dashboard":
            await show_dashboard(update)
            return

        elif text == "➕ Add Premium":
            context.user_data["state"] = ADD_PREMIUM_STATE
            await update.message.reply_text("Send User ID to add as Premium:")
            return

        elif text == "➖ Remove Premium":
            roles = get_roles()
            pros = roles.get("experts", {})
            if not pros:
                await update.message.reply_text("No Pro members found.")
                return
            msg = "➖ Active Pro Members:\n\n"
            for uid, info in pros.items():
                msg += f"🆔 {uid} → Expires: {info.get('expires')}\n"
            msg += "\nSend User ID to remove:"
            context.user_data["state"] = REMOVE_PREMIUM_STATE
            await update.message.reply_text(msg)
            return

        elif state == ADD_PREMIUM_STATE:
            try:
                target = str(int(text))
                roles = get_roles()
                expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                roles.setdefault("experts", {})
                roles["experts"][target] = {"expires": expiry}
                save_roles(roles)
                await update.message.reply_text(f"✅ User {target} is now Pro until {expiry}")
            except:
                await update.message.reply_text("❌ Invalid User ID")
            context.user_data["state"] = None
            return

        elif state == REMOVE_PREMIUM_STATE:
            roles = get_roles()
            uid = str(text.strip())
            if uid in roles.get("experts", {}):
                del roles["experts"][uid]
                save_roles(roles)
                await update.message.reply_text(f"✅ Removed Pro from user {uid}")
            else:
                await update.message.reply_text("❌ User not found.")
            context.user_data["state"] = None
            return

        if state == FREE_TIP_STATE:
            data = get_tips()
            data["free_tip"] = text
            data["free_history"].insert(0, text)
            data["free_history"] = data["free_history"][:20]
            save_tips(data)
            context.user_data["state"] = None
            await update.message.reply_text("✅ Free Tip Saved!")
            return

        if state == PRO_TIP_STATE:
            context.user_data["state"] = ADD_EXPERT_TIP_STATE
            await update.message.reply_text("💎 Choose expert to add tip for:", reply_markup=EXPERT_MENU)
            return

        if state == ADD_EXPERT_TIP_STATE:
            expert_map = {
                "👤 ShadowPicks01": "shadowpicks01",
                "👻 GhostPL": "ghostpl",
                "♠️ Blackjack": "blackjack",
                "🇪🇺 EuropePicks": "europepicks",
                "🔴 Exclusive Live Betting": "live"
            }
            if text in expert_map:
                context.user_data["expert_key"] = expert_map[text]
                context.user_data["state"] = WAITING_EXPERT_TIP
                await update.message.reply_text(f"Send the new tip for **{text}**:")
            return

        if state == WAITING_EXPERT_TIP:
            expert_key = context.user_data.get("expert_key")
            if expert_key:
                save_expert_tip(expert_key, text)
                context.user_data["state"] = None
                context.user_data.pop("expert_key", None)
                await update.message.reply_text("✅ Tip saved successfully!")
            return

    # ========================
    # FREE & PRO USER BUTTONS
    # ========================
    if text == "⭐ Bet With Pros":
        context.user_data["waiting_email"] = True
        await update.message.reply_text("💎 Send your email address:")
        return

    if text == "💎 Pro Tips":
        if role != "expert":
            await update.message.reply_text("❌ Pro membership required.")
            return
        await update.message.reply_text("💎 Select a Tipster:", reply_markup=EXPERT_MENU)
        return

    expert_map = {
        "👤 ShadowPicks01": "shadowpicks01",
        "👻 GhostPL": "ghostpl",
        "♠️ Blackjack": "blackjack",
        "🇪🇺 EuropePicks": "europepicks",
        "🔴 Exclusive Live Betting": "live"
    }

    if text in expert_map:
        if role != "expert":
            await update.message.reply_text("❌ Pro membership required.")
            return
        tips = get_expert_tips()
        tip = tips.get(expert_map[text], "No tip available yet.")
        await update.message.reply_text(f"{text}\n\n{tip}")
        return

    if text == "🔙 Back to Pro Menu":
        await update.message.reply_text("💎 PRO PANEL", reply_markup=PRO_MENU)
        return

    if text == "📊 Free Tips":
        tips = get_tips()
        await update.message.reply_text("🔥 FREE TIP\n\n" + tips.get("free_tip", "No tip yet."))

    elif text == "📜 Free History":
        tips = get_tips()
        hist = tips.get("free_history", [])
        msg = "📜 FREE HISTORY\n\n" + "\n\n".join(hist) if hist else "No history yet."
        await update.message.reply_text(msg)

    elif text == "📜 Pro History":
        await update.message.reply_text("📜 Pro History (coming soon...)")

    elif text == "📞 Support":
        await update.message.reply_text("📞 Contact Support: @YourUsername")

    elif text == "📝 Add Free Tip":
        context.user_data["state"] = FREE_TIP_STATE
        await update.message.reply_text("Send the new Free Tip:")

    elif text == "💎 Add Pro Tip":
        context.user_data["state"] = PRO_TIP_STATE
        await update.message.reply_text("💎 Choose which expert to update:")

# =========================
# MAIN - POLLING MODE
# =========================
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buttons))

    print("🚀 Winnings01 Bot Running in Polling Mode...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
