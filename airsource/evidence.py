"""AirSource X hypothesis screening. Evidence != emissions causality.

Only rule-policy reliability can be tested without independent source-apportionment labels.
Never display a physical source fraction or calibrated probability from this engine.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

@dataclass
class EvidenceInput:
    # Each unavailable input MUST be None rather than False or 0.
    fire_count_upwind: int | None = None
    fires_checked: bool = False  # True only for verified complete-enough observation coverage
    wind_supports_transport: bool | None = None  # verified weather/trajectory indication
    pm25: float | None = None
    pm10: float | None = None
    wind_speed: float | None = None
    humidity: float | None = None
    observed_at: str = 'synthetic-test'
    source_refs: dict = field(default_factory=dict)

@dataclass
class Assessment:
    hypothesis: str
    outcome: str
    support: list
    contradiction: list
    missing: list
    alternative_explanations: list
    rule_ids: list
    dependency_families: list
    source_refs: dict
    warnings: list

    def export(self):return asdict(self)


def biomass(x:EvidenceInput):
    s=[];c=[];m=[];r=[];families=[];warnings=[]
    if not x.fires_checked:
        m.append('Verified thermal-anomaly coverage unavailable');r.append('B-MISSING-FIRMS')
    elif x.fire_count_upwind is None:
        m.append('No valid fire-count measurement despite coverage flag');r.append('B-FIRMS-INCONSISTENT')
    elif x.fire_count_upwind>0:
        s.append(f'{x.fire_count_upwind} quality-screened upwind thermal anomalies');r.append('B-FIRE-DETECTIONS');families.append('VIIRS_fire')
    else:
        c.append('No thermal anomalies within the configured observed corridor; detection limits still apply');r.append('B-VERIFIED-NO-DETECTION')
    if x.wind_supports_transport is None:
        m.append('Wind/transport alignment unavailable');r.append('B-MISSING-TRANSPORT')
    elif x.wind_supports_transport:
        s.append('Observed transport direction compatible with possible influence');r.append('B-WIND-COMPATIBLE');families.append('transport')
    else:
        c.append('Available wind/transport alignment is inconsistent');r.append('B-WIND-INCOMPATIBLE')
    # Prevent two related support observations alone from mimicking independent families.
    if x.fires_checked and x.fire_count_upwind is not None and x.fire_count_upwind>0 and x.wind_supports_transport is True:
        outcome='supporting evidence present'
    elif m:
        outcome='insufficient evidence'
    elif c and s:
        outcome='mixed/contradictory'
    else:
        outcome='limited evidence'
    warnings.append('Thermal anomaly and transport consistency are not chemical source apportionment.')
    return Assessment('biomass_burning',outcome,s,c,m,
                      ['Industrial/other combustion', 'Secondary aerosol formation'],r,sorted(set(families)),x.source_refs,warnings)


def dust(x:EvidenceInput):
    s=[];c=[];m=[];r=[];families=[];warnings=[]
    if x.pm25 is None or x.pm10 is None or x.pm25<=0 or x.pm10<x.pm25:
        m.append('Synchronized valid PM2.5 and PM10 required; PM10 must be >= PM2.5');r.append('D-MISSING-COARSE')
        coarse=None
    else:
        coarse=(x.pm10-x.pm25)/x.pm10 if x.pm10>0 else None
        if coarse is not None and coarse>=.40:
            s.append(f'High measured coarse-particle proxy: {coarse:.2f}');r.append('D-COARSE-HIGH');families.append('particulates')
        else:
            c.append(f'Coarse-particle proxy not elevated: {coarse:.2f}');r.append('D-COARSE-LOW')
    if x.wind_speed is None:
        m.append('Wind-speed measurement unavailable');r.append('D-MISSING-WIND')
    elif x.wind_speed>=3.0:
        s.append(f'Wind speed {x.wind_speed:.1f} m/s consistent with resuspension possibility');r.append('D-WIND-HIGH');families.append('meteorology')
    else:
        c.append(f'Wind speed {x.wind_speed:.1f} m/s does not suggest strong resuspension');r.append('D-WIND-LOW')
    if x.humidity is None:
        m.append('Humidity measurement unavailable');r.append('D-MISSING-RH')
    elif x.humidity<40:
        s.append(f'Relatively dry air ({x.humidity:.0f}% RH)');r.append('D-DRY');families.append('meteorology')
    elif x.humidity>75:
        c.append(f'High RH {x.humidity:.0f}% may weaken dry-dust interpretation');r.append('D-HUMID')
    if coarse is None:
        outcome='insufficient evidence'
    elif coarse>=.4 and x.wind_speed is not None and x.wind_speed>=3 and (x.humidity is None or x.humidity<=75):
        outcome='supporting evidence present'
    elif s and c:
        outcome='mixed/contradictory'
    elif not s or len(set(families))<2:
        outcome='limited evidence'
    else:
        outcome='limited evidence'
    warnings.append('Coarse particulate conditions are not uniquely caused by mineral dust.')
    return Assessment('dust_like',outcome,s,c,m,
                      ['Other coarse-particle emissions', 'Sensor/calibration artifacts'],r,sorted(set(families)),x.source_refs,warnings)

ENGINES={'biomass_burning':biomass,'dust_like':dust}

def investigate(x:EvidenceInput):
    return {name:method(x).export() for name,method in ENGINES.items()}


def remove_evidence(x:EvidenceInput, disabled):
    y=deepcopy(x)
    for family in disabled:
        if family=='FIRMS':y.fire_count_upwind=None;y.fires_checked=False
        elif family=='WIND':y.wind_supports_transport=None;y.wind_speed=None
        elif family=='PM10':y.pm10=None
        elif family=='PM25':y.pm25=None
        elif family=='RH':y.humidity=None
        else:raise ValueError(f'Unknown evidence family: {family}')
    before=investigate(x);after=investigate(y)
    diffs={h:{'before':before[h]['outcome'],'after':after[h]['outcome'],
              'assessment_changed':before[h]['outcome']!=after[h]['outcome'],
              'changed_rules':sorted(set(before[h]['rule_ids']) ^ set(after[h]['rule_ids']))}
           for h in before}
    return {'before':before,'after':after,'diffs':diffs,'disabled':list(disabled)}


def naive_baseline(x:EvidenceInput, badge=False):
    """Intentionally simplistic baseline, designed to test consistency rather than physics."""
    label=('biomass_burning' if (x.fire_count_upwind is not None and x.fire_count_upwind>0) else
           'dust_like' if x.pm25 is not None and x.pm10 is not None and x.pm10>0 and (x.pm10-x.pm25)/x.pm10>=.4 else
           'traffic')
    return {'label':label,'abstained':False,'static_low_confidence_badge':bool(badge)}


def policy_fixtures():
    """36 predeclared SYNTHETIC rule-policy cases; not scientific source labels."""
    cases=[]
    situations=[
        ('complete_biomass',dict(fires_checked=True,fire_count_upwind=3,wind_supports_transport=True,pm25=120,pm10=155,wind_speed=1.5,humidity=60)),
        ('contradicted_fire',dict(fires_checked=True,fire_count_upwind=3,wind_supports_transport=False,pm25=100,pm10=130,wind_speed=1.5,humidity=55)),
        ('missing_firms',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=True,pm25=120,pm10=210,wind_speed=4,humidity=35)),
        ('missing_wind',dict(fires_checked=True,fire_count_upwind=6,wind_supports_transport=None,pm25=100,pm10=145,wind_speed=None,humidity=55)),
        ('verified_no_fire',dict(fires_checked=True,fire_count_upwind=0,wind_supports_transport=True,pm25=98,pm10=120,wind_speed=1,humidity=60)),
        ('complete_dust',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=80,pm10=180,wind_speed=5,humidity=22)),
        ('dust_missing_pm10',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=80,pm10=None,wind_speed=5,humidity=22)),
        ('dust_conflict_humid',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=80,pm10=180,wind_speed=5,humidity=90)),
        ('dust_missing_wind',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=80,pm10=180,wind_speed=None,humidity=25)),
        ('no_discriminating_evidence',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=45,pm10=75,wind_speed=1.1,humidity=60)),
        ('correlated_two_meteorology',dict(fires_checked=False,fire_count_upwind=None,wind_supports_transport=None,pm25=40,pm10=60,wind_speed=5,humidity=22)),
        ('fire_and_dust',dict(fires_checked=True,fire_count_upwind=2,wind_supports_transport=True,pm25=85,pm10=200,wind_speed=6,humidity=32))]
    # Reference policy outcomes are declared here, independently of investigate().
    # These are expert-designed logic expectations, NOT atmospheric causal ground truth.
    policy={
        'complete_biomass':('supporting evidence present','limited evidence'),
        'contradicted_fire':('mixed/contradictory','limited evidence'),
        'missing_firms':('insufficient evidence','supporting evidence present'),
        'missing_wind':('insufficient evidence','limited evidence'),
        'verified_no_fire':('limited evidence','limited evidence'),
        'complete_dust':('insufficient evidence','supporting evidence present'),
        'dust_missing_pm10':('insufficient evidence','insufficient evidence'),
        'dust_conflict_humid':('insufficient evidence','mixed/contradictory'),
        'dust_missing_wind':('insufficient evidence','limited evidence'),
        'no_discriminating_evidence':('insufficient evidence','limited evidence'),
        'correlated_two_meteorology':('insufficient evidence','mixed/contradictory'),
        'fire_and_dust':('supporting evidence present','supporting evidence present')}
    for replicate in range(3):
        for key,data in situations:
            perturbed=dict(data)
            for v in ['pm25','pm10']:
                if perturbed[v] is not None:perturbed[v]=perturbed[v]*(1+replicate*.025)
            if perturbed['wind_speed'] is not None:perturbed['wind_speed']+=replicate*.10
            if perturbed['humidity'] is not None:perturbed['humidity']+=replicate
            c=EvidenceInput(**perturbed,observed_at=f'SYNTHETIC_CASE_{replicate}')
            cases.append({'id':f'SYN-{len(cases)+1:03}', 'scenario':key,
                          'input':c,'synthetic':True,'policy_expected':{
                              'biomass_burning':policy[key][0], 'dust_like':policy[key][1]}})
    return cases


def run_policy_experiment(outdir):
    """B0 naive vs B1 badge vs X engine. All expected outcomes are *policy* only."""
    output=Path(outdir);output.mkdir(parents=True,exist_ok=True)
    cases=policy_fixtures();rows=[];detail=[]
    for c in cases:
        x=c['input'];ass=investigate(x);n0=naive_baseline(x);n1=naive_baseline(x,True)
        # Reference policy: insufficient if required independent observations unavailable.
        # This is implementation consistency, NOT atmospheric source identity.
        expected_insuff={key:value=='insufficient evidence' for key,value in c['policy_expected'].items()}
        for method in ['B0-naive','B1-badge','X-evidence']:
            for h in ['biomass_burning','dust_like']:
                if method=='X-evidence':
                    abstained=ass[h]['outcome']=='insufficient evidence'; label=ass[h]['outcome'];
                    provenance=bool(ass[h]['rule_ids']); contradiction_shown=bool(ass[h]['contradiction'])
                else:
                    label=n0['label'];abstained=False;provenance=False;contradiction_shown=False
                rows.append({'case_id':c['id'],'scenario':c['scenario'],'synthetic':True,
                             'method':method,'hypothesis':h,'label':label,'abstained':abstained,
                             'policy_insufficient':expected_insuff[h],
                             'expected_policy_outcome':c['policy_expected'][h],
                             'exact_policy_match':(ass[h]['outcome']==c['policy_expected'][h]) if method=='X-evidence' else False,
                             'unsupported_conclusion':expected_insuff[h] and not abstained,
                             'supported_decision_retained':(not expected_insuff[h]) and not abstained,
                             'provenance_shown':provenance,'contradiction_shown':contradiction_shown,
                             'contradiction_present':bool(ass[h]['contradiction'])})
        detail.append({'case_id':c['id'],'scenario':c['scenario'],'X':ass,'B0':n0,'B1':n1,'predeclared_expected':c['policy_expected']})
    table=__import__('pandas').DataFrame(rows)
    summary=[]
    for name, d in table.groupby('method'):
        insuff=d.loc[d.policy_insufficient];suff=d.loc[~d.policy_insufficient]
        contrad=d.loc[d.contradiction_present]
        summary.append({'experiment':'SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION',
                        'method':name,'cases':len(cases),'hypothesis_assessments':len(d),
                        'policy_insufficient_count':len(insuff),
                        'unsupported_conclusion_rate':round(float(insuff.unsupported_conclusion.mean()),4) if len(insuff) else None,
                        'appropriate_abstention_rate':round(float(insuff.abstained.mean()),4) if len(insuff) else None,
                        'supported_decision_retention':round(float(suff.supported_decision_retained.mean()),4) if len(suff) else None,
                        'provenance_trace_rate':round(float(d.provenance_shown.mean()),4),
                        'contradiction_visibility_rate':round(float(contrad.contradiction_shown.mean()),4) if len(contrad) else None,
                        'exact_policy_outcome_match':round(float(d.exact_policy_match.mean()),4) if name=='X-evidence' else None})
    sm=__import__('pandas').DataFrame(summary)
    table.to_csv(output/'policy_case_results.csv',index=False)
    sm.to_csv(output/'policy_comparison.csv',index=False)
    (output/'policy_case_trace.json').write_text(json.dumps(detail,indent=2))
    return sm,table


def next_best_measurement(x:EvidenceInput):
    """Explainable, heuristic next-measurement priorities (not expected information gain)."""
    steps=[]
    if not x.fires_checked or x.fire_count_upwind is None:
        steps.append({'for_hypothesis':'biomass_burning','priority':1,'suggestion':'Verify satellite thermal-anomaly coverage for the exact historical window',
                      'reason':'Fire observations are missing; unknown is not zero detections.',
                      'limits':'Overpass/cloud/size gaps still prevent complete fire exclusion.'})
    if x.wind_supports_transport is None:
        steps.append({'for_hypothesis':'biomass_burning','priority':2,'suggestion':'Obtain time-aligned meteorological transport context',
                      'reason':'Missing wind/transport compatibility limits assessment of possible regional influence.',
                      'limits':'A wind arrow or back-trajectory cannot establish a causal source share.'})
    if x.pm10 is None or x.pm25 is None or x.pm25<=0 or (x.pm10 is not None and x.pm10<x.pm25):
        steps.append({'for_hypothesis':'dust_like','priority':1,'suggestion':'Collect synchronized, quality-screened PM2.5 and PM10 measurements',
                      'reason':'Paired particulate observations are required for the coarse-fraction screening indicator.',
                      'limits':'Coarse particles may originate from non-dust sources.'})
    elif x.wind_speed is None:
        steps.append({'for_hypothesis':'dust_like','priority':2,'suggestion':'Collect quality-screened wind speed for the same event window',
                      'reason':'Wind context is missing; resuspension remains uncertain.',
                      'limits':'Weather compatibility alone does not prove dust emission.'})
    elif x.humidity is None:
        steps.append({'for_hypothesis':'dust_like','priority':3,'suggestion':'Collect humidity observations aligned with particulate readings',
                      'reason':'Dryness information is unavailable.',
                      'limits':'Dry air is not unique evidence of dust.'})
    if not steps:
        steps.append({'for_hypothesis':'both','priority':4,
                      'suggestion':'Consult independent source-apportionment or expert field measurements',
                      'reason':'Simple screening inputs are present but not causal or source-specific.',
                      'limits':'Additional measurement may still not establish attribution.'})
    return sorted(steps,key=lambda z:(z['priority'],z['for_hypothesis']))
