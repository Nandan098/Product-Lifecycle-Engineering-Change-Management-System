from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core.config import project_path
from core.seed import seed_demo_data
from services.analytics_service import dashboard_summary, export_powerbi_csv
from services.change_service import approve_ecr, create_ecr, implement_eco, list_ecrs, reject_ecr, start_review
from services.impact_service import analyze_change_impact
from services.integration_service import import_external_ebom, list_integration_jobs, sync_ebom_to_mbom
from services.product_service import (get_ebom, get_mbom, get_product, list_documents,
                                      list_products, list_production_orders, list_revisions)
from core.database import db_session

st.set_page_config(page_title="Product Lifecycle & Engineering Change Management", page_icon="⚙️", layout="wide")
seed_demo_data()

st.title("Product Lifecycle & Engineering Change Management")
st.caption("A portfolio application simulating SAP PLM, Engineering Change Management and PLM System Integration concepts.")

page = st.sidebar.radio("Navigation", [
    "Overview", "Product & EBOM", "Documents & Revisions", "Engineering Change Control",
    "Change Impact Analysis", "PLM Integration Center", "Power BI Exports", "About & Limitations"
])

products = list_products()
product_options = {f"{p['product_id']} — {p['product_name']}": p["product_id"] for p in products}


def show_table(rows: list[dict], empty_message: str = "No records found.") -> None:
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


if page == "Overview":
    summary = dashboard_summary()
    cols = st.columns(3)
    cols[0].metric("Products", summary["products"])
    cols[1].metric("Open / pending ECRs", summary["ecr_open"])
    cols[2].metric("Implemented ECRs", summary["ecr_implemented"])
    cols = st.columns(3)
    cols[0].metric("Active MBOM rows", summary["active_mbom_rows"])
    cols[1].metric("Documents needing review", summary["docs_review"])
    cols[2].metric("Failed integration jobs", summary["integration_failed"])
    st.subheader("Business workflow")
    st.markdown("**External Engineering / PLM → Integration & Validation → EBOM → Change Approval → MBOM → Manufacturing Planning**")
    st.info("Demo flow: use Product & EBOM to inspect the baseline; submit an ECR; review and approve it; implement the ECO to create a new revision; then synchronize the approved EBOM to the MBOM.")
    st.subheader("Product revision status")
    rev_rows = []
    for p in products:
        rev_rows.append({"Product": p["product_id"], "Name": p["product_name"],
                         "Current revision": p["current_revision"], "Lifecycle": p["lifecycle_status"]})
    show_table(rev_rows)

elif page == "Product & EBOM":
    selected = st.selectbox("Select product", list(product_options.keys()))
    pid = product_options[selected]
    product = get_product(pid)
    revs = list_revisions(pid)
    revisions = sorted({r["revision"] for r in revs} | {product["current_revision"]})
    revision = st.selectbox("Revision", revisions, index=revisions.index(product["current_revision"]))
    st.subheader(f"Engineering BOM — {pid} / Revision {revision}")
    ebom = get_ebom(pid, revision)
    show_table(ebom)
    st.subheader(f"Manufacturing BOM — {pid} / Revision {revision}")
    mbom = get_mbom(pid, revision)
    show_table(mbom, "No MBOM for this revision yet. Use the PLM Integration Center to transform the EBOM.")
    if st.button("Compare EBOM and MBOM component counts"):
        st.write({"EBOM component rows": len(ebom), "MBOM component rows": len(mbom),
                  "Status": "Aligned" if len(ebom) == len(mbom) and len(ebom) > 0 else "Review required"})

elif page == "Documents & Revisions":
    selected = st.selectbox("Select product", list(product_options.keys()))
    pid = product_options[selected]
    product = get_product(pid)
    st.subheader("Controlled product documents")
    show_table(list_documents(pid))
    st.caption("When an ECO is implemented, documents tied to the previous revision are flagged REVIEW_REQUIRED for engineering review.")
    st.subheader("Revision history")
    show_table(list_revisions(pid))
    if st.button("Export document register as CSV"):
        docs = list_documents(pid)
        path = project_path("exports", f"documents_{pid}.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(docs).to_csv(path, index=False)
        st.success(f"Saved {path.relative_to(project_path())}")

elif page == "Engineering Change Control":
    st.subheader("Submit an Engineering Change Request (ECR)")
    with st.form("ecr_form"):
        selected = st.selectbox("Product", list(product_options.keys()))
        pid = product_options[selected]
        current = get_product(pid)
        ebom = get_ebom(pid, current["current_revision"])
        component_options = {f"{r['component_id']} — {r['material_name']} (find {r['find_number']})": r["component_id"] for r in ebom}
        old_component_label = st.selectbox("Existing component to change", list(component_options.keys()))
        old_component = component_options[old_component_label]
        replacement_options = {"Keep same component (quantity / specification change)": ""}
        with db_session() as conn:
            materials = conn.execute("SELECT material_id, material_name FROM materials ORDER BY material_id").fetchall()
        for m in materials:
            if m["material_id"] != old_component:
                replacement_options[f"{m['material_id']} — {m['material_name']}"] = m["material_id"]
        replacement_label = st.selectbox("Replacement component (optional)", list(replacement_options.keys()))
        new_component = replacement_options[replacement_label]
        old_row = next(r for r in ebom if r["component_id"] == old_component)
        new_qty = st.number_input("New quantity per product", min_value=0.01, value=float(old_row["quantity"]), step=0.5)
        title = st.text_input("Change title", value="Bearing specification improvement")
        reason = st.selectbox("Reason code", ["QUALITY_IMPROVEMENT", "COST_REDUCTION", "DESIGN_UPDATE", "REGULATORY", "OBSOLESCENCE"])
        description = st.text_area("Business / engineering justification", value="Replace the standard bearing with a sealed bearing to improve contamination protection.")
        requester = st.text_input("Requested by", value="Design Engineering")
        effective_date = st.date_input("Requested effective date")
        submitted = st.form_submit_button("Submit ECR")
    if submitted:
        try:
            ecr_id = create_ecr(product_id=pid, title=title, description=description, reason_code=reason,
                                requested_by=requester, changed_component_id=old_component,
                                new_component_id=new_component or None, new_quantity=float(new_qty),
                                effective_date=effective_date.isoformat())
            st.success(f"Created {ecr_id}. It is now SUBMITTED.")
        except Exception as exc:
            st.error(str(exc))

    st.subheader("ECR / ECO workflow")
    ecr_rows = list_ecrs()
    show_table(ecr_rows)
    if ecr_rows:
        ecr_map = {f"{r['ecr_id']} | {r['title']} | {r['status']}": r["ecr_id"] for r in ecr_rows}
        chosen = st.selectbox("Select change request", list(ecr_map.keys()), key="ecr_select")
        ecr_id = ecr_map[chosen]
        actor = st.text_input("Reviewer / approver name", value="Manufacturing Engineering")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Start Review"):
            try:
                start_review(ecr_id, actor)
                st.success("ECR moved to UNDER_REVIEW. Refresh the page to see the status.")
            except Exception as exc:
                st.error(str(exc))
        if c2.button("Approve & Create ECO"):
            try:
                eco_id = approve_ecr(ecr_id, actor)
                st.success(f"Approved. Created {eco_id}.")
            except Exception as exc:
                st.error(str(exc))
        if c3.button("Reject ECR"):
            try:
                reject_ecr(ecr_id, actor, "Rejected during demo review.")
                st.warning("ECR rejected.")
            except Exception as exc:
                st.error(str(exc))
        with db_session() as conn:
            eco_rows = conn.execute("""SELECT c.eco_id, c.status, c.effective_date, e.ecr_id, e.product_id
                FROM change_orders c JOIN engineering_changes e ON e.ecr_id=c.ecr_id
                ORDER BY c.approved_at DESC""").fetchall()
        if eco_rows:
            eco_map = {f"{r['eco_id']} | {r['status']} | {r['product_id']}": r["eco_id"] for r in eco_rows}
            chosen_eco = st.selectbox("Approved ECO to implement", list(eco_map.keys()))
            if c4.button("Implement ECO"):
                try:
                    new_rev = implement_eco(eco_map[chosen_eco], actor)
                    st.success(f"ECO implemented. New engineering revision: {new_rev}. Next, synchronize the MBOM.")
                except Exception as exc:
                    st.error(str(exc))

elif page == "Change Impact Analysis":
    st.subheader("Assess downstream impact before implementing an engineering change")
    selected = st.selectbox("Product", list(product_options.keys()))
    pid = product_options[selected]
    product = get_product(pid)
    ebom = get_ebom(pid, product["current_revision"])
    component_map = {f"{r['component_id']} — {r['material_name']}": r["component_id"] for r in ebom}
    component_label = st.selectbox("Component under change", list(component_map.keys()))
    component_id = component_map[component_label]
    if st.button("Analyze impact", type="primary"):
        try:
            impact = analyze_change_impact(pid, component_id)
            a, b, c = st.columns(3)
            a.metric("Affected products", impact["affected_product_count"])
            b.metric("Open production orders", len(impact["open_production_orders"]))
            c.metric("Controlled documents", len(impact["documents_requiring_review"]))
            st.markdown("**Engineering BOM usage**")
            show_table(impact["affected_ebom_usage"])
            st.markdown("**Manufacturing BOM usage**")
            show_table(impact["affected_mbom_usage"])
            st.markdown("**Production orders requiring review**")
            show_table(impact["open_production_orders"])
            st.markdown("**Product documents**")
            show_table(impact["documents_requiring_review"])
        except Exception as exc:
            st.error(str(exc))

elif page == "PLM Integration Center":
    st.subheader("External PLM → Manufacturing data exchange")
    st.markdown("Import an approved EBOM revision from a simulated external PLM system, validate component master references, and create an auditable integration job.")
    example_path = project_path("data", "external_ebom_revision_B.json")
    uploaded = st.file_uploader("Upload external EBOM JSON", type=["json"])
    if uploaded:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
        except Exception as exc:
            payload = None
            st.error(f"Invalid JSON: {exc}")
    else:
        payload = json.loads(example_path.read_text(encoding="utf-8"))
        st.caption("No file selected: using the included Teamcenter-Sim example payload.")
    with st.expander("Preview incoming JSON"):
        st.json(payload)
    if st.button("Import approved EBOM", type="primary", disabled=payload is None):
        try:
            result = import_external_ebom(payload)
            st.success(f"Import complete: {result}")
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Transform current EBOM to MBOM")
    selected = st.selectbox("Product for synchronization", list(product_options.keys()), key="sync_product")
    pid = product_options[selected]
    product = get_product(pid)
    revision = st.text_input("Current product revision", value=product["current_revision"])
    if st.button("Synchronize EBOM → MBOM"):
        try:
            result = sync_ebom_to_mbom(pid, revision, "PLM Integration Center")
            st.success(f"Synchronization complete: {result}")
        except Exception as exc:
            st.error(str(exc))

    st.subheader("Integration job monitor")
    jobs = list_integration_jobs()
    show_table(jobs)

elif page == "Power BI Exports":
    st.subheader("Export project tables for Power BI")
    st.write("The export creates one CSV per business object. Import them into Power BI Desktop and relate them using product_id, ecr_id and job_id.")
    if st.button("Generate CSV exports", type="primary"):
        outputs = export_powerbi_csv(project_path("exports"))
        st.success(f"Generated {len(outputs)} files in the exports folder.")
        for path in outputs:
            st.write(f"- `{path.name}`")
    st.markdown("**Suggested report pages:** Product & Revision Overview; Engineering Change Pipeline; EBOM vs MBOM; Integration Job Monitor; Open Production Order Impact.")

else:
    st.subheader("Project scope and honest limitations")
    st.markdown("""
    **What this project demonstrates**
    - Product structures, EBOM and MBOM concepts.
    - ECR/ECO workflow, revision control and change traceability.
    - Impact analysis for documents, BOMs and open production orders.
    - A simulated REST/JSON integration boundary for external PLM data.
    - Data validation, integration job monitoring and CSV-based BI reporting.

    **What it does not claim to be**
    - It is not an SAP installation, SAP configuration project or certified SAP connector.
    - The external PLM endpoint is simulated with example JSON payloads; no Teamcenter or other licensed PLM is connected.
    - Approval roles and permissions are simplified for a portfolio demonstration.
    - The demo uses SQLite. A production deployment would require enterprise database, authentication, authorization, audit, security and integration controls.

    **Run the REST API separately**
    ```bash
    python -m scripts.run_api
    ```
    Then open `http://127.0.0.1:8000/docs` for interactive API documentation.
    """)
