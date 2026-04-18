# Corporate Instructions MCP (read-only)

**Mapa do repositório (agentes):** [`../AGENTS.md`](../AGENTS.md).

Servidor [Model Context Protocol](https://modelcontextprotocol.io/) em **stdio** que expõe o corpus canônico de instructions (Markdown com frontmatter) para o GitHub Copilot no Visual Studio — alinhado ao plano híbrido: poucas instructions nativas no repo + recuperação sob demanda.

## Requisitos

- Python 3.10+
- Variável de ambiente **`INSTRUCTIONS_ROOT`**: caminho absoluto ou relativo para uma pasta **existente** que contém os `.md` (por exemplo, clone do repositório `org/architecture-instructions`). Se o caminho não existir ou não for diretório, o servidor **falha ao atender tools** (fail-fast).

## Instalação

Fonte canônica de dependências: [`pyproject.toml`](pyproject.toml).

```bash
cd mcp-instructions-server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

O ficheiro [`requirements.txt`](requirements.txt) espelha apenas dependências de **runtime** para ambientes que não usam PEP 517; para desenvolvimento prefira sempre `pip install -e ".[dev]"`.

## Executar (stdio)

```bash
export INSTRUCTIONS_ROOT=/caminho/para/corpus-instructions
corporate-instructions-mcp
```

Windows (cmd):

```bat
set INSTRUCTIONS_ROOT=C:\caminho\para\corpus-instructions
corporate-instructions-mcp
```

Também: `python -m corporate_instructions_mcp` com o mesmo `INSTRUCTIONS_ROOT`.

**Logs:** mensagens operacionais (rebuild do índice, ficheiros ignorados por limite, etc.) vão para **stderr**, para não misturar com o JSON-RPC em **stdout**.

**Telemetria estruturada (opcional):** defina `CORPORATE_INSTRUCTIONS_TELEMETRY` como `minimal` ou `full` para emitir eventos **NDJSON** (uma linha JSON por evento) em stderr — útil para experimentos e análise posterior. `off` (omissão) desliga a telemetria. Em `minimal`, queries de pesquisa são registadas apenas como `query_sha256`; em `full` inclui `query_preview` (uso recomendado só em laboratório).

**Como ver, gravar em ficheiro e filtrar NDJSON:** [`docs/HOW-TO-TELEMETRY-LOGS.md`](docs/HOW-TO-TELEMETRY-LOGS.md). Telemetria nos testes: [`docs/TESTS.md`](docs/TESTS.md).

## Registrar no Visual Studio (MCP)

Adicione o servidor na configuração de MCP do VS (JSON), apontando o comando para o interpretador que tem o pacote instalado (`pip install -e ".[dev]"` a partir desta pasta).

Pode instalar em **venv** ou **globalmente** (`pip install -e .` no interpretador do sistema); em ambos os casos o VS deve usar o **`python.exe` exacto** onde correu o `pip`. No Windows, `where python` ou `py -0p` lista candidatos; copie o caminho completo para `command`.

**Recomendado:** use **`command` com caminho absoluto** (por exemplo `C:\\Users\\…\\AppData\\Local\\Programs\\Python\\Python313\\python.exe`, ou o `python.exe` do venv) e **`INSTRUCTIONS_ROOT` absoluto**. Assim o Visual Studio não depende do `PATH` da sessão nem da pasta de trabalho do processo — evita correr um `python` diferente do terminal ou uma versão antiga do pacote em `site-packages`.

```json
{
  "inputs": [],
  "servers": {
    "corporate-instructions": {
      "type": "stdio",
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "corporate_instructions_mcp"],
      "env": {
        "INSTRUCTIONS_ROOT": "C:\\path\\to\\corpus-instructions"
      }
    }
  }
}
```

Alternativa equivalente: `"command": "C:\\path\\to\\venv\\Scripts\\corporate-instructions-mcp.exe"` com `"args": []` (o entrypoint já chama `main()`).

**Desenvolvimento no monorepo (opcional):** se quiser executar o código em `mcp-instructions-server` sem reinstalar após cada `git pull`, defina `PYTHONPATH` para a pasta que contém o pacote (a pasta `mcp-instructions-server`, não `corporate_instructions_mcp`):

```json
"env": {
  "INSTRUCTIONS_ROOT": "C:\\path\\to\\corpus-instructions",
  "PYTHONPATH": "C:\\path\\to\\Copilot-Research\\mcp-instructions-server"
}
```

**Evitar:** `"command": "python"` sem caminho absoluto. O VS resolve outro executável do que o esperado com facilidade; o catálogo de tools (`list_instructions_index`, `search_instructions`, `get_instructions_batch`) vem do módulo realmente carregado.

### Visual Studio: tools no catálogo vs chat

1. Confirme o interpretador: `pip show corporate-instructions-mcp` e `python -c "import corporate_instructions_mcp.server as s; assert hasattr(s, 'get_instructions_batch')"`.
2. Valide o protocolo: na pasta `mcp-instructions-server`, `python -m pytest tests/integration_mcp_stdio_test.py::test_mcp_stdio_list_search_get_instruction` — verifica que `tools/list` expõe as três tools.
3. **Evidência JSON para suporte:** com o mesmo `INSTRUCTIONS_ROOT` que usa no VS, execute `python scripts/print_mcp_tools_list.py` (a partir de `mcp-instructions-server/`). A saída deve listar `get_instructions_batch`, `list_instructions_index` e `search_instructions` com `inputSchema`. Anexe ao reporte de bug.
4. Se o `pytest` e o script mostram as **três** tools mas o **chat** do Visual Studio continua a negar (incluindo após `command` absoluto ao `python.exe` onde correu o `pip`): confira no painel de MCP do VS se **cada tool está activada** (por predefinição podem vir desligadas após mudar o nome do servidor ou das tools).
5. Se após o passo anterior o chat ainda negar: o servidor pode estar conforme o MCP e o sintoma ser **do host Copilot no VS** (modo de chat vs agente, sessão antiga, ou regressão). Tente conversa nova; modo **agente** se estiver só em perguntas rápidas; confirmar que o servidor MCP está ligado para essa sessão; actualizar Visual Studio e GitHub Copilot. Para isolar, configure o **mesmo** comando/`env` no VS Code (`.vscode/mcp.json` ou definições MCP) — se lá as tools aparecem ao modelo, o problema é específico do VS.
6. Relatos semelhantes no ecossistema (VS Code): [Chat does not see all MCP tools](https://github.com/microsoft/vscode/issues/293598) — útil como referência ao abrir ticket na Microsoft / Developer Community para o Visual Studio.

## Tools

| Tool | Função |
|------|--------|
| `list_instructions_index` | Metadados de todos os `.md` (id, path, tags, hash) + agrupamento `by_tag` para navegação por tema. |
| `search_instructions` | Busca por palavras-chave (com expansão por sinónimos), `tags` opcional (lista separada por vírgulas), `max_results` 1–20 (default 10), e `related_ids` por interseção de tags. |
| `get_instructions_batch` | Conteúdo completo de 1 ou mais instructions por `ids` separados por vírgula; `max_chars_per_instruction` para truncagem individual e teto de payload total da resposta. Cada item inclui `frontmatter` (YAML parseado completo, com chaves extra além dos metadados listados no índice). |

**Reindexação:** o índice é reconstruído quando `INSTRUCTIONS_ROOT` muda entre chamadas. Reinicie o processo após alterações grandes no corpus se quiser libertar memória ou garantir estado limpo.

## Limites e segurança (resumo)

- **Tamanho máximo por ficheiro** indexado: 5 MiB (ficheiros maiores são ignorados com aviso em log).
- **Frontmatter YAML**: secção entre os primeiros `---` limitada a 64 KiB; valores YAML que não sejam objeto mapeado são tratados como metadados vazios.
- **Symlinks:** ficheiros cuja resolução saia de `INSTRUCTIONS_ROOT` são ignorados.
- **Modelo de ameaça e reporte de vulnerabilidades:** ver [SECURITY.md](../SECURITY.md) na raiz do repositório.

## Versionamento e compatibilidade

| Artefacto | Política |
|-----------|----------|
| Pacote `corporate-instructions-mcp` | [Semantic Versioning](https://semver.org/spec/v2.0.0.html); versão em [`pyproject.toml`](pyproject.toml). |
| Histórico de alterações | [`CHANGELOG.md`](CHANGELOG.md). |
| Python | Testado em CI em 3.10, 3.11 e 3.12. |
| Protocolo MCP | Dependente da biblioteca `mcp` declarada em `pyproject.toml`; sem matriz formal de cada release do upstream — actualize `mcp` com testes locais. |

## Runbook operacional (curto)

| Sintoma | Verificar |
|---------|-----------|
| Chat não reconhece `get_instructions_batch` mas as definições listam tools | Secção **Visual Studio: tools no catálogo vs chat** acima; `command` absoluto; `pytest` de integração. |
| Erro ao listar/buscar: `INSTRUCTIONS_ROOT is not a directory` | Caminho correcto, permissões de leitura, pasta montada em CI/CD. |
| Índice vazio sem erro | Nenhum `.md` válido sob a raiz, ou todos ignorados (tamanho / symlink). Ver **stderr**. |
| Conteúdo desactualizado | Reiniciar o processo MCP no IDE; o índice reflecte o disco no rebuild. |
| `get_instructions_batch` devolve `missing_ids` | Corrigir IDs com `list_instructions_index` ou `search_instructions` e repetir a chamada batch. |

## Transporte HTTP (roadmap)

O modo suportado hoje é **stdio** (IDE). Para alinhamento com gateways corporativos (TLS, auth, health checks), ver [docs/ROADMAP-TRANSPORT-HTTP.md](docs/ROADMAP-TRANSPORT-HTTP.md).

## Formato dos ficheiros

Ver [EPIC-01-inventory-governance.md](../planning/bmad/epicos/EPIC-01-inventory-governance.md) para o frontmatter esperado (`id`, `title`, `tags`, `scope`, `priority`, `kind`).

## Corpus de exemplo

Neste repositório Copilot, use:

`INSTRUCTIONS_ROOT` = `...\Copilot-Research\fixtures\instructions`

para validar as tools localmente (`pytest` em `mcp-instructions-server/`).

## Testes

Descrição de cada ficheiro e teste, corpus assumido e limites da cobertura: **[docs/TESTS.md](docs/TESTS.md)**.

## Pesquisa e análises

- Metodologia e experimentos: [`../research/README.md`](../research/README.md)
- Índice das análises técnicas datadas (MCP, corpus, estratégias): [`../research/analises/README.md`](../research/analises/README.md)

## Contribuição e políticas do repositório

- [CONTRIBUTING.md](../CONTRIBUTING.md) — ambiente de desenvolvimento, gates de qualidade.
- [SECURITY.md](../SECURITY.md) — reporte responsável.
