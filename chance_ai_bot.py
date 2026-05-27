import os
import requests
import telebot
from telebot import types
from collections import Counter

# ================= CONFIG =================

TOKEN = os.getenv("TG_TOKEN")
BASE44_API_KEY = os.getenv("CHANCE_API_KEY")
BASE44_APP_ID = os.getenv("CHANCE_APP_ID")

if not TOKEN:
    raise Exception("❌ חסר TG_TOKEN")

bot = telebot.TeleBot(TOKEN)   # 🔴 חובה להיות פה לפני הכל

# ================= HELPERS =================

def get_data(entity, limit=10, sort="-created_date"):
    url = f"https://app.base44.com/api/apps/{BASE44_APP_ID}/entities/{entity}?limit={limit}&sort_by={sort}"

    headers = {
        "api_key": BASE44_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    return response.json()

# ================= HANDLERS =================

@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data("Prediction", 4)

    if not data:
        bot.send_message(message.chat.id, "❌ אין חיזויים")
        return

    text = "⚡ חיזוי מהיר (Base44)\n\n"

    for i, p in enumerate(data):

        text += f"""
🎯 חיזוי #{i+1}

🎰 הגרלה יעד:
#{p.get('target_draw_number')}

♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}

🔥 חיזוקים:
1) {p.get('reinforcement_1')}
2) {p.get('reinforcement_2')}

────────────────────
"""

    bot.send_message(message.chat.id, text)

# ================= RUN =================

print("🚀 CHANCE AI BOT STARTED")

bot.infinity_polling(skip_pending=True)
