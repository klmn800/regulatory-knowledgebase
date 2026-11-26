# Regulatory Knowledgebase

## At a glance

*Updated 2026-11-25*

### Current state
Multi-source RAG over SNAP policy (OLG, 106 CMR, FNS Handbook 310, 7 CFR). All four sources
are parsed, chunked, embedded and searchable. Search UI, comparator, author and report are
built. Runs on both machines, synced through GitHub. Tests: `python -m pytest tests`
(160, offline, synthetic fixtures).

- **PRD 0001, Author reference uploads: done** (gate 6.3 closed 2026-11-25 on a real
  four-document draft). The References tab takes the author's unpublished pages with a
  description each, and drafts include them framed as unpublished. Every Claude Code
  session the app starts (Author draft and research, QC judge and PPT, comparator L2, and
  their resumes) now gets the project `.venv` first on PATH, so `python rag/query.py` works
  in those sessions on the laptop.
- **PRD 0002, CLI contract 1.0: done** (2026-11-21, handoff with `business` closed).
  `--mode dense|sparse|hybrid`, `--exact`, index build dates, exit codes. See
  `docs/cli_contract.md`.

### Blockers
- None.

### Next
- A PRD for Research using the uploads (systematic conflict checks against published sources).
- The OLG refresh (ask 3 of the 2026-11-19 handoff), as its own project, with a handoff to
  `business` before chunk ids change.

## Notes

- Codename was Policy Navigator. Renamed to Regulatory Knowledgebase to avoid confusion with
  the unrelated DTA Policy Navigator application. Folder renamed 2026-11-03.
- The GitHub repo `klmn800/regulatory-knowledgebase` is **public** and ships code only. The
  index, sources, outputs and `config.ini` are gitignored.

## Machine-specific setup

Setup steps that apply to one machine only live in gitignored files on that machine. On the
work laptop: `docs/laptop-setup.md` (read it before rebuilding `.venv`).
