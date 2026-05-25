import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN לא נמצא! הוסף אותו ב-Railway Variables.")

bot = telebot.TeleBot(TOKEN)

# ==================== MENU ====================

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("👋 שלום", "❓ עזרה")
    markup.add("🔄 איפוס", "ℹ️ על הבוט")
    return markup

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "שלום! 👋\n"
        "אני **Chance AI Bot**.\n"
        "מה ברצונך לעשות?",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "פקודות זמינות:\n"
        "/start - התחלה\n"
        "/help - עזרה",
        reply_markup=main_menu()
    )


# ==================== TEXT MESSAGES ====================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text.strip()

    if text == "👋 שלום":
        bot.send_message(message.chat.id, "שלום! מה קורה? 😊", reply_markup=main_menu())

    elif text == "❓ עזרה":
        bot.send_message(message.chat.id, "אני בוט פשוט כרגע.\nאפשר לשוחח איתי!", reply_markup=main_menu())

    elif text == "🔄 איפוס":
        bot.send_message(message.chat.id, "הבוט אופס בהצלחה ✅", reply_markup=main_menu())

    elif text == "ℹ️ על הבוט":
        bot.send_message(
            message.chat.id,
            "Chance AI Bot\n\n"
            "בוט פשוט לפי שעה.\n"
            "מפותח על ידי חיים 🚀",
            reply_markup=main_menu()
        )

    else:
        # Echo + תגובה חכמה קצת
        bot.send_message(
            message.chat.id,
            f"קיבלתי: {text}\n\nמה עוד אפשר לעשות?",
            reply_markup=main_menu()
        )


# ==================== START BOT ====================
if __name__ == "__main__":
    print("✅ Chance AI Bot התחיל לעבוד...")
    bot.infinity_polling()
