# Author: upload reference documents to draft from

- **From:** portfolio
- **To:** regulatory-knowledgebase
- **Opened:** 2026-11-03
- **Status:** accepted

## The problem

Ben wants to draft OLG pages, often an **Overview page**, from material he has already
written: pages that aren't in the published OLG yet. Today Author can't take that material
in directly. It draws only on the assignment text, the research versions selected for a
draft, and the style guide (`compose_draft_prompt` in `apps/author/author.py`).

The only workaround today:

1. Convert each `.docx` in the Convert tab.
2. Save the Markdown by hand into a folder under `output/author/<name>/`.
3. Write the file paths into the assignment, so the Claude Code draft session goes and reads
   them.

That works, but Ben has to go into the file system, handle conversion himself, and trust
that the drafting session actually reads every file.

**What Ben wants:** he expects this to be a regular workflow. He wants to upload documents
**in the app** and have the app convert them, without going into the folders, the
background or a separate conversion step himself.

This handoff is a starting point for a **design conversation with Ben**, not a spec. Please
brainstorm it with him before building anything. Once the design settles, follow the PRD,
then task list, then gated build workflow in `~/.claude/standards/ai-dev-tasks/`.

## Existing pieces worth knowing about

- **Conversion:** `tools/docx_reader.py` (`read_docx` + `to_markdown`) is what the Convert
  tab uses (`/convert/upload` in `ui/app.py`). It already handles headings, lists, tables,
  links, images and tracked changes (accept or reject). An upload feature probably shouldn't
  need a new parser.
- **Per-assignment folders:** each assignment has `output/author/<name>/`, which is
  gitignored. Research and drafts are numbered versions there (`ui/versioning.py`).
- **Draft provenance:** each draft version saves `full_prompt.md` and a `meta.json` with
  `based_on` (the research versions it used). The draft UI already has a pattern for
  choosing which research versions a draft uses.
- **The draft session** is unrestricted Claude Code started from the project root, so it can
  read files, but that relies on the model choosing to read them.

## Some possible directions (to discuss, not decided)

**Where uploads live.** Per assignment (`output/author/<name>/references/`, original plus
converted `.md` side by side) or a shared reference library reused across assignments. Per
assignment is simpler. A shared library helps if the same pages feed several overviews.

**How reference text reaches the draft.**
- *Included in the prompt:* the converted text goes into the assembled prompt as its own
  section, like research reports do. `full_prompt.md` then records exactly what the draft
  saw, and nothing depends on the model choosing to open files. A size warning covers very
  large uploads.
- *Referenced by path:* the prompt lists the files, and Claude Code reads them. The prompt
  stays smaller, but the provenance is weaker and the model might skip a file.

The portfolio session leaned toward including the text, but it's open.

**Choosing references per draft.** Checkboxes like the research-version picker, recorded in
`meta.json` `based_on`, so each draft version shows what went into it.

**How the prompt describes the documents.** This is likely the most important design point.
The drafting model needs to know these are the author's own **unpublished** pages:
authoritative for the new page's content, but not published OLG. Without that, it may cite
them as current policy. It should also flag (not resolve) conflicts between them and
published OLG, CMR, FNS or CFR, in keeping with "the disagreement is the finding".

**The upload experience.** Some details to settle:
- uploading several files at once;
- a list of uploaded files with a tracked-changes flag;
- previewing the converted text;
- maybe editing the converted text before it's used;
- removing a file;
- the default for tracked changes;
- what happens to images.

**Scope questions.**
- Which file types: `.docx` only, `.md` / `.txt`, or PDFs?
- Should references feed only the Draft phase, or Research too? In Research they could be
  used to find related published pages for an overview to link to.
- Does the command line need a matching `--reference` flag, given the project keeps the web
  UI and command line in step?

## Constraints

- **The repo is public.** Uploaded documents and their conversions must stay under
  gitignored paths (`output/` is). No sample documents in tracked folders, tests included.
  Use synthetic test fixtures.
- Uploaded text goes to Anthropic as part of the draft prompt, the same as research and
  OLG content already do. Worth stating in the PRD.
- Windows; FastAPI + HTMX, server-rendered partials (no JS framework), per the existing UI.

**Ben:** brainstorm the design with the project session before any code is written. Your
stated preferences so far: upload and convert in the app; no manual steps in the file
system.

## Response (regulatory-knowledgebase, 2026-11-04)

Designed with Ben and built: PRD `tasks/0001-prd-author-reference-uploads.md`, task list
`tasks/tasks-0001-prd-author-reference-uploads.md`. Per-assignment uploads (.docx/.md/.txt) in
a new References tab, a free-text description per upload, text included in the draft prompt
with framing (unpublished; follow the upload and flag conflicts), per-draft checkboxes
recorded in `meta.json`, and `--reference` / `--list-references` on the CLI. Research
integration is deferred to a later PRD. Also fixed a converter bug found along the way:
`docx_reader` never recognized heading styles (it matched style names against style IDs).

Verified so far: 38 offline tests (synthetic fixtures), plus an HTTP check against a running
server. Still open: Ben's real-document test in the browser (task 6.3). This handoff
becomes `done` after that.
