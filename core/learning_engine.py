class LearningEngine:

    def __init__(self):
        self.weights = {
            "diversity": 1.0,
            "markov": 1.0,
            "history": 1.0
        }

    def update(self, prediction, actual_result):
        """
        עדכון משקולות לפי הצלחה
        """

        predicted = set(prediction.values())
        actual = set(actual_result.values())

        hits = len(predicted & actual)

        # התאמה פשוטה
        if hits >= 3:
            self.weights["markov"] += 0.05
            self.weights["history"] += 0.03
        elif hits <= 1:
            self.weights["diversity"] += 0.02
            self.weights["markov"] -= 0.02

        # נרמול
        for k in self.weights:
            self.weights[k] = max(0.5, min(self.weights[k], 2.0))

        return self.weights
