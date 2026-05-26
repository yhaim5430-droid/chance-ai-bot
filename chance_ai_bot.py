import os
import requests
import telebot
from telebot import types
from collections import Counter

from core.orchestrator import Orchestrator

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

# ================= HELPERS =================

def get_data(entity, limit=10, sort="-created_date"):
    url = f"{BASE_URL}/entities/{entity}?limit={limit}&sort_by={sort}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return None

    return response.json()

# ================= MENU =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("🎯 חיזוי הבא", "⚡ חיזוי מהיר")
    markup.row("📊 סטטיסטיקות", "🏆 Accuracy")
    markup.row("🔥 Hot Cards", "❄️ Cold Cards")
    markup.row("📜 היסטוריה", "📈 Top Patterns")
    markup.row("🪞 Mirror", "🔄 Reverse")
    markup.row("🧪 Quantum", "🧠 AI Analysis")
    markup.row("👑 VIP", "🔔 התראות")
    markup.row("ℹ️ מערכת")

    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    text = """
♣️♦️ CHANCE AI BOT ♠️♥️

ברוך הבא למערכת התחזיות 🎰

🤖 AI Engine פעיל
📊 סטטיסטיקה חכמה
🧠 מודל דירוג מתקדם
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )

# ================= 🎯 SMART AI PREDICTION =================

@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    orch = Orchestrator()
    best, score = orch.generate_best_prediction()

    text = f"""
🎯 SMART PREDICTION ENGINE

♠️ {best['spade']}
♥️ {best['heart']}
♦️ {best['diamond']}
♣️ {best['club']}

📊 Score: {score}/100

🧠 Engine:
• Candidate Generator: ACTIVE
• Scoring System: ACTIVE
• Optimization: ACTIVE

⚠️ חשוב:
זה דירוג סטטיסטי בלבד, לא חיזוי עתיד
"""

    bot.send_message(message.chat.id, text)

# ================= QUICK PREDICTION (Base44) =================

@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data("Prediction", 3)

    if not data:
        bot.send_message(message.chat.id, "❌ אין תחזיות")
        return

    text = "⚡ חיזויים מהירים\n\n"

    for p in data:
        text += f"""
🎰 {p.get('target_draw_number')}

♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}
"""

    bot.send_message(message.chat.id, text)

# ================= HISTORY =================

@bot.message_handler(func=lambda m: m.text == "📜 היסטוריה")
def history(message):

    data = get_data("Draw", 10, "-draw_number")

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    text = "📜 10 הגרלות אחרונות\n\n"

    for d in data:
        text += f"""
#{d.get('draw_number')}
♠️ {d.get('spade')}
♥️ {d.get('heart')}
♦️ {d.get('diamond')}
♣️ {d.get('club')}
"""

    bot.send_message(message.chat.id, text)

# ================= HOT CARDS =================

@bot.message_handler(func=lambda m: m.text == "🔥 Hot Cards")
def hot_cards(message):

    data = get_data("Draw", 50)

    cards = []

    if data:
        for d in data:
            cards += [
                d.get("spade"),
                d.get("heart"),
                d.get("diamond"),
                d.get("club")
            ]

    counter = Counter(cards)

    text = "🔥 Hot Cards\n\n"

    for card, count in counter.most_common(5):
        text += f"{card} → {count}\n"

    bot.send_message(message.chat.id, text)

# ================= COLD CARDS =================

@bot.message_handler(func=lambda m: m.text == "❄️ Cold Cards")
def cold_cards(message):

    data = get_data("Draw", 50)

    all_cards = ["7","8","9","10","J","Q","K","A"]

    cards = []

    if data:
        for d in data:
            cards += [
                d.get("spade"),
                d.get("heart"),
                d.get("diamond"),
                d.get("club")
            ]

    counter = Counter(cards)

    text = "❄️ Cold Cards\n\n"

    for c in all_cards:
        if counter.get(c, 0) <= 10:
            text += f"{c} → {counter.get(c,0)}\n"

    bot.send_message(message.chat.id, text)

# ================= STATS =================

@bot.message_handler(func=lambda m: m.text == "📊 סטטיסטיקות")
def stats(message):

    draws = get_data("Draw", 1)
    predictions = get_data("Prediction", 1)
    results = get_data("PredictionResult", 100)

    total_hits = sum([x.get("hit_count", 0) for x in results or []])

    text = f"""
📊 סטטיסטיקות מערכת

🎰 הגרלה אחרונה:
{draws[0].get('draw_number') if draws else 'N/A'}

🎯 תחזית אחרונה:
{predictions[0].get('target_draw_number') if predictions else 'N/A'}

🏆 סה"כ פגיעות:
{total_hits}

🤖 AI Engine:
ACTIVE
"""

    bot.send_message(message.chat.id, text)

# ================= PLACEHOLDERS =================

@bot.message_handler(func=lambda m: m.text == "🧠 AI Analysis")
def ai_analysis(message):
    bot.send_message(message.chat.id, "🧠 AI Engine Active")

@bot.message_handler(func=lambda m: m.text == "📈 Top Patterns")
def patterns(message):
    bot.send_message(message.chat.id, "📈 Pattern Engine Active")

@bot.message_handler(func=lambda m: m.text == "🪞 Mirror")
def mirror(message):
    bot.send_message(message.chat.id, "🪞 Mirror Engine Active")

@bot.message_handler(func=lambda m: m.text == "🔄 Reverse")
def reverse(message):
    bot.send_message(message.chat.id, "🔄 Reverse Engine Active")

@bot.message_handler(func=lambda m: m.text == "🧪 Quantum")
def quantum(message):
    bot.send_message(message.chat.id, "🧪 Quantum Engine Active")

@bot.message_handler(func=lambda m: m.text == "👑 VIP")
def vip(message):
    bot.send_message(message.chat.id, "👑 VIP System Active")

@bot.message_handler(func=lambda m: m.text == "🔔 התראות")
def notifications(message):
    bot.send_message(message.chat.id, "🔔 Notifications Active")

@bot.message_handler(func=lambda m: m.text == "ℹ️ מערכת")
def about(message):
    bot.send_message(message.chat.id, "🤖 Chance AI System v2")

# ================= UNKNOWN =================

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id, "❌ בחר אפשרות מהתפריט", reply_markup=main_menu())

# ================= RUN =================

print("🚀 CHANCE AI BOT RUNNING")

bot.infinity_polling(skip_pending=True)
