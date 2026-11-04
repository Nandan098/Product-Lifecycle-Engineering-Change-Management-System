from __future__ import annotations

from core.database import db_session


def analyze_change_impact(product_id: str, component_id: str, new_component_id: str | None = None) -> dict:
    """Identify product structures, documents, and open orders touched by a component change."""
    with db_session() as conn:
        product = conn.execute("SELECT * FROM products WHERE product_id=?", (product_id,)).fetchone()
        if not product:
            raise ValueError(f"Unknown product: {product_id}")
        rev = product["current_revision"]
        ebom_use = conn.execute("""SELECT e.product_id, p.product_name, e.revision, e.find_number, e.quantity
            FROM engineering_bom e JOIN products p ON p.product_id=e.product_id
            WHERE e.component_id=? AND e.revision=(SELECT current_revision FROM products WHERE product_id=e.product_id)
            ORDER BY e.product_id""", (component_id,)).fetchall()
        mbom_use = conn.execute("""SELECT product_id, revision, find_number, operation_no, operation_name
            FROM manufacturing_bom WHERE component_id=? AND status='ACTIVE' ORDER BY product_id""", (component_id,)).fetchall()
        docs = conn.execute("SELECT document_id, title, document_type, revision, status FROM documents WHERE product_id=? ORDER BY document_id",
                            (product_id,)).fetchall()
        orders = conn.execute("""SELECT order_id, product_revision, quantity, status, planned_start, planned_finish
            FROM production_orders WHERE product_id=? AND status IN ('PLANNED','RELEASED','IN_PROGRESS') ORDER BY order_id""",
            (product_id,)).fetchall()
        return {
            "product": dict(product),
            "current_revision": rev,
            "changed_component_id": component_id,
            "new_component_id": new_component_id or component_id,
            "affected_ebom_usage": [dict(r) for r in ebom_use],
            "affected_mbom_usage": [dict(r) for r in mbom_use],
            "documents_requiring_review": [dict(r) for r in docs],
            "open_production_orders": [dict(r) for r in orders],
            "affected_product_count": len({r["product_id"] for r in ebom_use}),
        }
