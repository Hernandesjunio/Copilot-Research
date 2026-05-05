# Parte 1 — Execução

## 1) Cenário canónico
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação em memória/fila local conforme evidência no código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model** (`ClienteReadModel` ou equivalente do projeto); garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite e evidência no repositório.

## 2) Plano BMAD
- **Background**
  - **FATO:** API em camadas com projetos `Api`, `Dominio`, `Repositorio`, `Interfaces`, `Modelo`.
  - **FATO:** Persistência em SQL Server com Dapper (`ClienteRepositorioDapper`).
  - **FATO:** Não há broker real, nem cache explícito, nem testes automatizados no repositório.
- **Mission**
  - Implementar outbox transacional em `POST`/`PUT`, publicação assíncrona, consumo para read-model, idempotência e DLQ sem quebrar CRUD.
- **Approach**
  - Outbox em SQL (`ClienteEventosOutbox`) na mesma transação de `INSERT`/`UPDATE`.
  - Publicador em `BackgroundService` lendo outbox e publicando em fila local persistida (`ClienteEventosFila`).
  - Consumidor em `BackgroundService` aplicando upsert em `ClienteReadModel`.
  - Idempotência com tabela `ClienteEventosProcessados`.
  - DLQ com `ClienteEventosDlq` após `N=3` tentativas.
- **Delivery/validation**
  - Build da solução (`run_build`) e conferência de artefatos alterados.
  - Mapeamento objetivo dos critérios de aceite para evidências de código/comando.

## 3) Implementação (patch)
### Principais alterações
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
  - **FATO:** `CriarAsync` e `AtualizarAsync` agora recebem `correlationId` e registram evento no outbox na mesma transação do cliente.
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`, `IClienteServico.cs`
  - **FATO:** Assinaturas de `POST`/`PUT` propagam `correlationId`.
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
  - **FATO:** repasse de `correlationId` para repositório.
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
  - **FATO:** captura `X-Correlation-Id` (ou `TraceIdentifier`) e injeta em create/update.
- `ClientesAPI.Repositorio/ClienteMensageriaRepositorioDapper.cs` (novo)
  - **FATO:** cria schema idempotente (Outbox/Fila/ReadModel/Processados/DLQ) e implementa operações de outbox, fila, idempotência, DLQ e upsert.
- `ClientesAPI.Dominio/Servicos/ClienteOutboxPublisherWorker.cs` (novo)
  - **FATO:** publica eventos pendentes do outbox para fila local, retry e DLQ com `MaxTentativas = 3`.
- `ClientesAPI.Dominio/Servicos/ClienteEventosConsumerWorker.cs` (novo)
  - **FATO:** consome fila, verifica idempotência, atualiza read-model e move para DLQ após falhas repetidas (`MaxTentativas = 3`).
- `ClientesAPI.Dominio/Servicos/ClienteMessageBusInMemory.cs` (novo)
  - **FATO:** simulação de mensageria via fila local persistida.
- `ClientesAPI.Api/Extensions/MensageriaSchemaInitializerHostedService.cs` (novo) + DI em `Program.cs`, `DomainExtensions.cs`, `RepositoryExtensions.cs`
  - **FATO:** schema é garantido no startup e workers são registrados.

## 4) Validação
### Comandos executados
- **FATO:** `run_build` → **Build successful**.
- **FATO:** `get_tests` (Outcome=NotRun) → nenhum teste encontrado.

### Critérios de aceite x verificação
| Critério | Verificação executada / evidência |
|---|---|
| Build | **OK**: `dotnet build` (via `run_build`) sem erros |
| Outbox | **OK**: tabela e campos em `ClienteMensageriaRepositorioDapper.GarantirSchemaAsync` |
| POST gera evento | **OK (código)**: `CriarAsync` insere em `Cliente` e `ClienteEventosOutbox` na mesma transação |
| PUT gera evento | **OK (código)**: `AtualizarAsync` atualiza cliente e insere evento outbox na mesma transação |
| Read-model | **OK (código)**: consumidor chama `UpsertClienteReadModelAsync` |
| Idempotência | **OK (código)**: `RegistrarProcessamentoSeNovoAsync` evita reprocessamento |
| DLQ | **OK (código)**: `IncrementarTentativaOutboxAsync` e `IncrementarTentativaFilaAsync` movem para DLQ com `N=3` |
| Cache | **HIPÓTESE:** não existe cache no repo; sem invalidar/TTL |
| Correlação | **OK (código)**: `X-Correlation-Id`/`TraceIdentifier` propagado até outbox |
| Segurança | **OK**: SQL parametrizado com `CommandDefinition` e objetos de parâmetros (sem concatenação insegura) |

### Limites de validação
- **RISCO DE INTERPRETAÇÃO:** Sem teste de integração automatizado, os fluxos fim-a-fim (publicação/consumo/retry real) ficaram validados por inspeção de código + build.
- Comando sugerido para validação manual fim-a-fim: executar API, chamar `POST/PUT`, e inspecionar tabelas `ClienteEventosOutbox`, `ClienteEventosFila`, `ClienteReadModel`, `ClienteEventosDlq`.

---

# Parte 2 — Relatório do experimento

## 0. Métricas de execução
- tempo total (wall-clock)
  - `inicio_iso`: `2026-05-02T07:52:41.9999885-03:00`
  - `fim_iso`: `2026-05-02T08:04:03.0194706-03:00`
  - `duracao_ms`: `681019`
- latência por etapa (estimada por marcos de execução)
  - `exploracao_leitura_ms`: `180000`
  - `raciocinio_decisao_ms`: `60000`
  - `escrita_patch_ms`: `300000`
  - `validacao_ms`: `50000`
  - `escrita_relatorio_ms`: `91019`
- uso de tools
  - `qtd_tool_calls_total`: `42`
  - `qtd_por_tool`: ver JSON
  - `sucessos`: `41`
  - `falhas`: `1` (patch inválido ao criar interface)
  - `retries`: `1`
- I/O de contexto
  - `qtd_arquivos_lidos`: `20`
  - `qtd_arquivos_citados`: `18`
  - `qtd_trechos_citados`: `20`
  - `bytes_aprox_lidos`: `N/A` (plataforma não retorna bytes por leitura)
- tokens
  - `tokens_input`: `N/A`
  - `tokens_output`: `N/A`
  - `tokens_input_est`: `N/A`
  - `tokens_output_est`: `N/A`
  - método/margem: indisponível na plataforma
- custo
  - `custo_total`: `N/A`
  - `moeda`: `N/A`
- tamanho do resultado
  - `caracteres_resposta`: `N/A` (depende do cliente de chat)
  - `qtd_itens_patch`: `18` arquivos alterados/criados
- contagens de rigor
  - `qtd_afirmacoes_FATO`: `22`
  - `qtd_afirmacoes_HIPOTESE`: `3`
  - `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`: `4`

## 1. Uso de contexto
- **FATO:** decisões ancoradas no código: estrutura em camadas, Dapper/SQL Server, ausência de cache, ausência de broker, ausência de testes.
- **HIPÓTESE:** uso de fila local persistida como substituto de broker real foi inferência arquitetural por ausência de RabbitMQ no repo.
- **RISCO DE INTERPRETAÇÃO:** sem migrations/scripts formais, o schema foi criado em runtime; isso pode divergir do processo operacional desejado.

## 2. Qualidade técnica do plano
- Estrutura: adequada para um vertical slice (persistência + integração assíncrona + consumo).
- Camadas: preservadas (API captura correlação, domínio orquestra, repositório persiste/processa).
- Coerência arquitetural: boa com stack observada.
- Complexidade: moderada/alta; implementação abrangente sem depender de infraestrutura externa.
- Sinais de genericidade: baixos; nomes e fluxo centrados em Cliente.

## 3. Limitações estruturais da abordagem
- **RISCO DE INTERPRETAÇÃO:** depender apenas de código visível impede saber requisitos não-funcionais (observabilidade, volume, retenção DLQ, política de replay).
- Ausência de diretrizes explícitas aumenta variação de desenho entre execuções.
- Probabilidade de inconsistência entre execuções: média.
- Risco em desenvolvimento real: médio/alto sem alinhamento de operações e banco.

## 4. Sustentabilidade para implementação real
- Sustenta prototipagem e baseline técnico.
- Exige reprompt/iteração para convergir com padrões de operação reais (migrations, monitoramento, replay, tuning de lote).
- Decisões frágeis sem contexto adicional: limites de retry, estratégia de backoff, semântica exata de eventos e contratos externos.

## 5. Experiência de uso
- Fluidez: boa para evolução incremental.
- Previsibilidade: parcial; faltas de contexto exigem inferência.
- Descoberta manual: alta (mapear código para achar pontos de extensão).
- Dependência de interpretação do modelo: alta em decisões arquiteturais sem evidência explícita.

## Avaliação (0-2)
- aderência ao código observável: **2**
- qualidade técnica: **1**
- completude: **1**
- consistência: **1**
- previsibilidade: **1**
- sustentabilidade para implementação real: **1**

## Conclusão final
**baseline funciona parcialmente, mas exige muita inferência**.

- Principal evidência: ausência de contexto estruturado forçou decisões de infraestrutura (fila local, schema em runtime) por inferência, mesmo com build e fluxo arquitetural implementados.
- Principal limitação do experimento: não houve testes de integração automatizados no repositório para comprovar comportamento fim-a-fim em execução real.

```json
EXPERIMENT_METRICS_JSON
{
  "inicio_iso": "2026-05-02T07:52:41.9999885-03:00",
  "fim_iso": "2026-05-02T08:04:03.0194706-03:00",
  "duracao_ms": 681019,
  "latencia_por_etapa_ms": {
    "exploracao_leitura": 180000,
    "raciocinio_decisao": 60000,
    "escrita_patch": 300000,
    "validacao": 50000,
    "escrita_relatorio": 91019
  },
  "qtd_tool_calls_total": 42,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "get_files_in_project": 5,
    "get_file": 20,
    "code_search": 1,
    "file_search": 2,
    "run_command_in_terminal": 3,
    "plan": 1,
    "update_plan_progress": 4,
    "apply_patch": 11,
    "create_file": 8,
    "run_build": 2,
    "record_observation": 1,
    "get_tests": 1
  },
  "sucessos": 41,
  "falhas": 1,
  "retries": 1,
  "qtd_arquivos_lidos": 20,
  "qtd_arquivos_citados": 18,
  "qtd_trechos_citados": 20,
  "bytes_aprox_lidos": "N/A",
  "tokens_input": "N/A",
  "tokens_output": "N/A",
  "tokens_input_est": "N/A",
  "tokens_output_est": "N/A",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_patch": 18,
  "qtd_afirmacoes_FATO": 22,
  "qtd_afirmacoes_HIPOTESE": 3,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 4
}
```

```json
DECISIONS_JSON
{
  "decisoes": [
    {
      "decisao": "Usar fila local persistida em SQL em vez de RabbitMQ",
      "ancoragem": "inferencia",
      "evidencia": "N/A",
      "risco": "medio",
      "como_validar": "Substituir IClienteMessageBus por adapter RabbitMQ e validar mesma semântica de retries/DLQ"
    },
    {
      "decisao": "Registrar evento outbox na mesma transação de POST/PUT",
      "ancoragem": "codigo_repo",
      "evidencia": "ClientesAPI.Repositorio/ClienteRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "Executar POST/PUT e verificar presença simultânea em Cliente + ClienteEventosOutbox"
    },
    {
      "decisao": "Implementar idempotência com tabela ClienteEventosProcessados",
      "ancoragem": "inferencia",
      "evidencia": "ClientesAPI.Repositorio/ClienteMensageriaRepositorioDapper.cs",
      "risco": "medio",
      "como_validar": "Reenfileirar mesmo EventoId e confirmar ausência de dupla atualização efetiva no read-model"
    },
    {
      "decisao": "DLQ após 3 tentativas",
      "ancoragem": "inferencia",
      "evidencia": "ClienteOutboxPublisherWorker.MaxTentativas=3 e ClienteEventosConsumerWorker.MaxTentativas=3",
      "risco": "baixo",
      "como_validar": "Forçar falha de consumo/publicação 3x e inspecionar ClienteEventosDlq"
    },
    {
      "decisao": "Sem ação de cache",
      "ancoragem": "codigo_repo",
      "evidencia": "Sem referências a cache nas buscas de código",
      "risco": "baixo",
      "como_validar": "Se cache for introduzido, adicionar invalidação pós-publicação ou TTL explícito"
    }
  ]
}
```
