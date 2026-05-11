## Análise consolidada — Comparação A vs B vs C

### Escopo e fontes

- **Slug**: `abc-outbox-mensageria-baseline-mcp-rag`
- **Data(s)**: 2026-05-11
- **Fontes analisadas**:
  - A: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__baseline.md`
  - B: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__mcp.md`
  - C: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__rag.md`
- **Observação sobre múltiplas tentativas** (se aplicável):
  - Em **B** há uma tentativa **bem-sucedida** (com build/test) e, no mesmo arquivo, um registro de **execução abortada** (“execução parcial abortada”). Para as notas, o **resultado principal** é a tentativa bem-sucedida; o abort entra como risco/ameaça à validade.

### Resumo executivo (máx. 10 linhas)

- Os três cenários reportam a implementação do vertical slice (outbox + publish/consume + read-model + idempotência + DLQ) com mensageria **simulada em memória** (Channel), coerente com a ausência de broker evidenciada nos relatórios.
- **B** se destaca por **validação objetiva mais forte** (build + testes passando) e por marcar “Cache/GET coerente”, além de registrar passos de “Como validar”.
- **A** e **C** ficam muito próximos: ambos reportam build/test, implementação do slice e limites semelhantes (sem execução end-to-end / sem DB preparado).
- Risco relevante: em **B** existe uma tentativa abortada por indisponibilidade de tools MCP na sessão; isso reduz higiene/estabilidade do desenho experimental mesmo com uma execução bem-sucedida registrada.

### Notas por critério (0–10)

Para cada critério abaixo, foram atribuídas notas para A/B/C, com justificativas curtas e citações textuais dos relatórios quando há evidência.

#### 1) Validade do experimento (higiene/isolamento)

- **Definição**: O quão bem o cenário controla contaminação e cumpre requisitos de validade declarados (sessão isolada, procedimentos, pré-condições).
- **Notas**: A=8, B=7, C=8
- **Justificativas e evidências**:
  - A:
    - Checklist de validade marcado e medidas de isolamento do contexto do assistente foram registradas.
    - Evidência: “`- [x] Thread/sessão separada (sem contaminação)`” e “`- [x] .github/instructions/ removida durante o experimento e restaurada ao final`”.
  - B:
    - Checklist principal indica uso de MCP e build/test, mas o mesmo arquivo contém uma tentativa abortada por indisponibilidade do MCP, o que introduz instabilidade na execução da condição B.
    - Evidência (execução válida): “`- [x] (Somente B) Houve uso de MCP (`corporate_instructions_*`) para contexto/guardrails`”.
    - Evidência (tentativa abortada no mesmo arquivo): “`execução parcial abortada`” e “`Fail: tools MCP não disponíveis nesta sessão`”.
  - C:
    - Validade declarada como sessão separada e permissão explícita de RAG geral com `fixtures/` intacta.
    - Evidência: “`- [x] (Somente C) fixtures/ permaneceu intacta e foi permitido RAG geral no codebase`”.

#### 2) Aderência aos critérios de aceite (checklist Pass/Fail)

- **Definição**: Grau de atendimento ao checklist de aceite reportado (Pass/Fail) incluindo justificativas de N/A.
- **Notas**: A=8, B=9, C=8
- **Justificativas e evidências**:
  - A:
    - A maioria dos itens principais está marcada como Pass (outbox, publish/consume, read-model, idempotência, DLQ), com alguns itens marcados como N/A por falta de evidência (cache/correlation).
    - Evidência: “`- [x] DLQ após N tentativas (N explícito = 3)`” e “`- [ ] Cache/GET coerente ... (N/A — sem evidência de cache no código)`”.
  - B:
    - Checklist reporta Pass em todos os itens do slice, incluindo cache/GET, além de build passando.
    - Evidência: “`- [x] Cache/GET coerente (ou TTL documentado)`” e “`- [x] Build passa (`dotnet build`)`”.
  - C:
    - Checklist reporta Pass nos itens do slice, com cache e correlation não verificados.
    - Evidência: “`- [ ] Cache/GET coerente (ou TTL documentado)`” e “`- [x] DLQ após N tentativas (N explícito)`”.

#### 3) Completude do vertical slice

- **Definição**: Cobertura do slice (outbox + publicação + consumo + read-model + idempotência + DLQ) conforme relatado.
- **Notas**: A=8, B=9, C=8
- **Justificativas e evidências**:
  - A:
    - Declara outbox e consumidor, read-model, idempotência e DLQ com \(N=3\), mas sem validação funcional completa do fluxo.
    - Evidência: “`- [x] Idempotência demonstrável (ProcessedEvent com PK/UNIQUE)`” e “`- [x] DLQ após N tentativas (N explícito = 3)`”.
  - B:
    - Descreve explicitamente outbox transacional, publisher/consumer em background, read-model e idempotência (ProcessedMessage), mais DLQ com \(N=3\).
    - Evidência: “`Read-model materializado em dbo.ClienteReadModel com idempotência por dbo.ProcessedMessage (MessageId PK)`” e “`DLQ implementada ... com N=3 explícito no código.`”
  - C:
    - Descreve o slice completo com nomes de tabelas para idempotência e DLQ, com \(N=3\).
    - Evidência: “`Foi implementada projeção de read-model ... com idempotência por dbo.ProcessedEvent (EventId PK).`” e “`Foi implementada DLQ ... com N=3 tentativas explícitas.`”

#### 4) Qualidade arquitetural

- **Definição**: Separação de responsabilidades, clareza e acoplamento conforme afirmado/indicado no relatório (sem inferir além do texto).
- **Notas**: A=6, B=7, C=6
- **Justificativas e evidências**:
  - A:
    - Rubrica do próprio relatório indica qualidade arquitetural moderada/baixa (1 em 0–2), sem detalhar claramente a separação de camadas.
    - Evidência: “`- Qualidade arquitetural: 1`”.
  - B:
    - Rubrica também marca 1, mas o texto evidencia componentes separados (publisher/consumer em `BackgroundService`) e explicita idempotência/DLQ com entidades/tabelas distintas; ainda assim, sem avaliação detalhada de acoplamento.
    - Evidência: “`mensageria simulada ... com Channel<T>, publisher e consumer em BackgroundService`” e “`- Qualidade arquitetural: 1`”.
  - C:
    - Rubrica indica 1, com descrição de componentes (publisher/consumer em background), mas sem explicitar critérios arquiteturais além disso.
    - Evidência: “`- Qualidade arquitetural: 1`” e “`publisher/consumer em BackgroundService`”.

#### 5) Validação objetiva

- **Definição**: Evidência de build/test, passos reproduzíveis e cobertura do “como validar” (sem depender de suposições).
- **Notas**: A=6, B=8, C=6
- **Justificativas e evidências**:
  - A:
    - Reporta execução de build/test, mas declara ausência de validação funcional end-to-end por falta de ambiente de BD preparado.
    - Evidência: “`- comandos_executados: ... dotnet build ... dotnet test`” e “`a validação funcional completa ... não foi executada`”.
  - B:
    - Reporta build e testes com comandos explícitos e aponta um roteiro objetivo de validação no DB.
    - Evidência: “`dotnet test ClientesAPI.Api.Tests/ClientesAPI.Api.Tests.csproj -v minimal`” e “`Como validar: executar sql/002_CreateOutboxAndReadModel.sql ... verificando tabelas ...`”.
  - C:
    - Reporta build/test com exit code 0, mas também declara ausência de validação runtime end-to-end dependente de DB.
    - Evidência: “`dotnet build e dotnet test retornaram exit code 0`” e “`não foi validado runtime neste experimento`”.

#### 6) Segurança e boas práticas de dados

- **Definição**: Evidências de práticas de segurança de dados (ex.: SQL parametrizado) presentes no texto do relatório.
- **Notas**: A=8, B=8, C=8
- **Justificativas e evidências**:
  - A:
    - Checklist marca SQL parametrizado e menciona Dapper com parâmetros.
    - Evidência: “`- [x] SQL parametrizado / segurança básica (Dapper com parâmetros)`”.
  - B:
    - Checklist marca SQL parametrizado e o relatório descreve Dapper/SQL Server.
    - Evidência: “`- [x] SQL parametrizado / segurança básica`” e “`O repositório alvo usa .NET 8 com Dapper/SQL Server`”.
  - C:
    - Checklist marca SQL parametrizado, sem detalhar além disso.
    - Evidência: “`- [x] SQL parametrizado / segurança básica`”.

#### 7) Operabilidade/Confiabilidade

- **Definição**: Evidências de retry com \(N\) explícito, DLQ e idempotência demonstrável conforme descrito.
- **Notas**: A=8, B=8, C=8
- **Justificativas e evidências**:
  - A:
    - Idempotência e DLQ com \(N=3\) estão explicitamente reportadas.
    - Evidência: “`Idempotência demonstrável (ProcessedEvent com PK/UNIQUE)`” e “`DLQ após N tentativas (N explícito = 3)`”.
  - B:
    - Idempotência via `ProcessedMessage` e DLQ com \(N=3\) explícito no código.
    - Evidência: “`dbo.ProcessedMessage (MessageId PK)`” e “`DLQ implementada ... com N=3 explícito no código.`”
  - C:
    - Idempotência via `ProcessedEvent` e DLQ via `DeadLetterEvent` com \(N=3\).
    - Evidência: “`idempotência por dbo.ProcessedEvent (EventId PK)`” e “`DLQ ... com N=3 tentativas explícitas.`”

#### 8) Coerência com o contexto do repo

- **Definição**: Se as escolhas (ex.: broker real vs simulado) são justificadas como coerentes com o que o relatório evidencia existir (ou não) no repo.
- **Notas**: A=8, B=8, C=8
- **Justificativas e evidências**:
  - A:
    - Relatório justifica mensageria simulada por ausência de broker no repo.
    - Evidência: “`mensageria foi simulada ... por ausência de broker no repo`”.
  - B:
    - Relatório afirma ausência de broker e registra simulação em memória como compatível com o requisito.
    - Evidência: “`O repositório alvo usa .NET 8 com Dapper/SQL Server (sem evidência de broker).`” e “`A simulação em memória ... atende o requisito “broker real ou simulação”`”.
  - C:
    - Relatório declara mensageria simulada em memória, e marca itens como não verificados quando não encontra evidência (cache/correlation).
    - Evidência: “`mensageria simulada em memória (Channel<T>)`” e “`Não foi encontrada evidência de cache em GET no repo`”.

#### 9) Clareza do relatório

- **Definição**: Estrutura, distinção FATO/HIPÓTESE/RISCO, rastreabilidade (comandos/artefatos) e legibilidade.
- **Notas**: A=7, B=8, C=7
- **Justificativas e evidências**:
  - A:
    - Estrutura completa (Identificação, checklist, Pass/Fail, Rubrica, Métricas, FATO/HIPÓTESE/RISCO) com boa rastreabilidade.
    - Evidência: “`## Observações (FATO / HIPÓTESE / RISCO)`” e “`## Métricas ... comandos_executados`”.
  - B:
    - Tem estrutura forte e evidências (comandos e “Como validar”), porém mistura no mesmo arquivo uma execução bem-sucedida com um relatório de execução abortada, o que aumenta o ruído.
    - Evidência (clareza/validação): “`Como validar: executar sql/002_CreateOutboxAndReadModel.sql`”.
    - Evidência (ruído por múltiplas tentativas): “`# Relatório — Outbox/Mensageria (A/B/C)`” e “`execução parcial abortada`”.
  - C:
    - Estrutura similar (checklist, Pass/Fail, rubrica, métricas, FATO/HIPÓTESE/RISCO) e indica limitações claramente.
    - Evidência: “`## Observações (FATO / HIPÓTESE / RISCO)`” e “`não foi validado runtime neste experimento`”.

### Cálculo e ranking

- **Médias**:
  - A: 7.44
  - B: 8.00
  - C: 7.44
- **Ranking**: 1º=B, 2º=A, 3º=C
- **Racional do ranking** (1 parágrafo):
  - **B** fica em 1º por apresentar a melhor combinação de aderência ao checklist (inclui “Cache/GET coerente”), descrição detalhada do slice (incluindo tabelas e \(N=3\)) e **validação objetiva mais forte** (build + testes + “Como validar”). **A** e **C** empatam em média; o desempate favorece **A** por registrar explicitamente procedimentos de isolamento do contexto do assistente (remoção/restauração de `.github/instructions` e `.github/copilot-instructions.md`), enquanto **C** é sólido, mas não mostra diferencial de validação/aceite frente a A e mantém limitações equivalentes (sem end-to-end).

### Riscos e ameaças à validade (consolidados)

- **Ausência de validação end-to-end** (todos): relatórios indicam que a execução funcional completa depende de DB preparado e não foi executada.
  - Evidência A: “`a validação funcional completa ... não foi executada`”.
  - Evidência B: “`O fluxo end-to-end ... não foi executado neste experimento.`”
  - Evidência C: “`não foi validado runtime neste experimento.`”
- **Múltiplas tentativas no cenário B no mesmo arquivo**: há um registro de execução abortada por indisponibilidade do MCP (“tools MCP não disponíveis”), o que pode confundir leitura e sinaliza fragilidade operacional para repetir a condição B.
  - Evidência: “`Fail: tools MCP não disponíveis nesta sessão`”.
- **Mensageria simulada** (todos): atende ao requisito conforme relatórios, mas limita a evidência sobre integração real (ack/nack etc.).
  - Evidência A: “`mensageria foi simulada ... por ausência de broker no repo`”.
  - Evidência B: “`A simulação em memória não reproduz exatamente semânticas de ack/nack do RabbitMQ`”.

### Recomendações (para o próximo ciclo de experimento)

- Executar um **roteiro end-to-end** (API + DB com scripts aplicados) e capturar evidências objetivas (ex.: queries nas tabelas outbox/read-model/idempotência/DLQ), para reduzir a ameaça de validade comum aos 3 cenários.
- Normalizar a **forma de reporte** para evitar “múltiplas tentativas” no mesmo arquivo sem separação clara (ex.: separar “B-abortado” em outro artefato), mantendo a rastreabilidade.
- Se “Cache/GET” for requisito recorrente, explicitar no relatório **onde** está a evidência no código (ou declarar N/A com justificativa), já que A/C ficaram como “não evidenciado”.

