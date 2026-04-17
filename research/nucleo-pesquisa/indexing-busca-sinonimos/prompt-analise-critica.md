# Prompt(s) — análise crítica — sinónimos na busca

**Ferramenta alvo (opcional):** ChatGPT / Cursor

**Ficheiro de código a analisar:** [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py)

---

## Prompt principal

```
Você atuará como um Arquiteto de Software e Engenheiro de Busca/Recuperação de Contexto especializado em sistemas corporativos, indexação semântica, extensibilidade arquitetural e ferramentas de apoio ao desenvolvimento com IA.

## Objetivo da análise

Preciso que você faça uma análise técnica profunda do ficheiro `mcp-instructions-server/corporate_instructions_mcp/indexing.py` (fonte principal) e avalie criticamente o mecanismo atual de indexação e expansão por sinónimos.

O foco principal é verificar se a estratégia atual é adequada para um MCP corporativo cujo objetivo inicial é permitir a descentralização dos ficheiros `.github/instructions`, mas com capacidade real de funcionar de forma genérica e escalável para múltiplos contextos de desenvolvimento, assim como os ficheiros locais de instructions funcionam hoje.

## Contexto do problema

O ficheiro possui um mecanismo de sinónimos fixos, definidos manualmente em código (`SYNONYMS`, construção via `_build_synonym_lookup`, uso em `expand_query_with_synonyms`). Esse mecanismo parece funcionar para alguns cenários, porém identifiquei uma possível limitação arquitetural:

- a lista atual é estática;
- ela não parece extensível de forma natural;
- ela pode introduzir viés de domínio;
- ela depende de manutenção manual constante;
- ela pode não escalar bem para novos contextos técnicos.

Hoje os sinónimos aparentam estar muito focados em backend e alguns temas específicos. Porém o MCP que estou a construir precisa de atender cenários bem mais amplos, por exemplo:

- backend
- frontend
- desktop
- mobile / Flutter
- base de dados
- observabilidade
- segurança
- arquitetura
- integrações
- protocolos específicos
- mensagerias muito diferentes entre si

Exemplo importante:
- FIX messaging não deve ser tratado como se fosse semanticamente equivalente a RabbitMQ apenas porque ambos podem cair sob um guarda-chuva genérico de “mensageria”.
- Ou seja, existem domínios onde a similaridade superficial pode gerar recuperação incorreta de contexto.

O meu objetivo não é apenas identificar que “a lista é pequena”.
O meu objetivo é validar se existe uma limitação estrutural no modelo atual de indexação semântica e, se existir, propor uma solução técnica realmente extensível, eficiente e corporativa.

## O que preciso que faça

Quero uma análise técnica criteriosa e sem viés, cobrindo os pontos abaixo.

### 1. Entendimento do estado atual
Analise detalhadamente como o `indexing.py` funciona hoje, incluindo:

- parsing dos ficheiros markdown (`_parse_markdown`, frontmatter YAML, `InstructionRecord`)
- montagem do índice (`build_index`, ids únicos, limites de tamanho)
- tokenização (`tokenize_query`)
- normalização (`_normalize_token`, NFKD)
- construção do lookup de sinónimos (`SYNONYMS`, `_build_synonym_lookup`)
- expansão da query (`expand_query_with_synonyms`, pesos 1.0 vs 0.5, limite `[:5]`)
- estratégia de scoring (`score_record`, `expand_query_with_synonyms`, `PRIORITY_RANK`)
- limitações do uso de `blob.count(...)` sobre `InstructionRecord.search_blob()`
- impacto do peso por título, tags e prioridade

Explique de forma técnica como a busca funciona hoje de ponta a ponta (incluindo funções auxiliares relevantes como `excerpt_around_match`, `summarize_body`, se aplicável ao fluxo de recuperação).

### 2. Crítica arquitetural da abordagem atual
Avalie se a abordagem atual baseada em:

- sinónimos fixos em código
- lookup estático (`_SYNONYM_LOOKUP` ao importar o módulo)
- expansão lexical manual
- scoring por ocorrência textual

é adequada ou não para um MCP corporativo e genérico.

Quero que aponte:

- limitações reais
- riscos técnicos
- pontos de acoplamento
- custo de manutenção
- dificuldade de evolução
- risco de falso positivo semântico
- risco de falso negativo semântico
- risco de enviesamento por domínio
- impacto para escalabilidade organizacional
- impacto para múltiplas stacks e múltiplas equipas

### 3. Avaliação orientada ao objetivo do MCP
Considere explicitamente o objetivo do MCP neste cenário:

- servir como base centralizada de conhecimento/instructions
- reduzir dependência de ficheiros `.github/instructions` distribuídos
- continuar eficiente mesmo em cenários diversos
- funcionar para múltiplos domínios técnicos
- manter simplicidade operacional quando possível
- evitar soluções desnecessariamente complexas para o estágio atual

Com base nisso, avalie:
- se o modelo atual atende apenas um MVP restrito;
- se ele compromete uma evolução corporativa;
- se ele pode ser mantido como fallback;
- se ele deveria ser substituído ou complementado.

### 4. Comparação com alternativas técnicas
Quero que compare a abordagem atual com alternativas como:

- sinónimos definidos por configuração externa versionada
- taxonomias por domínio
- vocabulário controlado por área técnica
- expansão semântica baseada em metadados/tags
- stemming / lemmatization
- embeddings vetoriais
- busca híbrida lexical + semântica
- ontologias leves por domínio
- aliases definidos em frontmatter dos próprios ficheiros
- ranking por campos estruturados em vez de texto puro
- índice invertido simples
- BM25 ou estratégia similar
- re-ranking posterior
- plug-in/provider de expansão semântica por domínio

Não quero buzzword solta.
Quero comparação com prós, contras, complexidade, custo de implementação, custo operacional e aderência ao meu caso.

### 5. Proposta de arquitetura evolutiva
Proponha uma solução técnica evolutiva, pensando em fases.

Exemplo do tipo de raciocínio esperado:
- o que faz sentido no curto prazo
- o que faz sentido no médio prazo
- o que seria uma evolução futura
- o que deve continuar simples
- o que deve ser desacoplado desde já

A proposta deve considerar:

- extensibilidade
- baixo acoplamento
- manutenibilidade
- eficiência de busca
- previsibilidade do resultado
- explicabilidade do ranking
- governança corporativa
- possibilidade de múltiplos domínios técnicos coexistirem
- possibilidade de crescer sem reescrever tudo

### 6. Recomendação prática
Ao final, preciso de uma recomendação objetiva contendo:

#### a) Diagnóstico executivo
Resumo curto do problema arquitetural encontrado.

#### b) Diagnóstico técnico detalhado
Descrição detalhada do porquê a abordagem atual é limitada ou suficiente.

#### c) Melhor caminho recomendado
Diga qual solução recomenda para este contexto e por quê.

#### d) Estratégia incremental
Explique como migrar do estado atual para o recomendado sem ruptura desnecessária.

#### e) O que preservar do código atual
Identifique o que faz sentido manter.

#### f) O que refatorar imediatamente
Identifique os pontos que já valem refatoração.

#### g) O que não fazer agora
Aponte exageros técnicos que seriam prematuros para este momento.

## Restrições importantes

- Não invente requisitos que eu não mencionei.
- Não faça resposta genérica.
- Não trate embeddings como solução mágica.
- Não assuma que a melhor resposta é necessariamente IA/vetor.
- Não force complexidade desnecessária.
- Não proponha algo impossível de governar em ambiente corporativo.
- Não perca de vista que o objetivo principal é suportar o papel hoje exercido pelos `.github/instructions`.
- Separe factos observados no código de inferências e recomendações.
- Seja técnico, criterioso e pragmático.

## Forma da resposta esperada

Estruture a resposta exatamente nas secções abaixo:

1. Visão geral do funcionamento atual
2. Limitações arquiteturais identificadas
3. Riscos práticos para uso corporativo
4. Comparação entre alternativas
5. Arquitetura recomendada
6. Plano evolutivo em fases
7. Refatorações concretas no `indexing.py`
8. Conclusão e recomendação final

## Saída adicional desejada

Além da análise, gere também:

### A. Uma proposta de design alvo
Pode ser em texto estruturado ou pseudodiagrama.

### B. Uma lista de refatorações no código
Com sugestões concretas como:
- extrair provider de expansão semântica
- mover sinónimos para configuração externa
- suportar aliases por domínio
- separar scoring lexical de scoring semântico
- permitir estratégias plugáveis de ranking

### C. Um exemplo de interface/contrato
Se fizer sentido, proponha interfaces/classes para suportar evolução.
Exemplo:
- `IQueryExpansionProvider`
- `ISearchRanker`
- `IDomainVocabularyProvider`
- `ISearchIndex`

### D. Uma proposta de decisão arquitetural
No estilo ADR resumido:
- contexto
- problema
- decisão
- consequências
```

---

## Variantes (opcional)

### Variante A — foco em equivalências perigosas e viés de domínio

```
Use o mesmo enquadramento do prompt principal, mas priorize:

- O mapeamento actual em `SYNONYMS` (ex.: chave "mensageria" e termos associados) e o risco de equiparar protocolos ou produtos incomparáveis (ex.: FIX vs RabbitMQ).
- Falsos positivos por expansão lexical vs falsos negativos por vocabulário em falta.
- Como governar expansões por equipa/domínio sem duplicar listas em código.
- Testes de regressão mínimos sugeridos ao alterar sinónimos ou scoring.

Mantenha a mesma estrutura de saída (secções 1–8 + A–D).
```

### Variante B — foco em testes e regressão

```
Além da análise do prompt principal, inclua uma subsecção explícita:

- que casos de teste sugeriria (queries, documentos sintéticos, edge cases);
- como validar que uma mudança em `SYNONYMS` ou em `score_record` não degrada resultados esperados;
- se faz sentido golden files / fixtures no repositório para busca.

Referencie `mcp-instructions-server/docs/TESTS.md` ou a estrutura de testes existente apenas se a conhecer por leitura do repo; não invente ficheiros.
```

---

## Notas para quem cola o prompt

- O código relevante inclui: `InstructionRecord`, `build_index`, `_parse_markdown`, `tokenize_query`, `SYNONYMS`, `_build_synonym_lookup`, `expand_query_with_synonyms`, `score_record`, `PRIORITY_RANK`, `excerpt_around_match`, `summarize_body`.
- Se o analisador tiver acesso ao repo, pode cruzar com chamadas a estas funções noutros módulos do pacote `corporate_instructions_mcp`.
