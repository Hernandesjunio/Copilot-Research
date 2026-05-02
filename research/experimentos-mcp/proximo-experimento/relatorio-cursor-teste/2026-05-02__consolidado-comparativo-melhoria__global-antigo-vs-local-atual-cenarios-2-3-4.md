# Consolidado comparativo de melhoria

## Escopo

Este documento consolida os resultados dos cenários:

- `cenario-02-cep-viacep`
- `cenario-03-auth-jwt`
- `cenario-04-saga-onboarding`

Comparação entre:

- **Global antigo**: instância antiga de `corporate-instructions`
- **Local atual**: versão atual do projeto em `mcp-instructions-server/`

Objetivo:

- dar uma leitura única de **possível melhoria**
- facilitar repetição prática do teste **diretamente no Visual Studio via Copilot**

## Artefatos base desta consolidação

- `2026-05-02__smoke-mcp-stdio__global-antigo.md`
- `2026-05-02__smoke-mcp-stdio__local-atual.md`
- `2026-05-02__smoke-mcp-stdio__local-atual-iteracao-2.md`
- `2026-05-02__smoke-mcp-stdio__local-atual-iteracao-3.md`
- `2026-05-02__smoke-mcp-stdio__local-atual-cenarios-2-3-4.md`
- `2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual.md`
- `2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual-cenarios-2-3-4.md`

## Resumo executivo

Leitura consolidada:

- o **MCP local atual** é melhor do que o **global antigo** para consumo por agente/cliente
- o ganho mais claro não está só no ranking bruto, mas no **contrato utilizável**
- a melhoria mais forte apareceu em **JWT/autorização**
- a melhoria mais parcial apareceu em **CEP/ViaCEP**, porque o principal gargalo continua sendo a falta de contexto de domínio específico no corpus

Em termos práticos:

- se o objetivo for **usar no Visual Studio com Copilot** e aumentar a chance de o agente convergir com menos tentativa manual, a versão local atual é a candidata mais forte
- se o objetivo for apenas busca lexical básica, o global antigo ainda funciona, mas entrega menos suporte operacional

## Quadro consolidado

| Dimensão | Global antigo | Local atual | Leitura |
|---|---|---|---|
| Tools expostas | 3 | 6 | O atual amplia o contrato sem quebrar o núcleo antigo |
| Busca básica | boa | boa | O atual preserva a capacidade de discovery |
| Explicabilidade | baixa | alta | Diagnósticos e contexto resolvido ajudam a confiar/refinar |
| Checklist por cenário | não | sim | Melhora completude técnica |
| Conflitos/precedência | não | sim | Reduz uso ingênuo de instructions concorrentes |
| Ergonomia para agente | média | alta | Menos orquestração manual entre `search` e `batch` |
| Dependência de inferência de domínio | alta | ainda alta em alguns casos | Melhorou, mas não desapareceu |

## Cenário 2 — CEP / ViaCEP

### O que melhorou

- o atual continua encontrando bem resiliência, `HttpClient`, cache, contrato HTTP e observabilidade
- `resolve_instruction_context` já devolve um pacote mais acionável para integração HTTP resiliente
- `get_normative_checklist` ajuda a consolidar contrato HTTP mínimo
- `detect_instruction_conflicts` evita leitura simplista de instruções próximas de API/erros

### O que ainda limita

- não existe guidance realmente específico para **ViaCEP**
- não existe guidance específico para **modelo de endereço**
- estado como “validação pendente” continua dependendo de inferência e do repositório-alvo

### Veredicto do cenário

**Melhoria parcial, mas real.**

O atual melhora bastante o uso do corpus, mas não resolve sozinho a lacuna de domínio.

## Cenário 3 — Auth / JWT

### O que melhorou

- este já era o melhor cenário no corpus antigo
- no atual, o mesmo núcleo forte ficou mais utilizável:
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-api-validation-and-error-contracts`
- o contexto resolvido já separa e consolida o baseline normativo
- o checklist de `security_baseline` acelera leitura prática
- a tool de conflitos deixa claro que auth e resource-scope devem ser combinados, não escolhidos cegamente

### O que ainda limita

- nomes concretos de roles continuam locais
- regras exatas de `/clientes/meus` continuam locais
- detalhes de schema e auditoria continuam dependentes do produto

### Veredicto do cenário

**Melhoria forte.**

Este é o melhor candidato para validar ganho no Visual Studio com Copilot.

## Cenário 4 — Saga onboarding

### O que melhorou

- o corpus atual continua forte em saga, outbox, idempotência, resiliência e observabilidade
- `resolve_instruction_context` melhora muito a leitura:
  - `policy` de mensageria/outbox como baseline
  - `reference` de saga como apoio
- `get_normative_checklist` ajuda a transformar o tema em plano acionável
- `detect_instruction_conflicts` evita tratar a reference de saga como regra superior

### O que ainda limita

- `OnboardingSagaState` continua sem desenho pronto no corpus
- shape de compensações e integrações externas continua dependente do repositório
- timeout/retry por etapa continuam a exigir decisão local

### Veredicto do cenário

**Melhoria boa, com limite estrutural.**

O atual ajuda mais no desenho correto, mas não substitui contexto do sistema-alvo.

## Síntese de melhoria provável

Se a pergunta for “onde existe maior chance de o Copilot melhorar de forma observável no Visual Studio?”, a leitura consolidada é:

1. **Maior chance de melhoria**: `cenario-03-auth-jwt`
2. **Boa chance de melhoria**: `cenario-04-saga-onboarding`
3. **Chance de melhoria mais limitada**: `cenario-02-cep-viacep`

Justificativa:

- `JWT/auth` depende muito de guardrails transversais, onde o corpus já é forte
- `Saga` beneficia muito da nova separação entre baseline normativo e referência
- `CEP/ViaCEP` continua esbarrando em ausência de contexto de negócio específico

## O que validar no Visual Studio via Copilot

Para um teste direto e comparável no Visual Studio, o ideal é verificar não só o resultado final, mas o **comportamento intermediário** do agente.

### Sinais de melhoria esperados no local atual

- o agente faz menos idas e vindas manuais entre busca e leitura profunda
- o agente converge mais cedo para um conjunto menor de instructions relevantes
- o agente evita misturar policy e reference sem explicação
- o agente mostra mais consistência ao justificar decisões transversais
- o agente tende a produzir plano inicial mais alinhado ao corpus

### Sinais de que a melhoria não aconteceu

- o agente continua ignorando o MCP ou usando-o só superficialmente
- o agente continua inferindo demais mesmo quando há instruction clara
- o agente mistura guidance conflitante sem explicitar precedência
- o plano final continua genérico demais e pouco ancorado

## Roteiro prático de teste no Visual Studio

Use o mesmo repositório-alvo para os dois testes e rode os prompts o mais literalmente possível.

### Ordem recomendada

1. Testar primeiro `cenario-03-auth-jwt`
2. Depois `cenario-04-saga-onboarding`
3. Por último `cenario-02-cep-viacep`

### Como comparar

Para cada cenário, observe:

- quantidade de reprompts necessários
- se o agente consulta o MCP cedo ou tarde
- quantas decisões relevantes vêm ancoradas em instructions
- se o agente consegue montar plano coerente antes de editar
- se ele usa melhor o contexto composto no caso da versão atual

### Checklist simples de observação

- O agente identificou rapidamente as instructions centrais?
- O agente explicou conflitos ou apenas escolheu documentos “no feeling”?
- O plano inicial ficou mais específico?
- Houve menos deriva para soluções genéricas?
- A justificativa técnica ficou mais ancorada?
- O agente pareceu “menos perdido” entre múltiplas directions?

## Recomendação de teste direto

Se você quiser maximizar o valor do experimento no Visual Studio:

- comece por **JWT**
- use depois **Saga**
- deixe **CEP/ViaCEP** como cenário de stress para medir o limite do corpus

Isso dá um gradiente melhor:

- primeiro um caso onde a melhoria deve aparecer
- depois um caso onde a melhoria ajuda bastante, mas não fecha tudo
- por fim um caso onde o limite do corpus fica mais visível

## Conclusão consolidada

O MCP local atual mostra **melhoria plausível e relevante** sobre o global antigo para uso com Copilot no Visual Studio, principalmente porque transforma melhor o corpus em contexto operacional.

O ganho mais confiável para validação prática está em:

- `cenario-03-auth-jwt`
- `cenario-04-saga-onboarding`

O cenário mais útil para medir limite estrutural continua sendo:

- `cenario-02-cep-viacep`

## Veredicto final

Se a pergunta for “vale testar diretamente no Visual Studio via Copilot a versão atual para verificar ganho real?”, a resposta é **sim**.

Se a pergunta for “esse ganho deve aparecer igualmente em qualquer cenário?”, a resposta é **não**.

A expectativa mais realista é:

- **ganho forte** em `JWT`
- **ganho bom** em `Saga`
- **ganho parcial** em `CEP/ViaCEP`
