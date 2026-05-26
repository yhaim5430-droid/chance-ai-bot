from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine

class Orchestrator:

    def generate_best_prediction(self, target_draw=None):
        
        # לוקח היסטוריה של 100 הגרלות אחרונות
        from chance_ai_bot import get_data  # ייבוא זמני
        history = get_data("Draw", 100)
        from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine

class Orchestrator:

    def generate_best_prediction(self, target_draw=None):
        
        # תמיד מושך נתונים טריים
        from chance_ai_bot import get_data
        history = get_data("Draw", 150)   # יותר נתונים + טרי
        
        engine = PredictionEngine(draws=history)
        scorer = ScoringEngine()

        candidates = engine.generate_candidates(500)   # יותר מועמדים = יותר מגוון

        best = None
        best_score = -999

        for c in candidates:
            s = scorer.score(c)
            if s > best_score:
                best_score = s
                best = c

        return {
            "prediction": best,
            "score": best_score,
            "target_draw": target_draw,
            "history_size": len(history) if history else 0
        }
        engine = PredictionEngine(draws=history)
        scorer = ScoringEngine()

        candidates = engine.generate_candidates(400)

        best = None
        best_score = -999

        for c in candidates:
            s = scorer.score(c)
            if s > best_score:
                best_score = s
                best = c

        return {
            "prediction": best,
            "score": best_score,
            "target_draw": target_draw,
            "history_size": len(history) if history else 0
        }
