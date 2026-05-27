from collections import Counter


class DrawAnalyzer:

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

    def get_card_frequencies(self):

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

        frequencies = {}

        for v in self.values:

            frequencies[v] = (
                round(
                    counter.get(v, 0)
                    / total,
                    4
                )
                if total
                else 0
            )

        return frequencies

    def get_position_frequencies(self):

        result = {
            "spade": Counter(),
            "heart": Counter(),
            "diamond": Counter(),
            "club": Counter()
        }

        for d in self.draws:

            result["spade"][
                d.get("spade")
            ] += 1

            result["heart"][
                d.get("heart")
            ] += 1

            result["diamond"][
                d.get("diamond")
            ] += 1

            result["club"][
                d.get("club")
            ] += 1

        return result
