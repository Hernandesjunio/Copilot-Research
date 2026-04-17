# Experimento — Cenário 4 (Saga onboarding) — Condição **B: Instructions locais**

## Regras de orquestração (condição B)

- **Idioma:** português. **Segurança:** não expor credenciais.
- **Fonte:** `.github/instructions/`. Declarar lacunas.
- **Sem MCP.** **BMAD** + citação de ficheiros locais.

## Tarefa (implementação no repositório)

**Título:** Implementar saga (orquestração manual) para onboarding: criar cliente, criar formulário associado, enviar notificação — com compensações e timeout.

**Descrição:**

`POST` (ou rota equivalente) que executa:

1. Criar **cliente**.
2. Criar **formulário** associado (cliente HTTP mock, in-process ou fila, conforme projeto).
3. Enviar **notificação** (email simulado ou fila).

**Compensações** na ordem inversa em falhas; **idempotência** em passos e compensações.

**Requisitos:**

- Implementação **manual** (sem framework de saga obrigatório).
- Tabela **`OnboardingSagaState`** (ou equivalente).
- **Timeout** (ex.: 30s) e **retry** (ex.: 5s entre tentativas) explícitos.
- Mocks/configuração para serviços externos.

**Cenários:** happy path; falha etapa 2; falha etapa 3; retry; timeout.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | OK |
| Estado | Persistência de saga |
| Happy path | Fluxo completo |
| Compensações | Ordem reversa; consistência |
| Timeout | Abort + compensação |
| Retry | Verificável |
| Idempotência | Sem duplicação |
| Correlação | IDs de rastreio |

## Entrega pedida

1. **BMAD** com instructions locais citadas.
2. Implementação.
3. Validação com cenários de falha.
