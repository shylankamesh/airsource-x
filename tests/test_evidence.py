import pytest
from airsource.evidence import EvidenceInput,biomass,dust,investigate,remove_evidence,policy_fixtures,run_policy_experiment

def test_missing_fire_is_not_zero_fire():
    a=biomass(EvidenceInput(fires_checked=False,fire_count_upwind=None,wind_supports_transport=True))
    assert a.outcome=='insufficient evidence'
    assert any('unavailable' in x.lower() for x in a.missing)

def test_wind_contradiction_visible():
    x=EvidenceInput(fires_checked=True,fire_count_upwind=2,wind_supports_transport=False)
    result=biomass(x)
    assert result.outcome=='mixed/contradictory'
    assert result.contradiction

def test_supporting_biomass_is_not_source_fraction():
    x=EvidenceInput(fires_checked=True,fire_count_upwind=3,wind_supports_transport=True)
    result=biomass(x).export()
    assert result['outcome']=='supporting evidence present'
    assert 'percentage' not in str(result).lower()

def test_dust_requires_coarse_particle_data():
    x=EvidenceInput(pm25=80,pm10=None,wind_speed=5,humidity=10)
    assert dust(x).outcome=='insufficient evidence'

def test_dust_independence_two_meteorology_signals_not_enough():
    x=EvidenceInput(pm25=80,pm10=100,wind_speed=6,humidity=15)
    assert dust(x).outcome!='supporting evidence present'

def test_dust_support_from_particulates_and_meteorology():
    x=EvidenceInput(pm25=80,pm10=200,wind_speed=5,humidity=25)
    result=dust(x)
    assert result.outcome=='supporting evidence present'
    assert 'particulates' in result.dependency_families
    assert 'meteorology' in result.dependency_families

def test_fire_toggled_off_recomputes_only_dependent_hypothesis():
    x=EvidenceInput(fires_checked=True,fire_count_upwind=5,wind_supports_transport=True,pm25=80,pm10=200,wind_speed=5,humidity=25)
    r=remove_evidence(x,['FIRMS'])
    assert r['diffs']['biomass_burning']['assessment_changed']
    assert not r['diffs']['dust_like']['assessment_changed']

def test_wind_toggle_degrades_support():
    x=EvidenceInput(fires_checked=True,fire_count_upwind=5,wind_supports_transport=True,pm25=80,pm10=200,wind_speed=5,humidity=25)
    r=remove_evidence(x,['WIND'])
    assert r['after']['biomass_burning']['outcome']=='insufficient evidence'
    assert r['after']['dust_like']['outcome']!='supporting evidence present'

def test_unknown_evidence_family_rejected():
    with pytest.raises(ValueError):remove_evidence(EvidenceInput(),['MADE_UP'])

def test_36_policy_cases():
    f=policy_fixtures()
    assert len(f)==36
    assert all(x['synthetic'] for x in f)

def test_policy_metrics_have_denominators(tmp_path):
    a,b=run_policy_experiment(tmp_path)
    assert len(a)==3
    assert (a.hypothesis_assessments==72).all()
    assert a.set_index('method').loc['X-evidence','appropriate_abstention_rate']==1
    assert a.set_index('method').loc['X-evidence','supported_decision_retention']==1
    assert (tmp_path/'policy_case_results.csv').exists()

def test_measurement_suggestions_respond_to_missing_data():
    from airsource.evidence import next_best_measurement
    x=EvidenceInput(pm25=40,pm10=None,wind_speed=None,fire_count_upwind=None,fires_checked=False)
    s=next_best_measurement(x)
    suggestions=' '.join(row['suggestion'] for row in s)
    assert 'satellite' in suggestions.lower()
    assert 'PM10' in suggestions
    assert all('limits' in row for row in s)
