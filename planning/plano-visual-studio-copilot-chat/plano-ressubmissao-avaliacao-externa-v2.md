# Plano de Ressubmissao V2 - Avaliacao Externa `get_context_triggers`

## Objetivo

Gerar uma nova submissao para avaliacao externa que seja:

- comparavel entre rodadas;
- auditavel por evidencia;
- orientada a decisao (priorizacao e plano executavel);
- robusta para consumo por outra IA.

---

## Diagnostico da rodada anterior

## O que funcionou

- A resposta externa identificou gaps relevantes: contrato exposto ao host, evidence gate em duas fases, `tool_sequence`, governanca por catalogo.
- Houve boa profundidade tecnica e propostas concretas.

## O que falhou para benchmark

- O formato pedido nao foi seguido de forma estrita (faltou estrutura fixa e score final padronizado).
- A saida ficou mais "meta-analise" do que "avaliacao comparavel".
- Faltou matriz explicita de evidencia por afirmacao.
- Faltou plano final priorizado com impacto, esforco e criterio de aceite.

---

## Causa raiz

1. Escopo misturado: avaliacao de `copilot-instructions` versus revisao de um artefato de avaliacao externa.
2. Contrato de saida insuficientemente rigido (permitiu resposta livre).
3. Ausencia de "gates de conformidade" para forcar a estrutura final.

---

## Objetivo da nova rodada

Avaliar a qualidade da **avaliacao externa** como artefato de decisao, e nao apenas emitir opiniao tecnica.

Resultado esperado: saida reutilizavel para comparacao, priorizacao e execucao.

---

## Plano de Ressubmissao (executavel)

## Passo 1 - Pacote de entrada minimo (fixo)

Incluir sempre:

- `planning/plano-visual-studio-copilot-chat/avaliacao-externa-get-context-triggers.md`
- `planning/plano-visual-studio-copilot-chat/copilot-instructions.md`
- `planning/plano-visual-studio-copilot-chat/input.json`
- `planning/plano-visual-studio-copilot-chat/output.json`

Regra: "avaliar apenas com base nesses artefatos".

## Passo 2 - Critrios com escala operacional (0..2)

Usar 8 criterios (maximo 16 pontos):

1. Contrato exposto ao host (estrutura e validabilidade)
2. Evidence gate em duas fases (pre e pos-batch)
3. Qualidade da `tool_sequence` (guia sem rigidez excessiva)
4. Governanca catalogo vs procedural
5. Rastreabilidade evidencial
6. Qualidade da priorizacao (impacto x esforco)
7. Clareza de stop rules e fallbacks
8. Consumo por outra IA com baixa ambiguidade

## Passo 3 - Formato de saida obrigatorio (4 blocos)

- Bloco A: Analise em Markdown com seccoes fixas.
- Bloco B: Tabela de pontuacao por criterio.
- Bloco C: JSON estruturado com score, riscos e plano priorizado.
- Bloco D: Patch Plan (P0/P1/P2) com criterios de aceite.

## Passo 4 - Matriz de evidencia obrigatoria

Para cada achado, exigir:

- `claim`
- `evidence_file`
- `evidence_excerpt`
- `confidence` (`low|medium|high`)
- `gap_type` (`contract|orchestration|governance|evaluation-method`)

## Passo 5 - Regra anti-deriva

Se qualquer bloco obrigatorio estiver ausente ou incompleto:

- o avaliador deve refazer antes de concluir;
- nao aceitar resposta em texto livre sem score/matriz/json.

---

## Priorizacao recomendada para esta rodada

## P0 (imediato)

- Fechar contrato de resposta da avaliacao (formato fixo + JSON).
- Exigir matriz de evidencia por afirmacao.

## P1 (curto prazo)

- Resolver ordem de prioridade por objetivo:
  - foco em consumo por IA: contrato host primeiro;
  - foco em seguranca decisoria: reconciliacao pos-batch primeiro.
- Melhorar criterios de sucesso da `tool_sequence`.

## P2 (medio prazo)

- Migrar gradualmente governanca para modelo mais catalog-driven.

---

## Prompt V2 pronto para ressubmissao

> Copiar e colar como prompt unico.

```md
# Papel
Atue como revisor tecnico senior de orquestracao para IA (MCP/tool-calling/context engineering).

# Escopo da tarefa
Avalie a qualidade do artefato `avaliacao-externa-get-context-triggers.md` como documento de decisao.
Nao reavalie "a ferramenta em si" do zero; avalie se o documento avalia bem, mede bem e prioriza bem.

# Fontes permitidas
Use apenas os artefatos fornecidos:
- avaliacao-externa-get-context-triggers.md
- copilot-instructions.md
- input.json
- output.json
Se faltar evidencia, declarar: "sem evidencia suficiente".

# Criterios (nota 0, 1 ou 2)
1. Contrato exposto ao host
2. Evidence gate em duas fases
3. Qualidade da tool_sequence
4. Governanca catalogo vs procedural
5. Rastreabilidade evidencial
6. Priorizacao impacto x esforco
7. Stop rules e fallbacks
8. Consumo por outra IA (baixa ambiguidade)

# Escala
0 = fraco
1 = parcial
2 = forte
Pontuacao maxima = 16

# Saida obrigatoria (siga exatamente)

## BLOCO A - ANALISE (Markdown)
# 1. Resumo Executivo
# 2. Julgamento Geral
# 3. Achados por Eixo
## 3.1 Contrato
## 3.2 Evidence Gate
## 3.3 Tool Sequence
## 3.4 Catalogo vs Procedural
## 3.5 Priorizacao
# 4. Riscos
# 5. Veredito Final

## BLOCO B - SCORE
| Criterio | Nota | Justificativa |
|---|---:|---|

## BLOCO C - JSON
{
  "score_total": "X/16",
  "classificacao": "fraco|parcial|forte",
  "decision_confidence": "low|medium|high",
  "top_riscos": [
    {"id":"R1","descricao":"...","severidade":"alta|media|baixa"}
  ],
  "plano_priorizado": [
    {"prioridade":"P0|P1|P2","acao":"...","impacto":"alto|medio|baixo","esforco":"alto|medio|baixo","dependencias":["..."],"criterio_de_aceite":"..."}
  ]
}

## BLOCO D - MATRIZ DE EVIDENCIA
| claim | evidence_file | evidence_excerpt | confidence | gap_type |
|---|---|---|---|---|

# Regras obrigatorias
- Nao responder em formato livre.
- Se faltar algum BLOCO, refaça antes de concluir.
- Nao usar opinioes sem trecho de evidencia.
- Explicitar divergencias entre "recomendacao" e "capacidade comprovada por evidencia".
```

---

## Criterio de pronto (Definition of Done)

A nova rodada sera considerada valida somente se:

- entregar os 4 blocos obrigatorios;
- apresentar score total e classificacao;
- incluir matriz de evidencia completa;
- devolver plano priorizado P0/P1/P2 com criterio de aceite.

