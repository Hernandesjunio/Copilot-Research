# Experimento — Cenário 3 (JWT / autorização) — Condição **B: Instructions locais**

## Regras de orquestração (condição B)

- **Idioma:** português. **Segurança:** não expor segredos; configurar chaves de forma segura.
- **Fonte:** `.github/instructions/`. Lacunas declaradas; sem MCP.
- **BMAD** obrigatório; citar ficheiros locais usados.
- **Não inventar** políticas que não estejam no código ou nas instructions.

## Tarefa (implementação no repositório)

**Título:** Refactor para autenticação JWT com autorização por role e regras de propriedade de recurso.

**Descrição:**

1. Validação de **JWT** nos endpoints da API de clientes.
2. Autorização por **role** em `POST`/`PUT`/`DELETE` (ex.: `Admin`, `ClienteManager`).
3. Em `ClienteServico` (ou equivalente): obter **userId** do utilizador atual.
4. Colunas **`CriadoPor`** e **`UltimoAtualizadoPor`** na entidade/tabela cliente, com migração segura.
5. Rota **`GET /clientes/meus`** conforme regras de negócio e instructions locais.
6. **Handler** ou política para impedir edição de recursos alheios (exceto `Admin`).
7. **Auditoria** (`ClienteAuditLog` ou equivalente).

**Restrições:** manter contrato HTTP; introduzir 401/403 onde necessário; JWT configurável para dev.

**Cenários esperados:** 401 sem token/ token inválido; 403 por role ou propriedade; listagens diferenciadas; audit em operações mutáveis.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Auth | Sem token → 401 |
| Roles | Comportamento Admin vs utilizador restrito |
| Create | `CriadoPor` preenchido |
| Update | 403 ao editar alheio com role restrita; Admin permitido |
| Audit | Registos com ator e tempo |
| `/clientes/meus` | Funcional e alinhado às regras |
| Contrato | Envelope mantido |

## Entrega pedida

1. **BMAD** com referências a `.github/instructions/`.
2. Implementação.
3. Plano de testes manuais.
