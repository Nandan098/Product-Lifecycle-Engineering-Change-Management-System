from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.seed import seed_demo_data
from services.change_service import create_ecr, list_ecrs
from services.integration_service import import_external_ebom, import_external_ecr, list_integration_jobs, sync_ebom_to_mbom
from services.product_service import get_ebom, get_mbom, get_product, list_products

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_demo_data()
    yield


app = FastAPI(
    title="Product Lifecycle & Engineering Change API",
    description="Demo REST API simulating external PLM-to-manufacturing integration workflows.",
    version="1.0.0",
    lifespan=lifespan,
)


class SyncRequest(BaseModel):
    revision: str = Field(min_length=1)
    triggered_by: str = "API User"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "plm-integration-api", "version": "1.0.0"}


@app.get("/api/v1/products")
def products() -> list[dict]:
    return list_products()


@app.get("/api/v1/products/{product_id}/ebom")
def product_ebom(product_id: str, revision: str | None = None) -> dict:
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    selected_revision = revision or product["current_revision"]
    return {"product_id": product_id, "revision": selected_revision,
            "components": get_ebom(product_id, selected_revision)}


@app.get("/api/v1/products/{product_id}/mbom")
def product_mbom(product_id: str, revision: str | None = None) -> dict:
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    selected_revision = revision or product["current_revision"]
    return {"product_id": product_id, "revision": selected_revision,
            "components": get_mbom(product_id, selected_revision)}


@app.post("/api/v1/integrations/ebom/import", status_code=201)
def ebom_import(payload: dict) -> dict:
    try:
        return import_external_ebom(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/integrations/ecr/import", status_code=201)
def ecr_import(payload: dict) -> dict:
    try:
        return import_external_ecr(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/products/{product_id}/sync-mbom")
def mbom_sync(product_id: str, body: SyncRequest) -> dict:
    try:
        return sync_ebom_to_mbom(product_id, body.revision, body.triggered_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/engineering-changes")
def engineering_changes() -> list[dict]:
    return list_ecrs()


@app.get("/api/v1/integration-jobs")
def integration_jobs() -> list[dict]:
    return list_integration_jobs()
