class ScoringEngine:

    def __init__(self):
        pass

    def score(self, candidate, history=None):
        """
        מחשב ציון לחיזוי
        """

        score = 0
        reasons = []

        # בסיס יציבות
        score += 30
        reasons.append("base stability")

        # גיוון קלפים
        unique = len(set(candidate.values()))
        score += unique * 10
        reasons.append("diversity check")

        # בונוס אם יש התאמה להיסטוריה
        if history:
            score += 20
            reasons.append("history alignment")

        # נרמול
        score = min(score, 100)

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
