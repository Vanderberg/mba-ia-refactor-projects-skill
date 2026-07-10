from src.database import get_db


class UsuarioModel:
    def _row_to_dict(self, row, include_senha=False):
        d = {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"],
        }
        if include_senha:
            d["senha"] = row["senha"]
        return d

    def get_todos(self):
        db = get_db()
        rows = db.execute("SELECT * FROM usuarios").fetchall()
        return [self._row_to_dict(r, include_senha=True) for r in rows]

    def get_por_id(self, usuario_id):
        db = get_db()
        row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return self._row_to_dict(row, include_senha=True) if row else None

    def criar(self, nome, email, senha, tipo="cliente"):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha, tipo),
        )
        db.commit()
        return cursor.lastrowid

    def autenticar(self, email, senha):
        db = get_db()
        row = db.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
            (email, senha),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def count(self):
        db = get_db()
        return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
