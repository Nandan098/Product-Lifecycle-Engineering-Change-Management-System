# Functional Requirements Document (FRD)

## 1. Purpose

The Product Lifecycle & Engineering Change Management System is a student portfolio application that demonstrates product structure control, engineering change governance, and engineering-to-manufacturing data exchange.

## 2. Business scenario

An automotive supplier designs a gearbox assembly. Engineering owns the design definition (EBOM, CAD metadata and specifications), while manufacturing owns the production definition (MBOM, operation assignment and staging information). When engineering changes a component, the business must understand the downstream impact, approve the change, create a new product revision and share the approved structure with manufacturing.

## 3. Stakeholders and actors

| Actor | Responsibility |
|---|---|
| Design Engineer | Creates ECR and updates product definition |
| Engineering Change Board | Reviews and approves/rejects ECR |
| PLM Administrator | Maintains product/document/revision metadata |
| Manufacturing Engineer | Reviews MBOM and operation mappings |
| Integration Service | Validates and exchanges PLM data |
| Production Planner | Reviews open orders affected by changes |

## 4. Functional requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| FR-01 | Product master | User can view product ID, name, family and current revision |
| FR-02 | EBOM | User/API can retrieve a product EBOM by revision |
| FR-03 | Document register | User can view controlled document metadata and revision/status |
| FR-04 | ECR creation | User can submit a change against a component in the current EBOM |
| FR-05 | ECR review | Submitted ECR can be moved to UNDER_REVIEW |
| FR-06 | ECO approval | Only UNDER_REVIEW ECR can be approved and generate an ECO |
| FR-07 | ECO implementation | Only approved ECO can create a next EBOM revision |
| FR-08 | Revision traceability | New revision records change reference, summary, creator and timestamp |
| FR-09 | Document impact | Documents on the prior revision are flagged REVIEW_REQUIRED after implementation |
| FR-10 | Change impact | System lists current EBOM usage, MBOM usage, product documents and open production orders |
| FR-11 | EBOM-to-MBOM | System maps each EBOM component to a manufacturing operation and staging area |
| FR-12 | External EBOM import | API accepts approved external JSON, validates material numbers and creates an integration job |
| FR-13 | External ECR import | API translates an external change request into an internal ECR |
| FR-14 | Integration monitoring | System records source, target, type, status, record count, payload and message |
| FR-15 | BI extract | User can export product/BOM/change/document/job/order tables as CSV |

## 5. Business rules

1. An ECR must reference a product and a component in that product's current EBOM.
2. A replacement component, when supplied, must exist in the material master.
3. Requested quantity must be greater than zero.
4. An ECR must be reviewed before approval.
5. An ECO must be approved before implementation.
6. Implementation copies the current EBOM into the next revision and applies the requested component/quantity change.
7. Controlled documents on the prior revision are flagged for review; they are not silently changed.
8. EBOM-to-MBOM synchronization requires the requested revision to be the current product revision.
9. Every EBOM component must have an operation/staging mapping before the MBOM sync can complete.
10. External EBOM import requires approval_status = APPROVED and rejects unknown materials, duplicate find numbers, missing identifiers and non-positive quantities.

## 6. Out of scope

- Actual SAP configuration/customizing or direct SAP database access.
- Live Teamcenter, Windchill, 3DEXPERIENCE or SAP PLM connector.
- CAD geometry editing or native drawing rendering.
- Production-grade authorization, digital signatures and regulated electronic records.
- Multi-level recursive BOM explosion and full effectivity/date management.
- Enterprise-grade middleware, message queues and guaranteed delivery.
