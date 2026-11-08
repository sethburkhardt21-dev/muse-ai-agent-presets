"""Bounded, read-only privacy audit of the entire public source distribution.

Detects common secrets, local host paths, unsafe assets and filesystem links.
Outputs ONLY relative paths and categorical reasons, never matched values.
The private contributor/agent denylist is deliberately NOT shipped here:
a release operator may inject private names via forbidden_terms and must
also review the entire public Git history separately.

This is a heuristic source gate, not a license review, cryptographic source
attestation, complete PII detector, malware analysis or native Muse proof.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Only VCS internals and local tooling caches are outside the distribution.
_EXCLUDED_DIRS = frozenset((
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".venv", "venv",
))
_TEXT_SUFFIXES = frozenset((
    ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt",
    ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".jsx", ".html", ".css", ".xml", ".ini", ".cfg", ".rst",
))
_TEXT_NAMES = frozenset((
    "license", "makefile", "dockerfile", ".gitignore",
    ".gitattributes", ".editorconfig", ".dockerignore",
))
_SENSITIVE_NAMES = frozenset((
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "credentials.yml",
    "secrets.json", "secrets.yml", "token.json", "tokens.json",
    "auth.json", "service-account.json",
))
_SENSITIVE_SUFFIXES = frozenset((
    ".pem", ".p12", ".pfx", ".key", ".sqlite", ".sqlite3",
    ".db", ".bak", ".backup", ".log", ".p8", ".p7b",
    ".zip", ".tar", ".gz", ".7z", ".exe", ".dll", ".so",
    ".dylib", ".bin", ".wasm",
))
_PRIVATE_HOST_PATH = re.compile(
    r"(?i)(?:[a-z]:[\\/]Users[\\/][^\\/\s]+[\\/]|"
    r"/" + r"home/[^/\s]+/|/" + r"Users/[^/\s]+/)"
)
_POSSIBLE_SECRET = re.compile(
    r"(?i)(?:\bsk-(?:proj|live)-[A-Za-z0-9_-]{12,}\b|"
    r"\bAKIA[A-Z0-9]{16}\b|"
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|"
    r"\bgithub_pat_[A-Za-z0-9_]{25,}\b|"
    r"-----BEGIN (?:OPENSSH |RSA |EC |DSA |)PRIVATE KEY-----|"
    r"\bBearer[ \t]+[A-Za-z0-9_./+=:-]{32,}\b)"
)
_POSSIBLE_PASSWORD = re.compile(
    r"(?i)\b(?:api[_-]?key|client_secret|private_key|access_token|"
    r"auth_token|password)\s*[:=]\s*['\"][A-Za-z0-9_./+=:@-]{20,}['\"]"
)
_PERSONAL_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?!(?:example\.(?:com|org|net)|localhost)\b)"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.I
)
_MAX_BYTES = 2_000_000


def audit_public_tree(root: Path, *,
                      forbidden_terms: tuple[str, ...] = ()) -> list[dict[str, str]]:
    """Inspect every distributed file except .git and runtime caches.

    All findings contain a repository-relative path and fixed reason code.
    A caller's private forbidden_terms are never copied into these results
    or stored by the function. The caller must still audit Git history.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("INVALID_PUBLIC_ROOT")
    if len(forbidden_terms) > 128 or any(
        type(word) is not str or not 3 <= len(word) <= 128
        for word in forbidden_terms
    ):
        raise ValueError("INVALID_FORBIDDEN_TERMS")
    denied = tuple(
        re.compile(r"(?<![A-Za-z0-9])" + re.escape(word) +
                   r"(?![A-Za-z0-9])", re.I)
        for word in forbidden_terms
    )
    findings: list[dict[str, str]] = []
    def add(path: Path, reason: str) -> None:
        findings.append({"path":path.relative_to(root).as_posix(),
                         "reason":reason})

    for dirname, dirs, files in os.walk(root, topdown=True, followlinks=False):
        parent = Path(dirname)
        # Never inspect .git internals, or follow a directory symlink.
        for name in list(dirs):
            if name in _EXCLUDED_DIRS:
                dirs.remove(name)
                continue
            path = parent / name
            if path.is_symlink():
                add(path, "SYMLINK_REFUSED")
                dirs.remove(name)
        for name in files:
            # A Git linked-worktree .git pointer is VCS metadata, never a
            # distributable source file; exclude it like a .git directory.
            if name == ".git":
                continue
            path = parent / name
            if path.is_symlink():
                add(path, "SYMLINK_REFUSED")
                continue
            lowered = name.lower()
            if (lowered in _SENSITIVE_NAMES or lowered.startswith(".env.")
                or path.suffix.lower() in _SENSITIVE_SUFFIXES
                and path.suffix.lower() not in _TEXT_SUFFIXES):
                add(path, "SENSITIVE_FILE" if path.suffix.lower() in
                    {".sqlite", ".sqlite3", ".db", ".pem", ".p12", ".pfx", ".key",
                     ".bak", ".backup", ".log", ".p8", ".p7b"} or
                    lowered in _SENSITIVE_NAMES or lowered.startswith(".env.")
                    else "UNREVIEWED_BINARY_ASSET")
                continue
            if (path.suffix.lower() not in _TEXT_SUFFIXES and
                lowered not in _TEXT_NAMES):
                add(path, "UNREVIEWED_BINARY_ASSET")
                continue
            try:
                size = path.stat().st_size
                if size > _MAX_BYTES:
                    add(path, "OVERSIZED_ASSET")
                    continue
                raw = path.read_bytes()
                if b"\0" in raw:
                    add(path, "UNREVIEWED_BINARY_ASSET")
                    continue
                content = raw.decode("utf-8")
            except (OSError, UnicodeError):
                add(path, "UNREADABLE_OR_NON_UTF8")
                continue
            if _PRIVATE_HOST_PATH.search(content):
                add(path, "PRIVATE_HOST_PATH")
            if _POSSIBLE_SECRET.search(content) or _POSSIBLE_PASSWORD.search(content):
                add(path, "POSSIBLE_SECRET")
            if _PERSONAL_EMAIL.search(content):
                add(path, "PERSONAL_EMAIL_REVIEW_REQUIRED")
            if any(pattern.search(content) for pattern in denied):
                add(path, "FORBIDDEN_IDENTITY_LABEL")
    return sorted(findings, key=lambda row:(row["path"],row["reason"]))
