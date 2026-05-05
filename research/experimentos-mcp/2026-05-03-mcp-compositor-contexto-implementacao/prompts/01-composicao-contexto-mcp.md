# Prompt 01 — Composição de contexto com MCP

## Modelo recomendado

`GPT 5.4`

Alternativo: `Sonnet 4.6`

## Objetivo da etapa

Compor o contexto necessário para implementar o cenário de outbox/mensageria sem ainda produzir patch.

## Instruções de uso

1. Abra uma nova thread.
2. Configure a sessão com o MCP `corporate-instructions` disponível.
3. Cole o prompt abaixo integralmente.
4. Não peça implementação nesta etapa.

## Prompt

```md
Atue como um engenheiro de software sênior focado em composição de contexto para implementação.

Objetivo desta etapa:
compor o contexto necessário para implementar o cenário de publicação de eventos de cliente com outbox e mensageria no repositório atual.

Neste momento, não quero patch, não quero código final e não quero relatório completo.
Quero apenas a composição de contexto antes da implementação.

Use o MCP `corporate-instructions` como fonte principal de contexto organizacional.
Use o código do repositório como evidência factual.
Se existirem instructions locais no repo, trate-as apenas como evidência complementar.

Importante:
- não assuma que o usuário conhece nomes de tools;
- use o MCP de forma transparente;
- se existir recurso, prompt composto ou ferramenta composta do próprio MCP para montar contexto, prefira isso em vez de orquestração manual exposta ao usuário;
- não implemente nada nesta etapa.

Contexto do cenário:
- quando um cliente é criado (`POST /clientes`) ou atualizado (`PUT /clientes/{id}`), deve existir registro de evento em Outbox na mesma transação;
- depois, o evento deve ser publicado para mensageria ou alternativa mínima coerente com a evidência do repositório;
- deve existir consumidor para atualizar read-model;
- deve haver idempotência;
- deve haver DLQ após N tentativas;
- o CRUD atual não pode ser quebrado.

Sua saída deve ter exatamente estas seções:

## 1. Decisões que precisam de contexto externo
Liste entre 3 e 7 decisões que dependem de contexto adicional.

## 2. Contexto composto via MCP
Para cada item relevante, informe:
- tema
- instruction, resource ou contexto MCP usado
- por que parece aplicável
- risco se aplicado sem validação do repo

## 3. Evidência do repositório
Liste arquivos, módulos, pacotes, configurações ou ausências que confirmem ou limitem as decisões.

## 4. Matriz de contexto
Monte uma tabela com as colunas:
- decisão
- origem principal (`mcp`, `repo`, `instruction_local`, `inferencia`)
- evidência
- status (`aplica`, `hipotese`, `bloqueado`)
- observação

## 5. Lacunas críticas
Liste o que ainda falta para decidir com segurança.

## 6. Regras para a próxima etapa
Explique objetivamente:
- o que pode ser planejado;
- o que não pode ser inferido;
- onde o agente deve parar e pedir confirmação humana.

Restrições:
- responda em português;
- não escreva patch;
- não proponha endpoints técnicos extras sem evidência;
- não assuma broker real se isso não estiver sustentado pelo repositório ou pelo contexto MCP;
- diferencie explicitamente FATO, HIPÓTESE e RISCO DE INTERPRETAÇÃO quando necessário.
```

## Saída esperada

Salvar o resultado em:

`artefatos/YYYY-MM-DD__contexto-composto.md`
