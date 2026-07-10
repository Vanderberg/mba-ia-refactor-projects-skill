# Refactoring Playbook (Fase 3)

Padrões de transformação para corrigir cada anti-pattern do catálogo (`references/antipatterns-catalog.md`). Cada padrão mostra um exemplo antes/depois em Flask e/ou Express; generalize o princípio para a stack real do projeto.

## 1. God Class → separação em models + controllers por domínio

Ligado a: *God Class / God Method (CRITICAL)*.

**Antes (Flask, tudo em app.py):**
```python
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = sqlite3.connect("app.db")
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    total = sum(item["price"] * item["qty"] for item in get_items(order_id))
    return jsonify({"id": row[0], "total": total})
```

**Depois:**
```python
# src/models/order_model.py
class OrderModel:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, order_id):
        return self.db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def get_items(self, order_id):
        return self.db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()

# src/controllers/order_controller.py
class OrderController:
    def __init__(self, order_model):
        self.order_model = order_model

    def get_order_summary(self, order_id):
        order = self.order_model.get_by_id(order_id)
        items = self.order_model.get_items(order_id)
        total = sum(item["price"] * item["qty"] for item in items)
        return {"id": order["id"], "total": total}

# src/routes/order_routes.py
@order_bp.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    return jsonify(order_controller.get_order_summary(order_id))
```

## 2. Secrets hardcoded → módulo de config com variáveis de ambiente

Ligado a: *Credenciais/secrets hardcoded (CRITICAL)*.

**Antes:**
```python
DB_URI = "postgresql://admin:supersecret123@localhost/shop"
```

**Depois:**
```python
# src/config/settings.py
import os

DB_URI = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
```
```
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/shop
SECRET_KEY=change-me
```

## 3. SQL por concatenação → queries parametrizadas

Ligado a: *SQL Injection por concatenação de strings (CRITICAL)*.

**Antes (Express):**
```js
app.get("/users", (req, res) => {
  const query = `SELECT * FROM users WHERE name = '${req.query.name}'`;
  db.query(query, (err, rows) => res.json(rows));
});
```

**Depois:**
```js
app.get("/users", (req, res) => {
  db.query("SELECT * FROM users WHERE name = ?", [req.query.name], (err, rows) => {
    res.json(rows);
  });
});
```

## 4. Lógica de negócio em rota → extração para controller

Ligado a: *Lógica de negócio em rotas/controllers (HIGH)*.

**Antes (Flask):**
```python
@app.route("/checkout", methods=["POST"])
def checkout():
    cart = request.json["items"]
    total = 0
    for item in cart:
        total += item["price"] * item["qty"]
        if item["qty"] > item["stock"]:
            return jsonify({"error": "out of stock"}), 400
    total *= 0.9 if len(cart) > 5 else 1
    return jsonify({"total": total})
```

**Depois:**
```python
# src/controllers/checkout_controller.py
class CheckoutController:
    BULK_DISCOUNT_THRESHOLD = 5
    BULK_DISCOUNT_RATE = 0.9

    def calculate_total(self, cart_items):
        for item in cart_items:
            if item["qty"] > item["stock"]:
                raise OutOfStockError(item)
        total = sum(item["price"] * item["qty"] for item in cart_items)
        if len(cart_items) > self.BULK_DISCOUNT_THRESHOLD:
            total *= self.BULK_DISCOUNT_RATE
        return total

# src/routes/checkout_routes.py
@checkout_bp.route("/checkout", methods=["POST"])
def checkout():
    try:
        total = checkout_controller.calculate_total(request.json["items"])
        return jsonify({"total": total})
    except OutOfStockError as e:
        return jsonify({"error": "out of stock"}), 400
```

## 5. Acesso direto ao banco na rota → abstração em model

Ligado a: *God Class* e *Forte acoplamento sem injeção de dependência (HIGH)*.

**Antes (Express):**
```js
router.get("/products/:id", (req, res) => {
  db.query("SELECT * FROM products WHERE id = ?", [req.params.id], (err, rows) => {
    res.json(rows[0]);
  });
});
```

**Depois:**
```js
// src/models/productModel.js
class ProductModel {
  constructor(db) { this.db = db; }
  findById(id) {
    return new Promise((resolve, reject) => {
      this.db.query("SELECT * FROM products WHERE id = ?", [id], (err, rows) => {
        err ? reject(err) : resolve(rows[0]);
      });
    });
  }
}

// src/controllers/productController.js
class ProductController {
  constructor(productModel) { this.productModel = productModel; }
  async getById(req, res) {
    const product = await this.productModel.findById(req.params.id);
    res.json(product);
  }
}

// src/routes/productRoutes.js
router.get("/products/:id", (req, res) => productController.getById(req, res));
```

## 6. Estado global mutável → injeção de dependência / factory

Ligado a: *Estado global mutável (HIGH)*.

**Antes:**
```python
orders = []  # "banco" em memória, mutado por múltiplas rotas

@app.route("/orders", methods=["POST"])
def create_order():
    orders.append(request.json)
    return jsonify(request.json), 201
```

**Depois:**
```python
# src/models/order_model.py
class OrderModel:
    def __init__(self, db):
        self.db = db

    def create(self, order_data):
        return self.db.execute(
            "INSERT INTO orders (customer, total) VALUES (?, ?)",
            (order_data["customer"], order_data["total"]),
        )

# src/app.py (composition root)
def create_app():
    db = connect_db(settings.DB_URI)
    order_model = OrderModel(db)
    order_controller = OrderController(order_model)
    register_order_routes(app, order_controller)
    return app
```

## 7. Error handling espalhado → middleware/handler centralizado

Ligado a: *God Class* e organização geral de camadas.

**Antes (Express, try/catch repetido em cada rota):**
```js
router.get("/orders/:id", async (req, res) => {
  try {
    const order = await orderModel.findById(req.params.id);
    res.json(order);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

**Depois:**
```js
// src/middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  res.status(status).json({ error: err.message });
}

// src/routes/orderRoutes.js
router.get("/orders/:id", async (req, res, next) => {
  try {
    res.json(await orderModel.findById(req.params.id));
  } catch (e) {
    next(e);
  }
});

// composition root
app.use(errorHandler);
```

## 8. API deprecated → substituição pelo equivalente moderno

Ligado a: *APIs deprecated (MEDIUM/HIGH)*.

**Antes (Flask):**
```python
@app.before_first_request
def setup():
    init_db()
```

**Depois:**
```python
def create_app():
    app = Flask(__name__)
    init_db()  # executado uma vez no composition root, não em hook deprecated
    return app
```

**Antes (Python, datetime deprecated):**
```python
created_at = datetime.utcnow()
```

**Depois:**
```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

## 9. Queries N+1 → carregamento em lote/JOIN

Ligado a: *Queries N+1 (MEDIUM)*.

**Antes:**
```python
posts = db.execute("SELECT * FROM posts").fetchall()
for post in posts:
    post["author"] = db.execute(
        "SELECT * FROM users WHERE id = ?", (post["author_id"],)
    ).fetchone()
```

**Depois:**
```python
rows = db.execute("""
    SELECT posts.*, users.name AS author_name
    FROM posts JOIN users ON posts.author_id = users.id
""").fetchall()
```

## 10. Validação ausente → camada de validação na entrada da rota

Ligado a: *Validações ausentes nas rotas (MEDIUM)*.

**Antes:**
```python
@app.route("/products", methods=["POST"])
def create_product():
    name = request.json["name"]  # KeyError se ausente
    price = request.json["price"]
    ...
```

**Depois:**
```python
from pydantic import BaseModel

class ProductInput(BaseModel):
    name: str
    price: float

@app.route("/products", methods=["POST"])
def create_product():
    try:
        data = ProductInput(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    return jsonify(product_controller.create(data))
```
