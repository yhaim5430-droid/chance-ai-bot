```python
import os
import json
import aiohttp

from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ════════════════════════════════
# ENV
# ════════════════════════════════

TG_TOKEN = os.getenv("TG_TOKEN")

CHANCE_APP_ID = os.getenv("CHANCE_APP_ID")
CHANCE_API_KEY = os.getenv("CHANCE_API_KEY")

BASE_URL = "https://api.base44.com/v1"

# ════════════════════════════════
# DATABASE
# ════════════════════════════════

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


# ════════════════════════════════
# BASE44 API
# ════════════════════════════════

async def make_base44_request(entity_name, params=None):

    if not CHANCE_APP_ID or not CHANCE_API_KEY:
        print("❌ Missing Base44 credentials")
        return []

    headers = {
        "appId": CHANCE_APP_ID,
        "api_key": CHANCE_API_KEY,
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/entities/{entity_name}"

    print(f"📡 REQUEST: {url}")

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=20
            ) as response:

                print(f"📡 STATUS: {response.status}")

                if response.status != 200:
                    text = await response.text()

                    print(f"❌ API ERROR {response.status}")
                    print(text)

                    return []

                data = await response.json()

                print("✅ API SUCCESS")

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
        print(f"❌ BASE44 ERROR: {e}")
        return []


async def fetch_predictions():

    return await make_base44_request(
        "Prediction",
        {
            "sort_by": "-created_date",
            "limit": "10"
        }
    )


async def fetch_draws():

    return await make_base44_request(
        "Draw",
        {
            "sort_by": "-draw_number",
            "limit": "10"
        }
    )


async def fetch_hits():

    return await make_base44_request(
        "PredictionResult",
        {
            "sort_by": "-draw_number",
            "limit": "10"
        }
    )


# ════════════════════════════════
# BUILDERS
# ════════════════════════════════

def build_prediction_message(records):

    if not records:
        return "❌ אין תחזיות"

    p = records[0]

    return (
        f"🔮 תחזית אחרונה\n\n"

        f"🎯 הגרלה #{p.get('target_draw_number', '—')}\n\n"

        f"♠️ {p.get('main_spade', '—')}\n"
        f"❤️ {p.get('main_heart', '—')}\n"
        f"♦️ {p.get('main_diamond', '—')}\n"
        f"♣️ {p.get('main_club', '—')}\n\n"

        f"✨ {p.get('reinforcement_1', '—')}\n"
        f"✨ {p.get('reinforcement_2', '—')}"
    )


def build_draws_message(records):

    if not records:
        return "❌ אין הגרלות"

    text = "🎰 10 הגרלות אחרונות\n\n"

    for d in records:

        text += (
            f"#{d.get('draw_number', '—')} | "
            f"♠️{d.get('spade', '—')} "
            f"❤️{d.get('heart', '—')} "
            f"♦️{d.get('diamond', '—')} "
            f"♣️{d.get('club', '—')}\n"
        )

    return text


def build_hits_message(records):

    if not records:
        return "❌ אין נתונים"

    text = "🎯 Accuracy\n\n"

    for r in records:

        text += (
            f"#{r.get('draw_number', '—')} "
            f"| Hits {r.get('hit_count', 0)}/4\n"
        )

    return text


# ════════════════════════════════
# MENU
# ════════════════════════════════

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔮 תחזית",
                callback_data="prediction"
            ),

            InlineKeyboardButton(
                "🎰 הגרלות",
                callback_data="draws"
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 Accuracy",
                callback_data="hits"
            )
        ]
    ])


# ════════════════════════════════
# START
# ════════════════════════════════

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    db = load_db()

    if str(user.id) not in db["users"]:

        db["users"][str(user.id)] = {
            "id": user.id,
            "name": user.first_name,
            "joined": datetime.now().isoformat()
        }

        save_db(db)

    await update.message.reply_text(
        (
            f"🤖 Chance AI Bot\n\n"
            f"שלום {user.first_name}\n\n"
            f"בחר אפשרות:"
        ),
        reply_markup=main_menu()
    )


# ════════════════════════════════
# CALLBACKS
# ════════════════════════════════

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "prediction":

        await query.edit_message_text(
            "🔄 טוען תחזיות..."
        )

        predictions = await fetch_predictions()

        text = build_prediction_message(
            predictions
        )

        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )

    elif data == "draws":

        await query.edit_message_text(
            "🔄 טוען הגרלות..."
        )

        draws = await fetch_draws()

        text = build_draws_message(draws)

        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )

    elif data == "hits":

        await query.edit_message_text(
            "🔄 מחשב..."
        )

        hits = await fetch_hits()

        text = build_hits_message(hits)

        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )


# ════════════════════════════════
# MESSAGE
# ════════════════════════════════

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "שלח /start"
    )


# ════════════════════════════════
# MAIN
# ════════════════════════════════

def main():

    if not TG_TOKEN:
        print("❌ TG_TOKEN missing")
        return

    print("🚀 Bot Starting...")

    app = (
        Application
        .builder()
        .token(TG_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
```
