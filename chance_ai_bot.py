import os
import telebot
from telebot import types

# ==================== CONFIG ====================
TOKEN = os.getenv("BOT_TOKEN")  # שים את הטוקן ב-Railway Environment Variables

if not TOKEN:
    raise ValueError("BOT_TOKEN לא נמצא! הוסף אותו ב-Railway.")

bot = telebot.TeleBot(TOKEN)

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "שלום! 👋\n"
        "אני Chance AI Bot.\n"
        "איך אני יכול לעזור לך היום?")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, 
        "פקודות זמינות:\n"
        "/start - התחלה\n"
        "/help - עזרה")


# Echo - מחזיר את ההודעה של המשתמש (לדוגמה)
@bot.message_handler(func=lambda message: True)
def echo(message):
    try:
        bot.reply_to(message, f"קיבלתי: {message.text}")
    except Exception as e:
        bot.reply_to(message, "הייתה שגיאה, נסה שוב.")


# ==================== POLLING ====================
if __name__ == "__main__":
    print("✅ Chance AI Bot רץ...")
    bot.infinity_polling()
