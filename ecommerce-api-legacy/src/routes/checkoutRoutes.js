const express = require('express');

function createCheckoutRoutes(checkoutController) {
    const router = express.Router();

    router.post('/checkout', async (req, res, next) => {
        try {
            const { usr, eml, pwd, c_id, card } = req.body;

            if (!usr || !eml || !c_id || !card) {
                return res.status(400).send('Bad Request');
            }

            const result = await checkoutController.checkout({
                username: usr,
                email: eml,
                password: pwd,
                courseId: c_id,
                cardNumber: card
            });

            res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = createCheckoutRoutes;
