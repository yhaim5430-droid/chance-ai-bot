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
if not BASE44_API_KEY or not BASE44_APP_ID:
    raise Exception("❌ חסרים מפתחות API")

bot = telebot.TeleBot(TOKEN)

BASE_URL = f"https://app.base44.com/api/apps/{BASE44_APP_ID}"
HEADERS = {
    "api_key": BASE44_API_KEY,
    "Content-Type": "application/json"
}

# ================= HELPERS =================
def get_data(entity, limit=10, sort="-created_date"):
    try:
        url = f"{BASE_URL}/entities/{entity}?limit={limit}&sort_by={sort}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"שגיאה {response.status_code}"}
    except Exception as e:
        return {"error": f"שגיאת חיבור: {str(e)}"}

# ================= MENU =================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("🎯 חיזוי הבא", "⚡ חיזוי מהיר")
    markup.row("📊 סטטיסטיקות", "🔥 Hot Cards")
    markup.row("❄️ Cold Cards", "📜 היסטוריה")
    markup.row("🧠 AI Analysis", "📈 Top Patterns")
    markup.row("🪞 Mirror", "🔄 Reverse")
    markup.row("🧪 Quantum", "👑 VIP")
    markup.row("ℹ️ מערכת")
    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    text = """
♣️♦️ **CHANCE AI BOT** ♠️♥️
ברוך הבא למערכת חיזוי חכמה v2.4
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# ================= 🎯 חיזוי הבא =================
@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):
    try:
        orch = Orchestrator()
        data = get_data("Draw", 1)
        
        if isinstance(data, dict) and "error" in data:
            bot.send_message(message.chat.id, data["error"])
            return

        last_draw = data[0].get("draw_number") if isinstance(data, list) and len(data) > 0 else None

        result = orch.generate_best_prediction(target_draw=last_draw)
        
        best = result["prediction"]
        score = result["score"]
        target = result["target_draw"]
        history_size = result.get("history_size", 0)

        text = f"""
🎯 **חיזוי חכם למשיכה הבאה**

🎰 **Target Draw:** {target if target else 'Unknown'}

♠️ **Spade:**    {best.get('spade', '?')}
♥️ **Heart:**    {best.get('heart', '?')}
♦️ **Diamond:**  {best.get('diamond', '?')}
♣️ **Club:**     {best.get('club', '?')}

📊 **Confidence:** {score}/100
📈 מבוסס על {history_size} הגרלות
"""
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ שגיאה בחיזוי:\n{str(e)}")

# ================= שאר הכפתורים (עובדים) =================
@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):
    data = get_data("Prediction", 5)
    if isinstance(data, dict) and "error" in data:
        bot.send_message(message.chat.id, data["error"])
        return
    text = "⚡ **חיזויים מהירים**\n\n"
    for p in data[:5]:
        text += f"🎰 {p.get('target_draw_number')} → ♠️{p.get('main_spade')} ♥️{p.get('main_heart')} ♦️{p.get('main_diamond')} ♣️{p.get('main_club')}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 סטטיסטיקות")
def stats(message):
    draws = get_data("Draw", 50)
    count = len(draws) if isinstance(draws, list) else 0
    bot.send_message(message.chat.id, f"📊 **סטטיסטיקות**\n• הגרלות: {count}\n• AI: פעיל")

@bot.message_handler(func=lambda m: m.text == "🔥 Hot Cards")
def hot_cards(message):
    data = get_data("Draw", 100)
    cards = []
    if isinstance(data, list):
        for d in data:
            cards += [d.get(k) for k in ["spade","heart","diamond","club"] if d.get(k)]
    counter = Counter(cards)
    text = "🔥 **Hot Cards**\n\n"
    for card, count in counter.most_common(6):
        text += f"{card} → {count}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "❄️ Cold Cards")
def cold_cards(message):
    data = get_data("Draw", 100)
    all_cards = ["7","8","9","10","J","Q","K","A"]
    cards = []
    if isinstance(data, list):
        for d in data:
            cards += [d.get(k) for k in ["spade","heart","diamond","club"] if d.get(k)]
    counter = Counter(cards)
    text = "❄️ **Cold Cards**\n\n"
    for c in all_cards:
        text += f"{c} → {counter.get(c, 0)}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text
    responses = {
        "🧠 AI Analysis": "🧠 מנתח את הנתונים...",
        "📈 Top Patterns": "📈 מחשב דפוסים...",
        "🪞 Mirror": "🪞 Mirror Mode פעיל",
        "🔄 Reverse": "🔄 Reverse Mode פעיל",
        "🧪 Quantum": "🧪 Quantum Engine פעיל",
        "👑 VIP": "👑 VIP Mode פעיל",
        "ℹ️ מערכת": "🤖 Chance AI v2.4 - מערכת חיזוי מבוססת היסטוריה"
    }
    bot.send_message(message.chat.id, responses.get(text, "✅ פעיל"))

# ================= RUN =================
print("🚀 CHANCE AI BOT RUNNING - v2.4")
bot.infinity_polling(skip_pending=True)
