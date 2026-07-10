================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (Frankenstein LMS)
Stack:   JavaScript (Node.js) + Express ^4.18.2 + sqlite3 ^5.1.6
Files:   3 analyzed | ~183 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] God Class / God Method
File: src/AppManager.js:4-141
Description: A classe AppManager concentra criação/inicialização do banco (initDb, linhas 10-23), definição de todas as rotas (setupRoutes, linhas 25-138), queries SQL diretas via sqlite3, e toda a orquestração de regra de negócio (checkout, matrícula, pagamento, relatório financeiro) no mesmo arquivo e escopo, sem separação de camadas.
Impact: Qualquer mudança em uma responsabilidade (ex.: regra de pagamento) arrisca quebrar outra (ex.: rota ou acesso a dados); impossível testar unidades isoladamente; alta probabilidade de bugs em manutenção futura.
Recommendation: Separar em models (acesso a dados por domínio: User, Course, Enrollment, Payment), controllers (orquestração: CheckoutController, ReportController, UserController) e routes (apenas registro de rotas delegando para controllers).

### [CRITICAL] Credenciais/secrets hardcoded
File: src/utils.js:1-7
Description: Objeto `config` contém `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` escritos diretamente no código-fonte, sem leitura de variáveis de ambiente e sem `.env.example`.
Impact: Exposição de credenciais de produção (inclusive chave de gateway de pagamento) em qualquer cópia do repositório, histórico de git ou log.
Recommendation: Mover todos os valores sensíveis para variáveis de ambiente (`process.env.*`) carregadas em um módulo de config central; criar `.env.example` documentando as chaves esperadas sem valores reais.

### [CRITICAL] Hashing de senha inseguro (custom, reversível)
File: src/utils.js:17-23 (uso em src/AppManager.js:68-69)
Description: `badCrypto` não é uma função de hash criptográfico — repete `Buffer.from(pwd).toString('base64')` 10000 vezes e trunca o resultado; Base64 é reversível e o algoritmo não usa salt nem função de derivação de chave reconhecida (bcrypt/scrypt/argon2). É usado para "proteger" a senha do usuário ao criar uma conta.
Impact: Senhas de usuários armazenadas de forma efetivamente reversível/quebrável, violando práticas mínimas de segurança de autenticação; qualquer vazamento do banco expõe as senhas originais.
Recommendation: Substituir por uma biblioteca de hashing de senha estabelecida (ex.: `bcrypt`/`argon2`) com salt único por usuário, aplicada dentro de um model/serviço de autenticação dedicado.

### [HIGH] Lógica de negócio em rotas/controllers
File: src/AppManager.js:28-78
Description: O handler de `POST /api/checkout` implementa, inline, toda a orquestração de domínio: busca de curso, criação/lookup de usuário, hashing de senha, decisão de aprovação de pagamento (`cc.startsWith("4")`, linha 46), criação de matrícula, registro de pagamento e log de auditoria — tudo encadeado via callbacks dentro do handler de rota.
Impact: Regra de negócio crítica (aprovação de pagamento) fica misturada com parsing de request e formatação de resposta, dificultando testes automatizados e reuso da lógica fora do contexto HTTP.
Recommendation: Extrair o fluxo para um `CheckoutController`/serviço de domínio, deixando a rota apenas repassar o request e devolver a resposta do controller.

### [HIGH] Forte acoplamento sem injeção de dependência
File: src/AppManager.js:1-9
Description: A conexão SQLite (`new sqlite3.Database(':memory:')`) é instanciada diretamente dentro do construtor de `AppManager`, e o módulo `utils` (config, funções) é importado diretamente ao invés de recebido via parâmetro/injeção.
Impact: Impossível substituir o banco por um mock/stub em testes sem alterar o código de produção; qualquer novo consumidor de `AppManager` herda a mesma instância de banco sem controle externo.
Recommendation: Centralizar a criação da conexão de banco no composition root (entry point) e injetá-la via construtor nos models/controllers que precisam dela.

### [HIGH] Estado global mutável
File: src/utils.js:9-15
Description: `globalCache` (objeto) e `totalRevenue` (número) são variáveis mutáveis no escopo do módulo, compartilhadas entre todas as requisições; `logAndCache` (linhas 12-15) grava nelas a cada chamada de checkout (invocada em src/AppManager.js:59) sem isolamento por requisição ou usuário.
Impact: Estado compartilhado entre requisições concorrentes pode causar condições de corrida e vazamento de dados de um usuário para outro; `totalRevenue` nunca é atualizado nem lido, indicando código morto/inconsistente.
Recommendation: Substituir por acesso a um model/cache real isolado por requisição, ou remover se não for necessário; qualquer cache compartilhado deve ter escopo e concorrência explicitamente controlados.

### [MEDIUM] Queries N+1
File: src/AppManager.js:83-127
Description: O handler de `GET /api/admin/financial-report` busca todos os `courses` e, para cada curso, executa uma query de `enrollments`; para cada enrollment, executa mais uma query de `users` e outra de `payments` — resultando em `1 + N + 2*M` queries sequenciais em vez de joins/carregamento em lote.
Impact: Tempo de resposta degrada linearmente com o número de cursos e matrículas; sob carga, gera contenção significativa no banco.
Recommendation: Substituir por uma única query com JOIN (courses ⨝ enrollments ⨝ users ⨝ payments) ou carregamento em lote com `WHERE id IN (...)`, agregando os resultados em memória uma única vez.

### [MEDIUM] Validação ausente e integridade referencial quebrada
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` não valida o formato de `id`, não verifica se o usuário existe, e deleta o registro de `users` sem tratar `enrollments`/`payments` relacionados — a própria resposta da API confirma isso: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
Impact: Gera registros órfãos em `enrollments` e `payments`, corrompendo a integridade dos dados e potencialmente quebrando o relatório financeiro (que assume `user_id` válido).
Recommendation: Validar `id` na borda da rota, verificar existência do usuário (404 se ausente), e no model tratar explicitamente os registros relacionados (cascade ou bloqueio da exclusão com 409 se houver matrículas ativas).

### [MEDIUM] Código duplicado (tratamento de erro repetido)
File: src/AppManager.js:38,41,48,51,55
Description: O padrão `if (err) return res.status(500).send("Erro ...")` é repetido manualmente em cada callback aninhado do fluxo de checkout, com mensagens quase idênticas variando apenas o texto.
Impact: Qualquer mudança no formato de erro (ex.: passar a retornar JSON estruturado) exige editar múltiplos pontos manualmente, aumentando o risco de inconsistência.
Recommendation: Centralizar tratamento de erro em um middleware de erro do Express (`(err, req, res, next)`) e propagar erros via `next(err)` a partir dos models/controllers.

### [LOW] Nomenclatura ruim/pouco descritiva
File: src/AppManager.js:29-33
Description: Variáveis do payload de checkout são atribuídas a nomes de uma ou duas letras (`u`, `e`, `p`, `cid`, `cc`) que não comunicam seu significado de domínio (usuário, e-mail, senha, id do curso, cartão).
Impact: Reduz legibilidade e aumenta a chance de erro ao dar manutenção no fluxo de checkout.
Recommendation: Renomear para nomes descritivos (`username`, `email`, `password`, `courseId`, `cardNumber`).

### [LOW] Magic number
File: src/utils.js:19
Description: O laço em `badCrypto` usa o literal `10000` como número de iterações, sem constante nomeada explicando o motivo desse valor.
Impact: Dificulta entender e ajustar o comportamento da função sem contexto adicional (agravado pelo fato de a função ser substituída por hashing real — ver finding CRITICAL acima).
Recommendation: Se a função for mantida (não recomendado), extrair para uma constante nomeada como `HASH_ITERATIONS`.

================================
Total: 11 findings
================================
