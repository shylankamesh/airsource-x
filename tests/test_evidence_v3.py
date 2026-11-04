import pytest
from airsource.evidence_v3 import make_assessment, make_evidence_item, validate_assessment


def test_assessment_has_resolvable_evidence_trace():
    item = make_evidence_item(family="meteorology", indicator="wind_speed", value=12,
        unit="km/h", observed_at="2024-01-01T00:00:00Z", available_at="2024-01-01T00:05:00Z",
        source="test-provider", dependency_group="weather-run-1")
    assessment = make_assessment(hypothesis="test hypothesis", status="Mixed evidence",
        supporting_ids=[item["evidence_id"]], contradiction_ids=[], rule_version="1.0", engine_version="1.0")
    assert validate_assessment(assessment, [item]) == []
    assert assessment["supporting_evidence_ids"] == [item["evidence_id"]]


def test_assessment_rejects_same_item_as_support_and_contradiction():
    with pytest.raises(ValueError):
        make_assessment(hypothesis="x", status="Mixed evidence", supporting_ids=["id"],
                        contradiction_ids=["id"], rule_version="1", engine_version="1")



def test_legacy_claim_adapter_preserves_qualitative_only_trace():
    from airsource.evidence_v3 import claims_to_evidence, validate_assessment
    claims = [{"hypothesis":"dust-like", "status":"Mixed evidence", "family":"wind",
               "supports":["wind elevated"], "contradicts":["PM10 not elevated"]}]
    items, assessments = claims_to_evidence(claims, source="legacy-rule",
        observed_at="2024-01-01T00:00:00Z", available_at="2024-01-01T00:05:00Z")
    assert len(items) == 2
    assert validate_assessment(assessments[0], items) == []
    assert all(i["unit"] is None for i in items)
