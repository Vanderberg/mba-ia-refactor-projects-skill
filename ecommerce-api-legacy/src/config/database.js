const sqlite3 = require('sqlite3').verbose();

function createConnection() {
    return new sqlite3.Database(':memory:');
}

function run(connection, sql, params = []) {
    return new Promise((resolve, reject) => {
        connection.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(connection, sql, params = []) {
    return new Promise((resolve, reject) => {
        connection.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(connection, sql, params = []) {
    return new Promise((resolve, reject) => {
        connection.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

function initSchema(connection) {
    return new Promise((resolve, reject) => {
        connection.serialize(() => {
            connection.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
            connection.run("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
            connection.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
            connection.run("CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
            connection.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");

            connection.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
            connection.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
            connection.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
            connection.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')", (err) => {
                if (err) return reject(err);
                resolve();
            });
        });
    });
}

module.exports = { createConnection, run, get, all, initSchema };
