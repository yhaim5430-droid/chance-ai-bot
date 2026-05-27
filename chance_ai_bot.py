import os
import requests
import telebot
from telebot import types

from core.orchestrator import Orchestrator

# ================= CONFIG =================

TOKEN = os.getenv("TG_TOKEN")
BASE44_API_KEY = os.getenv("CHANCE_API_KEY")
BASE44_APP_ID = os.getenv("CHANCE_APP_ID")

if not TOKEN:
    raise Exception("Missing TG_TOKEN")

if not BASE44_API_KEY:
    raise Exception("Missing CHANCE_API_KEY")

if not BASE44_APP_ID:
    raise Exception("Missing CHANCE_APP_ID")

bot = telebot.TeleBot(TOKEN)

BASE_URL = f"https://app.base44.com/api/apps/{BASE44_APP_ID}"

HEADERS = {
    "api_key": BASE44_API_KEY,
    "Content-Type": "application/json"
}

# ================= HELPERS =================

def get_data(entity, limit=10, sort="-created_date"):
    url = f"{BASE_URL}/entities/{entity}?limit={limit}&sort_by={sort}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            return []

        data = r.json()

        # Base44 לפעמים מחזיר {"data": [...]}
        if isinstance(data, dict) and "data" in data:
            return data["data"]

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []

# ================= MENU =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🎯 חיזוי הבא", "⚡ חיזוי מהיר")
    markup.row("📊 סטטיסטיקות", "🏆 Accuracy")
    markup.row("🔥 Hot Cards", "❄️ Cold Cards")
    markup.row("📜 היסטוריה", "📈 Top Patterns")
    markup.row("🪞 Mirror", "🔄 Reverse")
    markup.row("🧠 AI Analysis", "🧪 Quantum")
    markup.row("👑 VIP", "🔔 התראות")

    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "♣️ CHANCE AI BOT",
        reply_markup=main_menu()
    )

# ================= QUICK (Base44 בלבד) =================

@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data("Prediction", 4)

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתוני Base44")
        return

    text = "⚡️ חיזוי מהיר (Base44)\n\n"

    for i, p in enumerate(data, start=1):

        text += f"""
🎯 חיזוי #{i}

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

# ================= NEXT (AI + Orchestrator) =================

@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    draws = get_data("History", 50)

    if not draws:
        bot.send_message(message.chat.id, "❌ אין נתוני היסטוריה")
        return

    orchestrator = Orchestrator(draws)
    result = orchestrator.predict()

    prediction = result["prediction"]

    text = f"""
🎯 חיזוי הבא (AI Engine)

🎰 הגרלה יעד:
#{result['target_draw']}

♠️ {prediction.get('spade')}
♥️ {prediction.get('heart')}
♦️ {prediction.get('diamond')}
♣️ {prediction.get('club')}

📊 Score:
{result['score']}/100

🧠 Confidence:
{result['confidence']}%

⚠️ Risk:
{result['confidence_level']}

Why selected:
{result['report']}
"""

    bot.send_message(message.chat.id, text)

# ================= OTHER =================

@bot.message_handler(func=lambda m: m.text == "📊 סטטיסטיקות")
def stats(message):
    bot.send_message(message.chat.id, "📊 סטטיסטיקות זמניות")

@bot.message_handler(func=lambda m: m.text == "🔥 Hot Cards")
def hot(message):
    bot.send_message(message.chat.id, "🔥 Hot Cards")

@bot.message_handler(func=lambda m: m.text == "❄️ Cold Cards")
def cold(message):
    bot.send_message(message.chat.id, "❄️ Cold Cards")

@bot.message_handler(func=lambda m: m.text == "📜 היסטוריה")
def history(message):
    bot.send_message(message.chat.id, "📜 היסטוריה")

@bot.message_handler(func=lambda m: m.text == "🪞 Mirror")
def mirror(message):
    bot.send_message(message.chat.id, "🪞 Mirror")

@bot.message_handler(func=lambda m: m.text == "🔄 Reverse")
def reverse(message):
    bot.send_message(message.chat.id, "🔄 Reverse")

@bot.message_handler(func=lambda m: m.text == "🧠 AI Analysis")
def ai(message):
    bot.send_message(message.chat.id, "🧠 AI Analysis")

@bot.message_handler(func=lambda m: m.text == "🧪 Quantum")
def quantum(message):
    bot.send_message(message.chat.id, "🧪 Quantum")

@bot.message_handler(func=lambda m: m.text == "👑 VIP")
def vip(message):
    bot.send_message(message.chat.id, "👑 VIP")

@bot.message_handler(func=lambda m: m.text == "🔔 התראות")
def alerts(message):
    bot.send_message(message.chat.id, "🔔 התראות")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "בחר אפשרות מהתפריט")

# ================= RUN =================

if __name__ == "__main__":
    print("🚀 CHANCE AI BOT STARTED")
    bot.infinity_polling(skip_pending=True)
