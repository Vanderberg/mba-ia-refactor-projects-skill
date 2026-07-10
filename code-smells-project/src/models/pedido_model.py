from src.database import get_db


class PedidoModel:
    _JOIN_QUERY = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
    """

    def _agrupar_pedidos(self, rows):
        pedidos = {}
        for row in rows:
            pid = row["id"]
            if pid not in pedidos:
                pedidos[pid] = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
            if row["produto_id"] is not None:
                pedidos[pid]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def criar(self, usuario_id, itens):
        db = get_db()
        total = 0
        for item in itens:
            row = db.execute(
                "SELECT * FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if row is None:
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if row["estoque"] < item["quantidade"]:
                return {"erro": f"Estoque insuficiente para {row['nome']}"}
            total += row["preco"] * item["quantidade"]

        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            preco_row = db.execute(
                "SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco_row["preco"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": total}

    def get_por_usuario(self, usuario_id):
        db = get_db()
        rows = db.execute(
            self._JOIN_QUERY + " WHERE p.usuario_id = ? ORDER BY p.id",
            (usuario_id,),
        ).fetchall()
        return self._agrupar_pedidos(rows)

    def get_todos(self):
        db = get_db()
        rows = db.execute(self._JOIN_QUERY + " ORDER BY p.id").fetchall()
        return self._agrupar_pedidos(rows)

    def atualizar_status(self, pedido_id, novo_status):
        db = get_db()
        db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )
        db.commit()

    def relatorio_vendas(self):
        db = get_db()
        total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
        pendentes = db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",)
        ).fetchone()[0]
        aprovados = db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",)
        ).fetchone()[0]
        cancelados = db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",)
        ).fetchone()[0]
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": faturamento,
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
        }

    def count(self):
        db = get_db()
        return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
