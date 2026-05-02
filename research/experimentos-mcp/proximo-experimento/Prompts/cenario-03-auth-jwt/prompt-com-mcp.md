Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, engenharia de contexto e escalabilidade em múltiplos repositórios.

## Contexto do experimento

**Identificação:** Cenário 3 (JWT / autorização) — condição **A: MCP** (`corporate-instructions`).

Estou avaliando o comportamento do Copilot em um cenário com MCP `corporate-instructions`.

Objetivo do experimento:
- avaliar a qualidade da implementação produzida (plano + patch + validação);
- avaliar o quanto a solução depende de contexto local real;
- analisar a viabilidade dessa abordagem em cenários com muitos repositórios;
- identificar riscos de duplicação, drift, manutenção, inconsistência e acoplamento ao repositório.

Neste teste, considere que o contexto vem de:
- contexto recuperado via MCP `corporate-instructions` (tools/resources), como fonte principal de guardrails organizacionais;
- instructions locais (quando existirem) e código disponível no workspace como evidência observável complementar.

**Regras de orquestração (condição A)**

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais em código ou logs; usar configuração segura para chaves.
- **Escopo:** apenas este repositório.
- **MCP `corporate-instructions`:** consultar antes de decisões de segurança, autorização, erros HTTP e camadas.
- **Passos MCP:** `list_instructions_index` → várias `search_instructions` (JWT, autorização, validação, erros) → `get_instructions_batch` para o conjunto relevante → cruzar com código (**FATO** vs **HIPÓTESE**) → citar ids e ficheiros.
- **Fluxo:** ler código alvo antes de editar; `dotnet build` após alterações.

## Tarefa

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

A implementação deve ser validável contra a tabela acima (comandos e critérios de sucesso explícitos na Parte 1).

## Regras obrigatórias

1. Execute a tarefa usando MCP `corporate-instructions` como fonte principal de guardrails organizacionais, cruzando sempre com o código do repositório; quando instructions locais existirem, incorpore-as como evidência complementar.
2. Após a execução, produza um relatório técnico estruturado.
3. Diferencie explicitamente:
   - FATO
   - HIPÓTESE
   - RISCO DE INTERPRETAÇÃO
4. Não trate inferência como evidência.
5. Seja crítico e direto.
6. Ao final, reporte métricas de execução. Se alguma métrica não puder ser obtida automaticamente, marque como N/A e explique o método de estimativa e o impacto na validade do experimento.
7. Exporte o resultado para um arquivo Markdown no workspace (ver seção “Exportação”).
8. Política de uso de tools: prefira “tool-first” para recuperar guardrails via MCP (e ler ficheiros do repo) antes de propor mudanças; se exceder o necessário, justifique no relatório (custo/benefício e o que foi obtido).

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__mcp.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`mcp`).

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Seleção de guardrails e evidências (antes de codar)
- Liste os `id` das instructions aplicáveis via MCP (e, se existirem, locais) e para qual decisão cada uma será usada (ex.: JWT, autorização, erros HTTP, auditoria).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).

#### 2) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- **JWT** + autorização por **roles**; **401/403** conforme tabela de aceite.
- **`CriadoPor` / `UltimoAtualizadoPor`** + migração; **`GET /clientes/meus`** e listagens Admin vs restrito.
- **Handler/política** de propriedade de recurso; **auditoria** das operações mutáveis.
- Configuração segura de segredos (sem expor no repo).

#### 3) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 4) Implementação (patch)
- Aplique as mudanças no código conforme padrões do repo e corpus MCP aplicável.

#### 5) Validação
- Execute/indique validações objetivas (por exemplo: `dotnet build`, testes quando aplicável).
- Relacione cada linha relevante da tabela de critérios de aceite a um passo de verificação ou comando.
- Se não for possível executar algo, descreva o comando exato e o critério de sucesso.

## Relatório do experimento

### 0. Métricas de execução (obrigatório)
Reporte, no mínimo, os itens abaixo (use N/A quando a plataforma não fornecer o dado):
- tempo total (wall-clock): `inicio_iso`, `fim_iso`, `duracao_ms`
- latência por etapa: exploração/leitura, raciocínio/decisão, escrita do patch, validação, escrita do relatório (em ms)
- uso de tools: `qtd_tool_calls_total`, `qtd_por_tool`, `sucessos`, `falhas`, `retries`
- I/O de contexto: `qtd_arquivos_lidos`, `qtd_arquivos_citados`, `qtd_trechos_citados`, `bytes_aprox_lidos` (ou N/A)
- tokens: `tokens_input` e `tokens_output` (se disponível); senão `tokens_input_est` e `tokens_output_est` + método + margem de erro assumida
- custo: `custo_total` e `moeda` (ou N/A)
- tamanho do resultado: `caracteres_resposta` (ou N/A) e `qtd_itens_patch`
- contagens para rigor experimental: `qtd_afirmacoes_FATO`, `qtd_afirmacoes_HIPOTESE`, `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`

Ao final do relatório, inclua obrigatoriamente um bloco único chamado `EXPERIMENT_METRICS_JSON` contendo exatamente os campos acima em JSON.

Inclua também obrigatoriamente um bloco único chamado `DECISIONS_JSON` (em JSON) com, no mínimo, uma lista de decisões-chave contendo:
- `decisao`
- `ancoragem` (MCP | instruction_local | codigo_repo | inferencia)
- `evidencia` (id/arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

### 1. Evidência de uso de contexto
Para cada decisão importante da solução, classifique como:
- ancorada em instruction MCP;
- ancorada em instruction local;
- ancorada no código do repositório;
- inferida por conhecimento geral.

Aponte:
- quais decisões mostram uso efetivo do corpus MCP;
- onde houve lacunas;
- onde o plano dependeu de inferência.

### 2. Qualidade técnica do plano
Avalie:
- estruturação do plano (BMAD) e adequação do patch ao plano;
- clareza de camadas;
- coerência arquitetural;
- adequação ao nível de complexidade da tarefa;
- presença de excesso de genericidade ou overengineering.

### 3. Limitações estruturais da abordagem
Analise criticamente:
- duplicação entre repositórios;
- risco de drift entre MCP e código local;
- dificuldade de evolução centralizada do corpus;
- acoplamento do conhecimento ao repositório.

### 4. Escalabilidade em 100+ repositórios
Explique:
- se a abordagem MCP + código se sustenta;
- em que condições ela deixa de se sustentar;
- qual esforço de manutenção ela tende a exigir;
- quais riscos operacionais são previsíveis.

### 5. Experiência de uso
Avalie:
- fluidez;
- necessidade de reprompt;
- dependência de descoberta manual;
- previsibilidade do comportamento.

## Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao contexto recuperado (MCP + repo)
- qualidade técnica
- completude
- consistência
- escalabilidade da abordagem
- facilidade de manutenção

## Conclusão final

Escolha apenas uma:

- “MCP corporate-instructions foi suficiente para ancorar guardrails neste tipo de implementação”
- “MCP ajudou parcialmente, mas ainda foi necessária inferência significativa”
- “MCP não foi adequado para reduzir inferência ou guiar a implementação de forma confiável”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como arquiteto de soluções corporativas, não como usuário casual.
- Priorize evidência observável (código, corpus MCP, instructions locais) sobre opinião.
- Não produza resposta diplomática quando a evidência for fraca; registre o risco.
