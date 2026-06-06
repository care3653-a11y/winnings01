import json
from datetime import datetime

EXPERTS = {
    "shadowpicks01": {"name": "ShadowPicks01", "emoji": "👤"},
    "ghostpl":       {"name": "GhostPL",       "emoji": "👻"},
    "blackjack":     {"name": "Blackjack",     "emoji": "♠️"},
    "europepicks":   {"name": "EuropePicks",   "emoji": "🇪🇺"},
    "live":          {"name": "Exclusive Live Betting", "emoji": "🔴"}
}

def get_expert_tips():
    try:
        with open("experts_tips.json", "r") as f:
            return json.load(f)
    except:
        # Create default structure
        data = {key: "" for key in EXPERTS.keys()}
        save_expert_tips(data)
        return data


def save_expert_tips(data):
    with open("experts_tips.json", "w") as f:
        json.dump(data, f, indent=4)


def add_expert_tip(expert_key: str, tip: str):
    tips = get_expert_tips()
    tips[expert_key] = tip.strip()
    save_expert_tips(tips)
    return True