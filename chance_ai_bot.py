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

# הגדרות API ל-Base44
BASE44_HEADERS = {
    "app_id": "699f6d52f3302128ab050b10",
    "api_key": "20742ca24625436b8963159c29dd34c3"
}
DRAW_URL = "https://api.base44.io/entities/Draw"

# פונקציית שליפה יציבה מה-API
def get_draws():
    try:
        # שליפת 10 אחרונות לפי מספר הגרלה יורד
        response = requests.get(DRAW_URL, headers=BASE44_HEADERS, params={"limit": 10, "sort_by": "-draw_number"})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"שגיאה בחיבור ל-Base44: {e}")
    return None

# שרת HealthCheck בסיסי
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args): pass

def run_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

# לוגיקת הבוט
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["⭐ המלצה חינם"], ["🎰 10 הגרלות אחרונות"]]
    await update.message.reply_text("שלום! בחר מהתפריט:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "10 הגרלות אחרונות" in text:
        await update.message.reply_text("טוען נתונים מהמערכת...")
        data = get_draws()
        if data and isinstance(data, list):
            msg = "🎰 **10 ההגרלות האחרונות:**\n\n"
            for d in data:
                msg += f"הגרלה {d['draw_number']}: ♠{d.get('spade')} ♥{d.get('heart')} ♦{d.get('diamond')} ♣{d.get('club')}\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("לא הצלחתי למשוך נתונים כרגע.")
    else:
        await update.message.reply_text("בחר אפשרות מהתפריט.")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()
