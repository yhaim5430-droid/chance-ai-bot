import os
import asyncio
import json
import aiohttp

from datetime import datetime, timedelta

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
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHAT_ID = os.getenv("CHAT_ID", "")

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
        return {
            "users": {}
        }


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def is_admin(user_id):
    return int(user_id) == ADMIN_ID


def get_user(user_id):
    db = load_db()
    return db["users"].get(str(user_id))


def is_subscribed(user_id):
    if is_admin(user_id):
        return True

    user = get_user(user_id)

    if not user:
        return False

    expiry = user.get("expiry")

    if not expiry:
        return False

    try:
        return datetime.fromisoformat(expiry) > datetime.now()
    except:
        return False


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

    try:
        async with aiohttp.ClientSession() as session:

            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=15
            ) as response:

                if response.status != 200:
                    print(f"❌ API ERROR {response.status}")
                    return []

                data = await response.json()

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


async def fetch_prediction_results():
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
        return "❌ אין תחזיות כרגע"

    p = records[0]

    return (
        f"🔮 <b>Chance AI Prediction</b>\n\n"

        f"🎯 הגרלה: #{p.get('target_draw_number', '—')}\n\n"

        f"♠️ ספייד: <b>{p.get('main_spade', '—')}</b>\n"
        f"❤️ לב: <b>{p.get('main_heart', '—')}</b>\n"
        f"♦️ יהלום: <b>{p.get('main_diamond', '—')}</b>\n"
        f"♣️ תלתן: <b>{p.get('main_club', '—')}</b>\n\n"

        f"✨ חיזוק 1: {p.get('reinforcement_1', '—')}\n"
        f"✨ חיזוק 2: {p.get('reinforcement_2', '—')}\n\n"

        f"🤖 מודל: {p.get('method', 'Quantum')}"
    )


def build_draws_message(draws):

    if not draws:
        return "❌ אין תוצאות"

    text = "🎰 <b>10 הגרלות אחרונות</b>\n\n"

    for d in draws:

        text += (
            f"#{d.get('draw_number', '—')} → "
            f"♠️{d.get('spade', '—')} "
            f"❤️{d.get('heart', '—')} "
            f"♦️{d.get('diamond', '—')} "
            f"♣️{d.get('club', '—')}\n"
        )

    return text


def build_hits_message(results):

    if not results:
        return "❌ אין נתוני Hit"

    text = "🎯 <b>Prediction Accuracy</b>\n\n"

    for r in results:

        hit_count = r.get("hit_count", 0)

        text += (
            f"#{r.get('draw_number', '—')} | "
            f"{r.get('method', '—')} | "
            f"Hits: {hit_count}/4\n"
        )

    return text


# ════════════════════════════════
# MENUS
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

async def cmd_start(
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

    status = (
        "👑 VIP"
        if is_subscribed(user.id)
        else "❌ Free"
    )

    text = (
        f"🤖 <b>Chance AI Bot</b>\n\n"

        f"שלום {user.first_name}\n"
        f"סטטוס: {status}\n\n"

        f"בחר אפשרות:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
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

    # ─────────────────────────

    if data == "prediction":

        await query.edit_message_text(
            "🔄 טוען תחזיות...",
            parse_mode="HTML"
        )

        predictions = await fetch_predictions()

        text = build_prediction_message(predictions)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        return

    # ─────────────────────────

    if data == "draws":

        await query.edit_message_text(
            "🔄 טוען הגרלות...",
            parse_mode="HTML"
        )

        draws = await fetch_draws()

        text = build_draws_message(draws)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        return

    # ─────────────────────────

    if data == "hits":

        await query.edit_message_text(
            "🔄 מחשב Accuracy...",
            parse_mode="HTML"
        )

        results = await fetch_prediction_results()

        text = build_hits_message(results)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        return


# ════════════════════════════════
# AUTO LOOP
# ════════════════════════════════

async def auto_scan_loop(app):

    await asyncio.sleep(10)

    last_draw = None

    while True:

        try:

            predictions = await fetch_predictions()

            if predictions:

                latest = predictions[0]

                draw_number = latest.get(
                    "target_draw_number"
                )

                if draw_number != last_draw:

                    last_draw = draw_number

                    text = (
                        f"🔮 תחזית חדשה!\n\n"
                        f"🎯 הגרלה #{draw_number}"
                    )

                    if CHAT_ID:

                        await app.bot.send_message(
                            chat_id=CHAT_ID,
                            text=text
                        )

        except Exception as e:
            print(f"LOOP ERROR: {e}")

        await asyncio.sleep(60)


# ════════════════════════════════
# MESSAGE HANDLER
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

    print("🚀 Starting Chance AI Bot")

    app = (
        Application
        .builder()
        .token(TG_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", cmd_start)
    )

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    async def post_init(application):
        asyncio.create_task(
            auto_scan_loop(application)
        )

    app.post_init = post_init

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
