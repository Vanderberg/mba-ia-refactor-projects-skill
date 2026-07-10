# Analysis Heuristics (Fase 1)

Heurísticas concretas e agnósticas de stack para mapear um projeto antes de auditá-lo. Sempre confirme abrindo os arquivos reais — nunca infira a partir do nome do repositório ou de suposições.

## 1. Detecção de linguagem

Detecte pela presença de arquivos de manifesto e extensões dominantes no código-fonte:

| Linguagem  | Arquivos de manifesto                          | Extensões dominantes |
|------------|--------------------------------------------------|-----------------------|
| Python     | `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | `.py` |
| Node.js    | `package.json`, `package-lock.json`, `yarn.lock` | `.js`, `.ts`, `.mjs` |
| Go         | `go.mod`, `go.sum`                                | `.go` |
| PHP        | `composer.json`, `composer.lock`                  | `.php` |
| Java       | `pom.xml`, `build.gradle`                         | `.java` |
| Ruby       | `Gemfile`, `Gemfile.lock`                          | `.rb` |

Se mais de um manifesto existir (ex.: monorepo com backend Python e frontend Node), identifique qual pasta contém o backend a ser refatorado.

## 2. Detecção de framework e versão

Nunca adivinhe a versão — leia a string declarada no manifesto:

- **Python**: procurar `flask==X.Y.Z`, `Flask>=X.Y`, `fastapi`, `django` em `requirements.txt` ou `pyproject.toml`. Se não houver pin de versão, verificar ambiente instalado (`pip show <pacote>`) ou reportar "versão não fixada".
- **Node.js**: procurar `"express": "^X.Y.Z"`, `"fastify"`, `"koa"` em `dependencies`/`devDependencies` de `package.json`.
- **PHP**: `"laravel/framework"`, `"slim/slim"` em `composer.json`.
- **Java**: `<artifactId>spring-boot-starter-web</artifactId>` em `pom.xml`.

Reporte framework + versão exatamente como declarado (ex.: "Flask 2.3.2", "Express ^4.18.2").

## 3. Detecção de banco de dados

Sinais concretos, em ordem de confiabilidade:

1. Driver nas dependências: `sqlite3`, `psycopg2`/`psycopg2-binary` (Postgres), `mysql-connector-python`/`PyMySQL` (MySQL), `pymongo` (MongoDB) em Python; `pg`, `mysql2`, `mongoose`, `sqlite3` em Node.
2. Strings de conexão no código ou em `.env`/`config`: `postgres://`, `mysql://`, `mongodb://`, caminho para arquivo `.db`/`.sqlite`/`.sqlite3`.
3. Presença de arquivo de banco embarcado (`*.db`, `*.sqlite3`) no repositório.
4. Comandos DDL no código ou em migrations: `CREATE TABLE`, `db.define`, `Schema(...)`, classes de model ORM (`class X(db.Model)`, `mongoose.Schema(...)`).

Se nenhum sinal for encontrado, reporte "sem persistência detectada" — não presuma um banco.

## 4. Mapeamento da arquitetura atual

Classifique com base na distribuição real de responsabilidades por arquivo, não pelo nome dos diretórios:

- **Monolítica**: a maior parte da lógica (rotas + queries + regras de negócio) está concentrada em 1-3 arquivos, sem diretórios de camada (`models/`, `controllers/`, `routes/` inexistentes ou vazios).
- **MVC parcial**: existem alguns diretórios de camada (ex.: `models/` com classes de dados), mas outras responsabilidades ainda vazam para fora deles (ex.: rotas fazendo query direta ao banco, ou controllers fazendo validação de schema de banco).
- **MVC completa**: rotas delegam a controllers, controllers delegam a models, e não há acesso a dados ou regra de negócio fora dessas camadas.
- **Camadas misturadas**: diretórios de camada existem mas o conteúdo não corresponde ao nome (ex.: um arquivo em `controllers/` contém definição de schema de banco).

Para decidir, abra uma amostra representativa dos arquivos-fonte e verifique: quem faz query ao banco? quem monta a resposta HTTP? quem contém regra de negócio (cálculos, validações complexas, decisões condicionais de domínio)?

## 5. Inferência de domínio

Leia:
- Padrões de rota (`/orders`, `/products`, `/users`) e seus verbos HTTP.
- Nomes de classes de model e de tabelas (`Order`, `Product`, `Customer`).
- Campos das entidades principais (dão pistas sobre o negócio: `price`, `stock`, `sku` → e-commerce; `task`, `assignee`, `due_date` → gestão de tarefas).

Produza uma frase curta e concreta (ex.: "API de gestão de pedidos e produtos de e-commerce" em vez de "aplicação web genérica").

## 6. Contagem de arquivos-fonte

Contar apenas arquivos de código-fonte do projeto. Excluir sempre:
- `node_modules/`, `venv/`, `.venv/`, `env/`
- `.git/`
- diretórios de build/dist: `dist/`, `build/`, `__pycache__/`, `.pytest_cache/`
- arquivos de lock (`package-lock.json`, `poetry.lock`) e binários
- assets estáticos não executáveis (imagens, fontes) a menos que sejam relevantes ao domínio

Reporte o número final como "N files analyzed".
