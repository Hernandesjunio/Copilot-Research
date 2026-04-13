Haja como um arquiteto de software sênior com forte capacidade analítica e experiência em experimentos técnicos.

Sua tarefa é gerar uma apresentação TÉCNICA, detalhada e orientada a evidências, baseada no documento abaixo (fonte única de verdade):

[COLE AQUI O DOCUMENTO COMPLETO]

OBJETIVO:
Apresentar uma análise técnica comparativa entre:
- Tools vs Prompts vs Resources no MCP
- MCP vs .github/instructions
- STDIO vs HTTP

A apresentação será para um público técnico, então deve conter:
- análise crítica
- comparações estruturadas
- tabelas
- critérios de avaliação
- trade-offs reais

==================================================
ESTILO DA APRESENTAÇÃO
==================================================

- Mais técnico que executivo
- Uso de tabelas comparativas
- Uso de bullets objetivos
- Pode conter mais conteúdo por slide (sem exagero)
- Linguagem direta e precisa
- Sem marketing
- Sem simplificações excessivas

==================================================
ESTRUTURA OBRIGATÓRIA
==================================================

Gerar os slides com essa estrutura:

1. Título
2. Contexto técnico do problema
3. Limitações do modelo atual (.github/instructions)
4. Hipótese técnica (MCP como solução)

5. MVP IMPLEMENTADO (OBRIGATÓRIO DETALHAR AS TOOLS)
6. Arquitetura e fluxo de funcionamento
7. Metodologia do experimento
8. Cenários testados
9. Critérios de avaliação

10. Comparação: Tools vs Prompts vs Resources (TABELA)
11. Análise detalhada por capacidade

12. Comparação: MCP vs Instructions (TABELA)
13. Comparação: STDIO vs HTTP (TABELA)

14. Resultados observados
15. Limitações identificadas
16. Riscos técnicos
17. Decisão arquitetural

18. Possível arquitetura híbrida
19. Próximos passos técnicos
20. Conclusão

==================================================
SLIDE OBRIGATÓRIO — MVP E TOOLS
==================================================

Você DEVE criar um slide específico explicando as 3 tools implementadas no MVP, com nível técnico adequado.

As tools são:

1. list_instructions_index
2. search_instructions
3. get_instruction

Para cada tool, explicar claramente:

- objetivo
- entrada (inputs)
- processamento interno
- saída (output)
- papel no fluxo geral
- por que ela existe

==================================================
DETALHAMENTO TÉCNICO DAS TOOLS (OBRIGATÓRIO)
==================================================

Você DEVE refletir corretamente o comportamento descrito no documento:

### list_instructions_index
- varre arquivos .md no INSTRUCTIONS_ROOT
- extrai metadados e frontmatter
- gera catálogo com hash (SHA256)
- permite descoberta do corpus

### search_instructions
- recebe query (texto livre) e opcionalmente tags
- tokeniza query
- aplica scoring heurístico léxico (determinístico)
- realiza ranking dos documentos
- gera excerpt baseado no match
- retorna contexto combinado (composed_context)

### get_instruction
- recebe id ou path
- valida segurança de path (evita traversal)
- lê conteúdo completo
- aplica truncagem (max_chars)
- retorna conteúdo + metadados

==================================================
SLIDE OBRIGATÓRIO — FLUXO (MUITO IMPORTANTE)
==================================================

Gerar um slide mostrando o fluxo lógico:

1. list → descoberta
2. search → seleção
3. get → recuperação completa

Explicar como isso implementa:
- two-stage retrieval
- otimização de contexto
- controle de custo

==================================================
TABELAS OBRIGATÓRIAS
==================================================

### Tools vs Prompts vs Resources

Critérios obrigatórios:
- capacidade de retrieval dinâmico
- controle operacional
- determinismo
- custo de tokens
- escalabilidade
- facilidade de uso
- latência
- governança
- testabilidade

---

### MCP vs .github/instructions

Critérios obrigatórios:
- centralização
- reuso
- manutenção
- custo de contexto
- precisão
- escalabilidade
- flexibilidade
- acoplamento

---

### STDIO vs HTTP

Critérios obrigatórios:
- latência
- experiência do dev
- complexidade
- escalabilidade
- governança
- overhead operacional

==================================================
ANÁLISE TÉCNICA (OBRIGATÓRIO)
==================================================

Você DEVE refletir fielmente o documento:

- Tools implementam lógica e política (ranking, truncagem, etc)
- Prompts não fazem retrieval real
- Resources não fazem seleção dinâmica
- Ranking é determinístico (heurístico léxico)
- Prompt não substitui tool sem reimplementar lógica
- Resource pode complementar, mas não substituir discovery/search
- STDIO tem melhor UX local
- HTTP tem melhor governança

==================================================
METODOLOGIA DO EXPERIMENTO
==================================================

Você DEVE estruturar:

- o que foi testado
- como foi testado
- variáveis consideradas
- limitações do experimento

==================================================
FORMATO DE CADA SLIDE
==================================================

## Slide X - [Título]

**Objetivo do slide:**
(frase técnica curta)

Conteúdo:
- bullet
- bullet
- bullet

Se necessário:
[TABELA]

==================================================
IMAGENS (IMPORTANTE)
==================================================

Para slides técnicos, sugerir imagens como:

- fluxo das 3 tools (pipeline)
- arquitetura MCP
- comparação tools vs prompt vs resource
- STDIO vs HTTP

Descrever de forma que outra IA consiga gerar.

==================================================
REGRAS CRÍTICAS
==================================================

- NÃO simplificar demais
- NÃO omitir limitações
- NÃO inventar comportamento das tools
- NÃO gerar conteúdo genérico
- NÃO afirmar ganhos sem base

==================================================
RESULTADO FINAL
==================================================

A apresentação deve parecer:

- um estudo técnico real
- uma análise arquitetural madura
- um experimento comparativo consistente

Gere a apresentação completa seguindo essa estrutura.