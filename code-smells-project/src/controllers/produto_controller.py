from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models.produto_model import CATEGORIAS_VALIDAS

NOME_MIN_LEN = 2
NOME_MAX_LEN = 200


class ProdutoController:
    def __init__(self, produto_model):
        self.model = produto_model

    def listar(self):
        return self.model.get_todos()

    def buscar_por_id(self, produto_id):
        produto = self.model.get_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.model.buscar(termo, categoria, preco_min, preco_max)

    def _validar_dados(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")
        if "nome" not in dados:
            raise ValidationError("Nome é obrigatório")
        if "preco" not in dados:
            raise ValidationError("Preço é obrigatório")
        if "estoque" not in dados:
            raise ValidationError("Estoque é obrigatório")
        nome = dados["nome"]
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")
        if preco < 0:
            raise ValidationError("Preço não pode ser negativo")
        if estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")
        if len(nome) < NOME_MIN_LEN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_MAX_LEN:
            raise ValidationError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")
        return nome, dados.get("descricao", ""), preco, estoque, categoria

    def criar(self, dados):
        nome, descricao, preco, estoque, categoria = self._validar_dados(dados)
        return self.model.criar(nome, descricao, preco, estoque, categoria)

    def atualizar(self, produto_id, dados):
        if not self.model.get_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        nome, descricao, preco, estoque, categoria = self._validar_dados(dados)
        self.model.atualizar(produto_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, produto_id):
        if not self.model.get_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.model.deletar(produto_id)
