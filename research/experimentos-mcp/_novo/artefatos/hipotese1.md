# Ticket canônico
Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código/MCP; caso contrário, declarar lacuna e não inventar).
- Se houver base no código/MCP para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver base, marcar como fora de escopo.

## Parte 1 — Execução

### 1) Seleção de guardrails e evidências (antes de codar)

#### Instructions aplicáveis
- `microservice-architecture-layering` (MCP): separar responsabilidades em `Api`, `Dominio`, `Interfaces`, `Repositorio`.
- `microservice-rest-http-semantics-and-status-codes` (MCP): semântica de `PUT` como substituição total; `GET` com `200`/`404`; `PUT` com `404` quando recurso não existe.
- `microservice-api-validation-and-error-contracts` (MCP): `400` para entrada inválida; não expor detalhes internos.
- `microservice-api-openfinance-patterns` (MCP): manter contrato de resposta já adotado no serviço (envelope `OpenFinanceResponse`) e tratamento consistente.
- `microservice-caching-imemorycache-policy` (MCP): chave estável de cache + TTL curto + invalidação explícita em mutações.
- `.github/copilot-instructions.md` (local): idioma português; usar MCP para decisões de design/erros/validação; declarar inferências quando faltar base.

#### Ficheiros/módulos que ancoraram decisões
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Responses/OpenFinanceResponse.cs`
- `ClientesAPI.Api/Extensions/ApiExtensions.cs`
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`

### 2) Ticket canônico
(igual ao topo; implementado no patch abaixo)

### 3) Plano BMAD

- **Background**
  - **FATO:** a API já usa Minimal API com envelope `OpenFinanceResponse<T>`.
  - **FATO:** existiam apenas `GET /` e `POST /` para clientes.
  - **FATO:** não havia operações de obter por `id` nem atualização completa no serviço/repositório.

- **Mission**
  - Implementar `PUT /api/v1/clientes/{id}` com persistência completa e contrato de erro.
  - Implementar `GET /api/v1/clientes/{id}` com cache em memória e invalidação na atualização.

- **Approach**
  1. Estender contratos em `Interfaces` para `ObterPorId` e `Atualizar`.
  2. Implementar regras de validação no `Dominio`.
  3. Implementar SQL parametrizado no `Repositorio` (Dapper) para leitura/atualização.
  4. Expor endpoints na `Api` com `status codes` e envelope consistentes.
  5. Adicionar `IMemoryCache` em DI, com chave estável `cliente:{id}:v1`, TTL 2 minutos e invalidação em `PUT`.

- **Delivery/validation**
  - Build do projeto `ClientesAPI.Api`.
  - Tentativa de `dotnet test` (sem suite de testes no projeto API).

### 4) Implementação (patch aplicado)

#### Arquivos alterados
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
  - Adicionados contratos: `ObterPorIdAsync(Guid id, ...)` e `AtualizarAsync(Guid id, ClienteRequisicao, ...)`.

- `ClientesAPI.Interfaces/IClienteServico.cs`
  - Adicionados contratos: `ObterClientePorIdAsync(Guid id, ...)` e `AtualizarClienteAsync(Guid id, ClienteRequisicao, ...)`.

- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
  - Implementada validação de `id` e requisição.
  - Implementados casos de uso: obter por id e atualizar cliente.

- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
  - Implementado `SELECT ... WHERE Id = @Id` com `QuerySingleOrDefaultAsync`.
  - Implementado `UPDATE ... OUTPUT INSERTED... WHERE Id = @Id` com SQL parametrizado.
  - `KeyNotFoundException` para cliente inexistente.

- `ClientesAPI.Api/Extensions/ApiExtensions.cs`
  - Registrado `AddMemoryCache` com `SizeLimit`.

- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
  - Adicionado `GET /api/v1/clientes/{id:guid}` com cache (`IMemoryCache`).
  - Adicionado `PUT /api/v1/clientes/{id:guid}` para atualização total.
  - Contratos de resposta: `200`, `400` (PUT), `404`, `408`, `500`.
  - Invalidação e atualização do cache após `PUT`.

#### Fora de escopo declarado
- **FATO:** não há evidência no código atual de integração HTTP externa para clientes.
- **Decisão:** exemplo de chamada externa com timeouts/resiliência ficou fora de escopo neste patch.

### 5) Validação

- Comando executado com sucesso:
  - `dotnet build "C:\Users\herna\source\repos\TestClientCorporateInstructions\ClientesAPI.Api\ClientesAPI.Api.csproj"`
  - Resultado: **build OK**, sem erros de compilação.

- Comando de teste executado:
  - `dotnet test "C:\Users\herna\source\repos\TestClientCorporateInstructions\ClientesAPI.Api\ClientesAPI.Api.csproj" --no-build`
  - **FATO:** projeto API não contém testes automatizados executáveis (não houve suíte efetiva para validar comportamento funcional).

---

## Parte 2 — Relatório técnico do experimento

### 0) Métricas de execução

- `inicio_iso`: N/A (timestamp bruto não exposto pela plataforma)
- `fim_iso`: N/A (timestamp bruto não exposto pela plataforma)
- `duracao_ms`: N/A (estimável apenas manualmente; não confiável para rigor)
- Latência por etapa (ms):
  - exploração/leitura: N/A
  - raciocínio/decisão: N/A
  - escrita do plano: N/A
  - escrita do relatório: N/A
- Uso de tools:
  - `qtd_tool_calls_total`: 21
  - `qtd_por_tool` (aprox):
    - `get_projects_in_solution`: 1
    - `get_files_in_project`: 5
    - `corporate_instructions_search_instructions`: 1
    - `corporate_instructions_get_instruction`: 5
    - `get_file`: 20
    - `file_search`: 2
    - `apply_patch`: 7
    - `run_command_in_terminal`: 6
    - `create_file`: 1
  - `sucessos`: 20
  - `falhas`: 1 (`dotnet test` apontando caminho de `.sln` inexistente)
  - `retries`: 1
- I/O de contexto:
  - `qtd_arquivos_lidos`: 20
  - `qtd_arquivos_citados`: 7
  - `qtd_trechos_citados`: N/A
  - `bytes_aprox_lidos`: N/A
- Tokens:
  - `tokens_input`: N/A
  - `tokens_output`: N/A
  - `tokens_input_est`: N/A
  - `tokens_output_est`: N/A
- Custo:
  - `custo_total`: N/A
  - `moeda`: N/A
- Tamanho do resultado:
  - `caracteres_resposta`: N/A
  - `qtd_itens_plano`: 4
- Rigor experimental:
  - `qtd_afirmacoes_FATO`: 13
  - `qtd_afirmacoes_HIPOTESE`: 4
  - `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`: 5

### 1) Evidência de uso de contexto

#### Decisões ancoradas em instruction local
- Uso obrigatório de MCP antes de decidir status/validação/erros.
- Linguagem e transparência de inferência.

#### Decisões ancoradas no código do repositório
- Manter envelope `OpenFinanceResponse<T>` (já existente).
- Manter padrão de organização por `Endpoints` + camadas `Interfaces/Dominio/Repositorio`.
- Dapper como tecnologia de persistência.

#### Decisões inferidas (declaradas)
- TTL de 2 minutos para cache: **HIPÓTESE** baseada em política MCP “TTL curto”; não havia valor explícito no repositório.
- Uso de `KeyNotFoundException` para traduzir “não encontrado”: **HIPÓTESE** para manter mudança mínima sem introduzir novo tipo de erro de domínio.

#### Lacunas
- Não há suíte de testes de contrato/integração para validar `PUT/GET{id}`.
- Não há política local explícita para `400` vs `422` no domínio atual; foi usado `400` por coerência com o código existente.

### 2) Qualidade técnica do plano

- **FATO:** o plano BMAD foi executado em sequência vertical (`Api`→`Interfaces`→`Dominio`→`Repositorio`).
- **FATO:** o patch é coerente com separação de camadas e mantém baixo acoplamento adicional.
- **RISCO DE INTERPRETAÇÃO:** ausência de `422` pode ser vista como simplificação excessiva se o domínio exigir distinção forte entre erro de contrato e erro de negócio.
- **Avaliação crítica:** tecnicamente correto para escopo pedido; porém sem testes automatizados, a confiabilidade operacional é limitada.

### 3) Limitações estruturais da abordagem

- **FATO:** há sobreposição entre instruções locais e MCP (tema de status codes/erro/arquitetura).
- **RISCO DE INTERPRETAÇÃO:** em múltiplos repositórios, essa sobreposição tende a gerar drift sem governança automática de versionamento de instruções.
- **FATO:** decisões ainda dependem de leitura manual do código para “contrato real” (envelope, exceptions, mapeamento).

### 4) Escalabilidade em 100+ repositórios

- **Conclusão técnica:** escala **parcialmente**.
- Sustenta-se quando:
  - há corpus MCP estável e versionado;
  - existe lint/CI para validar aderência a guardrails;
  - há templates de referência por stack.
- Deixa de sustentar quando:
  - cada repo mantém instruções locais divergentes sem reconciliação;
  - não há telemetria para detectar drift de contrato HTTP.
- Esforço de manutenção esperado:
  - alto no início (curadoria dos guardrails), médio contínuo com automação.
- Riscos operacionais previsíveis:
  - drift silencioso de contratos;
  - decisões inconsistentes por ambiguidades (`400` vs `422`, cache TTL, erro de domínio).

### 5) Experiência de uso

- Fluidez: boa para implementar vertical slice simples.
- Reprompt: baixo neste caso.
- Dependência de descoberta manual: média (necessário varrer arquivos-chave).
- Previsibilidade: média-alta quando MCP é consultado antes do patch.

## Avaliação (0–2)
- aderência ao contexto local: **2**
- qualidade técnica: **1**
- completude: **2**
- consistência: **1**
- escalabilidade da abordagem: **1**
- facilidade de manutenção: **1**

## Conclusão final
**instructions locais funcionam, mas não escalam bem**.

- Principal evidência: a implementação foi correta com guardrails MCP + código local, porém dependente de interpretação manual de lacunas (TTL, classificação de erro, ausência de testes), o que aumenta variabilidade entre repositórios.
- Principal limitação do experimento: ausência de suíte de testes e de métrica automática de aderência de contrato, reduzindo a força da validação empírica.

```json
EXPERIMENT_METRICS_JSON
{
  "inicio_iso": "N/A",
  "fim_iso": "N/A",
  "duracao_ms": "N/A",
  "latencia_por_etapa_ms": {
    "exploracao_leitura": "N/A",
    "raciocinio_decisao": "N/A",
    "escrita_plano": "N/A",
    "escrita_relatorio": "N/A"
  },
  "qtd_tool_calls_total": 21,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "get_files_in_project": 5,
    "corporate_instructions_search_instructions": 1,
    "corporate_instructions_get_instruction": 5,
    "get_file": 20,
    "file_search": 2,
    "apply_patch": 7,
    "run_command_in_terminal": 6,
    "create_file": 1
  },
  "sucessos": 20,
  "falhas": 1,
  "retries": 1,
  "qtd_arquivos_lidos": 20,
  "qtd_arquivos_citados": 7,
  "qtd_trechos_citados": "N/A",
  "bytes_aprox_lidos": "N/A",
  "tokens_input": "N/A",
  "tokens_output": "N/A",
  "tokens_input_est": "N/A",
  "tokens_output_est": "N/A",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_plano": 4,
  "qtd_afirmacoes_FATO": 13,
  "qtd_afirmacoes_HIPOTESE": 4,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 5
}
```

```json
DECISIONS_JSON
{
  "decisoes": [
    {
      "decisao": "Implementar `PUT /api/v1/clientes/{id}` como atualização total com retorno do recurso atualizado",
      "ancoragem": "MCP",
      "evidencia": "microservice-rest-http-semantics-and-status-codes",
      "risco": "baixo",
      "como_validar": "Teste de contrato HTTP para PUT + verificação de persistência no banco"
    },
    {
      "decisao": "Adicionar `GET /api/v1/clientes/{id}` com cache e chave estável `cliente:{id}:v1`",
      "ancoragem": "MCP",
      "evidencia": "microservice-caching-imemorycache-policy",
      "risco": "medio",
      "como_validar": "Teste de integração medindo hits de cache e invalidação após PUT"
    },
    {
      "decisao": "Manter envelope `OpenFinanceResponse<T>` em sucesso/erro",
      "ancoragem": "codigo_repo",
      "evidencia": "ClientesAPI.Api/Responses/OpenFinanceResponse.cs",
      "risco": "baixo",
      "como_validar": "Inspecionar payload de resposta dos novos endpoints"
    },
    {
      "decisao": "Mapear validação de entrada para `400` via `ArgumentException`",
      "ancoragem": "MCP",
      "evidencia": "microservice-api-validation-and-error-contracts",
      "risco": "medio",
      "como_validar": "Casos de teste com nome/email vazios e id inválido"
    },
    {
      "decisao": "Não implementar exemplo de integração HTTP externa com resiliência",
      "ancoragem": "inferencia",
      "evidencia": "N/A",
      "risco": "baixo",
      "como_validar": "Revisão de escopo: inexistência de integração externa no código atual"
    }
  ]
}
```