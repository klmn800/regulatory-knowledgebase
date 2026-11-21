"""Error kinds, exit codes and error output for the `rag/query.py` CLI.

The CLI contract (`docs/cli_contract.md`, contract 1.0) promises callers:

- an exit code per error kind (`usage` 2, `unavailable` 3, `api` 4, `internal` 5;
  0 is success, including zero results);
- exactly one stderr line per error: ``query.py: error [<kind>]: <message>``;
- with ``--json``, a JSON error object on stdout, and nothing else there.

A Python traceback goes to stderr only when the environment variable
``QUERY_DEBUG=1`` is set.

This module knows nothing about ChromaDB or Voyage. `rag/query.py` maps its
own exceptions onto these kinds.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Callable, TextIO

CONTRACT_VERSION = "1.0"
PROGRAM_NAME = "query.py"

EXIT_CODES: dict[str, int] = {
    "usage": 2,
    "unavailable": 3,
    "api": 4,
    "internal": 5,
}

COMMANDS = ("search", "exact", "chunk", "url", "list")


class CliError(Exception):
    """An error the CLI reports with a kind, a message and an exit code.

    Args:
        kind: One of the keys of `EXIT_CODES`.
        message: A short, single-line explanation for the caller.
    """

    def __init__(self, kind: str, message: str):
        if kind not in EXIT_CODES:
            raise ValueError(f"unknown error kind {kind!r}")
        super().__init__(message)
        self.kind = kind
        self.message = _one_line(message)

    @property
    def exit_code(self) -> int:
        """The process exit code for this error's kind."""
        return EXIT_CODES[self.kind]


def _one_line(text: str) -> str:
    """Collapse a message onto one line, so stderr stays one line per error."""
    return " ".join(str(text).split())


def debug_enabled() -> bool:
    """True when ``QUERY_DEBUG=1`` asks for tracebacks."""
    return os.environ.get("QUERY_DEBUG", "").strip() == "1"


def error_object(err: CliError, command: str | None, index: dict | None) -> dict:
    """The JSON error response: ``{contract_version, command, error, index}``."""
    return {
        "contract_version": CONTRACT_VERSION,
        "command": command,
        "error": {
            "kind": err.kind,
            "message": err.message,
            "exit_code": err.exit_code,
        },
        "index": index,
    }


def emit_error(
    err: CliError,
    command: str | None,
    source: str | None,
    as_json: bool,
    index_reader: Callable[[str], dict] | None = None,
    exc: BaseException | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Report `err` and return its exit code.

    Writes the stderr line (preceded by a traceback of `exc` when debugging is
    on) and, when `as_json` is set, the JSON error object on stdout. The
    ``index`` block is read for `source` with `index_reader`; it is ``null``
    when the source is unknown or no reader is given.
    """
    out = stdout or sys.stdout
    errs = stderr or sys.stderr

    if exc is not None and debug_enabled():
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=errs)
    print(f"{PROGRAM_NAME}: error [{err.kind}]: {err.message}", file=errs, flush=True)

    if as_json:
        index = None
        if source and index_reader is not None:
            try:
                index = index_reader(source)
            except Exception:  # the reader never raises, but stay safe
                index = None
        print(json.dumps(error_object(err, command, index), indent=2,
                         ensure_ascii=False), file=out, flush=True)

    return err.exit_code
