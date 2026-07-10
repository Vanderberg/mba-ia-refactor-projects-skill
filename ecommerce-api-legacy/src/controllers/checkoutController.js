const HttpError = require('../utils/httpError');

class CheckoutController {
    constructor({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, hashPassword, config, logger }) {
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.hashPassword = hashPassword;
        this.config = config;
        this.logger = logger;
    }

    async checkout({ username, email, password, courseId, cardNumber }) {
        let course;
        try {
            course = await this.courseModel.findActiveById(courseId);
        } catch (err) {
            course = null;
        }
        if (!course) throw new HttpError(404, 'Curso não encontrado');

        let user;
        try {
            user = await this.userModel.findByEmail(email);
        } catch (err) {
            throw new HttpError(500, 'Erro DB');
        }

        let userId;
        if (!user) {
            const passwordHash = this.hashPassword(password || '123456');
            let result;
            try {
                result = await this.userModel.create({ name: username, email, passwordHash });
            } catch (err) {
                throw new HttpError(500, 'Erro ao criar usuário');
            }
            userId = result.lastID;
        } else {
            userId = user.id;
        }

        console.log(`Processando cartão ${cardNumber} na chave ${this.config.paymentGatewayKey}`);
        const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
        if (status === 'DENIED') throw new HttpError(400, 'Pagamento recusado');

        let enrollment;
        try {
            enrollment = await this.enrollmentModel.create(userId, courseId);
        } catch (err) {
            throw new HttpError(500, 'Erro Matrícula');
        }
        const enrollmentId = enrollment.lastID;

        try {
            await this.paymentModel.create(enrollmentId, course.price, status);
        } catch (err) {
            throw new HttpError(500, 'Erro Pagamento');
        }

        try {
            await this.auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
        } catch (err) {
            // Preserva comportamento original: falha no audit log não bloqueia a resposta de sucesso.
        }

        this.logger.info(`Checkout registrado para usuário ${userId}: ${course.title}`);

        return { enrollmentId };
    }
}

module.exports = CheckoutController;
