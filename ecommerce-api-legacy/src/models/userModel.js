const db = require('../config/database');

class UserModel {
    constructor(connection) {
        this.connection = connection;
    }

    findByEmail(email) {
        return db.get(this.connection, "SELECT id FROM users WHERE email = ?", [email]);
    }

    findById(id) {
        return db.get(this.connection, "SELECT name, email FROM users WHERE id = ?", [id]);
    }

    create({ name, email, passwordHash }) {
        return db.run(this.connection, "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, passwordHash]);
    }

    deleteById(id) {
        return db.run(this.connection, "DELETE FROM users WHERE id = ?", [id]);
    }
}

module.exports = UserModel;
