class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    deleteUser(id) {
        return this.userModel.deleteById(id);
    }
}

module.exports = UserController;
