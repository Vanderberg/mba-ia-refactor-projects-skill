from flask import Blueprint, jsonify, request


def create_blueprint(controller):
    bp = Blueprint("pedidos", __name__)

    @bp.route("/pedidos", methods=["POST"])
    def criar():
        dados = request.get_json()
        resultado = controller.criar(dados)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @bp.route("/pedidos", methods=["GET"])
    def listar_todos():
        pedidos = controller.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
    def listar_por_usuario(usuario_id):
        pedidos = controller.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
    def atualizar_status(pedido_id):
        dados = request.get_json()
        controller.atualizar_status(pedido_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    @bp.route("/relatorios/vendas", methods=["GET"])
    def relatorio_vendas():
        relatorio = controller.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200

    return bp
