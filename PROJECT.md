# Regulatory Knowledgebase

## At a glance

*Updated 2026-11-04*

### Current state
Multi-source RAG over SNAP policy (OLG, 106 CMR, FNS Handbook 310, 7 CFR). All four sources
are parsed, chunked, embedded and searchable. Search UI, comparator, author and report are
built. Runs on both machines, synced through GitHub.

**New (PRD 0001):** Author reference uploads. A References tab takes the author's own
unpublished pages (.docx/.md/.txt) with a description each; the Draft picker includes them
in the prompt, framed as unpublished. Also, `docx_reader` now recognizes heading styles
(it never did before; the Convert tab benefits too). The repo now has a test suite:
`python -m pytest tests` (38 tests, offline, synthetic fixtures).

### Needs Ben
- **Restart the web UI** (the running copy predates the change), then do task 6.3: upload a
  real document in the References tab, write a description, launch a draft, and check the
  draft and its Author's Notes.
- Try a real question in the web UI on the laptop (`.venv\Scripts\python.exe ui/app.py`,
  then http://127.0.0.1:8001). Smoke tests passed; a full synthesis hasn't been run here.
  (Laptop set up 2026-11-03: `.venv` on Python 3.14, `chromadb==1.5.2`.)
- Laptop: `pytest` and `httpx` were installed into `.venv` here; run
  `pip install -r requirements.txt` on the development machine before running the tests.

### Blockers
- None.

### Next
After 6.3: mark the handoff done. Then a PRD for Research using the uploads (systematic
conflict checks against published sources).

## Notes

- Codename was Policy Navigator. Renamed to Regulatory Knowledgebase to avoid confusion with
  the unrelated DTA Policy Navigator application. Folder renamed 2026-11-03.
- The GitHub repo `klmn800/regulatory-knowledgebase` is **public** and ships code only. The
  index, sources, outputs and `config.ini` are gitignored.

## Machine-specific setup

Setup steps that apply to one machine only live in gitignored files on that machine. On the
work laptop: `docs/laptop-setup.md` (read it before rebuilding `.venv`).
