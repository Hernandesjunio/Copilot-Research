# Experimento — Cenário 4 (Saga onboarding) — Condição **C: Baseline**

## Regras de orquestração (condição C)

- **Idioma:** português. **Segurança:** credenciais apenas em configuração segura.
- **Sem MCP** e **sem** `.github/instructions/`. Só código do repositório.
- **HIPÓTESE** clara para integrações não presentes no código.
- **BMAD** antes de codificar.

## Tarefa (implementação no repositório)

**Título:** Implementar saga (orquestração manual) para onboarding: criar cliente, criar formulário associado, enviar notificação — com compensações e timeout.

**Descrição:**

Endpoint de onboarding que executa três passos sequenciais (cliente → formulário → notificação), com **compensações** em ordem inversa se falhar, **estado** persistido, **timeout** global (ex.: 30s), **retry** onde fizer sentido, **idempotência** em operações e compensações. Serviços externos simulados de forma explícita no código se não existirem.

**Cenários:** sucesso; falha em cada etapa; retry; timeout.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Estado | Tabela/store de saga |
| Happy path | Fluxo completo |
| Falhas | Compensações corretas |
| Timeout | Abort + compensação |
| Idempotência | Testável |
| Rastreio | Correlação mínima |

## Entrega pedida

1. **BMAD** só com base no código.
2. Implementação.
3. Passos de validação.
