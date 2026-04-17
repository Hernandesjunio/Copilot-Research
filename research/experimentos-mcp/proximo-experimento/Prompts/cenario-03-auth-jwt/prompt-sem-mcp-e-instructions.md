# Experimento — Cenário 3 (JWT / autorização) — Condição **C: Baseline**

## Regras de orquestração (condição C)

- **Idioma:** português. **Segurança:** proteger segredos e não os commitar.
- **Sem MCP** e **sem** `.github/instructions/`. Apenas código do repo.
- **HIPÓTESE** explícita quando o código não definir convenção.
- **BMAD** antes de implementar.

## Tarefa (implementação no repositório)

**Título:** Refactor para autenticação JWT com autorização por role e regras de propriedade de recurso.

**Descrição:**

1. Autenticação **JWT** na API de clientes.
2. Autorização por **role** em operações de escrita.
3. **userId** a partir de claims no serviço de clientes.
4. Colunas **`CriadoPor`** e **`UltimoAtualizadoPor`** + migração.
5. **`GET /clientes/meus`**.
6. Política/handler para recurso próprio vs alheio.
7. **Auditoria** de operações.

**Restrições:** preservar contrato HTTP; 401/403 onde aplicável.

**Cenários:** sem token; token inválido; role insuficiente; Admin vs utilizador; edição alheia bloqueada; audit.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Auth | 401 sem token |
| Listagens | Admin vs restrito conforme desenho |
| Create | `CriadoPor` |
| Update | 403 / exceção Admin |
| Audit | Registos |
| `/clientes/meus` | OK |
| Contrato | Mantido |

## Entrega pedida

1. **BMAD** baseado só no código.
2. Implementação.
3. Validação.
