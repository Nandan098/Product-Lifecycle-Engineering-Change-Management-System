from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_health_and_product_endpoints():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        products = client.get("/api/v1/products")
        assert products.status_code == 200
        assert any(p["product_id"] == "GEAR-ASSY-100" for p in products.json())
        ebom = client.get("/api/v1/products/GEAR-ASSY-100/ebom")
        assert ebom.status_code == 200
        assert len(ebom.json()["components"]) == 6


def test_ebom_import_endpoint_validates_approval():
    with TestClient(app) as client:
        response = client.post("/api/v1/integrations/ebom/import", json={
            "source_system": "TestPLM", "approval_status": "DRAFT",
            "product": {"product_id": "GEAR-ASSY-100", "revision": "B"},
            "components": [{"component_id": "BRG-6205", "quantity": 2, "find_number": "0010"}],
        })
        assert response.status_code == 422
        assert "approval_status" in response.json()["detail"]


def test_external_import_and_mbom_sync_endpoints():
    import json
    from core.config import project_path

    payload = json.loads(project_path("data", "external_ebom_revision_B.json").read_text(encoding="utf-8"))
    with TestClient(app) as client:
        imported = client.post("/api/v1/integrations/ebom/import", json=payload)
        assert imported.status_code == 201
        assert imported.json()["revision"] == "B"
        synced = client.post("/api/v1/products/GEAR-ASSY-100/sync-mbom", json={"revision": "B"})
        assert synced.status_code == 200
        assert synced.json()["status"] == "COMPLETED"
        mbom = client.get("/api/v1/products/GEAR-ASSY-100/mbom?revision=B")
        assert mbom.status_code == 200
        assert len(mbom.json()["components"]) == 6
