# PRD 0001: Author reference uploads

- **Status:** draft for Ben's review
- **Source:** handoff `handoffs/2026-11-03-author-reference-uploads.md` (from portfolio)
- **Decided with Ben (2026-11-03):** per-assignment storage; reference text goes into the
  draft prompt; free-text description per upload; per-draft checkboxes, all on by default;
  tracked changes accepted by default and flagged; converted text is preview-only;
  Research integration deferred to a later PRD.

## 1. Introduction

Ben drafts OLG pages, often Overview pages, from material he has already written: pages
that aren't in the published OLG yet. Today the Author app can't take that material in.
The workaround is manual: convert each `.docx` in the Convert tab, save the Markdown into a
folder by hand, and paste file paths into the assignment, hoping the draft session reads
them all.

This feature lets Ben upload `.docx`, `.md` and `.txt` files to an assignment in the Author
tab. The app converts them, stores them with the assignment, and puts their text into the
draft prompt in a clearly labeled section. A short description Ben writes for each upload
tells the drafting model how to treat it.

**Goal:** uploading a document is the only thing Ben has to do for its content to reach the
draft, and the draft's saved prompt shows exactly what it saw.

## 2. Goals

1. Upload one or more `.docx` / `.md` / `.txt` files to an assignment from the Author tab,
   with no file-system steps.
2. Every selected upload's full text appears in the draft prompt, so `full_prompt.md`
   records exactly what the draft saw. Nothing depends on the model choosing to open a file.
3. The drafting model treats uploads as the author's **unpublished** pages: authoritative
   for the new page's content, not cited as published OLG, with conflicts against published
   sources flagged rather than resolved.
4. Each draft version records which uploads (and which descriptions) it used.
5. The command line keeps parity: uploads can be added and used from `author.py`.

## 3. User stories

- As Ben, I want to drag three unpublished Word pages onto the assignment so the draft can
  build an Overview page from them without my converting anything.
- As Ben, I want to write "This is the replacement for the current Expedited page;
  everything here supersedes it" next to an upload, so the model knows how to use it.
- As Ben, I want to leave one upload out of a draft to see how the result changes, and
  later see which uploads each draft used.
- As Ben, I want to know when an uploaded doc had tracked changes, and re-convert it with
  the changes rejected if the accepted version isn't what I meant.
- As Ben, I want to replace an upload by uploading a corrected file with the same name.

## 4. Functional requirements

### Storage

1. Uploads are stored per assignment under `output/author/<name>/references/<ref_id>/`,
   which is gitignored. Each folder holds:
   - the original file, under its original filename;
   - `converted.md`, the text used in prompts;
   - `meta.json`: original filename, file type, upload timestamp, character count,
     `tracked_changes` (true/false/null for non-docx), `change_mode` (`accept`/`reject`/null),
     `image_count`, and `description` (free text, may be empty);
   - `images/`, for images extracted from a `.docx` (only when it has any).
2. `ref_id` is a filesystem-safe slug made from the original filename stem (lowercase,
   non-alphanumerics become `-`). Uploading a file whose slug already exists **replaces**
   that upload (original, conversion, images) and keeps its description. The UI says it
   replaced an existing upload.
3. Storage logic lives in a new module, `apps/author/reference_docs.py`, used by both the
   web UI and the CLI. (Not `references.py`: `apps/author/references/` is already a folder.)

### Conversion

4. `.docx` files convert with the existing `tools/docx_reader.py` (`read_docx` +
   `to_markdown`). No new parser.
5. Tracked changes default to **accept**. `has_tracked_changes` runs before conversion; the
   result is saved in `meta.json` and shown as a badge in the upload list.
6. A `.docx` with tracked changes can be **re-converted** with the other mode (accept ↔
   reject) from its upload row, without re-uploading.
7. `.md` and `.txt` files are stored as-is in `converted.md`. Read as UTF-8 (with or
   without BOM); if that fails, fall back to cp1252 (Windows Notepad's default).
8. Any other file type is rejected with a clear message naming the allowed types. One bad
   file in a multi-file upload doesn't block the others.
9. An upload whose converted text is empty is rejected ("no text found").

### Upload experience (Author tab)

10. A new **References** phase tab sits before Research: `References | Research | Draft |
    Format`. It follows the existing panel layout (list area + detail area).
11. The list area has a file input accepting several files at once (`.docx,.md,.txt`) and
    lists every upload with: filename, type, character count, tracked-changes badge (when
    applicable), a short preview of its description, and Remove.
12. Clicking an upload opens its detail view: a **read-only** preview of `converted.md`, an
    editable description box with Save, and (for tracked-change docs) the re-convert
    button. Images appear as their Markdown image references; they aren't rendered.
13. Remove asks for confirmation, then deletes the upload's folder.
14. The description box carries help text telling Ben what the drafting model needs to
    know. Proposed wording:

    > **Tell the drafting model how to use this document.** It already knows this is your
    > own, unpublished material. Helpful things to say:
    > - **What it is:** a new page, a rewrite of an existing OLG page (name it), notes, an
    >   outline.
    > - **Its status:** approved and awaiting publication, still in draft, superseded.
    > - **Its role in this assignment:** the page this overview summarizes, content to carry
    >   over word for word, background only.
    > - **How much to trust it:** e.g. "authoritative over the current OLG page", or
    >   "Section 3 is out of date; ignore it".
    > - **Anything else:** known conflicts with policy, where the page will live, the audience.

15. Descriptions can be edited at any time. Editing one doesn't change past drafts: each
    draft snapshots the descriptions it used (requirement 21).

### Draft integration

16. The Draft prompt editor gets a second picker below the research-version picker:
    "Reference documents to include", one checkbox per upload, **all checked by default**.
    It shows each upload's character count and a running total. If there are no uploads it
    says so and links to the References tab.
17. When the selected uploads total more than a threshold (config
    `[author] reference_warn_chars`, default 200,000), the picker shows a warning that the
    prompt is very large. The warning doesn't block the launch.
18. `compose_draft_prompt` takes the selected uploads and adds an **Author's Reference
    Documents** section after the Assignment and before the Research Findings. When there
    are no uploads selected, the section is left out entirely.
19. The section opens with fixed framing text (in a prompt file, not hard-coded), covering:
    - These are the assignment author's own documents, **not published OLG**. Don't cite
      or link them as existing OLG pages, and don't describe their content as current
      policy unless published sources confirm it.
    - They are authoritative for the content of the page being drafted, as qualified by
      each document's description.
    - Where a reference document conflicts with published OLG, CMR, FNS or CFR content,
      **don't resolve it**: follow the reference document unless its description says
      otherwise, and list each conflict in the Author's Notes with both sources.
    - The author's description of a document outranks these defaults.
20. Each document is wrapped in clear delimiters carrying its filename and description,
    e.g.
    ```
    <reference_document filename="Expedited Overview v3.docx">
    <author_description>…or "(none given)"…</author_description>
    <content>
    …converted.md…
    </content>
    </reference_document>
    ```
21. The draft version's `meta.json` gets a `references` list: `ref_id`, filename, and the
    description **as used**, for each included upload. `based_on` keeps its current meaning
    (research versions).
22. The draft detail view shows the references a draft used, next to "Based on research".
    The launch confirmation message lists them too.
23. `apps/author/prompts/author_draft.md` is updated so "You have been given" names the
    reference documents, and the Output Instructions' Author's Notes list adds
    "conflicts between reference documents and published sources".
24. The draft session's opening message says the prompt file is long and must be read in
    full (in several reads if needed) before drafting. This matters because Claude Code's
    file reader returns long files in pieces, and the prompt now includes reference text.

### Command line

25. `author.py --reference PATH` (repeatable) adds files to the assignment's references
    (same conversion and replace rules) before the phase runs.
26. `author.py --draft-only` (and the full pipeline's draft step) includes **all** stored
    uploads, matching how the CLI already uses all research versions.
27. `author.py --name X --list-references` prints the assignment's uploads.

## 5. Non-goals

- **Research integration** (uploads feeding the Research phase). Next PRD.
- A shared reference library across assignments.
- Editing converted text in the app.
- PDF uploads.
- Sending images to the model or describing them. Image references stay in the Markdown
  as paths; the draft session can open them if it chooses, but nothing requires it.
- Changing the Convert tab.

## 6. Design considerations

- Same look as the existing Author panels: server-rendered HTMX partials, no JS framework.
  Small additions to `ui/static/app.js` for the multi-file upload and the reference picker,
  in the style of the research picker (`research-checkboxes`).
- The tracked-changes badge reuses whatever the Convert tab shows for tracked changes.

## 7. Technical considerations

- **Data and privacy.** Uploads are agency policy drafts. They live only under
  `output/author/`, which is gitignored; the repo is public. Their text goes to Anthropic
  inside the draft prompt via the Claude Code session, the same path research reports and
  OLG content already take. No new external service.
- **Tests use synthetic fixtures only:** small `.docx` files built in the test with
  python-docx (including one with a tracked change), plus `.md`/`.txt` written to a temp
  folder. No real documents in tracked folders.
- **Filename safety:** the slug and the stored original filename must not allow path
  traversal (`..`, absolute paths, Windows reserved names like `CON`).
- **Upload size:** FastAPI `UploadFile` streams to memory/temp; reject a single file over a
  sane cap (config `[author] reference_max_mb`, default 25).
- `config.ini.example` gets the two new `[author]` keys in the same commit.
- Version folders: a draft's `full_prompt.md` already captures the full text, so no copy of
  the uploads is made per draft.

## 8. Success metrics

- Ben can go from a set of unpublished `.docx` pages to a launched draft using only the
  browser.
- For a test draft, `full_prompt.md` contains every selected upload's full text and
  description, and `meta.json` lists them.
- In Ben's first real Overview drafts, the Author's Notes flag conflicts between uploads and
  published sources instead of silently merging them, and the draft doesn't cite uploads
  as published OLG pages.

## 9. Open questions

1. Is the help-text wording in requirement 14 right, or should it be shorter?
2. Is 200,000 characters a sensible warning threshold? (A rough stand-in for "this is a lot
   to read in one session"; I haven't measured where drafting quality starts to drop.)
3. Default behavior in a conflict (requirement 19): follow the reference document and flag
   it. Do you want that, or flag it and follow the published source?
