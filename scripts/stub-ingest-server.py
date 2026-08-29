#!/usr/bin/env python3
"""Phase 0.1 spike: minimal ingest stub for iOS Shortcut testing.

Accepts POST /api/v1/ingest/transactions per docs/specs/01-spend-tracking.md §2.1.
Logs each payload to logs/ingest/ for offline analysis. Not for production use.

Usage:
    python3 scripts/stub-ingest-server.py [--port 8787] [--log-dir logs/ingest]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

INGEST_PATH = "/api/v1/ingest/transactions"
REQUIRED_FIELDS = ("idempotency_key", "amount_minor", "currency", "occurred_at")

# In-memory idempotency store (spike only; resets on restart).
_seen_keys: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_payload(body: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in body:
            errors.append(f"missing required field: {field}")
    if "amount_minor" in body and not isinstance(body["amount_minor"], int):
        errors.append("amount_minor must be an integer (minor units)")
    if "merchant" in body and body["merchant"] is not None and not isinstance(
        body["merchant"], str
    ):
        errors.append("merchant must be a string or null")
    return errors


def _append_log(log_dir: Path, record: dict[str, Any]) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = log_dir / f"ingest-{day}.jsonl"
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_file


class IngestHandler(BaseHTTPRequestHandler):
    log_dir: Path = Path("logs/ingest")

    def log_message(self, format: str, *args: Any) -> None:
        # Quieter default; payloads are logged to file instead.
        sys.stderr.write(f"[{_utc_now_iso()}] {self.address_string()} {format % args}\n")

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "churney-stub-ingest",
                    "ingest_path": INGEST_PATH,
                    "logged_payloads": len(_seen_keys),
                },
            )
            return
        self._send_json(404, {"error": {"code": "not_found", "message": "unknown path"}})

    def do_POST(self) -> None:
        if self.path != INGEST_PATH:
            self._send_json(404, {"error": {"code": "not_found", "message": "unknown path"}})
            return

        auth = self.headers.get("Authorization", "")
        if auth and not auth.startswith("Bearer "):
            self._send_json(
                401,
                {"error": {"code": "unauthorized", "message": "Bearer token required"}},
            )
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                400,
                {"error": {"code": "invalid_json", "message": "request body must be JSON"}},
            )
            return

        if not isinstance(body, dict):
            self._send_json(
                400,
                {"error": {"code": "invalid_body", "message": "JSON object expected"}},
            )
            return

        errors = _validate_payload(body)
        if errors:
            self._send_json(
                400,
                {"error": {"code": "validation_error", "message": "; ".join(errors)}},
            )
            return

        key = str(body["idempotency_key"])
        received_at = _utc_now_iso()
        log_record = {
            "received_at": received_at,
            "remote_addr": self.client_address[0],
            "authorization_present": bool(auth),
            "payload": body,
        }

        if key in _seen_keys:
            log_record["duplicate"] = True
            _append_log(self.log_dir, log_record)
            self._send_json(
                200,
                {
                    "status": "duplicate",
                    "idempotency_key": key,
                    "original_received_at": _seen_keys[key]["received_at"],
                    "transaction_id": _seen_keys[key]["transaction_id"],
                },
            )
            return

        transaction_id = f"stub_txn_{uuid4().hex[:12]}"
        _seen_keys[key] = {"received_at": received_at, "transaction_id": transaction_id}
        log_record["transaction_id"] = transaction_id
        log_file = _append_log(self.log_dir, log_record)

        self._send_json(
            201,
            {
                "status": "accepted",
                "transaction_id": transaction_id,
                "idempotency_key": key,
                "log_file": str(log_file),
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Churney Phase 0.1 stub ingest server")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8787, help="listen port (default: 8787)")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "logs" / "ingest",
        help="directory for JSONL payload logs",
    )
    args = parser.parse_args()

    IngestHandler.log_dir = args.log_dir.resolve()
    server = ThreadingHTTPServer((args.host, args.port), IngestHandler)

    print(f"Churney stub ingest listening on http://{args.host}:{args.port}{INGEST_PATH}")
    print(f"Health check: http://127.0.0.1:{args.port}/health")
    print(f"Logging payloads to: {IngestHandler.log_dir}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
