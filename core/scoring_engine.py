from collections import defaultdict

class ScoringEngine:

    def __init__(self):
        # למידה עתידית (לא חובה כרגע אבל מוכן)
        self.transition = defaultdict(lambda: defaultdict(int))

    def update(self, prediction, actual):
        """
        learning layer (future use)
        """
        pass

    def score(self, candidate, history=None):
        """
        מחשב ציון אמיתי (לא מזויף 100)
        """

        score = 0
        reasons = []

        values = list(candidate.values())

        # 1. גיוון בסיסי
        unique = len(set(values))
        diversity_score = unique * 12
        score += diversity_score

        if unique >= 4:
            reasons.append("good diversity")

        # 2. איזון בין קלפים גבוהים/נמוכים
        high_cards = sum(1 for v in values if v in ["10", "J", "Q", "K", "A"])
        low_cards = 4 - high_cards

        balance = 10 - abs(high_cards - low_cards)
        score += balance * 3

        if abs(high_cards - low_cards) <= 1:
            reasons.append("balanced structure")

        # 3. דמיון להיסטוריה (אם יש)
        if history:
            history_values = []
            for h in history[-10:]:
                history_values.extend(list(h.values()))

            overlap = len(set(values) & set(history_values))
            score += overlap * 4

            if overlap >= 2:
                reasons.append("statistical alignment")

        # 4. מניעת זיוף 100
        score = min(score, 92)

        # 5. נורמליזציה
        score = max(5, score)

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
