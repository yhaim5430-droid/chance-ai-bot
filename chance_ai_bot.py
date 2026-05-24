import os
import asyncio
import aiohttp
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ═══════════════════════════════════════════
# הגדרות מאובטחות וחיבור ל-Base44 API
# ═══════════════════════════════════════════
TG_TOKEN  = os.environ.get("TG_TOKEN",  "7754804245:AAEf5lCTTU3NB7qNnOa1-HKJXcpZLDOdseM")
CHAT_ID   = os.environ.get("CHAT_ID",   "-1002360888694") # מזהה קבוצת הטלגרם של העדכונים האוטומטיים
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "6775881845"))

# פרטי החיבור הרשמיים לפי המפרט ששלחת:
CHANCE_APP_ID  = "699f6d52f3302128ab050b10"
CHANCE_API_KEY = "20742ca24625436b8963159c29dd34c3"
BASE_URL       = "https://api.base44.com/v1"

# ── פרטי תשלום ──
PAYMENT_INFO = {
    "bit":    "שלח לביט למספר: *יתקבל לאחר פנייה בתמיכה*",
    "paybox": "שלח לפייבוקס למספר: *יתקבל לאחר פנייה בתמיכה*",
    "bank":   (
        "🏦 בנק הבינלאומי הראשון לישראל\n"
        "סניף: 062 — קרית גת\n"
        "מספר חשבון: 259794\n"
        "מספר IBAN/זיהוי: 034653667\n"
        "מדינה: ישראל"
    ),
}

PRICES = {
    "trial":   {"name": "ניסיון חינמי",  "price": 0,    "days": 3},
    "monthly": {"name": "מנוי חודשי",    "price": 300,  "days": 30},
    "yearly":  {"name": "מנוי שנתי",     "price": 3000, "days": 365},
}

# ═══════════════════════════════════════════
# מסד נתונים פנימי לניהול מנויי הבוט
# ═══════════════════════════════════════════
DB_FILE      = "users.json"
BLOCKED_FILE = "blocked.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"users": {}, "pending": {}, "referrals": {}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=2, ensure_ascii=False)

def load_blocked():
    try:
        with open(BLOCKED_FILE, "r") as f: return json.load(f)
    except: return {"blocked": [], "attempts": {}}

def save_blocked(data):
    with open(BLOCKED_FILE, "w") as f: json.dump(data, f, indent=2)

def is_blocked(user_id): return str(user_id) in load_blocked()["blocked"]
def is_admin(user_id): return int(user_id) == ADMIN_ID
def get_user(user_id): return load_db()["users"].get(str(user_id))

def is_subscribed(user_id):
    if is_admin(user_id): return True
    user = get_user(user_id)
    if not user or not user.get("expiry"): return False
    return datetime.fromisoformat(user["expiry"]) > datetime.now()

def get_expiry_str(user_id):
    user = get_user(user_id)
    if not user or not user.get("expiry"): return "—"
    exp  = datetime.fromisoformat(user["expiry"])
    days = max(0, (exp - datetime.now()).days)
    return f"{exp.strftime('%d/%m/%Y')} ({days} ימים)"

def add_subscription(user_id, username, plan_key, days):
    db  = load_db()
    uid = str(user_id)
    now = datetime.now()
    usr = db["users"].get(uid, {})
    cur = usr.get("expiry")
    base = datetime.fromisoformat(cur) if cur and datetime.fromisoformat(cur) > now else now
    exp  = base + timedelta(days=days)

    db["users"][uid] = {
        "user_id": user_id, "username": username, "plan": plan_key, "expiry": exp.isoformat(),
        "joined": usr.get("joined", now.isoformat()), "trial_used": True if plan_key == "trial" else usr.get("trial_used", False),
        "referrals_count": usr.get("referrals_count", 0), "referral_code": f"REF{user_id}"
    }
    save_db(db)

def add_referral(referrer_id, new_user_id):
    db  = load_db()
    rid = str(referrer_id)
    if "referrals" not in db: db["referrals"] = {}
    if rid not in db["referrals"]: db["referrals"][rid] = []
    if str(new_user_id) not in db["referrals"][rid]:
        db["referrals"][rid].append(str(new_user_id))
        count = len(db["referrals"][rid])
        usr   = db["users"].get(rid, {})
        db["users"][rid] = {**usr, "referrals_count": count}
        save_db(db)
        return count
    return len(db["referrals"].get(rid, []))

# ═══════════════════════════════════════════
# פונקציות קריאה מותאמות למפרט ה-API של Base44
# ═══════════════════════════════════════════
async def make_base44_request(entity_name, params=None):
    """פונקציה מרכזית לביצוע בקשות מאובטחות ל-API בהתאם למפרט שסיפקת"""
    headers = {
        "appId": CHANCE_APP_ID,
        "api_key": CHANCE_API_KEY,
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/entities/{entity_name}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as r:
                if r.status == 200:
                    res = await r.json()
                    # טיפול גמיש במבנה התשובה למניעת קריסות
                    if isinstance(res, list):
                        return res
                    if isinstance(res, dict):
                        return res.get("records", res.get("data", [res]))
                print(f"⚠️ שגיאת API בישות {entity_name}, סטטוס קוד: {r.status}")
    except Exception as e:
        print(f"❌ שגיאת חיבור חמורה בבקשת {entity_name}: {e}")
    return []

# ═══════════════════════════════════════════
# פונקציות שליפת דאטה ספציפיות
# ═══════════════════════════════════════════
async def fetch_predictions():
    # שימוש בפרמטר המיון המדויק מהמפרט: sort_by
    return await make_base44_request("Prediction", {"sort_by": "-created_date", "limit": 20})

async def fetch_draws():
    return await make_base44_request("Draw", {"sort_by": "-draw_number", "limit": 10})

async def fetch_prediction_results():
    return await make_base44_request("PredictionResult", {"sort_by": "-draw_number", "limit": 10})

# ═══════════════════════════════════════════
# בניית תוכן ההודעות (מעצבי ההודעות)
# ═══════════════════════════════════════════
def build_free_recommendation(records):
    if not records: return "❌ אין נתוני חיזוי מעודכנים במערכת כרגע. נסה שוב מאוחר יותר."
    # סינון מודל Human מתוך הרשימה
    human_pred = next((p for p in records if isinstance(p, dict) and p.get("method") == "Human"), None)
    if not human_pred: human_pred = records[0] # גיבוי אם אין Human
        
    return (f"⭐ <b>המלצה חינם — Quantum Human v5.0</b>\n"
            f"🎯 הגרלה מטרה: <b>#{human_pred.get('target_draw_number', '—')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"♠️ עלה (Spade):  <b>{human_pred.get('main_spade', '—')}</b>\n"
            f"❤️ לב (Heart):  <b>{human_pred.get('main_heart', '—')}</b>\n"
            f"♦️ יהלום (Diamond): <b>{human_pred.get('main_diamond', '—')}</b>\n"
            f"♣️ תלתן (Club):  <b>{human_pred.get('main_club', '—')}</b>\n\n"
            f"✨ <i>החיזוקים המלאים, ניתוחי העומק וכל 4 שיטות החיזוי זמינים באזור ה-VIP!</i>\n"
            f"<i>⬡ Chance AI Predictor</i>")

def build_last_draws(draws):
    if not draws: return "❌ לא נמצאו תוצאות הגרלה קודמות בארכיון השרת."
    msg = "🎰 <b>תוצאות 10 הגרלות אחרונות</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for d in draws:
        if isinstance(d, dict):
            msg += f"<b>🎰 הגרלה #{d.get('draw_number','—')}</b>: ♠️{d.get('spade','—')} ❤️{d.get('heart','—')} ♦️{d.get('diamond','—')} ♣️{d.get('club','—')}\n"
    msg += "\n<i>⬡ Chance AI Predictor</i>"
    return msg

def build_vip_hits(results):
    if not results: return "❌ אין נתוני תוצאות חיזויים זמינים כרגע."
    msg = "🎯 <b>איזור VIP — חיזוי מול תוצאה בזמן אמת</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for r in results:
        if isinstance(r, dict):
            hit_count = r.get('hit_count', 0)
            stars = "⭐" * hit_count if hit_count > 0 else "❌"
            msg += (f"<b>הגרלה #{r.get('draw_number')}</b> [שיטה: {r.get('method')}]\n"
                    f" פגיעות: <b>{hit_count}/4</b> {stars}\n"
                    f"• עלה: {'✅' if r.get('hit_spade') else '❌'} | לב: {'✅' if r.get('hit_heart') else '❌'} | יהלום: {'✅' if r.get('hit_diamond') else '❌'} | תלתן: {'✅' if r.get('hit_club') else '❌'}\n"
                    f"────────────────────\n")
    return msg

def build_vip_stats(records):
    if not records: return "❌ אין נתוני עומק סטטיסטיים זמינים כרגע."
    latest = records[0]
    msg = (f"📊 <b>סטטיסטיקות וניתוחי עומק VIP</b>\n"
           f"🎯 הגרלה נוכחית בחישוב: <b>#{latest.get('target_draw_number')}</b>\n"
           f"━━━━━━━━━━━━━━━━━━━━\n\n"
           f"📈 <b>פרמטרי מערכת מורחבים:</b>\n"
           f"• גודל חלון הגרלות לחישוב: <code>{latest.get('window_size_used', '—')}</code>\n"
           f"• עלות טור משוערת: <code>{latest.get('cost_ils', '—')} ₪</code>\n"
           f"• כמות טורים מומלצת: <code>{latest.get('rows_count', '—')}</code>\n"
           f"• שלב המודל הנוכחי: <code>{latest.get('phase', '—')}</code>\n\n"
           f"🔍 <b>קלפי חיזוק ייחודיים להגרלה זו:</b>\n"
           f"🔹 חיזוק ראשון: <b>{latest.get('reinforcement_1', 'אין')}</b>\n"
           f"🔹 חיזוק שני: <b>{latest.get('reinforcement_2', 'אין')}</b>\n\n"
           f"💬 <b>הערת אנליסט ומערכת:</b>\n"
           f"<i>\"{latest.get('note', 'אין הערות מיוחדות להגרלה זו.')}\"</i>")
    return msg

# ═══════════════════════════════════════════
# תפריטים וכפתורי הבוט המלאים (לפי בקשתך)
# ═══════════════════════════════════════════
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ המלצה חינם", callback_data="btn_free"),
         InlineKeyboardButton("🎰 10 הגרלות אחרונות", callback_data="btn_draws")],
        [InlineKeyboardButton("🎯 חיזוי מול תוצאה (VIP)", callback_data="btn_hits"),
         InlineKeyboardButton("📊 סטטיסטיקה וניתוחים (VIP)", callback_data="btn_stats")],
        [InlineKeyboardButton("👑 רכישת מנוי VIP", callback_data="btn_sub"),
         InlineKeyboardButton("👥 חבר מביא חבר", callback_data="btn_ref")],
        [InlineKeyboardButton("❓ שאלות ותשובות", callback_data="btn_faq"),
         InlineKeyboardButton("📞 יצירת קשר", callback_data="btn_contact")]
    ])

def sub_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆓 ניסיון חינמי — 3 ימים", callback_data="plan_trial")],
        [InlineKeyboardButton("📅 מנוי חודשי — ₪300", callback_data="plan_monthly")],
        [InlineKeyboardButton("🏆 מנוי שנתי — ₪3,000", callback_data="plan_yearly")],
        [InlineKeyboardButton("🔙 חזרה לתפריט", callback_data="btn_menu")]
    ])

def pay_menu(plan_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 תשלום ב-Bit", callback_data=f"pay_bit_{plan_key}")],
        [InlineKeyboardButton("💳 תשלום ב-PayBox", callback_data=f"pay_paybox_{plan_key}")],
        [InlineKeyboardButton("🏦 העברה בנקאית", callback_data=f"pay_bank_{plan_key}")],
        [InlineKeyboardButton("🔙 חזרה", callback_data="btn_sub")]
    ])

def action_menu(refresh_action):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 רענן נתונים", callback_data=refresh_action),
         InlineKeyboardButton("🔙 תפריט ראשי", callback_data="btn_menu")]
    ])

# ── פונקציית בדיקת גישת VIP ──
async def check_vip_access(update, callback=False):
    uid = update.effective_user.id
    if is_blocked(uid) and not is_admin(uid): return False
    if is_subscribed(uid): return True

    msg = ("🔒 <b>אזור זה נעול - לחברי VIP בלבד!</b>\n\n"
           "הצטרף ל-VIP וקבל גישה מיידית ל:\n"
           "🎯 מערכת חיזוי מול תוצאה בזמן אמת\n"
           "📊 סטטיסטיקות עומק וקלפי חיזוק מורחבים\n"
           "🚀 שליחת עדכונים אוטומטיים לנייד\n\n"
           "בחר באפשרות 'רכישת מנוי VIP' בתפריט כדי להצטרף!")
    if callback: await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 רכישת מנוי VIP", callback_data="btn_sub")], [InlineKeyboardButton("🔙 תפריט", callback_data="btn_menu")]]))
    else: await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_menu())
    return False

# ═══════════════════════════════════════════
# פקודות ואירועים של הבוט
# ═══════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uname = update.effective_user.username or update.effective_user.first_name or "משתמש"
    if is_blocked(uid) and not is_admin(uid): return

    # מנגנון חבר מביא חבר
    if ctx.args and ctx.args[0].startswith("REF"):
        referrer_id = ctx.args[0][3:]
        if str(referrer_id) != str(uid):
            count = add_referral(referrer_id, uid)
            if count > 0 and count % 2 == 0:
                add_subscription(int(referrer_id), "", "monthly", 30)
                try: await ctx.bot.send_message(chat_id=int(referrer_id), text="🎉 <b>מזל טוב!</b>\nצירפת 2 חברים בהצלחה וקיבלת חודש מנוי VIP מתנה!", parse_mode="HTML")
                except: pass

    db = load_db()
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {"user_id": uid, "username": uname, "plan": None, "expiry": None, "joined": datetime.now().isoformat(), "trial_used": False, "referrals_count": 0, "referral_code": f"REF{uid}"}
        save_db(db)

    status = f"👑 VIP פעיל עד: {get_expiry_str(uid)}" if is_subscribed(uid) else "❌ אין מנוי VIP פעיל"
    await update.message.reply_text(f"⬡ <b>Chance AI Predictor</b>\n\nשלום {uname}!\nסטטוס: {status}\n\nבחר אפשרות מהתפריט הבא:", parse_mode="HTML", reply_markup=main_menu())

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id; data = query.data; chat_id = query.message.chat_id

    if is_blocked(uid) and not is_admin(uid): return

    if data == "btn_menu":
        status = f"👑 VIP פעיל עד: {get_expiry_str(uid)}" if is_subscribed(uid) else "❌ אין מנוי VIP פעיל"
        await query.edit_message_text(f"⬡ <b>Chance AI Predictor</b>\n\nסטטוס: {status}\n\nבחר אפשרות מהתפריט הבא:", parse_mode="HTML", reply_markup=main_menu())
        return

    # 1. המלצה חינם
    if data == "btn_free":
        await query.edit_message_text("🔄 <i>מושך המלצה חינם משרתי Chance AI...</i>", parse_mode="HTML")
        records = await fetch_predictions()
        text = build_free_recommendation(records)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=action_menu("btn_free"))
        return

    # 2. 10 הגרלות אחרונות
    if data == "btn_draws":
        await query.edit_message_text("🔄 <i>שולף תוצאות הגרלה אחרונות מהארכיון...</i>", parse_mode="HTML")
        draws = await fetch_draws()
        text = build_last_draws(draws)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=action_menu("btn_draws"))
        return

    # 3. חיזוי מול תוצאה (VIP)
    if data == "btn_hits":
        if not await check_vip_access(update, callback=True): return
        await query.edit_message_text("🔄 <i>מנתח נתוני פגיעות והצלחות מודל...</i>", parse_mode="HTML")
        results = await fetch_prediction_results()
        text = build_vip_hits(results)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=action_menu("btn_hits"))
        return

    # 4. סטטיסטיקה וניתוחים (VIP)
    if data == "btn_stats":
        if not await check_vip_access(update, callback=True): return
        await query.edit_message_text("🔄 <i>מפיק דוח דאטה וסטטיסטיקת עומק...</i>", parse_mode="HTML")
        records = await fetch_predictions()
        text = build_vip_stats(records)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=action_menu("btn_stats"))
        return

    # 5. רכישת מנוי VIP
    if data == "btn_sub":
        txt = f"✅ <b>המנוי שלך פעיל!</b>\nתוקף: {get_expiry_str(uid)}" if is_subscribed(uid) else "👑 <b>הצטרפות לתכנית ה-VIP של Chance AI</b>\n\nפתח גישה מלאה לכל הכלים המורחבים, החיזוקים ואחוזי ההצלחה בזמן אמת.\n\nבחר תכנית להצטרפות:"
        await query.edit_message_text(txt, parse_mode="HTML", reply_markup=sub_menu())
        return

    if data.startswith("plan_"):
        plan_key = data.replace("plan_", ""); plan = PRICES[plan_key]
        if plan_key == "trial":
            user = get_user(uid)
            if user and user.get("trial_used"):
                await query.edit_message_text("❌ כבר ניצלת את תקופת הניסיון החינמית בעבר.", parse_mode="HTML", reply_markup=sub_menu())
                return
            add_subscription(uid, query.from_user.username, "trial", 3)
            await query.edit_message_text("🎉 <b>מנוי הניסיון שלך ל-3 ימים הופעל בהצלחה!</b>\nכל אפשרויות ה-VIP פתוחות בפניך כעת.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 לתפריט הראשי", callback_data="btn_menu")]]))
            return
        await query.edit_message_text(f"💳 <b>תכנית: {plan['name']} — עלות: ₪{plan['price']}</b>\n\nבחר את אמצעי התשלום הנוח לך לקבלת הנחיות:", parse_mode="HTML", reply_markup=pay_menu(plan_key))
        return

    if data.startswith("pay_"):
        parts = data.split("_"); method = parts[1]; plan_key = parts[2]; plan = PRICES[plan_key]
        db = load_db(); db["pending"][str(uid)] = {"user_id": uid, "username": query.from_user.username, "plan": plan_key, "method": method}
        save_db(db)
        
        details = {"bit": f"📱 <b>Bit</b>\nהעבר ₪{plan['price']} ל-<b>{PAYMENT_INFO['bit']}</b>", "paybox": f"📱 <b>PayBox</b>\nהעבר ₪{plan['price']} ל-<b>{PAYMENT_INFO['paybox']}</b>", "bank": f"🏦 <b>העברה בנקאית</b>\n{PAYMENT_INFO['bank']}\nסכום מדויק: ₪{plan['price']}"}
        await query.edit_message_text(f"{details[method]}\n\n⚠️ <b>שלב סופי לאישור:</b>\nלאחר ביצוע ההעברה, שלח צילום מסך (Screenshot) של האישור ישירות לצ'אט הזה כדי שהמנהל יפתח לך את המנוי באופן מיידי.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ביטול וחזרה", callback_data="btn_sub")]]))
        return

    # 6. חבר מביא חבר
    if data == "btn_ref":
        db = load_db(); count = len(db.get("referrals", {}).get(str(uid), []))
        link = f"https://t.me/{ctx.bot.username}?start=REF{uid}"
        await query.edit_message_text(f"👥 <b>תכנית חבר מביא חבר — Chance AI</b>\n\nשתף את הקישור הייחודי שלך עם חברים. על כל 2 חברים שיפעלו את הבוט, תקבל <b>חודש VIP מלא מתנה!</b>\n\n🔗 הקישור שלך:\n<code>{link}</code>\n\n📊 חברים שהצטרפו דרכך: <b>{count}</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 תפריט ראשי", callback_data="btn_menu")]]))
        return

    # 7. שאלות ותשובות (FAQ)
    if data == "btn_faq":
        faq_text = ("❓ <b>שאלות ותשובות נפוצות — Chance AI</b>\n\n"
                    "💡 <b>מה הבוט יודע לעשות?</b>\n"
                    "הבוט מחובר ישירות למערכת בינה מלאכותית שמנתחת את הגרלות הצ'אנס, מפיקה 4 מודלי חיזוי שונים, מחשבת קלפי חיזוק ומציגה אחוזי הצלחה בזמן אמת.\n\n"
                    "🥇 <b>מה המודל הכי מדויק?</b>\n"
                    "מודל ה-Quantum Human v5.0 הוא המודל המוביל שמציג את אחוזי הפגיעה הגבוהים ביותר ביחס לשאר השיטות.\n\n"
                    "⏱ <b>כל כמה זמן הנתונים מתעדכנים?</b>\n"
                    "הנתונים נמשכים אוטומטית וישירות משרתי Base44 מיד בסיום כל הגרלה רשמית.")
        await query.edit_message_text(faq_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 תפריט ראשי", callback_data="btn_menu")]]))
        return

    # 8. יצירת קשר
    if data == "btn_contact":
        contact_text = ("📞 <b>יצירת קשר ותמיכה טכנית</b>\n\n"
                        "נתקלת בבעיה? מעוניין לשאול שאלה או להפעיל מנוי בצורה ידנית?\n\n"
                        "📬 פנה למנהל המערכת ישירות בטלגרם:\n"
                        f"👉 @הכנס_שם_משתמש_שלך\n\n"
                        "<i>זמינים עבורכם לכל שאלה!</i>")
        await query.edit_message_text(contact_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 תפריט ראשי", callback_data="btn_menu")]]))
        return

async def handle_message_and_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; uname = update.effective_user.username or update.effective_user.first_name or "משתמש"
    if is_blocked(uid) and not is_admin(uid): return

    db = load_db(); pend = db.get("pending", {}).get(str(uid))

    # קבלת צילום מסך של אישור תשלום והעברה לאדמין
    if update.message.photo and pend:
        await ctx.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=f"📸 <b>אישור תשלום חדש ממתין לאישורך!</b>\n\n👤 משתמש: @{uname} (ID: {uid})\n📋 תכנית מבוקשת: {pend['plan']}\n💳 אמצעי: {pend['method']}\n\n✅ לאישור ידני והפעלת המנוי השתמש במערכת הניהול.")
        await update.message.reply_text("✅ <b>צילום המסך התקבל ונשלח לבדיקת מנהל!</b>\nהמנוי שלך יופעל באופן אוטומטי מיד עם אישור ההעברה (עד מספר דקות).", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 תפריט ראשי", callback_data="btn_menu")]]))
    else:
        await update.message.reply_text("שלח /start לפתיחת תפריט האפשרויות והחיזויים של Chance AI ⬡")

# ═══════════════════════════════════════════
# ניטור אוטומטי מבוסס מפרט ה-API
# ═══════════════════════════════════════════
async def auto_scan_loop(app):
    await asyncio.sleep(10)
    last_notified_draw = 0
    
    while True:
        try:
            records = await fetch_predictions()
            if records and isinstance(records, list) and len(records) > 0:
                latest_draw = records[0].get("target_draw_number")
                if latest_draw:
                    if last_notified_draw == 0:
                        last_notified_draw = latest_draw
                    elif latest_draw > last_notified_draw:
                        last_notified_draw = latest_draw
                        
                        # שליחת התראה אוטומטית לקבוצה הציבורית שלכם מיד כשיש הגרלה חדשה!
                        alert_text = (f"🔮 <b>חיזוי מורחב חדש עלה למערכת!</b>\n"
                                      f"🎯 הגרלה מספר: <b>#{latest_draw}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
                                      f"כל 4 שיטות החיזוי, קלפי החיזוק וסטטיסטיקות ההצלחה המלאות זמינים כעת בבוט!\n\n"
                                      f"🚀 היכנסו לבוט והתעדכנו בזמן אמת.")
                        try:
                            await app.bot.send_message(chat_id=CHAT_ID, text=alert_text, parse_mode="HTML")
                        except Exception as tg_err:
                            print(f"❌ שגיאה בשליחה האוטומטית לקבוצה: {tg_err}")
        except Exception as e:
            print(f"❌ שגיאה בלופ הניטור האוטומטי: {e}")
        await asyncio.sleep(60) # סריקה רציפה בכל 60 שניות כדי לתפוס את העדכון מייד

# ═══════════════════════════════════════════
# הפעלת המערכת
# ═══════════════════════════════════════════
def main():
    print("🚀 מפעיל את Chance AI Bot המותאם למפרט Base44...")
    app = Application.builder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message_and_photos))

    async def post_init(application):
        asyncio.create_task(auto_scan_loop(application))
        print("✅ הבוט מחובר, מנטר את ה-API ומוכן לעבודה!")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
