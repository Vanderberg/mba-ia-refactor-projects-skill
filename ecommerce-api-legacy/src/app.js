const express = require('express');

const config = require('./config');
const { createConnection, initSchema } = require('./config/database');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const createCheckoutRoutes = require('./routes/checkoutRoutes');
const createReportRoutes = require('./routes/reportRoutes');
const createUserRoutes = require('./routes/userRoutes');

const errorHandler = require('./middlewares/errorHandler');
const { hashPassword } = require('./utils/passwordHasher');
const logger = require('./utils/logger');

async function createApp() {
    const app = express();
    app.use(express.json());

    const connection = createConnection();
    await initSchema(connection);

    const userModel = new UserModel(connection);
    const courseModel = new CourseModel(connection);
    const enrollmentModel = new EnrollmentModel(connection);
    const paymentModel = new PaymentModel(connection);
    const auditLogModel = new AuditLogModel(connection);
    const reportModel = new ReportModel(connection);

    const checkoutController = new CheckoutController({
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        hashPassword,
        config,
        logger
    });
    const reportController = new ReportController({ reportModel });
    const userController = new UserController({ userModel });

    app.use('/api', createCheckoutRoutes(checkoutController));
    app.use('/api', createReportRoutes(reportController));
    app.use('/api', createUserRoutes(userController));

    app.use(errorHandler);

    return app;
}

if (require.main === module) {
    createApp().then((app) => {
        app.listen(config.port, () => {
            console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
        });
    });
}

module.exports = createApp;
