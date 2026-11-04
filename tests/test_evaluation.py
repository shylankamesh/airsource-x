import pytest
from airsource.evaluation import evaluate_predictions, evaluate_by_horizon
import pandas as pd


def test_event_metrics_are_explicit_and_correct():
    result = evaluate_predictions([10, 80, 100, 20], [20, 70, 110, 90], severe_threshold=75)
    assert result["severe_event"]["tp"] == 1
    assert result["severe_event"]["fn"] == 1
    assert result["severe_event"]["fp"] == 1


def test_metrics_ignore_nonfinite_pairs():
    result = evaluate_predictions([1, 2, float("nan")], [2, float("inf"), 3])
    assert result["samples"] == 1
    assert result["mae"] == 1


def test_length_mismatch_rejected():
    with pytest.raises(ValueError):
        evaluate_predictions([1], [1, 2])


def test_horizon_grouping():
    frame = pd.DataFrame({"actual":[1,2], "predicted":[2,2], "horizon":["1h","24h"]})
    assert set(evaluate_by_horizon(frame)) == {"1h", "24h"}
