const db = require('../config/database');

class AuditLogModel {
    constructor(connection) {
        this.connection = connection;
    }

    create(action) {
        return db.run(this.connection, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
    }
}

module.exports = AuditLogModel;
