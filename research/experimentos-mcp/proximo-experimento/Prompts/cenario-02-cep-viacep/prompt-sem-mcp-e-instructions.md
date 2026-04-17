# Experimento — Cenário 2 (CEP / ViaCEP) — Condição **C: Baseline**

## Regras de orquestração (condição C)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais.
- **Limites:** se faltar dado decisivo, explicitar inferência e 2–3 opções.
- **Não usar** MCP nem `.github/instructions/`. Apenas código do repositório.
- **HIPÓTESE** clara quando não houver evidência no código.
- **Contexto:** API de clientes, C#, .NET 8, ASP.NET Core.
- **BMAD** antes de codificar.

## Tarefa (implementação no repositório)

**Título:** Implementar validação de CEP com integração resiliente ao ViaCEP (ou serviço equivalente).

**Descrição:**

Ao criar ou atualizar cliente com CEP:

1. Validar **formato** do CEP (8 dígitos, normalizando se necessário).
2. Consultar **ViaCEP** ou **mock** para obter logradouro, bairro, cidade, estado.
3. Armazenar endereço ou estado de erro conforme o modelo atual.
4. **Resiliência:** timeout, retry com backoff, circuit breaker, fallback para “validação pendente”.
5. **Cache** por TTL configurável.
6. **Observabilidade** mínima alinhada ao que o projeto já usa (logs, etc.).

**Restrições:**

- Não quebrar o CRUD.
- Manter estilo assíncrono do projeto.
- Transação/consistência entre HTTP e BD explicada na implementação.

**Cenários esperados:** CEP válido; timeout+retry; indisponibilidade+circuito+fallback; cache hit.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| HttpClient | Cliente com políticas |
| Validação | Formato inválido → erro adequado |
| ViaCEP | CEP válido → dados persistidos |
| Resiliência | Timeout, retry, circuito, fallback verificáveis |
| Cache | Segunda consulta via cache no período TTL |
| Correlation | Se existir no projeto, propagar |
| Health | Se existir endpoint, integrar quando fizer sentido |
| Erros | Mapeamento coerente para a API |

## Entrega pedida

1. **BMAD** só com base no código.
2. Implementação.
3. Passos de validação.
