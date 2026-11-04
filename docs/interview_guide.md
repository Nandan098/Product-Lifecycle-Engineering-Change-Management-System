# Interview Walkthrough — Capgemini SAP Manufacturing

## 60-second explanation

"I developed a Product Lifecycle and Engineering Change Management application to demonstrate how engineering product data can be governed and handed over to manufacturing. It manages product master data, EBOM revisions and controlled documents; supports ECR review and ECO approval; analyzes the impact of a change on BOMs, documents and open production orders; and simulates external PLM integration through REST APIs and JSON. Once an approved EBOM revision is available, the system maps components to manufacturing operations and creates an MBOM version for manufacturing use."

## Explain the business problem

Engineering and manufacturing need a controlled handover. A design change cannot be treated as an isolated drawing update because it may affect materials, manufacturing operations, documentation and production orders. The application makes these dependencies visible and auditable.

## Demonstrate this scenario

1. Start from gearbox assembly revision A.
2. Show the standard BRG-6205 bearing in the EBOM.
3. Run change impact analysis and show current MBOM usage, documents and open orders.
4. Submit an ECR to replace the bearing with BRG-6205-2RS.
5. Move the request to review; approve it to create an ECO.
6. Implement the ECO to create revision B and flag revision-A documents for review.
7. Synchronize revision B from EBOM to MBOM.
8. Show the integration job log and updated MBOM.

## Concepts to revise

- EBOM vs MBOM: engineering design structure vs manufacturing/assembly structure.
- ECR vs ECO: request to evaluate a proposed change vs controlled order/instruction authorizing implementation.
- Revision vs effectivity: product version identifier vs when/where a change applies.
- Change impact analysis: identifies affected structures, documents, operations and orders.
- Data mapping: translates external PLM fields and identifiers into target ERP/PLM fields.
- REST API: HTTP interface for systems to exchange structured data.
- JSON: common payload format for API exchanges.
- Integration monitoring: tracks source, target, payload type, status, count and failure reason.

## Likely interview questions

**Q: Why do we need both EBOM and MBOM?**
A: Engineering defines what the product is. Manufacturing defines how the product is built, including operation sequence, work-center context and staging. They are related but not always identical.

**Q: Why is an ECR not enough?**
A: An ECR captures a proposed change and rationale. The change should be assessed and approved before implementation is authorized through the change-order process.

**Q: Why analyze impact before implementation?**
A: A component change can affect multiple product structures, manufacturing operations, controlled documents and open production orders. Impact analysis helps stakeholders decide what must be reviewed before release.

**Q: Why REST APIs and JSON?**
A: External PLM and ERP systems need a defined interface to exchange product structures and change information. REST/JSON is one possible integration pattern; actual SAP landscapes can also use OData, IDocs, SOAP, RFC/BAPI, middleware or other interfaces.

**Q: Is this an SAP implementation?**
A: No. It is an independent educational simulation of SAP PLM/PLMSI business concepts. I have not configured SAP or connected to a licensed SAP/Teamcenter environment.

## Keep claims accurate

Do not claim SAP configuration, live Teamcenter integration, CAD automation, or production deployment. Explain what the application actually implements and distinguish simulation from hands-on SAP experience.
