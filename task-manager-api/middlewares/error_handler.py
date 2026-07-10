from flask import jsonify
from werkzeug.exceptions import HTTPException
from middlewares.errors import AppError


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        app.logger.exception(err)
        return jsonify({'error': 'Erro interno'}), 500
