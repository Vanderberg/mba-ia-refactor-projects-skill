from src.middlewares.error_handler import NotFoundError, ValidationError


class UsuarioController:
    def __init__(self, usuario_model):
        self.model = usuario_model

    def listar(self):
        return self.model.get_todos()

    def buscar_por_id(self, usuario_id):
        usuario = self.model.get_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        return self.model.criar(nome, email, senha)

    def login(self, dados):
        if not dados:
            raise ValidationError("Payload JSON inválido")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        return self.model.autenticar(email, senha)
