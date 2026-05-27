import os
import time
import requests
import telebot
from telebot import types

# ================== CONFIG ==================

TOKEN = os.getenv("TG_TOKEN")

if not TOKEN:
    raise Exception("Missing TG_TOKEN")

bot = telebot.TeleBot(TOKEN)

print("🚀 CHANCE AI BOT STARTED")

# ================== SAFE START (ANTI 409) ==================

def safe_start():
    """
    מנקה getUpdates ישנים כדי למנוע 409
    """
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1")
    except:
        pass

safe_start()

# ================== DATA ==================

def get_data():
    # כאן אתה יכול לחבר Base44 אם צריך
    return [
        {
            "draw": 52953,
            "cards": ["♠️10", "♥️9", "♦️Q", "♣️K"]
        }
    ]

# ================== KEYBOARD ==================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🎯 חיזוי הבא", "⚡ חיזוי מהיר")
    markup.row("📊 סטטיסטיקות", "🔥 Hot Cards")

    return markup

# ================== START ==================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "♣️ CHANCE AI BOT",
        reply_markup=main_menu()
    )

# ================== NEXT ==================

@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    data = get_data()[0]

    text = f"""
🎯 חיזוי הבא

🎰 הגרלה #{data['draw']}

{data['cards'][0]}
{data['cards'][1]}
{data['cards'][2]}
{data['cards'][3]}
"""

    bot.send_message(message.chat.id, text)

# ================== QUICK ==================

@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data()

    text = "⚡ חיזוי מהיר\n\n"

    for i, d in enumerate(data):

        text += f"""
🎯 #{i+1} → #{d['draw']}
{d['cards'][0]} {d['cards'][1]} {d['cards'][2]} {d['cards'][3]}

----------------
"""

    bot.send_message(message.chat.id, text)

# ================== FALLBACK ==================

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "בחר אפשרות מהתפריט")

# ================== RUN (SAFE POLLING) ==================

while True:
    try:
        bot.infinity_polling(
            skip_pending=True,
            timeout=20,
            long_polling_timeout=20
        )

    except Exception as e:
        print("BOT ERROR:", e)
        time.sleep(3)
