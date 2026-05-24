import logging
import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרות מערכת
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 10000))

# הגדרות Base44
BASE44_HEADERS = {
    "app_id": "699f6d52f3302128ab050b10",
    "api_key": "20742ca24625436b8963159c29dd34c3"
}
BASE44_API_URL = "https://api.base44.io/entities/Draw"

# ========== תקשורת עם Base44 ==========
def get_last_10_draws_from_base44():
    params = {
        "limit": 10,
        "sort_by": "-draw_number"
    }
    try:
        response = requests.get(BASE44_API_URL, headers=BASE44_HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Base44 API Error: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Connection failed: {e}")
        return None

# ========== שרת Health ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chance Bot is running and connected to Base44!")

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

# ========== לוגיקת תפריט ==========
def main_menu():
    return ReplyKeyboardMarkup([["⭐ המלצה חינם"], ["🎰 10 הגרלות אחרונות"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ברוך הבא לבוט החיזויים!", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "10 הגרלות אחרונות" in text:
        draws = get_last_10_draws_from_base44()
        if draws:
            msg = "🎰 <b>10 ההגרלות האחרונות:</b>\n\n"
            for d in draws:
                msg += f"הגרלה {d['draw_number']}: ♠{d['spade']} ♥{d['heart']} ♦{d['diamond']} ♣{d['club']}\n"
            await update.message.reply_html(msg)
        else:
            await update.message.reply_text("מצטער, כרגע לא ניתן למשוך נתונים. נסה שוב מאוחר יותר.")
    else:
        await update.message.reply_text("בחר אפשרות מהתפריט:", reply_markup=main_menu())

# ========== הפעלה ==========
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot is running...")
    app.run_polling()
