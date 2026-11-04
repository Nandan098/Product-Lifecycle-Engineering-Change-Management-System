from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from core.database import db_session


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"


def create_ecr(*, product_id: str, title: str, description: str, reason_code: str,
               requested_by: str, changed_component_id: str, new_component_id: str | None,
               new_quantity: float, effective_date: str, source_system: str = "Internal PLM Demo") -> str:
    if not title.strip() or not description.strip() or not requested_by.strip():
        raise ValueError("Title, description, and requester are required.")
    if new_quantity <= 0:
        raise ValueError("New quantity must be greater than zero.")
    with db_session() as conn:
        product = conn.execute("SELECT current_revision FROM products WHERE product_id=?", (product_id,)).fetchone()
        if not product:
            raise ValueError(f"Unknown product: {product_id}")
        old = conn.execute("""SELECT quantity FROM engineering_bom
            WHERE product_id=? AND revision=? AND component_id=? LIMIT 1""",
            (product_id, product["current_revision"], changed_component_id)).fetchone()
        if not old:
            raise ValueError(f"Component {changed_component_id} is not in the current EBOM for {product_id}.")
        material = conn.execute("SELECT material_id FROM materials WHERE material_id=?", (changed_component_id,)).fetchone()
        if not material:
            raise ValueError(f"Unknown current material: {changed_component_id}")
        if new_component_id:
            replacement = conn.execute("SELECT material_id FROM materials WHERE material_id=?", (new_component_id,)).fetchone()
            if not replacement:
                raise ValueError(f"Unknown replacement material: {new_component_id}")
        ecr_id = _id("ECR")
        conn.execute("""INSERT INTO engineering_changes
            (ecr_id, product_id, title, description, reason_code, requested_by, changed_component_id,
             new_component_id, old_quantity, new_quantity, status, source_system, created_at, effective_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SUBMITTED', ?, ?, ?)""",
            (ecr_id, product_id, title.strip(), description.strip(), reason_code, requested_by.strip(),
             changed_component_id, new_component_id or changed_component_id, float(old["quantity"]),
             float(new_quantity), source_system, now_iso(), effective_date))
        return ecr_id


def list_ecrs() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("""SELECT e.*, p.product_name FROM engineering_changes e
            JOIN products p ON p.product_id=e.product_id ORDER BY e.created_at DESC""").fetchall()
        return [dict(r) for r in rows]


def get_ecr(ecr_id: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM engineering_changes WHERE ecr_id=?", (ecr_id,)).fetchone()
        return dict(row) if row else None


def start_review(ecr_id: str, reviewer: str) -> None:
    with db_session() as conn:
        row = conn.execute("SELECT status FROM engineering_changes WHERE ecr_id=?", (ecr_id,)).fetchone()
        if not row:
            raise ValueError(f"Unknown ECR: {ecr_id}")
        if row["status"] != "SUBMITTED":
            raise ValueError("Only submitted ECRs can enter review.")
        conn.execute("UPDATE engineering_changes SET status='UNDER_REVIEW', reviewed_by=?, reviewed_at=? WHERE ecr_id=?",
                     (reviewer, now_iso(), ecr_id))


def approve_ecr(ecr_id: str, approver: str, effective_date: str | None = None) -> str:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM engineering_changes WHERE ecr_id=?", (ecr_id,)).fetchone()
        if not row:
            raise ValueError(f"Unknown ECR: {ecr_id}")
        if row["status"] != "UNDER_REVIEW":
            raise ValueError("ECR must be under review before it can be approved.")
        eco_id = _id("ECO")
        eff_date = effective_date or row["effective_date"] or date.today().isoformat()
        conn.execute("""INSERT INTO change_orders
            (eco_id, ecr_id, status, approved_by, approved_at, effective_date, implementation_notes)
            VALUES (?, ?, 'APPROVED', ?, ?, ?, ?)""",
            (eco_id, ecr_id, approver, now_iso(), eff_date, "Approved; pending implementation and manufacturing synchronization."))
        conn.execute("UPDATE engineering_changes SET status='APPROVED', reviewed_by=?, reviewed_at=? WHERE ecr_id=?",
                     (approver, now_iso(), ecr_id))
        return eco_id


def reject_ecr(ecr_id: str, reviewer: str, reason: str) -> None:
    with db_session() as conn:
        row = conn.execute("SELECT status FROM engineering_changes WHERE ecr_id=?", (ecr_id,)).fetchone()
        if not row:
            raise ValueError(f"Unknown ECR: {ecr_id}")
        if row["status"] not in ("SUBMITTED", "UNDER_REVIEW"):
            raise ValueError("Only submitted or under-review ECRs can be rejected.")
        conn.execute("UPDATE engineering_changes SET status='REJECTED', reviewed_by=?, reviewed_at=?, description=description || ? WHERE ecr_id=?",
                     (reviewer, now_iso(), f"\nRejection note: {reason}", ecr_id))


def _next_revision(current: str) -> str:
    if len(current) == 1 and current.isalpha():
        return chr(ord(current.upper()) + 1) if current.upper() < "Z" else "AA"
    return f"{current}-NEXT"


def implement_eco(eco_id: str, implemented_by: str = "Manufacturing Engineering") -> str:
    """Create the next EBOM revision and mark affected controlled documents for review."""
    with db_session() as conn:
        eco = conn.execute("""SELECT c.*, e.* FROM change_orders c
            JOIN engineering_changes e ON e.ecr_id=c.ecr_id WHERE c.eco_id=?""", (eco_id,)).fetchone()
        if not eco:
            raise ValueError(f"Unknown ECO: {eco_id}")
        if eco["status"] != "APPROVED":
            raise ValueError("Only approved ECOs can be implemented.")
        product = conn.execute("SELECT current_revision FROM products WHERE product_id=?", (eco["product_id"],)).fetchone()
        current_rev = product["current_revision"]
        next_rev = _next_revision(current_rev)
        rows = conn.execute("SELECT * FROM engineering_bom WHERE product_id=? AND revision=? ORDER BY find_number",
                            (eco["product_id"], current_rev)).fetchall()
        if not rows:
            raise ValueError("Current EBOM is empty; implementation stopped.")
        target_found = False
        for row in rows:
            component_id = row["component_id"]
            quantity = float(row["quantity"])
            if component_id == eco["changed_component_id"]:
                target_found = True
                component_id = eco["new_component_id"] or component_id
                quantity = float(eco["new_quantity"])
            conn.execute("""INSERT INTO engineering_bom
                (product_id, revision, component_id, quantity, uom, find_number, reference_designator,
                 effectivity_start, effectivity_end, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (eco["product_id"], next_rev, component_id, quantity, row["uom"], row["find_number"],
                 row["reference_designator"], eco["effective_date"], None, now_iso()))
        if not target_found:
            raise ValueError("Changed component was not found in the current EBOM; no revision was created.")

        # Product documents remain on their old revision and are visibly flagged for review.
        conn.execute("UPDATE documents SET status='REVIEW_REQUIRED' WHERE product_id=? AND revision=?",
                     (eco["product_id"], current_rev))
        conn.execute("UPDATE products SET current_revision=? WHERE product_id=?", (next_rev, eco["product_id"]))
        conn.execute("""INSERT INTO product_revisions
            (product_id, revision, change_reference, change_summary, status, created_by, created_at)
            VALUES (?, ?, ?, ?, 'IN_REVIEW', ?, ?)""",
            (eco["product_id"], next_rev, eco_id,
             f"{eco['changed_component_id']} -> {eco['new_component_id']}; quantity {eco['old_quantity']} -> {eco['new_quantity']}",
             implemented_by, now_iso()))
        conn.execute("UPDATE change_orders SET status='IMPLEMENTED', implemented_at=?, implementation_notes=? WHERE eco_id=?",
                     (now_iso(), f"EBOM revision {next_rev} created. MBOM synchronization remains a separate step.", eco_id))
        conn.execute("UPDATE engineering_changes SET status='IMPLEMENTED' WHERE ecr_id=?", (eco["ecr_id"],))
        conn.execute("UPDATE product_revisions SET status='RELEASED' WHERE product_id=? AND revision=?",
                     (eco["product_id"], current_rev))
        return next_rev
