import logging
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8724235550:AAGU3ZSvXWt46VLZs01S6XJD1WRep3ZZNzA")
OWNER_ID = 6775881845

def main_menu(premium=False):
    keyboard = [
        ["⭐ המלצה חינם", "🎰 10 הגרלות אחרונות"],
        ["💳 רכישת מנוי", "👑 אזור VIP" if premium else "👑 פרמיום"],
        ["👥 חבר מביא חבר", "❓ שאלות ותשובות"],
        ["📞 יצירת קשר"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "חבר"
    await update.message.reply_html(
        f"👋 שלום <b>{name}</b>!\n\n"
        f"🃏 ברוך הבא ל-<b>♣️♦️ CHANCE PREDICTOR ♠️❤️</b>\n\n"
        f"🔓 גרסה חינמית — שדרג לפרמיום!\n"
        f"💳 250₪/חודש | 2,500₪/שנה\n\n"
        f"בחר אפשרות 👇",
        reply_markup=main_menu()
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

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy_monthly":
        await query.message.reply_html(
            "💳 <b>תשלום — מנוי חודשי (250₪)</b>\n\n"
            "1️⃣ בצע העברה בנקאית / קוד משיכה\n"
            "2️⃣ שלח <b>צילום מסך</b> של ההעברה כאן\n"
            "3️⃣ המנוי יופעל תוך 24 שעות ✅"
        )
        context.user_data["plan"] = "monthly"
        context.user_data["price"] = 250

    elif data == "buy_yearly":
        await query.message.reply_html(
            "💳 <b>תשלום — מנוי שנתי (2,500₪)</b>\n\n"
            "1️⃣ בצע העברה בנקאית / קוד משיכה\n"
            "2️⃣ שלח <b>צילום מסך</b> של ההעברה כאן\n"
            "3️⃣ המנוי יופעל תוך 24 שעות ✅"
        )
        context.user_data["plan"] = "yearly"
        context.user_data["price"] = 2500

    elif data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        plan = data.split("_")[2]
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 <b>המנוי הופעל!</b>\n👑 ברוך הבא לפרמיום!\nגישה מלאה לכל הפיצ'רים 🚀",
            parse_mode="HTML",
            reply_markup=main_menu(premium=True)
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ <b>אושר!</b>",
            parse_mode="HTML"
        )

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>ההוכחה לא אושרה.</b>\nלבירורים לחץ על 📞 יצירת קשר",
            parse_mode="HTML"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <b>נדחה</b>",
            parse_mode="HTML"
        )

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

    if "רכישת" in text or "💳" in text or "מנוי" in text:
        await handle_buy(update, context)
    elif "פרמיום" in text or "👑" in text or "VIP" in text or "אזור" in text:
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
            "🔹 <b>תשלום?</b> העברה בנקאית / קוד משיכה\n"
            "🔹 <b>הפעלה?</b> תוך 24 שעות מרגע אישור\n"
            "🔹 <b>חבר מביא חבר?</b> 2 חברים משלמים = חודש חינם!\n"
            "🔹 <b>מה ההבדל?</b> חינם: המלצה אחת | פרמיום: 4 מודלים + מועצה"
        )
    elif "קשר" in text or "📞" in text:
        await update.message.reply_html(
            "📞 <b>יצירת קשר</b>\n\n"
            "פנה ישירות למנהל\n"
            "⏰ זמן תגובה: עד 24 שעות\n"
            "<i>מנויים VIP מקבלים עדיפות 👑</i>"
        )
    elif "המלצה" in text or "⭐" in text:
        await update.message.reply_html(
            "⭐ <b>המלצה חינם</b>\n\n"
            "חיזוי מלא (4 מודלים + ניתוח מועצה) זמין למנויים VIP בלבד 👑\n\n"
            "לחץ על 💳 <b>רכישת מנוי</b> לגישה מלאה!"
        )
    elif "הגרלות" in text or "🎰" in text:
        await update.message.reply_html(
            "🎰 <b>10 הגרלות אחרונות</b>\n\n"
            "ניתוח מלא + היסטוריה מפורטת זמינים למנויים VIP בלבד 👑"
        )
    else:
        await update.message.reply_text("בחר אפשרות מהתפריט 👇", reply_markup=main_menu())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 בוט רץ...")
    app.run_polling()

if __name__ == "__main__":
    main()
