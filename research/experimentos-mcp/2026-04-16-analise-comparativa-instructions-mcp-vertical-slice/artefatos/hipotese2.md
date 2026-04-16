# Parte 1 — Execução

## 1) Seleção de guardrails e evidências (antes de codar)

### Instructions locais aplicáveis

- `assistant-workflow-bmad-planning-and-controlled-inference` (policy)
  - Decisão: obrigatoriedade de plano BMAD e rotulagem explícita de inferência.
- `microservice-architecture-layering` (reference)
  - Decisão: manter separação `Api` -> `Dominio` -> `Interfaces` -> `Repositorio`.
- `microservice-api-openfinance-patterns` (policy)
  - Decisão: manter envelope `OpenFinanceResponse<T>` e tratamento global de erros.
- `microservice-rest-http-semantics-and-status-codes` (policy)
  - Decisão: `PUT` para substituição total; `GET/PUT` por id com `404` para recurso inexistente.
- `microservice-api-validation-and-error-contracts` (policy)
  - Decisão: validação de entrada em `400`; inexistência em `404`; manter coerência de contrato de erro.
- `microservice-data-access-and-sql-security` (policy)
  - Decisão: SQL parametrizada com `CommandDefinition`, `CancellationToken` e timeout explícito.
- `microservice-caching-imemorycache-policy` (policy)
  - Decisão: avaliar cache em `GET /clientes/{id}` apenas se houver base concreta no código.
- `microservice-testing-strategy-unit-integration-contract` (policy)
  - Decisão: validação objetiva via build/checagem de compilação na ausência de suíte de testes no workspace.

### Arquivos/módulos do workspace que ancoraram decisões

- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`
- `ClientesAPI.Api/Responses/OpenFinanceResponse.cs`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
- `ClientesAPI.Repositorio/Conexao/DbConnectionFactory.cs`

---

## 2) Ticket canônico

Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código/instructions; caso contrário, declarar lacuna e não inventar).
- Se houver base no código/instructions para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver base, marcar como fora de escopo.

### Classificação de evidência

- **FATO**: o código existente usa rota base versionada `/api/v1/clientes`.
- **HIPÓTESE**: o ticket em formato `/clientes/{id}` é canônico para comparação e não necessariamente substitui o versionamento já adotado.
- **RISCO DE INTERPRETAÇÃO**: divergência entre rota canônica do experimento e convenção já existente no repositório.

---

## 3) Plano BMAD

### Background
- API já expõe `GET /api/v1/clientes` e `POST /api/v1/clientes`.
- Arquitetura em camadas está explícita no repositório.
- Contrato de resposta usa envelope `OpenFinanceResponse<T>`.
- Não havia operação por id nem atualização completa no serviço/repositório.

### Mission
- Entregar `GET` por id e `PUT` por id com persistência, validação e mapeamento de erros coerente com contrato atual.

### Approach
1. Estender contratos `IClienteServico` e `IClienteRepositorio`.
2. Implementar regras de validação e `not found` no domínio.
3. Implementar consultas SQL parametrizadas (`SELECT` por id, `UPDATE ... OUTPUT`) no repositório.
4. Mapear endpoints Minimal API com status codes (`200`, `400`, `404`, `408`, `500`).
5. Avaliar cache em `GET`:
   - **FATO**: não há uso de `IMemoryCache` no código existente.
   - **Decisão**: não implementar cache para evitar invenção de padrão.

### Delivery/validation
- Compilação do projeto `Api` para validar integração entre camadas.
- Verificação de erros nos arquivos alterados.

---

## 4) Implementação (patch aplicado)

Arquivos alterados:
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
  - Adicionados: `ObterPorIdAsync` e `AtualizarAsync`.
- `ClientesAPI.Interfaces/IClienteServico.cs`
  - Adicionados: `ObterClientePorIdAsync` e `AtualizarClienteAsync`.
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
  - Implementadas validações de `id`, `nome`, `email` e erro `KeyNotFoundException` para inexistência.
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
  - Implementado `SELECT` por id com `QuerySingleOrDefaultAsync`.
  - Implementado `UPDATE` completo com `OUTPUT INSERTED...` e retorno do registro atualizado.
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
  - Adicionados `GET /{id:guid}` e `PUT /{id:guid}` no grupo `/api/v1/clientes`.
  - Mapeamento de `400`, `404`, `408` e documentação de `500`.

### Classificação de escopo adicional
- **FATO**: não há integração HTTP externa neste vertical slice.
- **Conclusão**: exemplo de chamada externa com resiliência ficou fora de escopo por ausência de evidência de necessidade no fluxo implementado.

---

## 5) Validação

### Execução objetiva
- Comando executado: `dotnet build ClientesAPI.Api/ClientesAPI.Api.csproj`
- Resultado: execução concluída com sucesso (`0` erros, `2` warnings de pacote `Swashbuckle.AspNetCore` `NU1603` já pré-existente no projeto).
- Checagem complementar: consulta de erros nos 5 arquivos alterados sem diagnósticos.

### Lacunas de validação
- **FATO**: não foi identificado projeto de testes automatizados no workspace.
- **RISCO DE INTERPRETAÇÃO**: comportamento funcional em runtime (DB real) não foi exercitado por teste de integração.
- **Como validar**: executar API com base SQL disponível e testar cenários:
  1. `PUT` com `id` existente -> `200`.
  2. `PUT` com `id` inexistente -> `404`.
  3. `PUT` inválido (`nome/email` vazios) -> `400`.
  4. `GET` por `id` existente -> `200`.
  5. `GET` por `id` inexistente -> `404`.


# Parte 2 — Relatório do experimento

## 0. Métricas de execução

- tempo total (wall-clock):
  - `inicio_iso`: `2026-04-16T00:00:00.0000000Z` (**HIPÓTESE; estimado**)
  - `fim_iso`: `2026-04-16T00:00:00.0000000Z` (**HIPÓTESE; estimado**)
  - `duracao_ms`: `N/A` (plataforma não expõe timestamps por chamada nesta sessão)
- latência por etapa (ms):
  - exploração/leitura: `N/A`
  - raciocínio/decisão: `N/A`
  - escrita do patch: `N/A`
  - validação: `N/A`
  - escrita do relatório: `N/A`
- uso de tools:
  - `qtd_tool_calls_total`: `41` (contagem por chamadas subjacentes)
  - `qtd_por_tool`:
    - `get_projects_in_solution`: 1
    - `file_search`: 3
    - `get_files_in_project`: 5
    - `get_file`: 24
    - `code_search`: 1
    - `apply_patch`: 5
    - `run_command_in_terminal`: 2
    - `get_errors`: 1
  - `sucessos`: `41`
  - `falhas`: `0`
  - `retries`: `0`
- I/O de contexto:
  - `qtd_arquivos_lidos`: `24`
  - `qtd_arquivos_citados`: `15`
  - `qtd_trechos_citados`: `N/A` (sem telemetria automática de chunks)
  - `bytes_aprox_lidos`: `N/A`
- tokens:
  - `tokens_input`: `N/A`
  - `tokens_output`: `N/A`
  - `tokens_input_est`: `N/A`
  - `tokens_output_est`: `N/A`
- custo:
  - `custo_total`: `N/A`
  - `moeda`: `N/A`
- tamanho do resultado:
  - `caracteres_resposta`: `N/A`
  - `qtd_itens_patch`: `5`
- contagens para rigor experimental:
  - `qtd_afirmacoes_FATO`: `17`
  - `qtd_afirmacoes_HIPOTESE`: `4`
  - `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`: `5`

## 1. Uso das instructions locais

- **FATO**: houve uso explícito de policies para HTTP (`PUT`/`404`), validação (`400`) e SQL segura (parametrização + timeout).
- **FATO**: a instruction de arquitetura ajudou a manter alteração em múltiplas camadas sem colapsar regra de negócio no endpoint.
- **FATO**: a instruction de cache foi consultada; como não havia base de cache no código, a decisão foi não introduzir `IMemoryCache`.
- **Crítica**: o repositório já continha `try/catch` por endpoint, enquanto a policy recomenda centralização no middleware. A implementação manteve o padrão vigente para minimizar ruptura, mas isso preserva dívida técnica.
- **Dependência de inferência remanescente**: interpretação de rota canônica (`/clientes/{id}`) versus padrão existente (`/api/v1/clientes/{id}`).

## 2. Qualidade técnica do plano

- Estrutura BMAD: adequada e rastreável.
- Clareza de camadas: forte (interfaces, domínio, repositório e API alterados de forma coerente).
- Coerência arquitetural: boa para o contexto atual.
- Aderência ao contexto recuperado: alta, sem introdução de bibliotecas novas.
- Sinais de genericidade/overengineering: baixos.

## 3. Centralização de conhecimento

- **FATO**: policies locais permitiram padronizar decisões críticas sem consulta externa.
- **Valor real**: reduzir arbitrariedade em status codes e separação de camadas.
- **Limitação**: quando há conflito entre policy e legado (ex.: `try/catch` em endpoint), a governance depende de enforcement adicional (lint/review).

## 4. Escalabilidade em múltiplos repositórios

- Em ~100+ repositórios, a abordagem é viável para baseline, desde que haja:
  - versionamento de instructions;
  - processo de revisão e depreciação;
  - automações de conformidade.
- Riscos operacionais:
  - drift entre repositórios e corpus central;
  - exceções locais não documentadas;
  - custo de manutenção sem ownership claro.
- Dependências de tooling:
  - indexação estável das instructions;
  - telemetria de aderência;
  - integração com CI para validação automática.

## 5. Experiência de uso

- Fluidez: boa na recuperação de contexto e aplicação de patch.
- Previsibilidade: média-alta quando as instructions são específicas.
- Interrupções: baixas no fluxo técnico.
- Dependência de prompt: ainda alta para exigir relatório experimental detalhado.
- Impacto do uso de tools: positivo para rastreabilidade; negativo para métricas finas (latência/tokens/custo indisponíveis).

## Avaliação (0–2)

- aderência ao contexto recuperado: **2**
- qualidade técnica: **2**
- completude: **1**
- consistência: **2**
- capacidade de centralização: **1**
- escalabilidade: **1**
- governança: **1**

## Conclusão final

**MCP ajuda, mas precisa de complementos**.

- Principal evidência: as instructions locais direcionaram decisões técnicas corretas (camadas, HTTP e validação) e evitaram invenção de cache sem base.
- Principal limitação do experimento: ausência de métricas automáticas completas (tempo/tokens/custo) e ausência de testes de integração para comprovar comportamento em runtime.


`EXPERIMENT_METRICS_JSON`

```json
{
  "tempo_total": {
    "inicio_iso": "2026-04-16T00:00:00.0000000Z",
    "fim_iso": "2026-04-16T00:00:00.0000000Z",
    "duracao_ms": "N/A"
  },
  "latencia_por_etapa": {
    "exploracao_leitura": "N/A",
    "raciocinio_decisao": "N/A",
    "escrita_patch": "N/A",
    "validacao": "N/A",
    "escrita_relatorio": "N/A"
  },
  "qtd_tool_calls_total": 41,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "file_search": 3,
    "get_files_in_project": 5,
    "get_file": 24,
    "code_search": 1,
    "apply_patch": 5,
    "run_command_in_terminal": 2,
    "get_errors": 1
  },
  "sucessos": 41,
  "falhas": 0,
  "retries": 0,
  "qtd_arquivos_lidos": 24,
  "qtd_arquivos_citados": 15,
  "qtd_trechos_citados": "N/A",
  "bytes_aprox_lidos": "N/A",
  "tokens_input": "N/A",
  "tokens_output": "N/A",
  "tokens_input_est": "N/A",
  "tokens_output_est": "N/A",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_patch": 5,
  "qtd_afirmacoes_FATO": 17,
  "qtd_afirmacoes_HIPOTESE": 4,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 5
}
```

`DECISIONS_JSON`

```json
{
  "decisoes": [
    {
      "decisao": "Implementar atualização total via PUT com persistência no repositório",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-rest-http-semantics-and-status-codes (PUT = substituição total)",
      "risco": "baixo",
      "como_validar": "Teste de contrato: PUT com payload completo altera recurso e retorna 200"
    },
    {
      "decisao": "Retornar 404 para id inexistente em GET/PUT",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-rest-http-semantics-and-status-codes (recurso inexistente por id -> 404)",
      "risco": "baixo",
      "como_validar": "Executar GET/PUT com Guid não existente e verificar status 404"
    },
    {
      "decisao": "Mapear validação de id/nome/email para 400",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-api-validation-and-error-contracts (validação de entrada -> 400)",
      "risco": "baixo",
      "como_validar": "Enviar payload inválido e verificar 400 com envelope de erro"
    },
    {
      "decisao": "Manter envelope OpenFinanceResponse no retorno",
      "ancoragem": "codigo_repo",
      "evidencia": "ClientesAPI.Api/Responses/OpenFinanceResponse.cs e endpoints existentes",
      "risco": "baixo",
      "como_validar": "Comparar formato JSON das novas rotas com POST/GET já existentes"
    },
    {
      "decisao": "Não implementar cache em GET por ausência de base concreta no código",
      "ancoragem": "inferencia",
      "evidencia": "code_search sem ocorrências de IMemoryCache + policy microservice-caching-imemorycache-policy",
      "risco": "medio",
      "como_validar": "Alinhar com time se cache deve ser introduzido agora com requisitos de TTL/invalidação"
    },
    {
      "decisao": "Manter rota sob /api/v1/clientes/{id} em vez de alterar base para /clientes/{id}",
      "ancoragem": "codigo_repo",
      "evidencia": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs usa MapGroup('/api/v1/clientes')",
      "risco": "medio",
      "como_validar": "Confirmar no contrato OpenAPI esperado do experimento se rota canônica exige remoção de versão"
    }
  ]
}
```
