from collections import defaultdict

class MarkovEngine:

    def __init__(self, history):
        self.history = history
        self.transitions = defaultdict(lambda: defaultdict(int))
        self._build()

    def _build(self):
        """
        בונה מטריצת מעבר בין קלפים
        """

        for i in range(len(self.history) - 1):
            current = list(self.history[i].values())
            nxt = list(self.history[i + 1].values())

            for c in current:
                for n in nxt:
                    self.transitions[c][n] += 1

    def transition_score(self, candidate):
        """
        מחשב כמה החיזוי "מתאים" להיסטוריית מעברים
        """

        values = list(candidate.values())
        score = 0

        for c in values:
            if c in self.transitions:
                for n in values:
                    score += self.transitions[c].get(n, 0)

        return score
