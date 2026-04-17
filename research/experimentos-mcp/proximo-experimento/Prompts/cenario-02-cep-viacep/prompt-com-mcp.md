# Experimento — Cenário 2 (CEP / ViaCEP) — Condição **A: MCP**

## Regras de orquestração (condição A)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Stack assumida:** API de clientes em C#, .NET 8, ASP.NET Core, arquitetura em camadas.
- **MCP `corporate-instructions`:** padrões organizacionais vêm do MCP. Este bloco prevalece sobre o MCP se houver conflito explícito com o pedido abaixo.
- **Consulta MCP obrigatória em decisões transversais:**
  1. `list_instructions_index`
  2. `search_instructions` — várias queries (HttpClient, Polly, validação, cache, erros HTTP, observabilidade).
  3. `get_instructions_batch` — ler todas as instructions relevantes em profundidade.
  4. Cruzar policy × código: existente no repo = **FATO**; ausente = **HIPÓTESE**.
  5. Citar id da instruction + ficheiros do repo nas decisões.
- **Fluxo:** ler ficheiros antes de editar; após mudanças, `dotnet build` e testes se existirem.

## Tarefa (implementação no repositório)

**Título:** Implementar validação de CEP com integração resiliente ao ViaCEP (ou serviço equivalente).

**Descrição:**

Ao criar ou atualizar cliente com CEP:

1. Validar **formato** do CEP (8 dígitos, sem máscara ou normalizando entrada).
2. Consultar **ViaCEP** (URL pública habitual) ou **mock** configurável em testes/dev para obter logradouro, bairro, cidade, estado.
3. Armazenar endereço completo ou estado de erro de validação de forma consistente com o modelo de dados atual.
4. Implementar **resiliência:**
   - Timeout por chamada (ex.: 3 segundos — ajustar se as instructions MCP indicarem outro valor e o código já tiver padrão).
   - **Retry** com backoff exponencial (ex.: 1s, 2s, 4s) para falhas transitórias (5xx, timeout).
   - **Circuit breaker:** após um número definido de falhas consecutivas (ex.: 5), bloquear novas chamadas por um período (ex.: 30s); valores devem ser explícitos no código ou configuração.
   - **Fallback:** com circuito aberto ou falha persistente, permitir gravar cliente mas marcar validação de endereço como pendente (campo ou estado claro).
5. **Cache** do resultado de lookup por TTL (ex.: 24h ou configurável).
6. **Observabilidade:** registar latência, sucesso/falha e estado do circuit breaker (logs ou métricas já usadas no projeto).

**Restrições:**

- Não quebrar o CRUD existente.
- Evitar bloqueio desnecessário: se o projeto já usar padrão assíncrono end-to-end, mantê-lo.
- A validação de CEP e persistência devem ser **consistentes** com transações do repositório (definir na implementação como combinar chamada HTTP e escrita).

**Cenários esperados:**

- CEP válido → endereço obtido e armazenado.
- Timeout seguido de retry → eventual sucesso (quando o backend colaborar).
- Serviço indisponível (simular várias falhas) → circuit breaker abre → fallback aplicado.
- Mesmo CEP consultado duas vezes dentro do TTL → segunda leitura a partir de cache (sem novo HTTP).

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| HttpClient | Cliente HTTP nomeado/registado com políticas de resiliência |
| Validação | CEP com formato inválido → erro HTTP adequado (ex. 400) conforme contrato da API |
| ViaCEP | CEP válido → dados de endereço persistidos |
| Timeout / retry | Comportamento verificável sob simulação de lentidão/falha transitória |
| Circuit breaker | Após falhas repetidas → circuito aberto e fallback ou marcação pendente |
| Cache | Segunda consulta do mesmo CEP dentro do TTL não repete chamada HTTP |
| Correlation | Se existir `X-Correlation-Id` ou equivalente, propagar para a chamada externa |
| Health | Se o projeto expuser `/health` ou similar, incluir indicação do estado do circuito ou do cliente ViaCEP quando fizer sentido |
| Erros externos | CEP não encontrado na API externa mapeado para resposta da API de clientes de forma consistente (ex. 422) |

## Entrega pedida

1. Plano **BMAD** com FATO/HIPÓTESE face ao código e às instructions MCP usadas.
2. Implementação no repositório.
3. Passos de validação manual ou testes para cada critério relevante.
