PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_family TEXT NOT NULL,
    description TEXT,
    current_revision TEXT NOT NULL DEFAULT 'A',
    lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS materials (
    material_id TEXT PRIMARY KEY,
    material_name TEXT NOT NULL,
    material_type TEXT NOT NULL,
    base_uom TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS engineering_bom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    revision TEXT NOT NULL,
    component_id TEXT NOT NULL REFERENCES materials(material_id),
    quantity REAL NOT NULL CHECK(quantity > 0),
    uom TEXT NOT NULL,
    find_number TEXT NOT NULL,
    reference_designator TEXT,
    effectivity_start TEXT,
    effectivity_end TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(product_id, revision, find_number)
);

CREATE TABLE IF NOT EXISTS manufacturing_bom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    revision TEXT NOT NULL,
    source_ebom_revision TEXT NOT NULL,
    component_id TEXT NOT NULL REFERENCES materials(material_id),
    quantity REAL NOT NULL CHECK(quantity > 0),
    uom TEXT NOT NULL,
    find_number TEXT NOT NULL,
    operation_no INTEGER NOT NULL,
    operation_name TEXT NOT NULL,
    staging_area TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    UNIQUE(product_id, revision, find_number)
);

CREATE TABLE IF NOT EXISTS component_operation_map (
    component_id TEXT PRIMARY KEY REFERENCES materials(material_id),
    operation_no INTEGER NOT NULL,
    operation_name TEXT NOT NULL,
    staging_area TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    revision TEXT NOT NULL,
    file_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'APPROVED',
    owner TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engineering_changes (
    ecr_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    changed_component_id TEXT NOT NULL REFERENCES materials(material_id),
    new_component_id TEXT REFERENCES materials(material_id),
    old_quantity REAL NOT NULL,
    new_quantity REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED',
    source_system TEXT NOT NULL DEFAULT 'Internal PLM Demo',
    created_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    effective_date TEXT
);

CREATE TABLE IF NOT EXISTS change_orders (
    eco_id TEXT PRIMARY KEY,
    ecr_id TEXT NOT NULL UNIQUE REFERENCES engineering_changes(ecr_id),
    status TEXT NOT NULL DEFAULT 'APPROVED',
    approved_by TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    implemented_at TEXT,
    effective_date TEXT NOT NULL,
    implementation_notes TEXT
);

CREATE TABLE IF NOT EXISTS product_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    revision TEXT NOT NULL,
    change_reference TEXT,
    change_summary TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(product_id, revision)
);

CREATE TABLE IF NOT EXISTS production_orders (
    order_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    product_revision TEXT NOT NULL,
    quantity REAL NOT NULL,
    status TEXT NOT NULL,
    planned_start TEXT,
    planned_finish TEXT
);

CREATE TABLE IF NOT EXISTS integration_jobs (
    job_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    target_system TEXT NOT NULL,
    payload_type TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system TEXT NOT NULL,
    source_field TEXT NOT NULL,
    target_table TEXT NOT NULL,
    target_field TEXT NOT NULL,
    transformation_rule TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_ebom_product_revision ON engineering_bom(product_id, revision);
CREATE INDEX IF NOT EXISTS idx_mbom_product_revision ON manufacturing_bom(product_id, revision);
CREATE INDEX IF NOT EXISTS idx_ecr_product_status ON engineering_changes(product_id, status);
CREATE INDEX IF NOT EXISTS idx_docs_product ON documents(product_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON integration_jobs(created_at);
