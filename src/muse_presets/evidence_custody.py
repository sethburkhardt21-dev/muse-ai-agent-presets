"""Portable, local-only Evidence Finder custody using the public source finder.

A general-purpose stdlib implementation, not a copy of any private
specialist engine. Exact original UTF-8 findings are retained in a
role-labelled SQLite chain; a no-hit is recorded without inventing text.

SECURITY BOUNDARY: SHA-256 proves local byte consistency, NOT origin,
identity, immutable history, source truth, authorization, or a signed
independent witness. Caller-supplied role IDs are labels, not grants.
No network, LLM, Muse host integration, remote send, verdict or worker.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import stat

from .finder import find_exact_text

ROLES = (
    "coordinator", "software-engineer", "model-builder",
    "research-evaluator", "creative-studio", "adversarial-verifier",
    "personal-companion", "garden-companion", "learning-coach",
    "claims-adjudicator", "reverse-engineering-researcher",
    "evidence-finder",
)
SCHEMA = "muse-presets/local-evidence-custody-v1"
ZERO = "0" * 64
OP = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _refuse(code: str) -> None:
    raise ValueError(code)


def _check_operation(operation_id: str) -> None:
    if not isinstance(operation_id, str) or not OP.fullmatch(operation_id):
        _refuse("INVALID_OPERATION_ID")


class EvidenceLedger:
    """Explicit, source-bound local receipt store; never a host authority."""

    def __init__(self, state_root: Path, *, role_id: str):
        if role_id not in ROLES:
            _refuse("ROLE_NOT_ALLOWED")
        root = Path(state_root)
        if root.is_symlink() or not root.is_dir():
            _refuse("INVALID_STATE_ROOT")
        self._root = root
        self.role_id = role_id

    def _database(self, create: bool) -> Path | None:
        namespace = self._root / self.role_id
        if namespace.is_symlink():
            _refuse("STATE_SYMLINK_REFUSED")
        if not namespace.exists():
            if not create:
                return None
            namespace.mkdir(mode=0o700, exist_ok=True)
        if namespace.is_symlink() or not namespace.is_dir():
            _refuse("INVALID_STATE_NAMESPACE")
        db = namespace / "receipts.sqlite3"
        if db.is_symlink():
            _refuse("STATE_SYMLINK_REFUSED")
        if db.exists() and not stat.S_ISREG(db.lstat().st_mode):
            _refuse("INVALID_STATE_DATABASE")
        if not create and not db.exists():
            return None
        return db

    def _open(self, *, create: bool):
        db = self._database(create)
        if db is None:
            return None
        conn = sqlite3.connect(db, timeout=8, isolation_level=None)
        conn.execute("PRAGMA trusted_schema=OFF")
        conn.execute("PRAGMA busy_timeout=8000")
        conn.execute("BEGIN IMMEDIATE")
        if create:
            conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                "seq INTEGER PRIMARY KEY, operation_id TEXT UNIQUE NOT NULL,"
                "payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL,"
                "previous_chain_sha256 TEXT NOT NULL, chain_sha256 TEXT NOT NULL)"
            )
            if conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0] == 0:
                conn.executemany("INSERT INTO meta(key,value) VALUES (?,?)", (
                    ("schema", SCHEMA), ("role_id", self.role_id),
                    ("count", "0"), ("head", ZERO),
                ))
        return conn

    def _verify_rows(self, conn):
        try:
            meta = dict(conn.execute("SELECT key,value FROM meta").fetchall())
            rows = conn.execute(
                "SELECT seq,operation_id,payload,payload_sha256,"
                "previous_chain_sha256,chain_sha256 FROM entries ORDER BY seq"
            ).fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError("RECEIPT_CHAIN_INVALID") from exc
        if meta.get("role_id") != self.role_id:
            _refuse("ROLE_LEDGER_MISMATCH")
        if set(meta) != {"schema", "role_id", "count", "head"} or meta["schema"] != SCHEMA:
            _refuse("RECEIPT_CHAIN_INVALID")
        if len(rows) > 10000:
            _refuse("RECEIPT_CHAIN_INVALID")
        previous = ZERO
        for expected, row in enumerate(rows, start=1):
            seq, op, data, payload_digest, prior, chain = row
            if seq != expected or not isinstance(op, str) or not OP.fullmatch(op):
                _refuse("RECEIPT_CHAIN_INVALID")
            try:
                item = json.loads(data)
                if _canonical(item) != data or set(item) != {
                    "schema", "role_id", "operation_id", "source_uri",
                    "source_sha256", "query", "outcome", "source_text",
                }:
                    _refuse("RECEIPT_CHAIN_INVALID")
                if (item["schema"] != SCHEMA or item["role_id"] != self.role_id
                        or item["operation_id"] != op
                        or item["outcome"] not in ("FINDING", "NOTHING_FOUND")
                        or not re.fullmatch(r"[0-9a-f]{64}", item["source_sha256"])):
                    _refuse("RECEIPT_CHAIN_INVALID")
                if item["outcome"] == "FINDING":
                    if (not isinstance(item["source_text"], str)
                            or _sha(item["source_text"].encode("utf-8"))
                            != item["source_sha256"]):
                        _refuse("RECEIPT_CHAIN_INVALID")
                elif item["source_text"] is not None:
                    _refuse("RECEIPT_CHAIN_INVALID")
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError("RECEIPT_CHAIN_INVALID") from exc
            if (_sha(data.encode("utf-8")) != payload_digest or prior != previous
                    or _sha((previous + ":" + payload_digest).encode("ascii")) != chain):
                _refuse("RECEIPT_CHAIN_INVALID")
            previous = chain
        if meta["count"] != str(len(rows)) or meta["head"] != previous:
            _refuse("RECEIPT_CHAIN_INVALID")
        return rows, previous

    @staticmethod
    def _receipt(row):
        return {
            "sequence": row[0], "payload_sha256": row[3],
            "previous_chain_sha256": row[4], "chain_sha256": row[5],
            "signature_authenticated": False,
            "external_anchor_verified": False,
        }

    def _response(self, row, status):
        payload = json.loads(row[2])
        found = payload["outcome"] == "FINDING"
        return {
            "schema": SCHEMA,
            "status": status,
            "role_id": self.role_id,
            "outcome": payload["outcome"],
            "source_uri": payload["source_uri"],
            "source_sha256": payload["source_sha256"],
            "finding": (
                {"text": payload["source_text"], "source_sha256": payload["source_sha256"]}
                if found else None
            ),
            "receipt": self._receipt(row),
            "source_bytes_verified_locally": found,
            "source_owner_authenticated": False,
            "host_principal_verified": False,
            "native_muse_invoked": False,
            "external_effect_performed": False,
        }

    def record(
        self, *, operation_id: str, source_root: Path,
        relative_path: str, query: str,
    ) -> dict:
        """Record source-backed, literal lookup; explicit local write only."""
        _check_operation(operation_id)
        observation = find_exact_text(Path(source_root), relative_path, query)
        found = observation["result"] == "FOUND"
        item = {
            "schema": SCHEMA, "role_id": self.role_id,
            "operation_id": operation_id,
            "source_uri": observation["source_uri"],
            "source_sha256": observation["source_sha256"],
            "query": query,
            "outcome": "FINDING" if found else "NOTHING_FOUND",
            "source_text": observation["observation"] if found else None,
        }
        encoded = _canonical(item)
        payload_digest = _sha(encoded.encode("utf-8"))
        conn = self._open(create=True)
        assert conn is not None
        with closing(conn):
            try:
                rows, head = self._verify_rows(conn)
                for row in rows:
                    if row[1] == operation_id:
                        if row[2] != encoded:
                            _refuse("OPERATION_CONFLICT")
                        conn.execute("COMMIT")
                        return self._response(row, "LOCAL_RECEIPT_PRESERVED")
                seq = len(rows) + 1
                chain = _sha((head + ":" + payload_digest).encode("ascii"))
                conn.execute(
                    "INSERT INTO entries VALUES(?,?,?,?,?,?)",
                    (seq, operation_id, encoded, payload_digest, head, chain),
                )
                conn.execute("UPDATE meta SET value=? WHERE key='count'", (str(seq),))
                conn.execute("UPDATE meta SET value=? WHERE key='head'", (chain,))
                conn.execute("COMMIT")
                return self._response(
                    (seq, operation_id, encoded, payload_digest, head, chain),
                    "LOCAL_RECEIPT_RECORDED",
                )
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def read(self, operation_id: str) -> dict:
        """Reopen verified exact original finding without accessing source."""
        _check_operation(operation_id)
        conn = self._open(create=False)
        if conn is None:
            _refuse("OPERATION_NOT_FOUND")
        with closing(conn):
            try:
                rows, _ = self._verify_rows(conn)
                for row in rows:
                    if row[1] == operation_id:
                        conn.execute("COMMIT")
                        return self._response(row, "LOCAL_RECEIPT_REOPENED")
                conn.execute("COMMIT")
                _refuse("OPERATION_NOT_FOUND")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def verify(self) -> dict:
        """Local hash-chain verification. NOT an anti-rollback signature."""
        conn = self._open(create=False)
        if conn is None:
            count, head, exists = 0, ZERO, False
        else:
            with closing(conn):
                try:
                    rows, head = self._verify_rows(conn)
                    count, exists = len(rows), True
                    conn.execute("COMMIT")
                except BaseException:
                    if conn.in_transaction:
                        conn.execute("ROLLBACK")
                    raise
        return {
            "schema": SCHEMA,
            "role_id": self.role_id,
            "receipt_count": count,
            "head_chain_sha256": head,
            "ledger_exists": exists,
            "local_chain_verified": True,
            "external_anchor_verified": False,
            "host_principal_verified": False,
            "native_muse_invoked": False,
            "external_effect_performed": False,
        }
