const db = require('../config/database');

class ReportModel {
    constructor(connection) {
        this.connection = connection;
    }

    async getFinancialReport() {
        const rows = await db.all(this.connection, `
            SELECT courses.id AS course_id,
                   courses.title AS course_title,
                   enrollments.id AS enrollment_id,
                   users.name AS student_name,
                   payments.amount AS paid_amount,
                   payments.status AS payment_status
            FROM courses
            LEFT JOIN enrollments ON enrollments.course_id = courses.id
            LEFT JOIN users ON users.id = enrollments.user_id
            LEFT JOIN payments ON payments.enrollment_id = enrollments.id
            ORDER BY courses.id, enrollments.id
        `, []);

        const reportByCourseId = new Map();

        for (const row of rows) {
            if (!reportByCourseId.has(row.course_id)) {
                reportByCourseId.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }

            if (row.enrollment_id === null) continue;

            const courseData = reportByCourseId.get(row.course_id);

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.paid_amount;
            }

            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.paid_amount || 0
            });
        }

        return Array.from(reportByCourseId.values());
    }
}

module.exports = ReportModel;
