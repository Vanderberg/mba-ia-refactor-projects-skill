const db = require('../config/database');

class CourseModel {
    constructor(connection) {
        this.connection = connection;
    }

    findActiveById(id) {
        return db.get(this.connection, "SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
    }

    findAll() {
        return db.all(this.connection, "SELECT * FROM courses", []);
    }
}

module.exports = CourseModel;
