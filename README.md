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
