from __future__ import annotations

from core.database import db_session


def list_products() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY product_id").fetchall()
        return [dict(r) for r in rows]


def get_product(product_id: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM products WHERE product_id=?", (product_id,)).fetchone()
        return dict(row) if row else None


def get_ebom(product_id: str, revision: str | None = None) -> list[dict]:
    with db_session() as conn:
        if revision is None:
            product = conn.execute("SELECT current_revision FROM products WHERE product_id=?", (product_id,)).fetchone()
            if not product:
                return []
            revision = product["current_revision"]
        rows = conn.execute("""SELECT e.*, m.material_name, m.material_type
            FROM engineering_bom e JOIN materials m ON m.material_id=e.component_id
            WHERE e.product_id=? AND e.revision=? ORDER BY e.find_number""", (product_id, revision)).fetchall()
        return [dict(r) for r in rows]


def get_mbom(product_id: str, revision: str | None = None) -> list[dict]:
    with db_session() as conn:
        if revision is None:
            product = conn.execute("SELECT current_revision FROM products WHERE product_id=?", (product_id,)).fetchone()
            if not product:
                return []
            revision = product["current_revision"]
        rows = conn.execute("""SELECT b.*, m.material_name
            FROM manufacturing_bom b JOIN materials m ON m.material_id=b.component_id
            WHERE b.product_id=? AND b.revision=? ORDER BY b.operation_no, b.find_number""", (product_id, revision)).fetchall()
        return [dict(r) for r in rows]


def list_documents(product_id: str | None = None) -> list[dict]:
    with db_session() as conn:
        if product_id:
            rows = conn.execute("SELECT * FROM documents WHERE product_id=? ORDER BY document_id", (product_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY product_id, document_id").fetchall()
        return [dict(r) for r in rows]


def list_revisions(product_id: str) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM product_revisions WHERE product_id=? ORDER BY created_at DESC", (product_id,)).fetchall()
        return [dict(r) for r in rows]


def list_production_orders(product_id: str | None = None) -> list[dict]:
    with db_session() as conn:
        if product_id:
            rows = conn.execute("SELECT * FROM production_orders WHERE product_id=? ORDER BY order_id", (product_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM production_orders ORDER BY order_id").fetchall()
        return [dict(r) for r in rows]
