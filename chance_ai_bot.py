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
    raise Exception("Missing TG_TOKEN")

if not BASE44_API_KEY:
    raise Exception("Missing CHANCE_API_KEY")

bot = telebot.TeleBot(TOKEN)

BASE_URL = f"https://app.base44.com/api/apps/{BASE44_APP_ID}"

HEADERS = {
    "api_key": BASE44_API_KEY,
    "Content-Type": "application/json"
}

# ================= HELPERS =================

def get_data(entity, limit=10, sort="-created_date"):

    url = f"{BASE_URL}/entities/{entity}?limit={limit}&sort_by={sort}"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return None

    return r.json()

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
    markup.row("ℹ️ מערכת")

    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "♣️ CHANCE AI BOT",
        reply_markup=main_menu()
    )

# ================= NEXT PREDICTION =================

@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    data = get_data("Prediction", 1)

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    p = data[0]

    text = f"""
🎯 חיזוי הבא

🎰 #{p.get('target_draw_number')}

♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}

🔥 חיזוקים:
1) {p.get('reinforcement_1')}
2) {p.get('reinforcement_2')}
"""

    bot.send_message(message.chat.id, text)

# ================= QUICK =================

@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data("Prediction", 4)

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    text = "⚡ חיזוי מהיר\n\n"

    for i, p in enumerate(data):

        text += f"""
🎯 #{i+1} → #{p.get('target_draw_number')}
♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}

-------------------
"""

    bot.send_message(message.chat.id, text)

# ================= OTHER HANDLERS =================

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

print("🚀 CHANCE AI BOT STARTED")

bot.infinity_polling(skip_pending=True)
