# ═══════════════════════════════════════════
# 🧠 AI POSITION CORRECTION ENGINE
# מנוע AI לזיהוי קלפים "במיקום שגוי"
# ═══════════════════════════════════════════

def detect_position_patterns(predictions, results):
    """
    מזהה דפוסים שבהם הקלף נחזה נכון אך במיקום אחר.
    לדוגמה:
    נחזה ♠8 ובפועל ♥8 → המערכת תלמד ש-8 זז ממיקום ספייד ללב.
    """

    pattern_stats = {
        "spade_to_heart": 0,
        "spade_to_diamond": 0,
        "spade_to_club": 0,

        "heart_to_spade": 0,
        "heart_to_diamond": 0,
        "heart_to_club": 0,

        "diamond_to_spade": 0,
        "diamond_to_heart": 0,
        "diamond_to_club": 0,

        "club_to_spade": 0,
        "club_to_heart": 0,
        "club_to_diamond": 0,
    }

    try:
        for pred in predictions:
            if not isinstance(pred, dict):
                continue

            draw_number = pred.get("target_draw_number")

            matching_result = None

            for res in results:
                if res.get("draw_number") == draw_number:
                    matching_result = res
                    break

            if not matching_result:
                continue

            predicted = {
                "spade": str(pred.get("main_spade")),
                "heart": str(pred.get("main_heart")),
                "diamond": str(pred.get("main_diamond")),
                "club": str(pred.get("main_club")),
            }

            actual = {
                "spade": str(matching_result.get("spade")),
                "heart": str(matching_result.get("heart")),
                "diamond": str(matching_result.get("diamond")),
                "club": str(matching_result.get("club")),
            }

            for p_pos, p_card in predicted.items():
                for a_pos, a_card in actual.items():

                    if p_pos == a_pos:
                        continue

                    if p_card == a_card:
                        key = f"{p_pos}_to_{a_pos}"

                        if key in pattern_stats:
                            pattern_stats[key] += 1

    except Exception as e:
        print(f"AI Pattern Error: {e}")

    return pattern_stats


# ═══════════════════════════════════════════
# 🧠 AI SMART RECOMMENDATION
# מציע שינוי מיקום חכם אם זוהה דפוס חזק
# ═══════════════════════════════════════════

def build_ai_suggestion(prediction, patterns):
    """
    אם AI מזהה שקלף מסויים נוטה לזוז למיקום אחר —
    הוא יציע טופס נוסף עם שינוי מיקום.
    """

    if not prediction or not isinstance(prediction, dict):
        return ""

    suggestion = []

    cards = {
        "spade": prediction.get("main_spade"),
        "heart": prediction.get("main_heart"),
        "diamond": prediction.get("main_diamond"),
        "club": prediction.get("main_club"),
    }

    threshold = 3

    try:

        if patterns.get("spade_to_heart", 0) >= threshold:
            suggestion.append(
                f"♠️{cards['spade']} ➜ ❤️ "
                f"(AI זיהה שהקלף נוטה לעבור מעלים ללב)"
            )

        if patterns.get("heart_to_spade", 0) >= threshold:
            suggestion.append(
                f"❤️{cards['heart']} ➜ ♠️ "
                f"(AI זיהה מעבר קבוע מלב לעלה)"
            )

        if patterns.get("diamond_to_club", 0) >= threshold:
            suggestion.append(
                f"♦️{cards['diamond']} ➜ ♣️ "
                f"(דפוס מעבר יהלום → תלתן)"
            )

        if patterns.get("club_to_diamond", 0) >= threshold:
            suggestion.append(
                f"♣️{cards['club']} ➜ ♦️ "
                f"(AI זיהה היפוך תלתן → יהלום)"
            )

    except Exception as e:
        print(f"AI Suggestion Error: {e}")

    if not suggestion:
        return ""

    msg = "\n🧠 <b>AI Position Correction</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"

    for s in suggestion:
        msg += f"• {s}\n"

    msg += "\n💡 המערכת זיהתה דפוסי היפוך מיקום בהגרלות קודמות."

    return msg


# ═══════════════════════════════════════════
# עדכון fetch_prediction_results
# שולף גם תוצאות אמיתיות
# ═══════════════════════════════════════════

async def fetch_prediction_results():
    return await make_base44_request(
        "PredictionResult",
        {
            "sort_by": "-draw_number",
            "limit": "30"
        }
    )


# ═══════════════════════════════════════════
# עדכון build_free_recommendation
# מוסיף AI POSITION ANALYSIS
# ═══════════════════════════════════════════

def build_free_recommendation(records, ai_text=""):

    if not records or not isinstance(records, list):
        return "❌ אין נתוני חיזוי מעודכנים."

    human_pred = None

    for p in records:
        if isinstance(p, dict) and "Human" in str(p.get("method")):
            human_pred = p
            break

    if not human_pred:
        human_pred = records[0]

    txt = (
        f"⭐ <b>Quantum Human v5.0</b>\n"
        f"🎯 יעד: <b>#{human_pred.get('target_draw_number','—')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"

        f"♠️ עלה: <b>{human_pred.get('main_spade','—')}</b>\n"
        f"❤️ לב: <b>{human_pred.get('main_heart','—')}</b>\n"
        f"♦️ יהלום: <b>{human_pred.get('main_diamond','—')}</b>\n"
        f"♣️ תלתן: <b>{human_pred.get('main_club','—')}</b>\n"
    )

    if ai_text:
        txt += f"\n{ai_text}"

    txt += "\n\n<i>⬡ Chance AI Predictor</i>"

    return txt


# ═══════════════════════════════════════════
# בתוך callback_handler
# עדכן btn_free
# ═══════════════════════════════════════════

if data == "btn_free":

    await query.edit_message_text(
        "🧠 <i>AI מנתח דפוסי מיקום והיפוכים...</i>",
        parse_mode="HTML"
    )

    predictions = await fetch_predictions()
    results = await fetch_prediction_results()

    ai_patterns = detect_position_patterns(
        predictions,
        results
    )

    ai_text = ""

    if predictions:
        ai_text = build_ai_suggestion(
            predictions[0],
            ai_patterns
        )

    text = build_free_recommendation(
        predictions,
        ai_text
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=action_menu("btn_free")
    )

    return
