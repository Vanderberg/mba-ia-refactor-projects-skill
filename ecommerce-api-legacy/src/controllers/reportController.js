class ReportController {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    getFinancialReport() {
        return this.reportModel.getFinancialReport();
    }
}

module.exports = ReportController;
