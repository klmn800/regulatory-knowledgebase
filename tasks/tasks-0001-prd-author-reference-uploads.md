## Relevant Files

- `apps/author/reference_docs.py` - New. Storage and conversion for uploads: add, replace, list, load, remove, re-convert, update description, select for a prompt.
- `tests/test_reference_docs.py` - New. Unit tests for `reference_docs.py` with synthetic fixtures built in the test.
- `tests/test_author_prompt.py` - New. Tests that `compose_draft_prompt` includes, frames and omits reference documents correctly.
- `tests/conftest.py` - New. Shared fixtures (temp assignment folder, synthetic `.docx` builder, including one with a tracked change).
- `apps/author/author.py` - `compose_draft_prompt` and `launch_draft` take references; CLI flags `--reference` and `--list-references`.
- `apps/author/prompts/author_reference_framing.md` - New. Fixed framing text for the Author's Reference Documents section.
- `apps/author/prompts/author_draft.md` - Mention reference documents in "You have been given" and the Author's Notes list.
- `tools/docx_reader.py` - Existing converter (`read_docx`, `to_markdown`, `has_tracked_changes`); reused. Heading-style detection fixed (task 2.9).
- `tests/test_docx_reader.py` - New. Heading and list-paragraph style detection.
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

- [x] 1.0 Reference storage and conversion module (`apps/author/reference_docs.py`) with tests
  - [x] 1.1 Add `pytest` to `requirements.txt`; create `tests/` with `conftest.py` (temp assignment dir; synthetic `.docx` builder via python-docx, including a variant with a `w:ins`/`w:del` tracked change and one with an embedded image).
  - [x] 1.2 `make_ref_id(filename)`: lowercase slug of the stem, non-alphanumerics to `-`, trimmed; rejects empty results, `..`, and Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) by suffixing `-file`. Original filename stored by its basename only.
  - [x] 1.3 `add_reference(output_dir, filename, data: bytes, max_mb)`: validate extension (`.docx`, `.md`, `.txt`) and size; write to a temp folder first, convert, then swap into `references/<ref_id>/` so a failed conversion never leaves a half-written upload. Returns a result with `ref_id`, `replaced: bool`, or an error message.
  - [x] 1.4 Conversion: `.docx` via `has_tracked_changes` + `read_docx(change_mode="accept", extract_images_to=<ref>/images)` + `to_markdown`; `.md`/`.txt` decoded as UTF-8 (BOM-tolerant), falling back to cp1252. Empty text is an error. Write `converted.md` and `meta.json` (fields per PRD req. 1).
  - [x] 1.5 Replace rule: re-adding an existing `ref_id` replaces the files and keeps the old `description`.
  - [x] 1.6 `list_references`, `load_reference` (meta + text), `update_description`, `remove_reference`, `reconvert_reference(ref_id, change_mode)` (docx only; re-runs conversion from the stored original).
  - [x] 1.7 `select_references(output_dir, ref_ids)` returns the loaded references in a stable order (upload order), skipping unknown ids.
  - [x] 1.8 Tests in `tests/test_reference_docs.py`: each file type; tracked-change detection and accept vs. reject text; image count; replace keeps description; bad extension, oversize, empty file, cp1252 `.txt`; path-traversal and reserved filenames; remove; reconvert on a non-docx is refused.
- [x] 2.0 Draft prompt integration: framing prompt, `compose_draft_prompt`, draft `meta.json`, opening message, config keys, with tests
  - [x] 2.1 Write `apps/author/prompts/author_reference_framing.md` with the framing rules from PRD req. 19 (unpublished, authoritative as qualified by the description, don't cite as published OLG, follow the upload and flag conflicts in Author's Notes, description outranks defaults).
  - [x] 2.2 `compose_draft_prompt(..., references=None)`: when references are given, add `## Author's Reference Documents` after the Assignment and before Research Findings: framing text, then one `<reference_document filename="...">` block per upload with `<author_description>` (or "(none given)") and `<content>`. Omit the section entirely when there are none.
  - [x] 2.3 `launch_draft(..., references=None)`: write a `references` list (`ref_id`, `filename`, `description` as used) into the draft's `meta.json`.
  - [x] 2.4 Opening message tells the session the prompt file is long and must be read in full, in several reads if needed, before drafting.
  - [x] 2.5 Update `apps/author/prompts/author_draft.md` ("You have been given" names reference documents) and the Author's Notes bullet list in `compose_draft_prompt` (add conflicts between reference documents and published sources).
  - [x] 2.6 Add `reference_warn_chars = 200000` and `reference_max_mb = 25` under `[author]` in `config.ini.example` (and read them with these fallbacks).
  - [x] 2.7 Tests in `tests/test_author_prompt.py`: section present with framing, filenames, descriptions and full text; "(none given)" for empty descriptions; section absent with no references; order is Assignment, References, Research. `launch_draft` is not called in tests.
  - [x] 2.8 **GATE (See):** Show Ben the References section of a prompt assembled from two synthetic uploads, so he can judge the framing wording before the UI is built on it.
  - [x] 2.9 (Added at the 2.8 gate, approved by Ben.) Fix `tools/docx_reader.py` heading detection: paragraphs store style IDs (`Heading1`), not names (`Heading 1`), so heading styles were never recognized (also broke the `List Paragraph` check). Resolve IDs to names per document; tests in `tests/test_docx_reader.py`. Also affects the Convert tab, for the better.
- [ ] 3.0 References tab in the web UI: upload, list, preview, description, re-convert, remove
  - [ ] 3.1 Routes in `ui/app.py`: `GET /author/{name}/references` (list partial), `POST .../references/upload` (multiple `UploadFile`s; per-file results), `GET .../references/{ref_id}` (detail), `POST .../references/{ref_id}/description`, `POST .../references/{ref_id}/reconvert`, `POST .../references/{ref_id}/delete`, `GET .../references/picker` (draft picker partial, used in 4.0). All validate `ref_id` through `reference_docs`.
  - [ ] 3.2 Add the References phase tab and panel to `ui/templates/author.html` (first tab), and wire `authorSwitchTab('references')` in `app.js`.
  - [ ] 3.3 `author_references_list.html`: multi-file input (`accept=".docx,.md,.txt"`), upload results (added / replaced / rejected with reason), list rows with filename, type, character count, tracked-changes badge, description snippet, Remove (with confirm).
  - [ ] 3.4 `author_reference_detail.html`: read-only preview of `converted.md`, description textarea with the PRD req. 14 help text and Save, tracked-change status with a re-convert button (accept/reject toggle).
  - [ ] 3.5 Styles in `style.css` for the list, badge and help text, matching the existing Author panels.
  - [ ] 3.6 Smoke-test the routes with FastAPI's `TestClient` against a temp output dir and synthetic files (add to `tests/test_reference_routes.py`).
- [ ] 4.0 Draft phase in the web UI: reference picker with size warning, references shown on launch and in draft detail
  - [ ] 4.1 In `author_prompt_editor.html` (drafts phase), add a "Reference documents to include" area loaded from the picker route: one checkbox per upload, all checked, with character counts; an empty-state message pointing to the References tab.
  - [ ] 4.2 `app.js`: running total of checked characters; show the warning above `reference_warn_chars` (value passed into the partial); send `reference_ids` with the draft run.
  - [ ] 4.3 `author_draft_run` accepts `reference_ids`, loads them with `select_references`, passes them to `compose_draft_prompt` and `launch_draft`, and lists them in the launch message.
  - [ ] 4.4 `ui/versioning.py` exposes `references` for drafts (empty list for older drafts); `author_draft_detail.html` shows "References:" next to "Based on".
  - [ ] 4.5 Route test: a draft run with `launch_draft` patched out builds a prompt containing the selected references and only those.
- [ ] 5.0 Command-line parity: `--reference`, `--list-references`, all uploads in CLI drafts
  - [ ] 5.1 `--reference PATH` (repeatable): read each file and `add_reference` it before any phase runs; print added / replaced / rejected.
  - [ ] 5.2 `--list-references`: print the assignment's uploads (filename, characters, tracked changes, description snippet) and exit.
  - [ ] 5.3 The CLI draft step passes all stored references to `compose_draft_prompt` and `launch_draft`.
  - [ ] 5.4 Tests for argument handling of `--reference` / `--list-references` (no terminal launch).
- [ ] 6.0 Documentation and end-to-end check in the browser
  - [ ] 6.1 Update `CLAUDE.md` (Author section, project structure, commands, new test suite) and `README.md` (Author usage; tests run offline and free).
  - [ ] 6.2 Start the web UI and exercise the References tab and draft picker with synthetic files over HTTP (no draft launch).
  - [ ] 6.3 **GATE (Act):** Ben uploads a real document in the browser, writes a description, launches a draft, and checks the draft and its Author's Notes. Ben runs this himself: it uses real agency material and opens a Claude Code session.
