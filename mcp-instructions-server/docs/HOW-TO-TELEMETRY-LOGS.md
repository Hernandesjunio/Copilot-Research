# Como ver, gravar e filtrar logs de telemetria (NDJSON)

O servidor escreve **telemetria estruturada** em **stderr** (uma linha JSON por evento — NDJSON). O protocolo MCP continua apenas em **stdout**; não misture os fluxos ao capturar.

Por omissão a telemetria está **desligada** (`CORPORATE_INSTRUCTIONS_TELEMETRY` ausente ou `off`).

## 1. Activar a telemetria

Defina uma destas variáveis de ambiente no processo que arranca o MCP (perfil JSON do VS/Cursor, terminal, serviço, etc.):

| Valor | Efeito |
|--------|--------|
| `minimal` | Eventos NDJSON com queries de `search_instructions` resumidas (`query_sha256`; sem texto literal da query). |
| `full` | Inclui campos extra (ex.: `query_preview`, tokens). **Recomendado só em laboratório** — não use em dados sensíveis sem rever o corpus. |
| `off` / omitir | Sem NDJSON de telemetria (comportamento por omissão). |

Opcional: `CORPORATE_INSTRUCTIONS_SESSION_ID` — fixa um identificador de sessão nos eventos (útil para alinhar logs a um experimento).

Exemplo em JSON de configuração MCP:

```json
"env": {
  "INSTRUCTIONS_ROOT": "C:\\path\\to\\corpus-instructions",
  "CORPORATE_INSTRUCTIONS_TELEMETRY": "minimal",
  "CORPORATE_INSTRUCTIONS_SESSION_ID": "exp-2026-04-18-run-01"
}
```

## 2. O que aparece no stderr

- Linhas **NDJSON** (objectos JSON que começam tipicamente com `{` e ocupam uma linha).
- Mensagens de **logging** operacional do Python (nível INFO), por exemplo rebuild do índice — texto livre, não é JSON.

Para análise automática, filtre ou trate só as linhas JSON (secção 5).

Tipos de eventos incluem entre outros: `server_start`, `index_rebuilt`, `*.completed` (por tool, ex.: `search_instructions.completed`). O campo `schema_version` indica a versão do registo.

## 3. Ver os logs no IDE (Cursor / VS Code)

1. Abra o painel de **Output** (View → Output).
2. No selector, escolha o canal do **MCP** ou do processo onde o servidor corre (o nome depende da extensão / integração).

**Nota:** Nem todas as configurações mostram **stderr** do processo MCP no painel; se não vir NDJSON, use gravação para ficheiro (secção 4).

## 4. Gravar stderr num ficheiro (sessão)

Redireccione **apenas o stderr** do processo (por exemplo `2>>` ou equivalente). Uma extensão comum é `.jsonl`.

### PowerShell (Windows)

```powershell
$env:CORPORATE_INSTRUCTIONS_TELEMETRY = "minimal"
$env:INSTRUCTIONS_ROOT = "C:\path\to\corpus-instructions"
python -m corporate_instructions_mcp 2>> "C:\temp\mcp-telemetry.jsonl"
```

(Em produção o IDE lança o comando; o redireccionamento manual aplica-se quando corre o servidor **no terminal** ou com um *wrapper*.)

### Bash (Git Bash / WSL / Linux / macOS)

```bash
export CORPORATE_INSTRUCTIONS_TELEMETRY=minimal
export INSTRUCTIONS_ROOT=/path/to/corpus-instructions
python -m corporate_instructions_mcp 2>> /tmp/mcp-telemetry.jsonl
```

Depois abra o `.jsonl` no editor ou processe linha a linha com `jq`, Python, etc.

## 5. Filtrar só as linhas JSON (NDJSON)

O stderr pode misturar linhas de log em texto. Mantenha só linhas que parecem objectos JSON:

### PowerShell

```powershell
Get-Content C:\temp\mcp-telemetry.jsonl | Where-Object { $_ -match '^\s*\{' }
```

### Bash

```bash
grep '^{' /tmp/mcp-telemetry.jsonl
```

### Python (exemplo minimal)

```python
import json
from pathlib import Path

for line in Path("mcp-telemetry.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("{"):
        print(json.loads(line).get("event"))
```

## 6. Segurança e privacidade

- Com `full`, o conteúdo da query pode aparecer em claro nos eventos.
- Preferir `minimal` fora de ambientes de laboratório.
- Não grave stderr de sessões reais com dados sensíveis sem política de retenção e acesso.

## Ver também

- [`README.md`](../README.md) — instalação, `INSTRUCTIONS_ROOT`, configuração MCP no Visual Studio.
- [`TESTS.md`](TESTS.md) — telemetria nos testes automatizados.
