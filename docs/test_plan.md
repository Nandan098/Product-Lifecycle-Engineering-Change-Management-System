# Test Plan

## Objective

Verify critical product structure, change control and integration workflows before demonstrating the application.

## Test cases

| Test ID | Scenario | Expected result |
|---|---|---|
| TC-01 | Load seed data | Two products, baseline EBOM/MBOM and documents are present |
| TC-02 | Analyze impact of BRG-6205 | Current BOM usage, controlled documents and open orders are listed |
| TC-03 | Create ECR for a current EBOM component | ECR is created with SUBMITTED status |
| TC-04 | Attempt approval without review | Business rule blocks approval |
| TC-05 | Start ECR review and approve | ECR becomes APPROVED and an ECO is created |
| TC-06 | Implement approved ECO | New EBOM revision is created; previous documents are flagged |
| TC-07 | Synchronize new EBOM to MBOM | MBOM rows reflect the new component and assigned operation |
| TC-08 | Import approved external EBOM JSON | Revision and integration job are created |
| TC-09 | Import draft external EBOM | Import is rejected and FAILED job is logged |
| TC-10 | Import unknown material | Validation fails with a clear error |
| TC-11 | Query products and EBOM using REST API | API returns expected JSON |
| TC-12 | Synchronize via REST API | MBOM is updated and job appears in monitor |

## Automated execution

```bash
pytest -q
```

The automated tests use a temporary SQLite database; the local demo database is not modified by the test suite.
