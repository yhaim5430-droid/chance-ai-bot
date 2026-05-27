class ScoringEngine:

    def __init__(self):
        pass

    def score(self, candidate, history=None):
        """
        מחשב ציון לחיזוי (גרסה מאוזנת ולא מנופחת)
        """

        score = 0
        reasons = []

        values = list(candidate.values())

        # =========================
        # בסיס נמוך יותר (לא מנפח ציונים)
        # =========================
        score += 10
        reasons.append("base signal")

        # =========================
        # גיוון – מדורג ולא מקסימום
        # =========================
        unique = len(set(values))
        diversity_score = unique * 7  # פחות אגרסיבי מהגרסה הקודמת
        score += diversity_score

        if unique == 4:
            reasons.append("good diversity")
        elif unique == 3:
            reasons.append("medium diversity")
        else:
            reasons.append("low diversity")

        # =========================
        # היסטוריה – השפעה אמיתית אבל לא מוגזמת
        # =========================
        if history:
            hits = 0

            for d in history[:20]:
                for v in d.values():
                    if v in values:
                        hits += 1

            history_score = min(hits * 1.2, 20)
            score += history_score

            if hits > 15:
                reasons.append("strong history alignment")
            elif hits > 8:
                reasons.append("moderate history alignment")
            else:
                reasons.append("weak history alignment")

        # =========================
        # מניעת זיוף 100
        # =========================
        score = min(score, 90)

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
