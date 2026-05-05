Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, qualidade de implementação e comportamento do Copilot na ausência de contexto estruturado.

## Contexto do experimento

**Identificação:** Cenário 3 (JWT / autorização) — condição **C: Baseline**.

Estou avaliando o comportamento do Copilot em um cenário sem contexto estruturado dedicado, sem uso de `copilot-instructions.md`, `.github/instructions` e MCP `corporate-instructions`.

Neste teste, considere que:
- não há `.github/instructions` como fonte confiável de orientação adicional;
- não há MCP como mecanismo de recuperação de contexto;
- o contexto disponível vem apenas do código visível no workspace e do conhecimento geral do modelo.

**Regras de orquestração (condição C)**

- **Idioma:** português. **Segurança:** proteger segredos e não os commitar.
- **Sem MCP** e **sem** `.github/instructions/`. Apenas código do repo.
- **HIPÓTESE** explícita quando o código não definir convenção.
- **BMAD** antes de implementar.

O objetivo do experimento não é apenas avaliar a qualidade da resposta, mas observar:
- quanto da solução depende de inferência;
- quais lacunas aparecem sem uma fonte estruturada de contexto;
- quão sustentável é esse modo de trabalho para implementação real.

## Tarefa

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

A implementação deve ser validável contra a tabela acima (comandos e critérios de sucesso explícitos na Parte 1).

## Regras obrigatórias

1. Execute a tarefa normalmente com base apenas no código disponível.
2. Após a execução, produza um relatório técnico estruturado.
3. Diferencie explicitamente:
   - FATO
   - HIPÓTESE
   - RISCO DE INTERPRETAÇÃO
4. Não trate inferência como evidência.
5. Seja crítico e direto.
6. Ao final, reporte métricas de execução. Se alguma métrica não puder ser obtida automaticamente, marque como N/A e explique o método de estimativa e o impacto na validade do experimento.
7. Exporte o resultado para um arquivo Markdown no workspace (ver seção “Exportação”).

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__baseline.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`baseline`).

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- **JWT** na API de clientes (middleware/authentication alinhado ao projeto).
- Autorização por **roles** em operações mutáveis; **401/403** onde aplicável.
- **`CriadoPor`** / **`UltimoAtualizadoPor`** com migração segura.
- **`GET /clientes/meus`** e regras de listagem (Admin vs restrito) conforme código.
- **Política/handler** de propriedade de recurso (edição alheia bloqueada salvo Admin).
- **Auditoria** das operações relevantes.

#### 2) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 3) Implementação (patch)
- Aplique as mudanças no código (auth, autorização, modelo, rotas, migração, auditoria conforme padrões do repo).

#### 4) Validação
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
- `ancoragem` (codigo_repo | inferencia)
- `evidencia` (arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

### 1. Uso de contexto
Avalie:
- quais decisões foram ancoradas diretamente no código;
- quais decisões dependeram de inferência;
- quais lacunas impediram maior precisão.

### 2. Qualidade técnica do plano
Avalie:
- estrutura do plano;
- clareza de camadas;
- coerência arquitetural;
- adequação ao nível de complexidade da tarefa;
- sinais de genericidade ou overengineering.

### 3. Limitações estruturais da abordagem
Analise:
- riscos de depender apenas do código visível;
- impacto da ausência de diretrizes explícitas;
- probabilidade de respostas inconsistentes entre execuções;
- risco de erro em desenvolvimento real.

### 4. Sustentabilidade para implementação real
Explique:
- se essa abordagem se sustenta em tarefas reais;
- qual esforço de reprompt tende a ser necessário;
- quais tipos de decisão ficam frágeis sem contexto adicional.

### 5. Experiência de uso
Avalie:
- fluidez;
- previsibilidade;
- necessidade de descoberta manual;
- dependência de interpretação do modelo.

## Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao código observável
- qualidade técnica
- completude
- consistência
- previsibilidade
- sustentabilidade para implementação real

## Conclusão final

Escolha apenas uma:

- “baseline é suficiente para este tipo de implementação”
- “baseline funciona parcialmente, mas exige muita inferência”
- “baseline é insuficiente para implementação confiável”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como arquiteto, não como usuário casual.
- Priorize evidência observável sobre opinião.
