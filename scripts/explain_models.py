"""Optional genuine model SHAP decomposition; NOT physical pollution source attribution."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'

def main():
    import shap
    from airsource.pipeline import FEATURES
    issues=pd.read_csv(OUT/'forecast_issue_table.csv')
    issues['issue_ist']=pd.to_datetime(issues.issue_ist,utc=True)
    data=[];locals_=[]
    for file in sorted((OUT/'models').glob('*/*_lightgbm.joblib')):
        horizon=file.stem.replace('_lightgbm','')
        station=file.parent.name
        meta=json.loads((file.parent/f'{horizon}_metadata.json').read_text())
        start=pd.to_datetime(meta['test_first'],utc=True)
        s=issues.loc[(issues.station==station)&(issues.issue_ist>=start)&issues[horizon].notna()].head(40)
        if len(s)<10:continue
        model=joblib.load(file) # only load model files generated locally; untrusted pickle is unsafe
        X=s[FEATURES]
        exp=shap.TreeExplainer(model)
        values=np.asarray(exp.shap_values(X))
        if values.ndim!=2:raise ValueError('Unexpected SHAP shape; refusing to make claim')
        for j,col in enumerate(FEATURES):
            data.append({'station':station,'horizon':horizon,'feature':col,
                         'mean_absolute_SHAP_ugm3':float(np.abs(values[:,j]).mean()),
                         'rows':len(s),'interpretation':'model effect, NOT physical source contribution'})
        for j,col in enumerate(FEATURES):
            locals_.append({'station':station,'horizon':horizon,'issue_ist':s.issue_ist.iloc[0].isoformat(),
                            'feature':col,'feature_value':X.iloc[0,j],
                            'SHAP_contribution_ugm3':float(values[0,j]),
                            'interpretation':'prediction decomposition only'})
    if not data:raise RuntimeError('No valid trained model and held-out features')
    pd.DataFrame(data).to_csv(OUT/'shap_global_importance.csv',index=False)
    pd.DataFrame(locals_).to_csv(OUT/'shap_local_example.csv',index=False)
    print('Saved SHAP outputs; physical source attribution NOT established.')

if __name__=='__main__':main()
