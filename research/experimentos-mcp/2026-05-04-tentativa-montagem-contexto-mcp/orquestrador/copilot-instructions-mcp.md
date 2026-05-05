# Instruções locais

- Responde em português.
- Nunca exponhas segredos, tokens ou PII.
- Não assumas serviços, infraestrutura ou integrações sem evidência no repo.

## Repositório

- API de gestão de clientes em camadas. Stack principal: C# / .NET 8 / ASP.NET Core.

## Padrões organizacionais (MCP `corporate-instructions`)

- O corpus normativo não está neste repo.
- Este ficheiro governa a **orquestração local** e as **restrições específicas do repo**.
- O corpus governa as **rules normativas reutilizáveis**.
- O código do repo governa a **evidência factual**.
- Chama o MCP antes de decidir padrões cross-cutting: segurança, contratos API, resiliência, mensageria, dados, testes, observabilidade, estilo, ou quando houver dúvida se existe policy aplicável.

### Tools

Usa sempre os **nomes reais** das tools expostas pelo MCP.

| Tool | Gatilho |
|------|----------|
| `corporate_instructions_list_instructions_index` | visão geral / ids / temas |
| `corporate_instructions_search_instructions` | tema conhecido / busca por palavras-chave |
| `corporate_instructions_get_instructions_batch` | leitura obrigatória antes de decidir/aplicar |
| `corporate_instructions_resolve_instruction_context` | contexto inicial rápido / tema pouco delimitado |
| `corporate_instructions_get_context_triggers` | decidir sequência de orquestração quando o pedido estiver ambíguo/cross-cutting |
| `corporate_instructions_validate_applicability` | evidence gate formal por policy/artefacto com `workspace_evidence` |
| `corporate_instructions_build_compliance_matrix` | consolidar estado operacional após aplicabilidade e observações |
| `corporate_instructions_get_normative_checklist` | cenário repetível |
| `corporate_instructions_detect_instruction_conflicts` | múltiplas policies plausíveis |

### Matriz rápida

- Tema ou repo pouco conhecido -> `corporate_instructions_list_instructions_index` ou `corporate_instructions_resolve_instruction_context`.
- Pedido ambíguo/cross-cutting -> `corporate_instructions_get_context_triggers` para sequência recomendada.
- Tema conhecido -> `corporate_instructions_search_instructions`.
- Policy candidata encontrada -> `corporate_instructions_get_instructions_batch` antes de decidir.
- Policy candidata com evidence gate -> `corporate_instructions_validate_applicability`.
- Com aplicabilidade decidida + observações do artefacto -> `corporate_instructions_build_compliance_matrix`.
- Cenário conhecido e repetível -> `corporate_instructions_get_normative_checklist`.
- Mais do que uma policy plausível -> `corporate_instructions_detect_instruction_conflicts`.
- Sem batch lido -> não aplicar policy.
- Só depois -> BMAD e implementação.

### Protocolo

1. **Discover**
   - Se o tema ou o repo ainda forem pouco conhecidos, usa `corporate_instructions_list_instructions_index` ou `corporate_instructions_resolve_instruction_context`.
   - Se o pedido estiver ambíguo, de alto risco ou cross-cutting, usa `corporate_instructions_get_context_triggers` para escolher sequência e modo de execução.
   - Se o tema já for conhecido, usa `corporate_instructions_search_instructions` com palavras-chave; sobe `max_results` até 20 quando o tema for largo.
2. **Read**
   - Resultados de search são atalhos; não apliques policy só com base neles.
   - Lê sempre o corpo com `corporate_instructions_get_instructions_batch` antes de impor padrão, contrato ou implementação.
   - Se o batch truncar, repete apenas para os ids em falta.
3. **Evidence gate**
   - Ao ler o batch, verifica também o `frontmatter`.
   - Se `workspace_evidence_required=true`, procura `workspace_signals` no código antes de aplicar a policy.
   - Formaliza essa decisão com `corporate_instructions_validate_applicability`.
   - Sem evidência, segue `on_absence`; por omissão, trata como **hipótese** e não introduzas infraestrutura nova por inferência.
4. **Decide**
   - Código do repo = facto.
   - `kind: policy` lida no batch = regra aplicável; cita o `id`.
   - `kind: reference` = guia; segue com ressalva.
   - Consolida o estado operacional com `corporate_instructions_build_compliance_matrix` (não confundir ausência de evidência com não conformidade).
   - Se o cenário for repetível, usa `corporate_instructions_get_normative_checklist` para cobertura.
   - Se houver mais do que uma policy plausível, usa `corporate_instructions_detect_instruction_conflicts`.
   - Sem corpus ou sem evidência suficiente, nomeia a lacuna e apresenta hipótese ou pede input humano.
5. **Plan**
   - Só depois sintetiza um **BMAD** mínimo com **Background** (ficheiros e `id`s aplicáveis), **Mission**, **Approach** e **Delivery/validation**.
   - Acrescenta **riscos**, **dependências** e **critérios de aceite técnico** quando a mudança for cross-cutting ou tocar contrato, dados, segurança ou operação.

### Escala

- Mantém neste ficheiro apenas a **orquestração** de consumo do MCP; não dupliques conteúdo normativo do corpus.
- Trata os `id`s recuperados como fonte canónica reutilizável entre projetos.
- Padroniza queries, cenários de checklist e critérios de evidência para reduzir deriva entre repositórios e ferramentas.
- Não uniformizes infraestrutura por suposição só para manter consistência entre projetos.

## Fluxo

- Antes de mudar ficheiros sensíveis, lê o alvo.
- Depois de alterações relevantes, faz build/testes.
