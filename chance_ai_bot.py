@bot.message_handler(func=lambda m: m.text == "⚡ חיזוי מהיר")
def quick_prediction(message):

    data = get_data("Prediction", 4)

    if not data:
        bot.send_message(message.chat.id, "❌ אין נתונים")
        return

    text = "⚡️ חיזוי מהיר (Base44)\n\n"

    for i, p in enumerate(data):

        text += f"""
🎯 חיזוי #{i+1}

🎰 הגרלה יעד:
#{float(p.get('target_draw_number'))}

♠️ {p.get('main_spade')}
♥️ {p.get('main_heart')}
♦️ {p.get('main_diamond')}
♣️ {p.get('main_club')}

🔥 חיזוקים:
1) {p.get('reinforcement_1')}
2) {p.get('reinforcement_2')}

────────────────────
"""

    bot.send_message(message.chat.id, text)
