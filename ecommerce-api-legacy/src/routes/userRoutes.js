const express = require('express');

function createUserRoutes(userController) {
    const router = express.Router();

    router.delete('/users/:id', async (req, res, next) => {
        try {
            await userController.deleteUser(req.params.id);
            res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = createUserRoutes;
