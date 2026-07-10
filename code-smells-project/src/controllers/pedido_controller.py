from src.middlewares.error_handler import ValidationError

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

DESCONTO_TIER_ALTO = 10000
DESCONTO_TIER_MEDIO = 5000
DESCONTO_TIER_BAIXO = 1000
TAXA_DESCONTO_ALTO = 0.10
TAXA_DESCONTO_MEDIO = 0.05
TAXA_DESCONTO_BAIXO = 0.02


class PedidoController:
    def __init__(self, pedido_model):
        self.model = pedido_model

    def criar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        resultado = self.model.criar(usuario_id, itens)
        if "erro" in resultado:
            raise ValidationError(resultado["erro"])
        print(f"ENVIANDO EMAIL: Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
        print("ENVIANDO SMS: Seu pedido foi recebido!")
        print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
        return resultado

    def listar_por_usuario(self, usuario_id):
        return self.model.get_por_usuario(usuario_id)

    def listar_todos(self):
        return self.model.get_todos()

    def atualizar_status(self, pedido_id, dados):
        if not dados:
            raise ValidationError("Payload JSON inválido")
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        self.model.atualizar_status(pedido_id, novo_status)
        if novo_status == "aprovado":
            print(f"NOTIFICAÇÃO: Pedido {pedido_id} foi aprovado! Preparar envio.")
        if novo_status == "cancelado":
            print(f"NOTIFICAÇÃO: Pedido {pedido_id} cancelado. Devolver estoque.")

    def relatorio_vendas(self):
        dados = self.model.relatorio_vendas()
        faturamento = dados["faturamento_bruto"]
        if faturamento > DESCONTO_TIER_ALTO:
            desconto = faturamento * TAXA_DESCONTO_ALTO
        elif faturamento > DESCONTO_TIER_MEDIO:
            desconto = faturamento * TAXA_DESCONTO_MEDIO
        elif faturamento > DESCONTO_TIER_BAIXO:
            desconto = faturamento * TAXA_DESCONTO_BAIXO
        else:
            desconto = 0
        total_pedidos = dados["total_pedidos"]
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": dados["pedidos_pendentes"],
            "pedidos_aprovados": dados["pedidos_aprovados"],
            "pedidos_cancelados": dados["pedidos_cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
