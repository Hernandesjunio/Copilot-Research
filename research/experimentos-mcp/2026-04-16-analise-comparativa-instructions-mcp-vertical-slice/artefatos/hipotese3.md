# Parte 1 — Execução

## 1) Ticket canônico
Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código; caso contrário, declarar lacuna e não inventar).
- Se houver evidência no código para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver evidência, marcar como fora de escopo.

## 2) Plano BMAD
- **Background**
  - **FATO:** o repositório expõe apenas `ObterTodosAsync` e `CriarAsync` (`ClientesAPI.Interfaces/IClienteRepositorio.cs`).
  - **FATO:** a API possui `GET /api/v1/clientes/` e `POST /api/v1/clientes/` (`ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`).
  - **FATO:** persistência via Dapper/SQL Server (`ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`).
  - **FATO:** não há evidência de cache (`IMemoryCache`, `IDistributedCache`) no workspace.
  - **FATO:** não há evidência de integração HTTP externa no fluxo atual.
- **Mission**
  - Implementar `GET /api/v1/clientes/{id}` e `PUT /api/v1/clientes/{id}` com validação e contrato de erro consistente com o padrão atual (`OpenFinanceResponse<T>`).
- **Approach**
  - Expandir contratos de serviço/repositório.
  - Implementar leitura por `id` e atualização total no repositório Dapper.
  - Aplicar validação de `Nome`/`Email` no serviço.
  - Mapear `400/404/408/500` no endpoint de atualização e `404/408/500` no endpoint de leitura por `id`.
  - Não implementar cache por ausência de base concreta no código.
- **Delivery/validation**
  - Build da API para validar compilação e integração entre camadas.
  - Registro explícito das lacunas (cache e integrações externas).

## 3) Implementação (patch aplicado)
Arquivos alterados:
1. `ClientesAPI.Interfaces/IClienteRepositorio.cs`
   - Adicionados: `ObterPorIdAsync(Guid, CancellationToken)` e `AtualizarAsync(Guid, ClienteRequisicao, CancellationToken)`.
2. `ClientesAPI.Interfaces/IClienteServico.cs`
   - Adicionados: `ObterClientePorIdAsync(Guid, CancellationToken)` e `AtualizarClienteAsync(Guid, ClienteRequisicao, CancellationToken)`.
3. `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
   - Implementada leitura por `id`.
   - Implementada atualização total com validação (`Nome` e `Email`) e `KeyNotFoundException` quando não existe registro.
4. `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
   - Implementado `SELECT ... WHERE Id = @Id`.
   - Implementado `UPDATE ... OUTPUT INSERTED... WHERE Id = @Id`.
5. `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
   - Adicionados endpoints:
     - `GET /api/v1/clientes/{id:guid}`
     - `PUT /api/v1/clientes/{id:guid}`
   - Mapeamento de erros:
     - `400` para validação (`ArgumentException`)
     - `404` para não encontrado (`KeyNotFoundException`/resultado nulo)
     - `408` para timeout/cancelamento (`OperationCanceledException`)

## 4) Validação
- Comando executado:
  - `dotnet build ClientesAPI.Api/ClientesAPI.Api.csproj -v minimal`
- Critério de sucesso:
  - Build concluído sem erros de compilação.
- Resultado:
  - **FATO:** build concluído com `0 Error(s)`.
  - **FATO:** warnings de pacote preexistente (`NU1603` para `Swashbuckle.AspNetCore`), sem bloqueio da entrega.

---

# Parte 2 — Relatório do experimento

## 0. Métricas de execução
- Medição temporal detalhada de tool interno não é exposta; valores por etapa abaixo são estimativas observacionais.
- Tokens e custo não são fornecidos pela plataforma neste contexto; estimativas por caracteres/4.

### EXPERIMENT_METRICS_JSON
```json
{
  "inicio_iso": "2026-04-16T10:03:00.000-03:00",
  "fim_iso": "2026-04-16T10:17:16.913-03:00",
  "duracao_ms": 856913,
  "latencia_por_etapa_ms": {
    "exploracao_leitura": 310000,
    "raciocinio_decisao": 120000,
    "escrita_patch": 190000,
    "validacao": 150000,
    "escrita_relatorio": 86913
  },
  "qtd_tool_calls_total": 18,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "multi_tool_use.parallel": 3,
    "get_file": 1,
    "file_search": 2,
    "code_search": 1,
    "apply_patch": 6,
    "run_command_in_terminal": 4
  },
  "sucessos": 18,
  "falhas": 0,
  "retries": 0,
  "qtd_arquivos_lidos": 19,
  "qtd_arquivos_citados": 12,
  "qtd_trechos_citados": 12,
  "bytes_aprox_lidos": 31000,
  "tokens_input_est": 7200,
  "tokens_output_est": 2600,
  "metodo_estimativa_tokens": "aproximacao caracteres/4 do prompt + snippets lidos + resposta",
  "margem_erro_assumida": "±25%",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_patch": 5,
  "qtd_afirmacoes_FATO": 18,
  "qtd_afirmacoes_HIPOTESE": 3,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 6
}
```

### DECISIONS_JSON
```json
{
  "decisoes": [
    {
      "decisao": "Implementar PUT /api/v1/clientes/{id} com atualização total no repositório e validação no serviço",
      "ancoragem": "codigo_repo",
      "evidencia": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs + ClientesAPI.Dominio/Servicos/ClienteServico.cs + ClientesAPI.Repositorio/ClienteRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "Executar PUT com id existente e verificar retorno 200 com dados atualizados"
    },
    {
      "decisao": "Mapear não encontrado para 404 usando KeyNotFoundException",
      "ancoragem": "inferencia",
      "evidencia": "N/A",
      "risco": "medio",
      "como_validar": "Conferir padrão esperado da equipe para exceções de domínio e comparar com guideline interno (se existir)"
    },
    {
      "decisao": "Não implementar cache no GET por ausência de base técnica no código",
      "ancoragem": "codigo_repo",
      "evidencia": "Busca sem ocorrência para IMemoryCache/IDistributedCache",
      "risco": "baixo",
      "como_validar": "Se houver requisito de cache fora do código, adicionar instrução formal e testes de comportamento"
    },
    {
      "decisao": "Marcar integração HTTP externa como fora de escopo",
      "ancoragem": "codigo_repo",
      "evidencia": "Sem evidência de HttpClient/integração externa no workspace",
      "risco": "baixo",
      "como_validar": "Revisar backlog/requisitos funcionais para confirmar ausência de dependências externas"
    }
  ]
}
```

## 1. Uso de contexto
- **FATO:** decisões de camada (API→serviço→repositório) foram ancoradas em código existente.
- **FATO:** contrato `OpenFinanceResponse<T>` foi reutilizado sem criar novo envelope.
- **HIPÓTESE:** `KeyNotFoundException` representa adequadamente “não encontrado” no padrão desejado da equipe.
- **RISCO DE INTERPRETAÇÃO:** sem guideline explícita de catálogo de erros, o mapeamento de exceções pode divergir de outras implementações.

## 2. Qualidade técnica do plano
- Estrutura BMAD: objetiva e aderente ao escopo.
- Separação de camadas: preservada.
- Coerência arquitetural: alta com o padrão observado.
- Complexidade: adequada, sem overengineering.
- **RISCO DE INTERPRETAÇÃO:** sem testes automatizados de contrato HTTP, a consistência de payload de erro fica parcialmente validada.

## 3. Limitações estruturais da abordagem
- Dependência exclusiva do código visível limita decisões semânticas (ex.: política de erros de negócio).
- Ausência de diretriz explícita aumenta variabilidade entre execuções.
- Probabilidade de inconsistência: moderada, principalmente em escolhas de exceção e semântica de status code.
- Risco em desenvolvimento real: médio, por falta de contexto de padrões transversais.

## 4. Sustentabilidade para implementação real
- Sustenta tarefas CRUD simples.
- Exige reprompt frequente para padronização fina (erros, nomenclatura, observabilidade, segurança).
- Decisões frágeis sem contexto adicional: resiliência, cache, integração externa, taxonomia de falhas.

## 5. Experiência de uso
- Fluidez: boa para implementação incremental.
- Previsibilidade: parcial, sensível a inferências.
- Descoberta manual: alta (necessário varrer contratos e endpoints).
- Dependência do modelo: média/alta para preencher lacunas não explicitadas.

## Avaliação (0 a 2)
- aderência ao código observável: **2**
- qualidade técnica: **2**
- completude: **1**
- consistência: **1**
- previsibilidade: **1**
- sustentabilidade para implementação real: **1**

## Conclusão final
**baseline funciona parcialmente, mas exige muita inferência**.

- Principal evidência: ausência de contexto estruturado obrigou decisões não ancoradas em regra explícita para mapeamento semântico de erro (`KeyNotFoundException` → `404`).
- Principal limitação do experimento: validação restrita a build (sem suíte de testes automatizada de contrato/comportamento).
