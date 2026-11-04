# Data Dictionary

| Entity/table | Key fields | Purpose |
|---|---|---|
| products | product_id, current_revision | Product master and current controlled revision |
| materials | material_id, material_type, base_uom | Component/material master |
| engineering_bom | product_id, revision, component_id, quantity, find_number | Engineering product structure (EBOM) |
| manufacturing_bom | product_id, revision, component_id, operation_no, staging_area | Manufacturing structure (MBOM) |
| component_operation_map | component_id, operation_no, operation_name, staging_area | Maps an engineering component to a manufacturing operation |
| documents | document_id, product_id, revision, status | Controlled drawing/specification/work-instruction metadata |
| engineering_changes | ecr_id, product_id, changed_component_id, new_component_id, status | ECR record and requested change |
| change_orders | eco_id, ecr_id, status, effective_date | Approved/implemented ECO record |
| product_revisions | product_id, revision, change_reference, status | Product revision audit history |
| production_orders | order_id, product_id, product_revision, status | Open downstream production orders for impact analysis |
| integration_jobs | job_id, source_system, target_system, payload_type, status | Integration monitor and payload audit |
| data_mappings | source_field, target_table, target_field, transformation_rule | Example source-to-target mapping configuration |

## Key relationships

- `products.product_id` is referenced by EBOM, MBOM, documents, ECRs, revisions and production orders.
- `materials.material_id` is referenced by EBOM, MBOM and component-operation mappings.
- `engineering_changes.ecr_id` is referenced by `change_orders.ecr_id`.
- `product_revisions.change_reference` stores the ECO or external change reference.
- `integration_jobs.job_id` uniquely identifies an integration execution.

## Status values used in the demo

- ECR: `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `IMPLEMENTED`.
- ECO: `APPROVED`, `IMPLEMENTED`.
- Product revision: `IN_REVIEW`, `RELEASED`, `IMPORTED`.
- Document: `APPROVED`, `REVIEW_REQUIRED`.
- Integration job: `COMPLETED`, `FAILED`.
