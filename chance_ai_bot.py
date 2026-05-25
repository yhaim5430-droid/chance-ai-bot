import os
import telebot
import requests
from telebot import types

# ================= CONFIG =================

TOKEN = os.getenv("TG_TOKEN")
BASE44_API_KEY = os.getenv("CHANCE_API_KEY")
BASE44_APP_ID = os.getenv("CHANCE_APP_ID")

if not TOKEN:
    raise Exception("❌ חסר TG_TOKEN")

if not BASE44_API_KEY:
    raise Exception("❌ חסר CHANCE_API_KEY")

if not BASE44_APP_ID:
    raise Exception("❌ חסר CHANCE_APP_ID")

bot = telebot.TeleBot(TOKEN)

BASE_URL = f"https://app.base44.com/api/apps/{BASE44_APP_ID}"

HEADERS = {
    "api_key": BASE44_API_KEY,
    "Content-Type": "application/json"
}

# ================= MENU =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎯 תחזית אחרונה", "🎰 הגרלות")
    markup.row("📊 Accuracy", "ℹ️ על הבוט")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "♣️♦️ CHANCE PREDICTOR ♠️♥️\n\nברוך הבא למערכת התחזיות",
        reply_markup=main_menu()
    )

# ================= PREDICTION =================

@bot.message_handler(func=lambda m: m.text == "🎯 תחזית אחרונה")
def latest_prediction(message):

    try:
        url = f"{BASE_URL}/entities/Prediction?limit=1&sort_by=-created_date"

        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            bot.send_message(message.chat.id, f"❌ API ERROR {response.status_code}")
            return

        data = response.json()

        if not data:
            bot.send_message(message.chat.id, "❌ אין תחזיות כרגע")
            return

        p = data[0]

        text = f"""
🎯 תחזית אחרונה

🎰 הגרלה: {p.get('target_draw_number')}

♠️ ספייד: {p.get('main_spade')}
♥️ לב: {p.get('main_heart')}
♦️ יהלום: {p.get('main_diamond')}
♣️ תלתן: {p.get('main_club')}

🔥 חיזוקים:
{p.get('reinforcement_1')}
{p.get('reinforcement_2')}

📈 שיטה:
{p.get('method')}
"""

        bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ERROR\n{e}")

# ================= DRAWS =================

@bot.message_handler(func=lambda m: m.text == "🎰 הגרלות")
def latest_draws(message):

    try:
        url = f"{BASE_URL}/entities/Draw?limit=5&sort_by=-draw_number"

        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            bot.send_message(message.chat.id, f"❌ API ERROR {response.status_code}")
            return

        data = response.json()

        if not data:
            bot.send_message(message.chat.id, "❌ אין נתוני הגרלות")
            return

        text = "🎰 5 הגרלות אחרונות\n\n"

        for d in data:
            text += f"""
#{d.get('draw_number')}

♠️ {d.get('spade')}
♥️ {d.get('heart')}
♦️ {d.get('diamond')}
♣️ {d.get('club')}

"""

        bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ERROR\n{e}")

# ================= ACCURACY =================

@bot.message_handler(func=lambda m: m.text == "📊 Accuracy")
def accuracy(message):

    try:
        url = f"{BASE_URL}/entities/PredictionResult?limit=20"

        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            bot.send_message(message.chat.id, f"❌ API ERROR {response.status_code}")
            return

        data = response.json()

        if not data:
            bot.send_message(message.chat.id, "❌ אין נתוני Accuracy")
            return

        total = len(data)
        hits = sum([x.get("hit_count", 0) for x in data])

        avg = round(hits / total, 2)

        text = f"""
📊 Accuracy Report

בדיקות: {total}

סה"כ פגיעות: {hits}

ממוצע פגיעות: {avg}
"""

        bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ERROR\n{e}")

# ================= ABOUT =================

@bot.message_handler(func=lambda m: m.text == "ℹ️ על הבוט")
def about(message):

    text = """
🤖 Chance AI Bot

מערכת תחזיות צ'אנס חכמה
מבוססת Base44

פותח על ידי חיים 🚀
"""

    bot.send_message(message.chat.id, text)

# ================= OTHER =================

@bot.message_handler(func=lambda m: True)
def other(message):

    bot.send_message(
        message.chat.id,
        "❌ לא הבנתי\nבחר אפשרות מהתפריט",
        reply_markup=main_menu()
    )

# ================= RUN =================

print("🚀 Bot Starting...")

bot.infinity_polling(skip_pending=True)
