const express = require('express');

function createReportRoutes(reportController) {
    const router = express.Router();

    router.get('/admin/financial-report', async (req, res, next) => {
        try {
            const report = await reportController.getFinancialReport();
            res.json(report);
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = createReportRoutes;
