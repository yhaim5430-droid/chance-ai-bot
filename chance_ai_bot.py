import os
import telebot
import random
from telebot import types

# ==================== CONFIG ====================
# תומך גם ב-TG_TOKEN וגם ב-BOT_TOKEN
TOKEN = os.getenv("TG_TOKEN") or os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ לא נמצא TG_TOKEN או BOT_TOKEN! בדוק ב-Railway Variables.")

bot = telebot.TeleBot(TOKEN)

# ==================== MAIN MENU ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("⭐ המלצה חינם", "🎰 הגרלה מלאה")
    markup.add("📊 סטטיסטיקות", "ℹ️ על הבוט")
    return markup

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "♣️♦️ **CHANCE PREDICTOR** ♠️♥️\n\n"
        "ברוך הבא! 🎰\n"
        "אני כאן כדי לתת לך המלצות להגרלות ולוטו.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "לחץ על הכפתורים בתפריט 👇", reply_markup=main_menu())

# ==================== MESSAGES ====================
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text.strip()

    if text == "⭐ המלצה חינם":
        numbers = sorted(random.sample(range(1, 38), 6))
        bot.send_message(
            message.chat.id,
            f"⭐ **המלצה חינם להגרלה:**\n\n"
            f"🎟️ {numbers}\n\n"
            f"בהצלחה! 🍀",
            reply_markup=main_menu()
        )

    elif text == "🎰 הגרלה מלאה":
        bot.send_message(
            message.chat.id,
            "בחר סוג הגרלה:\n• לוטו\n• חישגד\n• 777",
            reply_markup=main_menu()
        )

    elif text == "📊 סטטיסטיקות":
        bot.send_message(
            message.chat.id,
            "📈 סטטיסטיקות חמות יגיעו בקרוב...",
            reply_markup=main_menu()
        )

    elif text == "ℹ️ על הבוט":
        bot.send_message(
            message.chat.id,
            "♣️♦️ **CHANCE PREDICTOR** ♠️♥️\n\n"
            "בוט המלצות והגרלות.\n"
            "מפותח על ידי חיים 🚀\n\n"
            "שחק באחריות!",
            reply_markup=main_menu()
        )

    else:
        bot.send_message(
            message.chat.id,
            "לא הבנתי 😅\nלחץ על אחד מהכפתורים בתפריט.",
            reply_markup=main_menu()
        )


# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("✅ CHANCE PREDICTOR התחיל לעבוד בהצלחה!")
    bot.infinity_polling()
