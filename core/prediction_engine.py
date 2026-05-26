import random

VALUES = ["7","8","9","10","J","Q","K","A"]

class PredictionEngine:

    def generate_candidates(self, n=200):

        return [
            {
                "spade": random.choice(VALUES),
                "heart": random.choice(VALUES),
                "diamond": random.choice(VALUES),
                "club": random.choice(VALUES)
            }
            for _ in range(n)
        ]
