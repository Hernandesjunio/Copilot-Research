"""EPIC-10 tests — Corpus Query Expansion Map (generated from EPIC markdown sections)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURES_ROOT = Path(__file__).parent.parent.parent / "fixtures" / "instructions"
MAP_DIR = FIXTURES_ROOT / "metadata" / "corpus-query-expansion-map"


@pytest.fixture(autouse=True)
def _epic10_instructions_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """EPIC-10 server integration tests require the fixture corpus as INSTRUCTIONS_ROOT."""
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(FIXTURES_ROOT))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None


# === ARQUIVO: mcp-instructions-server/tests/test_epic10_corpus_query_expansion_map.py ===
# Seção: S-01 — Schema e tipos

def test_FAIL_S01_module_expansion_importable() -> None:
    """Módulo expansion.py deve existir e ser importável.

    Input:  import do módulo corporate_instructions_mcp.expansion
    Output: nenhuma exceção levantada
    RED:    falha com ModuleNotFoundError
    GREEN:  importa sem erro
    """
    from corporate_instructions_mcp import expansion  # noqa: F401


def test_FAIL_S01_weight_constants_values() -> None:
    """Constantes de peso devem ter os valores exatos definidos na ADR-002.

    Input:
      import de ALIAS_WEIGHT, STRONG_WEIGHT, WEAK_WEIGHT de expansion

    Output (esperado após GREEN):
      ALIAS_WEIGHT  == 0.9   (alias: quase equivalente ao canonical)
      STRONG_WEIGHT == 0.7   (strong_terms: forte sinal semântico)
      WEAK_WEIGHT   == 0.3   (weak_terms: sinal fraco, contexto-dependente)

    RED:  ModuleNotFoundError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import ALIAS_WEIGHT, STRONG_WEIGHT, WEAK_WEIGHT
    assert ALIAS_WEIGHT == 0.9, f"ALIAS_WEIGHT esperado 0.9, obtido {ALIAS_WEIGHT}"
    assert STRONG_WEIGHT == 0.7, f"STRONG_WEIGHT esperado 0.7, obtido {STRONG_WEIGHT}"
    assert WEAK_WEIGHT == 0.3, f"WEAK_WEIGHT esperado 0.3, obtido {WEAK_WEIGHT}"


def test_FAIL_S01_parse_domain_file_valid_full_entry() -> None:
    """parse_domain_file aceita YAML válido com todos os campos preenchidos.

    Input:
      raw = {
          "domain":   "messaging",
          "version":  "1",
          "entries":  [
              {
                  "canonical":    "mensageria",
                  "aliases":      ["messaging"],
                  "strong_terms": ["rabbitmq", "publish", "consume"],
                  "weak_terms":   ["outbox"],
                  "contexts":     []
              }
          ]
      }
      source = "messaging.yaml"

    Output esperado:
      result                           is not None
      result.domain                    == "messaging"
      result.version                   == "1"
      result.source_file               == "messaging.yaml"
      len(result.entries)              == 1
      result.entries[0].canonical      == "mensageria"
      result.entries[0].aliases        == ["messaging"]
      result.entries[0].strong_terms   == ["rabbitmq", "publish", "consume"]
      result.entries[0].weak_terms     == ["outbox"]
      result.entries[0].contexts       == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "aliases": ["messaging"],
                "strong_terms": ["rabbitmq", "publish", "consume"],
                "weak_terms": ["outbox"],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    assert result.domain == "messaging"
    assert result.version == "1"
    assert result.source_file == "messaging.yaml"
    assert len(result.entries) == 1

    entry = result.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["messaging"]
    assert entry.strong_terms == ["rabbitmq", "publish", "consume"]
    assert entry.weak_terms == ["outbox"]
    assert entry.contexts == []


def test_FAIL_S01_parse_domain_file_normalizes_tokens() -> None:
    """parse_domain_file normaliza todos os tokens: lowercase, sem acento, underscore→hífen.

    Input:
      canonical com maiúscula e acento: "Mensageria"
      alias com maiúscula:             "RabbitMQ"
      strong_term com underscore:      "publish_subscribe"
      weak_term com acento:            "publicação"

    Output esperado:
      entry.canonical     == "mensageria"          (lowercase + sem acento)
      entry.aliases       == ["rabbitmq"]           (lowercase)
      entry.strong_terms  == ["publish-subscribe"]  (underscore → hífen via _normalize_token)
      entry.weak_terms    == ["publicacao"]          (sem acento)

    Nota: _normalize_token() de indexing.py realiza NFKD + remoção de combining chars +
          lowercase + strip. O underscore é convertido em hífen por esse normalizador.

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "Mensageria",
                "aliases": ["RabbitMQ"],
                "strong_terms": ["publish_subscribe"],
                "weak_terms": ["publicação"],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    entry = result.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["rabbitmq"]
    assert entry.strong_terms == ["publish-subscribe"]
    assert entry.weak_terms == ["publicacao"]


def test_FAIL_S01_parse_domain_file_missing_domain_returns_none() -> None:
    """parse_domain_file retorna None quando campo 'domain' está ausente.

    Input:
      raw = {
          "version": "1",
          "entries": [{"canonical": "mensageria", "aliases": [], "strong_terms": [],
                        "weak_terms": [], "contexts": []}]
      }
      source = "bad.yaml"

    Output esperado:
      result is None

    Justificativa: sem 'domain', não há como registrar a origem semântica da entrada;
    descartar é mais seguro do que aceitar.

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_missing_entries_returns_none() -> None:
    """parse_domain_file retorna None quando campo 'entries' está ausente.

    Input:
      raw = {"domain": "messaging", "version": "1"}
      source = "bad.yaml"

    Output esperado:
      result is None

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {"domain": "messaging", "version": "1"}
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_empty_domain_string_returns_none() -> None:
    """parse_domain_file retorna None quando 'domain' é string vazia.

    Input:
      raw = {"domain": "", "version": "1", "entries": []}
      source = "bad.yaml"

    Output esperado:
      result is None

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {"domain": "", "version": "1", "entries": []}
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_entry_without_canonical_is_skipped() -> None:
    """parse_domain_file ignora entradas sem 'canonical', mantém as válidas.

    Input:
      entries com 2 entradas:
        - entrada 1: sem campo 'canonical' (apenas aliases, strong_terms, etc.)
        - entrada 2: canonical='cache', aliases=['caching'], strong_terms=['ttl'],
                     weak_terms=[], contexts=[]

    Output esperado:
      result is not None
      len(result.entries) == 1          (entrada 1 foi ignorada)
      result.entries[0].canonical == "cache"
      result.entries[0].aliases   == ["caching"]
      result.entries[0].strong_terms == ["ttl"]
      result.entries[0].weak_terms   == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "version": "1",
        "entries": [
            {
                # sem 'canonical'
                "aliases": ["caching"],
                "strong_terms": ["imemorycache"],
                "weak_terms": [],
                "contexts": [],
            },
            {
                "canonical": "cache",
                "aliases": ["caching"],
                "strong_terms": ["ttl"],
                "weak_terms": [],
                "contexts": [],
            },
        ],
    }
    result = parse_domain_file(raw, source="caching.yaml")

    assert result is not None
    assert len(result.entries) == 1
    assert result.entries[0].canonical == "cache"
    assert result.entries[0].aliases == ["caching"]
    assert result.entries[0].strong_terms == ["ttl"]
    assert result.entries[0].weak_terms == []


def test_FAIL_S01_parse_domain_file_unknown_fields_ignored() -> None:
    """parse_domain_file ignora campos desconhecidos (schema extensível).

    Input:
      raw com campo desconhecido 'future_field' no nível superior
      entrada com campo desconhecido 'extra_metadata'

    Output esperado:
      Nenhuma exceção
      result is not None
      result.entries[0].canonical == "cache"

    RED:  ModuleNotFoundError
    GREEN: nenhuma exceção + asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "version": "1",
        "future_field": "ignored at top level",
        "entries": [
            {
                "canonical": "cache",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "contexts": [],
                "extra_metadata": "ignored at entry level",
            }
        ],
    }
    result = parse_domain_file(raw, source="caching.yaml")

    assert result is not None
    assert result.entries[0].canonical == "cache"


def test_FAIL_S01_parse_domain_file_optional_fields_default_to_empty_list() -> None:
    """parse_domain_file trata aliases/strong_terms/weak_terms/contexts ausentes como [].

    Input:
      entrada com somente 'canonical', sem os demais campos opcionais

    Output esperado:
      entry.aliases      == []
      entry.strong_terms == []
      entry.weak_terms   == []
      entry.contexts     == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "minimal",
        "version": "1",
        "entries": [{"canonical": "cache"}],
    }
    result = parse_domain_file(raw, source="minimal.yaml")

    assert result is not None
    entry = result.entries[0]
    assert entry.aliases == []
    assert entry.strong_terms == []
    assert entry.weak_terms == []
    assert entry.contexts == []


def test_FAIL_S01_parse_domain_file_version_defaults_to_one() -> None:
    """parse_domain_file usa '1' como version default quando campo ausente.

    Input:
      raw sem campo 'version'

    Output esperado:
      result.version == "1"

    RED:  ModuleNotFoundError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "entries": [{"canonical": "cache"}],
    }
    result = parse_domain_file(raw, source="no-version.yaml")

    assert result is not None
    assert result.version == "1"


def test_FAIL_S01_parse_domain_file_context_rule_fields_v11() -> None:
    """parse_domain_file faz parse do campo 'contexts' em ContextRule com schema V1.1.

    Schema V1.1: activation_terms, applies_to, terms (ADR-002 §2.1).
    Nenhum campo 'path_pattern' ou 'extra_terms' (schema pré-V1.1 rejeitado).

    Input:
      entry com contexts contendo um ContextRule V1.1:
        activation_terms: ["queue", "broker"]
        applies_to:       ["**/*.cs"]
        terms:            ["servicebus", "rabbitmq"]

    Output esperado:
      entry.contexts[0].activation_terms == ["queue", "broker"]
      entry.contexts[0].applies_to       == ["**/*.cs"]
      entry.contexts[0].terms            == ["servicebus", "rabbitmq"]

    Nota: scoring contextual (aplicar terms ao resultado) está fora do escopo deste
    épico — os campos são parseados e armazenados, não usados em scoring ainda.

    RED:  ModuleNotFoundError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "applies_to": [],
                "contexts": [
                    {
                        "activation_terms": ["queue", "broker"],
                        "applies_to": ["**/*.cs"],
                        "terms": ["servicebus", "rabbitmq"],
                    }
                ],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    entry = result.entries[0]
    assert len(entry.contexts) == 1
    ctx = entry.contexts[0]
    assert ctx.activation_terms == ["queue", "broker"]
    assert ctx.applies_to == ["**/*.cs"]
    assert ctx.terms == ["servicebus", "rabbitmq"]


def test_FAIL_S01_parse_domain_file_context_rule_optional_fields_default_to_empty() -> None:
    """parse_domain_file trata activation_terms/applies_to/terms ausentes como [] em contexto.

    Input:
      contexto sem nenhum dos campos opcionais explícitos

    Output esperado:
      ctx.activation_terms == []
      ctx.applies_to       == []
      ctx.terms            == []

    Nota: contexto com terms=[] é aceito mesmo sem activation_terms/applies_to
    (contexto vazio é inofensivo; ADR-002 critério 9 só rejeita terms não vazio
    sem nenhum mecanismo de ativação).

    RED:  ModuleNotFoundError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "dns",
        "version": "1",
        "entries": [
            {
                "canonical": "ttl",
                "contexts": [{}],   # contexto sem campos — todos defaultam para []
            }
        ],
    }
    result = parse_domain_file(raw, source="dns.yaml")

    assert result is not None
    entry = result.entries[0]
    assert len(entry.contexts) == 1
    ctx = entry.contexts[0]
    assert ctx.activation_terms == []
    assert ctx.applies_to == []
    assert ctx.terms == []


def test_FAIL_S01_parse_domain_file_context_with_terms_no_activation_is_rejected() -> None:
    """parse_domain_file descarta contexto com terms mas sem activation_terms nem applies_to.

    Critério ADR-002 V1.2 nº 9: contexto com terms não vazio e sem nenhum mecanismo de
    ativação é erro de curadoria — o loader deve rejeitar esse contexto (não a entrada
    inteira) e logar warning.

    Input:
      entrada com dois contextos:
        ctx1: terms=["servicebus"], activation_terms=[], applies_to=[] → REJEITADO
        ctx2: terms=["rabbitmq"], activation_terms=["queue"]           → aceito

    Output esperado:
      result is not None                  (entrada não é descartada, só o contexto inválido)
      len(entry.contexts) == 1            (ctx1 descartado, ctx2 mantido)
      entry.contexts[0].terms == ["rabbitmq"]

    RED:  ModuleNotFoundError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "contexts": [
                    {
                        "terms": ["servicebus"],
                        # sem activation_terms nem applies_to → inválido
                    },
                    {
                        "activation_terms": ["queue"],
                        "terms": ["rabbitmq"],
                    },
                ],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    entry = result.entries[0]
    assert len(entry.contexts) == 1, (
        f"Esperado 1 contexto (ctx inválido descartado), obtido {len(entry.contexts)}"
    )
    assert entry.contexts[0].terms == ["rabbitmq"]


# === Seção: S-02 — Loader corpus-aware ===

def test_FAIL_S02_load_from_nonexistent_directory_returns_disabled() -> None:
    """load_corpus_expansion_map retorna ExpansionMap disabled quando dir não existe.

    Input:
      corpus_root = Path("/tmp/nonexistent_corpus_xyz_12345")
      (garante-se que não existe via tmp aleatório)

    Output esperado:
      result.disabled == True
      result.domains  == []

    Justificativa: corpus sem mapa de expansão → expansão desabilitada,
    não fallback silencioso (ADR-002, seção 2).

    RED:  ImportError ou AttributeError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    with tempfile.TemporaryDirectory() as tmp:
        nonexistent = Path(tmp) / "nonexistent_subdir"
        result = load_corpus_expansion_map(nonexistent)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_from_empty_map_directory_returns_disabled() -> None:
    """load_corpus_expansion_map retorna disabled quando metadata/corpus-query-expansion-map/ existe mas vazio.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/   ← diretório vazio (nenhum .yaml)

    Output esperado:
      result.disabled == True
      result.domains  == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_single_valid_file() -> None:
    """load_corpus_expansion_map carrega um arquivo YAML válido com sucesso.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            messaging.yaml    ← conteúdo abaixo

    Conteúdo de messaging.yaml:
      domain: messaging
      version: "1"
      entries:
        - canonical: mensageria
          aliases:      [messaging]
          strong_terms: [rabbitmq, publish, consume]
          weak_terms:   [outbox]
          contexts:     []

    Output esperado:
      result.disabled        == False
      len(result.domains)    == 1
      result.domains[0].domain           == "messaging"
      result.domains[0].source_file      == "messaging.yaml"
      len(result.domains[0].entries)     == 1
      result.domains[0].entries[0].canonical     == "mensageria"
      result.domains[0].entries[0].aliases       == ["messaging"]
      result.domains[0].entries[0].strong_terms  == ["rabbitmq", "publish", "consume"]
      result.domains[0].entries[0].weak_terms    == ["outbox"]

    RED:  ImportError
    GREEN: todos os asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    yaml_content = """\
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases:
      - messaging
    strong_terms:
      - rabbitmq
      - publish
      - consume
    weak_terms:
      - outbox
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "messaging.yaml").write_text(yaml_content, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 1
    domain = result.domains[0]
    assert domain.domain == "messaging"
    assert domain.source_file == "messaging.yaml"
    assert len(domain.entries) == 1
    entry = domain.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["messaging"]
    assert entry.strong_terms == ["rabbitmq", "publish", "consume"]
    assert entry.weak_terms == ["outbox"]


def test_FAIL_S02_load_multiple_valid_files() -> None:
    """load_corpus_expansion_map carrega múltiplos arquivos YAML e consolida.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            messaging.yaml    ← domain: messaging, 1 entry
            caching.yaml      ← domain: caching,   1 entry

    Output esperado:
      result.disabled        == False
      len(result.domains)    == 2
      {d.domain for d in result.domains} == {"messaging", "caching"}

    Nota: a ordem dos domínios pode variar (sorted() por filename garantirá ordem estável
    se implementado, mas o teste só verifica o conjunto).

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    messaging_yaml = """\
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases: [messaging]
    strong_terms: [rabbitmq]
    weak_terms: []
    contexts: []
"""
    caching_yaml = """\
domain: caching
version: "1"
entries:
  - canonical: cache
    aliases: [caching]
    strong_terms: [imemorycache, ttl]
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "messaging.yaml").write_text(messaging_yaml, encoding="utf-8")
        (map_dir / "caching.yaml").write_text(caching_yaml, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 2
    domains_names = {d.domain for d in result.domains}
    assert domains_names == {"messaging", "caching"}


def test_FAIL_S02_invalid_yaml_syntax_skipped_valid_loaded() -> None:
    """Arquivo com YAML inválido é ignorado; arquivos válidos são carregados.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            bad.yaml       ← YAML sintaticamente inválido
            caching.yaml   ← YAML válido

    Output esperado:
      result.disabled        == False   (ao menos um arquivo válido)
      len(result.domains)    == 1       (somente caching carregado)
      result.domains[0].domain == "caching"

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    bad_yaml = "domain: [unclosed bracket\n  invalid: yaml: :\n"
    caching_yaml = """\
domain: caching
version: "1"
entries:
  - canonical: cache
    aliases: []
    strong_terms: [ttl]
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "bad.yaml").write_text(bad_yaml, encoding="utf-8")
        (map_dir / "caching.yaml").write_text(caching_yaml, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 1
    assert result.domains[0].domain == "caching"


def test_FAIL_S02_all_files_invalid_returns_disabled() -> None:
    """Se todos os arquivos falharem no parse, retorna disabled=True.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            bad1.yaml   ← YAML inválido
            bad2.yaml   ← YAML sem campo 'domain' (parse_domain_file retorna None)

    Output esperado:
      result.disabled     == True
      result.domains      == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    bad1 = "::invalid yaml::"
    bad2 = """\
version: "1"
entries:
  - canonical: cache
    aliases: []
    strong_terms: []
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "bad1.yaml").write_text(bad1, encoding="utf-8")
        (map_dir / "bad2.yaml").write_text(bad2, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_does_not_raise_on_os_error() -> None:
    """load_corpus_expansion_map não lança exceção em caso de erro de OS/permissão.

    Estratégia: criar arquivo com conteúdo que cause erro de leitura simulado através de
    monkeypatching de yaml.safe_load para lançar OSError.

    Input:
      corpus_root existente com um arquivo .yaml válido
      yaml.safe_load mockado para lançar OSError("permission denied")

    Output esperado:
      Nenhuma exceção levantada
      result.disabled == True
      result.domains  == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from unittest.mock import patch
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    yaml_content = "domain: caching\nversion: '1'\nentries: []\n"

    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "caching.yaml").write_text(yaml_content, encoding="utf-8")

        with patch("yaml.safe_load", side_effect=OSError("permission denied")):
            result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []


# === Seção: S-03 — Lookup unidirecional ponderado ===

def _make_expansion_map_from_raw(domains_raw: list[dict], sources: list[str]):
    """Helper: cria ExpansionMap diretamente de dicts (para isolar S-03 de S-02)."""
    from corporate_instructions_mcp.expansion import parse_domain_file, ExpansionMap
    domains = []
    for raw, src in zip(domains_raw, sources):
        d = parse_domain_file(raw, source=src)
        if d is not None:
            domains.append(d)
    return ExpansionMap(domains=domains, disabled=len(domains) == 0)


def test_FAIL_S03_canonical_expands_to_typed_terms() -> None:
    """build_unidirectional_lookup mapeia canonical → [ExpansionCandidate] corretamente.

    Input:
      ExpansionMap com um domínio 'messaging' (source_file="messaging.yaml"), uma entry:
        canonical:    "mensageria"
        aliases:      ["messaging"]
        strong_terms: ["rabbitmq", "publish"]
        weak_terms:   ["outbox"]
        contexts:     []

    Output esperado (lookup["mensageria"]):
      Candidato para "messaging":  weight=0.9, relation="alias",  source_domain="messaging"
      Candidato para "rabbitmq":   weight=0.7, relation="strong", source_domain="messaging"
      Candidato para "publish":    weight=0.7, relation="strong", source_domain="messaging"
      Candidato para "outbox":     weight=0.3, relation="weak",   source_domain="messaging"

    Verificação por termo (ordem não garantida).

    RED:  ImportError ou AttributeError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "mensageria" in lookup
    by_term = {c.term: c for c in lookup["mensageria"]}

    assert "messaging" in by_term
    assert by_term["messaging"].weight == pytest.approx(0.9)
    assert by_term["messaging"].relation == "alias"
    assert by_term["messaging"].source_domain == "messaging"
    assert by_term["messaging"].source_file == "messaging.yaml"

    assert "rabbitmq" in by_term
    assert by_term["rabbitmq"].weight == pytest.approx(0.7)
    assert by_term["rabbitmq"].relation == "strong"

    assert "publish" in by_term
    assert by_term["publish"].weight == pytest.approx(0.7)
    assert by_term["publish"].relation == "strong"

    assert "outbox" in by_term
    assert by_term["outbox"].weight == pytest.approx(0.3)
    assert by_term["outbox"].relation == "weak"


def test_FAIL_S03_non_canonical_term_has_no_entry() -> None:
    """Termos expanded (não-canonical) NÃO aparecem como chave no lookup.

    Este é o comportamento central da ADR-002: lookup UNIDIRECIONAL.

    Input (mesmo do teste anterior):
      canonical:    "mensageria"
      aliases:      ["messaging"]
      strong_terms: ["rabbitmq", "publish"]
      weak_terms:   ["outbox"]

    Output esperado:
      "rabbitmq" NOT in lookup     ← só mensageria é canonical; lookup é unidirecional
      "messaging" NOT in lookup
      "publish" NOT in lookup
      "outbox" NOT in lookup

    Contraste com comportamento ATUAL (bidirecional) que seria:
      "rabbitmq" IN lookup (gerado por _build_expansion_lookup)

    RED:  ImportError ou AttributeError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "rabbitmq" not in lookup, (
        "rabbitmq é termo expandido, não canonical — NÃO deve aparecer como chave no lookup unidirecional"
    )
    assert "messaging" not in lookup
    assert "publish" not in lookup
    assert "outbox" not in lookup


def test_FAIL_S03_same_canonical_across_two_domains_merges_with_max_weight() -> None:
    """Mesmo canonical em dois domínios: expansões concatenadas, duplicata mantém maior peso.

    Input:
      Domínio 'observability':
        canonical: "observabilidade"
        strong_terms: ["opentelemetry", "health"]
        weak_terms:   ["deployment"]

      Domínio 'configuration':
        canonical: "observabilidade"   ← mesmo canonical em outro domínio
        strong_terms: ["production"]
        weak_terms:   ["health"]       ← 'health' reaparece como weak

    Output esperado para lookup["observabilidade"]:
      "opentelemetry": weight=0.7, relation="strong", source_domain="observability"
      "health":        weight=0.7, relation="strong"  ← max(0.7 strong, 0.3 weak) = 0.7
      "deployment":    weight=0.3, relation="weak",   source_domain="observability"
      "production":    weight=0.7, relation="strong", source_domain="configuration"

    RED:  ImportError ou AttributeError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "observability",
                "version": "1",
                "entries": [
                    {
                        "canonical": "observabilidade",
                        "aliases": [],
                        "strong_terms": ["opentelemetry", "health"],
                        "weak_terms": ["deployment"],
                        "contexts": [],
                    }
                ],
            },
            {
                "domain": "configuration",
                "version": "1",
                "entries": [
                    {
                        "canonical": "observabilidade",
                        "aliases": [],
                        "strong_terms": ["production"],
                        "weak_terms": ["health"],
                        "contexts": [],
                    }
                ],
            },
        ],
        ["observability.yaml", "configuration.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    by_term = {c.term: c for c in lookup["observabilidade"]}
    assert by_term["opentelemetry"].weight == pytest.approx(0.7)
    assert by_term["opentelemetry"].source_domain == "observability"
    assert by_term["health"].weight == pytest.approx(0.7)       # max(0.7, 0.3) = 0.7
    assert by_term["health"].relation == "strong"               # vencedor é o strong
    assert by_term["deployment"].weight == pytest.approx(0.3)
    assert by_term["deployment"].source_domain == "observability"
    assert by_term["production"].weight == pytest.approx(0.7)
    assert by_term["production"].source_domain == "configuration"


def test_FAIL_S03_disabled_map_returns_empty_lookup() -> None:
    """ExpansionMap com disabled=True gera lookup vazio.

    Input:
      ExpansionMap(domains=[], disabled=True)

    Output esperado:
      lookup == {}

    RED:  ImportError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, ExpansionMap

    expansion_map = ExpansionMap(domains=[], disabled=True)
    lookup = build_unidirectional_lookup(expansion_map)

    assert lookup == {}


def test_FAIL_S03_canonical_not_self_expanding() -> None:
    """O canonical em si NÃO aparece como expansão de si mesmo.

    Input:
      canonical: "cache"
      aliases:      ["caching"]
      strong_terms: ["ttl"]
      weak_terms:   []

    Output esperado:
      lookup["cache"] não contém ("cache", qualquer_peso)
      lookup["cache"] contém ("caching", 0.9)
      lookup["cache"] contém ("ttl", 0.7)

    RED:  ImportError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "caching",
                "version": "1",
                "entries": [
                    {
                        "canonical": "cache",
                        "aliases": ["caching"],
                        "strong_terms": ["ttl"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["caching.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "cache" in lookup
    terms_in_lookup = {c.term for c in lookup["cache"]}
    assert "cache" not in terms_in_lookup, (
        "O canonical 'cache' não deve aparecer como expansão de si mesmo"
    )
    assert "caching" in terms_in_lookup
    assert "ttl" in terms_in_lookup


# === Seção: S-04 — Integração expand_query_with_metadata ===

def test_FAIL_S04_expand_with_none_map_disables_expansion() -> None:
    """expand_query_with_metadata com expansion_map=None retorna só user tokens.

    Input:
      tokens = ["mensageria", "rabbitmq"]
      expansion_map = None

    Output esperado:
      info.expansion_disabled == True
      info.expansion_added_terms == []
      info.expansion_count == 0
      info.weights == {"mensageria": 1.0, "rabbitmq": 1.0}
        (apenas user tokens com peso 1.0; nenhum termo adicionado por expansão)
      info.diagnostics == []

    RED:  TypeError (parâmetro expansion_map não aceito ainda)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    tokens = ["mensageria", "rabbitmq"]
    info = expand_query_with_metadata(tokens, expansion_map=None)

    assert info.expansion_disabled is True
    assert info.expansion_added_terms == []
    assert info.expansion_count == 0
    assert info.diagnostics == []
    assert info.skipped_entries == []
    assert info.context_conflicts == []
    assert info.weights.get("mensageria") == pytest.approx(1.0)
    assert info.weights.get("rabbitmq") == pytest.approx(1.0)
    # Nenhum outro termo com peso < 1.0 deve aparecer
    for term, w in info.weights.items():
        assert w == pytest.approx(1.0), (
            f"Com expansion_map=None, '{term}' não deveria ter peso {w} (esperado 1.0)"
        )


def test_FAIL_S04_expand_with_disabled_map_disables_expansion() -> None:
    """expand_query_with_metadata com ExpansionMap(disabled=True) retorna só user tokens.

    Input:
      tokens = ["observabilidade"]
      expansion_map = ExpansionMap(domains=[], disabled=True)

    Output esperado:
      info.expansion_disabled == True
      info.expansion_added_terms == []
      "observabilidade" in info.weights com peso 1.0
      Nenhum termo expandido presente em info.weights

    RED:  ImportError / TypeError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata
    from corporate_instructions_mcp.expansion import ExpansionMap

    disabled_map = ExpansionMap(domains=[], disabled=True)
    tokens = ["observabilidade"]
    info = expand_query_with_metadata(tokens, expansion_map=disabled_map)

    assert info.expansion_disabled is True
    assert info.weights.get("observabilidade") == pytest.approx(1.0)
    assert info.expansion_added_terms == []


def test_FAIL_S04_expand_with_valid_map_applies_typed_weights() -> None:
    """expand_query_with_metadata usa pesos tipados do novo mapa.

    Setup:
      ExpansionMap com um domínio 'messaging':
        canonical: "mensageria"
        aliases:      ["messaging"]
        strong_terms: ["rabbitmq", "publish"]
        weak_terms:   ["outbox"]

    Input:
      tokens = ["mensageria"]
      expansion_map = (mapa acima)

    Output esperado:
      info.expansion_disabled == False
      info.weights["mensageria"] == 1.0    ← user token
      info.weights["messaging"]  == 0.9   ← alias
      info.weights["rabbitmq"]   == 0.7   ← strong_term
      info.weights["publish"]    == 0.7   ← strong_term
      info.weights["outbox"]     == 0.3   ← weak_term
      "rabbitmq" in info.expansion_added_terms
      "outbox" in info.expansion_added_terms

    RED:  ImportError / TypeError / AssertionError (pesos errados no sistema atual)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["mensageria"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert info.expansion_disabled is False
    assert info.weights.get("mensageria") == pytest.approx(1.0)
    assert info.weights.get("messaging") == pytest.approx(0.9)
    assert info.weights.get("rabbitmq") == pytest.approx(0.7)
    assert info.weights.get("publish") == pytest.approx(0.7)
    assert info.weights.get("outbox") == pytest.approx(0.3)

    assert "rabbitmq" in info.expansion_added_terms
    assert "outbox" in info.expansion_added_terms


def test_FAIL_S04_expand_diagnostics_populated() -> None:
    """expand_query_with_metadata popula diagnostics quando mapa válido.

    Setup:
      ExpansionMap com um domínio 'messaging' (source_file="messaging.yaml"):
        canonical: "mensageria"
        aliases:   ["messaging"]   ← deve gerar um ExpansionDiagnostic

    Input:
      tokens = ["mensageria"]

    Output esperado:
      len(info.diagnostics) >= 1
      info.diagnostics tem um item onde:
        diagnostic.canonical     == "mensageria"
        diagnostic.term          == "messaging"
        diagnostic.relation      == "alias"
        diagnostic.weight        == 0.9
        diagnostic.source_domain == "messaging"
        diagnostic.source_file   == "messaging.yaml"

    RED:  ImportError / AttributeError (campo diagnostics não existe)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["mensageria"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert len(info.diagnostics) >= 1

    alias_diag = next(
        (d for d in info.diagnostics if d.term == "messaging"),
        None,
    )
    assert alias_diag is not None, "Diagnóstico para alias 'messaging' não encontrado"
    assert alias_diag.canonical == "mensageria"
    assert alias_diag.relation == "alias"
    assert alias_diag.weight == pytest.approx(0.9)
    assert alias_diag.source_domain == "messaging"
    assert alias_diag.source_file == "messaging.yaml"


def test_FAIL_S04_expand_unidirectional_no_cross_contamination() -> None:
    """Com o novo mapa, 'rabbitmq' como token de usuário NÃO expande para 'mensageria'.

    Este é o teste central da ADR-002: sem expansão cruzada indevida.

    Setup:
      ExpansionMap com 'mensageria' como canonical → strong: rabbitmq
      (rabbitmq NÃO é canonical, portanto não tem expansão)

    Input:
      tokens = ["rabbitmq"]

    Output esperado:
      info.expansion_disabled == False   (mapa está ativo)
      info.expansion_added_terms == []   (rabbitmq não tem expansão no lookup)
      "mensageria" NOT in info.weights   (não houve expansão cruzada)

    Contraste com comportamento ATUAL (bidirecional):
      "mensageria" ESTARIA em info.weights via _EXPANSION_LOOKUP["rabbitmq"]

    RED:  AssertionError (sistema atual é bidirecional) ou ImportError
    GREEN: asserts passam (sistema novo é unidirecional)
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": [],
                        "strong_terms": ["rabbitmq"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["rabbitmq"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert info.expansion_disabled is False
    assert info.expansion_added_terms == [], (
        f"'rabbitmq' não é canonical, não deve ter expansão. "
        f"Termos adicionados: {info.expansion_added_terms}"
    )
    assert "mensageria" not in info.weights, (
        "Expansão cruzada indevida: 'rabbitmq' expandiu para 'mensageria' "
        "(ADR-002 exige lookup unidirecional)"
    )


def test_FAIL_S04_expand_query_without_explicit_map_parameter_backward_compat() -> None:
    """expand_query_with_metadata sem parâmetro expansion_map continua funcionando.

    Garante retrocompatibilidade da assinatura. Quando chamada sem o novo parâmetro,
    o comportamento deve ser equivalente a expansion_map=None (expansão desabilitada).

    Input:
      tokens = ["cache"]
      (sem parâmetro expansion_map — chamada legada)

    Output esperado:
      Nenhuma exceção
      info.expansion_disabled == True
      info.weights.get("cache") == 1.0

    RED:  pode passar ou falhar dependendo do estado de refatoração
    GREEN: asserts passam com nova implementação
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    tokens = ["cache"]
    info = expand_query_with_metadata(tokens)  # sem expansion_map

    assert info.expansion_disabled is True
    assert info.weights.get("cache") == pytest.approx(1.0)


# === Seção: S-05 — Domain YAML files no fixture corpus ===
# Setup: os testes assumem que INSTRUCTIONS_ROOT aponta para fixtures/instructions/

import os
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent.parent.parent / "fixtures" / "instructions"
MAP_DIR = FIXTURES_ROOT / "metadata" / "corpus-query-expansion-map"


def test_FAIL_S05_map_directory_exists() -> None:
    """Diretório metadata/corpus-query-expansion-map/ deve existir no fixture corpus.

    Input:  filesystem — fixtures/instructions/metadata/corpus-query-expansion-map/
    Output: diretório existe e é um diretório (não arquivo)

    RED:  AssertionError (diretório não existe antes da criação dos arquivos)
    GREEN: assert passa
    """
    assert MAP_DIR.exists(), f"Diretório não existe: {MAP_DIR}"
    assert MAP_DIR.is_dir(), f"Caminho existe mas não é diretório: {MAP_DIR}"


def test_FAIL_S05_required_domain_files_present() -> None:
    """Todos os arquivos de domínio obrigatórios devem estar presentes.

    Input:  filesystem listing de MAP_DIR
    Output: cada filename da lista abaixo existe como arquivo .yaml

    Arquivos obrigatórios:
      messaging.yaml, observability.yaml, architecture.yaml, persistence.yaml,
      resilience.yaml, api.yaml, security.yaml, caching.yaml, validation.yaml,
      configuration.yaml, dns.yaml, integration.yaml

    RED:  AssertionError (arquivos não existem)
    GREEN: asserts passam
    """
    required = [
        "messaging.yaml",
        "observability.yaml",
        "architecture.yaml",
        "persistence.yaml",
        "resilience.yaml",
        "api.yaml",
        "security.yaml",
        "caching.yaml",
        "validation.yaml",
        "configuration.yaml",
        "dns.yaml",
        "integration.yaml",
        "core.yaml",
        "dotnet.yaml",
        "governance.yaml",
    ]
    for filename in required:
        path = MAP_DIR / filename
        assert path.exists(), f"Arquivo de domínio ausente: {path}"
        assert path.is_file(), f"Caminho existe mas não é arquivo: {path}"


def test_FAIL_S05_messaging_yaml_mensageria_entry() -> None:
    """messaging.yaml contém entry 'mensageria' com strong_terms incluindo 'rabbitmq'.

    Input:  leitura e parse de fixtures/instructions/metadata/corpus-query-expansion-map/messaging.yaml
    Output:
      domain == "messaging"
      entry com canonical == "mensageria" existe
      entry.strong_terms contém "rabbitmq"
      entry.strong_terms contém "publish"
      entry.strong_terms contém "consume"
      entry.weak_terms contém "outbox"
      "rabbitmq" NÃO é canonical no arquivo (unidirectionality)

    RED:  FileNotFoundError ou AssertionError
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "messaging.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="messaging.yaml")

    assert domain is not None
    assert domain.domain == "messaging"

    mensageria_entry = next(
        (e for e in domain.entries if e.canonical == "mensageria"), None
    )
    assert mensageria_entry is not None, "Entry 'mensageria' não encontrada em messaging.yaml"
    assert "rabbitmq" in mensageria_entry.strong_terms
    assert "publish" in mensageria_entry.strong_terms
    assert "consume" in mensageria_entry.strong_terms
    assert "outbox" in mensageria_entry.strong_terms
    assert "event" in mensageria_entry.weak_terms

    # Verificar unidirectionality: rabbitmq NÃO é canonical
    canonicals = {e.canonical for e in domain.entries}
    assert "rabbitmq" not in canonicals, (
        "'rabbitmq' não deve ser canonical em messaging.yaml (unidirecional: mensageria→rabbitmq)"
    )


def test_FAIL_S05_dns_yaml_retry_not_in_strong_or_weak_terms() -> None:
    """dns.yaml NÃO deve ter 'retry' como strong_term nem weak_term.

    Esta é a correção central do problema I-05 (EPIC-07): evitar que 'resiliencia → retry'
    contamine 'dns-retry-pattern' via expansão cruzada.

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/dns.yaml
    Output:
      Para toda entry do domínio dns:
        'retry' NOT in entry.strong_terms
        'retry' NOT in entry.weak_terms
        'retry' NOT in entry.aliases

    RED:  FileNotFoundError ou AssertionError (se retry estiver presente)
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "dns.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="dns.yaml")

    assert domain is not None
    for entry in domain.entries:
        assert "retry" not in entry.strong_terms, (
            f"'retry' está em strong_terms de '{entry.canonical}' em dns.yaml — "
            f"isto causaria expansão cruzada indevida com resiliencia"
        )
        assert "retry" not in entry.weak_terms, (
            f"'retry' está em weak_terms de '{entry.canonical}' em dns.yaml"
        )
        assert "retry" not in entry.aliases, (
            f"'retry' está em aliases de '{entry.canonical}' em dns.yaml"
        )


def test_FAIL_S05_resilience_yaml_retry_not_as_canonical() -> None:
    """resilience.yaml: 'retry' NÃO é canonical (evita geração de expansão bidirecional via retry).

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/resilience.yaml
    Output:
      'retry' NOT in {e.canonical for e in domain.entries}

    Justificativa: 'retry' como canonical geraria um lookup entry própria que poderia
    reconectar indiretamente com dns. A cobertura de retry vem via 'polly' e 'circuit-breaker'
    como strong_terms de 'resiliencia'.

    RED:  FileNotFoundError ou AssertionError
    GREEN: assert passa
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "resilience.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="resilience.yaml")

    assert domain is not None
    canonicals = {e.canonical for e in domain.entries}
    assert "retry" not in canonicals, (
        "'retry' não deve ser canonical em resilience.yaml — "
        "use 'polly' e 'circuit-breaker' como strong_terms de 'resiliencia'"
    )


def test_FAIL_S05_observability_yaml_observabilidade_entry() -> None:
    """observability.yaml contém entry 'observabilidade' com opentelemetry e health.

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/observability.yaml
    Output:
      domain == "observability"
      entry com canonical == "observabilidade" existe
      entry.strong_terms contém "opentelemetry"
      entry.strong_terms contém "health"

    RED:  FileNotFoundError ou AssertionError
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "observability.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="observability.yaml")

    assert domain is not None
    assert domain.domain == "observability"

    obs_entry = next(
        (e for e in domain.entries if e.canonical == "observabilidade"), None
    )
    assert obs_entry is not None, "Entry 'observabilidade' não encontrada em observability.yaml"
    assert "opentelemetry" in obs_entry.strong_terms
    assert "health" in obs_entry.strong_terms


def test_FAIL_S05_load_corpus_expansion_map_from_fixtures() -> None:
    """load_corpus_expansion_map carrega todos os domínios do fixture corpus com sucesso.

    Input:  FIXTURES_ROOT = fixtures/instructions/
    Output:
      result.disabled == False
      len(result.domains) >= 10   (ao menos 10 domínios carregados)
      {d.domain for d in result.domains} contém:
        "messaging", "observability", "architecture", "persistence",
        "resilience", "api", "security", "caching", "validation",
        "configuration", "dns", "integration"

    RED:  ImportError / FileNotFoundError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    result = load_corpus_expansion_map(FIXTURES_ROOT)

    assert result.disabled is False, (
        f"ExpansionMap retornou disabled=True. Verifique que os arquivos YAML existem em {MAP_DIR}"
    )
    assert len(result.domains) >= 10, (
        f"Esperado ao menos 10 domínios, obtido {len(result.domains)}: "
        f"{[d.domain for d in result.domains]}"
    )

    expected_domains = {
        "messaging", "observability", "architecture", "persistence",
        "resilience", "api", "security", "caching", "validation",
        "configuration", "dns", "integration", "core", "dotnet", "governance",
    }
    loaded_domains = {d.domain for d in result.domains}
    missing = expected_domains - loaded_domains
    assert not missing, f"Domínios ausentes no mapa carregado: {missing}"


# === Seção: S-06 — Remoção de DEFAULT_SYNONYMS e synonyms.yaml bundled ===

def test_FAIL_S06_default_synonyms_not_in_indexing() -> None:
    """DEFAULT_SYNONYMS não deve existir em indexing.py após a remoção.

    Verifica que o módulo indexing não exporta mais DEFAULT_SYNONYMS.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, 'DEFAULT_SYNONYMS')` == False

    RED:  AssertionError (DEFAULT_SYNONYMS ainda existe no módulo atual)
    GREEN: assert passa após remoção
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "DEFAULT_SYNONYMS"), (
        "DEFAULT_SYNONYMS ainda existe em indexing.py — deve ser removido conforme ADR-002"
    )


def test_FAIL_S06_load_expansion_map_from_file_not_in_indexing() -> None:
    """_load_expansion_map_from_file não deve existir em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_load_expansion_map_from_file')` == False

    RED:  AssertionError (função ainda existe)
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_load_expansion_map_from_file"), (
        "_load_expansion_map_from_file ainda existe em indexing.py — deve ser removido"
    )


def test_FAIL_S06_build_expansion_lookup_not_in_indexing() -> None:
    """_build_expansion_lookup não deve existir em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_build_expansion_lookup')` == False

    RED:  AssertionError
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_build_expansion_lookup"), (
        "_build_expansion_lookup ainda existe em indexing.py — deve ser removido"
    )


def test_FAIL_S06_query_expansion_map_not_module_level() -> None:
    """QUERY_EXPANSION_MAP não deve existir como módulo-level em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, 'QUERY_EXPANSION_MAP')` == False

    RED:  AssertionError (ainda existe como global)
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "QUERY_EXPANSION_MAP"), (
        "QUERY_EXPANSION_MAP ainda existe em indexing.py como módulo-level global"
    )


def test_FAIL_S06_expansion_lookup_not_module_level() -> None:
    """_EXPANSION_LOOKUP não deve existir como módulo-level em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_EXPANSION_LOOKUP')` == False

    RED:  AssertionError
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_EXPANSION_LOOKUP"), (
        "_EXPANSION_LOOKUP ainda existe em indexing.py"
    )


def test_FAIL_S06_synonyms_yaml_not_in_package_directory() -> None:
    """synonyms.yaml bundled não deve existir dentro do pacote Python após remoção.

    Input:  filesystem — corporate_instructions_mcp/synonyms.yaml
    Output: arquivo NÃO existe

    RED:  AssertionError (arquivo ainda existe antes da remoção)
    GREEN: assert passa
    """
    from pathlib import Path
    import corporate_instructions_mcp
    package_dir = Path(corporate_instructions_mcp.__file__).parent
    bundled_synonyms = package_dir / "synonyms.yaml"
    assert not bundled_synonyms.exists(), (
        f"synonyms.yaml bundled ainda existe em {bundled_synonyms} — deve ser removido conforme ADR-002"
    )


# === Seção: S-07 — Validação dos critérios ADR-002 ===
# Estes testes usam o servidor completo com o fixture corpus.
# Requerem que S-04 e S-05 estejam implementados (expansion_map carregado em _ensure_index).

def test_FAIL_S07_adr002_criterion1_recall_improves_for_zero_result_queries() -> None:
    """ADR-002 critério 1: recall de ao menos 3 queries previamente sem resultado melhora.

    As queries abaixo devem retornar ao menos 1 resultado relevante via expansão.
    Em estado sem expansão (antes desta implementação ou com map disabled), retornam 0
    ou resultados irrelevantes.

    Queries testadas e resultado mínimo esperado:

    Query 1: "healthcheck live ready producao"
      Resultado mínimo: "microservice-configuration-production-readiness" em selected_ids
      Justificativa: 'healthcheck' → strong: live, ready, readiness; 'producao' → via
        'transacao' ou 'logs' que têm 'production' como strong/weak.

    Query 2: "mensageria publicação assincrona"
      Resultado mínimo: "microservice-messaging-rabbitmq-publish-consume" em selected_ids
      Justificativa: 'mensageria' → strong: rabbitmq, publish, consume.

    Query 3: "resiliencia circuito e tolerancia"
      Resultado mínimo: "microservice-resilience-polly-timeouts-and-circuit-breaker" em selected_ids
      Justificativa: 'resiliencia' → strong: polly, circuit-breaker, timeout.

    Input:  server tools com fixture corpus + expansion_map ativo
    Output: para cada query, o resultado mínimo está em selected_ids

    RED:  AssertionError (sem expansão tipada, queries falham em recuperar o doc correto)
    GREEN: asserts passam
    """
    import json
    from corporate_instructions_mcp.server import resolve_instruction_context

    # Query 1: healthcheck → production-readiness
    data1 = json.loads(resolve_instruction_context(
        "healthcheck live ready producao", max_results=7
    ))
    assert "microservice-configuration-production-readiness" in data1["selected_ids"], (
        f"ADR-002 critério 1, query 1: 'microservice-configuration-production-readiness' ausente. "
        f"selected_ids={data1['selected_ids']}"
    )

    # Query 2: mensageria → rabbitmq
    data2 = json.loads(resolve_instruction_context(
        "mensageria publicacao assincrona", max_results=7
    ))
    assert "microservice-messaging-rabbitmq-publish-consume" in data2["selected_ids"], (
        f"ADR-002 critério 1, query 2: 'microservice-messaging-rabbitmq-publish-consume' ausente. "
        f"selected_ids={data2['selected_ids']}"
    )

    # Query 3: resiliencia → polly
    data3 = json.loads(resolve_instruction_context(
        "resiliencia circuito tolerancia", max_results=7
    ))
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in data3["selected_ids"], (
        f"ADR-002 critério 1, query 3: 'microservice-resilience-polly-timeouts-and-circuit-breaker' ausente. "
        f"selected_ids={data3['selected_ids']}"
    )


def test_FAIL_S07_adr002_criterion2_precision_not_degraded_single_domain() -> None:
    """ADR-002 critério 2: precisão (top-1 correto) não piora em queries de domínio único.

    Queries de domínio único (sem contexto ambíguo) devem ter seu documento principal
    como primeiro resultado, mesmo com expansão ativa.

    Query 1: "rabbitmq publish consume outbox"
      top-1 esperado: "microservice-messaging-rabbitmq-publish-consume"
      (termo rabbitmq aparece no título, tags e body — deve dominar)

    Query 2: "polly retry circuit breaker timeout"
      top-1 esperado: "microservice-resilience-polly-timeouts-and-circuit-breaker"

    Query 3: "imemorycache idistributedcache ttl invalidation"
      top-1 esperado: "microservice-caching-imemorycache-policy"

    Input:  server tools com fixture corpus + expansion_map ativo
    Output:
      query 1: results[0]["id"] == "microservice-messaging-rabbitmq-publish-consume"
      query 2: results[0]["id"] == "microservice-resilience-polly-timeouts-and-circuit-breaker"
      query 3: results[0]["id"] == "microservice-caching-imemorycache-policy"

    RED:  AssertionError se expansão introduz ruído que derruba o top-1
    GREEN: asserts passam
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    # Query 1: rabbitmq direto → deve ser top-1
    data1 = json.loads(search_instructions(
        query="rabbitmq publish consume outbox", max_results=5
    ))
    top1_id_1 = data1["results"][0]["id"]
    assert top1_id_1 == "microservice-messaging-rabbitmq-publish-consume", (
        f"ADR-002 critério 2, query 1: top-1 esperado 'microservice-messaging-rabbitmq-publish-consume', "
        f"obtido '{top1_id_1}'. Expansão pode estar introduzindo ruído."
    )

    # Query 2: polly direto
    data2 = json.loads(search_instructions(
        query="polly retry circuit breaker timeout", max_results=5
    ))
    top1_id_2 = data2["results"][0]["id"]
    assert top1_id_2 == "microservice-resilience-polly-timeouts-and-circuit-breaker", (
        f"ADR-002 critério 2, query 2: top-1 esperado 'microservice-resilience-polly-timeouts-and-circuit-breaker', "
        f"obtido '{top1_id_2}'"
    )

    # Query 3: imemorycache direto
    data3 = json.loads(search_instructions(
        query="imemorycache idistributedcache ttl invalidation", max_results=5
    ))
    top1_id_3 = data3["results"][0]["id"]
    assert top1_id_3 == "microservice-caching-imemorycache-policy", (
        f"ADR-002 critério 2, query 3: top-1 esperado 'microservice-caching-imemorycache-policy', "
        f"obtido '{top1_id_3}'"
    )


def test_FAIL_S07_adr002_criterion3_no_cross_domain_contamination() -> None:
    """ADR-002 critério 3: termos contextuais NÃO aparecem em resultados sem contexto do domínio.

    Cenário principal: 'mensageria' expande para 'rabbitmq', mas uma query sem nenhum
    termo de mensageria NÃO deve trazer 'microservice-messaging-rabbitmq-publish-consume'
    via expansão cruzada.

    Query: "polly retry circuit breaker"
      'rabbitmq' não está no lookup de 'resiliencia' → messaging doc não deve aparecer
      'dns-retry-pattern' não deve aparecer (retry isolado de dns)

    Expected top-5 NOT to contain:
      "microservice-messaging-rabbitmq-publish-consume"
      "dns-retry-pattern"

    Input:  server tools com fixture corpus + expansion_map ativo
    Output:
      "microservice-messaging-rabbitmq-publish-consume" NOT in top-5 ids
      "dns-retry-pattern" NOT in top-5 ids

    RED:  AssertionError se expansão bidirecional ainda estiver ativa
    GREEN: asserts passam (lookup unidirecional)
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(
        query="polly retry circuit breaker", max_results=7
    ))
    top5_ids = [r["id"] for r in data["results"][:5]]

    assert "microservice-messaging-rabbitmq-publish-consume" not in top5_ids, (
        f"ADR-002 critério 3: 'mensageria/rabbitmq' contaminou query de resiliência. "
        f"top-5={top5_ids}"
    )
    assert "dns-retry-pattern" not in top5_ids, (
        f"ADR-002 critério 3: 'dns-retry-pattern' apareceu em query de polly/circuit-breaker. "
        f"top-5={top5_ids} — 'retry' não deve ser strong_term de resilience nem de dns"
    )


def test_FAIL_S07_adr002_criterion4_diagnostics_reproducible() -> None:
    """ADR-002 critério 4: diagnóstico reproduz exatamente o comportamento observado.

    Executa a mesma query duas vezes; os diagnósticos devem ser idênticos (determinísticos).

    Query: "observabilidade health opentelemetry"

    Para cada execução:
      - info.diagnostics deve ter ao menos um ExpansionDiagnostic
      - diagnostics[0] da execução 1 == diagnostics[0] da execução 2
        (mesmo canonical, term, relation, weight, source_domain, source_file)

    Input:
      tokens = tokenize_query("observabilidade health opentelemetry")
      expansion_map = load_corpus_expansion_map(FIXTURES_ROOT)

    Output:
      Duas chamadas a expand_query_with_metadata(tokens, expansion_map) retornam
      diagnostics com o mesmo conteúdo.

    RED:  ImportError / AttributeError (campo diagnostics não existe)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata, tokenize_query
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    map1 = load_corpus_expansion_map(FIXTURES_ROOT)
    tokens = tokenize_query("observabilidade health opentelemetry")

    info1 = expand_query_with_metadata(tokens, expansion_map=map1)
    info2 = expand_query_with_metadata(tokens, expansion_map=map1)

    assert len(info1.diagnostics) > 0, "Nenhum diagnóstico gerado — mapa pode estar disabled"
    assert len(info1.diagnostics) == len(info2.diagnostics), (
        f"Diagnósticos não-determinísticos: run1={len(info1.diagnostics)}, run2={len(info2.diagnostics)}"
    )

    for i, (d1, d2) in enumerate(zip(info1.diagnostics, info2.diagnostics)):
        assert d1.canonical == d2.canonical, f"diagnostic[{i}].canonical diferente"
        assert d1.term == d2.term, f"diagnostic[{i}].term diferente"
        assert d1.relation == d2.relation, f"diagnostic[{i}].relation diferente"
        assert d1.weight == pytest.approx(d2.weight), f"diagnostic[{i}].weight diferente"
        assert d1.source_domain == d2.source_domain, f"diagnostic[{i}].source_domain diferente"
        assert d1.source_file == d2.source_file, f"diagnostic[{i}].source_file diferente"


def test_REGRESSION_S07_dns_query_still_finds_dns_retry_pattern() -> None:
    """REGRESSÃO: query de DNS ainda deve encontrar dns-retry-pattern como top-1.

    Este teste DEVE SEMPRE PASSAR (não é RED/GREEN — é invariante de regressão).

    Input:
      query = "retry DNS polly"
      max_results = 3

    Output esperado:
      results[0]["id"] == "dns-retry-pattern"

    Justificativa: dns-retry-pattern permanece findable via tokens diretos de DNS
    (não via expansão cruzada de resiliência).
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"][0]["id"] == "dns-retry-pattern", (
        f"REGRESSÃO: 'dns-retry-pattern' deixou de ser top-1 para query 'retry DNS polly'. "
        f"results={[r['id'] for r in data['results']]}"
    )


def test_REGRESSION_S07_cep_viacep_bundle_intact() -> None:
    """REGRESSÃO: bundle de CEP/ViaCEP continua funcionando após as mudanças.

    Input:
      context query = "buscar endereço por CEP usando ViaCEP com retry e cache"
      max_results = 7

    Output esperado:
      selected_ids contém ao menos 3 dos seguintes:
        "microservice-integration-httpclientfactory-contracts"
        "microservice-resilience-polly-timeouts-and-circuit-breaker"
        "microservice-caching-imemorycache-policy"
        "microservice-api-validation-and-error-contracts"
    """
    import json
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(
        "buscar endereco por CEP usando ViaCEP com retry e cache",
        max_results=7,
    ))
    expected = {
        "microservice-integration-httpclientfactory-contracts",
        "microservice-resilience-polly-timeouts-and-circuit-breaker",
        "microservice-caching-imemorycache-policy",
        "microservice-api-validation-and-error-contracts",
    }
    found = expected & set(data["selected_ids"])
    assert len(found) >= 3, (
        f"REGRESSÃO: bundle CEP/ViaCEP incompleto. "
        f"Encontrados: {found}. "
        f"selected_ids={data['selected_ids']}"
    )


def test_REGRESSION_S07_persistencia_sql_returns_data_access() -> None:
    """REGRESSÃO: query de persistência SQL retorna data-access doc.

    Input:
      query = "persistencia sql dapper repositorio"
      max_results = 5

    Output esperado:
      results[0]["id"] == "microservice-data-access-and-sql-security"
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(
        query="persistencia sql dapper repositorio", max_results=5
    ))
    assert data["results"][0]["id"] == "microservice-data-access-and-sql-security", (
        f"REGRESSÃO: top-1 para query de persistência SQL mudou. "
        f"results={[r['id'] for r in data['results']]}"
    )


# === Seção: S-07b — Critérios ADR-002 V1.1/V1.2 (critérios 5–10) ===

# ---------------------------------------------------------------------------
# Critério 5: applies_to no nível do termo
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion5a_applies_to_blocks_entry_when_path_known() -> None:
    """ADR-002 critério 5a: applies_to filtra entrada quando current_file_path fornecido
    e não corresponde.

    Setup:
      ExpansionEntry:
        canonical:   "options"
        strong_terms: ["ioptions"]
        applies_to:  ["**/*.cs"]   ← só expande para arquivos .cs

    Input:
      tokens = ["options"]
      current_file_path = "docs/readme.md"   ← não é .cs → não deve expandir

    Output esperado:
      info.expansion_disabled == False    (mapa está ativo)
      "ioptions" NOT in info.weights      (entrada barrada por applies_to)
      len(info.skipped_entries) == 1
      info.skipped_entries[0].reason == "skipped_by_applies_to"
      info.skipped_entries[0].canonical == "options"
      info.skipped_entries[0].current_file_path == "docs/readme.md"

    RED:  ImportError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "dotnet",
                "version": "1",
                "entries": [
                    {
                        "canonical": "options",
                        "strong_terms": ["ioptions"],
                        "applies_to": ["**/*.cs"],
                    }
                ],
            }
        ],
        ["dotnet.yaml"],
    )

    tokens = ["options"]
    info = expand_query_with_metadata(
        tokens, expansion_map=expansion_map, current_file_path="docs/readme.md"
    )

    assert info.expansion_disabled is False
    assert "ioptions" not in info.weights, (
        "ADR-002 critério 5a: applies_to deveria ter barrado a entrada para docs/readme.md"
    )
    assert len(info.skipped_entries) == 1
    assert info.skipped_entries[0].reason == "skipped_by_applies_to"
    assert info.skipped_entries[0].canonical == "options"
    assert info.skipped_entries[0].current_file_path == "docs/readme.md"


def test_FAIL_S07b_criterion5b_applies_to_does_not_block_when_path_absent() -> None:
    """ADR-002 critério 5b: applies_to não bloqueia expansão quando current_file_path ausente.

    Mesma entrada de S-07b-criterion5a, sem current_file_path.

    Input:
      tokens = ["options"]
      current_file_path = None

    Output esperado:
      "ioptions" in info.weights          (applies_to ignorado sem path)
      len(info.skipped_entries) == 0

    RED:  ImportError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "dotnet",
                "version": "1",
                "entries": [
                    {
                        "canonical": "options",
                        "strong_terms": ["ioptions"],
                        "applies_to": ["**/*.cs"],
                    }
                ],
            }
        ],
        ["dotnet.yaml"],
    )

    tokens = ["options"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map, current_file_path=None)

    assert "ioptions" in info.weights, (
        "ADR-002 critério 5b: applies_to deve ser ignorado quando current_file_path é None"
    )
    assert len(info.skipped_entries) == 0


def test_FAIL_S07b_criterion5c_applies_to_allows_matching_path() -> None:
    """ADR-002 critério 5c: applies_to não bloqueia quando path corresponde ao padrão.

    Input:
      tokens = ["options"]
      current_file_path = "src/MyService.cs"   ← corresponde a **/*.cs

    Output esperado:
      "ioptions" in info.weights
      len(info.skipped_entries) == 0

    RED:  ImportError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "dotnet",
                "version": "1",
                "entries": [
                    {
                        "canonical": "options",
                        "strong_terms": ["ioptions"],
                        "applies_to": ["**/*.cs"],
                    }
                ],
            }
        ],
        ["dotnet.yaml"],
    )

    tokens = ["options"]
    info = expand_query_with_metadata(
        tokens, expansion_map=expansion_map, current_file_path="src/MyService.cs"
    )

    assert "ioptions" in info.weights, (
        "ADR-002 critério 5c: path 'src/MyService.cs' corresponde a '**/*.cs' — deve expandir"
    )
    assert len(info.skipped_entries) == 0


# ---------------------------------------------------------------------------
# Critério 6: ativação cruzada produz sinal explícito
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion6_cross_activation_conflict_signaled() -> None:
    """ADR-002 critério 6: dois contextos do mesmo canonical ativos → ContextConflictDiagnostic.

    Setup:
      canonical: "mensageria" com dois contextos:
        ctx0: activation_terms=["queue"], terms=["rabbitmq"]
        ctx1: activation_terms=["queue", "broker"], terms=["servicebus"]

      Token "queue" satisfaz AMBOS os contextos simultaneamente → conflito.

    Input:
      tokens = ["mensageria", "queue"]

    Output esperado:
      len(info.context_conflicts) >= 1
      info.context_conflicts[0].canonical == "mensageria"
      len(info.context_conflicts[0].conflicting_context_indices) == 2
      info.context_conflicts[0].resolution == "agent_must_decide"

    Nota: nenhum termo de contexto (rabbitmq, servicebus) deve ser adicionado a weights
    quando há conflito (scoring contextual não é aplicado neste épico de qualquer forma).

    RED:  ImportError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": [],
                        "strong_terms": [],
                        "weak_terms": [],
                        "contexts": [
                            {
                                "activation_terms": ["queue"],
                                "terms": ["rabbitmq"],
                            },
                            {
                                "activation_terms": ["queue", "broker"],
                                "terms": ["servicebus"],
                            },
                        ],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["mensageria", "queue"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert len(info.context_conflicts) >= 1, (
        "ADR-002 critério 6: ativação cruzada de contextos não gerou ContextConflictDiagnostic"
    )
    conflict = next(
        (c for c in info.context_conflicts if c.canonical == "mensageria"), None
    )
    assert conflict is not None, "Conflito para canonical 'mensageria' não encontrado"
    assert len(conflict.conflicting_context_indices) == 2
    assert conflict.resolution == "agent_must_decide"


# ---------------------------------------------------------------------------
# Critério 7: arquivos YAML usam schema V1.1 (sem when_path_matches / path_pattern)
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion7_yaml_files_use_v11_schema() -> None:
    """ADR-002 critério 7: nenhum arquivo YAML do fixture corpus usa schema pré-V1.1.

    Verificação estrutural: nenhum arquivo .yaml em MAP_DIR deve conter as chaves
    'path_pattern' ou 'when_path_matches' em nenhum nível.

    Input:  filesystem — todos os *.yaml em MAP_DIR
    Output:
      Para cada arquivo, parse YAML bem-sucedido.
      Nenhum contexto de nenhuma entrada contém 'path_pattern' ou 'when_path_matches'.

    RED:  AssertionError se algum arquivo usar schema pré-V1.1
    GREEN: asserts passam
    """
    import yaml

    for yaml_file in sorted(MAP_DIR.glob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue
        for entry in raw.get("entries", []):
            for ctx in entry.get("contexts", []):
                assert "path_pattern" not in ctx, (
                    f"{yaml_file.name}: contexto usa 'path_pattern' (schema pré-V1.1 rejeitado). "
                    f"Usar 'activation_terms' + 'applies_to' conforme ADR-002 §2.1."
                )
                assert "when_path_matches" not in ctx, (
                    f"{yaml_file.name}: contexto usa 'when_path_matches' (schema pré-V1.1 rejeitado)."
                )


# ---------------------------------------------------------------------------
# Critério 8: skipped_by_applies_to no diagnóstico
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion8_skipped_by_applies_to_in_diagnostic() -> None:
    """ADR-002 critério 8: diagnóstico registra omissão skipped_by_applies_to.

    Valida que SkippedEntryDiagnostic contém os campos corretos (ADR-002 §2.1 V1.2):
      reason, canonical, applies_to, current_file_path, source_domain, source_file.

    Setup:
      ExpansionEntry canonical="cache", applies_to=["**/*.cs"], strong_terms=["ttl"]
    Input:
      tokens=["cache"], current_file_path="docs/readme.md"

    Output esperado:
      skipped = info.skipped_entries[0]
      skipped.reason            == "skipped_by_applies_to"
      skipped.canonical         == "cache"
      skipped.applies_to        == ["**/*.cs"]
      skipped.current_file_path == "docs/readme.md"
      skipped.source_domain     == "caching"
      skipped.source_file       == "caching.yaml"

    RED:  ImportError / AttributeError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "caching",
                "version": "1",
                "entries": [
                    {
                        "canonical": "cache",
                        "strong_terms": ["ttl"],
                        "applies_to": ["**/*.cs"],
                    }
                ],
            }
        ],
        ["caching.yaml"],
    )

    tokens = ["cache"]
    info = expand_query_with_metadata(
        tokens, expansion_map=expansion_map, current_file_path="docs/readme.md"
    )

    assert len(info.skipped_entries) == 1
    skipped = info.skipped_entries[0]
    assert skipped.reason == "skipped_by_applies_to"
    assert skipped.canonical == "cache"
    assert skipped.applies_to == ["**/*.cs"]
    assert skipped.current_file_path == "docs/readme.md"
    assert skipped.source_domain == "caching"
    assert skipped.source_file == "caching.yaml"


# ---------------------------------------------------------------------------
# Critério 9: validação rejeita contexto com terms sem activation/applies_to
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion9_context_with_terms_no_activation_rejected() -> None:
    """ADR-002 critério 9: parse_domain_file rejeita contexto com terms mas sem ativação.

    Já coberto em S-01 (test_FAIL_S01_parse_domain_file_context_with_terms_no_activation_is_rejected).
    Este teste repete a verificação com dois contextos e confirma que o contexto válido
    é preservado, garantindo que a validação é por contexto (não por entrada).

    Input:
      entry com:
        ctx_invalido: terms=["servicebus"], sem activation_terms nem applies_to
        ctx_valido:   terms=["rabbitmq"], activation_terms=["queue"]

    Output esperado:
      result is not None
      len(entry.contexts) == 1
      entry.contexts[0].terms == ["rabbitmq"]

    RED:  ModuleNotFoundError / AssertionError
    GREEN: asserts passam (idêntico ao teste S-01 — confirma invariante do critério)
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "contexts": [
                    {"terms": ["servicebus"]},
                    {"activation_terms": ["queue"], "terms": ["rabbitmq"]},
                ],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    entry = result.entries[0]
    assert len(entry.contexts) == 1
    assert entry.contexts[0].terms == ["rabbitmq"]


# ---------------------------------------------------------------------------
# Critério 10: combinação applies_to (termo × contexto) — reproduzível
# ---------------------------------------------------------------------------

def test_FAIL_S07b_criterion10_applies_to_term_blocks_context_evaluation() -> None:
    """ADR-002 critério 10: applies_to no nível do termo barra avaliação dos contextos.

    Conforme ADR-002 §2.1: 'applies_to no termo restringe a entrada inteira: aliases,
    strong_terms, weak_terms, e a elegibilidade para avaliar contexts desse termo.'

    Setup:
      ExpansionEntry:
        canonical:    "options"
        strong_terms: ["ioptions"]
        applies_to:   ["**/*.cs"]     ← barra toda a entrada se path não for .cs
        contexts:
          - activation_terms: ["configuration"]
            terms:            ["optionspattern"]

    Input:
      tokens = ["options", "configuration"]
      current_file_path = "docs/readme.md"   ← não é .cs

    Output esperado:
      "ioptions" NOT in info.weights        (strong_terms barrado)
      "optionspattern" NOT in info.weights  (contexto não avaliado — entrada barrada)
      len(info.skipped_entries) == 1
      info.skipped_entries[0].canonical == "options"

    RED:  ImportError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "dotnet",
                "version": "1",
                "entries": [
                    {
                        "canonical": "options",
                        "strong_terms": ["ioptions"],
                        "applies_to": ["**/*.cs"],
                        "contexts": [
                            {
                                "activation_terms": ["configuration"],
                                "terms": ["optionspattern"],
                            }
                        ],
                    }
                ],
            }
        ],
        ["dotnet.yaml"],
    )

    tokens = ["options", "configuration"]
    info = expand_query_with_metadata(
        tokens, expansion_map=expansion_map, current_file_path="docs/readme.md"
    )

    assert "ioptions" not in info.weights, (
        "ADR-002 critério 10: applies_to no termo deveria ter barrado strong_terms"
    )
    assert "optionspattern" not in info.weights, (
        "ADR-002 critério 10: applies_to no termo deveria ter barrado avaliação do contexto"
    )
    assert len(info.skipped_entries) >= 1
    assert any(s.canonical == "options" for s in info.skipped_entries)
