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
# הגדרות מאובטחות וחיבור ל-Chance AI
# ═══════════════════════════════════════════
TG_TOKEN  = os.environ.get("TG_TOKEN",  "7754804245:AAEf5lCTTU3NB7qNnOa1-HKJXcpZLDOdseM")
CHAT_ID   = os.environ.get("CHAT_ID",   "-1002360888694") # מזהה הקבוצה שלך מהצילום מסך
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "6775881845"))

# פרטי ה-API של אפליקציית Chance AI מתוך צילום המסך שלך:
CHANCE_APP_ID  = "699f6d52f3302128ab050b10"
CHANCE_API_KEY = "20742ca24625436b8963159c29dd34c3"
BASE_URL       = "https://api.base44.com/v1" # כתובת ה-API הסטנדרטית של פלטפורמת Base44

# ── פרטי תשלום ──
PAYMENT_INFO = {
    "bit":    "שלח לביט למספר: *יתקבל לאחר פנייה*",
    "paybox": "שלח לפייבוקס למספר: *יתקבל לאחר פנייה*",
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
# מסד נתונים מאובטח
# ═══════════════════════════════════════════
DB_FILE      = "users.json"
BLOCKED_FILE = "blocked.json"
LOG_FILE     = "security.log"

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

def security_log(event, user_id, detail=""):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f: f.write(f"[{t}] {event} | UID:{user_id} | {detail}\n")

def is_blocked(user_id):
    bl = load_blocked()
    return str(user_id) in bl["blocked"]

def record_attempt(user_id):
    bl  = load_blocked()
    uid = str(user_id)
    bl["attempts"][uid] = bl["attempts"].get(uid, 0) + 1
    if bl["attempts"][uid] >= 5:
        if uid not in bl["blocked"]:
            bl["blocked"].append(uid)
            security_log("AUTO_BLOCK", user_id, f"יותר מ-5 ניסיונות")
    save_blocked(bl)
    return bl["attempts"][uid]

def is_admin(user_id): return int(user_id) == ADMIN_ID
def get_user(user_id): return load_db()["users"].get(str(user_id))

def is_subscribed(user_id):
    if is_admin(user_id): return True
    user = get_user(user_id)
    if not user or not user.get("expiry"): return False
    return datetime.fromisoformat(user["expiry"]) > datetime.now()

def is_trial_used(user_id):
    user = get_user(user_id)
    return user.get("trial_used", False) if user else False

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
        "user_id":        user_id,
        "username":       username,
        "plan":           plan_key,
        "expiry":         exp.isoformat(),
        "joined":         usr.get("joined", now.isoformat()),
        "trial_used":     True if plan_key == "trial" else usr.get("trial_used", False),
        "referrals_count": usr.get("referrals_count", 0),
        "referral_code":  f"REF{user_id}",
        "approved_by":    "admin",
        "approved_at":    now.isoformat(),
    }
    save_db(db)
    security_log("SUBSCRIPTION", user_id, f"plan={plan_key} days={days} exp={exp.strftime('%d/%m/%Y')}")

def add_pending(user_id, username, plan_key, method):
    db = load_db()
    db["pending"][str(user_id)] = {
        "user_id":  user_id,
        "username": username,
        "plan":     plan_key,
        "method":   method,
        "time":     datetime.now().isoformat(),
        "token":    secrets.token_hex(8),
    }
    save_db(db)

def remove_pending(user_id):
    db = load_db()
    db["pending"].pop(str(user_id), None)
    save_db(db)

def add_referral(referrer_id, new_user_id):
    db  = load_db()
    rid = str(referrer_id)
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
# פונקציות משיכת נתונים ישירות מ-Chance AI
# ═══════════════════════════════════════════
async def fetch_predictions():
    """מושך את כל החיזויים האחרונים מטבלת Prediction באפליקציה שלך"""
    headers = {"Authorization": f"Bearer {CHANCE_API_KEY}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/apps/{CHANCE_APP_ID}/entities/Prediction/records"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={"sort": "-target_draw_number", "limit": 20}) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("records", [])
    except Exception as e:
        print(f"❌ שגיאה במשיכת חיזויים: {e}")
    return []

async def fetch_draws():
    """מושך את תוצאות ההגרלות האחרונות מטבלת Draw באפליקציה שלך"""
    headers = {"Authorization": f"Bearer {CHANCE_API_KEY}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/apps/{CHANCE_APP_ID}/entities/Draw/records"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={"sort": "-draw_number", "limit": 10}) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("records", [])
    except Exception as e:
        print(f"❌ שגיאה במשיכת הגרלות: {e}")
    return []

# ── עיצוב הודעות לבוט החדש ──
def build_free_recommendation(predictions):
    if not predictions: return "❌ אין חיזויים מעודכנים במערכת כרגע."
    
    # סינון מודל Human (Quantum Human v5.0)
    human_pred = [p for p in predictions if p.get("method") in ("Human", "Quantum Human v5.0")]
    if not human_pred: return "❌ לא נמצא חיזוי מעודכן לשיטת Quantum Human."
    
    p = human_pred[0]
    return (f"⭐ <b>המלצה חינם — Quantum Human v5.0</b>\n"
            f"🎯 הגרלה מטרה: <b>#{p.get('target_draw_number', '—')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"♠️ עלה (Spade):  <b>{p.get('main_spade', '—')}</b>\n"
            f"❤️ לב (Heart):  <b>{p.get('main_heart', '—')}</b>\n"
            f"♦️ יהלום (Diamond): <b>{p.get('main_diamond', '—')}</b>\n"
            f"♣️ תלתן (Club):  <b>{p.get('main_club', '—')}</b>\n\n"
            f"✨ <i>החיזוקים והשיטות המלאות זמינים במנוי ה-VIP!</i>\n"
            f"<i>⬡ Chance AI Predictor</i>")

def build_vip_predictions(predictions):
    if not predictions: return "❌ אין נתונים זמינים."
    
    # מוצאים את מספר ההגרלה העדכני ביותר בטבלה
    latest_draw = predictions[0].get("target_draw_number")
    current_preds = [p for p in predictions if p.get("target_draw_number") == latest_draw]
    
    msg = f"🔮 <b>ריכוז חיזויים מורחב להגרלה #{latest_draw}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # מיפוי השמות של 4 השיטות שלך
    methods_map = {
        "Human": "🥇 Quantum Human v5.0 (הכי מדויק)",
        "Baseline": "🥈 Baseline v5.1",
        "Hybrid": "🥉 Hybrid v6",
        "MirrorReverse": "🔄 Mirror Reverse Theory"
    }
    
    for m_key, m_name in methods_map.items():
        match = [p for p in current_preds if p.get("method") == m_key]
        if match:
            p = match[0]
            msg += (f"<b>{m_name}:</b>\n"
                    f"• ראשי: ♠️{p.get('main_spade','')} ❤️{p.get('main_heart','')} ♦️{p.get('main_diamond','')} ♣️{p.get('main_club','')}\n"
                    f"• חיזוקים: {p.get('strong_cards', 'אין')}\n\n")
            
    msg += "⚠️ <i>השתמש במידע באחריותך בלבד. בהצלחה!</i>\n<i>⬡ Chance AI VIP</i>"
    return msg

def build_last_draws(draws):
    if not draws: return "❌ לא נמצאו הגרלות קודמות."
    msg = "🎰 <b>תוצאות 10 הגרלות אחרונות</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for d in draws:
        msg += f"<b>הגרלה #{d.get('draw_number')}</b>: ♠️{d.get('spade')} ❤️{d.get('heart')} ♦️{d.get('diamond')} ♣️{d.get('club')}\n"
    msg += "\n<i>⬡ Chance AI Predictor</i>"
    return msg

# ═══════════════════════════════════════════
# תפריטים (מעודכנים עבור אפליקציית הצ'אנס)
# ═══════════════════════════════════════════
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ המלצה חינם",        callback_data="free_recommendation"),
         InlineKeyboardButton("🔮 חיזוי VIP (כל 4 השיטות)", callback_data="vip_signals")],
        [InlineKeyboardButton("🎰 10 הגרלות אחרונות",   callback_data="last_draws")],
        [InlineKeyboardButton("👑 רכישת מנוי VIP",      callback_data="subscribe"),
         InlineKeyboardButton("👥 חבר מביא חבר",       callback_data="referral")],
        [InlineKeyboardButton("ℹ️ עזרה",                callback_data="help")],
    ])

def sub_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆓 ניסיון חינמי — 3 ימים",  callback_data="plan_trial")],
        [InlineKeyboardButton("📅 מנוי חודשי — ₪300",       callback_data="plan_monthly")],
        [InlineKeyboardButton("🏆 מנוי שנתי — ₪3,000",      callback_data="plan_yearly")],
        [InlineKeyboardButton("🔙 חזרה",                     callback_data="menu")],
    ])

def pay_menu(plan_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 ביט",           callback_data=f"pay_bit_{plan_key}")],
        [InlineKeyboardButton("💳 פייבוקס",       callback_data=f"pay_paybox_{plan_key}")],
        [InlineKeyboardButton("🏦 העברה בנקאית", callback_data=f"pay_bank_{plan_key}")],
        [InlineKeyboardButton("🔙 חזרה",          callback_data="subscribe")],
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 תפריט ראשי", callback_data="menu")]])

def no_sub_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 הצטרף ל-VIP עכשיו", callback_data="subscribe")],
        [InlineKeyboardButton("🔙 תפריט",       callback_data="menu")],
    ])

def action_menu(action):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 רענן",        callback_data=action),
         InlineKeyboardButton("🔙 תפריט",       callback_data="menu")]
    ])

# ── בדיקת גישה לתוכן VIP ──
async def check_access(update, ctx, callback=False):
    uid = update.effective_user.id
    if is_blocked(uid) and not is_admin(uid):
        security_log("BLOCKED_ATTEMPT", uid)
        msg = "🚫 הגישה שלך נחסמה. פנה לתמיכה."
        if callback: await update.callback_query.answer(msg, show_alert=True)
        else: await update.message.reply_text(msg)
        return False

    if is_subscribed(uid): return True

    security_log("NO_SUB_ATTEMPT", uid)
    msg = ("🔒 <b>תוכן זה זמין למנויי VIP בלבד</b>\n\n"
           "פתח גישה לכל 4 שיטות החיזוי והחיזוקים בזמן אמת:\n"
           "🆓 ניסיון חינמי 3 ימים\n"
           "📅 מנוי חודשי ₪300\n"
           "🏆 מנוי שנתי ₪3,000\n\n"
           "לחץ להצטרפות ↓")
    if callback: await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=no_sub_menu())
    else: await update.message.reply_text(msg, parse_mode="HTML", reply_markup=no_sub_menu())
    return False

# ═══════════════════════════════════════════
# פקודות
# ═══════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    uname = update.effective_user.username or update.effective_user.first_name or "משתמש"

    if is_blocked(uid) and not is_admin(uid):
        await update.message.reply_text("🚫 הגישה שלך נחסמה. פנה לתמיכה.")
        return

    # הפניות חברים
    args = ctx.args
    if args and args[0].startswith("REF"):
        referrer_id = args[0][3:]
        if str(referrer_id) != str(uid):
            count = add_referral(referrer_id, uid)
            if count > 0 and count % 2 == 0:
                add_subscription(int(referrer_id), "", "monthly", 30)
                try:
                    await ctx.bot.send_message(
                        chat_id=int(referrer_id),
                        text=("🎉 <b>מזל טוב!</b>\n\nצירפת 2 חברים — קיבלת <b>חודש VIP חינמי!</b>\n\n"
                              f"תוקף חדש: {get_expiry_str(referrer_id)}\n\n<i>⬡ Chance AI</i>"),
                        parse_mode="HTML"
                    )
                except: pass

    db = load_db()
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {
            "user_id": uid, "username": uname, "plan": None, "expiry": None,
            "joined": datetime.now().isoformat(), "trial_used": False, "referrals_count": 0, "referral_code": f"REF{uid}",
        }
        save_db(db)
        security_log("NEW_USER", uid, f"username={uname}")

    sub    = is_subscribed(uid)
    status = f"👑 מנוי VIP פעיל עד: {get_expiry_str(uid)}" if sub else "❌ אין מנוי VIP פעיל"

    await update.message.reply_text(
        f"⬡ <b>Chance AI Predictor</b>\n\nברוך הבא! 👋\n{status}\n\nבחר פעולה מהתפריט:",
        parse_mode="HTML", reply_markup=main_menu()
    )

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        record_attempt(update.effective_user.id)
        return
    db     = load_db()
    users  = db["users"]
    pend   = db
