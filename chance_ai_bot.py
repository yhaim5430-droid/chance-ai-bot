import logging
import os
import json
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = 6775881845
PORT = int(os.environ.get("PORT", 10000))

GITHUB_RAW_URL = "https://raw.githubusercontent.com/yhaim5430-droid/chance-ai-bot/main/prediction_latest.json"

PREMIUM_USERS = set()
FREE_PRED_USED = {}

# ========== שרת HTTP קטן כדי ש-Render לא יסגור ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chance Bot is running!")
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logging.info(f"Health server running on port {PORT}")
    server.serve_forever()

# ========== תפריט ==========
def main_menu(premium=False):
    keyboard = [
        ["⭐ המלצה חינם", "🎰 10 הגרלות אחרונות"],
        ["💎 מנוי פרימיום", "❓ עזרה"],
        ["📞 יצירת קשר"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== פונקציות עזר ==========
def fetch_data():
    try:
        with urllib.request.urlopen(GITHUB_RAW_URL) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return None

# ========== הנדלרים ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    premium = user_id in PREMIUM_USERS or user_id == OWNER_ID
    await update.message.reply_text("ברוכים הבאים לבוט ה-Chance AI!", reply_markup=main_menu(premium))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    premium = user_id in PREMIUM_USERS or user_id == OWNER_ID

    if "המלצה חינם" in text:
        data = fetch_data()
        if data:
            pred = data.get("baseline", {})
            msg = (f"⭐ <b>המלצה להגרלה {data.get('draw')}</b>\n\n"
                   f"♠ עלה: {pred.get('spade')}\n♥ לב: {pred.get('heart')}\n"
                   f"♦ יהלום: {pred.get('diamond')}\n♣ תלתן: {pred.get('club')}")
            await update.message.reply_html(msg)
        else:
            await update.message.reply_text("כרגע אין נתונים זמינים. נסה שוב מאוחר יותר.")

    elif "10 הגרלות אחרונות" in text:
        await update.message.reply_text("פונקציה זו בבנייה...")

    elif "עזרה" in text or "❓" in text:
        await update.message.reply_html(
            "❓ <b>שאלות ותשובות</b>\n\n"
            "🔹 <b>מחיר?</b> 250₪/חודש | 2,500₪/שנה\n"
            "🔹 <b>איך מקבלים חיזוי?</b> לחץ ⭐ המלצה חינם\n"
            "🔹 <b>מתי מתעדכנים חיזויים?</b> לפני כל הגרלה\n"
            "🔹 <b>שאלה אחרת?</b> לחץ 📞 יצירת קשר"
        )
    elif "קשר" in text or "📞" in text:
        await update.message.reply_html(
            "📞 <b>יצירת קשר</b>\n\n"
            "לכל שאלה או בעיה — פנה ישירות:\n"
            "👤 @yhaim5430_droid\n\n"
            "⏰ זמן תגובה: עד 24 שעות"
        )
    else:
        await update.message.reply_html("👇 בחר אפשרות מהתפריט", reply_markup=main_menu(premium))

# ========== הפעלה ==========
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN לא מוגדר!")

    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
