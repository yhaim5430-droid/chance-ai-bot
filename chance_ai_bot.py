import os
from telebot import TeleBot

from core.orchestrator import Orchestrator

# =========================
# 🔐 TOKEN (בטוח לפרודקשן)
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN לא מוגדר ב-ENV (Railway / Render)")

bot = TeleBot(TOKEN)


# =========================
# 📦 נתונים (תחליף לפי Base44 שלך)
# =========================
def get_data(table_name, limit):
    """
    ⚠️ זה placeholder בלבד
    חבר כאן את Base44 / DB שלך
    """
    return []


# =========================
# ⚡ חיזוי מהיר (Base44)
# =========================
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
#{p.get('target_draw_number', '')}

♠️ {p.get('main_spade', '')}
♥️ {p.get('main_heart', '')}
♦️ {p.get('main_diamond', '')}
♣️ {p.get('main_club', '')}

🔥 חיזוקים:
1) {p.get('reinforcement_1', '')}
2) {p.get('reinforcement_2', '')}

────────────────────
"""

    bot.send_message(message.chat.id, text)


# =========================
# 🎯 חיזוי הבא (AI Engine)
# =========================
@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    draws = get_data("History", 50)

    if not draws:
        bot.send_message(message.chat.id, "❌ אין היסטוריה לניתוח")
        return

    orchestrator = Orchestrator(draws)

    result = orchestrator.predict()

    prediction = result.get("prediction", {})

    text = f"""
🎯 חיזוי הבא (AI Engine)

🎰 הגרלה יעד:
#{result.get('target_draw', '')}

♠️ {prediction.get('spade', '')}
♥️ {prediction.get('heart', '')}
♦️ {prediction.get('diamond', '')}
♣️ {prediction.get('club', '')}

📊 Score:
{result.get('score', 0)}/100

🧠 Confidence:
{result.get('confidence', 0)}%

⚠️ Risk:
{result.get('confidence_level', '')}

Why selected:
{result.get('report', '')}
"""

    bot.send_message(message.chat.id, text)


# =========================
# 🚀 הפעלה
# =========================
if __name__ == "__main__":
    print("🚀 CHANCE AI BOT STARTED")
    bot.infinity_polling(skip_pending=True)
