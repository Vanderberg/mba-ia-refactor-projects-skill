---
name: refactor-arch
description: Analisa, audita e refatora qualquer codebase para o padrão MVC em 3 fases (análise, auditoria, refatoração). Use sempre que o usuário invocar /refactor-arch ou pedir para auditar arquitetura, detectar anti-patterns ou code smells, refatorar para MVC, ou revisar separação de camadas.
---

# Refactor Arch

## Overview

Executa uma auditoria de arquitetura e refatoração para o padrão MVC (Model-View-Controller) em qualquer projeto backend, de forma agnóstica de stack (Python/Flask, Node.js/Express, etc). O trabalho acontece em 3 fases sequenciais e obrigatórias: **Análise → Auditoria → Refatoração**. Cada fase só lê seus arquivos de referência quando é executada (progressive disclosure) — não carregue todas as referências de uma vez.

## Restrições Gerais (aplicam-se às 3 fases)

- **Nunca inventar** arquivo ou número de linha. Todo finding do relatório deve ser verificado abrindo o arquivo real e conferindo as linhas — nunca estimado ou lembrado de memória.
- **Nunca iniciar a Fase 3** sem confirmação explícita do usuário (resposta afirmativa ao prompt de fim da Fase 2).
- **Nunca alterar o comportamento externo** da aplicação: mesmas rotas, mesmos formatos de request/response, mesmo schema de banco de dados.
- A skill deve funcionar em qualquer projeto backend — não referencie nomes de arquivos específicos de um projeto ao aplicar este workflow. Ela deve ser copiável entre projetos sem alterações.
- Trabalhe sempre a partir do projeto atual (diretório de trabalho), nunca assuma stack ou estrutura antes de inspecionar os arquivos reais.

## Fase 1 — Análise

Leia `references/analysis-heuristics.md` antes de começar esta fase.

Passos:
1. Detectar linguagem, framework (com versão) e dependências relevantes a partir dos arquivos de manifesto reais do projeto (nunca adivinhar — abrir e ler `requirements.txt`, `package.json`, etc.).
2. Inferir o domínio da aplicação lendo rotas, models e entidades existentes.
3. Mapear a arquitetura atual (monolítica / MVC parcial / camadas misturadas) e contar os arquivos-fonte relevantes, excluindo `node_modules`, `venv`, `.venv`, `.git`, diretórios de build/dist e caches.
4. Identificar tabelas/entidades de banco de dados quando existirem.
5. Imprimir o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Domain:        <descrição curta do domínio>
Architecture:  <descrição da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades, se aplicável>
================================
```

Ao final da Fase 1, prossiga automaticamente para a Fase 2 (não é necessário pedir confirmação aqui).

## Fase 2 — Auditoria

Leia `references/antipatterns-catalog.md` e `references/audit-report-template.md` antes de começar esta fase.

Passos:
1. Cruzar todo o código-fonte relevante contra o catálogo de anti-patterns, registrando cada finding com **arquivo e intervalo de linhas exatos** — abra cada arquivo e confira as linhas de fato, nunca estime.
2. Incluir detecção de **APIs deprecated** da linguagem/framework em uso, recomendando o equivalente moderno (ver seção correspondente no catálogo).
3. Ordenar os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW.
4. Garantir no mínimo 5 findings, com pelo menos 1 CRITICAL ou HIGH. Se encontrar menos que isso, revisar o código novamente contra o catálogo completo antes de concluir — não finalizar a fase com um relatório artificialmente curto.
5. Gerar o relatório seguindo estritamente `references/audit-report-template.md`. Imprimir o relatório completo E salvá-lo em `audit-report.md` na raiz do projeto sendo analisado.
6. Encerrar a fase pausando e pedindo confirmação explícita do usuário, terminando a mensagem com exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

A Fase 3 **só pode começar após resposta afirmativa explícita** do usuário nesta conversa. Se a resposta for negativa (ou ambígua), encerrar o trabalho entregando apenas o relatório da Fase 2 — não prosseguir para a Fase 3 sob nenhuma justificativa.

## Fase 3 — Refatoração

Só executar esta fase após confirmação explícita do usuário ao final da Fase 2.

Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md` antes de começar esta fase.

Passos:
1. Reestruturar o projeto para MVC corrigindo todos os findings do relatório da Fase 2, aplicando os padrões de transformação do playbook. Estrutura alvo (adaptar nomes de diretório às convenções idiomáticas da stack detectada):
   - `src/config/` — configuração extraída (secrets via variáveis de ambiente + arquivo `.env.example`, nunca hardcoded no código);
   - `src/models/` — um model por domínio, abstraindo todo acesso a dados;
   - `src/views/` ou `src/routes/` — apenas roteamento/apresentação, sem lógica de negócio;
   - `src/controllers/` — um controller por domínio, concentrando o fluxo de orquestração;
   - `src/middlewares/` — error handling centralizado (e outras cross-cutting concerns);
   - um entry point claro atuando como composition root (monta config, models, controllers e rotas).
2. **Adaptar-se ao contexto do projeto**: em projetos parcialmente organizados, aproveitar e melhorar a estrutura existente em vez de recriar tudo do zero; em monolitos completos, fazer a separação completa em camadas.
3. Preservar 100% do comportamento externo observável: mesmas rotas, mesmos formatos de resposta, mesmo schema de banco de dados.
4. Validar de forma real, nunca apenas assumida:
   - iniciar a aplicação e confirmar que ela sobe sem erros;
   - exercitar todos os endpoints originais (via `curl`, o arquivo `api.http` do projeto quando existir, ou equivalente) e comparar respostas com o comportamento anterior;
   - reauditar o código novo contra `references/antipatterns-catalog.md` confirmando zero anti-patterns remanescentes.
   - Se qualquer validação falhar, corrigir o problema e revalidar antes de reportar sucesso. Nunca imprimir um ✓ sem ter executado a verificação correspondente.
5. Imprimir o resumo final exatamente neste formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```
