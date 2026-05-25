import os
import telebot
from telebot import types

# ==================== CONFIG ====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN לא נמצא! הוסף אותו ב-Variables ב-Railway.")

bot = telebot.TeleBot(TOKEN)

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "שלום! 👋\nאני Chance AI Bot.\nמה קורה?")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "פקודות:\n/start\n/help")


@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"קיבלתי: {message.text}")


# ==================== START BOT ====================
if __name__ == "__main__":
    print("✅ Chance AI Bot התחיל לעבוד...")
    bot.infinity_polling()
