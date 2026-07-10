from flask import Blueprint, jsonify, request


def create_blueprint(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.route("/usuarios", methods=["GET"])
    def listar():
        usuarios = controller.listar()
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    @bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
    def buscar_por_id(usuario_id):
        usuario = controller.buscar_por_id(usuario_id)
        return jsonify({"dados": usuario, "sucesso": True}), 200

    @bp.route("/usuarios", methods=["POST"])
    def criar():
        dados = request.get_json()
        usuario_id = controller.criar(dados)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @bp.route("/login", methods=["POST"])
    def login():
        dados = request.get_json()
        usuario = controller.login(dados)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    return bp
