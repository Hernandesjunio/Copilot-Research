Quero que você atue como um avaliador técnico com foco em arquitetura, centralização de conhecimento e extensibilidade do Copilot.

Contexto do experimento:

* Estou avaliando um MCP customizado com tools que fornecem contexto e capacidades para o Copilot
* O objetivo principal é verificar se essa abordagem permite criar uma “fonte única de verdade” reutilizável entre múltiplos repositórios (100+)
* Diferente das instructions locais, o MCP centraliza conhecimento e comportamento
* Neste teste, priorize o uso do MCP como mecanismo principal de contexto

---

Tarefa:
Fazer um planejamento de implementação de um novo endpoint para atualizar o cliente por completo, usando boas práticas definidas, SOLID, mecanismos de resiliência e tolerância a falhas.

---

Regras:

1. Execute a tarefa considerando uso de tools e contexto fornecido pelo MCP
2. Após a execução, produza um relatório técnico estruturado

---

### Relatório do experimento

#### 1. Uso do MCP

* Evidências de uso efetivo das tools
* Onde o MCP agregou valor real
* Onde poderia ter sido melhor utilizado

#### 2. Qualidade técnica do plano

* Estruturação (BMAD implícito ou explícito)
* Organização em camadas
* Aderência a boas práticas

#### 3. Centralização de conhecimento

* O MCP permite evitar duplicação entre repositórios?
* O conhecimento parece reutilizável?
* Há indícios de consistência transversal?

#### 4. Limitações da abordagem

* Dependência de chamadas de tool
* Latência
* Possíveis gargalos
* Complexidade operacional

#### 5. Escalabilidade (100+ repositórios)

* O MCP se comporta bem como fonte única de verdade?
* Facilidade de evolução centralizada
* Governança de conhecimento

#### 6. Experiência de uso

* Fluidez
* Interrupções no fluxo
* Dependência de prompt

---

### Avaliação (0 a 10)

* aderência ao contexto
* qualidade técnica
* completude
* consistência
* capacidade de centralização
* escalabilidade
* governança

---

### Conclusão final

Escolha apenas uma:

* “MCP é viável como fonte única de verdade”
* “MCP ajuda, mas precisa de complementos”
* “MCP não resolve o problema de centralização”

---

Importante:

* Seja crítico
* Avalie como solução arquitetural, não apenas técnica
* Considere cenário corporativo real
