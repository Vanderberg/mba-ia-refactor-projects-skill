const db = require('../config/database');

class EnrollmentModel {
    constructor(connection) {
        this.connection = connection;
    }

    create(userId, courseId) {
        return db.run(this.connection, "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, courseId]);
    }

    findByCourseId(courseId) {
        return db.all(this.connection, "SELECT * FROM enrollments WHERE course_id = ?", [courseId]);
    }
}

module.exports = EnrollmentModel;
