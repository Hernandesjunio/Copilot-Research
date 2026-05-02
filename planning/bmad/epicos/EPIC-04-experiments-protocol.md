# EPIC-04 — Experimentos MCP e hardening iterativo

## Objetivo

Medir o efeito real do servidor MCP no consumo de contexto, comparar iterações de tuning e deixar evidência reproduzível para decisões de produto.

## Estado implementado

O épico deixou de ser apenas hipótese de experimento. A implementação atual já inclui:

- smoke tests MCP `stdio` reais;
- comparação entre instância global antiga e versão local atual;
- comparação entre iterações locais;
- cenários específicos de experimento (`CEP/ViaCEP`, `Auth/JWT`, `Saga onboarding`);
- benchmark mínimo de relevância em `tests/benchmark/`;
- relatório agregado de qualidade em `scripts/build_quality_report.py`.

## Experimentos já executados

### Linha base e comparativos

- smoke local atual:
  - [`2026-05-02__smoke-mcp-stdio__local-atual.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__smoke-mcp-stdio__local-atual.md)
  - [`2026-05-02__smoke-mcp-stdio__local-atual-iteracao-2.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__smoke-mcp-stdio__local-atual-iteracao-2.md)
  - [`2026-05-02__smoke-mcp-stdio__local-atual-iteracao-3.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__smoke-mcp-stdio__local-atual-iteracao-3.md)
- comparativos:
  - [`2026-05-02__comparativo-smoke-mcp-stdio__local-atual-vs-iteracao-2.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__local-atual-vs-iteracao-2.md)
  - [`2026-05-02__comparativo-smoke-mcp-stdio__local-atual-iteracao-2-vs-iteracao-3.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__local-atual-iteracao-2-vs-iteracao-3.md)
  - [`2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual.md)

### Cenários de negócio avaliados

- cenário 2:
  - [`2026-05-02__comparativo-smoke-mcp-stdio__cenario-02-cep-viacep-local-atual-antes-vs-pos-tuning.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__cenario-02-cep-viacep-local-atual-antes-vs-pos-tuning.md)
- cenários 2, 3 e 4:
  - [`2026-05-02__smoke-mcp-stdio__local-atual-cenarios-2-3-4.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__smoke-mcp-stdio__local-atual-cenarios-2-3-4.md)
  - [`2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual-cenarios-2-3-4.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual-cenarios-2-3-4.md)
  - [`2026-05-02__consolidado-comparativo-melhoria__global-antigo-vs-local-atual-cenarios-2-3-4.md`](../../../research/experimentos-mcp/proximo-experimento/relatorio-cursor-teste/2026-05-02__consolidado-comparativo-melhoria__global-antigo-vs-local-atual-cenarios-2-3-4.md)

## O que foi endurecido no produto por causa dos experimentos

- descrições e contrato das tools;
- diagnósticos de busca;
- governança de sinónimos;
- benchmark mínimo de relevância;
- checklist por cenário;
- deteção de conflitos e precedência;
- relatório de qualidade com métricas operacionais.

## Métricas-alvo já suportadas pelo código

- `tool_failure_rate`
- `retry_rate`
- `zero_result_rate`
- `low_confidence_rate`
- `avg_search_confidence`
- `expected_instruction_rank`
- `precision_at_1`
- `precision_at_3`
- `precision_at_5`
- `mrr`

## Protocolo atualizado

### O que comparar

1. mesma query ou mesmo cenário;
2. mesmo corpus;
3. mesma infraestrutura de execução (`stdio`);
4. mesma família de prompts;
5. diferença controlada apenas em tuning do servidor ou instrução local.

### O que concluir

- se a melhoria foi de **ranking**;
- se a melhoria foi de **contrato/utilizabilidade**;
- se a melhoria foi apenas de **telemetria/explicabilidade**;
- onde o gargalo continua a ser **domínio local** e não MCP central.

## Regra metodológica importante

Quando o problema for específico do produto ou do fornecedor, a conclusão esperada **não** é “adicionar tudo ao MCP central”. O experimento deve distinguir:

- **guardrails transversais**: pertencem ao MCP central;
- **regras de negócio e integrações específicas**: pertencem à instruction local e ao código do serviço.

Exemplo explícito: `ViaCEP` é uma integração de domínio e não precisa virar instruction central do corpus. O MCP central deve ancorar HTTP, resiliência, cache, contrato de erro e observabilidade; os detalhes do fornecedor ficam locais.

## Próximos passos naturais

- repetir o protocolo com agente real ponta a ponta em Visual Studio/Copilot;
- expandir benchmark com mais queries reais e expected ids;
- testar efeitos de tuning por família de domínio sem degradar cenários fortes existentes.

## Aceite deste épico

- [x] smoke `stdio` real executado e documentado;
- [x] benchmark mínimo de relevância implementado;
- [x] comparativos entre versões/iterações registados;
- [x] hardening refletido no código Python do servidor;
- [ ] validação ponta a ponta com agente real em tarefa completa ainda pendente.
