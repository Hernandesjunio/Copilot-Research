# Análise: distribuição central do corpus + cache local com MCP STDIO (modelo híbrido)

- **Data:** 2026-04-09
- **Objetivo:** detalhar uma arquitetura que mantenha o **corpus centralizado** (governança, rollout, auditoria) mas preserve **desempenho local** (MCP via `stdio`) ao executar busca/retrieval no próprio desktop.
- **Contexto:** extensão do raciocínio do documento [`2026-04-09-analise-tecnica-mcp-copilot.md`](2026-04-09-analise-tecnica-mcp-copilot.md), cobrindo uma implementação **sem ambiguidades** para o “híbrido” (distribuição central + execução local).

---

## 1. Problema que esta arquitetura resolve

Queremos simultaneamente:

- **Fonte da verdade central** para instruções organizacionais (sem replicar `.github/copilot-instructions.md` volumoso em dezenas/centenas de repositórios).
- **Retrieval rápido** durante o fluxo de coding (múltiplas chamadas e composição de contexto sem latência de rede em cada turno).
- **Rollout controlado** (stable/beta), com versionamento e rollback.
- **Baixa complexidade operacional no cliente**: o desenvolvedor não deve “gerenciar” manualmente versões todo dia.

O ponto central é separar dois planos:

- **Plano frio (distribuição/update)**: pode ser central e remoto (HTTP).
- **Plano quente (consulta/retrieval)**: deve ser local (stdio) por performance e previsibilidade.

---

## 2. Visão geral da arquitetura

### 2.1 Componentes

1. **Servidor de Distribuição do Corpus (central, remoto)**
   - Pode ser HTTP (API simples) ou até um artefato em release/registry (ex.: GitHub Releases, pacote em storage).
   - Responsável por: **manifesto de versões**, **download de pacote**, política de **canais** (stable/beta) e opcionalmente autorização.
   - Não participa do retrieval de cada pergunta do Copilot (não é o “MCP HTTP do dia-a-dia”).

2. **MCP Local (stdio) — “motor de retrieval”**
   - Roda no desktop (servidor MCP atual `corporate-instructions`).
   - Aponta `INSTRUCTIONS_ROOT` para um **cache local** com o corpus.
   - Expõe tools de busca/leitura (`search_instructions`, `get_instructions_batch`; historicamente `get_instruction`).

3. **Cache Local de Corpus (no desktop)**
   - Diretório com versão atual (`current`) e staging (`staging`), com metadados de versão/hashes.
   - Permite swap atômico e rollback.

4. **Thin per-repo (nativo)**
   - Um `copilot-instructions.md` “fino” que:
     - define regras sempre-ativas do repo;
     - direciona **quando** consultar MCP (pseudo-hook);
     - **não** carrega o corpus.

### 2.2 Fluxos (alto nível)

- **Update (plano frio)**: Thin → MCP local chama tool de update → baixa pacote do servidor central → valida → aplica swap → reinicia MCP local se necessário.
- **Retrieval (plano quente)**: Thin → MCP local consulta cache local (sem rede) → retorna conteúdos para o Copilot.

---

## 3. Estrutura do cache local (padrão recomendado)

### 3.1 Localização do cache

Definir uma variável (ou config) com caminho absoluto:

- `CORPUS_CACHE_DIR`

Exemplos:

- Windows: `C:\Users\<user>\AppData\Local\CorporateInstructions\cache`
- macOS/Linux: `~/.cache/corporate-instructions`

### 3.2 Estrutura de diretórios

```text
CORPUS_CACHE_DIR/
├── manifest.json                 # último manifesto baixado (opcional, cache)
├── state.json                    # estado local (canal, versão atual, histórico)
├── current/
│   ├── corpus/                   # diretório com os .md (frontmatter YAML)
│   ├── index.json                # opcional: índice persistido local (se houver)
│   └── meta.json                 # metadados da versão aplicada (hashes, timestamps)
├── staging/
│   ├── corpus/
│   └── meta.json
└── previous/
    ├── corpus/
    └── meta.json
```

### 3.3 Estado local (contrato do `state.json`)

`state.json` deve ser pequeno e deterministicamente interpretável:

```json
{
  "channel": "stable",
  "current_version": "2026.04.09+1",
  "current_sha256": "sha256-do-pacote",
  "last_check_utc": "2026-04-09T12:34:56Z",
  "previous_version": "2026.04.02+3",
  "previous_sha256": "sha256-anterior",
  "last_error": null
}
```

Regras:

- `current_sha256` é o hash do **pacote** baixado (não do conteúdo individual).
- O cache local deve manter `previous/` para rollback rápido.

---

## 4. Contratos de distribuição (manifesto + pacote)

### 4.1 Manifesto (contrato canônico)

O manifesto descreve “qual pacote baixar” por canal e (opcionalmente) por tenant.

Formato recomendado: JSON (simples, fácil em qualquer runtime).

Exemplo `manifest.json`:

```json
{
  "schema_version": 1,
  "generated_at_utc": "2026-04-09T12:00:00Z",
  "channels": {
    "stable": {
      "version": "2026.04.09+1",
      "package": {
        "url": "https://dist.example.org/corpus/stable/corpus-2026.04.09+1.zip",
        "sha256": "BASE16_SHA256",
        "size_bytes": 1234567
      }
    },
    "beta": {
      "version": "2026.04.10+0",
      "package": {
        "url": "https://dist.example.org/corpus/beta/corpus-2026.04.10+0.zip",
        "sha256": "BASE16_SHA256",
        "size_bytes": 1337000
      }
    }
  }
}
```

Regras:

- `schema_version` permite evolução compatível.
- `channels.<name>.version` é string livre, mas deve ser estável e comparável (recomendado: `YYYY.MM.DD+N`).
- `sha256` deve ser do **arquivo do pacote**.

### 4.2 Pacote do corpus (conteúdo)

O pacote é um `.zip` contendo uma pasta `corpus/` com arquivos `.md` com frontmatter YAML (conforme EPIC-01).

Estrutura dentro do `.zip`:

```text
corpus/
├── microservice-architecture-layering.md
├── security-baseline-secrets.md
└── ...
meta.json
```

`meta.json` (dentro do pacote) deve conter pelo menos:

```json
{
  "version": "2026.04.09+1",
  "channel": "stable",
  "generated_at_utc": "2026-04-09T12:00:00Z",
  "package_sha256": "BASE16_SHA256",
  "document_count": 123
}
```

### 4.3 Validações obrigatórias no cliente (antes de aplicar)

Antes do swap `staging → current`, validar:

- **Integridade do pacote**: sha256 do arquivo baixado confere com o manifesto.
- **Estrutura**: existe diretório `corpus/` e `meta.json`.
- **Documentos**: cada `.md` tem frontmatter com `id` e `title` (o restante pode ser recomendado conforme EPIC-01).
- **Tamanho**: opcional, mas recomendado impor limites por documento (ex.: evitar doc de 10 MB).

Falha em validação → não aplica, mantém `current` intacto.

---

## 5. Segurança, tenant e isolamento

### 5.1 O que este modelo reduz

Ao tirar o retrieval do caminho quente:

- reduz superfície de “mistura de contexto” por chamadas de rede;
- reduz risco de vazamento acidental por queries remotas;
- reduz necessidade de multi-tenancy sofisticado para cada interação.

### 5.2 Ainda é necessário controlar quem baixa o quê

O servidor de distribuição precisa impedir que um time baixe o pacote de outro, se houver segmentação.

Opções:

- **URL por tenant** (mais simples).
- **Header de autorização** (Bearer token) com escopo por tenant.
- **Assinatura** do pacote (e validação no cliente) como camada adicional.

### 5.3 Regra de ouro

O thin **não** deve ser a barreira de isolamento (“use o pacote do time X”). O isolamento deve estar no **serviço de distribuição** (autorização/escopo).

---

## 6. UX do desenvolvedor (update sem atrito)

### 6.1 Modos de update

Recomendação para MVP: **assistido via chat** (low-friction e previsível).

- **Manual**: dev roda “atualizar corpus” sob demanda.
- **Assistido**: MCP detecta update, pergunta e aplica com confirmação.
- **Automático**: aplica em startup (mais complexo; risco de mudar contexto durante a sessão).

### 6.2 Política sugerida (assistido)

- Só oferecer update quando:
  - uma nova versão estiver disponível; e
  - nenhuma aplicação parcial estiver em curso (sem staging pendente).
- Ao aplicar:
  - baixar → validar → swap → (se necessário) reiniciar MCP local.

---

## 7. Proposta de tools no MCP local (contratos detalhados)

Estas tools existem **no MCP local (stdio)**. Elas chamam o servidor de distribuição para update, mas não para retrieval.

### 7.1 `knowledge_status()`

**Objetivo:** retornar o estado do cache local e versão aplicada.

**Retorno (JSON):**

```json
{
  "channel": "stable",
  "current_version": "2026.04.09+1",
  "current_sha256": "BASE16_SHA256",
  "cache_dir": "C:\\Users\\...\\CorporateInstructions\\cache",
  "has_staging": false,
  "last_check_utc": "2026-04-09T12:34:56Z"
}
```

### 7.2 `knowledge_check_update(channel?)`

**Objetivo:** consultar manifesto remoto e dizer se há update.

**Parâmetros:**

- `channel` (opcional): default = canal atual do `state.json`.

**Retorno (JSON):**

```json
{
  "channel": "stable",
  "current_version": "2026.04.09+1",
  "available_version": "2026.04.10+0",
  "update_available": true,
  "package": {
    "url": "https://dist.example.org/...zip",
    "sha256": "BASE16_SHA256",
    "size_bytes": 1337000
  }
}
```

**Erros:**

- `NETWORK_ERROR` (timeout/DNS)
- `AUTH_ERROR` (401/403)
- `INVALID_MANIFEST` (JSON inválido ou schema_version desconhecido)

### 7.3 `knowledge_download_update(channel?)`

**Objetivo:** baixar o pacote para `staging/` (sem aplicar).

**Regras:**

- Se já houver staging com a mesma versão+hash, pode retornar “já baixado”.
- Deve salvar `staging/meta.json` e atualizar `state.json.last_error` em falha.

**Retorno (JSON):**

```json
{
  "downloaded": true,
  "channel": "stable",
  "version": "2026.04.10+0",
  "sha256": "BASE16_SHA256",
  "staging_path": "...\\staging",
  "size_bytes": 1337000
}
```

### 7.4 `knowledge_validate_staging()`

**Objetivo:** validar `staging/` sem aplicar.

**Retorno (JSON):**

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    { "code": "MISSING_TAGS", "message": "Alguns docs não possuem tags (recomendado, não obrigatório)." }
  ]
}
```

### 7.5 `knowledge_apply_update()`

**Objetivo:** swap atômico `current → previous` e `staging → current`.

**Regras:**

- Se `knowledge_validate_staging` falhar: não aplica.
- Swap deve ser atômico no nível de diretório (mover/renomear).
- Após aplicar, o MCP pode exigir restart para reindexar (depende do servidor stdio).

**Retorno (JSON):**

```json
{
  "applied": true,
  "channel": "stable",
  "current_version": "2026.04.10+0",
  "previous_version": "2026.04.09+1",
  "restart_required": true
}
```

### 7.6 `knowledge_rollback()`

**Objetivo:** retornar de `current` para `previous`.

**Retorno (JSON):**

```json
{
  "rolled_back": true,
  "current_version": "2026.04.09+1",
  "previous_version": "2026.04.10+0",
  "restart_required": true
}
```

---

## 8. Integração com as tools atuais de retrieval

O servidor MCP local existente (`corporate-instructions`) continua expondo:

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch` *(histórico: `get_instruction`)*

Regra de implementação:

- `INSTRUCTIONS_ROOT` deve apontar para `CORPUS_CACHE_DIR/current/corpus`.

Atualização aplicada → reiniciar o processo MCP local para reconstruir índice (ou implementar reindexação incremental se/quando fizer sentido).

---

## 9. Como o thin por repo deve mencionar isso (sem acoplamento excessivo)

Recomendação: o thin deve:

- dizer que “padrões organizacionais” vêm do MCP;
- opcionalmente incluir uma frase de update sob demanda (“se suspeitar de drift, verifique atualização do corpus”);
- evitar amarrar o usuário a detalhes do serviço de distribuição.

Exemplo enxuto (texto a ser adaptado no thin do repo do serviço):

- “Para padrões organizacionais, consulte o MCP `corporate-instructions`.”
- “Se houver suspeita de instruções desatualizadas, verifique update do corpus e aplique antes de continuar.”

---

## 10. Trade-offs explícitos

- **Prós**
  - performance local no caminho quente;
  - governança central por distribuição;
  - rollback real (versão anterior no cache);
  - evita construir “plataforma MCP HTTP” para cada consulta.
- **Contras**
  - existe um novo componente “distribuição” (mesmo que simples);
  - necessidade de gerenciar cache local e permissões de escrita;
  - precisa de um fluxo claro de restart/reindex do MCP local após apply.

---

## 11. Esteira de deploy (CI/CD) para o ambiente corporativo

Esta arquitetura fica **realmente útil** quando há uma esteira que publica versões do corpus com rastreabilidade e canais.

### 11.1 Artefatos publicados pela esteira

A esteira deve publicar, no mínimo, dois artefatos por canal:

- **Pacote do corpus**: `corpus-<version>.zip`
- **Manifesto do canal**: `manifest.json` (ou `manifest-<channel>.json`)

Opcional (recomendado em ambientes corporativos):

- **Assinatura** do pacote (`.sig`) e/ou manifesto
- **SBOM** e metadados de build (commit SHA, pipeline run id)

### 11.2 Fonte do corpus

A esteira deve apontar para a fonte “canônica” do corpus (ex.: repositório dedicado de instructions) e empacotar apenas o que será distribuído:

- arquivos `.md` com frontmatter (EPIC-01);
- `meta.json` gerado na build com version, canal, timestamp, contagem.

### 11.3 Passos obrigatórios da pipeline (sem ambiguidades)

1. **Checkout** do repositório do corpus (branch/tag do canal).
2. **Validação estática** do corpus:
   - todos os `.md` têm frontmatter parseável;
   - `id` único por documento;
   - campos mínimos presentes (`id`, `title`);
   - (opcional) validação de `scope/priority/kind` contra enum.
3. **Build do pacote**:
   - gerar estrutura `corpus/` + `meta.json`;
   - gerar `.zip` determinístico;
   - calcular `sha256` do `.zip`.
4. **Publicação do pacote** em storage corporativo (ou release):
   - o resultado precisa ser um URL estável para download.
5. **Geração/publicação do manifesto** para o canal:
   - atualizar `channels.<canal>.version` e `package.url/sha256/size_bytes`.
6. **(Opcional) Assinar** pacote e manifesto.
7. **(Opcional) Smoke test**:
   - baixar o pacote recém-publicado;
   - rodar as mesmas validações do cliente;
   - garantir que o manifesto referencia um artefato existente.

### 11.4 Canais e estratégia de rollout

Recomendação simples:

- **`beta`**: publica a cada merge (alta cadência, validação + early adopters).
- **`stable`**: promove manualmente (ou por regra) uma versão de `beta` após validação adicional.

O manifesto é o “ponteiro” do canal — atualizar o manifesto é o que efetivamente **move** o canal para uma nova versão.

### 11.5 Integração com o cliente (MCP STDIO)

No cliente, as tools de update (seção 7) devem:

- ler o manifesto do canal;
- baixar o pacote do URL publicado pela pipeline;
- aplicar o swap local com rollback.

Isso garante que a esteira governa **distribuição**, mas o MCP local mantém **performance** no uso diário.

---

## 12. Recomendação de próxima ação (para o repositório)

1. Manter o servidor MCP local como está para retrieval (stdio).
2. Implementar (ou prototipar) o “serviço de distribuição” como API simples + zip.
3. Adicionar tools de update no MCP local (ou um “updater” acoplado ao mesmo pacote) seguindo os contratos acima.
4. Padronizar `CORPUS_CACHE_DIR` e documentar no README do servidor.

