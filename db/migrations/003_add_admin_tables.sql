CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT NOT NULL,
    message TEXT NOT NULL,
    admin_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_system_logs_type ON system_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs(created_at);

CREATE TABLE IF NOT EXISTS content_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_number INTEGER NOT NULL,
    source_file TEXT,
    questions_added INTEGER DEFAULT 0,
    questions_updated INTEGER DEFAULT 0,
    imported_by INTEGER,
    imported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS backups_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_size_bytes INTEGER,
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);
