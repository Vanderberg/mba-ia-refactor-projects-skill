**A) Seção "Análise Manual":**

---

## Projeto 1 — `code-smells-project/` (Python/Flask — API de E-commerce)

Estrutura original: 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), ~800 linhas, sem nenhuma separação em camadas real (nomes de "controllers"/"models" existem, mas `models.py` concentra SQL cru, regra de negócio e formatação de todos os domínios).

| # | Severidade | Problema | Local |
|---|---|---|---|
| 1 | **CRITICAL** | SQL Injection generalizado — praticamente todas as queries são montadas por concatenação de string com input do usuário, sem parametrização | `models.py:28,48-50,58-61,68,92,109-111,126-129,140,148-151,163-166,174,188,220,279-281,291-297` |
| 2 | **CRITICAL** | Endpoints administrativos sem autenticação: `/admin/reset-db` apaga o banco inteiro e `/admin/query` executa **qualquer SQL arbitrário** enviado no corpo da requisição — RCE via SQL, sem login, sem role check | `app.py:47-78` |
| 3 | **CRITICAL** | Credenciais e segredos hardcoded e expostos: `SECRET_KEY` fixo no código e o endpoint `/health` devolve `secret_key` e `debug: true` na resposta JSON pública | `app.py:7-8`, `controllers.py:286-289` |
| 4 | **CRITICAL** | Senhas em texto puro: sem hashing em `criar_usuario`/`login_usuario`; `listar_usuarios` retorna o campo `senha` de todos os usuários na API pública | `models.py:72-87,105-120,122-131` |
| 5 | **HIGH** | God File / mistura de camadas: `models.py` concentra acesso a dados, regra de negócio (cálculo de total de pedido, desconto no relatório) e formatação de resposta para 4 domínios diferentes — impossível testar em isolamento | `models.py:1-315` |
| 6 | **MEDIUM** | N+1 queries: para montar a lista de pedidos, o código abre um cursor extra por pedido e mais um cursor por item do pedido dentro de loops aninhados | `models.py:171-201,203-233` |
| 7 | **MEDIUM** | Duplicação de lógica de validação: os blocos de validação de `nome`/`preco`/`estoque` em `criar_produto` e `atualizar_produto` são praticamente idênticos, copiados e colados | `controllers.py:24-58,64-96` |
| 8 | **LOW** | Uso de `print()` para logging de negócio e erros em vez de um logger configurável (`logging`) | `controllers.py:8,11,57,61,106,161,179,182,208-210,248-250` |
| 9 | **LOW** | Mensagens de erro internas (`str(e)`) vazadas diretamente na resposta HTTP, tanto em rotas de negócio quanto no `/admin/query` — vazamento de detalhes de implementação para o cliente | `controllers.py:10-12,21-22,...`, `app.py:77-78` |

**Justificativa:** este projeto é o caso mais grave dos três — é essencialmente um monolito de 4 arquivos sem qualquer fronteira de responsabilidade, com múltiplas vulnerabilidades de segurança exploráveis (SQLi e SQL arbitrário via endpoint), o que o torna o melhor "pior caso" para validar se a skill detecta problemas CRITICAL de segurança, não só de arquitetura.

---

## Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express — LMS com checkout)

Estrutura: `app.js` (bootstrap), `AppManager.js` (classe única que inicializa o banco, define TODAS as rotas via closures e contém a lógica de pagamento), `utils.js` (config + helpers). SQLite em memória.

| # | Severidade | Problema | Local |
|---|---|---|---|
| 1 | **CRITICAL** | Segredos hardcoded no código-fonte versionado: senha de banco, chave de gateway de pagamento (`pk_live_...`) e credencial de SMTP em texto puro | `src/utils.js:1-6` |
| 2 | **CRITICAL** | "Criptografia" de senha caseira e insegura: `badCrypto` apenas concatena 10.000 vezes trechos de Base64 da senha — não é um algoritmo de hash real, é reversível e trivialmente quebrável | `src/utils.js:16-22` |
| 3 | **CRITICAL** | Endpoints sem autenticação/autorização: `GET /api/admin/financial-report` (dados financeiros sensíveis) e `DELETE /api/users/:id` (exclusão de usuário) são públicos, sem checagem de sessão/role | `src/AppManager.js:87-118,120-127` |
| 4 | **HIGH** | God Class: `AppManager` concentra inicialização de schema, roteamento (Views), regra de negócio de checkout e acesso a dados — não há Model, Controller nem separação alguma; tudo roda em closures dentro do construtor | `src/AppManager.js:1-129` |
| 5 | **HIGH** | Simulação de pagamento sem gateway real: aprovação é decidida apenas por `cc.startsWith("4")`, e o número completo do cartão é logado em texto puro no console — grave violação de PCI-DSS mesmo em ambiente de exemplo | `src/AppManager.js:36-38` |
| 6 | **MEDIUM** | "Callback hell": lógica de checkout e do relatório financeiro usa callbacks aninhados em 4-5 níveis, com contadores manuais (`enrPending`, `coursesPending`) para sincronizar respostas assíncronas — alto risco de race condition e difícil manutenção | `src/AppManager.js:29-84,86-118` |
| 7 | **MEDIUM** | Integridade referencial quebrada por design: `DELETE /api/users/:id` remove o usuário mas deixa `enrollments` e `payments` órfãos — o próprio código reconhece isso na mensagem de resposta | `src/AppManager.js:120-127` |
| 8 | **LOW** | Persistência inexistente: banco SQLite `:memory:` — todo o histórico de matrículas/pagamentos é perdido a cada restart do processo | `src/AppManager.js:7` |
| 9 | **LOW** | Nomenclatura pouco descritiva de variáveis de domínio (`u`, `e`, `p`, `cid`, `cc` para usuário, email, senha, curso, cartão) dificultando leitura do fluxo de checkout | `src/AppManager.js:24-28` |

**Justificativa:** apesar de usar uma stack totalmente diferente (Node/Express, callback-based, sem framework de rotas explícito), o projeto reproduz o mesmo padrão de "tudo em uma classe" do Projeto 1, mas com problemas específicos de JS assíncrono (callback hell) — útil para validar que a skill não depende de sintaxe Python/Flask para detectar violações de MVC.

---

## Projeto 3 — `task-manager-api/` (Python/Flask — Task Manager, parcialmente organizado)

Estrutura: já possui `models/`, `routes/` (blueprints), `services/`, `utils/` — aparenta seguir camadas, mas as rotas (que deveriam ser "Views/Controllers finos") concentram lógica de negócio, agregação de relatórios e serialização manual, e há falhas de segurança mesmo com a separação física de pastas.

| # | Severidade | Problema | Local |
|---|---|---|---|
| 1 | **HIGH** | Hashing de senha com MD5, sem salt — algoritmo obsoleto e criptograficamente quebrado para senhas, reversível via rainbow tables | `models/user.py:113-118` |
| 2 | **HIGH** | Autenticação falsa: `/login` retorna um "token" que é apenas a string `'fake-jwt-token-' + id`, sem assinatura nem expiração; nenhuma rota valida esse token — todos os endpoints (incluindo `DELETE /users/:id`) são publicamente acessíveis sem sessão real | `routes/user_routes.py:842-868` |
| 3 | **HIGH** | Lógica de negócio vazando para as rotas (violação de separação Controller/Service): cálculo de "overdue", agregações de relatório e regras de validação estão implementadas diretamente dentro dos handlers Flask em vez de nos `services/`, mesmo o projeto já tendo uma camada de `services/` disponível | `routes/task_routes.py:367-419`, `routes/report_routes.py:143-232` |
| 4 | **MEDIUM** | N+1 queries: `get_tasks` faz um `User.query.get()` e um `Category.query.get()` por task dentro do loop, e `summary_report` roda uma query de tasks por usuário dentro de outro loop, em vez de usar `join`/eager loading | `routes/task_routes.py:397-413`, `routes/report_routes.py:184-199` |
| 5 | **MEDIUM** | Duplicação da regra "task está atrasada" copiada e colada em pelo menos 4 lugares diferentes, apesar de já existir `Task.is_overdue()` pronto no model e nunca ser chamado | `models/task.py:74-84` vs. `routes/task_routes.py:386-395,427-436`, `routes/user_routes.py:828-837`, `routes/report_routes.py:164-174,263-266` |
| 6 | **LOW** | Vazamento de dado sensível na serialização: `User.to_dict()` inclui o hash da senha, retornado por `GET /users`, `GET /users/:id` e `/login` | `models/user.py:102-111` |
| 7 | **LOW** | Segredos hardcoded de menor exposição: `SECRET_KEY` do Flask e credenciais SMTP fixas no código-fonte | `app.py:13`, `services/notification_service.py:882-883` |
| 8 | **LOW** | `except:` genérico (bare except) em várias rotas, mascarando qualquer exceção — inclusive erros de programação — como um erro 500 genérico | `routes/task_routes.py:418,592-594`, `routes/user_routes.py:786-789,806-808` |


**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou
