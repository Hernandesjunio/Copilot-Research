# Corporate Instructions MCP (read-only)

Servidor [Model Context Protocol](https://modelcontextprotocol.io/) em **stdio** que expõe o corpus canônico de instructions (Markdown com frontmatter) para o GitHub Copilot no Visual Studio — alinhado ao plano híbrido: poucas instructions nativas no repo + recuperação sob demanda.

## Requisitos

- Python 3.10+
- Variável de ambiente **`INSTRUCTIONS_ROOT`**: caminho absoluto ou relativo para a pasta raiz que contém os `.md` (por exemplo, clone do repositório `org/architecture-instructions`).

## Instalação

```bash
cd mcp-instructions-server
pip install -e .
```

Ou apenas dependências:

```bash
pip install -r requirements.txt
```

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
| `list_instructions_index` | Metadados de todos os `.md` (id, path, tags, hash). |
| `search_instructions` | Busca por palavras-chave; `tags` opcional (lista separada por vírgulas); `max_results` 1–10 (default 5). |
| `get_instruction` | Conteúdo completo por `id` ou `path` relativo; `max_chars` para truncar. |

**Reindexação:** o índice é reconstruído quando o processo inicia ou quando `INSTRUCTIONS_ROOT` muda. Reinicie o servidor após atualizar arquivos no corpus.

## Formato dos arquivos

Ver [EPIC-01-inventory-governance.md](../planning/bmad/EPIC-01-inventory-governance.md) para o frontmatter esperado (`id`, `title`, `tags`, `scope`, `priority`, `kind`).

## Corpus de exemplo

Neste repositório Copilot, use:

`INSTRUCTIONS_ROOT` = `...\Copilot\fixtures\instructions`

para validar as três tools localmente.
