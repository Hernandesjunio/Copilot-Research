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

## Registrar no Visual Studio (MCP)

Adicione o servidor na configuração de MCP do VS (JSON), apontando o comando para o interpretador e módulo instalados, por exemplo:

```json
{
  "inputs": [],
  "servers": {
    "corporate-instructions": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "corporate_instructions_mcp"],
      "env": {
        "INSTRUCTIONS_ROOT": "endereço das instructions"
      }
    }
  }
}

```

Ajuste `command` para o Python do venv se necessário: `"command": "C:\\path\\to\\venv\\Scripts\\corporate-instructions-mcp.exe"`.

## Tools

| Tool | Função |
|------|--------|
| `list_instructions_index` | Metadados de todos os `.md` (id, path, tags, hash) + agrupamento `by_tag` para navegação por tema. |
| `search_instructions` | Busca por palavras-chave (com expansão por sinónimos), `tags` opcional (lista separada por vírgulas), `max_results` 1–20 (default 10), e `related_ids` por interseção de tags. |
| `get_instructions_batch` | Conteúdo completo de 1 ou mais instructions por `ids` separados por vírgula; `max_chars_per_instruction` para truncagem individual e teto de payload total da resposta. |

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
