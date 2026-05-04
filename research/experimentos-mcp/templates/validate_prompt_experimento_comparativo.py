#!/usr/bin/env python3
"""
Valida o template `prompt-experimento-comparativo.md` contra o ficheiro base
`.../Prompts/prompt-sem-mcp-e-instructions.md`, após substituir os placeholders
pelos fragmentos desse mesmo ficheiro (condição baseline).

Uso (a partir da raiz do repositório):
  python research/experimentos-mcp/templates/validate_prompt_experimento_comparativo.py

Código de saída: 0 se OK, 1 se diferenças.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / (
    "research/experimentos-mcp/2026-04-16-analise-comparativa-"
    "instructions-mcp-vertical-slice/Prompts/prompt-sem-mcp-e-instructions.md"
)
TEMPLATE = Path(__file__).with_name("prompt-experimento-comparativo.md")


def canon(s: str) -> str:
    return s.replace("\r\n", "\n").rstrip("\n") + "\n"


def main() -> int:
    text_b = BASE.read_text(encoding="utf-8")
    lines_b = text_b.splitlines(keepends=True)
    ctx = "".join(lines_b[2:15])
    tarefa = "".join(lines_b[18:32])
    rule1 = lines_b[35].rstrip("\r\n")
    subs = {
        "{{CONTEXTO_DO_EXPERIMENTO}}": ctx,
        "{{TAREFA_CORPO}}": tarefa,
        "{{REGRA_1_EXECUCAO}}": rule1,
        "{{SUFIXO_ARQUIVO}}": "baseline",
        "{{SUFIXO_ARQUIVO_LABEL}}": "baseline",
        "{{PARTE1_ITEM_1_TITULO}}": lines_b[62].replace("#### ", "", 1).strip(),
        "{{PARTE1_ITEM_1_CORPO}}": "".join(lines_b[63:67]),
        "{{ANCORAGEM_DECISIONS_JSON}}": "(codigo_repo | inferencia)",
    }
    tpl_text = TEMPLATE.read_text(encoding="utf-8")
    if "---\n\n## Referência" not in tpl_text:
        print("ERRO: separador '--- / ## Referência' não encontrado no template.", file=sys.stderr)
        return 1
    prompt_part = tpl_text.split("---\n\n## Referência", 1)[0].rstrip() + "\n"
    out = prompt_part
    for k, v in subs.items():
        out = out.replace(k, v)
    if canon(out) != canon(text_b):
        import difflib

        a = canon(text_b).splitlines()
        b = canon(out).splitlines()
        for line in difflib.unified_diff(a, b, fromfile="baseline", tofile="instantiated", lineterm=""):
            print(line)
        return 1
    print("OK: prompt instantiado (baseline) coincide com o ficheiro base (newline EOF normalizado).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
