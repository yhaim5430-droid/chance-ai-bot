from telebot import TeleBot

from core.orchestrator import Orchestrator
from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine

# ❗ כאן אתה צריך את הפונקציה שלך שמביאה נתונים מ־Base44 / DB
# תשאיר כמו שיש לך בפועל
def get_data(table_name, limit):
    return []  # placeholder - אל תשאיר ככה בפרודקשן


TOKEN = "YOUR_BOT_TOKEN"
bot = TeleBot(TOKEN)


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


# =========================
# 🎯 חיזוי הבא (AI Engine)
# =========================
@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):

    draws = get_data("History", 50)

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


# =========================
# 🚀 הפעלה
# =========================
if __name__ == "__main__":
    print("🚀 CHANCE AI BOT STARTED")
    bot.infinity_polling(skip_pending=True)
