"""Index Markdown instruction files: frontmatter, body, and lightweight search."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from corporate_instructions_mcp.paths import is_path_under_root

FRONTMATTER_SPLIT = re.compile(r"^---\s*$", re.MULTILINE)
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]*")
PHRASE_PATTERN = re.compile(r'"([^"]+)"')
VERSION_CHUNK_PATTERN = re.compile(r"[a-z]+|\d+")

# Defensive limits (OWASP-style abuse of CPU/memory via corpus).
MAX_INSTRUCTION_FILE_BYTES = 5 * 1024 * 1024
MAX_FRONTMATTER_SECTION_CHARS = 65536

log = logging.getLogger(__name__)

_INDEX_WARNINGS: list[dict[str, Any]] = []

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1, None: 0}
EXPANSION_CAP_PER_TOKEN = 5

STOPWORDS = {
    "the",
    "and",
    "or",
    "for",
    "of",
    "to",
    "in",
    "with",
    "a",
    "an",
    "para",
    "com",
    "sem",
    "uma",
    "um",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "no",
    "nas",
    "nos",
    "ao",
    "aos",
    "this",
    "that",
    "using",
}

DEFAULT_SYNONYMS: dict[str, list[str]] = {
    "cache": ["imemorycache", "idistributedcache", "caching", "ttl", "invalidation"],
    "persistencia": ["dapper", "sql", "repositorio", "data-access", "efcore"],
    "validacao": ["validation", "error-contracts", "400", "422", "problem-details"],
    "http": ["rest", "status-codes", "endpoint", "api", "patch"],
    "resiliencia": ["polly", "retry", "circuit-breaker", "timeout", "tolerancia"],
    "arquitetura": ["layering", "camadas", "clean-architecture", "solid", "dotnet"],
    "testes": ["testing", "unit", "integration", "contract", "xunit"],
    "observabilidade": ["opentelemetry", "health", "correlation", "tracing", "metrics"],
    "mensageria": ["rabbitmq", "messaging", "publish", "consume", "outbox"],
    "seguranca": ["security", "secrets", "jwt", "authentication", "authorization"],
    "api": ["problem-details", "rfc7807", "pagination", "filtering", "minimal-api"],
    "configuracao": ["configuration", "options", "ioptions", "feature-flags", "deployment"],
    "dominio": ["domain", "repository", "interfaces", "models", "table-storage"],
    "integracao": ["integration", "httpclient", "contracts", "serialization", "resilience"],
    "saga": ["orchestration", "process-manager", "consistency", "idempotency", "compensation"],
    "governanca": ["governance", "bmad", "corpus", "instructions", "mcp"],
    "encoding": ["utf-8", "unicode", "markdown", "line-endings", "repository"],
    "csharp": ["dotnet", "async", "style", "generics", "performance"],
    "planejamento": ["planning", "assistant", "inference", "confidence", "legacy"],
    "conformidade": ["compliance", "secrets", "audit", "ownership", "resource-scope"],
    "dns": ["nameserver", "resolver", "lookup", "network", "retry"],
}


def _normalize_token(token: str) -> str:
    normalized = unicodedata.normalize("NFKD", token)
    no_diacritics = "".join(c for c in normalized if not unicodedata.combining(c))
    compact = no_diacritics.replace("_", "-").strip().lower()
    return compact


def normalize_text(text: str) -> str:
    return _normalize_token(text)


def _normalize_for_index(text: str) -> str:
    lowered = normalize_text(text)
    return lowered.replace("_", " ").replace("-", " ")


def _requires_boundary_match(term: str) -> bool:
    compact = re.sub(r"[^a-z0-9]+", "", term)
    return bool(compact) and len(compact) <= 3


def _boundary_count(text: str, term: str) -> int:
    if not term:
        return 0
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])")
    return len(pattern.findall(text))


def _term_hit_count(text: str, term: str) -> int:
    if not term:
        return 0
    if _requires_boundary_match(term):
        return _boundary_count(text, term)
    return text.count(term)


def _term_in_text(text: str, term: str) -> bool:
    return _term_hit_count(text, term) > 0


def _token_variants(token: str) -> list[str]:
    normalized = _normalize_token(token)
    variants: set[str] = {normalized}
    parts = VERSION_CHUNK_PATTERN.findall(normalized.replace(".", ""))
    if len(parts) >= 2:
        joined = "".join(parts)
        variants.add(joined)
        for part in parts:
            if len(part) > 1 and part not in STOPWORDS:
                variants.add(part)
        if parts[0] == "net" and any(part.isdigit() for part in parts[1:]):
            numeric = "".join(part for part in parts[1:] if part.isdigit())
            if numeric:
                variants.add(f"dotnet{numeric}")
                variants.add(f"net{numeric}")
    if normalized.startswith("v") and normalized[1:].isdigit():
        variants.add(normalized[1:])
    return sorted(
        variant
        for variant in variants
        if ((len(variant) > 1) or variant.isdigit()) and variant not in STOPWORDS
    )


def _record_index_warning(code: str, path: str, details: dict[str, Any] | None = None) -> None:
    warning = {"code": code, "path": path}
    if details:
        warning["details"] = details
    _INDEX_WARNINGS.append(warning)


def clear_index_warnings() -> None:
    _INDEX_WARNINGS.clear()


def get_index_warnings() -> list[dict[str, Any]]:
    return [dict(item) for item in _INDEX_WARNINGS]


@dataclass
class InstructionRecord:
    """Single instruction document with parsed frontmatter and body."""

    id: str
    rel_path: str
    title: str
    tags: list[str]
    scope: str | None
    priority: str | None
    kind: str | None
    body: str
    content_hash: str
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)

    def search_blob(self) -> str:
        return _normalize_for_index(f"{self.title}\n{' '.join(self.tags)}\n{self.body}")


@dataclass(frozen=True)
class CorpusSignature:
    signature: str
    file_count: int
    latest_mtime_ns: int


def corpus_signature(root: Path) -> CorpusSignature:
    root = root.resolve()
    hasher = hashlib.sha256()
    file_count = 0
    latest_mtime_ns = 0
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        if not is_path_under_root(path, root):
            continue
        st = path.stat()
        file_count += 1
        latest_mtime_ns = max(latest_mtime_ns, st.st_mtime_ns)
        rel = str(path.relative_to(root)).replace("\\", "/")
        hasher.update(f"{rel}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8"))
    return CorpusSignature(signature=hasher.hexdigest(), file_count=file_count, latest_mtime_ns=latest_mtime_ns)


def _slug_from_path(path: Path) -> str:
    stem = path.stem.lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "instruction"


def _parse_markdown(path: Path, root: Path) -> InstructionRecord:
    text = path.read_text(encoding="utf-8", errors="replace")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rel = str(path.relative_to(root)).replace("\\", "/")

    meta: dict[str, Any] = {}
    body = text
    parts = FRONTMATTER_SPLIT.split(text, maxsplit=2)
    if len(parts) >= 3 and parts[0].strip() == "":
        fm_raw = parts[1]
        if len(fm_raw) > MAX_FRONTMATTER_SECTION_CHARS:
            log.warning(
                "frontmatter_truncated_skipped path=%s size=%s max=%s",
                rel,
                len(fm_raw),
                MAX_FRONTMATTER_SECTION_CHARS,
            )
            _record_index_warning(
                "FRONTMATTER_TOO_LARGE",
                rel,
                {
                    "frontmatter_chars": len(fm_raw),
                    "max_frontmatter_chars": MAX_FRONTMATTER_SECTION_CHARS,
                },
            )
            meta = {}
        else:
            try:
                loaded = yaml.safe_load(fm_raw)
                meta = loaded if isinstance(loaded, dict) else {}
            except yaml.YAMLError:
                _record_index_warning("FRONTMATTER_PARSE_FAILED", rel)
                meta = {}
        body = parts[2].lstrip("\n")

    doc_id = str(meta.get("id") or _slug_from_path(path))
    title = str(meta.get("title") or path.stem)
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tags = [_normalize_token(str(t)) for t in tags]
    scope = meta.get("scope")
    scope = str(scope) if scope is not None else None
    priority = meta.get("priority")
    priority = _normalize_token(str(priority)) if priority is not None else None
    kind = meta.get("kind")
    kind = _normalize_token(str(kind)) if kind is not None else None

    return InstructionRecord(
        id=doc_id,
        rel_path=rel,
        title=title,
        tags=tags,
        scope=scope,
        priority=priority,
        kind=kind,
        body=body.strip(),
        content_hash=h,
        raw_frontmatter=meta,
    )


def build_index(root: Path) -> dict[str, InstructionRecord]:
    """Load all ``*.md`` under ``root`` (recursive). Keys are document ids (must be unique)."""
    root = root.resolve()
    if not root.is_dir():
        return {}

    clear_index_warnings()
    by_id: dict[str, InstructionRecord] = {}
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        if not is_path_under_root(path, root):
            log.warning("skipped_path_outside_root path=%s", path)
            _record_index_warning("SKIPPED_PATH_OUTSIDE_ROOT", str(path))
            continue
        try:
            st = path.stat()
        except OSError as exc:
            log.warning("skipped_unreadable path=%s error=%s", path, exc)
            _record_index_warning("SKIPPED_UNREADABLE", str(path), {"reason": str(exc)})
            continue
        if st.st_size > MAX_INSTRUCTION_FILE_BYTES:
            log.warning(
                "skipped_large_file path=%s bytes=%s max=%s",
                path,
                st.st_size,
                MAX_INSTRUCTION_FILE_BYTES,
            )
            _record_index_warning(
                "SKIPPED_LARGE_FILE",
                str(path.relative_to(root)).replace("\\", "/"),
                {"size_bytes": st.st_size, "max_size_bytes": MAX_INSTRUCTION_FILE_BYTES},
            )
            continue
        try:
            rec = _parse_markdown(path, root)
        except OSError as exc:
            log.warning("skipped_read_error path=%s error=%s", path, exc)
            _record_index_warning("SKIPPED_READ_ERROR", str(path), {"reason": str(exc)})
            continue
        if rec.id in by_id:
            msg = f"Duplicate instruction id {rec.id!r}: {by_id[rec.id].rel_path} vs {rec.rel_path}"
            raise ValueError(msg)
        by_id[rec.id] = rec
    log.info(
        "index_built root=%s count=%s max_file_bytes=%s",
        root,
        len(by_id),
        MAX_INSTRUCTION_FILE_BYTES,
    )
    return by_id


def _load_synonyms_from_file() -> dict[str, list[str]]:
    file_path = Path(__file__).with_name("synonyms.yaml")
    if not file_path.exists():
        return dict(DEFAULT_SYNONYMS)
    try:
        loaded = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return dict(DEFAULT_SYNONYMS)
    if not isinstance(loaded, dict):
        return dict(DEFAULT_SYNONYMS)
    out: dict[str, list[str]] = {}
    for key, values in loaded.items():
        if not isinstance(key, str):
            continue
        normalized_key = _normalize_token(key)
        if isinstance(values, dict):
            values = values.get("terms", [])
        if not isinstance(values, list):
            continue
        cleaned = []
        for value in values:
            if not isinstance(value, str):
                continue
            cleaned.append(_normalize_token(value))
        out[normalized_key] = sorted({v for v in cleaned if v})
    return out or dict(DEFAULT_SYNONYMS)


def _build_synonym_lookup(synonyms: dict[str, list[str]]) -> dict[str, list[str]]:
    lookup: dict[str, set[str]] = {}
    for canonical, related in synonyms.items():
        terms = [canonical, *related]
        normalized_terms = {_normalize_token(term): _normalize_token(term) for term in terms}
        for term_norm in normalized_terms:
            others = {other for other_norm, other in normalized_terms.items() if other_norm != term_norm}
            if not others:
                continue
            lookup.setdefault(term_norm, set()).update(others)
    return {key: sorted(values) for key, values in lookup.items()}


SYNONYMS: dict[str, list[str]] = _load_synonyms_from_file()
_SYNONYM_LOOKUP = _build_synonym_lookup(SYNONYMS)


def extract_exact_phrases(query: str) -> list[str]:
    phrases: list[str] = []
    for raw in PHRASE_PATTERN.findall(query):
        normalized = _normalize_for_index(raw).strip()
        if normalized:
            phrases.append(normalized)
    return phrases


def tokenize_query(q: str) -> list[str]:
    lowered = _normalize_token(q)
    lowered = lowered.replace("/", " ").replace("\\", " ").replace("-", " ").replace("_", " ")
    tokens = [match.group(0) for match in TOKEN_PATTERN.finditer(lowered)]
    out: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for variant in _token_variants(token):
            if variant in seen:
                continue
            seen.add(variant)
            out.append(variant)
    return out


@dataclass(frozen=True)
class ExpandedQueryInfo:
    """Token expansion for telemetry (synonym map is weighted in scoring)."""

    weights: dict[str, float]
    user_tokens: list[str]
    terms_added_by_dictionary: list[str]
    expansion_truncated: bool
    synonym_expansion_count: int


def expand_query_with_synonyms(tokens: list[str]) -> dict[str, float]:
    info = expand_query_with_metadata(tokens)
    return info.weights


def expand_query_with_metadata(tokens: list[str]) -> ExpandedQueryInfo:
    normalized_tokens = [_normalize_token(token) for token in tokens]
    user_set: set[str] = set(tokens)
    user_set.update(normalized_tokens)
    expanded: dict[str, float] = {}
    expansion_truncated = False
    added: set[str] = set()
    synonym_expansion_count = 0
    for original, normalized in zip(tokens, normalized_tokens, strict=False):
        expanded[original] = max(expanded.get(original, 0.0), 1.0)
        expanded[normalized] = max(expanded.get(normalized, 0.0), 1.0)
        related_list = _SYNONYM_LOOKUP.get(normalized, [])
        if len(related_list) > EXPANSION_CAP_PER_TOKEN:
            expansion_truncated = True
        for related in related_list[:EXPANSION_CAP_PER_TOKEN]:
            synonym_expansion_count += 1
            if related not in user_set:
                added.add(related)
            expanded[related] = max(expanded.get(related, 0.0), 0.5)
    added_sorted = sorted(added)
    return ExpandedQueryInfo(
        weights=expanded,
        user_tokens=sorted(user_set),
        terms_added_by_dictionary=added_sorted,
        expansion_truncated=expansion_truncated,
        synonym_expansion_count=synonym_expansion_count,
    )


@dataclass(frozen=True)
class ScoreBreakdown:
    """Heuristic score split (same total semantics as legacy score_record)."""

    total: float
    score_title: float
    score_tags: float
    score_body_blob: float
    score_priority: float
    score_from_user_terms: float
    score_from_expansion_terms: float
    score_exact_phrase: float
    score_proximity: float


def _term_parts(rec: InstructionRecord, t: str, weight: float, blob: str, title_l: str) -> tuple[float, float, float]:
    c = _term_hit_count(blob, t)
    body_blob = weight * (1.0 + min(5.0, 0.25 * c)) if c else 0.0
    short_token = _requires_boundary_match(t)
    title_multiplier = 4.0 if short_token else 3.0
    tag_multiplier = 3.0 if short_token else 2.0
    title = weight * title_multiplier if _term_in_text(title_l, t) else 0.0
    tags = 0.0
    for tag in rec.tags:
        normalized_tag = _normalize_for_index(tag)
        if normalized_tag == t or _term_in_text(normalized_tag, t):
            tags += weight * tag_multiplier
    return body_blob, title, tags


def _passes_tags_filter(rec: InstructionRecord, tag_filter: set[str] | None, tags_mode: str) -> bool:
    if not tag_filter:
        return True
    rec_tags = set(rec.tags)
    if tags_mode == "all":
        return tag_filter.issubset(rec_tags)
    return bool(tag_filter & rec_tags)


def _count_exact_phrase_bonus(rec: InstructionRecord, exact_phrases: list[str]) -> float:
    if not exact_phrases:
        return 0.0
    text = _normalize_for_index(f"{rec.title}\n{rec.body}")
    title = _normalize_for_index(rec.title)
    score = 0.0
    for phrase in exact_phrases:
        if phrase in title:
            score += 2.5
        elif phrase in text:
            score += 1.5
    return score


def _proximity_bonus(rec: InstructionRecord, terms: list[str], window: int = 80) -> float:
    if len(terms) < 2:
        return 0.0
    body = _normalize_for_index(rec.body)
    positions: dict[str, list[int]] = {}
    for term in terms:
        start = 0
        pos_list: list[int] = []
        while True:
            idx = body.find(term, start)
            if idx < 0:
                break
            pos_list.append(idx)
            start = idx + len(term)
        if pos_list:
            positions[term] = pos_list
    if len(positions) < 2:
        return 0.0
    min_distance = None
    keys = list(positions.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            for p1 in positions[keys[i]]:
                for p2 in positions[keys[j]]:
                    d = abs(p1 - p2)
                    if min_distance is None or d < min_distance:
                        min_distance = d
    if min_distance is None or min_distance > window:
        return 0.0
    return 1.0 + (window - min_distance) / max(1.0, window)


def score_record_breakdown(
    rec: InstructionRecord,
    tokens: list[str],
    tag_filter: set[str] | None,
    expanded_info: ExpandedQueryInfo | None = None,
    *,
    tags_mode: str = "any",
    exact_phrases: list[str] | None = None,
    expansion_penalty_ratio: float = 1.0,
) -> ScoreBreakdown:
    if not _passes_tags_filter(rec, tag_filter, tags_mode):
        return ScoreBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    info = expanded_info if expanded_info is not None else expand_query_with_metadata(tokens)
    user_set = frozenset(info.user_tokens)

    blob = rec.search_blob()
    title_l = _normalize_for_index(rec.title)
    score_body = 0.0
    score_title = 0.0
    score_tags = 0.0
    from_user = 0.0
    from_exp = 0.0

    for t, weight in info.weights.items():
        normalized_term = _normalize_for_index(t)
        bp, tp, gp = _term_parts(rec, normalized_term, weight, blob, title_l)
        part = bp + tp + gp
        score_body += bp
        score_title += tp
        score_tags += gp
        if t in user_set:
            from_user += part
        else:
            from_exp += part

    pr = 0.5 * PRIORITY_RANK.get(rec.priority, 0) if (score_body + score_title + score_tags) > 0.0 else 0.0
    phrase_bonus = _count_exact_phrase_bonus(rec, exact_phrases or [])
    proximity = _proximity_bonus(rec, list(user_set))
    total = score_body + score_title + score_tags + pr + phrase_bonus + proximity
    if from_user <= 1e-9 and from_exp > 1e-9:
        total *= max(0.0, min(1.0, expansion_penalty_ratio))
    return ScoreBreakdown(
        total=total,
        score_title=score_title,
        score_tags=score_tags,
        score_body_blob=score_body,
        score_priority=pr,
        score_from_user_terms=from_user,
        score_from_expansion_terms=from_exp,
        score_exact_phrase=phrase_bonus,
        score_proximity=proximity,
    )


def score_record(
    rec: InstructionRecord,
    tokens: list[str],
    tag_filter: set[str] | None,
    *,
    tags_mode: str = "any",
    exact_phrases: list[str] | None = None,
    expansion_penalty_ratio: float = 1.0,
) -> float:
    return score_record_breakdown(
        rec,
        tokens,
        tag_filter,
        tags_mode=tags_mode,
        exact_phrases=exact_phrases,
        expansion_penalty_ratio=expansion_penalty_ratio,
    ).total


def terms_with_positive_hits(
    rec: InstructionRecord,
    expanded_info: ExpandedQueryInfo,
    tag_filter: set[str] | None,
    *,
    tags_mode: str = "any",
) -> tuple[set[str], set[str]]:
    """Terms that contributed non-zero score: (matched_user_terms, matched_dictionary_only_terms)."""
    if not _passes_tags_filter(rec, tag_filter, tags_mode):
        return set(), set()

    user_set = frozenset(expanded_info.user_tokens)
    blob = rec.search_blob()
    title_l = _normalize_for_index(rec.title)

    matched_user: set[str] = set()
    matched_dict_only: set[str] = set()

    for t, weight in expanded_info.weights.items():
        normalized_term = _normalize_for_index(t)
        bp, tp, gp = _term_parts(rec, normalized_term, weight, blob, title_l)
        if bp + tp + gp <= 0.0:
            continue
        if t in user_set:
            matched_user.add(t)
        else:
            matched_dict_only.add(t)
    return matched_user, matched_dict_only


def excerpt_around_match(body: str, tokens: list[str], max_len: int = 400) -> str:
    lower = _normalize_for_index(body)
    pos = -1
    for t in tokens:
        idx = lower.find(_normalize_for_index(t))
        if idx != -1:
            pos = idx
            break
    if pos == -1:
        snippet = body[:max_len]
    else:
        start = max(0, pos - max_len // 3)
        snippet = body[start : start + max_len]
    if len(snippet) >= max_len:
        snippet = snippet[: max_len - 3] + "..."
    return snippet.strip()


def summarize_body(body: str, limit: int = 200) -> str:
    one_line = " ".join(body.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."
