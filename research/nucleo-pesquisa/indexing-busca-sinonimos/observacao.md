# Observação — Limitação do Mecanismo de Sinônimos no Indexing

## Contexto

Durante a análise do arquivo `indexing.py`, foi identificado que o mecanismo de expansão de query utiliza uma abordagem baseada em um dicionário estático de sinônimos embutido diretamente no código.

Esse mecanismo tem como objetivo melhorar a recuperação de documentos ao considerar termos relacionados durante a busca.

## Observação Principal

A estratégia atual de sinônimos apresenta uma limitação estrutural para uso em um cenário corporativo e multi-domínio.

O problema não está apenas na quantidade de sinônimos definidos, mas no próprio modelo adotado:

- a lista é estática e hardcoded;
- não existe mecanismo natural de extensão;
- a evolução depende de alteração de código;
- não há separação entre domínio e mecanismo de busca;
- não existe governança formal do vocabulário.

## Problema Arquitetural

A abordagem atual acopla diretamente o conhecimento semântico ao código da aplicação.

Isso gera alguns efeitos relevantes:

- dificulta a escalabilidade para novos domínios técnicos;
- introduz viés baseado nos domínios inicialmente modelados;
- exige manutenção manual constante;
- aumenta o risco de inconsistência semântica ao longo do tempo;
- impede evolução independente do mecanismo de busca e do vocabulário.

## Impacto em Cenário Corporativo

Considerando o objetivo do MCP de atuar como uma camada centralizada de contexto para múltiplos repositórios e múltiplos domínios técnicos, essa limitação pode gerar:

- baixa cobertura semântica fora dos domínios iniciais (ex: backend);
- dificuldade de suportar áreas como frontend, mobile, banco de dados, segurança, etc;
- aumento de falso positivo ao tratar conceitos diferentes como equivalentes;
- aumento de falso negativo por ausência de termos relevantes;
- necessidade de intervenção constante no código para cada novo contexto;
- dificuldade de governança do vocabulário entre times diferentes.

## Exemplo de Risco

Domínios distintos podem compartilhar termos genéricos, mas possuir semânticas diferentes.

Exemplo:

- FIX messaging vs RabbitMQ

Embora ambos possam ser classificados superficialmente como "mensageria", possuem:

- modelos de comunicação diferentes;
- protocolos distintos;
- requisitos específicos de domínio.

Uma expansão semântica simplista pode gerar recuperação de contexto inadequado, prejudicando a qualidade das respostas.

## Conclusão

O mecanismo atual de sinônimos é adequado como solução inicial (MVP), porém apresenta limitações estruturais para evolução do MCP como solução corporativa.

A principal limitação não é a falta de termos, mas o fato de que o modelo:

- não é extensível de forma desacoplada;
- não permite governança adequada;
- não escala para múltiplos domínios técnicos;
- pode comprometer a precisão da recuperação de contexto.

## Direção de Evolução (Hipótese)

Como próximo passo, é recomendado avaliar uma evolução arquitetural que permita:

- desacoplar o vocabulário do código;
- suportar múltiplos domínios técnicos;
- permitir extensão sem alteração direta do core;
- melhorar controle sobre expansão semântica;
- manter previsibilidade e explicabilidade do ranking.

Essa evolução deve ser feita de forma incremental, preservando a simplicidade onde possível e evitando overengineering.
