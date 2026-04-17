# Experimento — Cenário 3 (JWT / autorização) — Condição **A: MCP**

## Regras de orquestração (condição A)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais em código ou logs; usar configuração segura para chaves.
- **Escopo:** apenas este repositório.
- **MCP `corporate-instructions`:** consultar antes de decisões de segurança, autorização, erros HTTP e camadas.
- **Passos MCP:** `list_instructions_index` → várias `search_instructions` (JWT, autorização, validação, erros) → `get_instructions_batch` para o conjunto relevante → cruzar com código (**FATO** vs **HIPÓTESE**) → citar ids e ficheiros.
- **Fluxo:** ler código alvo antes de editar; `dotnet build` após alterações.

## Tarefa (implementação no repositório)

**Título:** Refactor para autenticação JWT com autorização por role e regras de propriedade de recurso.

**Descrição:**

1. Implementar validação de **JWT** nos endpoints da API de clientes (middleware ou `AddAuthentication("Bearer")` + configuração alinhada ao projeto).
2. Aplicar autorização por **role** nos endpoints de criação, atualização e eliminação de clientes (ex.: roles `Admin`, `ClienteManager` — ajustar nomes ao domínio se as instructions indicarem convenção).
3. No serviço de domínio de clientes (ex.: `ClienteServico`): obter **identificador do utilizador** a partir de `ClaimsPrincipal` / contexto atual.
4. Adicionar colunas **`CriadoPor`** (GUID) e **`UltimoAtualizadoPor`** (GUID) na entidade/tabela `Cliente` (com migração compatível com dados existentes).
5. Adicionar rota **`GET /clientes/meus`** que devolve apenas clientes do utilizador autenticado quando a role assim o exigir; `Admin` pode ver todos conforme regras abaixo.
6. Implementar **handler** ou política de autorização (ex.: `ClientePermissionHandler`) que garanta: utilizador só altera clientes que criou **ou** tem role elevada (`Admin`), conforme definido.
7. **Auditoria:** registar operações (criação, atualização, eliminação) com ator e timestamp — tabela `ClienteAuditLog` ou mecanismo equivalente já usado no projeto.

**Restrições:**

- Não quebrar o contrato HTTP existente (envelope de resposta, códigos exceto introdução de 401/403 onde aplicável).
- `GET /clientes` (lista): comportamento diferenciado — ex.: `Admin` vê todos; `ClienteManager` vê apenas os seus (ou conforme combinado com o código base).
- Token JWT pode usar configuração local de desenvolvimento (sem expor segredos no repositório).

**Cenários esperados:**

- Pedido sem token → **401 Unauthorized**.
- Token inválido → **401**.
- Token válido mas role insuficiente para a operação → **403 Forbidden**.
- `Admin` lista todos os clientes em `GET /clientes` (se esse for o desenho).
- Utilizador com âmbito restrito lista apenas os seus em `GET /clientes` ou `/clientes/meus` conforme implementação coerente.
- Utilizador tenta editar cliente de outro → **403** (salvo `Admin`).
- Operações de escrita registam criador/atualizador e audit log quando aplicável.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Auth | `GET /clientes` sem token → 401 |
| Admin | Com token `Admin` → listagem completa se esse for o requisito |
| Utilizador | Com token de âmbito restrito → apenas clientes permitidos |
| Create | `POST` regista `CriadoPor` = id do utilizador |
| Update alheio | `PUT` em recurso de outro utilizador com role restrita → 403 |
| Admin edita | `PUT` com `Admin` em recurso alheio → permitido |
| Audit | `DELETE` (e outras operações definidas) geram registo de auditoria |
| `/clientes/meus` | Endpoint implementado e coerente com as regras |
| Contrato | Envelope de resposta mantido onde já existia |

## Entrega pedida

1. **BMAD** com FATO/HIPÓTESE e referências MCP.
2. Implementação completa.
3. Como testar cada fluxo (incl. exemplos de claims/roles sem dados sensíveis).
