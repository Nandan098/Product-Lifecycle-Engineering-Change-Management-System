# Business Process Flow

## A. Internal engineering change process

```mermaid
flowchart TD
    A[Identify product design issue] --> B[Create Engineering Change Request]
    B --> C[Validate product and current EBOM component]
    C --> D[Submit ECR]
    D --> E[Engineering Change Board review]
    E -->|Reject| F[Record rejection and close ECR]
    E -->|Approve| G[Create Engineering Change Order]
    G --> H[Implement ECO]
    H --> I[Create next EBOM revision]
    I --> J[Flag previous-revision documents for review]
    J --> K[Analyze downstream impact]
    K --> L[Map EBOM components to manufacturing operations]
    L --> M[Synchronize EBOM to MBOM]
    M --> N[Manufacturing review and planning]
```

## B. External PLM system integration process

```mermaid
flowchart TD
    A[External PLM system] --> B[Export approved EBOM JSON]
    B --> C[REST API receives payload]
    C --> D[Validate product, revision, materials and quantities]
    D -->|Invalid| E[Create FAILED integration job with reason]
    D -->|Valid| F[Persist EBOM revision]
    F --> G[Create COMPLETED integration job]
    G --> H[Transform EBOM to MBOM using component-operation map]
    H --> I[Record synchronization job]
    I --> J[Manufacturing system consumes updated MBOM]
```

## C. Product data lifecycle

Engineering creates the product definition and EBOM. Controlled changes are requested and approved through ECR/ECO. The approved revision is implemented and mapped into a manufacturing-specific BOM. Documents and downstream orders are reviewed before manufacturing adopts the new version.

## D. Important process distinction

EBOM and MBOM serve related but different purposes. EBOM represents the engineering design structure. MBOM represents how the product is planned/assembled/manufactured, and can group or sequence components to manufacturing operations. This demo uses a one-to-one component transformation with an operation mapping table to keep the logic understandable; real implementations can require more complex transformation rules.
