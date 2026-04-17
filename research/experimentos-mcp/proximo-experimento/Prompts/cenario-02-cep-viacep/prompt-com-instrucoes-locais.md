# Experimento — Cenário 2 (CEP / ViaCEP) — Condição **B: Instructions locais**

## Regras de orquestração (condição B)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Não inventar:** sem evidência no código ou em `.github/instructions/`, rotular como **HIPÓTESE** e dizer como validar.
- **Fonte principal:** `.github/instructions/`. Se inexistente ou incompleta, declarar **lacuna**.
- **Não usar MCP** nesta condição.
- **BMAD** antes de codificar; citar ficheiros de instructions usados.

## Tarefa (implementação no repositório)

**Título:** Implementar validação de CEP com integração resiliente ao ViaCEP (ou serviço equivalente).

**Descrição:**

Ao criar ou atualizar cliente com CEP:

1. Validar **formato** do CEP (8 dígitos, sem máscara ou normalizando entrada).
2. Consultar **ViaCEP** ou **mock** configurável em testes/dev para obter logradouro, bairro, cidade, estado.
3. Armazenar endereço completo ou estado de erro de validação de forma consistente com o modelo de dados atual.
4. Implementar **resiliência:**
   - Timeout por chamada (ex.: 3s).
   - **Retry** com backoff exponencial (ex.: 1s, 2s, 4s) para falhas transitórias.
   - **Circuit breaker:** após falhas consecutivas (ex.: 5), bloquear chamadas por um período (ex.: 30s).
   - **Fallback:** circuito aberto ou falha persistente → gravar cliente com validação de endereço pendente.
5. **Cache** do resultado de lookup por TTL (ex.: 24h ou configurável).
6. **Observabilidade:** latência, sucesso/falha, estado do circuit breaker.

**Restrições:**

- Não quebrar o CRUD existente.
- Evitar bloqueio desnecessário; manter padrão assíncrono do projeto se houver.
- Consistência entre chamada HTTP e persistência (definir na implementação).

**Cenários esperados:**

- CEP válido → endereço obtido e armazenado.
- Timeout + retry → sucesso quando possível.
- Serviço fora do ar → circuit breaker → fallback.
- Mesmo CEP duas vezes no intervalo de cache → segunda via cache.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| HttpClient | Cliente HTTP com políticas de resiliência |
| Validação | Formato inválido → erro HTTP adequado |
| ViaCEP | CEP válido → endereço persistido |
| Timeout / retry | Comportamento sob simulação |
| Circuit breaker | Falhas repetidas → circuito aberto + fallback |
| Cache | Segunda consulta dentro do TTL sem HTTP |
| Correlation | Propagação de correlation id se o projeto usar |
| Health | Indicação no health check se aplicável |
| Erros externos | Mapeamento coerente (ex. não encontrado → 422) |

## Entrega pedida

1. Plano **BMAD** com referência às instructions locais usadas.
2. Implementação.
3. Validação alinhada aos critérios.
