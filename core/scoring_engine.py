class ScoringEngine:

    def __init__(self):
        pass

    def score(self, candidate, history=None):
        """
        מחשב ציון לחיזוי
        """

        score = 0
        reasons = []

        values = list(candidate.values())

        # בסיס יציבות
        score += 25
        reasons.append("base stability")

        # גיוון קלפים
        unique = len(set(values))
        score += unique * 12
        reasons.append("diversity check")

        # בונוס על מבנה מאוזן (לא אותו סוג חוזר)
        if unique >= 4:
            score += 15
            reasons.append("balanced structure")

        # חיזוק היסטוריה אמיתי (אם קיים)
        if history:
            hits = 0
            for d in history[:10]:
                for v in d.values():
                    if v in values:
                        hits += 1

            score += min(hits * 2, 20)
            reasons.append("history alignment")

        # מניעת overfit
        if len(set(values)) < 3:
            score -= 10
            reasons.append("low diversity penalty")

        score = max(0, min(score, 100))

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
