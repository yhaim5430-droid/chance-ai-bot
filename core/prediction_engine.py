import random

from core.draw_analyzer import DrawAnalyzer


class PredictionEngine:

    def __init__(self, draws):

        self.draws = draws

        self.values = [
            "7",
            "8",
            "9",
            "10",
            "J",
            "Q",
            "K",
            "A"
        ]

        self.analyzer = DrawAnalyzer(draws)

        self.global_freq = (
            self.analyzer.get_card_frequencies()
        )

        self.position_freq = (
            self.analyzer.get_position_frequencies()
        )

    def weighted_pick(self, suit):

        weights = []

        for value in self.values:

            position_weight = (
                self.position_freq[suit].get(value, 0)
            )

            global_weight = (
                self.global_freq.get(value, 0)
            )

            score = (
                position_weight * 0.7
                + global_weight * 100 * 0.3
            )

            weights.append(score + 1)

        return random.choices(
            self.values,
            weights=weights,
            k=1
        )[0]

    def generate_candidate(self):

        return {
            "spade": self.weighted_pick("spade"),
            "heart": self.weighted_pick("heart"),
            "diamond": self.weighted_pick("diamond"),
            "club": self.weighted_pick("club")
        }

    def generate_candidates(self, n=300):

        candidates = []

        for _ in range(n):
            candidates.append(
                self.generate_candidate()
            )

        return candidates
