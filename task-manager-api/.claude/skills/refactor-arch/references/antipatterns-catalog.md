# Anti-patterns Catalog (Fase 2)

Catálogo de anti-patterns arquiteturais a procurar ao auditar qualquer projeto backend. Para cada finding registrado no relatório, confira o arquivo e as linhas reais — nunca estime.

## Escala de severidade

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex.: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex.: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex.: lógica de negócio pesada dentro de Controllers, forte acoplamento sem Injeção de Dependência, estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos moderados de performance (ex.: queries N+1, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura ruim de variáveis, "magic numbers" soltos pelo código.

## Catálogo

### 1. God Class / God Method (CRITICAL)

**Descrição:** Um único arquivo ou função concentra roteamento, acesso a dados e regras de negócio, muitas vezes o próprio entry point da aplicação.

**Sinais de detecção:**
- Um arquivo (ex.: `app.py`, `server.js`, `index.js`) contém definição de rotas, queries SQL/ORM diretas e lógica de negócio no mesmo escopo.
- Uma única função/handler com mais de ~50 linhas misturando validação, acesso a dados e formatação de resposta.
- Import direto do driver de banco (`sqlite3`, `psycopg2`, `mysql2`) dentro do arquivo de rotas.

**Recomendação:** Separar em models (dados), controllers (orquestração) e routes (apresentação), um por domínio.

### 2. Credenciais/secrets hardcoded (CRITICAL)

**Descrição:** Strings de conexão, senhas, chaves de API ou tokens escritos diretamente no código-fonte.

**Sinais de detecção:**
- Literais como `password = "..."`, `SECRET_KEY = "..."`, `api_key = "..."`, strings de conexão com usuário/senha embutidos (`postgres://user:pass@host`).
- Ausência de leitura via variável de ambiente (`os.environ`, `process.env`) para esses valores.
- Ausência de arquivo `.env.example` documentando as variáveis esperadas.

**Recomendação:** Mover para variáveis de ambiente carregadas em um módulo de config central; criar `.env.example` sem valores reais.

### 3. SQL Injection por concatenação de strings (CRITICAL)

**Descrição:** Query SQL montada por concatenação ou f-string/template string incluindo input do usuário, sem parametrização.

**Sinais de detecção:**
- Python: `f"SELECT * FROM users WHERE id = {user_id}"`, `"... WHERE name = '" + name + "'"`, `.format()` em query SQL.
- Node.js: template strings (`` `SELECT * FROM x WHERE id = ${id}` ``) passadas diretamente para `query()`/`execute()`.
- Ausência de placeholders (`?`, `%s`, `$1`) e de passagem de parâmetros separados para o driver.

**Recomendação:** Reescrever toda query com parâmetros ligados (`cursor.execute(query, (param,))`, `db.query('... WHERE id = ?', [id])`) ou usar o ORM corretamente.

### 4. Lógica de negócio em rotas/controllers (HIGH)

**Descrição:** Cálculos de domínio, regras condicionais complexas ou orquestração de múltiplas entidades implementados diretamente no handler de rota.

**Sinais de detecção:**
- Handler de rota contendo laços, cálculos (ex.: totais, descontos, validações de estoque) em vez de apenas chamar um controller/service.
- Blocos `if/else` de regra de negócio (não validação de request) dentro da função de rota.

**Recomendação:** Extrair a lógica para um controller (ou service) do domínio correspondente; a rota deve apenas receber o request, chamar o controller e devolver a resposta.

### 5. Forte acoplamento sem injeção de dependência (HIGH)

**Descrição:** Módulos instanciam diretamente suas dependências (conexão de banco, outros serviços) em vez de recebê-las, impedindo testes isolados e reuso.

**Sinais de detecção:**
- `new Database(...)` ou `sqlite3.connect(...)` instanciado dentro de cada função/controller em vez de centralizado e injetado.
- Import direto de um módulo concreto de outro domínio em vez de receber a dependência via parâmetro/construtor.
- Impossibilidade de substituir a dependência em teste sem alterar o código de produção.

**Recomendação:** Centralizar a criação de dependências no composition root (entry point) e passá-las via construtor/parâmetro (factory functions, injeção via app context/Blueprint).

### 6. Estado global mutável (HIGH)

**Descrição:** Variáveis globais mutáveis (listas, dicionários, contadores) usadas como "banco de dados" ou estado compartilhado entre requisições.

**Sinais de detecção:**
- Variável no escopo do módulo (ex.: `users = []`, `let orders = {}`) alterada por múltiplos handlers de rota.
- Ausência de qualquer persistência real quando o domínio exige (dados somem ao reiniciar o processo).
- Uso de variáveis globais para armazenar contadores/IDs incrementais sem controle de concorrência.

**Recomendação:** Substituir por acesso a um model que encapsula a fonte de dados real (banco de dados), com estado isolado por requisição.

### 7. Queries N+1 (MEDIUM)

**Descrição:** Uma query é executada para buscar uma lista, seguida de uma query adicional por item dentro de um laço, em vez de uma única query com JOIN ou carregamento em lote.

**Sinais de detecção:**
- Laço `for item in items:` contendo uma chamada de query dentro do corpo (ex.: buscar o "autor" de cada "post" individualmente).
- Uso de ORM sem eager loading (`.select_related`/`.join`/`populate`) quando relacionamentos são acessados dentro de iteração.

**Recomendação:** Substituir por uma única query com JOIN, ou usar carregamento em lote (`WHERE id IN (...)`) / eager loading do ORM.

### 8. Validações ausentes nas rotas (MEDIUM)

**Descrição:** Handler de rota acessa campos do corpo da requisição sem validar presença, tipo ou formato antes de usá-los.

**Sinais de detecção:**
- Acesso direto a `request.json["campo"]` / `req.body.campo` sem checagem de existência ou tipo antes de usar em query/lógica.
- Ausência de qualquer schema de validação (manual, ou biblioteca como `pydantic`, `marshmallow`, `joi`, `zod`) para o payload de entrada.
- Rotas que quebram com erro 500 (em vez de 400) para payload malformado.

**Recomendação:** Adicionar validação de entrada na borda da rota (schema de validação ou checagem explícita), retornando 400 para payload inválido.

### 9. APIs deprecated da linguagem/framework (MEDIUM, ou HIGH se removidas na versão em uso)

**Descrição:** Uso de métodos, módulos ou padrões marcados como deprecated pela linguagem ou framework declarado nas dependências.

**Sinais de detecção e equivalente moderno (exemplos por stack — verificar contra a versão real detectada na Fase 1):**

| Stack | API deprecated | Equivalente moderno |
|---|---|---|
| Python | `@app.before_first_request` (Flask, removido no 2.3+) | usar setup no factory/composition root (`create_app`) |
| Python | `datetime.utcnow()` (deprecated 3.12+) | `datetime.now(timezone.utc)` |
| Python | `flask.Markup` (removido no Flask 2.3+) | `markupsafe.Markup` |
| Node.js | `new Buffer(...)` (deprecated) | `Buffer.from(...)` |
| Node.js | `body-parser` standalone (Express 4.16+) | `express.json()` / `express.urlencoded()` |
| Node.js | callbacks de `fs` sem promisify em código novo | `fs/promises` |
| Express | middleware de erro com 3 args | manter assinatura de 4 args `(err, req, res, next)` |

Se a versão exata do framework não permitir confirmar a remoção, classificar como MEDIUM com nota "verificar changelog da versão X"; se a versão detectada já removeu a API (quebra em runtime), classificar como HIGH.

**Recomendação:** Substituir pela API moderna equivalente indicada acima, confirmando compatibilidade com a versão detectada na Fase 1.

### 10. Código duplicado (MEDIUM)

**Descrição:** Blocos de lógica quase idênticos repetidos em múltiplos lugares (ex.: mesma query repetida em 3 rotas, mesma validação copiada e colada).

**Sinais de detecção:**
- Dois ou mais trechos com >5 linhas quase idênticas (variando apenas nomes/literais).
- Mesma query SQL escrita em múltiplos handlers em vez de centralizada no model.

**Recomendação:** Extrair para uma função/método único no model ou controller apropriado.

### 11. Magic numbers/strings (LOW)

**Descrição:** Valores literais (números, strings) usados diretamente no código sem nome que explique seu significado.

**Sinais de detecção:**
- Comparações como `if status == 3:`, `if role == "2":` sem constante/enum nomeado.
- Limites, timeouts ou taxas embutidos como literais (`if len(x) > 42:`).

**Recomendação:** Extrair para constantes nomeadas ou enum no módulo de config/domínio.

### 12. Nomenclatura ruim ou inconsistente (LOW)

**Descrição:** Nomes de variáveis, funções ou arquivos que não comunicam propósito, ou inconsistência de convenção (camelCase misturado com snake_case no mesmo idioma/stack).

**Sinais de detecção:**
- Variáveis de uma letra ou nomes genéricos (`data`, `tmp`, `x`) fora de escopos triviais (ex.: contadores de laço).
- Mistura de convenções de case dentro do mesmo arquivo/linguagem sem padrão do próprio framework justificando.

**Recomendação:** Renomear para nomes descritivos do domínio, seguindo a convenção idiomática da linguagem/framework detectado.
