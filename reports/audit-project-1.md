================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] SQL Injection por concatenação de strings
File: models.py:28, 47-50, 57-63, 68, 92, 109-111, 126-129, 140-166, 174, 188, 192, 220, 224, 279-282, 290-297
Description: Todas as queries do projeto são montadas por concatenação direta de strings com valores recebidos como parâmetros de função (vindo originalmente de request), sem uso de placeholders parametrizados. Exemplos: `"SELECT * FROM produtos WHERE id = " + str(id)` (linha 28), `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (linhas 109-111), e o caso mais grave: `buscar_produtos` (linhas 290-297) monta uma query inteira com `termo`, `categoria`, `preco_min` e `preco_max` vindos diretamente de query string via request.
Impact: Permite injeção arbitrária de SQL via qualquer parâmetro de entrada. O endpoint de busca e o de login são os vetores de ataque mais diretos — um payload como `' OR '1'='1` no campo email bypassa autenticação completamente.
Recommendation: Reescrever todas as queries usando placeholders do driver SQLite (`?`) com passagem de parâmetros como tupla: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

### [CRITICAL] Credenciais hardcoded e expostas na resposta da API
File: app.py:7 | controllers.py:285-290
Description: A SECRET_KEY da aplicação está hardcoded em app.py linha 7 (`"minha-chave-super-secreta-123"`). O mesmo valor é exposto publicamente na resposta JSON do endpoint `GET /health` em controllers.py linha 289 (`"secret_key": "minha-chave-super-secreta-123"`), junto com `"db_path"` e `"debug": True`. Não existe arquivo `.env.example` nem leitura via `os.environ`.
Impact: Qualquer consumidor do endpoint `/health` recebe a chave secreta da aplicação em texto plano, viabilizando falsificação de sessões e tokens.
Recommendation: Mover `SECRET_KEY` e `db_path` para variáveis de ambiente lidas via `os.environ.get()`; criar `.env.example`; remover todos os campos sensíveis da resposta do health check.

### [CRITICAL] Endpoint de execução arbitrária de SQL sem autenticação
File: app.py:59-78
Description: O endpoint `POST /admin/query` aceita um campo `"sql"` no corpo da requisição e o executa diretamente no banco de dados sem qualquer autenticação, autorização ou validação do conteúdo. Qualquer cliente HTTP pode enviar `DROP TABLE usuarios` ou `SELECT * FROM usuarios` e o servidor executa.
Impact: Exposição total de todos os dados do banco e possibilidade de destruição irreversível de dados por qualquer agente externo sem credenciais.
Recommendation: Remover o endpoint completamente. Se funcionalidade de diagnóstico for necessária, implementar via CLI local com autenticação de sistema operacional, nunca exposta via HTTP.

### [HIGH] Lógica de negócio em controllers e models fora de uma camada de serviço
File: controllers.py:43-54 | controllers.py:241-251 | models.py:256-262
Description: (a) `criar_produto` em controllers.py (linhas 43-54) implementa regras de domínio inline: limites de tamanho de nome (2-200 chars), validação de preço e estoque não-negativos, e lista hardcoded de categorias válidas. (b) `atualizar_status_pedido` (linhas 241-251) emite "notificações" (print de email/SMS/push) diretamente no controller. (c) `relatorio_vendas` em models.py (linhas 256-262) calcula descontos escalonados por faturamento total — regra de negócio pura misturada com acesso a dados.
Impact: Controllers e models acumulam responsabilidades incompatíveis; qualquer mudança de regra de negócio exige editar múltiplas camadas simultaneamente, e a lógica não pode ser testada isoladamente.
Recommendation: Extrair regras de domínio (validações, cálculos, notificações) para uma camada de serviço (`src/services/`) separada de controllers (orquestração HTTP) e models (acesso a dados).

### [HIGH] Estado global mutável: conexão SQLite singleton não thread-safe
File: database.py:4-10
Description: A variável global `db_connection = None` (linha 4) armazena uma única conexão SQLite reutilizada em todas as requisições. Embora inicializada com `check_same_thread=False`, uma conexão SQLite compartilhada entre threads sem lock externo pode corromper dados em escrita concorrente. Adicionalmente, o padrão singleton dificulta qualquer substituição em testes.
Impact: Em ambiente com mais de uma thread (modo `debug=True` do Flask já usa threading), escritas concorrentes podem resultar em "database is locked" ou corrupção silenciosa de dados.
Recommendation: Usar `flask.g` para armazenar a conexão por requisição (`g.db = sqlite3.connect(...)`, fechada no `teardown_appcontext`), ou migrar para SQLAlchemy com pool gerenciado.

### [HIGH] Acoplamento direto ao banco em health_check, bypassing a camada de models
File: controllers.py:264-292
Description: `health_check` chama `get_db()` diretamente (linha 266) e executa 4 queries SQL inline (linhas 268-274), ignorando completamente a camada de models que já encapsula o acesso ao banco para as entidades produtos, usuários e pedidos.
Impact: Viola a separação de camadas estabelecida pelo restante do projeto; qualquer mudança de schema ou de driver de banco exige editar também este controller diretamente.
Recommendation: Expor métodos de contagem nos respectivos models (ex.: `ProdutoModel.count()`) e chamá-los a partir do controller, ou mover o health check para um blueprint de diagnóstico com sua própria camada de acesso.

### [MEDIUM] Queries N+1 na listagem de pedidos
File: models.py:171-200 | models.py:203-232
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam, para cada pedido retornado: (1) uma query em `itens_pedido` e (2) uma query por item em `produtos` para buscar o nome. Para N pedidos com M itens cada, isso resulta em 1 + N + N×M queries ao banco. O padrão é idêntico nas duas funções (código duplicado).
Impact: Degradação de performance proporcional ao volume de dados; 10 pedidos com 3 itens cada geram 41 queries onde bastaria 1 JOIN.
Recommendation: Substituir por uma única query com JOIN entre `pedidos`, `itens_pedido` e `produtos`, retornando todas as colunas necessárias de uma vez. Eliminar a duplicação extraindo a query para uma função privada única.

### [MEDIUM] Validação ausente no payload de login e atualização de status
File: controllers.py:168-186 | controllers.py:237-255
Description: Em `login` (linha 169), `dados = request.get_json()` é chamado sem verificar se o retorno é `None` (ocorre quando o Content-Type não é `application/json` ou o body está malformado). A linha seguinte `dados.get("email", "")` lança `AttributeError` com status 500 em vez de 400. O mesmo padrão ocorre em `atualizar_status_pedido` (linha 240).
Impact: Requisições malformadas causam erro 500 (Internal Server Error) expondo stack traces em vez de retornar 400 (Bad Request) com mensagem clara.
Recommendation: Adicionar verificação `if not dados: return jsonify({"erro": "Payload JSON inválido"}), 400` imediatamente após `get_json()` em ambas as funções.

### [LOW] Magic numbers e strings em regras de negócio
File: controllers.py:48-54 | models.py:257-261
Description: Limites de negócio aparecem como literais sem nome: `len(nome) < 2`, `len(nome) > 200` (controllers.py:48-49); lista de categorias inline `["informatica", "moveis", ...]` (linha 52); limiares de desconto `10000`, `5000`, `1000` e taxas `0.1`, `0.05`, `0.02` (models.py:257-261).
Impact: Alterar qualquer regra exige busca manual por literais espalhados; risco de inconsistência se o mesmo valor aparecer em múltiplos lugares.
Recommendation: Extrair para constantes nomeadas em um módulo de config ou domínio (`NOME_MAX_LEN`, `CATEGORIAS_VALIDAS`, `DESCONTO_TIER_1`, etc.).

### [LOW] Redefinição do built-in `id` como nome de variável
File: controllers.py:56-57 | models.py:24, 43, 54, 65, 89, 92
Description: O nome `id` é usado como parâmetro e variável local em múltiplas funções (`criar_produto`, `atualizar_produto`, `deletar_produto`, `get_produto_por_id`, etc.), sobrescrevendo o built-in `id()` do Python dentro desses escopos.
Impact: Baixo risco prático no código atual, mas pode causar bugs sutis se alguém precisar usar `id()` dentro das mesmas funções no futuro.
Recommendation: Renomear para `produto_id`, `usuario_id`, `pedido_id` — nomes descritivos do domínio que também eliminam a ambiguidade.

================================
Total: 10 findings
================================
