from core.prediction_engine import PredictionEngine
from core.scoring_engine import ScoringEngine


class Orchestrator:

    def generate_best_prediction(self):

        engine = PredictionEngine()
        scorer = ScoringEngine()

        candidates = engine.generate_candidates(300)

        best = None
        best_score = -999

        for c in candidates:
            s = scorer.score(c)

            if s > best_score:
                best_score = s
                best = c

        return best, best_score
