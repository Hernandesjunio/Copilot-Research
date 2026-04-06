# Instructions nativas vs MCP no Visual Studio

## Metadados
- **ID:** PROMPT-20260403-002
- **Data:** 2026-04-03
- **Contexto:** Copilot Chat no Visual Studio; repositório com `.github/instructions` (~100 Markdown); avaliação de MCP como camada de busca e composição de contexto
- **Objetivo:** Definir divisão prática de responsabilidades entre instructions nativas e MCP, sem duplicar a base existente
- **Hipótese (opcional):** Um modelo híbrido (baseline estável + recuperação sob demanda) maximiza utilidade sem substituir o mecanismo nativo

## Prompt (cole exatamente o que enviar ao Copilot)

```
Quero entender, em nível funcional e sem solicitar qualquer detalhe interno sensível, como devo combinar instruções nativas do repositório com um MCP no Visual Studio.

Contexto:
- Já possuo uma base grande de conhecimento em .github/instructions, com cerca de 100 arquivos Markdown pequenos, organizados por temas e escopo.
- Essas instructions já funcionam bem hoje para fornecer contexto arquitetural e convenções do projeto.
- Estou avaliando construir um MCP para elevar esse modelo, atuando como camada de busca, seleção, composição e priorização de contexto.
- Meu objetivo não é duplicar instruções, mas entender como dividir responsabilidades entre instructions nativas e MCP.

Explique de forma prática:

1) Quando uma informação deve permanecer em custom instructions nativas
2) Quando essa informação deveria migrar para resources/tools de um MCP
3) Como evitar duplicidade, conflito ou redundância entre instructions e MCP
4) Se você tende a se beneficiar mais de:
   - instruções estáveis e sempre presentes
   - contexto recuperado sob demanda
   - modelo híbrido
5) Como estruturar um MCP para usar a base existente de instructions como fonte indexável, sem perder o valor do mecanismo nativo
6) Qual formato seria mais eficiente para um MCP retornar esse conteúdo:
   - trecho literal
   - resumo
   - evidências ranqueadas
   - combinação dos três
7) Como priorizar apenas as instructions relevantes para a tarefa atual
8) Quais riscos existem quando muitas instructions pequenas coexistem com tools externas que também retornam contexto

Ao responder, diferencie:
- o que é claramente suportado
- o que é inferência prática
- o que pode variar conforme o modo agente e a configuração do ambiente
```

## Notas pós-envio
- Resposta do Copilot registada em `responses/PROMPT-20260403-002-instructions-nativas-vs-mcp.response.md` (2026-04-03).
