from __future__ import annotations

from datetime import datetime, timezone

from core.database import db_session, init_db


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def seed_demo_data() -> None:
    init_db()
    created = now_iso()
    with db_session() as conn:
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
            return

        products = [
            ("GEAR-ASSY-100", "Automotive Gearbox Assembly", "Transmission", "Two-stage gearbox assembly for passenger vehicles.", "A", "ACTIVE", created),
            ("PUMP-ASSY-200", "Industrial Pump Assembly", "Process Equipment", "Centrifugal pump assembly for process industry.", "A", "ACTIVE", created),
        ]
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", products)

        materials = [
            ("GEAR-IN-01", "Input Helical Gear", "COMPONENT", "EA", "Machined input gear"),
            ("GEAR-OUT-01", "Output Spur Gear", "COMPONENT", "EA", "Machined output gear"),
            ("BRG-6205", "Deep Groove Ball Bearing 6205", "COMPONENT", "EA", "Standard bearing"),
            ("BRG-6205-2RS", "Sealed Ball Bearing 6205-2RS", "COMPONENT", "EA", "Sealed bearing replacement"),
            ("HOUSING-AL", "Aluminium Gearbox Housing", "COMPONENT", "EA", "Cast aluminium housing"),
            ("SEAL-01", "Oil Seal", "COMPONENT", "EA", "Radial shaft oil seal"),
            ("BOLT-M8", "Hex Bolt M8", "COMPONENT", "EA", "Fastener"),
            ("PUMP-IMPELLER", "Pump Impeller", "COMPONENT", "EA", "Pump impeller"),
            ("PUMP-CASING", "Pump Casing", "COMPONENT", "EA", "Pump casing"),
            ("MOTOR-1P5", "1.5 kW Electric Motor", "COMPONENT", "EA", "Electric drive motor"),
        ]
        conn.executemany("INSERT INTO materials(material_id, material_name, material_type, base_uom, description) VALUES (?, ?, ?, ?, ?)", materials)

        ebom_rows = [
            ("GEAR-ASSY-100", "A", "GEAR-IN-01", 1, "EA", "0010", "IN-GEAR"),
            ("GEAR-ASSY-100", "A", "GEAR-OUT-01", 1, "EA", "0020", "OUT-GEAR"),
            ("GEAR-ASSY-100", "A", "BRG-6205", 2, "EA", "0030", "BEARING-L/R"),
            ("GEAR-ASSY-100", "A", "HOUSING-AL", 1, "EA", "0040", "HOUSING"),
            ("GEAR-ASSY-100", "A", "SEAL-01", 2, "EA", "0050", "SEAL-L/R"),
            ("GEAR-ASSY-100", "A", "BOLT-M8", 8, "EA", "0060", "FASTENERS"),
            ("PUMP-ASSY-200", "A", "PUMP-IMPELLER", 1, "EA", "0010", "IMPELLER"),
            ("PUMP-ASSY-200", "A", "PUMP-CASING", 1, "EA", "0020", "CASING"),
            ("PUMP-ASSY-200", "A", "MOTOR-1P5", 1, "EA", "0030", "DRIVE"),
            ("PUMP-ASSY-200", "A", "SEAL-01", 1, "EA", "0040", "SEAL"),
        ]
        conn.executemany("""INSERT INTO engineering_bom
            (product_id, revision, component_id, quantity, uom, find_number, reference_designator, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", [r + (created,) for r in ebom_rows])

        operation_maps = [
            ("GEAR-IN-01", 20, "Gear machining", "WIP-RACK-02", "CNC gear cutting"),
            ("GEAR-OUT-01", 20, "Gear machining", "WIP-RACK-02", "CNC gear cutting"),
            ("BRG-6205", 50, "Bearing assembly", "ASSEMBLY-KIT-A", "Press-fit bearing"),
            ("BRG-6205-2RS", 50, "Bearing assembly", "ASSEMBLY-KIT-A", "Sealed bearing press-fit"),
            ("HOUSING-AL", 10, "Housing preparation", "WIP-RACK-01", "Deburr and clean housing"),
            ("SEAL-01", 50, "Bearing assembly", "ASSEMBLY-KIT-A", "Install oil seal"),
            ("BOLT-M8", 60, "Final fastening", "FASTENER-BIN", "Torque fasteners"),
            ("PUMP-IMPELLER", 20, "Rotor assembly", "WIP-RACK-03", "Prepare impeller"),
            ("PUMP-CASING", 10, "Casing preparation", "WIP-RACK-01", "Inspect casing"),
            ("MOTOR-1P5", 40, "Drive installation", "ASSEMBLY-KIT-B", "Mount electric motor"),
        ]
        conn.executemany("INSERT INTO component_operation_map VALUES (?, ?, ?, ?, ?)", operation_maps)

        # Seed initial MBOM for both products, derived from revision A EBOM.
        for product_id in ("GEAR-ASSY-100", "PUMP-ASSY-200"):
            rows = conn.execute("SELECT * FROM engineering_bom WHERE product_id=? AND revision='A'", (product_id,)).fetchall()
            for row in rows:
                op = conn.execute("SELECT * FROM component_operation_map WHERE component_id=?", (row["component_id"],)).fetchone()
                conn.execute("""INSERT INTO manufacturing_bom
                    (product_id, revision, source_ebom_revision, component_id, quantity, uom, find_number,
                     operation_no, operation_name, staging_area, status, created_at)
                    VALUES (?, 'A', 'A', ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)""",
                    (product_id, row["component_id"], row["quantity"], row["uom"], row["find_number"],
                     op["operation_no"], op["operation_name"], op["staging_area"], created))

        docs = [
            ("DOC-GEAR-CAD-001", "GEAR-ASSY-100", "CAD_DRAWING", "Gearbox Assembly CAD Drawing", "A", "gearbox_assembly_rev_A.step", "APPROVED", "Engineering", created),
            ("DOC-GEAR-SPEC-001", "GEAR-ASSY-100", "SPECIFICATION", "Gearbox Product Specification", "A", "gearbox_spec_rev_A.pdf", "APPROVED", "Engineering", created),
            ("DOC-GEAR-WI-001", "GEAR-ASSY-100", "WORK_INSTRUCTION", "Gearbox Assembly Work Instruction", "A", "gearbox_work_instruction_rev_A.pdf", "APPROVED", "Manufacturing Engineering", created),
            ("DOC-PUMP-CAD-001", "PUMP-ASSY-200", "CAD_DRAWING", "Pump Assembly CAD Drawing", "A", "pump_assembly_rev_A.step", "APPROVED", "Engineering", created),
        ]
        conn.executemany("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", docs)

        revisions = [
            ("GEAR-ASSY-100", "A", None, "Initial released product definition", "RELEASED", "Seed Data", created),
            ("PUMP-ASSY-200", "A", None, "Initial released product definition", "RELEASED", "Seed Data", created),
        ]
        conn.executemany("""INSERT INTO product_revisions
            (product_id, revision, change_reference, change_summary, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", revisions)

        orders = [
            ("PO-GEAR-1001", "GEAR-ASSY-100", "A", 120, "RELEASED", "2026-11-10", "2026-11-14"),
            ("PO-GEAR-1002", "GEAR-ASSY-100", "A", 60, "IN_PROGRESS", "2026-11-12", "2026-11-16"),
            ("PO-PUMP-2001", "PUMP-ASSY-200", "A", 35, "PLANNED", "2026-11-18", "2026-11-21"),
        ]
        conn.executemany("INSERT INTO production_orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)

        mappings = [
            ("Teamcenter-Sim", "Item.id", "products", "product_id", "Direct string mapping", 1),
            ("Teamcenter-Sim", "Item.revision", "engineering_bom", "revision", "Direct string mapping", 1),
            ("Teamcenter-Sim", "Structure.component.partNumber", "engineering_bom", "component_id", "Resolve external part number to material_id", 1),
            ("Teamcenter-Sim", "Structure.component.quantity", "engineering_bom", "quantity", "Numeric conversion; must be > 0", 1),
            ("Teamcenter-Sim", "Structure.component.findNumber", "engineering_bom", "find_number", "Pad to four digits where required", 1),
        ]
        conn.executemany("""INSERT INTO data_mappings
            (source_system, source_field, target_table, target_field, transformation_rule, active)
            VALUES (?, ?, ?, ?, ?, ?)""", mappings)
