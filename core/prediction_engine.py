import random
from collections import Counter

VALUES = ["7", "8", "9", "10", "J", "Q", "K", "A"]

class PredictionEngine:

    def __init__(self, draws=None):
        self.draws = draws or []
        self.weights = self.build_weights()

    def build_weights(self):
        """בונה משקלים לפי ההיסטוריה האמיתית"""
        if not self.draws:
            # אם אין היסטוריה - משקלים שווים
            return {v: 1.0 for v in VALUES}

        all_cards = []
        for d in self.draws:
            all_cards += [
                d.get("spade"),
                d.get("heart"),
                d.get("diamond"),
                d.get("club")
            ]

        counter = Counter(all_cards)
        total = sum(counter.values())

        # חישוב הסתברות
        weights = {}
        for v in VALUES:
            count = counter.get(v, 0)
            weights[v] = (count / total) if total > 0 else 1.0

        return weights

    def weighted_pick(self):
        """בוחר קלף לפי משקל (הסתברות)"""
        return random.choices(
            VALUES,
            weights=[self.weights[v] for v in VALUES],
            k=1
        )[0]

    def generate_candidates(self, n=300):
        """מייצר מועמדים עם הטיה היסטורית"""
        return [
            {
                "spade": self.weighted_pick(),
                "heart": self.weighted_pick(),
                "diamond": self.weighted_pick(),
                "club": self.weighted_pick()
            }
            for _ in range(n)
        ]
