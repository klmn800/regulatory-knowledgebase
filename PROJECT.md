# Regulatory Knowledgebase

## At a glance

*Updated 2026-11-03*

### Current state
Multi-source RAG over SNAP policy (OLG, 106 CMR, FNS Handbook 310, 7 CFR). All four sources
are parsed, chunked, embedded and searchable. Search UI, comparator, author and report are
built. Runs on both machines, synced through GitHub. Laptop set up 2026-11-03: `.venv` on
Python 3.14 with `chromadb==1.5.2` (pinned to match the development machine). The copied
index answers queries on all four sources, the Anthropic API works, and the web UI serves.

### Needs Ben
- Try a real question in the web UI on the laptop (`.venv\Scripts\python.exe ui/app.py`,
  then http://127.0.0.1:8001). Smoke tests passed; a full synthesis hasn't been run here.

### Blockers
- None.

### Next
Product work, from `big-to-do-list.txt` or whatever Ben picks.

## Notes

- Codename was Policy Navigator. Renamed to Regulatory Knowledgebase to avoid confusion with
  the unrelated DTA Policy Navigator application. Folder renamed 2026-11-03.
- The GitHub repo `klmn800/regulatory-knowledgebase` is **public** and ships code only. The
  index, sources, outputs and `config.ini` are gitignored.

## Machine-specific setup

Setup steps that apply to one machine only live in gitignored files on that machine. On the
work laptop: `docs/laptop-setup.md` (read it before rebuilding `.venv`).
