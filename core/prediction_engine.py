import hashlib


class PredictionEngine:

    def __init__(self, draws):
        self.draws = draws

        self.suits = ["spade", "heart", "diamond", "club"]
        self.values = ["A", "K", "Q", "J", "10", "9", "8", "7"]

    # =========================
    # MAIN (compatibility fallback)
    # =========================

    def generate_candidates(self, n=300):
        """
        fallback ישן (לא בשימוש במצב יציב)
        """
        return [self.generate_deterministic(f"fallback_{i}") for i in range(n)]

    # =========================
    # CORE: DETERMINISTIC GENERATION
    # =========================

    def generate_deterministic(self, seed):
        """
        מייצר חיזוי אחד קבוע לחלוטין לפי seed
        """

        # hash קבוע
        h = hashlib.sha256(seed.encode()).hexdigest()

        # חיתוך ערכים מה-hash
        parts = [
            h[i:i+2] for i in range(0, 8, 2)
        ]

        # יצירת אינדקסים יציבים
        idx_s = int(parts[0], 16) % len(self.values)
        idx_h = int(parts[1], 16) % len(self.values)
        idx_d = int(parts[2], 16) % len(self.values)
        idx_c = int(parts[3], 16) % len(self.values)

        return {
            "spade": self.values[idx_s],
            "heart": self.values[idx_h],
            "diamond": self.values[idx_d],
            "club": self.values[idx_c]
        }

    # =========================
    # OPTIONAL: legacy random (not used)
    # =========================

    def generate_random_like(self):
        """
        שמור רק לצורך בדיקות, לא בשימוש במערכת היציבה
        """
        import random

        return {
            "spade": random.choice(self.values),
            "heart": random.choice(self.values),
            "diamond": random.choice(self.values),
            "club": random.choice(self.values)
        }
