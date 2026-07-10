from flask import Blueprint, jsonify, request


def create_blueprint(controller):
    bp = Blueprint("produtos", __name__)

    @bp.route("/produtos", methods=["GET"])
    def listar():
        produtos = controller.listar()
        return jsonify({"dados": produtos, "sucesso": True}), 200

    @bp.route("/produtos/busca", methods=["GET"])
    def buscar():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria")
        preco_min = request.args.get("preco_min")
        preco_max = request.args.get("preco_max")
        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)
        resultados = controller.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.route("/produtos/<int:produto_id>", methods=["GET"])
    def buscar_por_id(produto_id):
        produto = controller.buscar_por_id(produto_id)
        return jsonify({"dados": produto, "sucesso": True}), 200

    @bp.route("/produtos", methods=["POST"])
    def criar():
        dados = request.get_json()
        produto_id = controller.criar(dados)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.route("/produtos/<int:produto_id>", methods=["PUT"])
    def atualizar(produto_id):
        dados = request.get_json()
        controller.atualizar(produto_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
    def deletar(produto_id):
        controller.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
