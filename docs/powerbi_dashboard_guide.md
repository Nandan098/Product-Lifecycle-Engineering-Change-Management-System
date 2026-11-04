# Power BI Dashboard Guide

1. Run the Streamlit app and open **Power BI Exports**, or run `python -m scripts.export_powerbi`.
2. In Power BI Desktop, choose **Get Data → Text/CSV** and import the CSVs in `exports/`.
3. Create relationships using `product_id` and `ecr_id` as described below.

## Suggested pages and visuals

### Page 1 — Product & Revision Overview
- Cards: product count, latest revision count, number of documents requiring review.
- Table: product ID, product name, current revision, lifecycle status.
- Bar chart: EBOM component count by product/revision.

### Page 2 — Engineering Change Pipeline
- Cards: submitted, under review, approved, rejected and implemented ECR count.
- Funnel: ECR status.
- Table: ECR title, product, requester, reason code, status and created date.

### Page 3 — EBOM / MBOM Alignment
- Matrix: product, revision, find number, EBOM component, MBOM component, operation number.
- KPI: EBOM rows vs MBOM rows for selected revision.

### Page 4 — Integration Monitoring
- Cards: completed jobs, failed jobs, records imported.
- Bar chart: jobs by source system and status.
- Table: job ID, payload type, source, target, record count, message and timestamp.

### Page 5 — Downstream Impact
- Table: production orders by product revision and status.
- Table: documents by revision and review status.

## Suggested relationships

- Products 1-to-many Engineering BOM, Manufacturing BOM, Documents, Production Orders, Engineering Changes.
- Engineering Changes 1-to-1 Change Orders (ECR to ECO).
- Integration Jobs are independent audit records. Use job_id as a unique row key.
