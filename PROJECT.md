# Regulatory Knowledgebase

## At a glance

*Updated 2026-11-03*

### Current state
Multi-source RAG over SNAP policy (OLG, 106 CMR, FNS Handbook 310, 7 CFR). All four sources
are parsed, chunked, embedded and searchable. Search UI, comparator, author and report are
built. Copied to this laptop from the development machine on 2026-11-03, including the built
index; the environment is not set up here yet (no `chromadb` installed).

### Needs Ben
- Install the same `chromadb` version as the dev machine (`pip show chromadb` there) so the
  copied index opens without a format migration. Check it supports Python 3.14.
- `config.ini` came over with the dev machine's Anthropic and Voyage keys. If they're
  personal, consider keys made just for this laptop, so they can be revoked separately.
- Run `git status`, then `git pull`, on the development machine. The laptop's onboarding
  commits are on GitHub as of 2026-11-03.

### Blockers
- None.

### Next
Set up the Python environment on this laptop and confirm the web UI runs against the copied
index.

## Notes

- Codename was Policy Navigator. Renamed to Regulatory Knowledgebase to avoid confusion with
  the unrelated DTA Policy Navigator application. Folder renamed 2026-11-03.
- The GitHub repo `klmn800/regulatory-knowledgebase` is **public** and ships code only. The
  index, sources, outputs and `config.ini` are gitignored.
