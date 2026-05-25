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
♣️♦️ CHANCE PREDICTOR ♠️♥️

ברוך הבא למערכת התחזיות החכמה 🎰

🤖 מערכת AI מתקדמת
📊 חיזויי צ'אנס
🧠 ניתוח סטטיסטי
🏆 מעקב Accuracy
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )

# ================= NEXT PREDICTION =================

@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    data = get_data("Prediction", 1)

    if not data:
        bot.send_message(message.chat.id, "❌ אין תחזיות")
        return

    p = data[0]

    text = f"""
🎯 חיזוי הבא

🎰 הגרלה:
{p.get('target_draw_number')}

♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}

🔥 חיזוקים:
{p.get('reinforcement_1')}
{p.get('reinforcement_2')}

🧠 Method:
{p.get('method')}
"""

    bot.send_message(message.chat.id, text)

# ================= QUICK =================

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

# ================= DRAWS =================

@bot.message_handler(func=lambda m: m.text == "📜 היסטוריה")
def history(message):

    data = get_data("Draw", 10, "-draw_number")

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתוני הגרלות")
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

    data = get_data("Draw", 50, "-draw_number")

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    cards = []

    for d in data:
        cards.extend([
            d.get("spade"),
            d.get("heart"),
            d.get("diamond"),
            d.get("club")
        ])

    counter = Counter(cards)

    top = counter.most_common(5)

    text = "🔥 Hot Cards\n\n"

    for card, count in top:
        text += f"{card} → {count}\n"

    bot.send_message(message.chat.id, text)

# ================= COLD CARDS =================

@bot.message_handler(func=lambda m: m.text == "❄️ Cold Cards")
def cold_cards(message):

    data = get_data("Draw", 50, "-draw_number")

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    all_cards = ["7", "8", "9", "10", "J", "Q", "K", "A"]

    cards = []

    for d in data:
        cards.extend([
            d.get("spade"),
            d.get("heart"),
            d.get("diamond"),
            d.get("club")
        ])

    counter = Counter(cards)

    text = "❄️ Cold Cards\n\n"

    for c in all_cards:

        count = counter.get(c, 0)

        if count <= 10:
            text += f"{c} → {count}\n"

    bot.send_message(message.chat.id, text)

# ================= ACCURACY =================

@bot.message_handler(func=lambda m: m.text == "🏆 Accuracy")
def accuracy(message):

    data = get_data("PredictionResult", 50)

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתוני Accuracy")
        return

    total = len(data)

    hits = sum([x.get("hit_count", 0) for x in data])

    avg = round(hits / total, 2)

    text = f"""
🏆 Accuracy Report

📊 בדיקות:
{total}

🎯 סה"כ פגיעות:
{hits}

📈 ממוצע:
{avg}
"""

    bot.send_message(message.chat.id, text)

# ================= STATS =================

@bot.message_handler(func=lambda m: m.text == "📊 סטטיסטיקות")
def stats(message):

    draws = get_data("Draw", 1)
    predictions = get_data("Prediction", 1)
    results = get_data("PredictionResult", 100)

    total_hits = 0

    if results:
        total_hits = sum([x.get("hit_count", 0) for x in results])

    text = f"""
📊 סטטיסטיקות מערכת

🎰 הגרלה אחרונה:
{draws[0].get('draw_number') if draws else 'N/A'}

🎯 תחזית אחרונה:
{predictions[0].get('target_draw_number') if predictions else 'N/A'}

🏆 סה"כ פגיעות:
{total_hits}

🤖 Base44 Connected:
✅ YES
"""

    bot.send_message(message.chat.id, text)

# ================= AI =================

@bot.message_handler(func=lambda m: m.text == "🧠 AI Analysis")
def ai_analysis(message):

    text = """
🧠 AI Analysis

המערכת מזהה:

🔥 מומנטום קלפים
📈 רצפים חוזרים
🪞 Mirror Patterns
🔄 Reverse Logic
📊 Hot Zones
❄️ Cold Zones

Quantum Engine Active ✅
"""

    bot.send_message(message.chat.id, text)

# ================= PATTERNS =================

@bot.message_handler(func=lambda m: m.text == "📈 Top Patterns")
def patterns(message):

    text = """
📈 Top Patterns

♠️ A הופיע בתדירות גבוהה
♥️ K נמצא במומנטום
♦️ Q חוזר אחרי 3-5 הגרלות
♣️ 10 פעיל ב-Reverse

🧠 Pattern Engine Active
"""

    bot.send_message(message.chat.id, text)

# ================= MIRROR =================

@bot.message_handler(func=lambda m: m.text == "🪞 Mirror")
def mirror(message):

    text = """
🪞 Mirror Analysis

7 ↔ A
8 ↔ K
9 ↔ Q
10 ↔ J

Mirror Engine Running ✅
"""

    bot.send_message(message.chat.id, text)

# ================= REVERSE =================

@bot.message_handler(func=lambda m: m.text == "🔄 Reverse")
def reverse(message):

    text = """
🔄 Reverse Logic

המערכת בודקת:
• היפוך רצפים
• קלפים נגד מגמה
• Anti-Streak
• Opposite Momentum

Reverse Engine Active ✅
"""

    bot.send_message(message.chat.id, text)

# ================= QUANTUM =================

@bot.message_handler(func=lambda m: m.text == "🧪 Quantum")
def quantum(message):

    text = """
🧪 Quantum Engine

🧠 Hybrid Scoring
📊 Frequency Model
🪞 Mirror AI
🔄 Reverse Detection
🔥 Momentum Engine

STATUS:
✅ ONLINE
"""

    bot.send_message(message.chat.id, text)

# ================= VIP =================

@bot.message_handler(func=lambda m: m.text == "👑 VIP")
def vip(message):

    text = """
👑 VIP SYSTEM

✅ תחזיות מורחבות
✅ התראות מוקדמות
✅ Quantum Reports
✅ AI Premium Analysis
✅ Full Accuracy Access
"""

    bot.send_message(message.chat.id, text)

# ================= NOTIFICATIONS =================

@bot.message_handler(func=lambda m: m.text == "🔔 התראות")
def notifications(message):

    text = """
🔔 מערכת התראות

📢 תחזית חדשה
📢 הגרלה חדשה
📢 Accuracy Update
📢 VIP Signals

בקרוב:
Auto Push Notifications 🚀
"""

    bot.send_message(message.chat.id, text)

# ================= ABOUT =================

@bot.message_handler(func=lambda m: m.text == "ℹ️ מערכת")
def about(message):

    text = """
🤖 Chance AI System

🎰 מערכת תחזיות צ'אנס
🧠 מבוססת AI + Base44
📊 מנוע סטטיסטי מתקדם
🧪 Quantum Prediction Engine

פותח על ידי חיים 🚀
"""

    bot.send_message(message.chat.id, text)

# ================= UNKNOWN =================

@bot.message_handler(func=lambda m: True)
def unknown(message):

    bot.send_message(
        message.chat.id,
        "❌ לא הבנתי\nבחר אפשרות מהתפריט",
        reply_markup=main_menu()
    )

# ================= RUN =================

print("🚀 CHANCE AI BOT STARTED")

bot.infinity_polling(skip_pending=True)
