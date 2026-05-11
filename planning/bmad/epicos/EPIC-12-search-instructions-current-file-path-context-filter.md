# EPIC-12 — `search_instructions` com `current_file_path` opcional para filtro contextual declarativo

## Objetivo

Implementar a [ADR-004](../../adr/ADR-004-search-instructions-current-file-path-context-filter.md): evoluir `search_instructions` **in-place** para aceitar `current_file_path` como evidência contextual opcional, usada pelo MCP em filtros declarativos de aplicabilidade, principalmente `applies_to` do **Corpus Query Expansion Map**, sem leitura do workspace do utilizador e sem introduzir `context_mode`.

## Motivação

A ADR-002 já define semântica dependente de `current_file_path` para `applies_to`, mas a tool pública `search_instructions` ainda não expõe esse argumento. Isso limita a precisão contextual da expansão em tarefas com ficheiro em foco e mantém a busca em modo excessivamente genérico mesmo quando o host possui essa evidência.

## Escopo

### Em escopo

- Adicionar `current_file_path: str | None = None` ao contrato público de `search_instructions`.  
- Preservar todos os parâmetros existentes da tool (`query`, `tags`, `max_results`, `include_diagnostics`, `tags_mode`, `kind`, `scope`, `priority`, `workspace_evidence_required`, `telemetry_expected_instruction_id`, `queries`, `max_results_per_query`).  
- Normalização sintática mínima de `current_file_path` antes de o encaminhar ao pipeline.  
- Propagar `current_file_path` para `expand_query_with_metadata(...)`.  
- Diagnóstico opcional indicando se o valor foi considerado, ignorado ou ausente.  
- Atualização de README, descrição da tool e docs de testes para explicar a nova semântica.  
- Testes unitários/integrados cobrindo a passagem do argumento pela tool.

### Fora do escopo

- Leitura do ficheiro físico ou do workspace do utilizador.  
- Verificação de existência no disco, root real do projeto, ou classificação ficheiro/diretório por IO.  
- `context_mode`, `current_directory` ou `related_file_paths`.  
- BM25, ranking vetorial, alteração do mecanismo base de token scoring.  
- Mudança semântica dos filtros já existentes.  
- Reescrita da tool ou versionamento `v2`.

## Princípios de implementação

- Mudança **aditiva** e **in-place**.  
- `current_file_path` é evidência contextual, não verdade absoluta.  
- O MCP deve usar o campo apenas em mecanismos declarativos já definidos, não para inferir estado oculto do projeto.  
- Quando o campo não puder ser aproveitado, a busca deve fazer fallback silencioso para o comportamento atual, com diagnóstico opcional.

## Fases

| Fase | Conteúdo |
|------|----------|
| **1** | Assinatura da tool + schema MCP + docstring |
| **2** | Normalização sintática de `current_file_path` e passagem ao pipeline de expansão |
| **3** | Diagnósticos e telemetria coerentes com o novo campo |
| **4** | Testes unitários, smoke e integração |
| **5** | Documentação e exemplos de uso |

## Tasks técnicas (checklist)

- [ ] Atualizar a assinatura de `search_instructions` em `server.py` com `current_file_path` opcional.  
- [ ] Ajustar o schema MCP / descrição da tool para incluir o novo argumento sem quebrar compatibilidade.  
- [ ] Implementar normalização sintática mínima do path recebido (trim, nulo/vazio, separadores).  
- [ ] Encaminhar `current_file_path` para `expand_query_with_metadata(tokens, expansion_map=..., current_file_path=...)`.  
- [ ] Garantir que o fluxo multi-query reutiliza o mesmo `current_file_path` da chamada.  
- [ ] Incluir em `include_diagnostics` um bloco explícito sobre uso de `current_file_path` (`provided`, `normalized`, `used_for_expansion`, `ignored_reason` quando aplicável).  
- [ ] Rever telemetria para resumir o novo argumento sem expor paths completos quando isso não for desejável pelo nível configurado.  
- [ ] Atualizar `README.md`, `docs/TESTS.md` e exemplos de contrato/documentação da tool.

## Testes (plano mínimo)

1. **Compatibilidade**: chamadas antigas de `search_instructions` continuam válidas sem `current_file_path`.  
2. **Single-query com path**: `current_file_path` é propagado ao pipeline e altera a elegibilidade de `applies_to` conforme ADR-002.  
3. **Single-query sem path**: comportamento continua igual ao fluxo atual, com `applies_to` ignorado quando aplicável.  
4. **Path sintaticamente inválido/vazio**: busca não falha; o valor é tratado como ausente ou ignorado.  
5. **Multi-query**: `queries` + `current_file_path` funcionam no mesmo pedido sem regressão.  
6. **Diagnóstico**: quando `include_diagnostics = true`, o payload explica se `current_file_path` foi usado.  
7. **Sem regressão arquitetural**: não há leitura do workspace nem nova dependência de filesystem fora do corpus de instructions.

## Critérios de aceite (épico)

- [ ] Todos os critérios da ADR-004 satisfeitos.  
- [ ] O contrato evoluiu in-place, sem remover parâmetros já existentes.  
- [ ] `current_file_path` influencia a expansão contextual apenas por mecanismos declarativos compatíveis com ADR-002.  
- [ ] `context_mode` não foi introduzido nesta iteração.  
- [ ] `pytest` do servidor MCP continua verde sem regressões não explicadas.  
- [ ] Documentação da tool orienta o agente a não inventar caminhos.

## Riscos

- O host pode não enviar `current_file_path`, reduzindo o ganho esperado.  
- O host pode enviar path impreciso; mitigar com semântica conservadora e diagnóstico.  
- Mau uso do campo pode levar a overfitting de contrato se a implementação extrapolar para leitura de workspace; mitigar com revisão explícita contra ADR-004.

## Plano de rollback

- Reverter a adição do parâmetro e o encaminhamento ao pipeline de expansão.  
- Manter a semântica prévia da tool sem impacto sobre ADR-002, que continua válida no nível do motor.

## Métricas de sucesso

- Maior precisão em queries ambíguas quando o ficheiro em contexto é informado corretamente.  
- Nenhuma regressão em queries gerais sem `current_file_path`.  
- Diagnóstico suficientemente claro para mostrar quando `applies_to` foi activado ou ignorado por ausência de path.

## Referências cruzadas

- [ADR-004 — decisão](../../adr/ADR-004-search-instructions-current-file-path-context-filter.md)  
- [ADR-002 — Corpus Query Expansion Map](../../adr/ADR-002-corpus-query-expansion-map.md)  
- [EPIC-10 — Expansion Map](EPIC-10-corpus-query-expansion-map.md)  
- [EPIC-07 — Search ranking quality](EPIC-07-search-ranking-quality-and-corpus-integrity.md)
