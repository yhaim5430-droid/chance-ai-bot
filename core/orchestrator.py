from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine


class Orchestrator:

    def __init__(self, draws):

        self.draws = draws
        self.predictor = PredictionEngine(draws)
        self.scorer = ScoringEngine()

    def calculate_confidence(self, best_score):

        confidence = round(min(best_score, 95), 1)

        if confidence >= 80:
            level = "Moderate"
        elif confidence >= 60:
            level = "Low-Moderate"
        else:
            level = "Low"

        return confidence, level

    def build_report(self, prediction, score, confidence_level):

        unique_cards = len(set(prediction.values()))
        reasons = []

        if unique_cards >= 4:
            reasons.append("• good diversity")

        if score >= 70:
            reasons.append("• balanced structure")

        if score >= 60:
            reasons.append("• statistically weighted")

        if not reasons:
            reasons.append("• weak statistical signal")

        return "\n".join(reasons)

    def predict(self):

        candidates = self.predictor.generate_candidates(200)

        scored = []

        for candidate in candidates:

            result = self.scorer.score(candidate)

            scored.append({
                "candidate": candidate,
                "score": result["score"]
            })

        best = max(scored, key=lambda x: x["score"])

        latest_draw = max(
            [int(d.get("draw_number", 0)) for d in self.draws],
            default=0
        )

        target_draw = latest_draw + 1

        confidence, level = self.calculate_confidence(best["score"])

        report = self.build_report(
            prediction=best["candidate"],
            score=best["score"],
            confidence_level=level
        )

        return {
            "target_draw": target_draw,
            "prediction": best["candidate"],
            "score": best["score"],
            "confidence": confidence,
            "confidence_level": level,
            "report": report
        }

    def update_learning(self, prediction, actual_result):
        """
        אופציונלי לשלב C (לא חובה עכשיו)
        """
        self.scorer.update(prediction, actual_result)
