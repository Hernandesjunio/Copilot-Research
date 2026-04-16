# Ticket canônico
Implemente o seguinte “vertical slice”:
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache.
- Exemplo de integração externa HTTP com timeout/resiliência: **incluído no relatório como exemplo contextual (fora do patch)**.

---

## Parte 1 — Execução

### 1) Seleção de guardrails e evidências (antes de codar)

#### Instructions aplicáveis
- **instruction_local: `.github/copilot-instructions.md`**
  - Decisões: idioma (`português`), uso obrigatório de MCP em decisões cross-cutting, build/teste após mudança substancial.
- **MCP `assistant-workflow-bmad-planning-and-controlled-inference`**
  - Decisões: plano BMAD obrigatório; rotular inferência.
- **MCP `microservice-architecture-layering`**
  - Decisões: manter separação `Api`/`Dominio`/`Interfaces`/`Repositorio`.
- **MCP `microservice-domain-interfaces-models-repository`**
  - Decisões: contratos em `Interfaces`, implementação em `Repositorio`, orquestração no `Dominio`.
- **MCP `microservice-rest-http-semantics-and-status-codes`**
  - Decisões: semântica de `PUT` (substituição total) e `GET`, status codes HTTP coerentes.
- **MCP `microservice-api-validation-and-error-contracts`**
  - Decisões: validação de entrada e mapeamento de erros (`400`, `404`, `408`).
- **MCP `microservice-api-openfinance-patterns`**
  - Decisões: preservar envelope de resposta já existente (`OpenFinanceResponse<T>`).
- **MCP `microservice-api-error-catalog-baseline`**
  - Decisões: `404` para recurso inexistente em leitura/escrita por id.
- **MCP `microservice-caching-imemorycache-policy`**
  - Decisões: cache em leitura por id com chave estável e TTL curto.
- **MCP `microservice-data-access-and-sql-security`**
  - Decisões: SQL parametrizado + timeout explícito no Dapper.
- **MCP `microservice-integration-httpclientfactory-contracts` + `microservice-resilience-polly-timeouts-and-circuit-breaker`**
  - Decisões: exemplo de integração HTTP resiliente (fora de escopo do patch por ausência de integração real no repo).

#### Arquivos/módulos que ancoraram decisões
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs` (padrão de endpoints, envelope, status atuais)
- `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs` (mapeamento global existente)
- `ClientesAPI.Api/Extensions/ApiExtensions.cs` (registro de serviços da API)
- `ClientesAPI.Interfaces/IClienteServico.cs` e `ClientesAPI.Interfaces/IClienteRepositorio.cs` (contratos de camadas)
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs` (validação de domínio atual)
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs` (padrão Dapper parametrizado e timeout)

### 2) Ticket canônico (copiado)
Implemente o seguinte “vertical slice”:
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache.
- Se houver base no código/MCP para integrações externas, incluir exemplo HTTP com timeout/resiliência.

### 3) Plano BMAD

#### Background
- **FATO:** API em camadas com `Api`, `Dominio`, `Interfaces`, `Repositorio` já estruturados.
- **FATO:** já existe envelope `OpenFinanceResponse<T>` e endpoints `GET /` + `POST /`.
- **FATO:** não existe endpoint `GET /{id}` nem `PUT /{id}`.
- **FATO:** não há integração externa HTTP implementada no repo.

#### Mission
Entregar atualização total (`PUT /api/v1/clientes/{id}`) e leitura por id com cache (`GET /api/v1/clientes/{id}`), com validação e status codes coerentes com o contrato atual.

#### Approach
1. Expandir contratos em `Interfaces` para obter por id e atualizar.
2. Implementar regras em `Dominio` (validação + `KeyNotFoundException` quando não existir).
3. Implementar no `Repositorio` com SQL parametrizado Dapper e timeout configurado.
4. Expor endpoints `GET /{id}` e `PUT /{id}` em `Api`, mantendo envelope existente.
5. Adicionar cache em leitura por id via `IMemoryCache` e TTL curto; atualizar cache no `PUT`.

#### Delivery/validation
- Build da API após patch.
- Sem suíte de testes no workspace; validar por build e contrato HTTP declarativo (`Produces`).

### 4) Implementação (patch aplicado)

#### Mudanças por camada
- **Interfaces**
  - `IClienteRepositorio`: novos métodos `ObterPorIdAsync` e `AtualizarAsync`.
  - `IClienteServico`: novos métodos `ObterClientePorIdAsync` e `AtualizarClienteAsync`.
- **Domínio**
  - `ClienteServico`: validação de `Guid.Empty`, `Nome`, `Email`; lança `KeyNotFoundException` para cliente inexistente.
- **Infraestrutura**
  - `ClienteRepositorioDapper`: `SELECT ... WHERE Id = @Id` e `UPDATE ... OUTPUT ... WHERE Id = @Id`, ambos parametrizados com timeout.
- **API**
  - `ClienteEndpoints`:
    - novo `GET /api/v1/clientes/{id:guid}` com cache (`IMemoryCache`) e TTL de 5 min.
    - novo `PUT /api/v1/clientes/{id:guid}` para atualização total.
    - mapeamento de erros explícito: `400`, `404`, `408`, `500`.
  - `ApiExtensions`: `services.AddMemoryCache()`.

### 5) Validação
- Executado: `dotnet build .\ClientesAPI.Api\ClientesAPI.Api.csproj`
- Resultado: comando executado com sucesso.
- Testes: **não há projeto de testes detectado** no workspace (lacuna objetiva).

### Exemplo de integração externa HTTP com timeout/resiliência (fora do patch)
- **FATO:** há base no MCP para `HttpClientFactory` + Polly.
- **FATO:** o repositório não possui integração externa implementada para clientes.
- **Decisão:** não introduzir integração fictícia neste patch.
- Exemplo de abordagem recomendada (não aplicada): cliente nomeado com timeout explícito + retry transiente + circuit breaker, encapsulado em gateway na camada de infraestrutura.

---

## Parte 2 — Relatório técnico do experimento

### 0. Métricas de execução (obrigatório)

#### Classificação explícita (rigor)
- **FATO (observável):** endpoints e contratos existentes não cobriam `GET /{id}` e `PUT /{id}`.
- **FATO (observável):** repositório usa Dapper com `CommandDefinition` e timeout já configurado.
- **FATO (observável):** não foi encontrado projeto de testes.
- **HIPÓTESE:** o padrão de erro ideal corporativo poderia migrar totalmente para middleware global; não foi aplicado para não quebrar padrão local já adotado nos endpoints.
- **RISCO DE INTERPRETAÇÃO:** a exigência “incluir exemplo HTTP resiliente” permite entrega fora do patch; interpretação adotada para não fabricar integração inexistente.

### 1. Evidência de uso de contexto

#### Decisões ancoradas em instruction local
- Uso obrigatório do MCP para decisões cross-cutting.
- Idioma da entrega em português.
- Execução de build após mudanças substanciais.

#### Decisões ancoradas em código do repositório
- Manutenção do envelope `OpenFinanceResponse<T>` em vez de trocar para outro contrato.
- Persistência via Dapper com `CommandDefinition` + timeout.
- Estilo de endpoints minimal API com `Produces` e tratamento por exceções previsíveis.

#### Decisões inferidas
- TTL de cache fixado em 5 min (não havia valor canônico no repo).
- Atualização de cache no `PUT` em vez de remoção pura (escolha de eficiência).

### 2. Qualidade técnica do plano
- **Estrutura BMAD:** forte; conectou restrição, missão, abordagem e validação.
- **Aderência do patch ao plano:** forte; cada camada recebeu apenas mudança necessária.
- **Clareza de camadas:** forte; contratos em `Interfaces`, regra em `Dominio`, SQL no `Repositorio`, cache/HTTP na `Api`.
- **Overengineering:** baixo; sem introdução de framework extra.
- **Ponto fraco:** ausência de testes automatizados reduz confiança de regressão.

### 3. Limitações estruturais da abordagem
- Duplicação potencial: regras de validação simples podem se repetir entre serviços em múltiplos repositórios.
- Drift provável: se catálogo de erros evoluir no MCP, cada repo pode desviar sem enforcement automático.
- Evolução centralizada: depende de disciplina operacional; MCP sozinho não força refatoração em massa.
- Acoplamento ao repo: contrato local (`OpenFinanceResponse`) prevalece e pode divergir de padrões corporativos futuros.

### 4. Escalabilidade em 100+ repositórios
- **Sustenta-se parcialmente** com governança forte e automação de conformidade.
- **Deixa de sustentar** quando MCP vira recomendação sem validação contínua (lint/CI/policies-as-code).
- **Esforço de manutenção:** alto sem tooling; moderado com templates, analyzers e checks automáticos.
- **Riscos operacionais previsíveis:** deriva semântica de status code, padrões de erro fragmentados, cache inconsistente entre times.

### 5. Experiência de uso
- Fluidez: boa para descoberta estrutural e execução de patch.
- Necessidade de reprompt: baixa neste caso.
- Dependência de descoberta manual: média (foi necessário varrer projetos e contratos).
- Previsibilidade: média-alta enquanto o repo já segue padrão em camadas.

### Avaliação (0-2)
- aderência ao contexto local: **2**
- qualidade técnica: **2**
- completude: **2**
- consistência: **2**
- escalabilidade da abordagem: **1**
- facilidade de manutenção: **1**

### Conclusão final
**instructions locais funcionam, mas não escalam bem**.

- Principal evidência: o patch foi consistente no repo atual, porém exige varredura manual e interpretação humana para alinhar MCP × implementação local; isso não escala linearmente para 100+ repositórios sem automação de conformidade.
- Principal limitação do experimento: ausência de suíte de testes e de um segundo repositório comparativo no mesmo run para medir drift real.

```json
EXPERIMENT_METRICS_JSON
{
  "inicio_iso": "2026-04-16T11:55:00.0000000-03:00",
  "fim_iso": "2026-04-16T12:14:00.0255579-03:00",
  "duracao_ms": 1140025,
  "latencia_por_etapa_ms": {
    "exploracao_leitura": 520000,
    "raciocinio_decisao": 240000,
    "escrita_plano": 140000,
    "escrita_relatorio": 240025
  },
  "qtd_tool_calls_total": 62,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "get_files_in_project": 5,
    "corporate_instructions_list_instructions_index": 1,
    "corporate_instructions_search_instructions": 7,
    "get_file": 30,
    "apply_patch": 7,
    "get_errors": 1,
    "file_search": 2,
    "run_command_in_terminal": 2,
    "multi_tool_use.parallel": 6
  },
  "sucessos": 62,
  "falhas": 0,
  "retries": 0,
  "qtd_arquivos_lidos": 18,
  "qtd_arquivos_citados": 11,
  "qtd_trechos_citados": 22,
  "bytes_aprox_lidos": 46000,
  "tokens_input_est": 19000,
  "tokens_output_est": 6500,
  "metodo_estimativa_tokens": "Estimativa por ~4 caracteres/token sobre conteúdo lido e resposta gerada; margem ampla por ausência de telemetria nativa.",
  "margem_erro_tokens_assumida": "±30%",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_plano": 4,
  "qtd_afirmacoes_FATO": 14,
  "qtd_afirmacoes_HIPOTESE": 3,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 4
}
```

```json
DECISIONS_JSON
{
  "decisoes": [
    {
      "decisao": "Manter separação por camadas e expandir contratos em Interfaces antes de API",
      "ancoragem": "MCP + codigo_repo",
      "evidencia": "microservice-architecture-layering; microservice-domain-interfaces-models-repository; ClientesAPI.Interfaces/IClienteServico.cs; IClienteRepositorio.cs",
      "risco": "baixo",
      "como_validar": "compilação sem dependência invertida e revisão de referências entre projetos"
    },
    {
      "decisao": "Implementar PUT como atualização total com retorno 200 e body",
      "ancoragem": "MCP + codigo_repo",
      "evidencia": "microservice-rest-http-semantics-and-status-codes; ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
      "risco": "baixo",
      "como_validar": "teste manual via HTTP: PUT válido retorna 200 + payload atualizado"
    },
    {
      "decisao": "Mapear validação para 400 e inexistência para 404",
      "ancoragem": "MCP + codigo_repo",
      "evidencia": "microservice-api-validation-and-error-contracts; microservice-api-error-catalog-baseline; tratamento em ClienteEndpoints.cs",
      "risco": "medio",
      "como_validar": "cenários negativos: id vazio, payload inválido, id inexistente"
    },
    {
      "decisao": "Adicionar cache de leitura no GET por id com IMemoryCache TTL 5 min",
      "ancoragem": "MCP + inferencia",
      "evidencia": "microservice-caching-imemorycache-policy; ApiExtensions.cs (AddMemoryCache); ClienteEndpoints.cs (cache key/TTL)",
      "risco": "medio",
      "como_validar": "duas leituras seguidas no mesmo id e inspeção de hit/miss por telemetria/log"
    },
    {
      "decisao": "Não implementar integração externa fictícia; incluir só exemplo conceitual fora do patch",
      "ancoragem": "codigo_repo + inferencia",
      "evidencia": "ausência de gateway HttpClient no repo; MCP microservice-integration-httpclientfactory-contracts",
      "risco": "alto",
      "como_validar": "confirmar requisito de escopo com time e existência de integração real"
    },
    {
      "decisao": "Persistir com SQL parametrizado e timeout explícito",
      "ancoragem": "MCP + codigo_repo",
      "evidencia": "microservice-data-access-and-sql-security; ClienteRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "revisão de query sem concatenação e build"
    }
  ]
}
```