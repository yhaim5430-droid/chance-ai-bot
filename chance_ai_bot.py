import os
import telebot
import random
from telebot import types

TOKEN = os.getenv("TG_TOKEN")

if not TOKEN:
    raise ValueError("❌ TG_TOKEN לא נמצא!")

bot = telebot.TeleBot(TOKEN)

# ==================== MAIN MENU ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("⭐ המלצה חינם", "🎰 הגרלה מלאה")import os
import telebot
import random
from telebot import types

TOKEN = os.getenv("TG_TOKEN")

if not TOKEN:
    raise ValueError("❌ TG_TOKEN לא נמצא!")

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
        numbers = sorted(random.sample(range(1, 38), 6))   # לוטו ישראלי לדוגמה
        bot.send_message(
            message.chat.id,
            f"⭐ **המלצה חינם להגרלה הבאה:**\n\n"
            f"🎟️ {numbers}\n\n"
            f"בהצלחה! 🍀",
            reply_markup=main_menu()
        )

    elif text == "🎰 הגרלה מלאה":
        bot.send_message(
            message.chat.id,
            "🔢 בחר סוג הגרלה:\n"
            "• לוטו (6 מתוך 37)\n"
            "• חישגד (7 מתוך 70)\n"
            "• 777\n"
            "שלח לי את השם של ההגרלה שתרצה.",
            reply_markup=main_menu()
        )

    elif text == "📊 סטטיסטיקות":
        bot.send_message(
            message.chat.id,
            "📈 *סטטיסטיקות*\n\n"
            "עדיין אין נתונים...\n"
            "בקרוב אוסיף סטטיסטיקות חמות 🔥",
            reply_markup=main_menu()
        )

    elif text == "ℹ️ על הבוט":
        bot.send_message(
            message.chat.id,
            "♣️♦️ **CHANCE PREDICTOR** ♠️♥️\n\n"
            "בוט חיזוי והמלצות להגרלות.\n"
            "מפותח על ידי חיים 🚀\n\n"
            "בהצלחה ותמיד לשחק באחריות!",
            reply_markup=main_menu()
        )

    else:
        bot.send_message(
            message.chat.id,
            "לא הבנתי 😅\nלחץ על אחד מהכפתורים בתפריט.",
            reply_markup=main_menu()
        )


# ==================== RUN ====================
if __name__ == "__main__":
    print("✅ CHANCE PREDICTOR התחיל לעבוד...")
    bot.infinity_polling()
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
        numbers = sorted(random.sample(range(1, 38), 6))   # לוטו ישראלי לדוגמה
        bot.send_message(
            message.chat.id,
            f"⭐ **המלצה חינם להגרלה הבאה:**\n\n"
            f"🎟️ {numbers}\n\n"
            f"בהצלחה! 🍀",
            reply_markup=main_menu()
        )

    elif text == "🎰 הגרלה מלאה":
        bot.send_message(
            message.chat.id,
            "🔢 בחר סוג הגרלה:\n"
            "• לוטו (6 מתוך 37)\n"
            "• חישגד (7 מתוך 70)\n"
            "• 777\n"
            "שלח לי את השם של ההגרלה שתרצה.",
            reply_markup=main_menu()
        )

    elif text == "📊 סטטיסטיקות":
        bot.send_message(
            message.chat.id,
            "📈 *סטטיסטיקות*\n\n"
            "עדיין אין נתונים...\n"
            "בקרוב אוסיף סטטיסטיקות חמות 🔥",
            reply_markup=main_menu()
        )

    elif text == "ℹ️ על הבוט":
        bot.send_message(
            message.chat.id,
            "♣️♦️ **CHANCE PREDICTOR** ♠️♥️\n\n"
            "בוט חיזוי והמלצות להגרלות.\n"
            "מפותח על ידי חיים 🚀\n\n"
            "בהצלחה ותמיד לשחק באחריות!",
            reply_markup=main_menu()
        )

    else:
        bot.send_message(
            message.chat.id,
            "לא הבנתי 😅\nלחץ על אחד מהכפתורים בתפריט.",
            reply_markup=main_menu()
        )


# ==================== RUN ====================
if __name__ == "__main__":
    print("✅ CHANCE PREDICTOR התחיל לעבוד...")
    bot.infinity_polling()
