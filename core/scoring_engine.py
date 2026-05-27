class ScoringEngine:

    def __init__(self):
        pass

    def score(self, candidate, history=None):
        """
        ניקוד יציב, מאוזן ולא מנופח (A stage)
        """

        score = 0
        reasons = []

        values = list(candidate.values())

        # =========================
        # בסיס יציב
        # =========================
        score += 8
        reasons.append("base signal")

        # =========================
        # גיוון (לא דומיננטי מדי)
        # =========================
        unique = len(set(values))
        score += unique * 6

        if unique == 4:
            reasons.append("good diversity")
        elif unique == 3:
            reasons.append("medium diversity")
        else:
            reasons.append("low diversity")

        # =========================
        # אנטי חזרתיות (חשוב מאוד ל-A)
        # =========================
        if len(values) != len(set(values)):
            score -= 8
            reasons.append("duplicate penalty")

        # =========================
        # Recency / היסטוריה אמיתית
        # =========================
        if history:
            recent = history[:10]

            hits = 0
            recent_bias = 0

            for i, d in enumerate(recent):
                weight = 1.0 - (i * 0.08)  # יותר משקל לאחרונים
                for v in d.values():
                    if v in values:
                        hits += weight

            score += min(hits * 1.5, 18)

            if hits > 12:
                reasons.append("strong recent alignment")
            elif hits > 6:
                reasons.append("moderate recent alignment")
            else:
                reasons.append("weak recent alignment")

        # =========================
        # חסימת אשליית 100
        # =========================
        score = max(0, min(score, 88))

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
