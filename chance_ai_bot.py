import os
import requests
import telebot
from telebot import types

# =========================================
# CONFIG
# =========================================
TOKEN = os.getenv("TG_TOKEN") or os.getenv("BOT_TOKEN")
CHANCE_APP_ID = os.getenv("CHANCE_APP_ID")
CHANCE_API_KEY = os.getenv("CHANCE_API_KEY")

if not TOKEN:
    raise ValueError("❌ TG_TOKEN חסר ב-Railway Variables")
if not CHANCE_APP_ID:
    raise ValueError("❌ CHANCE_APP_ID חסר")
if not CHANCE_API_KEY:
    raise ValueError("❌ CHANCE_API_KEY חסר")

BASE_URL = "https://api.base44.com/v1"

bot = telebot.TeleBot(TOKEN)
print("🚀 Chance Predictor Bot התחיל לעבוד")

# =========================================
# HEADERS
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
    try:
        response = requests.get(
            f"{BASE_URL}/entities/Prediction",
            headers=get_headers(),
            params={"sort_by": "-created_date", "limit": 1},
            timeout=15
        )
        print(f"📡 Prediction API Status: {response.status_code}")

        if response.status_code != 200:
            print("Error Response:", response.text)
            return None

        data = response.json()
        # טיפול במבנים שונים של תשובה
        if isinstance(data, list):
            return data
        return data.get("records") or data.get("data") or data.get("results") or []

    except Exception as e:
        print("❌ Prediction Fetch Error:", e)
        return None


def fetch_draws():
    try:
        response = requests.get(
            f"{BASE_URL}/entities/Draw",
            headers=get_headers(),
            params={"sort_by": "-draw_number", "limit": 10},
            timeout=15
        )
        print(f"📡 Draws API Status: {response.status_code}")

        if response.status_code != 200:
            return None

        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("records") or data.get("data") or data.get("results") or []

    except Exception as e:
        print("❌ Draws Fetch Error:", e)
        return None


def fetch_accuracy():
    try:
        response = requests.get(
            f"{BASE_URL}/entities/PredictionResult",
            headers=get_headers(),
            params={"sort_by": "-draw_number", "limit": 10},
            timeout=15
        )
        print(f"📡 Accuracy API Status: {response.status_code}")

        if response.status_code != 200:
            return None

        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("records") or data.get("data") or data.get("results") or []

    except Exception as e:
        print("❌ Accuracy Fetch Error:", e)
        return None


# =========================================
# MENU
# =========================================
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🔮 תחזית", "🎰 הגרלות")
    markup.add("🎯 Accuracy", "ℹ️ על הבוט")
    return markup


# =========================================
# HANDLERS
# =========================================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🤖 *Chance Predictor Bot*\n\n"
        "ברוך הבא למערכת התחזיות החכמה 🎰",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text.strip()

    if text == "🔮 תחזית":
        predictions = fetch_predictions()
        if not predictions:
            bot.send_message(message.chat.id, "❌ אין תחזיות זמינות כרגע\nאו בעיית חיבור ל-Base44", reply_markup=main_menu())
            return

        p = predictions[0] if isinstance(predictions, list) else predictions
        msg = f"""🔮 *תחזית חדשה*

🎯 הגרלה מס' {p.get('target_draw_number', '—')}

♠️ ספייד: *{p.get('main_spade', '—')}*
❤️ לב: *{p.get('main_heart', '—')}*
♦️ יהלום: *{p.get('main_diamond', '—')}*
♣️ תלתן: *{p.get('main_club', '—')}*

✨ חיזוק 1: {p.get('reinforcement_1', '—')}
✨ חיזוק 2: {p.get('reinforcement_2', '—')}
🤖 מודל: {p.get('method', 'Quantum')}"""

        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

    elif text == "🎰 הגרלות":
        draws = fetch_draws()
        if not draws:
            bot.send_message(message.chat.id, "❌ אין נתוני הגרלות זמינים", reply_markup=main_menu())
            return

        msg = "🎰 *10 הגרלות אחרונות*\n\n"
        for d in draws[:10]:
            msg += f"#{d.get('draw_number', '—')} → ♠️{d.get('spade','—')} ❤️{d.get('heart','—')} ♦️{d.get('diamond','—')} ♣️{d.get('club','—')}\n"
        
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

    elif text == "🎯 Accuracy":
        results = fetch_accuracy()
        if not results:
            bot.send_message(message.chat.id, "❌ אין נתוני דיוק זמינים", reply_markup=main_menu())
            return

        msg = "🎯 *דיוק התחזיות*\n\n"
        for r in results[:10]:
            msg += f"#{r.get('draw_number', '—')} | {r.get('method','—')} | Hits: {r.get('hit_count', 0)}/4\n"
        
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

    elif text == "ℹ️ על הבוט":
        bot.send_message(
            message.chat.id,
            "🤖 *Chance Predictor*\n\n"
            "מערכת תחזיות מבוססת Base44\n"
            "פותח על ידי חיים 🚀\n\n"
            "שחק באחריות!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    else:
        bot.send_message(
            message.chat.id,
            "❌ לא הבנתי\nבחר אחת מהאפשרויות בתפריט 👇",
            reply_markup=main_menu()
        )


# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    print("✅ BOT IS RUNNING SUCCESSFULLY")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
