from realview_chat.services.analysis_service import compute_stats, compute_summary, get_properties
from realview_chat.services.analysis_service import _compute_calibration
import pytest

class FakeFeedback:
    def __init__(self, property_id, filename, classification):
        self.property_id = property_id
        self.filename = filename
        self.classification = classification
        self.scores = []

class FakeScore:
        def __init__(self, score_type, value):
            self.score_type = score_type
            self.value = value


def test_compute_stats_basic():
    feedback = [
    FakeFeedback("123", "a.jpg", "correct"),
    FakeFeedback("123", "b.jpg", "fp"),
    FakeFeedback("123", "c.jpg", "fn"),
    ]   

    ai_scores = []

    result = compute_stats(feedback, ai_scores)
    
    assert result["correct"] == 1
    assert result["fp"] == 1
    assert result["fn"] == 1

    assert result["total_classified"] == 3

def test_compute_stats_empty():

    result = compute_stats([], [])

    assert result["correct"] == 0
    assert result["fp"] == 0
    assert result["fn"] == 0
    assert result["total_classified"] == 0


def test_compute_calibration_basic():

    flattened = [
        {
            "property_id": "123",
            "filename": "a.jpg",
            "score_type": "condition",
            "value": 3
        }
    ]

    ai_scores = {
        ("123", "a.jpg"): {
            "condition": 5
        }
    }

    result = _compute_calibration(flattened, ai_scores)

    assert result["condition"]["pairs"] == 1
    assert result["condition"]["mae"] == 2
    assert result["condition"]["bias"] != 0
    assert result["condition"]["agreement_rate"] < 100