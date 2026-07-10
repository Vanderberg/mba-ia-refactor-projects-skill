from flask import Flask, jsonify
from flask_cors import CORS

from src.config import settings
from src import database
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.models.pedido_model import PedidoModel
from src.controllers.produto_controller import ProdutoController
from src.controllers.usuario_controller import UsuarioController
from src.controllers.pedido_controller import PedidoController
from src.routes import produto_routes, usuario_routes, pedido_routes
from src.middlewares.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    database.init_db()
    database.init_app(app)

    produto_model = ProdutoModel()
    usuario_model = UsuarioModel()
    pedido_model = PedidoModel()

    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(pedido_model)

    app.register_blueprint(produto_routes.create_blueprint(produto_controller))
    app.register_blueprint(usuario_routes.create_blueprint(usuario_controller))
    app.register_blueprint(pedido_routes.create_blueprint(pedido_controller))

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            }
        })

    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produto_model.count(),
                "usuarios": usuario_model.count(),
                "pedidos": pedido_model.count(),
            },
            "versao": "1.0.0",
        }), 200

    register_error_handlers(app)
    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
