## Relevant Files

- `apps/author/reference_docs.py` - New. Storage and conversion for uploads: add, replace, list, load, remove, re-convert, update description, select for a prompt.
- `tests/test_reference_docs.py` - New. Unit tests for `reference_docs.py` with synthetic fixtures built in the test.
- `tests/test_author_prompt.py` - New. Tests that `compose_draft_prompt` includes, frames and omits reference documents correctly.
- `tests/conftest.py` - New. Shared fixtures (temp assignment folder, synthetic `.docx` builder, including one with a tracked change).
- `apps/author/author.py` - `compose_draft_prompt` and `launch_draft` take references; CLI flags `--reference` and `--list-references`.
- `apps/author/prompts/author_reference_framing.md` - New. Fixed framing text for the Author's Reference Documents section.
- `apps/author/prompts/author_draft.md` - Mention reference documents in "You have been given" and the Author's Notes list.
- `tools/docx_reader.py` - Existing converter (`read_docx`, `to_markdown`, `has_tracked_changes`); reused, not changed.
- `ui/app.py` - New `/author/{name}/references/...` routes; draft run accepts selected references.
- `ui/versioning.py` - Draft view exposes `references` from `meta.json`.
- `ui/templates/author.html` - New References phase tab and panel.
- `ui/templates/partials/author_references_list.html` - New. Upload control and upload list.
- `ui/templates/partials/author_reference_detail.html` - New. Read-only preview, description editor with help text, re-convert.
- `ui/templates/partials/author_prompt_editor.html` - Reference picker in the Draft editor.
- `ui/templates/partials/author_draft_detail.html` - Show references a draft used.
- `ui/static/app.js` - Multi-file upload, reference picker, running character total and size warning.
- `ui/static/style.css` - Styles for the upload list, badge and warning.
- `config.ini.example` - New `[author]` keys `reference_warn_chars`, `reference_max_mb`.
- `requirements.txt` - Add `pytest` (the repo has no test suite yet).
- `CLAUDE.md`, `README.md`, `docs/` - Document the feature and the new test suite.

### Notes

- This feature starts the repo's test suite. Run it from the project root with `python -m pytest tests`. It is offline and free: no API calls, and no test launches a Claude Code terminal.
- Fixtures are synthetic and built in code. No real or agency documents go in `tests/`; the repo is public.

## Tasks

- [ ] 1.0 Reference storage and conversion module (`apps/author/reference_docs.py`) with tests
- [ ] 2.0 Draft prompt integration: framing prompt, `compose_draft_prompt`, draft `meta.json`, opening message, config keys, with tests
- [ ] 3.0 References tab in the web UI: upload, list, preview, description, re-convert, remove
- [ ] 4.0 Draft phase in the web UI: reference picker with size warning, references shown on launch and in draft detail
- [ ] 5.0 Command-line parity: `--reference`, `--list-references`, all uploads in CLI drafts
- [ ] 6.0 Documentation and end-to-end check in the browser
