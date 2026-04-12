Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções e escalabilidade de contexto em múltiplos repositórios.

Contexto do experimento:

* Estou avaliando o uso de arquivos locais `.github/instructions` com entrypoints definidos em `copilot-instructions.md`
* O objetivo não é apenas avaliar qualidade da resposta, mas sim analisar a viabilidade dessa abordagem em um cenário com aproximadamente 100+ repositórios
* Quero entender se essa estratégia é sustentável como “fonte única de verdade” ou se gera problemas operacionais (duplicação, drift, manutenção, inconsistência)
* Neste teste, considere que o contexto vem exclusivamente das instructions locais

---

Tarefa:
Fazer um planejamento de implementação de um novo endpoint para atualizar o cliente por completo, usando boas práticas definidas, SOLID, mecanismos de resiliência e tolerância a falhas.

---

Regras:

1. Execute a tarefa normalmente utilizando o contexto local disponível
2. Após a execução, produza um relatório técnico estruturado

---

### Relatório do experimento

#### 1. Uso de contexto

* Quais sinais indicam uso efetivo das instructions locais
* Se houve lacunas mesmo com instructions presentes
* Dependência de inferência vs uso real de contexto

#### 2. Qualidade técnica do plano

* Estrutura BMAD (mesmo implícita)
* Clareza de camadas (API, domínio, infra)
* Uso de boas práticas (.NET, SOLID, resiliência)

#### 3. Limitações estruturais dessa abordagem

* Problemas de duplicação entre repositórios
* Risco de divergência entre instructions
* Dificuldade de evolução centralizada
* Acoplamento ao repositório

#### 4. Escalabilidade (100+ repositórios)

* Essa abordagem se sustenta?
* Qual esforço de manutenção esperado?
* Riscos operacionais

#### 5. Experiência de uso

* Fluidez
* Necessidade de reprompt
* Dependência de contexto manual

---

### Avaliação (0 a 10)

* aderência ao contexto
* qualidade técnica
* completude
* consistência
* escalabilidade da abordagem
* facilidade de manutenção

---

### Conclusão final

Escolha apenas uma:

* “instructions locais são viáveis como fonte única de verdade”
* “instructions locais funcionam, mas não escalam bem”
* “instructions locais não são adequadas para centralização de conhecimento”

---

Importante:

* Seja crítico
* Avalie como arquiteto, não como usuário casual
* Considere impacto organizacional
