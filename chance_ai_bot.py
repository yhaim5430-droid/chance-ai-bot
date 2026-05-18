import logging
import os
import json
import urllib.request
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = 6775881845

GITHUB_RAW_URL = "https://raw.githubusercontent.com/yhaim5430-droid/chance-ai-bot/main/prediction_latest.json"

# רשימת מנויים פעילים (user_id)
PREMIUM_USERS = set()

# מעקב חיזוי חינם יומי — {user_id: "YYYY-MM-DD"}
FREE_PRED_USED = {}

def main_menu(premium=False):
    keyboard = [
        ["⭐ המלצה חינם", "🎰 10 הגרלות אחרונות"],
        ["💳 רכישת מנוי", "👑 אזור VIP" if premium else "👑 פרמיום"],
        ["👥 חבר מביא חבר", "❓ שאלות ותשובות"],
        ["📞 יצירת קשר"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def is_premium(user_id):
    return user_id in PREMIUM_USERS or user_id == OWNER_ID

def get_prediction_from_github():
    """
    קורא את החיזוי האחרון מ-GitHub JSON — חינם לחלוטין!
    """
    try:
        req = urllib.request.Request(
            GITHUB_RAW_URL,
            headers={"Cache-Control": "no-cache", "User-Agent": "ChanceBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data
    except Exception as e:
        logging.error(f"שגיאה בקריאת GitHub: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name or "חבר"
    premium = is_premium(user_id)
    await update.message.reply_html(
        f"👋 שלום <b>{name}</b>!\n\n"
        f"🃏 ברוך הבא ל-<b>♣️♦️ CHANCE PREDICTOR ♠️❤️</b>\n\n"
        + (f"👑 <b>מנוי פרמיום פעיל!</b>\n" if premium else
           f"🔓 גרסה חינמית — שדרג לפרמיום!\n💳 250₪/חודש | 2,500₪/שנה\n") +
        f"\nבחר אפשרות 👇",
        reply_markup=main_menu(premium)
    )

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 חודשי — 250₪", callback_data="buy_monthly")],
        [InlineKeyboardButton("📆 שנתי — 2,500₪ (חסוך 500₪!)", callback_data="buy_yearly")]
    ])
    await update.message.reply_html(
        "💳 <b>רכישת מנוי פרמיום</b>\n\n"
        "👑 <b>מה כלול:</b>\n"
        "• 4 מודלי חיזוי מלאים\n"
        "• ניתוח מועצה (דן, רון, מיכאל, אלון)\n"
        "• קלפים חמים/קרים\n"
        "• עדכונים לפני כל הגרלה\n\n"
        "בחר תכנית:",
        reply_markup=keyboard
    )

async def handle_free_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.now().strftime("%Y-%m-%d")

    # בדוק אם כבר השתמש היום
    if FREE_PRED_USED.get(user_id) == today and user_id != OWNER_ID:
        await update.message.reply_html(
            "⭐ <b>המלצה חינם</b>\n\n"
            "⏰ כבר קיבלת את החיזוי החינמי שלך היום!\n\n"
            "לחיזויים מלאים לפני <b>כל הגרלה</b> + ניתוח מועצה מלא 👑\n"
            "לחץ על 💳 <b>רכישת מנוי</b>"
        )
        return

    # סמן שהשתמש היום
    FREE_PRED_USED[user_id] = today

    # קרא חיזוי מ-GitHub
    pred = get_prediction_from_github()

    if pred and pred.get("draw_number", "?") != "?":
        draw_num = pred.get("draw_number", "?")
        spade   = pred.get("spade", "?")
        heart   = pred.get("heart", "?")
        diamond = pred.get("diamond", "?")
        club    = pred.get("club", "?")
        conf    = pred.get("confidence", "?")
        updated = pred.get("updated", "")

        await update.message.reply_html(
            f"⭐ <b>חיזוי חינם יומי</b>\n"
            f"<i>Baseline — ללא ניתוח מועצה</i>\n\n"
            f"🎯 הגרלה מס' <b>{draw_num}</b>\n\n"
            f"♠️ עלה:   <b>{spade}</b>\n"
            f"❤️ לב:    <b>{heart}</b>\n"
            f"♦️ יהלום: <b>{diamond}</b>\n"
            f"♣️ תלתן:  <b>{club}</b>\n\n"
            f"📊 ביטחון: <b>{conf}</b>\n"
            f"🕐 עודכן: {updated}\n\n"
            f"🔒 לחיזוי מלא + ניתוח מועצה לפני <b>כל הגרלה</b>\n"
            f"שדרג ל-👑 פרמיום!"
        )
    else:
        await update.message.reply_html(
            "⭐ <b>חיזוי חינם</b>\n\n"
            "⏳ החיזוי הבא עוד לא זמין — יתעדכן לפני ההגרלה הבאה.\n\n"
            "🔔 לקבלת עדכונים מיידיים שדרג ל-👑 פרמיום!"
        )

async def handle_last_10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_premium(user_id):
        await update.message.reply_html(
            "🎰 <b>10 הגרלות האחרונות</b>\n\n"
            "🔒 תוכן זה זמין <b>למנויים בלבד</b>\n\n"
            "לחץ על 💳 <b>רכישת מנוי</b> לגישה מלאה 👑"
        )
        return

    # קרא מ-GitHub
    pred = get_prediction_from_github()
    if pred:
        await update.message.reply_html(
            f"🎰 <b>הגרלה אחרונה</b>\n\n"
            f"🔹 <b>#{pred.get('draw_number','?')}</b>  "
            f"♠️{pred.get('spade','?')}  "
            f"❤️{pred.get('heart','?')}  "
            f"♦️{pred.get('diamond','?')}  "
            f"♣️{pred.get('club','?')}\n\n"
            f"<i>נתונים נוספים בקרוב...</i>"
        )
    else:
        await update.message.reply_html("❌ לא ניתן לטעון נתונים כרגע. נסה שוב מאוחר יותר.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy_monthly":
        await query.message.reply_html(
            "💳 <b>תשלום — מנוי חודשי (250₪)</b>\n\n"
            "1️⃣ בצע העברה בנקאית / ביט / פייבוקס\n"
            "2️⃣ שלח <b>צילום מסך</b> של ההעברה כאן\n"
            "3️⃣ המנוי יופעל תוך 24 שעות ✅"
        )
        context.user_data["plan"] = "monthly"
        context.user_data["price"] = 250

    elif data == "buy_yearly":
        await query.message.reply_html(
            "💳 <b>תשלום — מנוי שנתי (2,500₪)</b>\n\n"
            "1️⃣ בצע העברה בנקאית / ביט / פייבוקס\n"
            "2️⃣ שלח <b>צילום מסך</b> של ההעברה כאן\n"
            "3️⃣ המנוי יופעל תוך 24 שעות ✅"
        )
        context.user_data["plan"] = "yearly"
        context.user_data["price"] = 2500

    elif data.startswith("approve_"):
        parts = data.split("_")
        user_id = int(parts[1])
        plan = parts[2] if len(parts) > 2 else "monthly"
        PREMIUM_USERS.add(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 <b>המנוי הופעל!</b>\n👑 ברוך הבא לפרמיום!\nגישה מלאה לכל הפיצ'רים 🚀",
            parse_mode="HTML",
            reply_markup=main_menu(premium=True)
        )
        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>אושר!</b>",
                parse_mode="HTML"
            )
        except Exception:
            await query.message.reply_html("✅ המנוי אושר!")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>ההוכחה לא אושרה.</b>\nלבירורים לחץ על 📞 יצירת קשר",
            parse_mode="HTML"
        )
        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ <b>נדחה</b>",
                parse_mode="HTML"
            )
        except Exception:
            await query.message.reply_html("❌ הבקשה נדחתה.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = context.user_data.get("plan", "monthly")
    price = context.user_data.get("price", 250)
    file_id = update.message.photo[-1].file_id

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ אשר מנוי", callback_data=f"approve_{user.id}_{plan}"),
        InlineKeyboardButton("❌ דחה", callback_data=f"reject_{user.id}")
    ]])

    caption = (
        f"💳 <b>בקשת מנוי חדשה!</b>\n"
        f"👤 {user.first_name} {user.last_name or ''}\n"
        f"🆔 {user.id}\n"
        f"📱 @{user.username or 'אין'}\n"
        f"📅 {'חודשי' if plan == 'monthly' else 'שנתי'} — {price}₪"
    )

    await context.bot.send_photo(
        chat_id=OWNER_ID,
        photo=file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await update.message.reply_html(
        "✅ <b>תודה! ההוכחה התקבלה.</b>\n"
        "המנוי יופעל תוך 24 שעות לאחר אישור 🎉"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.effective_user.id
    premium = is_premium(user_id)

    if "רכישת" in text or "💳" in text:
        await handle_buy(update, context)
    elif "מנוי" in text and "רכישת" not in text:
        await handle_buy(update, context)
    elif "המלצה" in text or "⭐" in text:
        await handle_free_prediction(update, context)
    elif "10 הגרלות" in text or "🎰" in text:
        await handle_last_10(update, context)
    elif "פרמיום" in text or "👑" in text or "VIP" in text or "אזור" in text:
        if premium:
            await update.message.reply_html("👑 <b>אזור VIP</b>\n\nהמנוי שלך פעיל! גישה מלאה לכל הפיצ'רים ✅")
        else:
            await update.message.reply_html("🔒 <b>אזור VIP — מנויים בלבד</b>\n\nלחץ על 💳 <b>רכישת מנוי</b> להצטרפות!")
    elif "חבר" in text or "👥" in text:
        ref_link = f"https://t.me/CHANCEAihaybot?start=ref_{user_id}"
        await update.message.reply_html(
            f"👥 <b>חבר מביא חבר!</b>\n\n"
            f"שתף את הלינק שלך:\n<code>{ref_link}</code>\n\n"
            f"🎁 על כל <b>2 חברים</b> שמשלמים — חודש חינם!"
        )
    elif "שאלות" in text or "❓" in text:
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
        await update.message.reply_html(
            "👇 בחר אפשרות מהתפריט",
            reply_markup=main_menu(premium)
        )

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN לא מוגדר!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logging.info("🤖 בוט מופעל...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
