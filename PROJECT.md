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

## Laptop setup (work laptop only)

The laptop's network runs Zscaler, which re-signs HTTPS traffic with its own CA. Python 3.13+
rejects that CA ("Basic Constraints of CA cert not marked critical"), and `certifi` doesn't
include it, so Voyage calls (made through `requests`) fail with `CERTIFICATE_VERIFY_FAILED`.
The Anthropic SDK already trusts the Windows store and works as it is.

The fix lives in the venv only, not the repo, because the development machine doesn't need it:

1. `.venv\Scripts\python.exe -m pip install truststore`
2. Create `.venv\Lib\site-packages\sitecustomize.py` with:
   ```python
   try:
       import truststore
       import urllib3.util.ssl_ as _u3ssl
       _u3ssl.SSLContext = truststore.SSLContext
   except Exception:
       pass
   ```

This makes `urllib3` (under `requests`, under `voyageai`) verify through the Windows trust
store. Don't use `pip-system-certs` or a global `truststore.inject_into_ssl()`: the Anthropic
SDK then fails with a `RecursionError`. A custom CA bundle via `REQUESTS_CA_BUNDLE` doesn't
work either; Python's strict check still rejects the Zscaler CA.

Rebuild the venv from scratch:
`python -m venv .venv`, then `.venv\Scripts\python.exe -m pip install -r requirements.txt`,
then the two steps above.
