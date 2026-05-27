from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine
from core.transition_engine import TransitionEngine
import hashlib


class Orchestrator:

    def __init__(self, draws):

        self.draws = draws

        self.predictor = PredictionEngine(draws)
        self.scorer = ScoringEngine()
        self.transition = TransitionEngine(draws)

    # =========================
    # STABLE SEED (הדבר הכי חשוב)
    # =========================

    def _get_seed(self):
        """
        יוצר seed קבוע לפי ההגרלה האחרונה
        => מבטיח חיזוי אחד בלבד
        """

        if not self.draws:
            return "0"

        latest = max(
            self.draws,
            key=lambda d: int(d.get("draw_number", 0))
        )

        raw = f"{latest.get('draw_number')}|{latest}"

        return hashlib.sha256(raw.encode()).hexdigest()

    # =========================
    # CONFIDENCE
    # =========================

    def calculate_confidence(self, score):

        confidence = round(min(score, 95), 1)

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

        if score >= 60:
            reasons.append("• statistically weighted")

        if not reasons:
            reasons.append("• weak statistical signal")

        return "\n".join(reasons)

    # =========================
    # SINGLE STABLE PREDICTION
    # =========================

    def predict(self):

        # 1. seed קבוע
        seed = self._get_seed()

        # 2. יצירת מועמד אחד בלבד (לא 300)
        candidate = self.predictor.generate_deterministic(seed)

        # 3. score יציב
        score_data = self.scorer.score(candidate)
        score = score_data["score"]

        # 4. יעד הגרלה
        latest_draw = max(
            [int(d.get("draw_number", 0)) for d in self.draws],
            default=0
        )

        target_draw = latest_draw + 1

        # 5. confidence
        confidence, level = self.calculate_confidence(score)

        # 6. report
        report = self.build_report(candidate, score)

        return {
            "target_draw": target_draw,
            "prediction": candidate,
            "score": score,
            "confidence": confidence,
            "confidence_level": level,
            "report": report
        }

    # =========================
    # FUTURE LEARNING
    # =========================

    def update_learning(self, prediction, actual_result):
        pass
