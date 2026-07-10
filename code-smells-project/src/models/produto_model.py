from src.database import get_db

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


class ProdutoModel:
    def _row_to_dict(self, row):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"],
        }

    def get_todos(self):
        db = get_db()
        rows = db.execute("SELECT * FROM produtos").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_por_id(self, produto_id):
        db = get_db()
        row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = get_db()
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        db.commit()

    def deletar(self, produto_id):
        db = get_db()
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        db = get_db()
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = db.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def count(self):
        db = get_db()
        return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
