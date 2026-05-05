# Prompt 03 — Implementação guiada por contexto e plano

## Modelo recomendado

`Codex 5.3`

Alternativo: `Sonnet 4.6`

## Objetivo da etapa

Executar a implementação com base no contexto composto e no plano BMAD já aprovados.

## Instruções de uso

1. Abra uma nova thread.
2. Forneça como entrada o artefato da etapa 1 e o da etapa 2.
3. Cole o prompt abaixo.
4. Nesta etapa, o objetivo é codificar e validar minimamente.

## Prompt

```md
Implemente o cenário de outbox/mensageria no repositório atual usando como base obrigatória:

1. o artefato de composição de contexto;
2. o plano BMAD já definido.

Objetivo:
produzir a menor implementação coerente com o cenário, mantendo o MCP como compositor de contexto e evitando inferência desnecessária.

Regras obrigatórias:
- siga o plano BMAD;
- não reabra o desenho do experimento;
- não invente infraestrutura sem evidência;
- não crie endpoints técnicos públicos extras sem justificativa explícita;
- se existir lacuna crítica bloqueante, sinalize antes do patch;
- prefira mudanças mínimas e verificáveis.

Cenário técnico:
- `POST /clientes` e `PUT /clientes/{id}` devem registrar evento no outbox na mesma transação;
- publicar evento para mensageria real ou alternativa mínima coerente com MCP + repo;
- consumidor atualiza read-model;
- idempotência deve ser demonstrável;
- DLQ após N tentativas;
- preservar CRUD atual.

Sua saída deve incluir:

## 1. Resumo pré-patch
- o que vai implementar;
- o que ficou bloqueado;
- o que continua como hipótese controlada.

## 2. Patch
Aplique as mudanças necessárias no código.

## 3. Validação mínima executada
Informe build e testes executados, ou explique objetivamente o que não foi possível executar.

## 4. Decisões aplicadas
Liste decisões em formato curto com:
- decisão
- origem principal (`mcp`, `repo`, `instruction_local`, `inferencia`)
- evidência resumida

## 5. Pendências
Liste apenas pendências reais que impactam a robustez ou a validação.

Restrições:
- responda em português;
- diferencie FATO, HIPÓTESE e RISCO DE INTERPRETAÇÃO quando isso afetar a implementação;
- mantenha foco na mudança mínima necessária.
```

## Saída esperada

Salvar a resposta bruta desta execução em:

`artefatos/YYYY-MM-DD__implementacao-execucao.md`
