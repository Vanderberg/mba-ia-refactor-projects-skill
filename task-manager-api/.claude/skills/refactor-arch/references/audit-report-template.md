# Audit Report Template (Fase 2)

Use este template exatamente para gerar o relatório da Fase 2, tanto na impressão para o usuário quanto no arquivo `audit-report.md` salvo na raiz do projeto auditado.

Regras de preenchimento:
- Todo finding deve ter arquivo e linhas verificados de fato (abrir o arquivo e conferir), nunca estimados.
- Ordenar os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW.
- Mínimo de 5 findings, com pelo menos 1 CRITICAL ou HIGH.
- Cada finding referencia um anti-pattern do catálogo (`references/antipatterns-catalog.md`).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome do anti-pattern>
File: <arquivo>:<linha-início>-<linha-fim>
Description: <o que foi encontrado, concreto e específico>
Impact: <consequência prática>
Recommendation: <correção proposta>

(repetir o bloco acima para cada finding, ordenado CRITICAL → HIGH → MEDIUM → LOW)

================================
Total: <N> findings
================================
```

## Exemplo preenchido (ilustrativo, não usar como conteúdo real)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Python 3.11 + Flask 2.3.2
Files:   6 analyzed | ~430 lines of code

## Summary
CRITICAL: 2 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Credenciais hardcoded
File: app.py:12-14
Description: String de conexão do banco com usuário e senha em texto plano diretamente no código-fonte.
Impact: Exposição de credenciais em qualquer cópia do repositório ou log de erro.
Recommendation: Mover para variável de ambiente carregada via módulo de config, com .env.example documentando a chave.

### [CRITICAL] SQL Injection por concatenação
File: app.py:47-49
Description: Query monta filtro de busca por f-string interpolando o parâmetro de query string diretamente na cláusula WHERE.
Impact: Permite injeção arbitrária de SQL via parâmetro de request.
Recommendation: Reescrever com query parametrizada usando placeholders do driver.

(...)

================================
Total: 9 findings
================================
```
