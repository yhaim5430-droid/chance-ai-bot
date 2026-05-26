import random
from collections import Counter

VALUES = ["7", "8", "9", "10", "J", "Q", "K", "A"]

class PredictionEngine:

    def __init__(self, draws=None):
        self.draws = draws or []
        self.weights = self.build_weights()

    def build_weights(self):
        if not self.draws:
            return {v: 1.0 for v in VALUES}

        all_cards = []
        for d in self.draws:
            all_cards.extend([
                d.get("spade"),
                d.get("heart"),
                d.get("diamond"),
                d.get("club")
            ])

        counter = Counter(all_cards)
        total = sum(counter.values()) or 1

        weights = {v: (counter.get(v, 0) / total) for v in VALUES}
        
        # קצת רעש כדי שהחיזויים לא יהיו זהים כל פעם
        for v in weights:
            weights[v] += random.uniform(-0.03, 0.03)
            if weights[v] < 0.01:
                weights[v] = 0.01

        return weights

    def weighted_pick(self):
        return random.choices(
            VALUES,
            weights=[self.weights[v] for v in VALUES],
            k=1
        )[0]

    def generate_candidates(self, n=500):
        return [
            {
                "spade": self.weighted_pick(),
                "heart": self.weighted_pick(),
                "diamond": self.weighted_pick(),
                "club": self.weighted_pick()
            }
            for _ in range(n)
        ]
