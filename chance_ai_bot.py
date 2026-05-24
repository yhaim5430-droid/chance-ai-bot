import { createClient } from '@base44/sdk'; // במידה והמערכת משתמשת ב-SDK הפנימי

// ═══════════════════════════════════════════
# הגדרות חיבור ל-Chance AI ולטלגרם
// ═══════════════════════════════════════════
const CHANCE_APP_ID = "699f6d52f3302128ab050b10";
const CHANCE_API_KEY = "20742ca24625436b8963159c29dd34c3";
const TELEGRAM_TOKEN = "7754804245:AAEf5lCTTU3NB7qNnOa1-HKJXcpZLDOdseM";
const CHAT_ID = "-1002360888694"; // מזהה קבוצת הטלגרם שלך

// פונקציית עזר לשליחת הודעות לטלגרם
async function sendTelegramMessage(chatId, text) {
    const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
    await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: chatId,
            text: text,
            parse_mode: 'HTML'
        })
    });
}

// ═══════════════════════════════════════════
# משיכת נתונים ישירות מ-Chance AI
// ═══════════════════════════════════════════

// 1. כפתור: המלצה חינם (מודל Quantum Human)
async function handleFreeRecommendation(userId) {
    try {
        // פנייה ישירה לישות Prediction באפליקציה שלך
        const response = await fetch(`https://api.base44.com/v1/apps/${CHANCE_APP_ID}/entities/Prediction/records?sort=-target_draw_number&limit=20`, {
            headers: { 'Authorization': `Bearer ${CHANCE_API_KEY}` }
        });
        const data = await response.json();
        const records = data.records || [];

        // סינון מודל Human (Quantum Human v5.0)
        const humanPred = records.find(p => p.method === "Human");

        if (humanPred) {
            const msg = `⭐ <b>המלצה חינם — Quantum Human v5.0</b>\n` +
                        `🎯 הגרלה מטרה: <b>#${humanPred.target_draw_number}</b>\n` +
                        `━━━━━━━━━━━━━━━━━━━━\n\n` +
                        `♠️ עלה:  <b>${humanPred.main_spade || '—'}</b>\n` +
                        `❤️ לב:  <b>${humanPred.main_heart || '—'}</b>\n` +
                        `♦️ יהלום: <b>${humanPred.main_diamond || '—'}</b>\n` +
                        `♣️ תלתן:  <b>${humanPred.main_club || '—'}</b>\n\n` +
                        `✨ <i>החיזוקים והשיטות המלאות זמינים במנוי ה-VIP!</i>\n` +
                        `<i>⬡ Chance AI Predictor</i>`;
            await sendTelegramMessage(userId, msg);
        } else {
            await sendTelegramMessage(userId, "❌ לא נמצא חיזוי מעודכן לשיטת Quantum Human כרגע.");
        }
    } catch (error) {
        console.error("Error fetching free recommendation:", error);
    }
}

// 2. כפתור: חיזוי VIP (כל 4 השיטות והחיזוקים)
async function handleVipPredictions(userId) {
    try {
        const response = await fetch(`https://api.base44.com/v1/apps/${CHANCE_APP_ID}/entities/Prediction/records?sort=-target_draw_number&limit=20`, {
            headers: { 'Authorization': `Bearer ${CHANCE_API_KEY}` }
        });
        const data = await response.json();
        const records = data.records || [];

        if (records.length === 0) {
            await sendTelegramMessage(userId, "❌ אין נתונים זמינים כרגע.");
            return;
        }

        const latestDraw = records[0].target_draw_number;
        const currentPreds = records.filter(p => p.target_draw_number === latestDraw);

        let msg = `🔮 <b>ריכוז חיזויים מורחב להגרלה #${latestDraw}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n`;

        const methodsMap = {
            "Human": "🥇 Quantum Human v5.0 (הכי מדויק)",
            "Baseline": "🥈 Baseline v5.1",
            "Hybrid": "🥉 Hybrid v6",
            "MirrorReverse": "🔄 Mirror Reverse Theory"
        };

        for (const [m_key, m_name] of Object.entries(methodsMap)) {
            const p = currentPreds.find(pred => pred.method === m_key);
            if (p) {
                msg += `<b>{m_name}:</b>\n` +
                       `• ראשי: ♠️${p.main_spade || ''} ❤️${p.main_heart || ''} ♦️${p.main_diamond || ''} ♣️${p.main_club || ''}\n` +
                       `• חיזוקים: <b>${p.strong_cards || 'אין'}</b>\n\n`;
            }
        }

        msg += `⚠️ <i>השתמש במידע באחריותך בלבד. בהצלחה!</i>\n<i>⬡ Chance AI VIP</i>`;
        await sendTelegramMessage(userId, msg);
    } catch (error) {
        console.error("Error fetching VIP predictions:", error);
    }
}

// 3. כפתור: 10 הגרלות אחרונות
async function handleLastDraws(userId) {
    try {
        const response = await fetch(`https://api.base44.com/v1/apps/${CHANCE_APP_ID}/entities/Draw/records?sort=-draw_number&limit=10`, {
            headers: { 'Authorization': `Bearer ${CHANCE_API_KEY}` }
        });
        const data = await response.json();
        const draws = data.records || [];

        let msg = `🎰 <b>תוצאות 10 הגרלות אחרונות</b>\n━━━━━━━━━━━━━━━━━━━━\n\n`;
        draws.forEach(d => {
            msg += `<b>הגרלה #${d.draw_number}</b>: ♠️${d.spade} ❤️${d.heart} ♦️${d.diamond} ♣️${d.club}\n`;
        });
        msg += `\n<i>⬡ Chance AI Predictor</i>`;
        
        await sendTelegramMessage(userId, msg);
    } catch (error) {
        console.error("Error fetching last draws:", error);
    }
}

// ═══════════════════════════════════════════
# ניטור אוטומטי - שליחה לקבוצה בכל הגרלה חדשה
// ═══════════════════════════════════════════
let lastNotifiedDraw = 0;

async function checkNewDrawAuto() {
    try {
        const response = await fetch(`https://api.base44.com/v1/apps/${CHANCE_APP_ID}/entities/Prediction/records?sort=-target_draw_number&limit=1`, {
            headers: { 'Authorization': `Bearer ${CHANCE_API_KEY}` }
        });
        const data = await response.json();
        const records = data.records || [];

        if (records.length > 0) {
            const latestDraw = records[0].target_draw_number;
            
            // אם זיהינו מספר הגרלה חדש שעוד לא שלחנו לקבוצה
            if (latestDraw > lastNotifiedDraw) {
                lastNotifiedDraw = latestDraw;
                // שולח את ריכוז כל החיזויים ישירות לקבוצת הטלגרם שלך
                await handleVipPredictions(CHAT_ID);
                console.log(`✅ עדכון אוטומטי נשלח לקבוצה עבור הגרלה #${latestDraw}`);
            }
        }
    } catch (error) {
        console.error("Error in auto scan loop:", error);
    }
}

// הרצת בדיקה אוטומטית כל 5 דקות
setInterval(checkNewDrawAuto, 5 * 60 * 1000);

// ═══════════════════════════════════════════
# קליטת לחיצות על כפתורים מטלגרם (הגדרת ה-Handler של הבוט)
// ═══════════════════════════════════════════
export async function onTelegramCallback(callbackQuery) {
    const data = callbackQuery.data;
    const userId = callbackQuery.from.id;

    if (data === "free_recommendation") {
        await handleFreeRecommendation(userId);
    } else if (data === "vip_signals") {
        await handleVipPredictions(userId);
    } else if (data === "last_draws") {
        await handleLastDraws(userId);
    }
    // כאן נשארים מנגנוני המנויים וחבר מביא חבר המקוריים שלך...
}
