function errorHandler(err, req, res, next) {
    const statusCode = err.statusCode || 500;
    res.status(statusCode).send(err.message || 'Erro interno');
}

module.exports = errorHandler;
