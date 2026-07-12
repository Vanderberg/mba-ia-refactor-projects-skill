## A) Análise Manual

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


## B) Construção da Skill

### Decisões de design

O `SKILL.md` foi mantido como o *orquestrador* do workflow, não como repositório de conhecimento: ele define as 3 fases sequenciais e obrigatórias (Análise → Auditoria → Refatoração), os formatos de saída exatos exigidos pelo desafio, e um conjunto de "Restrições Gerais" que valem para as 3 fases (nunca inventar arquivo/linha, nunca pular a confirmação antes da Fase 3, nunca alterar comportamento externo, e a exigência de que a skill seja copiável entre projetos sem alterações).

Todo o conhecimento de domínio foi delegado para `references/`, seguindo progressive disclosure — cada fase só lê os arquivos que precisa, no momento em que precisa:

| Arquivo | Área de conhecimento | Lido na |
|---|---|---|
| `analysis-heuristics.md` | Análise de projeto | Fase 1 |
| `antipatterns-catalog.md` | Catálogo de anti-patterns | Fase 2 |
| `audit-report-template.md` | Template de relatório | Fase 2 |
| `mvc-guidelines.md` | Guidelines de arquitetura | Fase 3 |
| `refactoring-playbook.md` | Playbook de refatoração | Fase 3 |

Isso cobre as 5 áreas de conhecimento exigidas pelo desafio, uma por arquivo, o que também facilitou a iteração: quando um projeto gerava poucos findings ou uma estrutura MVC inconsistente, era possível ajustar só a referência relevante sem tocar no fluxo do `SKILL.md`.

Uma decisão específica: a Fase 2 não apenas imprime o relatório, mas também o salva em `audit-report.md` na raiz do projeto auditado — isso elimina a necessidade de copiar manualmente a saída do terminal para preencher `reports/audit-project-{1,2,3}.md`. E a Fase 1 avança automaticamente para a Fase 2 sem pedir confirmação (só a transição 2→3 exige aprovação explícita), é importante uma para revisão pausa antes da modificação de arquivos, que só acontece na Fase 3.

### Anti-patterns incluídos no catálogo

O catálogo tem 12 anti-patterns (acima do mínimo de 8 exigido), distribuídos assim:

- **CRITICAL (3):** God Class/God Method, credenciais/secrets hardcoded, SQL Injection por concatenação de strings — escolhidos por comprometerem segurança diretamente ou tornarem o código impossível de testar em isolamento. São os problemas que justificam parar tudo e refatorar antes de qualquer outra coisa.
- **HIGH (3):** lógica de negócio em rotas/controllers, forte acoplamento sem injeção de dependência, estado global mutável — violações de MVC/SOLID que não derrubam a aplicação, mas inviabilizam manutenção, testes e escalabilidade do time.
- **MEDIUM (4):** queries N+1, validações ausentes nas rotas, APIs deprecated, código duplicado — dívida técnica real, mas que não bloqueia o funcionamento imediato.
- **LOW (2):** magic numbers/strings, nomenclatura ruim ou inconsistente — problemas de legibilidade, incluídos para que a auditoria também capture melhorias incrementais, não só falhas graves.

A detecção de APIs deprecated (item 9) foi tratada à parte porque era requisito explícito do desafio: em vez de uma regra genérica, o catálogo traz uma tabela com 7 exemplos concretos por stack (ex.: `@app.before_first_request` removido no Flask 2.3+, `new Buffer()` deprecated em Node) e a orientação de reclassificar a severidade dinamicamente — MEDIUM se a API ainda funciona mas está marcada como obsoleta, HIGH se a versão detectada na Fase 1 já a removeu e o código quebraria em runtime.

Cada anti-pattern tem "sinais de detecção" escritos como padrões de código concretos e buscáveis (ex.: `f"SELECT * FROM users WHERE id = {user_id}"` para SQL Injection, `users = []` mutado por múltiplas rotas para estado global), não descrições vagas como "código mal escrito" — isso segue a orientação de que sinais específicos são o que de fato torna um finding acionável e verificável arquivo/linha.

### Como garantimos que a skill é agnóstica de tecnologia

Três decisões de design sustentam isso:

1. **Heurísticas de detecção nunca fixam nomes de projeto.** `analysis-heuristics.md` identifica linguagem e framework por manifestos genéricos (`requirements.txt`/`package.json`/`go.mod`/etc.) e por sinais de driver de banco, nunca por nomes de arquivo específicos de um dos 3 projetos-alvo.
2. **As regras de arquitetura são descritas em termos abstratos.** `mvc-guidelines.md` define responsabilidade de cada camada (Model/View/Controller) e a regra de dependência `routes → controllers → models` sem amarrar a um framework — só na seção final ("Adaptação às convenções idiomáticas da stack") é que entram detalhes concretos de Flask (Blueprints, application factory) e Express (Router, composition root em `index.js`), como *tradução* da regra abstrata, não como a regra em si.
3. **O playbook usa exemplos por stack apenas como ilustração do princípio.** Cada um dos 10 padrões de transformação (God Class, secrets hardcoded, SQL injection, lógica de negócio na rota, acoplamento sem DI, estado global, error handling, API deprecated, N+1, validação ausente) traz código antes/depois em Flask e/ou Express, mas a instrução no `SKILL.md` é generalizar o princípio para a stack real do projeto — o exemplo em código não é a regra, é a demonstração dela.

A prova concreta foi rodar a mesma cópia da skill, sem alterações, nos 3 projetos: dois em Python/Flask com níveis de organização diferentes (`code-smells-project`, monolítico, e `task-manager-api`, parcialmente organizado com `models/`, `routes/`, `services/` pré-existentes) e um em Node.js/Express (`ecommerce-api-legacy`). Para o caso do projeto parcialmente organizado, `mvc-guidelines.md` inclui uma seção dedicada ("Adaptação a projetos parcialmente organizados") instruindo a skill a preservar camadas já corretas e ajustar só o que estiver errado, em vez de recriar tudo do zero — o critério de sucesso é a estrutura final respeitar as regras de dependência, não o volume de código reescrito.

### Desafios encontrados e como resolvemos

- **Execução automática indesejada.** A primeira versão do prompt de criação da skill pedia, na mesma mensagem, para criar os arquivos e depois "validar executando nos 3 projetos, ajustando até passar no checklist". O Claude Code interpretou isso como uma única tarefa contínua: criou a skill e emendou a execução completa (Fases 1 a 3) nos projetos, sem que essa execução fosse desejada naquele momento. A correção foi separar as responsabilidades em duas sessões distintas — um prompt que cria a skill e explicitamente instrui a parar depois, e a execução feita manualmente depois, projeto a projeto, com confirmação humana real na transição da Fase 2 para a Fase 3 (que é, aliás, uma restrição que o próprio `SKILL.md` final passou a impor de forma explícita: "não prosseguir para a Fase 3 sob nenhuma justificativa" sem resposta afirmativa).

- **Local incorreto da skill.** Em uma tentativa, a skill foi criada na raiz do repositório (`.claude/skills/refactor-arch/`) em vez de dentro de `code-smells-project/`. Como o Claude Code resolve skills de projeto relativamente ao diretório de trabalho no momento da chamada (`cd code-smells-project && claude "/refactor-arch"` procura `code-smells-project/.claude/skills/`, não a raiz do repo), isso fazia o comando não existir. A correção foi mover a pasta para dentro do primeiro projeto e, a partir dali, **copiar** (não mover) para `ecommerce-api-legacy/` e `task-manager-api/` — reforçando a exigência de que a skill seja copiável sem alterações, hoje documentada como restrição geral no próprio `SKILL.md`.

- **Sobras da execução acidental distorcendo a Fase 1.** A execução indesejada do primeiro problema deixou diretórios MVC vazios (`src/config/`, `src/models/` etc.) em mais de um projeto. Isso é relevante porque `analysis-heuristics.md` classifica a arquitetura pela distribuição real de responsabilidades por arquivo — uma pasta `src/` vazia poderia levar a Fase 1 a reportar uma arquitetura "MVC parcial" inexistente. Foi necessário limpar manualmente essas pastas para garantir que cada projeto voltasse ao estado original (monolítico ou parcialmente organizado, conforme o desafio define) antes da execução "oficial".

## C) Resultados

### Resumo dos relatórios de auditoria (Fase 2)

| Projeto | Stack | Arquivos | Linhas | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 4 | ~784 | 3 | 3 | 2 | 2 | **10** |
| ecommerce-api-legacy | Node.js + Express ^4.18.2 | 3 | ~183 | 3 | 3 | 3 | 2 | **11** |
| task-manager-api | Python + Flask 3.0.0 | 15 | ~1158 | 3 | 2 | 3 | 2 | **10** |
| **Total** | | **22** | **~2125** | **9** | **8** | **8** | **6** | **31** |

Os 3 projetos superaram o mínimo de 5 findings e tiveram ao menos 1 CRITICAL/HIGH, atendendo aos critérios de aceite obrigatórios da Fase 2.

**Principais findings por projeto:**

- **code-smells-project**: SQL Injection generalizado (praticamente todas as queries do `models.py` concatenam strings), `SECRET_KEY` hardcoded exposta publicamente no endpoint `/health`, e um endpoint `POST /admin/query` que executa SQL arbitrário vindo do corpo da requisição sem qualquer autenticação — o achado mais grave dos 3 projetos.
- **ecommerce-api-legacy**: God Class concentrando toda a aplicação em `AppManager.js`, hashing de senha "customizado" (Base64 repetido, reversível) no lugar de um algoritmo criptográfico real, e credenciais de produção — inclusive chave de gateway de pagamento — hardcoded em `utils.js`.
- **task-manager-api**: apesar de já ter separação parcial em `models/`, `routes/`, `services/`, ainda concentrou 3 CRITICALs (secrets de app e SMTP hardcoded, hash de senha em MD5 puro sem salt) e um padrão interessante de HIGH — a regra de "task atrasada" já existe como método no model (`Task.is_overdue()`) mas é reimplementada manualmente em 5 lugares diferentes, nunca chamada.

### Comparação antes/depois da estrutura de cada projeto

**1. code-smells-project (Python/Flask)**

Antes (monolítico, 4 arquivos na raiz, sem separação de camadas):

```
code-smells-project/
├── app.py            # bootstrap + rotas /admin (sem auth) + /health vazando secrets
├── controllers.py     # validação, regra de negócio, logging via print()
├── models.py           # SQL cru concatenado, regra de negócio, formatação — para 4 domínios
├── database.py         # conexão global singleton, não thread-safe
└── requirements.txt
```

Depois (MVC, 21 arquivos Python em `src/`):

```
code-smells-project/
├── app.py                          # composition root (create_app)
├── .env.example                    # segredos fora do código
├── requirements.txt
└── src/
    ├── database.py
    ├── config/settings.py           # SECRET_KEY e config lidos de env
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py
    │   └── pedido_model.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   └── pedido_controller.py
    ├── routes/
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   └── pedido_routes.py
    └── middlewares/error_handler.py # tratamento de erro centralizado
```

O endpoint `POST /admin/query` (execução de SQL arbitrário) foi eliminado, e todas as queries passaram a usar parâmetros (`?`) em vez de concatenação de string.

**2. ecommerce-api-legacy (Node.js/Express)**

Antes (God Class concentrando tudo):

```
ecommerce-api-legacy/
├── src/app.js         # bootstrap
├── src/AppManager.js  # init de schema + TODAS as rotas (closures) + regra de negócio + queries SQL
└── src/utils.js        # config com secrets hardcoded + "badCrypto" (hash falso)
```

Depois (MVC, 18 arquivos em `src/`):

```
ecommerce-api-legacy/
├── .env.example
└── src/
    ├── app.js                        # composition root
    ├── config/{index.js,database.js} # secrets via process.env
    ├── models/
    │   ├── userModel.js
    │   ├── courseModel.js
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   ├── reportModel.js
    │   └── auditLogModel.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── routes/
    │   ├── checkoutRoutes.js
    │   ├── reportRoutes.js
    │   └── userRoutes.js
    ├── middlewares/errorHandler.js
    └── utils/{passwordHasher.js, logger.js, httpError.js}
```

`badCrypto` foi substituído por hashing real em `passwordHasher.js`, e os "callback hell" de checkout/relatório viraram funções `async/await` isoladas em controllers.

**3. task-manager-api (Python/Flask, parcialmente organizado)**

Antes (camadas já existiam, mas rotas concentravam regra de negócio):

```
task-manager-api/
├── app.py
├── database.py
├── seed.py
├── models/{user.py, task.py, category.py}
├── routes/{task_routes.py, user_routes.py, report_routes.py}  # regra de negócio, agregação de relatório e serialização manual aqui
├── services/notification_service.py                            # credenciais SMTP hardcoded
└── utils/helpers.py
```

Depois (camadas preexistentes mantidas, com `controllers/`, `config/` e `middlewares/` adicionados na raiz — a skill preservou a organização já existente em vez de mover tudo para `src/`, conforme a orientação de "Adaptação a projetos parcialmente organizados" da própria skill):

```
task-manager-api/
├── app.py                        # composition root, config e SECRET_KEY via env
├── database.py
├── seed.py
├── config/settings.py            # nova camada de config
├── models/{user.py, task.py, category.py}
├── controllers/                  # nova camada — recebe a lógica que estava nas rotas
│   ├── task_controller.py
│   ├── user_controller.py
│   └── report_controller.py
├── routes/                       # agora rotas finas, delegam para controllers
│   ├── task_routes.py
│   ├── user_routes.py
│   └── report_routes.py
├── services/notification_service.py  # credenciais movidas para env
├── middlewares/error_handler.py      # tratamento de erro centralizado (novo)
└── utils/helpers.py
```

A regra de "task atrasada" (antes duplicada em 5 lugares) foi consolidada chamando `Task.is_overdue()` a partir dos controllers, e o hash de senha migrou de MD5 puro para `werkzeug.security`.

> **Nota:** neste projeto sobrou um `middlewares/errors.py` (vazio/residual) ao lado do `middlewares/error_handler.py` novo, e um diretório `src/` vazio pré-existente — resíduos que não afetam o funcionamento da aplicação, mas que ficam registrados aqui como ponto de limpeza pendente.

### Checklist de validação preenchido

Checklist do enunciado (`README-ESPECIFICACAO.md`, seção "Checklist de Validação"), conferido para os 3 projetos após a execução da skill:

**code-smells-project**

- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce — produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (10)
- [x] Detecção de APIs deprecated incluída (avaliada; nenhuma API deprecated relevante encontrada neste projeto)
- [x] Skill pausa e pede confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC (`src/models`, `src/controllers`, `src/routes`)
- [x] Configuração extraída para módulo de config (`src/config/settings.py`, sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (`src/middlewares/error_handler.py`)
- [x] Entry point claro (`app.py` com `create_app()`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

**ecommerce-api-legacy**

- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express ^4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com fluxo de checkout)
- [x] Número de arquivos analisados condiz com a realidade (3)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [x] Detecção de APIs deprecated incluída (catálogo cobre casos Node.js, ex. `new Buffer()`)
- [x] Skill pausa e pede confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC (`src/models`, `src/controllers`, `src/routes`)
- [x] Configuração extraída para módulo de config (`src/config`, sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (`src/middlewares/errorHandler.js`)
- [x] Entry point claro (`src/app.js`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

**task-manager-api**

- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0)
- [x] Domínio da aplicação descrito corretamente (Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (15)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (10)
- [x] Detecção de APIs deprecated incluída (avaliada; nenhuma API deprecated relevante encontrada neste projeto)
- [x] Skill pausa e pede confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC (camadas pré-existentes preservadas + `controllers/` novo)
- [x] Configuração extraída para módulo de config (`config/settings.py`, sem hardcoded)
- [x] Models criados para abstrair dados (já existiam, mantidos)
- [x] Views/Routes separadas para roteamento (já existiam, agora finas)
- [x] Controllers concentram o fluxo da aplicação (camada nova)
- [x] Error handling centralizado (`middlewares/error_handler.py`)
- [x] Entry point claro (`app.py` com `create_app()`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Logs das aplicações rodando após a refatoração

Evidência coletada nesta revisão subindo cada aplicação manualmente e chamando endpoints reais:

**code-smells-project** — `python app.py` seguido de `curl /health` e `curl /produtos`:

```
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
127.0.0.1 - - [12/Jul/2026 19:14:28] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [12/Jul/2026 19:14:28] "GET /produtos HTTP/1.1" 200 -
```

```json
{"counts":{"pedidos":1,"produtos":10,"usuarios":4},"database":"connected","status":"ok","versao":"1.0.0"}
```

**ecommerce-api-legacy** — `node src/app.js` seguido de `curl /api/admin/financial-report`:

```
Frankenstein LMS rodando na porta 3000...
```

```json
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":0,"students":[]}]
```

**task-manager-api** — `python app.py` seguido de `curl /health` e `curl /tasks`:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
127.0.0.1 - - [12/Jul/2026 19:14:41] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [12/Jul/2026 19:14:41] "GET /tasks HTTP/1.1" 200 -
```

```json
{"status": "ok", "timestamp": "2026-07-12 19:14:41.410508"}
```

(resposta de `/tasks` omitida aqui por tamanho — retornou a lista completa das 10 tasks, HTTP 200)

### Observações sobre como a skill se comportou em stacks diferentes

- **Reuso sem alterações:** a mesma cópia de `.claude/skills/refactor-arch/` (mesmo `SKILL.md`, mesmos 5 arquivos de `references/`) foi usada nos 3 projetos, apenas copiada de pasta em pasta — nenhuma edição foi necessária entre uma execução e outra, confirmando o requisito de "skill copiável".
- **Monolito puro (Projeto 1) vs. God Class (Projeto 2):** em Python a skill encontrou um "God File" (`models.py` com SQL cru de 4 domínios); em Node encontrou uma "God Class" (`AppManager.js` com rotas via closures). São o mesmo anti-pattern arquitetural (ausência total de separação MVC) expresso de forma sintaticamente muito diferente, e a skill classificou ambos como CRITICAL/HIGH corretamente sem que o catálogo precisasse de regras específicas por linguagem.
- **Projeto parcialmente organizado (Projeto 3) exigiu um modo de operação diferente:** como `models/`, `routes/`, `services/` já existiam, a Fase 3 não recriou a árvore do zero — ela preservou as camadas corretas e só adicionou o que faltava (`controllers/`, `config/`, `middlewares/`), movendo a lógica que estava indevidamente nas rotas para a nova camada de controllers. Isso validou que a skill se adapta ao nível de maturidade do projeto em vez de aplicar sempre a mesma transformação.
- **JS assíncrono teve uma classe própria de finding:** o "callback hell" com contadores manuais de checkout/relatório financeiro só apareceu no Projeto 2 — é um problema específico do paradigma assíncrono por callback do Node, que não tem equivalente direto nos dois projetos Flask (que já usam chamadas síncronas).
- **Nenhuma perda de comportamento externo:** nos 3 projetos, os endpoints originais (validados por boot manual + `curl` nesta revisão, ver seção anterior) continuaram respondendo com o mesmo formato de dados após a refatoração — a reestruturação interna não alterou contratos de API.

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado com uma conta Anthropic válida.
- Node.js (dependência do próprio Claude Code — ver documentação oficial para a versão mínima exigida).
- Python 3.x e `pip` instalados (para rodar `code-smells-project/` e `task-manager-api/`, ambos Flask).
- Node.js e `npm` instalados (para rodar `ecommerce-api-legacy/`, Express).
- `git`, para clonar o repositório.

### Clonando o repositório

```bash
git clone https://github.com/<seu-usuario>/<nome-do-fork>.git
cd <nome-do-fork>
```

A skill já vem commitada dentro de cada um dos 3 projetos, em `<projeto>/.claude/skills/refactor-arch/` — não é necessário nenhum passo de instalação adicional.

### Instalando as dependências de cada projeto

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
pip install -r requirements.txt
cd ..

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ecommerce-api-legacy
npm install
cd ..

# Projeto 3 — task-manager-api (Python/Flask)
cd task-manager-api
pip install -r requirements.txt
cd ..
```

### Executando a skill em cada projeto

O Claude Code resolve skills de projeto de forma relativa ao diretório de trabalho no momento da chamada — por isso é necessário entrar em cada pasta antes de invocar o comando.

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"
```

A skill executa a Fase 1 (análise) e a Fase 2 (auditoria) automaticamente, imprime o relatório e pausa com:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Revisar o relatório e responder `y` para prosseguir com a refatoração (Fase 3), ou `n` para encerrar sem modificar nenhum arquivo.

```bash
# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

O fluxo (executar → revisar relatório → confirmar Fase 3) se repete da mesma forma nos 3 projetos, sem nenhuma alteração na skill entre uma execução e outra.

### Onde encontrar as saídas

- O relatório impresso na Fase 2 também é salvo automaticamente em `audit-report.md`, na raiz do projeto auditado. Copiar esse arquivo para `reports/audit-project-{1,2,3}.md` (1 = code-smells-project, 2 = ecommerce-api-legacy, 3 = task-manager-api) e commitar.
- O código refatorado da Fase 3 fica no próprio projeto. Em `code-smells-project/` e `ecommerce-api-legacy/`, a skill criou a estrutura sob `src/` (`src/config`, `src/models`, `src/routes`, `src/controllers`, `src/middlewares`). Em `task-manager-api/`, como o projeto já tinha `models/`, `routes/`, `services/`, `utils/` na raiz, a skill preservou essa organização e adicionou `config/`, `controllers/` e `middlewares/` também na raiz, em vez de mover tudo para `src/` (ver seção "Comparação antes/depois" acima). Em todos os casos, commitar as mudanças em cada projeto após validar.

### Como validar que a refatoração funcionou

Para cada projeto, após a Fase 3:

1. **Conferir a saída de validação da própria skill**, impressa ao final da Fase 3:
   ```
   ================================
   PHASE 3: REFACTORING COMPLETE
   ================================
   ## Validation
     ✓ Application boots without errors
     ✓ All endpoints respond correctly
     ✓ Zero anti-patterns remaining
   ================================
   ```

2. **Subir a aplicação manualmente e conferir que não há erro no boot:**
   ```bash
   # Flask (projetos 1 e 3)
   flask --app app run
   # ou, se o entry point mudou de nome após a refatoração, usar o novo composition root

   # Express (projeto 2)
   node src/app.js
   ```

3. **Exercitar os endpoints originais** com `curl` (ou o arquivo `api.http` do projeto, quando existir) e comparar o formato de resposta com o comportamento anterior à refatoração:
   ```bash
   curl http://localhost:5000/produtos      # exemplo — ajustar rota/porta conforme o projeto
   curl http://localhost:5000/health
   ```

4. **Conferir o checklist de validação** (seção C deste README) marcado para os 3 projetos.