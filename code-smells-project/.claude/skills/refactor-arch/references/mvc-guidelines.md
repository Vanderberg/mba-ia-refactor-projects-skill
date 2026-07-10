# MVC Guidelines (Fase 3)

Regras de arquitetura alvo para a refatoração, agnósticas de stack. Aplique adaptando os nomes de diretório e idiomas à stack detectada na Fase 1.

## Responsabilidade de cada camada

- **Model**: dados e regras de domínio. Encapsula todo acesso à fonte de dados (banco, arquivo, API externa) e as regras de negócio que dependem diretamente desses dados (ex.: cálculo de total de um pedido a partir de seus itens). Um model nunca conhece HTTP (não recebe `request`/`response`).
- **View / Routes**: apresentação e roteamento. Recebe a requisição HTTP, delega ao controller correspondente e devolve a resposta no formato esperado (JSON, HTML). Não contém regra de negócio nem acesso a dados.
- **Controller**: orquestração. Recebe dados já extraídos da rota, chama um ou mais models, aplica lógica de orquestração (não de persistência) e devolve o resultado para a rota formatar. É o único lugar onde fluxos multi-model são coordenados.

## Regra de dependência

```
routes → controllers → models
```

Nunca o inverso: um model não pode importar um controller; um controller não pode importar código de rota. Isso garante que models sejam testáveis isoladamente e controllers não dependam do transporte HTTP.

## Composition root

O entry point da aplicação (ex.: `app.py`/`main.py`/`server.js`/`index.js`) atua como composition root: é o único lugar que instancia config, conecta ao banco, monta models, injeta models em controllers e registra rotas/blueprints/routers. Nenhuma outra camada deve instanciar suas próprias dependências diretamente — elas recebem o que precisam via parâmetro, construtor ou factory.

## Módulo de config

Um módulo único (`src/config/`) centraliza leitura de variáveis de ambiente e valores de configuração (porta, string de conexão, chaves). Nenhum outro arquivo lê `os.environ`/`process.env` diretamente para esses valores. Secrets nunca ficam hardcoded — sempre via variável de ambiente, com um `.env.example` documentando as chaves esperadas (sem valores reais).

## Error handling centralizado

Erros são tratados em um único ponto (`src/middlewares/`): um error handler/middleware que captura exceções não tratadas, mapeia para o código HTTP e formato de resposta apropriados, e registra logging quando necessário. Controllers e models lançam exceções de domínio; a camada de rota/middleware é quem decide o formato de resposta de erro.

## Granularidade

Um model por domínio (ex.: `OrderModel`, `ProductModel`) e um controller por domínio correspondente (ex.: `OrderController`, `ProductController`). Evitar um único model/controller "genérico" cobrindo múltiplos domínios não relacionados — isso reintroduz o anti-pattern de God Class.

## Adaptação às convenções idiomáticas da stack

- **Flask**: usar Blueprints como unidade de `views/routes` por domínio; `app.py`/`create_app()` como composition root (application factory); models como classes (SQLAlchemy) ou funções de acesso a dados puras se não houver ORM.
- **Express**: usar `Router()` por domínio em `routes/`; `index.js`/`server.js` como composition root que monta os routers; models como módulos de acesso a dados (Mongoose schemas, ou funções sobre o driver de banco).
- Para outras stacks, seguir o padrão idiomático equivalente de roteamento modular (ex.: `blueprints`/`routers`/`controllers` do framework), sem forçar nomes de diretório que não fazem sentido na convenção da linguagem.

## Adaptação a projetos parcialmente organizados

Antes de recriar qualquer camada, verificar o que já existe e decidir:

- Se já existe um diretório `models/` com separação por domínio e sem vazamento de responsabilidades, **preservar e apenas ajustar** o que estiver incorreto (ex.: query insegura) em vez de reescrever do zero.
- Se existe uma camada nomeada corretamente mas com conteúdo incorreto (ex.: `controllers/` com acesso direto a banco), mover o acesso a dados para um novo/existente model, mantendo o arquivo do controller e apenas removendo a responsabilidade indevida.
- Só recriar a estrutura inteira do zero quando o projeto for de fato monolítico (sem qualquer separação de camadas pré-existente).
- Em qualquer caso, o critério de sucesso é a estrutura final respeitar as regras acima — não o quanto de código foi reescrito.
