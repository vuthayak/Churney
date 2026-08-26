"""Atomic JSON emission to data/cards/<slug>.json (docs/04 §9.2)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from churney.models import CardFile


def card_file_path(out_dir: Path, slug: str) -> Path:
    return Path(out_dir) / "cards" / f"{slug}.json"


def emit(card_file: CardFile, out_dir: Path) -> Path:
    """Validate (pydantic re-check happens at model construction) and write.

    Atomic write: temp file + rename so a crash never leaves a half-written
    versioned artifact.
    """
    path = card_file_path(out_dir, card_file.card.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = card_file.model_dump_json(indent=2, exclude_none=True)
    fd = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    )
    try:
        with fd as f:
            f.write(payload)
            f.write("\n")
        Path(fd.name).replace(path)
    except BaseException:
        Path(fd.name).unlink(missing_ok=True)
        raise
    return path


def load_card_file(path: Path) -> CardFile:
    return CardFile.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


_VOLATILE_KEYS = {"verified_at", "seen_on", "valid_from", "source_url", "page_url"}


def _strip_volatile(node):
    """Remove fields that legitimately change between runs without the underlying
    facts changing (timestamps, effective-date stamps, URL restatements)."""
    if isinstance(node, dict):
        return {
            k: _strip_volatile(v)
            for k, v in node.items()
            if k not in _VOLATILE_KEYS and k != "content_hash"
        }
    if isinstance(node, list):
        return [_strip_volatile(v) for v in node]
    return node


def semantic_dict(card_file: CardFile) -> dict:
    """Data-only view of a CardFile for change detection."""
    return _strip_volatile(card_file.model_dump(exclude_none=True))
