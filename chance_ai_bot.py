import os
import telebot
from telebot import types

# ==================== CONFIG ====================
TOKEN = os.getenv("TG_TOKEN")   # ← שינוי חשוב כאן

if not TOKEN:
    raise ValueError("❌ TG_TOKEN לא נמצא! בדוק ב-Railway Variables.")

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
        "שלום! 👋\nאני **Chance AI Bot**.\nמה ברצונך לעשות?",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "פקודות זמינות:\n/start\n/help", reply_markup=main_menu())

# ==================== MESSAGES ====================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text.strip()

    if text == "👋 שלום":
        bot.send_message(message.chat.id, "שלום! מה קורה? 😊", reply_markup=main_menu())
    
    elif text == "❓ עזרה":
        bot.send_message(message.chat.id, "אני בוט פשוט.\nאפשר לשוחח איתי!", reply_markup=main_menu())
    
    elif text == "🔄 איפוס":
        bot.send_message(message.chat.id, "הבוט אופס בהצלחה ✅", reply_markup=main_menu())
    
    elif text == "ℹ️ על הבוט":
        bot.send_message(message.chat.id, "Chance AI Bot\nמפותח על ידי חיים 🚀", reply_markup=main_menu())
    
    else:
        bot.send_message(message.chat.id, f"קיבלתי: {text}", reply_markup=main_menu())


# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("✅ Chance AI Bot התחיל לעבוד בהצלחה!")
    bot.infinity_polling()
