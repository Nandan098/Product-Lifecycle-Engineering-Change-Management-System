from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.config import project_path
from services.change_service import approve_ecr, create_ecr, implement_eco, start_review
from services.impact_service import analyze_change_impact
from services.integration_service import import_external_ebom, list_integration_jobs, sync_ebom_to_mbom
from services.product_service import get_ebom, get_mbom, get_product, list_documents


def test_seed_has_products_and_matching_baseline_structures():
    assert get_product("GEAR-ASSY-100")["current_revision"] == "A"
    assert len(get_ebom("GEAR-ASSY-100", "A")) == 6
    assert len(get_mbom("GEAR-ASSY-100", "A")) == 6


def test_impact_analysis_identifies_orders_and_documents():
    impact = analyze_change_impact("GEAR-ASSY-100", "BRG-6205", "BRG-6205-2RS")
    assert impact["affected_product_count"] >= 1
    assert len(impact["open_production_orders"]) == 2
    assert len(impact["documents_requiring_review"]) == 3


def test_internal_ecr_review_approval_implementation_and_mbom_sync():
    ecr = create_ecr(
        product_id="GEAR-ASSY-100", title="Bearing upgrade", description="Use sealed bearing.",
        reason_code="QUALITY_IMPROVEMENT", requested_by="Design Engineering",
        changed_component_id="BRG-6205", new_component_id="BRG-6205-2RS",
        new_quantity=2, effective_date="2026-12-01",
    )
    start_review(ecr, "Engineering Lead")
    eco = approve_ecr(ecr, "Change Board")
    new_revision = implement_eco(eco, "PLM Admin")
    assert new_revision == "B"
    assert get_product("GEAR-ASSY-100")["current_revision"] == "B"
    revised = get_ebom("GEAR-ASSY-100", "B")
    assert any(row["component_id"] == "BRG-6205-2RS" for row in revised)
    assert all(doc["status"] == "REVIEW_REQUIRED" for doc in list_documents("GEAR-ASSY-100"))
    result = sync_ebom_to_mbom("GEAR-ASSY-100", "B", "Test Suite")
    assert result["status"] == "COMPLETED"
    mbom = get_mbom("GEAR-ASSY-100", "B")
    assert any(row["component_id"] == "BRG-6205-2RS" and row["operation_no"] == 50 for row in mbom)


def test_external_approved_ebom_import_and_sync():
    payload = json.loads(project_path("data", "external_ebom_revision_B.json").read_text(encoding="utf-8"))
    result = import_external_ebom(payload)
    assert result["status"] == "COMPLETED"
    assert result["record_count"] == 6
    assert get_product("GEAR-ASSY-100")["current_revision"] == "B"
    synced = sync_ebom_to_mbom("GEAR-ASSY-100", "B")
    assert synced["record_count"] == 6
    assert any(row["component_id"] == "BRG-6205-2RS" for row in get_mbom("GEAR-ASSY-100", "B"))
    assert any(job["payload_type"] == "EBOM_IMPORT" and job["status"] == "COMPLETED" for job in list_integration_jobs())


def test_external_import_rejects_unapproved_payload():
    payload = json.loads(project_path("data", "external_ebom_revision_B.json").read_text(encoding="utf-8"))
    payload["approval_status"] = "DRAFT"
    with pytest.raises(ValueError, match="approval_status"):
        import_external_ebom(payload)
    assert any(job["status"] == "FAILED" for job in list_integration_jobs())


def test_external_import_rejects_unknown_material():
    payload = json.loads(project_path("data", "external_ebom_revision_B.json").read_text(encoding="utf-8"))
    payload["components"][0]["component_id"] = "UNKNOWN-PART"
    with pytest.raises(ValueError, match="Unknown component"):
        import_external_ebom(payload)


def test_eco_cannot_be_implemented_before_approval():
    ecr = create_ecr(
        product_id="GEAR-ASSY-100", title="Quantity change", description="Adjust quantity.",
        reason_code="DESIGN_UPDATE", requested_by="Engineer", changed_component_id="BRG-6205",
        new_component_id="BRG-6205", new_quantity=3, effective_date="2026-12-05",
    )
    with pytest.raises(ValueError, match="Unknown ECO"):
        implement_eco("ECO-NOT-FOUND")
    assert get_product("GEAR-ASSY-100")["current_revision"] == "A"
