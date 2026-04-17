# Experimento — Cenário 4 (Saga onboarding) — Condição **A: MCP**

## Regras de orquestração (condição A)

- **Idioma:** português. **Segurança:** sem segredos em texto claro; configurar integrações de forma segura.
- **MCP `corporate-instructions`:** usar para camadas, padrões de mensageria/outbox se existirem, idempotência, resiliência, dados SQL, observabilidade, testes.
- **Passos:** `list_instructions_index` → `search_instructions` (várias) → `get_instructions_batch` → cruzar com código → citar fontes.
- **Fluxo:** leitura antes de editar; build após mudanças.

## Tarefa (implementação no repositório)

**Título:** Implementar saga (orquestração manual) para onboarding: criar cliente, criar formulário associado, enviar notificação — com compensações e timeout.

**Descrição:**

Expor um fluxo (ex.: `POST /clientes/onboarding` ou rota equivalente acordada com o projeto) que execute em sequência:

1. **Criar cliente** (serviço/repositório de clientes já existente).
2. **Criar formulário inicial** associado ao cliente — via cliente HTTP simulado, interface in-process ou fila, conforme o código base permitir (declarar **FATO** vs **HIPÓTESE**).
3. **Enviar email de boas-vindas** — via publicador simulado ou fila.

Se **qualquer** etapa falhar após sucesso das anteriores, executar **compensações** na ordem inversa (ex.: apagar formulário criado, apagar cliente) de forma **idempotente**.

**Requisitos de desenho:**

- **Sem** framework de saga externo obrigatório (NServiceBus/MassTransit/Temporal): implementação **manual** clara no código.
- Tabela de estado **`OnboardingSagaState`** (ou nome alinhado) com: identificador da saga, id do cliente, passo atual, estado, timestamps.
- **Timeout global** da saga (ex.: 30 segundos): se exceder, abortar e compensar.
- **Retry** configurável em etapas (ex.: etapa 2 falha, retry após intervalo — ex.: 5s) — valores explícitos no código.
- **Idempotência** em todas as chamadas e compensações (chaves ou idempotency key por operação).
- Serviços externos (formulário, notificação) podem ser **mocks** ou interfaces já existentes; não inventar URLs reais sem configuração.

**Cenários esperados:**

- Happy path: cliente + formulário + notificação concluídos; estado final “completo”.
- Falha na etapa 2: compensar etapa 1 (ex.: remover cliente) — estado final consistente (sem cliente órfão sem formulário se assim foi definido).
- Falha na etapa 3: compensar etapas 2 e 1 na ordem inversa.
- Retry após falha transitória na etapa 2 → eventual sucesso.
- Timeout superior a 30s → abort + compensação.

**Observabilidade:** `CorrelationId` / `SagaId` propagado em logs ou eventos alinhados ao projeto.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Estado | Tabela ou store de estado de saga com campos essenciais |
| Happy path | Onboarding completo com todos os passos |
| Falha etapa 2 | Cliente não permanece inconsistente; compensação executada |
| Falha etapa 3 | Compensações em ordem reversa |
| Timeout | Cancelamento + compensação após limite |
| Retry | Comportamento de retry verificável |
| Idempotência | Reexecução não duplica efeitos colaterais |
| Correlação | `SagaId` / correlation alinhados em logs ou eventos |

## Entrega pedida

1. **BMAD** com referências MCP e distinção FATO/HIPÓTESE sobre mocks e integrações.
2. Implementação.
3. Como simular falhas e validar compensações e timeout.
