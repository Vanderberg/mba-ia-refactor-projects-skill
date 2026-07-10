from flask import jsonify


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"erro": str(e), "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_generic(e):
        return jsonify({"erro": str(e)}), 500
