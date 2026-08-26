"""Generate the static UI data bundle from emitted card JSON files.

Writes ui/cards.js (window.CHURNEY_DATA = {...}) so the viewer works from
file:// without any server or build step.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from churney.emit import load_card_file

PIPELINE_DIR = Path(__file__).resolve().parent.parent


def build(cards_dir: Path | None = None, out_dir: Path | None = None) -> Path:
    cards_dir = cards_dir or PIPELINE_DIR / "data" / "cards"
    out_dir = out_dir or PIPELINE_DIR / "ui"
    out_dir.mkdir(parents=True, exist_ok=True)

    cards = []
    for f in sorted(Path(cards_dir).glob("*.json")):
        try:
            cf = load_card_file(f)
        except Exception as e:  # noqa: BLE001 - skip corrupt file, keep building
            print(f"skip {f.name}: {e}", file=__import__("sys").stderr)
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        d["file"] = f.name
        cards.append(d)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(cards),
        "cards": cards,
    }
    target = out_dir / "cards.js"
    target.write_text(
        "window.CHURNEY_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {target} ({len(cards)} cards)")
    return target
