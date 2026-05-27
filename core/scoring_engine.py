from core.markov_engine import MarkovEngine


class ScoringEngine:

    def __init__(self):
        pass

    def score(self, candidate, history=None):
        """
        Scoring Engine משודרג (B stage) עם Markov transitions
        """

        score = 0
        reasons = []

        values = list(candidate.values())

        # =========================
        # בסיס יציב
        # =========================
        score += 6
        reasons.append("base signal")

        # =========================
        # גיוון
        # =========================
        unique = len(set(values))
        diversity_score = unique * 5
        score += diversity_score

        if unique == 4:
            reasons.append("good diversity")
        elif unique == 3:
            reasons.append("medium diversity")
        else:
            reasons.append("low diversity")

        # =========================
        # Markov transitions (B core upgrade)
        # =========================
        if history and len(history) > 5:

            try:
                markov = MarkovEngine(history)
                transition_score = markov.transition_score(candidate)

                # מנרמלים כדי לא לנפח ציונים
                score += min(transition_score * 0.7, 25)

                if transition_score > 20:
                    reasons.append("strong transition pattern")
                elif transition_score > 10:
                    reasons.append("moderate transition pattern")
                else:
                    reasons.append("weak transition pattern")

            except Exception:
                # fallback בטוח אם משהו נשבר
                reasons.append("markov unavailable")

        # =========================
        # מניעת ציונים מנופחים
        # =========================
        score = max(0, min(score, 92))

        return {
            "score": round(score, 2),
            "reasons": reasons
        }
