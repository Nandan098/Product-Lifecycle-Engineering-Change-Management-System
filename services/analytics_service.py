from __future__ import annotations

import csv
from pathlib import Path

from core.database import db_session


def dashboard_summary() -> dict:
    with db_session() as conn:
        products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        ecr_open = conn.execute("SELECT COUNT(*) FROM engineering_changes WHERE status IN ('SUBMITTED','UNDER_REVIEW','APPROVED')").fetchone()[0]
        ecr_implemented = conn.execute("SELECT COUNT(*) FROM engineering_changes WHERE status='IMPLEMENTED'").fetchone()[0]
        docs_review = conn.execute("SELECT COUNT(*) FROM documents WHERE status='REVIEW_REQUIRED'").fetchone()[0]
        integration_failed = conn.execute("SELECT COUNT(*) FROM integration_jobs WHERE status='FAILED'").fetchone()[0]
        mbom_rows = conn.execute("SELECT COUNT(*) FROM manufacturing_bom WHERE status='ACTIVE'").fetchone()[0]
        return {"products": products, "ecr_open": ecr_open, "ecr_implemented": ecr_implemented,
                "docs_review": docs_review, "integration_failed": integration_failed, "active_mbom_rows": mbom_rows}


def export_powerbi_csv(export_dir: str | Path) -> list[Path]:
    target = Path(export_dir)
    target.mkdir(parents=True, exist_ok=True)
    exports = {
        "products.csv": "SELECT * FROM products",
        "engineering_bom.csv": "SELECT * FROM engineering_bom",
        "manufacturing_bom.csv": "SELECT * FROM manufacturing_bom",
        "engineering_changes.csv": "SELECT * FROM engineering_changes",
        "change_orders.csv": "SELECT * FROM change_orders",
        "documents.csv": "SELECT * FROM documents",
        "integration_jobs.csv": "SELECT * FROM integration_jobs",
        "production_orders.csv": "SELECT * FROM production_orders",
    }
    outputs = []
    with db_session() as conn:
        for filename, query in exports.items():
            rows = conn.execute(query).fetchall()
            path = target / filename
            if rows:
                headers = rows[0].keys()
                with path.open("w", newline="", encoding="utf-8-sig") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(headers)
                    writer.writerows([tuple(row) for row in rows])
            else:
                path.write_text("", encoding="utf-8")
            outputs.append(path)
    return outputs
