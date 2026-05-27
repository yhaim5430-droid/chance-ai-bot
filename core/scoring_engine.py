from collections import Counter
import math


class ScoringEngine:

    def __init__(self, draws):

        self.draws = draws

    def calculate_entropy(self, values):

        freq = Counter(values)

        total = len(values)

        entropy = 0

        for count in freq.values():

            p = count / total

            entropy -= p * math.log2(p)

        return entropy

    def diversity_score(self, candidate):

        values = list(candidate.values())

        unique = len(set(values))

        return unique / 4

    def balance_score(self, candidate):

        values = list(candidate.values())

        duplicates = len(values) - len(set(values))

        return max(0, 1 - duplicates * 0.25)

    def entropy_score(self, candidate):

        values = list(candidate.values())

        entropy = self.calculate_entropy(values)

        return min(entropy / 2, 1)

    def score(self, candidate):

        diversity = self.diversity_score(candidate)
        balance = self.balance_score(candidate)
        entropy = self.entropy_score(candidate)

        final_score = (
            diversity * 40
            + balance * 30
            + entropy * 30
        )

        return round(final_score, 2)
