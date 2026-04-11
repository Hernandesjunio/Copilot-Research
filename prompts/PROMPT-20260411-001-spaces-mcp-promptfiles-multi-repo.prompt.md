# Copilot Spaces vs MCP vs prompt files: contexto multi-repo e padronização

## Metadados
- **ID:** PROMPT-20260411-001
- **Data:** 2026-04-11
- **Contexto:** Pesquisa técnica (Copilot Chat / agente no Visual Studio); organização com 100+ repositórios e conhecimento transversal compartilhado
- **Objetivo:** Análise crítica e baseada em evidências sobre Spaces, MCP (tools vs resources) e prompt files para construção de contexto e padronização de tarefas; identificar trade-offs e estratégia híbrida realista
- **Hipótese (opcional):** Spaces pode estar subutilizado por limitações de produto/latência; MCP sem resources pode inflar tokens ou gerar round-trips; prompt files podem compensar previsibilidade localmente

## Prompt (cole exatamente o que enviar ao Copilot)

```
Estou conduzindo uma pesquisa técnica para melhorar o uso do GitHub Copilot em cenários com múltiplos repositórios (100+) e conhecimento transversal compartilhado.

Preciso de uma análise crítica e baseada em evidências (não marketing) sobre Copilot Spaces em comparação com MCP (Model Context Protocol) e prompt files para construção de contexto e padronização de tarefas.

Contexto empírico dos meus testes (Visual Studio):
- Consegui listar Copilot Spaces via integração no VS
- Consegui acessar repositórios
- Porém: interação prática com Spaces foi limitada; recuperação de custom instructions remotas com alta latência; fluxo iterativo (planejamento → implementação) não foi fluido

Críticas recebidas em uma análise técnica interna:
1) Copilot Spaces está sendo ignorado apesar de ser posicionado como mecanismo de compartilhamento de contexto entre equipes
2) MCP está sendo usado só com tools, sem resources — possível ineficiência
3) Prompt files estão subutilizados como mecanismo de padronização

Regras de resposta:
- Evite respostas genéricas. Priorize comportamento real do sistema, limitações de integração no VS, e trade-offs mensuráveis (tokens, round-trips, cache, rede, UX).
- Separe explicitamente: (a) fatos documentados / garantias de produto; (b) inferências técnicas plausíveis; (c) incerteza onde não houver fonte pública clara.
- Se citar documentação oficial, indique o tipo de fonte (docs / blog / changelog) sem precisar de URLs longas, a menos que seja essencial.

Responda de forma estruturada:

1) Capacidades reais e limitações atuais do Copilot Spaces em termos de:
   - recuperação de contexto (o que entra no prompt, quando, e com que granularidade)
   - latência (fontes prováveis: rede, cold start, indexação, sincronização de instructions)
   - integração com fluxo de desenvolvimento (planejamento + implementação iterativa)
   - uso via Visual Studio (o que a UI expõe vs o que o modelo efetivamente consome)

2) O comportamento que observei (latência alta e baixa interatividade) é esperado neste estágio? Quais causas técnicas mais prováveis (arquitetura cliente-servidor, políticas de context window, throttling, ausência de streaming de “space context”, etc.)?

3) Em cenário multi-repo com conhecimento compartilhado, compare Copilot Spaces vs MCP (tools vs resources) vs prompt files, avaliando em uma tabela ou bullets paralelos:
   - desempenho (latência, custo de tokens, número de idas e voltas)
   - controle de contexto (determinismo, vazamento de escopo, versionamento)
   - reutilização (por time, por repo, por máquina)
   - custo cognitivo para o desenvolvedor
   - previsibilidade (repetibilidade de outputs para mesma entrada)

4) Faz sentido usar Copilot Spaces como substituto ou complemento ao MCP? Em quais cenários cada abordagem é mais adequada (ex.: políticas corporativas, catálogo de APIs internas, runbooks, ADRs, padrões de código)?

5) Considerando limitações atuais do Copilot, proponha uma estratégia híbrida pragmática para:
   - reduzir latência percebida
   - melhorar recuperação de contexto sem explodir o context window
   - padronizar tarefas como planejamento BMAD e implementação (onde colocar cada artefato: repo, org, Space, MCP resource, prompt file)

Inclua uma seção final “Riscos e anti-padrões” (ex.: duplicar a mesma policy em três lugares; MCP tool que retorna payloads gigantes sem paginação; depender de Space para estado volátil da sessão).
```

## Notas pós-envio
- Comportamento observado (opcional, preencher depois)
