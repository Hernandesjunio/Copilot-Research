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

# Defensive limits (OWASP-style abuse of CPU/memory via corpus).
MAX_INSTRUCTION_FILE_BYTES = 5 * 1024 * 1024
MAX_FRONTMATTER_SECTION_CHARS = 65536

log = logging.getLogger(__name__)


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
        return f"{self.title}\n{' '.join(self.tags)}\n{self.body}".lower()


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
            meta = {}
        else:
            try:
                loaded = yaml.safe_load(fm_raw)
                meta = loaded if isinstance(loaded, dict) else {}
            except yaml.YAMLError:
                meta = {}
        body = parts[2].lstrip("\n")

    doc_id = str(meta.get("id") or _slug_from_path(path))
    title = str(meta.get("title") or path.stem)
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(t).lower() for t in tags]
    scope = meta.get("scope")
    scope = str(scope) if scope is not None else None
    priority = meta.get("priority")
    priority = str(priority).lower() if priority is not None else None
    kind = meta.get("kind")
    kind = str(kind).lower() if kind is not None else None

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
    """Load all ``*.md`` under ``root`` (recursive). Keys are document ids (must be unique).

    Skips files outside ``root`` after resolution (symlink escapes), files larger than
    :data:`MAX_INSTRUCTION_FILE_BYTES`, and unreadable paths.
    """
    root = root.resolve()
    if not root.is_dir():
        return {}

    by_id: dict[str, InstructionRecord] = {}
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        if not is_path_under_root(path, root):
            log.warning("skipped_path_outside_root path=%s", path)
            continue
        try:
            st = path.stat()
        except OSError as exc:
            log.warning("skipped_unreadable path=%s error=%s", path, exc)
            continue
        if st.st_size > MAX_INSTRUCTION_FILE_BYTES:
            log.warning(
                "skipped_large_file path=%s bytes=%s max=%s",
                path,
                st.st_size,
                MAX_INSTRUCTION_FILE_BYTES,
            )
            continue
        try:
            rec = _parse_markdown(path, root)
        except OSError as exc:
            log.warning("skipped_read_error path=%s error=%s", path, exc)
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


def tokenize_query(q: str) -> list[str]:
    return [t for t in re.split(r"\W+", q.lower()) if len(t) > 1]


PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1, None: 0}

SYNONYMS: dict[str, list[str]] = {
    "cache": ["imemorycache", "idistributedcache", "caching", "ttl", "invalidation"],
    "persistencia": ["dapper", "sql", "repositorio", "data-access", "query"],
    "validacao": ["validation", "error-contracts", "400", "422"],
    "http": ["rest", "status-codes", "get", "put", "post", "delete", "endpoint"],
    "resiliencia": ["polly", "retry", "circuit-breaker", "timeout", "tolerancia"],
    "arquitetura": ["layering", "camadas", "clean-architecture", "solid"],
    "testes": ["testing", "unit", "integration", "contract"],
    "observabilidade": ["opentelemetry", "health", "correlation", "tracing"],
    "mensageria": ["rabbitmq", "messaging", "publish", "consume"],
    "seguranca": ["security", "secrets", "tokens"],
}


def _normalize_token(token: str) -> str:
    normalized = unicodedata.normalize("NFKD", token)
    no_diacritics = "".join(c for c in normalized if not unicodedata.combining(c))
    return no_diacritics.lower()


def _build_synonym_lookup(synonyms: dict[str, list[str]]) -> dict[str, list[str]]:
    lookup: dict[str, set[str]] = {}
    for canonical, related in synonyms.items():
        terms = [canonical, *related]
        normalized_terms = {_normalize_token(term): term for term in terms}
        for term_norm in normalized_terms:
            others = {other for other_norm, other in normalized_terms.items() if other_norm != term_norm}
            if not others:
                continue
            lookup.setdefault(term_norm, set()).update(others)
    return {key: sorted(values) for key, values in lookup.items()}


_SYNONYM_LOOKUP = _build_synonym_lookup(SYNONYMS)

EXPANSION_CAP_PER_TOKEN = 5


@dataclass(frozen=True)
class ExpandedQueryInfo:
    """Token expansion for telemetry (synonym map is weighted in scoring)."""

    weights: dict[str, float]
    user_tokens: list[str]
    terms_added_by_dictionary: list[str]
    expansion_truncated: bool
    synonym_expansion_count: int


def expand_query_with_synonyms(tokens: list[str]) -> dict[str, float]:
    """Expand query tokens with related terms weighted lower than direct matches."""
    info = expand_query_with_metadata(tokens)
    return info.weights


def expand_query_with_metadata(tokens: list[str]) -> ExpandedQueryInfo:
    """Like expand_query_with_synonyms plus telemetry on dictionary terms and truncation."""
    user_set = frozenset(tokens)
    expanded: dict[str, float] = {}
    expansion_truncated = False
    added: set[str] = set()
    synonym_expansion_count = 0
    for token in tokens:
        expanded[token] = max(expanded.get(token, 0.0), 1.0)
        normalized = _normalize_token(token)
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
        user_tokens=list(tokens),
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


def _term_parts(rec: InstructionRecord, t: str, weight: float, blob: str, title_l: str) -> tuple[float, float, float]:
    """Returns body_blob, title, tags contribution for one term."""
    c = blob.count(t)
    body_blob = weight * (1.0 + min(5.0, 0.25 * c)) if c else 0.0
    title = weight * 3.0 if t in title_l else 0.0
    tags = 0.0
    for tag in rec.tags:
        if t == tag or t in tag:
            tags += weight * 2.0
    return body_blob, title, tags


def score_record_breakdown(
    rec: InstructionRecord,
    tokens: list[str],
    tag_filter: set[str] | None,
    expanded_info: ExpandedQueryInfo | None = None,
) -> ScoreBreakdown:
    """Per-document score with component and user vs synonym expansion split."""
    if tag_filter and not (tag_filter & set(rec.tags)):
        return ScoreBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    info = expanded_info if expanded_info is not None else expand_query_with_metadata(tokens)
    user_set = frozenset(info.user_tokens)

    blob = rec.search_blob()
    title_l = rec.title.lower()
    score_body = 0.0
    score_title = 0.0
    score_tags = 0.0
    from_user = 0.0
    from_exp = 0.0

    for t, weight in info.weights.items():
        bp, tp, gp = _term_parts(rec, t, weight, blob, title_l)
        part = bp + tp + gp
        score_body += bp
        score_title += tp
        score_tags += gp
        if t in user_set:
            from_user += part
        else:
            from_exp += part

    pr = 0.5 * PRIORITY_RANK.get(rec.priority, 0)
    total = score_body + score_title + score_tags + pr
    return ScoreBreakdown(
        total=total,
        score_title=score_title,
        score_tags=score_tags,
        score_body_blob=score_body,
        score_priority=pr,
        score_from_user_terms=from_user,
        score_from_expansion_terms=from_exp,
    )


def score_record(rec: InstructionRecord, tokens: list[str], tag_filter: set[str] | None) -> float:
    return score_record_breakdown(rec, tokens, tag_filter).total


def terms_with_positive_hits(
    rec: InstructionRecord,
    expanded_info: ExpandedQueryInfo,
    tag_filter: set[str] | None,
) -> tuple[set[str], set[str]]:
    """Terms that contributed non-zero score: (matched_user_terms, matched_dictionary_only_terms)."""
    if tag_filter and not (tag_filter & set(rec.tags)):
        return set(), set()

    user_set = frozenset(expanded_info.user_tokens)
    blob = rec.search_blob()
    title_l = rec.title.lower()

    matched_user: set[str] = set()
    matched_dict_only: set[str] = set()

    for t, weight in expanded_info.weights.items():
        bp, tp, gp = _term_parts(rec, t, weight, blob, title_l)
        if bp + tp + gp <= 0.0:
            continue
        if t in user_set:
            matched_user.add(t)
        else:
            matched_dict_only.add(t)
    return matched_user, matched_dict_only


def excerpt_around_match(body: str, tokens: list[str], max_len: int = 400) -> str:
    lower = body.lower()
    pos = -1
    for t in tokens:
        idx = lower.find(t)
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
