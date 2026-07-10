const db = require('../config/database');

class PaymentModel {
    constructor(connection) {
        this.connection = connection;
    }

    create(enrollmentId, amount, status) {
        return db.run(this.connection, "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]);
    }

    findByEnrollmentId(enrollmentId) {
        return db.get(this.connection, "SELECT amount, status FROM payments WHERE enrollment_id = ?", [enrollmentId]);
    }
}

module.exports = PaymentModel;
