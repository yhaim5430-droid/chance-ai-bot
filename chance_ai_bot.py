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

BASE_URL = (
    f"https://app.base44.com/api/apps/"
    f"{BASE44_APP_ID}"
)

HEADERS = {
    "api_key": BASE44_API_KEY,
    "Content-Type": "application/json"
}


# ================= HELPERS =================

def get_data(
    entity,
    limit=10,
    sort="-created_date"
):

    url = (
        f"{BASE_URL}/entities/"
        f"{entity}"
        f"?limit={limit}"
        f"&sort_by={sort}"
    )

    response = requests.get(
        url,
        headers=HEADERS
    )

    if response.status_code != 200:
        return None

    return response.json()


# ================= MENU =================

def main_menu():

    markup = (
        types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )
    )

    markup.row(
        "🎯 חיזוי הבא",
        "⚡ חיזוי מהיר"
    )

    markup.row(
        "📊 סטטיסטיקות",
        "🏆 Accuracy"
    )

    markup.row(
        "🔥 Hot Cards",
        "❄️ Cold Cards"
    )

    markup.row(
        "📜 היסטוריה",
        "📈 Top Patterns"
    )

    markup.row(
        "🪞 Mirror",
        "🔄 Reverse"
    )

    markup.row(
        "🧪 Quantum",
        "🧠 AI Analysis"
    )

    markup.row(
        "👑 VIP",
        "🔔 התראות"
    )

    markup.row("ℹ️ מערכת")

    return markup


# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    text = """
♣️♦️ CHANCE AI BOT ♠️♥️

ברוך הבא למערכת הניתוח 🎰

🤖 Smart Prediction
📊 Statistical Analysis
🧠 Confidence Report
🏆 Accuracy Tracking
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# ================= NEXT PREDICTION =================

@bot.message_handler(
    func=lambda m:
    m.text == "🎯 חיזוי הבא"
)
def next_prediction(message):

    draws = get_data(
        "Draw",
        200,
        "-draw_number"
    )

    if not draws:

        bot.send_message(
            message.chat.id,
            "❌ אין נתוני Draw"
        )
        return

    orchestrator = (
        Orchestrator(draws)
    )

    result = (
        orchestrator.predict()
    )

    p = result["prediction"]

    text = f"""
🎯 Smart Prediction

🎰 הגרלה יעד:
#{result['target_draw']}

♠️ {p['spade']}
♥️ {p['heart']}
♦️ {p['diamond']}
♣️ {p['club']}

📊 Score:
{result['score']}/100

🧠 Confidence:
{result['confidence']}%

⚠️ Risk:
{result['confidence_level']}

Why selected:
{result['report']}
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ================= QUICK =================

@bot.message_handler(
    func=lambda m:
    m.text == "⚡ חיזוי מהיר"
)
def quick_prediction(message):

    draws = get_data(
        "Draw",
        200,
        "-draw_number"
    )

    if not draws:

        bot.send_message(
            message.chat.id,
            "❌ אין נתוני Draw"
        )
        return

    orchestrator = (
        Orchestrator(draws)
    )

    text = "⚡ Smart Picks\n\n"

    for i in range(3):

        result = (
            orchestrator.predict()
        )

        p = result["prediction"]

        text += f"""
#{i+1}

🎰 יעד:
{result['target_draw']}

♠️ {p['spade']}
♥️ {p['heart']}
♦️ {p['diamond']}
♣️ {p['club']}

Score:
{result['score']}

Confidence:
{result['confidence']}%

-------------------
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ================= HISTORY =================

@bot.message_handler(
    func=lambda m:
    m.text == "📜 היסטוריה"
)
def history(message):

    data = get_data(
        "Draw",
        10,
        "-draw_number"
    )

    if not data:

        bot.send_message(
            message.chat.id,
            "❌ אין נתוני הגרלות"
        )
        return

    text = (
        "📜 10 הגרלות אחרונות\n\n"
    )

    for d in data:

        text += f"""
#{d.get('draw_number')}

♠️ {d.get('spade')}
♥️ {d.get('heart')}
♦️ {d.get('diamond')}
♣️ {d.get('club')}

"""

    bot.send_message(
        message.chat.id,
        text
    )


# ================= HOT CARDS =================

@bot.message_handler(
    func=lambda m:
    m.text == "🔥 Hot Cards"
)
def hot_cards(message):

    data = get_data(
        "Draw",
        50,
        "-draw_number"
    )

    if not data:

        bot.send_message(
            message.chat.id,
            "❌ אין נתונים"
        )
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

    top = (
        counter.most_common(5)
    )

    text = "🔥 Hot Cards\n\n"

    for card, count in top:

        text += (
            f"{card} → {count}\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# ================= COLD CARDS =================

@bot.message_handler(
    func=lambda m:
    m.text == "❄️ Cold Cards"
)
def cold_cards(message):

    data = get_data(
        "Draw",
        50,
        "-draw_number"
    )

    if not data:

        bot.send_message(
            message.chat.id,
            "❌ אין נתונים"
        )
        return

    all_cards = [
        "7", "8", "9", "10",
        "J", "Q", "K", "A"
    ]

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

            text += (
                f"{c} → {count}\n"
            )

    bot.send_message(
        message.chat.id,
        text
    )


# ================= ACCURACY =================

@bot.message_handler(
    func=lambda m:
    m.text == "🏆 Accuracy"
)
def accuracy(message):

    text = """
🏆 Accuracy

המערכת כרגע בודקת:

• Score consistency
• Statistical weighting
• Prediction stability

Replay testing coming soon
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ================= STATS =================

@bot.message_handler(
    func=lambda m:
    m.text == "📊 סטטיסטיקות"
)
def stats(message):

    draws = get_data(
        "Draw",
        1,
        "-draw_number"
    )

    draw_number = (
        draws[0].get(
            "draw_number"
        )
        if draws
        else "N/A"
    )

    text = f"""
📊 System Stats

🎰 הגרלה אחרונה:
{draw_number}

📚 Draw Window:
200

🤖 Engine:
Statistical Weighted

🧠 Confidence:
Enabled
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ================= SIMPLE PAGES =================

@bot.message_handler(
    func=lambda m:
    m.text == "🧠 AI Analysis"
)
def ai_analysis(message):

    bot.send_message(
        message.chat.id,
        "🧠 Statistical AI active"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "📈 Top Patterns"
)
def patterns(message):

    bot.send_message(
        message.chat.id,
        "📈 Pattern engine active"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "🪞 Mirror"
)
def mirror(message):

    bot.send_message(
        message.chat.id,
        "🪞 Mirror engine active"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "🔄 Reverse"
)
def reverse(message):

    bot.send_message(
        message.chat.id,
        "🔄 Reverse engine active"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "🧪 Quantum"
)
def quantum(message):

    bot.send_message(
        message.chat.id,
        "🧪 Quantum scoring active"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "👑 VIP"
)
def vip(message):

    bot.send_message(
        message.chat.id,
        "👑 VIP soon"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "🔔 התראות"
)
def notifications(message):

    bot.send_message(
        message.chat.id,
        "🔔 Notifications soon"
    )


@bot.message_handler(
    func=lambda m:
    m.text == "ℹ️ מערכת"
)
def about(message):

    bot.send_message(
        message.chat.id,
        "🤖 Chance AI System"
    )


# ================= UNKNOWN =================

@bot.message_handler(
    func=lambda m: True
)
def unknown(message):

    bot.send_message(
        message.chat.id,
        "❌ לא הבנתי\nבחר אפשרות מהתפריט",
        reply_markup=main_menu()
    )


# ================= RUN =================

print(
    "🚀 CHANCE AI BOT STARTED"
)

bot.infinity_polling(
    skip_pending=True
)
