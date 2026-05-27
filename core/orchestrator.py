from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine
from core.transition_engine import TransitionEngine


class Orchestrator:

    def __init__(self, draws):

        self.draws = draws

        # engines
        self.predictor = PredictionEngine(draws)
        self.scorer = ScoringEngine()
        self.transition = TransitionEngine(draws)

    # =========================
    # CONFIDENCE
    # =========================

    def calculate_confidence(self, best_score):

        confidence = round(min(best_score, 95), 1)

        if confidence >= 80:
            level = "Moderate"
        elif confidence >= 60:
            level = "Low-Moderate"
        else:
            level = "Low"

        return confidence, level

    # =========================
    # REPORT
    # =========================

    def build_report(self, prediction, score):

        unique_cards = len(set(prediction.values()))
        reasons = []

        if unique_cards >= 4:
            reasons.append("• good diversity")

        if score >= 75:
            reasons.append("• balanced structure")

        if score >= 65:
            reasons.append("• statistically weighted")

        # שימוש ב־transition engine (אמיתי עכשיו)
        spade = prediction.get("spade")
        heart = prediction.get("heart")
        diamond = prediction.get("diamond")
        club = prediction.get("club")

        if spade:
            stability = self.transition.stability("spade", spade)
            if stability > 0.3:
                reasons.append("• spade stability signal")

        if heart:
            stability = self.transition.stability("heart", heart)
            if stability > 0.3:
                reasons.append("• heart stability signal")

        if not reasons:
            reasons.append("• weak statistical signal")

        return "\n".join(reasons)

    # =========================
    # PREDICT
    # =========================

    def predict(self):

        candidates = self.predictor.generate_candidates(300)

        scored = []

        for candidate in candidates:

            score_data = self.scorer.score(candidate)
            score = score_data["score"]

            scored.append({
                "candidate": candidate,
                "score": score
            })

        best = max(scored, key=lambda x: x["score"])

        latest_draw = max(
            [
                int(d.get("draw_number", 0))
                for d in self.draws
            ],
            default=0
        )

        target_draw = latest_draw + 1

        confidence, level = self.calculate_confidence(best["score"])

        report = self.build_report(
            prediction=best["candidate"],
            score=best["score"]
        )

        return {
            "target_draw": target_draw,
            "prediction": best["candidate"],
            "score": best["score"],
            "confidence": confidence,
            "confidence_level": level,
            "report": report
        }

    # =========================
    # OPTIONAL FUTURE LEARNING
    # =========================

    def update_learning(self, prediction, actual_result):
        """
        עתידי: שיפור מודלים לפי תוצאות אמת
        """
        pass
