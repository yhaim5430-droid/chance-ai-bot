import os
import requests
import telebot
from telebot import types

# =========================================
# CONFIG
# =========================================

TOKEN = os.getenv("TG_TOKEN") or os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ TG_TOKEN חסר")

CHANCE_APP_ID = os.getenv("CHANCE_APP_ID")
CHANCE_API_KEY = os.getenv("CHANCE_API_KEY")

if not CHANCE_APP_ID:
    raise ValueError("❌ CHANCE_APP_ID חסר")

if not CHANCE_API_KEY:
    raise ValueError("❌ CHANCE_API_KEY חסר")

# חשוב:
# החלף לכתובת API האמיתית שלך מ-Base44
BASE_URL = f"https://api.base44.com/v1"

bot = telebot.TeleBot(TOKEN)

print("🚀 Chance AI Bot Started")

# =========================================
# MENU
# =========================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )

    markup.add(
        "🔮 תחזית",
        "🎰 הגרלות"
    )

    markup.add(
        "🎯 Accuracy",
        "ℹ️ על הבוט"
    )

    return markup

# =========================================
# BASE44 API
# =========================================

def get_headers():
    return {
        "appId": CHANCE_APP_ID,
        "api_key": CHANCE_API_KEY,
        "Content-Type": "application/json"
    }

# =========================================
# FETCH FUNCTIONS
# =========================================

def fetch_predictions():

    url = f"{BASE_URL}/entities/Prediction"

    params = {
        "sort_by": "-created_date",
        "limit": 1
    }

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=15
        )

        print("Prediction Status:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            if "records" in data:
                return data["records"]

            if "data" in data:
                return data["data"]

            if "results" in data:
                return data["results"]

        return []

    except Exception as e:
        print("Prediction Error:", e)
        return []


def fetch_draws():

    url = f"{BASE_URL}/entities/Draw"

    params = {
        "sort_by": "-draw_number",
        "limit": 10
    }

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=15
        )

        print("Draw Status:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            if "records" in data:
                return data["records"]

            if "data" in data:
                return data["data"]

            if "results" in data:
                return data["results"]

        return []

    except Exception as e:
        print("Draw Error:", e)
        return []


def fetch_accuracy():

    url = f"{BASE_URL}/entities/PredictionResult"

    params = {
        "sort_by": "-draw_number",
        "limit": 10
    }

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=15
        )

        print("Accuracy Status:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            if "records" in data:
                return data["records"]

            if "data" in data:
                return data["data"]

            if "results" in data:
                return data["results"]

        return []

    except Exception as e:
        print("Accuracy Error:", e)
        return []

# =========================================
# START
# =========================================

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "🤖 *Chance AI Bot*\n\n"
        "ברוך הבא למערכת התחזיות 🎰\n\n"
        "בחר אפשרות:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# =========================================
# MESSAGES
# =========================================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):

    text = message.text.strip()

    # =====================================
    # PREDICTION
    # =====================================

    if text == "🔮 תחזית":

        predictions = fetch_predictions()

        if not predictions:

            bot.send_message(
                message.chat.id,
                "❌ אין תחזיות כרגע\n\n"
                "או שיש בעיית חיבור ל-Base44",
                reply_markup=main_menu()
            )

            return

        p = predictions[0]

        msg = (
            f"🔮 *Chance AI Prediction*\n\n"

            f"🎯 הגרלה: #{p.get('target_draw_number', '—')}\n\n"

            f"♠️ ספייד: *{p.get('main_spade', '—')}*\n"
            f"❤️ לב: *{p.get('main_heart', '—')}*\n"
            f"♦️ יהלום: *{p.get('main_diamond', '—')}*\n"
            f"♣️ תלתן: *{p.get('main_club', '—')}*\n\n"

            f"✨ חיזוק 1: {p.get('reinforcement_1', '—')}\n"
            f"✨ חיזוק 2: {p.get('reinforcement_2', '—')}\n\n"

            f"🤖 מודל: {p.get('method', 'Quantum')}"
        )

        bot.send_message(
            message.chat.id,
            msg,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # =====================================
    # DRAWS
    # =====================================

    elif text == "🎰 הגרלות":

        draws = fetch_draws()

        if not draws:

            bot.send_message(
                message.chat.id,
                "❌ אין נתוני הגרלות",
                reply_markup=main_menu()
            )

            return

        msg = "🎰 *10 הגרלות אחרונות*\n\n"

        for d in draws:

            msg += (
                f"#{d.get('draw_number', '—')} → "
                f"♠️{d.get('spade', '—')} "
                f"❤️{d.get('heart', '—')} "
                f"♦️{d.get('diamond', '—')} "
                f"♣️{d.get('club', '—')}\n"
            )

        bot.send_message(
            message.chat.id,
            msg,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # =====================================
    # ACCURACY
    # =====================================

    elif text == "🎯 Accuracy":

        results = fetch_accuracy()

        if not results:

            bot.send_message(
                message.chat.id,
                "❌ אין נתוני Accuracy",
                reply_markup=main_menu()
            )

            return

        msg = "🎯 *Prediction Accuracy*\n\n"

        for r in results:

            msg += (
                f"#{r.get('draw_number', '—')} | "
                f"{r.get('method', '—')} | "
                f"Hits: {r.get('hit_count', 0)}/4\n"
            )

        bot.send_message(
            message.chat.id,
            msg,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # =====================================
    # ABOUT
    # =====================================

    elif text == "ℹ️ על הבוט":

        bot.send_message(
            message.chat.id,
            "🤖 *Chance AI Bot*\n\n"
            "מערכת תחזיות צ'אנס חכמה\n"
            "מבוססת Base44\n\n"
            "פותח על ידי חיים 🚀",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # =====================================
    # UNKNOWN
    # =====================================

    else:

        bot.send_message(
            message.chat.id,
            "❌ לא הבנתי\nבחר אפשרות מהתפריט",
            reply_markup=main_menu()
        )

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    print("✅ BOT IS RUNNING")

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30
    )
