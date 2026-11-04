from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from core.database import db_session


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _job_id() -> str:
    return f"INT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def list_integration_jobs(limit: int = 100) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM integration_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def _insert_job(conn, *, job_id: str, source: str, target: str, payload_type: str,
                status: str, count: int, message: str, payload: Any) -> None:
    conn.execute("""INSERT INTO integration_jobs
        (job_id, source_system, target_system, payload_type, status, record_count, message, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_id, source, target, payload_type, status, count, message,
         json.dumps(payload, ensure_ascii=False), now_iso()))


def import_external_ebom(payload: dict) -> dict:
    """Import an approved engineering BOM payload from a simulated external PLM system."""
    job_id = _job_id()
    source = str(payload.get("source_system") or "External PLM")
    product = payload.get("product") or {}
    product_id = str(product.get("product_id") or "")
    revision = str(product.get("revision") or "").strip()
    components = payload.get("components") or []
    approval_status = str(payload.get("approval_status") or "").upper()
    try:
        if not product_id or not revision:
            raise ValueError("product.product_id and product.revision are required.")
        if approval_status != "APPROVED":
            raise ValueError("External EBOM must have approval_status='APPROVED' before import.")
        if not isinstance(components, list) or not components:
            raise ValueError("components must be a non-empty array.")
        seen_find_numbers: set[str] = set()
        with db_session() as conn:
            prod = conn.execute("SELECT * FROM products WHERE product_id=?", (product_id,)).fetchone()
            if not prod:
                raise ValueError(f"Unknown product_id: {product_id}")
            exists = conn.execute("SELECT 1 FROM engineering_bom WHERE product_id=? AND revision=? LIMIT 1",
                                  (product_id, revision)).fetchone()
            if exists:
                raise ValueError(f"EBOM revision {revision} already exists for {product_id}.")
            normalized = []
            for idx, item in enumerate(components, start=1):
                component_id = str(item.get("component_id") or "").strip()
                find_number = str(item.get("find_number") or f"{idx:04d}").strip()
                quantity = float(item.get("quantity", 0))
                if not component_id:
                    raise ValueError(f"Component row {idx} is missing component_id.")
                if quantity <= 0:
                    raise ValueError(f"Component {component_id} quantity must be greater than zero.")
                if find_number in seen_find_numbers:
                    raise ValueError(f"Duplicate find_number: {find_number}")
                seen_find_numbers.add(find_number)
                material = conn.execute("SELECT base_uom FROM materials WHERE material_id=?", (component_id,)).fetchone()
                if not material:
                    raise ValueError(f"Unknown component material: {component_id}")
                normalized.append((component_id, quantity, str(item.get("uom") or material["base_uom"]),
                                   find_number, str(item.get("reference_designator") or "")))
            for component_id, quantity, uom, find_number, ref in normalized:
                conn.execute("""INSERT INTO engineering_bom
                    (product_id, revision, component_id, quantity, uom, find_number, reference_designator, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (product_id, revision, component_id, quantity, uom, find_number, ref, now_iso()))
            previous_revision = prod["current_revision"]
            conn.execute("UPDATE documents SET status='REVIEW_REQUIRED' WHERE product_id=? AND revision=?",
                         (product_id, previous_revision))
            conn.execute("UPDATE product_revisions SET status='RELEASED' WHERE product_id=? AND revision=?",
                         (product_id, previous_revision))
            conn.execute("UPDATE products SET current_revision=? WHERE product_id=?", (revision, product_id))
            conn.execute("""INSERT INTO product_revisions
                (product_id, revision, change_reference, change_summary, status, created_by, created_at)
                VALUES (?, ?, ?, ?, 'RELEASED', ?, ?)""",
                (product_id, revision, payload.get("change_reference"),
                 payload.get("change_summary") or f"Imported approved EBOM revision {revision} from {source}",
                 source, now_iso()))
            _insert_job(conn, job_id=job_id, source=source, target="Manufacturing PLM Demo",
                        payload_type="EBOM_IMPORT", status="COMPLETED", count=len(normalized),
                        message=f"Imported {len(normalized)} EBOM component rows for {product_id} revision {revision}.",
                        payload=payload)
        return {"job_id": job_id, "status": "COMPLETED", "product_id": product_id,
                "revision": revision, "record_count": len(normalized)}
    except Exception as exc:
        # A failed job is still auditable.
        with db_session() as conn:
            _insert_job(conn, job_id=job_id, source=source, target="Manufacturing PLM Demo",
                        payload_type="EBOM_IMPORT", status="FAILED", count=0,
                        message=str(exc), payload=payload)
        raise


def sync_ebom_to_mbom(product_id: str, revision: str, triggered_by: str = "PLM Integration Demo") -> dict:
    """Transform an approved/current EBOM revision into a manufacturing BOM using component mappings."""
    job_id = _job_id()
    source = "PLM Engineering Data"
    try:
        with db_session() as conn:
            product = conn.execute("SELECT * FROM products WHERE product_id=?", (product_id,)).fetchone()
            if not product:
                raise ValueError(f"Unknown product: {product_id}")
            if product["current_revision"] != revision:
                raise ValueError(f"Revision {revision} is not the current released product revision ({product['current_revision']}).")
            rows = conn.execute("SELECT * FROM engineering_bom WHERE product_id=? AND revision=? ORDER BY find_number",
                                (product_id, revision)).fetchall()
            if not rows:
                raise ValueError("No EBOM rows found for the requested product revision.")
            mappings = {}
            missing = []
            for row in rows:
                mapping = conn.execute("SELECT * FROM component_operation_map WHERE component_id=?",
                                       (row["component_id"],)).fetchone()
                if not mapping:
                    missing.append(row["component_id"])
                else:
                    mappings[row["component_id"]] = dict(mapping)
            if missing:
                raise ValueError("Missing manufacturing operation mapping for: " + ", ".join(sorted(set(missing))))
            conn.execute("UPDATE manufacturing_bom SET status='SUPERSEDED' WHERE product_id=? AND revision<>? AND status='ACTIVE'",
                         (product_id, revision))
            conn.execute("DELETE FROM manufacturing_bom WHERE product_id=? AND revision=?", (product_id, revision))
            for row in rows:
                mapping = mappings[row["component_id"]]
                conn.execute("""INSERT INTO manufacturing_bom
                    (product_id, revision, source_ebom_revision, component_id, quantity, uom, find_number,
                     operation_no, operation_name, staging_area, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)""",
                    (product_id, revision, revision, row["component_id"], row["quantity"], row["uom"],
                     row["find_number"], mapping["operation_no"], mapping["operation_name"],
                     mapping["staging_area"], now_iso()))
            conn.execute("UPDATE product_revisions SET status='RELEASED' WHERE product_id=? AND revision=?",
                         (product_id, revision))
            _insert_job(conn, job_id=job_id, source=source, target="Manufacturing Execution System",
                        payload_type="EBOM_TO_MBOM_SYNC", status="COMPLETED", count=len(rows),
                        message=f"{len(rows)} EBOM rows transformed to MBOM by {triggered_by}.",
                        payload={"product_id": product_id, "revision": revision, "rows": [dict(r) for r in rows]})
        return {"job_id": job_id, "status": "COMPLETED", "product_id": product_id,
                "revision": revision, "record_count": len(rows)}
    except Exception as exc:
        with db_session() as conn:
            _insert_job(conn, job_id=job_id, source=source, target="Manufacturing Execution System",
                        payload_type="EBOM_TO_MBOM_SYNC", status="FAILED", count=0,
                        message=str(exc), payload={"product_id": product_id, "revision": revision})
        raise


def import_external_ecr(payload: dict) -> dict:
    """Create an internal ECR from a partner-system change request payload."""
    from services.change_service import create_ecr

    source = str(payload.get("source_system") or "External PLM")
    ecr_id = create_ecr(
        product_id=str(payload.get("product_id") or ""),
        title=str(payload.get("title") or "External engineering change"),
        description=str(payload.get("description") or "Imported from external PLM system."),
        reason_code=str(payload.get("reason_code") or "DESIGN_UPDATE"),
        requested_by=str(payload.get("requested_by") or source),
        changed_component_id=str(payload.get("changed_component_id") or ""),
        new_component_id=payload.get("new_component_id"),
        new_quantity=float(payload.get("new_quantity", 0)),
        effective_date=str(payload.get("effective_date") or ""),
        source_system=source,
    )
    job_id = _job_id()
    with db_session() as conn:
        _insert_job(conn, job_id=job_id, source=source, target="Manufacturing PLM Demo",
                    payload_type="ECR_IMPORT", status="COMPLETED", count=1,
                    message=f"Imported external change request as {ecr_id}.", payload=payload)
    return {"job_id": job_id, "status": "COMPLETED", "ecr_id": ecr_id, "record_count": 1}
