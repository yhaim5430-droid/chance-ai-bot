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
ברוך הבא למערכת התחזיות החכמה 🎰

🤖 מנוע AI משופר
📊 מבוסס על היסטוריית הגרלות
🧠 דירוג הסתברותי
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# ================= 🎯 SMART AI PREDICTION =================
@bot.message_handler(func=lambda m: m.text == "🎯 חיזוי הבא")
def next_prediction(message):
    orch = Orchestrator()
    
    data = get_data("Draw", 1)
    last_draw = data[0].get("draw_number") if data and len(data) > 0 else None

    result = orch.generate_best_prediction(target_draw=last_draw)

    best = result["prediction"]
    score = result["score"]
    target = result["target_draw"]
    history_size = result.get("history_size", 0)

    text = f"""
🎯 **SMART PREDICTION ENGINE** 🔄

🎰 **Target Draw:** {target if target else 'Unknown'}

♠️ **Spade:**    {best['spade']}
♥️ **Heart:**    {best['heart']}
♦️ **Diamond:**  {best['diamond']}
♣️ **Club:**     {best['club']}

📊 **Confidence:** {score}/100
📈 **Based on:** {history_size} הגרלות אחרונות

✅ נתונים טריים • מודל הסתברותי
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= ⚡ QUICK PREDICTION =================
@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):
    data = get_data("Prediction", 5)
    if not data:
        bot.send_message(message.chat.id, "❌ אין תחזיות זמינות")
        return
    text = "⚡ **חיזויים מהירים אחרונים**\n\n"
    for p in data:
        text += f"""
🎰 Draw {p.get('target_draw_number')}
♠️ {p.get('main_spade')} ♥️ {p.get('main_heart')} ♦️ {p.get('main_diamond')} ♣️ {p.get('main_club')}
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= 📊 STATISTICS =================
@bot.message_handler(func=lambda m: m.text == "📊 סטטיסטיקות")
def stats(message):
    draws = get_data("Draw", 100)
    text = f"""
📊 **סטטיסטיקות מערכת**
🎰 הגרלות שנאספו: {len(draws) if draws else 0}
🤖 AI Engine: **Active**
📈 מודל הסתברות: **עדכני**
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= 🔥 HOT CARDS =================
@bot.message_handler(func=lambda m: m.text == "🔥 Hot Cards")
def hot_cards(message):
    data = get_data("Draw", 100)
    cards = []
    if data:
        for d in data:
            cards += [d.get(k) for k in ["spade","heart","diamond","club"] if d.get(k)]
    counter = Counter(cards)
    text = "🔥 **Hot Cards** (100 הגרלות)\n\n"
    for card, count in counter.most_common(6):
        text += f"{card} → {count} פעמים\n"
    bot.send_message(message.chat.id, text)

# ================= ❄️ COLD CARDS =================
@bot.message_handler(func=lambda m: m.text == "❄️ Cold Cards")
def cold_cards(message):
    data = get_data("Draw", 100)
    all_cards = ["7","8","9","10","J","Q","K","A"]
    cards = []
    if data:
        for d in data:
            cards += [d.get(k) for k in ["spade","heart","diamond","club"] if d.get(k)]
    counter = Counter(cards)
    text = "❄️ **Cold Cards**\n\n"
    for c in all_cards:
        count = counter.get(c, 0)
        text += f"{c} → {count} פעמים\n"
    bot.send_message(message.chat.id, text)

# ================= 📜 HISTORY =================
@bot.message_handler(func=lambda m: m.text == "📜 היסטוריה")
def history(message):
    data = get_data("Draw", 10, "-draw_number")
    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return
    text = "📜 **10 הגרלות אחרונות**\n\n"
    for d in data:
        text += f"#{d.get('draw_number')} → ♠️{d.get('spade')} ♥️{d.get('heart')} ♦️{d.get('diamond')} ♣️{d.get('club')}\n"
    bot.send_message(message.chat.id, text)

# ================= OTHER BUTTONS =================
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text
    if text in ["🧠 AI Analysis", "📈 Top Patterns", "🪞 Mirror", "🔄 Reverse", "🧪 Quantum", "👑 VIP", "🔔 התראות", "ℹ️ מערכת"]:
        bot.send_message(message.chat.id, f"✅ {text} - פעיל / בפיתוח")
    else:
        bot.send_message(message.chat.id, "❌ בחר אפשרות מהתפריט", reply_markup=main_menu())

# ================= RUN =================
print("🚀 CHANCE AI BOT RUNNING - v2.2")
bot.infinity_polling(skip_pending=True)
