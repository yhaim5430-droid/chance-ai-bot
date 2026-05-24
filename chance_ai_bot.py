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
CHAT_ID   = os.environ.get("CHAT_ID",   "-1002360888694") # מזהה קבוצת הטלגרם שלך מהצילום מסך
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "6775881845"))

# פרטי ה-API של אפליקציית Chance AI שלך:
CHANCE_APP_ID  = "699f6d52f3302128ab050b10"
CHANCE_API_KEY = "20742ca24625436b8963159c29dd34c3"
BASE_URL       = "https://api.base44.com/v1" # כתובת ה-API הרשמית של Base44

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
# פונקציות משיכת נתונים ישירות מ-Chance AI API
# ═══════════════════════════════════════════
async def fetch_predictions_from_api():
    """פנייה ישירה לטבלת Prediction באפליקציית Chance AI שלך"""
    headers = {"Authorization": f"Bearer {CHANCE_API_KEY}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/apps/{CHANCE_APP_ID}/entities/Prediction/records"
    params = {"sort": "-target_draw_number", "limit": 20}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as r:
                if r.status == 200:
                    res = await r.json()
                    return res.get("records", [])
    except Exception as e:
        print(f"❌ שגיאה במשיכת חיזויים: {e}")
    return []

async def fetch_draws_from_api():
    """פנייה ישירה לטבלת Draw באפליקציית Chance AI שלך - תיקון הבעיה של 10 הגרלות"""
    headers = {"Authorization": f"Bearer {CHANCE_API_KEY}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/apps/{CHANCE_APP_ID}/entities/Draw/records"
    params = {"sort": "-draw_number", "limit": 10} # מביא במדויק את ה-10 האחרונות
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as r:
                if r.status == 200:
                    res = await r.json()
                    return res.get("records", [])
    except Exception as e:
        print(f"❌ שגיאה במשיכת 10 הגרלות: {e}")
    return []

# ── עיצוב הודעות מבוסס נתוני אמת ──
def build_free_recommendation(records):
    if not records: return "❌ אין נתוני חיזוי מעודכנים במערכת כרגע. נסה שוב מאוחר יותר."
    
    # סינון לטובת המודל האנושי (Quantum Human v5.0) המועדף
    human_pred = next((p for p in records if p.get("method") in ("Human", "Quantum Human", "Quantum Human v5.0")), None)
    
    if not human_pred:
        # גיבוי: אם מסיבה כלשהי לא הוגדר 'Human', ניקח את הרשומה הראשונה
        human_pred = records[0]
        
    return (f"⭐ <b>המלצה חינם — Quantum Human v5.0</b>\n"
            f"🎯 הגרלה מטרה: <b>#{human_pred.get('target_draw_number', '—')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"♠️ עלה (Spade):  <b>{human_pred.get('main_spade', '—')}</b>\n"
            f"❤️ לב (Heart):  <b>{human_pred.get('main_heart', '—')}</b>\n"
            f"♦️ יהלום (Diamond): <b>{human_pred.get('main_diamond', '—')}</b>\n"
            f"♣️ תלתן (Club):  <b>{human_pred.get('main_club', '—')}</b>\n\n"
            f"✨ <i>החיזוקים וכל 4 שיטות החיזוי המלאות זמינים לחברי ה-VIP!</i>\n"
            f"<i>⬡ Chance AI Predictor</i>")

def build_vip_signals(records):
    if not records: return "❌ אין נתונים זמינים כרגע."
    
    latest_draw = records[0].get("target_draw_number")
    current_preds = [p for p in records if p.get("target_draw_number") == latest_draw]
    
    msg = f"🔮 <b>ריכוז חיזויים מורחב להגרלה #{latest_draw}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    methods_map = {
        "Human": "🥇 Quantum Human v5.0 (הכי מדויק)",
        "Baseline": "🥈 Baseline v5.1",
        "Hybrid": "🥉 Hybrid v6",
        "MirrorReverse": "🔄 Mirror Reverse Theory"
    }
    
    for m_key, m_name in methods_map.items():
        p = next((pred for pred in current_preds if pred.get("method") == m_key), None)
        if p:
            msg += (f"<b>{m_name}:</b>\n"
                    f"• ראשי: ♠️{p.get('main_spade','')} ❤️{p.get('main_heart','')} ♦️{p.get('main_diamond','')} ♣️{p.get('main_club','')}\n"
                    f"• חיזוקים: <b>{p.get('strong_cards', 'אין')}</b>\n\n")
            
    msg += "⚠️ <i>השתמש במידע באחריותך בלבד. בהצלחה!</i>\n<i>⬡ Chance AI VIP</i>"
    return msg

def build_last_draws(draws):
    if not draws: return "❌ לא נמצאו תוצאות הגרלה קודמות בבסיס הנתונים."
    
    msg = "🎰 <b>תוצאות 10 הגרלות אחרונות</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for d in draws:
        msg += f"<b>🎰 הגרלה #{d.get('draw_number')}</b>: ♠️{d.get('spade','')} ❤️{d.get('heart','')} ♦️{d.get('diamond','')} ♣️{d.get('club','')}\n"
        
    msg += "\n<i>⬡ Chance AI Predictor</i>"
    return msg

# ═══════════════════════════════════════════
# תפריטים
# ═══════════════════════════════════════════
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ המלצה חינם",        callback_data="watchlist"), # משתמש בפונקציה החינמית
         InlineKeyboardButton("🔮 חיזוי VIP (כל 4 השיטות)", callback_data="signals")],
        [InlineKeyboardButton("🎰 10 הגרלות אחרונות",   callback_data="briefing")], # משותף ל-10 הגרלות
        [InlineKeyboardButton("👑 מנויים",              callback_data="subscribe"),
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
        [InlineKeyboardButton("👑 הצטרף עכשיו", callback_data="subscribe")],
        [InlineKeyboardButton("🔙 תפריט",       callback_data="menu")],
    ])

def action_menu(action):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 רענן",        callback_data=action),
         InlineKeyboardButton("🔙 תפריט",       callback_data="menu")]
    ])

# ── בדיקת גישה ──
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
# פקודות בוט
# ═══════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    uname = update.effective_user.username or update.effective_user.first_name or "משתמש"

    if is_blocked(uid) and not is_admin(uid):
        await update.message.reply_text("🚫 הגישה שלך נחסמה. פנה לתמיכה.")
        return

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
    pend   = db["pending"]
    active = [u for u in users.values() if u.get("expiry") and datetime.fromisoformat(u["expiry"]) > datetime.now()]

    msg = f"👑 <b>לוח בקרה — מנהל</b>\n\n👥 סה\"כ משתמשים: {len(users)}\n✅ מנויים פעילים: {len(active)}\n⏳ ממתינים לאישור: {len(pend)}\n\n"
    if pend:
        msg += "⏳ <b>ממתינים לאישור:</b>\n\n"
        for uid, p in pend.items():
            plan = PRICES.get(p["plan"], {})
            msg += f"👤 @{p.get('username','?')} (ID: {uid})\n📋 {plan.get('name','?')} — ₪{plan.get('price',0)}\n💳 {p.get('method','?')} · ✅ /approve_{uid} · ❌ /reject_{uid}\n\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def cmd_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = update.message.text.replace("/approve_", "").strip()
    db = load_db(); pend = db["pending"].get(uid)
    if not pend: return
    plan = PRICES[pend["plan"]]
    add_subscription(int(uid), pend.get("username",""), pend["plan"], plan["days"])
    remove_pending(uid)
    await update.message.reply_text(f"✅ אושר! @{pend.get('username','?')} — {plan['name']}")
    try:
        await ctx.bot.send_message(chat_id=int(uid), text=f"✅ <b>המנוי שלך אושר!</b>\n\nתוכנית: <b>{plan['name']}</b>\nתוקף: <b>{get_expiry_str(uid)}</b>\n\nשלח /start להתחלה 🚀", parse_mode="HTML", reply_markup=back_menu())
    except: pass

async def cmd_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = update.message.text.replace("/reject_", "").strip()
    db = load_db(); pend = db["pending"].get(uid)
    if not pend: return
    remove_pending(uid)
    await update.message.reply_text(f"❌ נדחה — @{pend.get('username','?')}")
    try:
        await ctx.bot.send_message(chat_id=int(uid), text="❌ <b>התשלום לא אושר.</b>\nאנא שלח צילום מסך ברור של אישור התשלום המלא.", parse_mode="HTML", reply_markup=back_menu())
    except: pass

async def cmd_block(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = update.message.text.replace("/block_", "").strip()
    bl = load_blocked()
    if uid not in bl["blocked"]:
        bl["blocked"].append(uid); save_blocked(bl)
        await update.message.reply_text(f"🚫 משתמש {uid} נחסם.")

async def cmd_unblock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = update.message.text.replace("/unblock_", "").strip()
    bl = load_blocked()
    if uid in bl["blocked"]:
        bl["blocked"].remove(uid); save_blocked(bl)
        await update.message.reply_text(f"✅ משתמש {uid} שוחרר מחסימה.")

# ═══════════════════════════════════════════
# טיפול בלחיצות כפתורים
# ═══════════════════════════════════════════
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id; uname = query.from_user.username or query.from_user.first_name or "משתמש"
    chat_id = query.message.chat_id; data = query.data

    if is_blocked(uid) and not is_admin(uid): return

    if data == "menu":
        sub = is_subscribed(uid); status = f"👑 מנוי VIP פעיל עד: {get_expiry_str(uid)}" if sub else "❌ אין מנוי VIP פעיל"
        await query.edit_message_text(f"⬡ <b>Chance AI Predictor</b>\n\n{status}\n\nבחר פעולה מהתפריט:", parse_mode="HTML", reply_markup=main_menu())
        return

    if data == "help":
        await query.edit_message_text("⬡ <b>פקודות זמינות:</b>\n\n/start — תפריט ראשי\n\n⭐ <b>המלצה חינם:</b> מציג את שיטת Quantum Human המדויקת ביותר.\n🔮 <b>חיזוי VIP:</b> מציג את כל 4 המודלים כולל קלפי חיזוק מורחבים.", parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "subscribe":
        txt = f"✅ <b>יש לך מנוי VIP פעיל!</b>\n\nתוקף: {get_expiry_str(uid)}" if is_subscribed(uid) else "👑 <b>Chance AI — הצטרפות ל-VIP</b>\n\n🆓 <b>ניסיון חינמי</b> — 3 ימים\n📅 <b>מנוי חודשי</b> — ₪300\n🏆 <b>מנוי שנתי</b> — ₪3,000\n\nבחר תוכנית מנוי:"
        await query.edit_message_text(txt, parse_mode="HTML", reply_markup=sub_menu())
        return

    if data.startswith("plan_"):
        plan_key = data.replace("plan_", ""); plan = PRICES.get(plan_key)
        if plan_key == "trial":
            if is_trial_used(uid):
                await query.edit_message_text("❌ <b>כבר השתמשת בניסיון החינמי בעבר.</b>\nאנא בחר מנוי בתשלום:", parse_mode="HTML", reply_markup=sub_menu())
                return
            add_subscription(uid, uname, "trial", 3)
            await query.edit_message_text("🎉 <b>הניסיון החינמי ל-3 ימים הופעל בהצלחה!</b>\nתהנה מחיזויי Chance AI!", parse_mode="HTML", reply_markup=back_menu())
            return
        await query.edit_message_text(f"💳 <b>{plan['name']} — ₪{plan['price']}</b>\n\nבחר אמצעי תשלום להוראות המעבר:", parse_mode="HTML", reply_markup=pay_menu(plan_key))
        return

    if data.startswith("pay_"):
        parts = data.split("_"); method = parts[1]; plan_key = parts[2]; plan = PRICES[plan_key]
        add_pending(uid, uname, plan_key, method)
        details = {"bit": f"💳 <b>ביט</b>\nהעבר ₪{plan['price']} ל-<b>{PAYMENT_INFO['bit']}</b>", "paybox": f"💳 <b>פייבוקס</b>\nהעבר ₪{plan['price']} ל-<b>{PAYMENT_INFO['paybox']}</b>", "bank": f"🏦 <b>העברה בנקאית</b>\n{PAYMENT_INFO['bank']}\nסכום: ₪{plan['price']}"}
        await query.edit_message_text(f"📋 <b>הוראות תשלום:</b>\n\n{details[method]}\n\n⚠️ <b>חשוב מאוד:</b> לאחר ביצוע ההעברה, צלם מסך ושלח את התמונה ישירות לצ'אט הזה כדי שהמנהל יאשר אותך.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📸 שלחתי אישור תשלום", callback_data=f"sent_{plan_key}")]]))
        return

    if data.startswith("sent_"):
        await query.edit_message_text("⏳ <b>הבקשה נקלטה!</b>\nהמנהל יבדוק את צילום המסך ששלחת ויאשר את המנוי בהקדם (עד 24 שעות).", parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "referral":
        db = load_db(); count = len(db["referrals"].get(str(uid), []))
        link = f"https://t.me/{ctx.bot.username}?start=REF{uid}"
        await query.edit_message_text(f"👥 <b>חבר מביא חבר</b>\n\nהקישור הייחודי שלך:\n<code>{link}</code>\n\n📊 חברים שהצטרפו דרכך: <b>{count}</b>\n🎁 כל 2 חברים מעניקים לך חודש VIP חינם!", parse_mode="HTML", reply_markup=back_menu())
        return

    # ── טיפול בפעולות דאטה מול Chance AI API ──
    
    # 1. המלצה חינם (נגיש לכולם ללא הגבלת מנוי)
    if data == "watchlist":
        await query.edit_message_text("🔄 <i>מושך המלצה חינם מ-Chance AI...</i>", parse_mode="HTML")
        predictions = await fetch_predictions_from_api()
        text = build_free_recommendation(predictions)
        await ctx.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, parse_mode="HTML", reply_markup=action_menu("watchlist"))
        return

    # 2. 10 הגרלות אחרונות (נגיש לכולם ללא הגבלת מנוי)
    if data == "briefing":
        await query.edit_message_text("🔄 <i>מושך תוצאות מהארכיון...</i>", parse_mode="HTML")
        draws = await fetch_draws_from_api()
        text = build_last_draws(draws)
        await ctx.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, parse_mode="HTML", reply_markup=action_menu("briefing"))
        return

    # 3. חיזוי VIP (דורש מנוי)
    if data == "signals":
        if not await check_access(update, ctx, callback=True): return
        await query.edit_message_text("🔄 <i>מחשב את כל 4 המודלים והחיזוקים...</i>", parse_mode="HTML")
        predictions = await fetch_predictions_from_api()
        text = build_vip_signals(predictions)
        await ctx.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, parse_mode="HTML", reply_markup=action_menu("signals"))
        return

# ═══════════════════════════════════════════
# טיפול בצילומי מסך והודעות טקסט
# ═══════════════════════════════════════════
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; uname = update.effective_user.username or update.effective_user.first_name or "משתמש"
    if is_blocked(uid) and not is_admin(uid): return

    db = load_db(); pend = db["pending"].get(str(uid))

    if update.message.photo and pend:
        await ctx.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=f"📸 <b>אישור תשלום חדש!</b>\n\n👤 @{uname} (ID: {uid})\n✅ לאישור: /approve_{uid}\n❌ לדחייה: /reject_{uid}", parse_mode="HTML")
        await update.message.reply_text("✅ <b>צילום המסך התקבל בהצלחה!</b>\nהמנוי שלך יופעל ברגע שהמנהל יאשר את ההעברה.", parse_mode="HTML", reply_markup=back_menu())
    else:
        await update.message.reply_text("שלח /start לפתיחת תפריט האפשרויות של Chance AI ⬡")

# ═══════════════════════════════════════════
# ניטור אוטומטי - שליחה לקבוצה בכל הגרלה חדשה
# ═══════════════════════════════════════════
async def auto_scan_loop(app):
    await asyncio.sleep(10)
    last_notified_draw = 0
    
    while True:
        try:
            print("🔄 בודק האם עלתה הגרלה חדשה ב-Chance AI...")
            predictions = await fetch_predictions_from_api()
            
            if predictions:
                latest_draw = predictions[0].get("target_draw_number")
                
                # תנאי פתיחה: פעם ראשונה שהלופ רץ, הוא מסתנכרן על המספר הנוכחי
                if last_notified_draw == 0:
                    last_notified_draw = latest_draw
                    
                # אם מספר ההגרלה גדל, סימן שיש הגרלה חדשה באוויר!
                elif latest_draw > last_notified_draw:
                    last_notified_draw = latest_draw
                    alert_text = build_vip_signals(predictions)
                    
                    # שליחה ישירה לקבוצה הציבורית שלך שמספרה הוגדר למעלה
                    try:
                        await app.bot.send_message(chat_id=CHAT_ID, text=alert_text, parse_mode="HTML")
                        print(f"🎯 עדכון אוטומטי נשלח בהצלחה לקבוצה עבור הגרלה #{latest_draw}")
                    except Exception as tg_err:
                        print(f"❌ שגיאה בשליחה לקבוצת הטלגרם: {tg_err}")
                        
        except Exception as e:
            print(f"❌ שגיאה בלופ הניטור האוטומטי: {e}")
            
        await asyncio.sleep(60) # בודק עדכון ב-API בכל דקה אחת כדי להיות הכי מהיר

# ═══════════════════════════════════════════
# הפעלת המערכת
# ═══════════════════════════════════════════
def main():
    print("🚀 מפעיל Chance AI Predictor Bot...")
    app = Application.builder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("admin",  cmd_admin))
    app.add_handler(MessageHandler(filters.Regex(r"^/approve_"), cmd_approve))
    app.add_handler(MessageHandler(filters.Regex(r"^/reject_"),  cmd_reject))
    app.add_handler(MessageHandler(filters.Regex(r"^/block_"),   cmd_block))
    app.add_handler(MessageHandler(filters.Regex(r"^/unblock_"), cmd_unblock))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    async def post_init(application):
        asyncio.create_task(auto_scan_loop(application))
        print("✅ הבוט התחבר ומנטר את Chance AI בהצלחה!")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
