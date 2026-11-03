from pathlib import Path
import pandas as pd
from airsource.pipeline import make_synthetic_fixture,build_issues,evaluate_forecasts
from app import app_factory

def test_model_end_to_end(tmp_path):
    h=make_synthetic_fixture(225,seed=88)
    i=build_issues(h,station='SYNTHETIC_INTEGRATION')
    scores,preds,splits=evaluate_forecasts(i,tmp_path,data_label='SYNTHETIC INTEGRATION',train_per_station=True)
    assert len(scores)==8 # 2 horizons x (LightGBM, Persistence, Seasonal, Validation-selected)
    assert len(preds)>30
    assert (tmp_path/'models/SYNTHETIC_INTEGRATION/target_0_24_lightgbm.joblib').exists()
    assert (tmp_path/'interval_metrics.csv').exists()
    assert (scores.data_label=='SYNTHETIC INTEGRATION').all()

def test_actual_gradio_app_constructs():
    app=app_factory()
    assert app is not None
