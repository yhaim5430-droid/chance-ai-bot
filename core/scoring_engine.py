from collections import Counter
import math


class ScoringEngine:

    def __init__(self, draws):

        self.draws = draws

        self.values = ["7", "8", "9", "10", "J", "Q", "K", "A"]

        self.analyzed = self._analyze()

    # =========================
    # ANALYSIS
    # =========================

    def _analyze(self):

        cards = []

        for d in self.draws:

            cards.extend([
                d.get("spade"),
                d.get("heart"),
                d.get("diamond"),
                d.get("club")
            ])

        counter = Counter(cards)

        total = sum(counter.values())

        freq = {}

        for v in self.values:

            freq[v] = counter.get(v, 0) / total if total else 0

        return {
            "freq": freq,
            "counter": counter,
            "total": total
        }

    # =========================
    # CARD SCORE
    # =========================

    def score_card(self, card):

        freq = self.analyzed["freq"].get(card, 0)

        # rarity score (יותר נדיר = יותר גבוה)
        rarity = 1 - freq

        # stability penalty (מונע overfitting)
        stability = math.log(1 + self.analyzed["counter"].get(card, 0))

        score = (0.7 * rarity) + (0.3 * (1 / (1 + stability)))

        return round(score, 4)

    # =========================
    # PREDICTION SCORE
    # =========================

    def score_prediction(self, prediction):

        cards = [
            prediction.get("main_spade"),
            prediction.get("main_heart"),
            prediction.get("main_diamond"),
            prediction.get("main_club")
        ]

        scores = [self.score_card(c) for c in cards]

        avg_score = sum(scores) / len(scores)

        # diversity bonus (מונע חזרתיות)
        unique_bonus = len(set(cards)) / 4

        final_score = (0.8 * avg_score) + (0.2 * unique_bonus)

        confidence = min(0.85, avg_score)

        return {
            "score": round(final_score * 100, 2),
            "confidence": round(confidence * 100, 2),
            "details": {
                "card_scores": dict(zip(cards, scores)),
                "unique_ratio": unique_bonus
            }
        }
