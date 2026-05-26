from collections import Counter
import math

class ScoringEngine:

    def score(self, c):

        values = [c[k] for k in c]

        unique = len(set(values))
        balance = unique / 4

        freq = Counter(values)
        entropy = -sum((v/4)*math.log2(v/4) for v in freq.values())

        return round(balance*60 + entropy*40, 2)
