================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.x + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Credenciais/config sensível hardcoded
File: app.py:11-13
Description: `SQLALCHEMY_DATABASE_URI` e `SECRET_KEY` estão escritos diretamente no código-fonte (`'super-secret-key-123'`), sem leitura de variável de ambiente nem arquivo `.env.example`.
Impact: A `SECRET_KEY` fica exposta em qualquer cópia do repositório/histórico git, comprometendo assinatura de sessão/cookies; a URI do banco fica fixa impedindo configuração por ambiente (dev/staging/prod).
Recommendation: Mover ambos os valores para variáveis de ambiente carregadas via `python-dotenv` em um módulo de config central; criar `.env.example` documentando as chaves sem valores reais.

### [CRITICAL] Credenciais SMTP hardcoded
File: services/notification_service.py:7-10
Description: Host, porta, usuário e senha do servidor SMTP (`self.email_password = 'senha123'`) estão fixos no construtor de `NotificationService`.
Impact: Vazamento de credenciais de e-mail em texto plano no repositório, permitindo uso indevido da conta de envio.
Recommendation: Mover todas as credenciais para variáveis de ambiente injetadas na construção do serviço, documentadas em `.env.example`.

### [CRITICAL] Hash de senha inseguro (MD5 sem salt)
File: models/user.py:27-32
Description: `set_password`/`check_password` usam `hashlib.md5` puro, sem salt, para armazenar e comparar senhas de usuário.
Impact: MD5 é criptograficamente quebrado e sujeito a rainbow tables; um vazamento do banco expõe todas as senhas dos usuários rapidamente.
Recommendation: Substituir por um algoritmo de hashing para senhas (`werkzeug.security.generate_password_hash`/`check_password_hash`, ou `bcrypt`), preservando a mesma interface `set_password`/`check_password`.

### [HIGH] Lógica de negócio duplicada em múltiplas rotas (cálculo de "overdue")
File: routes/task_routes.py:30-39
Description: O cálculo de "task atrasada" (`due_date < utcnow() and status not in ('done','cancelled')`) é reimplementado manualmente em routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/user_routes.py:171-180, routes/report_routes.py:34-37 e routes/report_routes.py:132-135 — apesar de já existir `Task.is_overdue()` em models/task.py:50-60, que nunca é chamado.
Impact: Qualquer mudança na regra de negócio (ex.: novo status terminal) exige editar 5 lugares distintos; alto risco de divergência e bugs de manutenção.
Recommendation: Remover as reimplementações e chamar `task.is_overdue()` em todos os pontos, centralizando a regra no model.

### [HIGH] Rotas concentrando serialização manual, orquestração e N+1 em vez de controller
File: routes/task_routes.py:11-63
Description: `get_tasks` monta cada campo de resposta manualmente campo a campo (duplicando `Task.to_dict()`), recalcula overdue, e para cada task executa `User.query.get()`/`Category.query.get()` dentro do laço, tudo dentro do handler de rota, sem nenhuma camada de controller intermediária.
Impact: Rota mistura apresentação HTTP, orquestração entre 3 models e regra de negócio; impossível reutilizar ou testar a lógica isoladamente da camada HTTP.
Recommendation: Extrair a montagem/orquestração para um controller (`TaskController.list_tasks`) que devolve dados prontos; a rota deve só chamar o controller e serializar a resposta.

### [MEDIUM] Queries N+1
File: routes/report_routes.py:53-68
Description: `summary_report` itera sobre todos os usuários (`for u in users`) e, dentro do laço, executa `Task.query.filter_by(user_id=u.id).all()` para cada um — uma query adicional por usuário em vez de uma única query agregada.
Impact: Tempo de resposta degrada linearmente com o número de usuários; mesmo padrão existe em routes/task_routes.py:41-56 (query de `User`/`Category` por task dentro do laço de `get_tasks`).
Recommendation: Substituir por uma única query agregada (`GROUP BY user_id` com `func.count`) ou eager loading via relacionamento SQLAlchemy.

### [MEDIUM] Validação de payload ausente
File: routes/report_routes.py:190-202
Description: `update_category` chama `data = request.get_json()` e acessa `data['name']`/`data['description']`/`data['color']` sem checar se `data` é `None` (diferente de `create_category`, que faz essa checagem em report_routes.py:170-171).
Impact: Um PUT sem corpo JSON (ou `Content-Type` incorreto) causa `AttributeError` não tratado e retorna 500 em vez de 400.
Recommendation: Adicionar `if not data: return jsonify({'error': 'Dados inválidos'}), 400` no início do handler, como já é feito nos demais endpoints de escrita.

### [MEDIUM] Constantes de validação duplicadas e não reutilizadas
File: utils/helpers.py:110-116
Description: `utils/helpers.py` define `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` e `DEFAULT_COLOR`, além da função `process_task_data` (linhas 57-108) que as usaria — mas nada disso é importado em lugar nenhum. As rotas reimplementam os mesmos literais: lista `['pending', 'in_progress', 'done', 'cancelled']` aparece de novo em routes/task_routes.py:110 e :177, e os limites de título (3/200) são recopiados em routes/task_routes.py:96-100 e :167-170.
Impact: Duas fontes de verdade divergentes para as mesmas regras de validação; código morto (`process_task_data`) some sem uso e aumenta a superfície de manutenção.
Recommendation: Remover a duplicação, importando as constantes de `utils/helpers.py` (ou movendo-as para o model/controller de domínio) nos pontos onde a validação hoje é reescrita.

### [LOW] Uso de `datetime.utcnow()` (deprecated)
File: models/task.py:15-16
Description: `datetime.utcnow()` é usado como default de coluna e em `is_overdue()` (models/task.py:52); o mesmo padrão se repete em models/user.py:14 e em todas as rotas que calculam overdue. `datetime.utcnow()` está deprecated desde Python 3.12 em favor de `datetime.now(timezone.utc)`.
Impact: Código passará a emitir `DeprecationWarning` (ou quebrar em versões futuras do Python) sem que o requirements.txt fixe uma versão de Python compatível — verificar changelog da versão de Python usada em produção.
Recommendation: Substituir por `datetime.now(timezone.utc)` de forma centralizada, ajustando comparações que hoje assumem datetime naive.

### [LOW] Variáveis de uma letra em laços com lógica não trivial
File: routes/report_routes.py:55-68
Description: O laço de cálculo de produtividade por usuário usa `u` e `t` como nomes de variável (`for u in users`, `for t in user_tasks`) para acumular contadores de negócio, não apenas iteração trivial; o mesmo padrão se repete em routes/task_routes.py e routes/user_routes.py.
Impact: Reduz a legibilidade do bloco que calcula métricas de negócio, dificultando revisão e manutenção.
Recommendation: Renomear para `user`/`task` (ou equivalentes descritivos) nos laços que carregam lógica de domínio.

================================
Total: 10 findings
================================
