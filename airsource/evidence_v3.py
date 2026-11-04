"""Structured, traceable evidence records for AirSource-X V3."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Iterable
import uuid

VALID_ASSESSMENTS = {"Pattern present", "Mixed evidence", "No strong pattern", "Insufficient evidence", "Insufficient spatial coverage", "Not assessed"}


def make_evidence_item(*, family: str, indicator: str, value: Any, unit: str | None,
                       observed_at: str | None, available_at: str | None,
                       source: str, source_record_id: str | None = None,
                       qc_status: str = "unknown", reliability_note: str = "",
                       dependency_group: str | None = None,
                       spatial_scope: str | None = None) -> dict[str, Any]:
    """Create a serialisable evidence record; timestamps are retained as supplied."""
    if not family.strip() or not indicator.strip() or not source.strip():
        raise ValueError("family, indicator and source are required")
    return {
        "evidence_id": str(uuid.uuid4()), "family": family, "indicator": indicator,
        "value": value, "unit": unit, "observed_at": observed_at,
        "available_at": available_at, "source": source,
        "source_record_id": source_record_id, "qc_status": qc_status,
        "reliability_note": reliability_note,
        "dependency_group": dependency_group or family,
        "spatial_scope": spatial_scope,
    }


def make_assessment(*, hypothesis: str, status: str,
                    supporting_ids: Iterable[str] = (),
                    contradiction_ids: Iterable[str] = (),
                    missing_evidence: Iterable[str] = (),
                    quality_concerns: Iterable[str] = (),
                    alternative_explanations: Iterable[str] = (),
                    rule_version: str, engine_version: str,
                    mode: str = "retrospective") -> dict[str, Any]:
    """Create an assessment with explicit evidence dependencies and audit metadata."""
    if status not in VALID_ASSESSMENTS:
        raise ValueError(f"Unsupported assessment status: {status}")
    support, contradiction = list(supporting_ids), list(contradiction_ids)
    overlap = set(support) & set(contradiction)
    if overlap:
        raise ValueError("An evidence item cannot be both supporting and contradictory in one assessment")
    return {
        "assessment_id": str(uuid.uuid4()), "hypothesis": hypothesis, "status": status,
        "supporting_evidence_ids": support, "contradiction_evidence_ids": contradiction,
        "missing_evidence": list(missing_evidence), "quality_concerns": list(quality_concerns),
        "alternative_explanations": list(alternative_explanations),
        "rule_version": rule_version, "engine_version": engine_version, "mode": mode,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def validate_assessment(assessment: dict[str, Any], evidence_items: Iterable[dict[str, Any]]) -> list[str]:
    """Return traceability errors; an empty list means all referenced IDs resolve."""
    known = {item.get("evidence_id") for item in evidence_items}
    errors = []
    for key in ("supporting_evidence_ids", "contradiction_evidence_ids"):
        for evidence_id in assessment.get(key, []):
            if evidence_id not in known:
                errors.append(f"{key} references unknown evidence ID: {evidence_id}")
    return errors



def claims_to_evidence(claims: Iterable[dict[str, Any]], *, source: str,
                       observed_at: str | None, available_at: str | None,
                       rule_version: str = "legacy-screen-v1",
                       engine_version: str = "evidence-v3") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Wrap existing screening claim text as traceable records without inventing measurements.

    Values are qualitative text from the legacy rule output, not raw sensor readings.
    """
    items, assessments = [], []
    for claim in claims:
        family = str(claim.get("family") or "legacy-screen")
        support_ids, contradiction_ids = [], []
        for kind, statements, target in (
            ("support", claim.get("supports", []), support_ids),
            ("contradiction", claim.get("contradicts", []), contradiction_ids),
        ):
            for statement in statements:
                item = make_evidence_item(family=family, indicator=f"{kind}_statement",
                    value=str(statement), unit=None, observed_at=observed_at,
                    available_at=available_at, source=source, qc_status="qualitative_rule_output",
                    reliability_note="Derived from a legacy heuristic statement; not a raw measurement.",
                    dependency_group=family)
                items.append(item); target.append(item["evidence_id"])
        assessment = make_assessment(hypothesis=str(claim.get("hypothesis", "Unspecified hypothesis")),
            status=claim.get("status", "Not assessed"), supporting_ids=support_ids,
            contradiction_ids=contradiction_ids, missing_evidence=[str(claim.get("reason", ""))] if claim.get("reason") else [],
            rule_version=rule_version, engine_version=engine_version, mode="retrospective")
        assessments.append(assessment)
    return items, assessments
