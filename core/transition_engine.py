from collections import defaultdict, Counter


class TransitionEngine:
    """
    מנתח מעבר בין הגרלות (Markov-style קל משקל)
    לכל צבע (♠ ♥ ♦ ♣) ולכל ערך קלף.
    """

    def __init__(self, draws):
        self.draws = draws

        # transitions[suit][prev_value][next_value]
        self.transitions = {
            "spade": defaultdict(Counter),
            "heart": defaultdict(Counter),
            "diamond": defaultdict(Counter),
            "club": defaultdict(Counter),
        }

        self._build()

    # =========================
    # BUILD MODEL
    # =========================

    def _build(self):
        """
        בונה קשרים בין הגרלות עוקבות
        """
        if not self.draws or len(self.draws) < 2:
            return

        sorted_draws = sorted(
            self.draws,
            key=lambda x: int(x.get("draw_number", 0))
        )

        for i in range(len(sorted_draws) - 1):

            current = sorted_draws[i]
            nxt = sorted_draws[i + 1]

            for suit in ["spade", "heart", "diamond", "club"]:

                prev_val = current.get(suit)
                next_val = nxt.get(suit)

                if prev_val is None or next_val is None:
                    continue

                self.transitions[suit][prev_val][next_val] += 1

    # =========================
    # PROBABILITY
    # =========================

    def next_probability(self, suit, value):
        """
        מחזיר התפלגות מעבר לקלף הבא
        """

        if suit not in self.transitions:
            return {}

        next_map = self.transitions[suit].get(value, {})

        total = sum(next_map.values())

        if total == 0:
            return {}

        return {
            k: round(v / total, 4)
            for k, v in next_map.items()
        }

    # =========================
    # MOST LIKELY NEXT
    # =========================

    def most_likely_next(self, suit, value):
        """
        הקלף הכי סביר אחרי קלף נתון
        """

        next_map = self.transitions[suit].get(value, {})

        if not next_map:
            return None

        return next_map.most_common(1)[0][0]

    # =========================
    # STABILITY SCORE
    # =========================

    def stability(self, suit, value):
        """
        כמה הקלף "נשאר אותו דבר" בהגרלה הבאה
        """

        next_map = self.transitions[suit].get(value, {})

        if not next_map:
            return 0.0

        stay = next_map.get(value, 0)
        total = sum(next_map.values())

        return round(stay / total, 4)

    # =========================
    # GLOBAL INSIGHT
    # =========================

    def suit_dominance(self, suit):
        """
        כמה יציב כל צבע לאורך זמן
        """

        transitions = self.transitions.get(suit, {})

        total = 0
        self_loops = 0

        for prev, nexts in transitions.items():
            for nxt, count in nexts.items():
                total += count
                if prev == nxt:
                    self_loops += count

        if total == 0:
            return 0.0

        return round(self_loops / total, 4)
