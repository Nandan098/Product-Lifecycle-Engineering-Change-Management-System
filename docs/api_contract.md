# REST API Contract

Base URL: `http://127.0.0.1:8000`

Interactive docs: `/docs`

## Health

`GET /health`

Returns service status and version.

## Products

`GET /api/v1/products`

Returns products and current revisions.

`GET /api/v1/products/{product_id}/ebom?revision=A`

Returns EBOM rows for the requested revision. If revision is omitted, current revision is used.

`GET /api/v1/products/{product_id}/mbom?revision=A`

Returns MBOM rows for the requested revision. If revision is omitted, current revision is used.

## Import an approved external EBOM

`POST /api/v1/integrations/ebom/import`

Example body:

```json
{
  "source_system": "Teamcenter-Sim",
  "approval_status": "APPROVED",
  "change_reference": "CC-EXT-2026-0042",
  "product": {"product_id": "GEAR-ASSY-100", "revision": "B"},
  "components": [
    {"component_id": "BRG-6205-2RS", "quantity": 2, "uom": "EA", "find_number": "0030"}
  ]
}
```

The example above is intentionally abbreviated; the actual sample payload contains all six component rows. The service validates product/material master references, positive quantity, unique find numbers and approval status. Successful imports set the product current revision to the imported revision and create a `COMPLETED` job. Failed imports create a `FAILED` job and return HTTP 422.

## Import external ECR

`POST /api/v1/integrations/ecr/import`

Example body is available at `data/external_ecr_bearing_update.json`. It is converted into an internal `SUBMITTED` ECR that must go through review/approval in the Streamlit app.

## Synchronize EBOM to MBOM

`POST /api/v1/products/{product_id}/sync-mbom`

Body:

```json
{"revision": "B", "triggered_by": "PLM Integration API"}
```

The revision must be current. Every component needs a `component_operation_map` entry. The service writes MBOM rows and an integration job.

## Monitor integration

`GET /api/v1/integration-jobs`

Returns recent integration jobs with source, target, payload type, status, count, message and payload JSON.

## HTTP behavior

- `200`: successful GET or sync.
- `201`: successful import.
- `404`: product not found.
- `422`: invalid payload, business rule violation or invalid synchronization request.
