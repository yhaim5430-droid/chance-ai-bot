from core.markov_engine import MarkovEngine
from core.learning_engine import LearningEngine


class ScoringEngine:

    def __init__(self):
        self.learning = LearningEngine()

    def score(self, candidate, history=None):

        score = 0
        reasons = []

        values = list(candidate.values())

        # =========================
        # בסיס
        # =========================
        score += 5 * self.learning.weights["diversity"]
        reasons.append("base signal")

        # =========================
        # גיוון
        # =========================
        unique = len(set(values))
        score += unique * 4 * self.learning.weights["diversity"]

        if unique == 4:
            reasons.append("good diversity")

        # =========================
        # Markov
        # =========================
        if history and len(history) > 5:

            markov = MarkovEngine(history)
            transition = markov.transition_score(candidate)

            score += min(
                transition * 0.6 * self.learning.weights["markov"],
                25
            )

            if transition > 20:
                reasons.append("strong transition pattern")

        # =========================
        # היסטוריה
        # =========================
        if history:
            hits = 0

            for d in history[:15]:
                for v in d.values():
                    if v in values:
                        hits += 1

            score += min(hits * 1.2 * self.learning.weights["history"], 20)

        # =========================
        # מניעת אשליה
        # =========================
        score = max(0, min(score, 92))

        return {
            "score": round(score, 2),
            "reasons": reasons,
            "weights": self.learning.weights
        }
