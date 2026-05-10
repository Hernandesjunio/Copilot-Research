"""Corpus Query Expansion Map — modular typed expansion (ADR-002)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

ALIAS_WEIGHT: float = 0.9
STRONG_WEIGHT: float = 0.7
WEAK_WEIGHT: float = 0.3


@dataclass(frozen=True)
class ContextRule:
    activation_terms: list[str]
    applies_to: list[str]
    terms: list[str]


@dataclass(frozen=True)
class ExpansionEntry:
    canonical: str
    aliases: list[str]
    strong_terms: list[str]
    weak_terms: list[str]
    applies_to: list[str]
    contexts: list[ContextRule]


@dataclass(frozen=True)
class ExpansionDomain:
    domain: str
    version: str
    source_file: str
    entries: list[ExpansionEntry]


@dataclass(frozen=True)
class ExpansionMap:
    domains: list[ExpansionDomain]
    disabled: bool


@dataclass(frozen=True)
class ExpansionCandidate:
    term: str
    weight: float
    relation: str
    source_domain: str
    source_file: str


@dataclass(frozen=True)
class ExpansionDiagnostic:
    canonical: str
    term: str
    relation: str
    weight: float
    source_domain: str
    source_file: str


@dataclass(frozen=True)
class SkippedEntryDiagnostic:
    canonical: str
    reason: str
    applies_to: list[str]
    current_file_path: str
    source_domain: str
    source_file: str


@dataclass(frozen=True)
class ContextConflictDiagnostic:
    canonical: str
    conflicting_context_indices: list[int]
    activation_signals: list[str]
    resolution: str = "agent_must_decide"


def _normalize_token(token: str) -> str:
    from corporate_instructions_mcp.indexing import _normalize_token as nt

    return nt(token)


def _path_matches_globs(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return True
    normalized = path.replace("\\", "/").lstrip("/")
    p = PurePosixPath(normalized)
    return any(p.match(pat) for pat in patterns)


def parse_domain_file(raw: dict, source: str) -> ExpansionDomain | None:
    """Parse YAML dict into ExpansionDomain; None if structurally invalid."""
    if not isinstance(raw, dict):
        log.warning("parse_domain_file_invalid_root source=%s", source)
        return None
    domain = raw.get("domain")
    if not isinstance(domain, str) or not domain.strip():
        log.warning("parse_domain_file_missing_domain source=%s", source)
        return None
    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, list):
        log.warning("parse_domain_file_missing_entries source=%s", source)
        return None

    version = raw.get("version")
    version_str = str(version).strip() if version is not None else ""
    if not version_str:
        version_str = "1"

    entries: list[ExpansionEntry] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        canon_raw = item.get("canonical")
        if not isinstance(canon_raw, str) or not canon_raw.strip():
            log.warning("parse_domain_file_skip_entry_no_canonical source=%s", source)
            continue

        aliases_in = item.get("aliases") if isinstance(item.get("aliases"), list) else []
        strong_in = item.get("strong_terms") if isinstance(item.get("strong_terms"), list) else []
        weak_in = item.get("weak_terms") if isinstance(item.get("weak_terms"), list) else []
        ctx_in = item.get("contexts") if isinstance(item.get("contexts"), list) else []
        applies_entry = item.get("applies_to") if isinstance(item.get("applies_to"), list) else []

        aliases = [_normalize_token(str(a)) for a in aliases_in if isinstance(a, str)]
        strong_terms = [_normalize_token(str(a)) for a in strong_in if isinstance(a, str)]
        weak_terms = [_normalize_token(str(a)) for a in weak_in if isinstance(a, str)]
        applies_to = [str(a) for a in applies_entry if isinstance(a, str)]

        contexts: list[ContextRule] = []
        for ctx_item in ctx_in:
            if not isinstance(ctx_item, dict):
                continue
            act_raw = ctx_item.get("activation_terms") if isinstance(ctx_item.get("activation_terms"), list) else []
            app_raw = ctx_item.get("applies_to") if isinstance(ctx_item.get("applies_to"), list) else []
            terms_raw = ctx_item.get("terms") if isinstance(ctx_item.get("terms"), list) else []
            activation_terms = [_normalize_token(str(a)) for a in act_raw if isinstance(a, str)]
            applies_ctx = [str(a) for a in app_raw if isinstance(a, str)]
            terms = [_normalize_token(str(a)) for a in terms_raw if isinstance(a, str)]

            if terms and not activation_terms and not applies_ctx:
                log.warning(
                    "parse_domain_file_discard_context_no_activation source=%s canonical=%s",
                    source,
                    _normalize_token(canon_raw),
                )
                continue

            contexts.append(
                ContextRule(
                    activation_terms=activation_terms,
                    applies_to=applies_ctx,
                    terms=terms,
                )
            )

        entries.append(
            ExpansionEntry(
                canonical=_normalize_token(canon_raw),
                aliases=aliases,
                strong_terms=strong_terms,
                weak_terms=weak_terms,
                applies_to=applies_to,
                contexts=contexts,
            )
        )

    return ExpansionDomain(
        domain=str(domain).strip(),
        version=version_str,
        source_file=source,
        entries=entries,
    )


def load_corpus_expansion_map(corpus_root: Path) -> ExpansionMap:
    """Load all *.yaml under corpus_root/metadata/corpus-query-expansion-map/."""
    map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
    valid_domains: list[ExpansionDomain] = []

    try:
        if not map_dir.is_dir():
            return ExpansionMap(domains=[], disabled=True)
    except OSError as exc:
        log.warning("load_corpus_expansion_map_dir_stat_failed path=%s error=%s", map_dir, exc)
        return ExpansionMap(domains=[], disabled=True)

    try:
        yaml_files = sorted(map_dir.glob("*.yaml"))
    except OSError as exc:
        log.warning("load_corpus_expansion_map_glob_failed path=%s error=%s", map_dir, exc)
        return ExpansionMap(domains=[], disabled=True)

    if not yaml_files:
        return ExpansionMap(domains=[], disabled=True)

    for ypath in yaml_files:
        try:
            text = ypath.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("load_corpus_expansion_map_read_failed path=%s error=%s", ypath, exc)
            continue
        try:
            loaded = yaml.safe_load(text)
        except (OSError, yaml.YAMLError) as exc:
            log.warning("load_corpus_expansion_map_yaml_failed path=%s error=%s", ypath, exc)
            continue
        domain_obj = parse_domain_file(loaded if isinstance(loaded, dict) else {}, source=ypath.name)
        if domain_obj is None:
            log.warning("load_corpus_expansion_map_parse_none path=%s", ypath)
            continue
        valid_domains.append(domain_obj)

    disabled = len(valid_domains) == 0
    return ExpansionMap(domains=valid_domains, disabled=disabled)


def _candidate_from(
    term: str,
    weight: float,
    relation: str,
    source_domain: str,
    source_file: str,
) -> ExpansionCandidate:
    return ExpansionCandidate(
        term=term,
        weight=weight,
        relation=relation,
        source_domain=source_domain,
        source_file=source_file,
    )


def _merge_candidate_map(
    into: dict[str, ExpansionCandidate],
    cand: ExpansionCandidate,
) -> None:
    prev = into.get(cand.term)
    if prev is None or cand.weight > prev.weight:
        into[cand.term] = cand


def build_unidirectional_lookup(
    expansion_map: ExpansionMap,
) -> dict[str, list[ExpansionCandidate]]:
    if expansion_map.disabled:
        return {}

    lookup: dict[str, dict[str, ExpansionCandidate]] = {}

    for domain in expansion_map.domains:
        for entry in domain.entries:
            key = entry.canonical
            bucket = lookup.setdefault(key, {})
            for term in entry.aliases:
                _merge_candidate_map(
                    bucket,
                    _candidate_from(term, ALIAS_WEIGHT, "alias", domain.domain, domain.source_file),
                )
            for term in entry.strong_terms:
                _merge_candidate_map(
                    bucket,
                    _candidate_from(term, STRONG_WEIGHT, "strong", domain.domain, domain.source_file),
                )
            for term in entry.weak_terms:
                _merge_candidate_map(
                    bucket,
                    _candidate_from(term, WEAK_WEIGHT, "weak", domain.domain, domain.source_file),
                )

    return {k: list(inner.values()) for k, inner in lookup.items()}


def context_is_active(
    ctx: ContextRule,
    query_terms_normalized: set[str],
    current_file_path: str | None,
) -> bool:
    """Whether a ContextRule is active given query tokens and optional path."""
    has_act = bool(ctx.activation_terms)
    has_app = bool(ctx.applies_to)
    norm_act = set(ctx.activation_terms)
    act_match = bool(norm_act & query_terms_normalized)

    if has_act and has_app:
        app_match = bool(current_file_path) and _path_matches_globs(current_file_path, ctx.applies_to)
        return act_match and app_match
    if has_act:
        return act_match
    if has_app:
        return bool(current_file_path) and _path_matches_globs(current_file_path, ctx.applies_to)
    return False


def collect_entry_expansion(
    domain: ExpansionDomain,
    entry: ExpansionEntry,
    current_file_path: str | None,
    query_terms_normalized: set[str],
) -> tuple[list[ExpansionCandidate], SkippedEntryDiagnostic | None, ContextConflictDiagnostic | None]:
    """Candidates from one entry, optional skip/conlict diagnostics."""
    if entry.applies_to:
        if current_file_path is not None:
            if not _path_matches_globs(current_file_path, entry.applies_to):
                skip = SkippedEntryDiagnostic(
                    canonical=entry.canonical,
                    reason="skipped_by_applies_to",
                    applies_to=list(entry.applies_to),
                    current_file_path=current_file_path,
                    source_domain=domain.domain,
                    source_file=domain.source_file,
                )
                return [], skip, None

    active_ctx_indices: list[int] = []
    signals: list[str] = []
    for i, ctx in enumerate(entry.contexts):
        if context_is_active(ctx, query_terms_normalized, current_file_path):
            active_ctx_indices.append(i)
            overlap = sorted(set(ctx.activation_terms) & query_terms_normalized)
            signals.append(f"ctx{i}:{'+'.join(overlap) if overlap else 'applies_to'}")

    conflict: ContextConflictDiagnostic | None = None
    if len(active_ctx_indices) >= 2:
        conflict = ContextConflictDiagnostic(
            canonical=entry.canonical,
            conflicting_context_indices=active_ctx_indices,
            activation_signals=signals,
        )

    merged: dict[str, ExpansionCandidate] = {}
    for term in entry.aliases:
        _merge_candidate_map(
            merged,
            _candidate_from(term, ALIAS_WEIGHT, "alias", domain.domain, domain.source_file),
        )
    for term in entry.strong_terms:
        _merge_candidate_map(
            merged,
            _candidate_from(term, STRONG_WEIGHT, "strong", domain.domain, domain.source_file),
        )
    for term in entry.weak_terms:
        _merge_candidate_map(
            merged,
            _candidate_from(term, WEAK_WEIGHT, "weak", domain.domain, domain.source_file),
        )

    return list(merged.values()), None, conflict
