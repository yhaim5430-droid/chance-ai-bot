import os
import asyncio
import json
import aiohttp
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# ENV
# =========================

TG_TOKEN = os.getenv("TG_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHAT_ID = os.getenv("CHAT_ID", "")

CHANCE_APP_ID = os.getenv("CHANCE_APP_ID")
CHANCE_API_KEY = os.getenv("CHANCE_API_KEY")

BASE_URL = "https://api.base44.com/v1"

# =========================
# DB
# =========================

DB_FILE = "users.json"


def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}}


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# =========================
# BASE44 API
# =========================

async def make_base44_request(entity_name, params=None):

    headers = {
        "appId": CHANCE_APP_ID,
        "api_key": CHANCE_API_KEY,
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/entities/{entity_name}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:

                if response.status != 200:
                    print(f"❌ API ERROR {response.status}")
                    return []

                data = await response.json()

                if isinstance(data, list):
                    return data

                if isinstance(data, dict):
                    return data.get("records") or data.get("data") or data.get("results") or []

                return []

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []


async def fetch_predictions():
    return await make_base44_request("Prediction", {
        "sort_by": "-created_date",
        "limit": "10"
    })


async def fetch_draws():
    return await make_base44_request("Draw", {
        "sort_by": "-draw_number",
        "limit": "10"
    })


async def fetch_results():
    return await make_base44_request("PredictionResult", {
        "sort_by": "-draw_number",
        "limit": "10"
    })


# =========================
# UI
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔮 תחזית", callback_data="prediction"),
            InlineKeyboardButton("🎰 הגרלות", callback_data="draws"),
        ],
        [
            InlineKeyboardButton("🎯 Accuracy", callback_data="hits"),
        ]
    ])


# =========================
# HANDLERS
# =========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Chance AI Bot\nלחץ על כפתור:",
        reply_markup=main_menu()
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "prediction":
        data = await fetch_predictions()
        await query.edit_message_text(f"🔮 תחזיות:\n{data}", reply_markup=main_menu())

    elif query.data == "draws":
        data = await fetch_draws()
        await query.edit_message_text(f"🎰 הגרלות:\n{data}", reply_markup=main_menu())

    elif query.data == "hits":
        data = await fetch_results()
        await query.edit_message_text(f"🎯 תוצאות:\n{data}", reply_markup=main_menu())


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלח /start")


# =========================
# AUTO LOOP
# =========================

async def auto_scan_loop(app):
    await asyncio.sleep(5)

    while True:
        try:
            preds = await fetch_predictions()

            if preds:
                latest = preds[0]
                draw_number = latest.get("target_draw_number")

                if CHAT_ID:
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"🔮 תחזית חדשה להגרלה #{draw_number}"
                    )

        except Exception as e:
            print(f"LOOP ERROR: {e}")

        await asyncio.sleep(60)


# =========================
# MAIN
# =========================

def main():

    if not TG_TOKEN:
        print("❌ Missing TG_TOKEN")
        return

    print("🚀 Bot Starting...")

    app = Application.builder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    async def post_init(application):
        asyncio.create_task(auto_scan_loop(application))

    app.post_init = post_init

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
