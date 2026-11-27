# OLG refresh: requirements notes (pre-PRD)

Discussion between Ben and Claude, 2026-11-25 to 2026-11-27, before drafting a PRD. These
notes feed the PRD; they are not the PRD. This repo is public: no agency names, URLs, staff
names or email content here.

## Why

- The OLG index was last scraped 2026-04-30 (chunks 2026-05-01, embeddings 2026-05-04). It
  has missed every release since, including a policy change on self-declarations, which
  staff use to verify much of an applicant's information.
- The index is in production: the business-side Claude Code agents call this laptop's
  `rag/query.py` directly. Ben: "it's gotta be up to date."
- An internal source repository for the guide exists, with one commit per release. Access is
  pending and may not come through. This project must not depend on it. If access does
  come, it would replace only the discovery and change-detection front end; parse onward is
  the same.

## Decisions so far

1. **Build and refresh on this laptop.** The old rule (rebuild only on the other machine,
   copy by flash drive) dated from when Ben had less control of this laptop. The other
   machine is "essentially abandoned" for this project and needs no index. The "Working
   Across Two Machines" section of `CLAUDE.md` gets rewritten.
2. **Not on autopilot.** One approval gate, before the Voyage spend: Ben sees what changed,
   how it cross-checked, and the cost estimate. Ben: "we won't want this on autopilot for a
   while, until we're very comfortable with it."
3. **Incremental from the first run.** Re-embed only new or changed pages, even though the
   first run covers seven months of releases. Ben: "it's important to test that part of the
   automation, even if it is much larger than it would in practice."
4. **Retired pages are archived, not deleted.** Hidden from search by default; reachable on
   purpose (for example an `--include-archived` flag, a minor CLI contract bump). Ben: "We
   don't want it to accidentally appear in search results for research, but we do want to
   reach it if we are actually looking for it."
5. **Raw HTML snapshots in a separate local git repo** (working name `olg-snapshots/`),
   outside this public repo. One commit per refresh gives a per-release diff and a history
   that can't be re-fetched later. Raw HTML so an improved parser can be re-run on history.
   Remote: undecided (see open questions). A live `.git` inside OneDrive risks sync damage;
   a `git bundle` copied to OneDrive is the backup option if one is wanted.
6. **Release emails are the trigger and the cross-check.** The publisher's digest lists each
   release note and its pages, with links. A Power Automate flow saves each digest to a
   OneDrive folder, on the registration-reports pattern (see below). Schedule: later.
7. **No special handling for moved pages** (a page whose URL changes). It is treated as one
   page retired and one added. Reasoning in "Moved pages" below. Accepted by Ben 2026-11-27,
   pending the first run's evidence.

## The workflow

```
 Release digest email ──► Outlook rule ──► folder ──► Power Automate ──► OneDrive folder
        │
        ▼
 1 DISCOVER     menu data files (whxdata/toc*.js) ──► manifest
 2 FETCH        every page's raw HTML ──► olg-snapshots/ working tree
 3 RECORD       commit "OLG as of <date>"; diff = added / changed / removed pages
 4 CROSS-CHECK  diff vs digest links vs links found inside pages ──► mismatch: stop, Ben
 5 PARSE        raw HTML ──► staging scraped_pages/
 6 CHUNK        ──► staging chunks; compare chunk text (with context prefix) to live
 ── GATE ──     Ben approves: change list, cross-check result, Voyage cost estimate
 7 EMBED        new and changed chunks only ──► staging vectors; retired ──► archived
 8 SPARSE       rebuild BM25
 9 VERIFY       counts, build_record, test queries (e.g. the self-declaration change)
10 PUBLISH      swap staging into the live index; handoff to business
```

| Step | Lives in | Exists today? |
|---|---|---|
| Digest capture | Outlook rule + Power Automate (Microsoft cloud) + OneDrive folder | No |
| 1 Discover | `rag/olg/extractor.py`, new mode reading the menu files directly | Only from a HAR file |
| 2 Fetch | `rag/olg/scraper.py` | Yes, but discards raw HTML |
| 3 Record | New; git in `olg-snapshots/` | No |
| 4 Cross-check | New; reads the saved digests | No |
| 5-6 Parse, chunk | `parser.py`, `chunker.py` | Yes; need staging output |
| 7 Embed | `rag/embedder.py` | Full rebuild or resume only; no per-page replace or archive |
| 8 Sparse | `rag/sparse_index.py` | Yes |
| 9 Verify | New | Partly (`build_record`) |
| 10 Publish | New swap step + handoff | No |

Build to staging, then swap: production agents may be querying the live index during a
refresh.

## Discovery: how new pages are found

The site's navigation menu is built from data files (`whxdata/toc.new.js`, `toc0.new.js`,
...). Each lists one menu level's entries, their URLs, and pointers to the files below. The
original HAR capture was only a way to collect them; `extractor.py:66-160` rebuilds the tree
from them. A script can fetch the root file and follow every pointer, so new URLs don't need
to be supplied by Ben. **Untested:** whether the files can be fetched outside a browser.

Three independent URL sources: the menu, internal links inside pages (the parser already
records them), and the digest's links. A URL in one and not the others is a mismatch.

## Digest capture: replicating registration-reports

registration-reports' flow (documented in its `docs/pipeline.md`, section [2]): an Outlook
rule files the email into a folder; a Power Automate flow ("When a new email arrives (V3)" on
that folder) saves the attachment to a OneDrive folder; Task Scheduler runs the local
pipeline. The flow is "deliberately dumb": it moves a file and does no parsing.

Ours is the same shape with one difference: the content is the email **body**, not an
attachment.

- Trigger: When a new email arrives (V3), on a folder the Outlook rule fills.
- Action: OneDrive for Business, Create file. File Content: the email Body (HTML). File Name
  built from the received time, e.g.
  `formatDateTime(triggerOutputs()?['body/receivedDateTime'],'yyyy-MM-dd_HHmm')` + `.html`,
  not from the subject (subjects can contain characters file names can't).
- No parsing in the flow (their decision 14). The refresh's step 4 parses the saved HTML.

Gotchas carried over from registration-reports: the trigger only sees mail that arrives after
it starts watching (past digests go in by hand); if it silently stops firing, repoint it to
Inbox, test, and repoint back. Failure detection belongs downstream (a refresh that finds a
release on the site with no digest, or the reverse, says so).

**To check:** whether links in the saved body are rewritten by a link-scanning service (e.g.
Safe Links). If so, the parser unwraps them to the real URL. Not verified.

The digests stay in OneDrive, never in either repo.

## Moved pages

If a page's URL changes, the default handling (retire old, add new) costs:

- Embedding one page's chunks again: small.
- New chunk ids for that page. Business callers were already told not to keep ids across a
  refresh.
- An archived copy duplicating a live page. Hidden by default, so visible only when
  deliberately searching archives, where "this URL was retired on <date>" is accurate.
- History: git's rename detection (`git diff -M`) reports likely moves from content
  similarity, with no code of ours. The approval summary can list them.

A move-detection mechanism would add matching logic, thresholds and tests to save the above.
Not worth it unless the first run shows moves are common; the first run compares April's
URL list to today's and will show how often it happened in seven months.

Related: a page that moves in the menu but keeps its URL gets a new breadcrumb, which is in
every chunk's context prefix. Change detection must compare chunk text including the
prefix, not only the page HTML, or such pages would keep stale prefixes.

## The first run's baseline

No raw HTML exists from April, so run 1 has nothing to diff at the HTML level. Run 1
compares parsed text against the April `index/olg/scraped_pages/` JSON; HTML diffs start
with run 2. (Alternative considered: the pages' "Last Update" dates. Cheaper, but trusts the
publisher to update them.)

## Findings from the discussion

- `config.ini` on this laptop has no `[olg]` section, so the scraper has no site address
  here. One-line fix.
- `docs/olg_pipeline.md` calls the site MadCap Flare. The `whxdata/` layout is RoboHelp,
  matching Ben's meeting notes. Fix in the PRD work.
- The 2026-11-19 handoff reply told business that OLG chunk ids "come from page
  breadcrumbs". The code builds them from the URL path plus a section number
  (`rag/olg/chunker.py:199-222`): an unchanged page keeps its ids; a changed page that gains
  or loses a section renumbers the sections after it; a moved URL gets new ids. The advice
  (don't keep ids) stands; the stated reason was wrong. Correct it in the refresh handoff.

## Tests run 2026-11-27 (read-only, public site, scratch files only)

- **Menu files fetch directly.** Starting from the root menu file and following every
  pointer: 244 files, 0 failures, 1,190 page URLs. No browser or HAR needed.
- **Today's menu vs the April page list** (1,204 unique URLs): 48 added, 62 removed (60
  pages plus two `#anchor` entries). Only 2 are same-filename moves to a new folder. Most
  of the rest are renames and consolidations that no matcher would pair: several
  program-specific SSN pages replaced by a few cross-program ones, four verification
  sub-pages by one overview, eight child-care pages by one consolidated page. Supports
  decision 7.
- **The April page list was older than the April scrape.** It is dated 2026-04-06 on disk
  and lacks pages from a 2026-03-10 release, though April's scraped pages already link to
  them. So the April index missed pages added between the HAR capture and the scrape.
- **Internal links as a discovery source:** April's pages link to 837 distinct in-site page
  URLs; 110 are not in the April list, and 12 of those 110 are in today's menu (all 12 are
  among today's 48 added). The other 98 are not in today's menu: broken links, retired
  pages or pages outside the menu. Not fetched, so which is not established.
- **The site keeps its own release log.** A yearly "Transmittal Updates" page has one row
  per release: date, number, program, title, and "Topics" (the titles of the pages it
  changed, or "Transmittal only"). The current year's page has 69 rows; 44 are newer than
  the last release the April index holds, 4 of them transmittal-only. Two self-declaration
  releases (June and August 2026) are among them. This is a second cross-check source,
  on the site itself, matched by page title rather than URL.
- **Raw HTML size:** a 25-page random sample averaged 11.5 KB a page, about 14 MB for all
  pages. A snapshot repo stays small; one release changes a handful of pages.
- **Archive filtering in ChromaDB 1.5.2:** `where={"status": {"$ne": "archived"}}` returns
  chunks that have no `status` field at all, in both `get` and `query`. So only archived
  chunks need the field; live chunks need no rewrite. Version-dependent behaviour: pin it
  with a test. Sparse (BM25) and `--exact` search need the same filter separately.

## Open questions

1. Snapshot repo remote: none, a private GitHub repo (which account?), or a bundle in
   OneDrive. Recommendation: no remote; a `git bundle` to OneDrive after each refresh.
2. Retired-page archive: same collections with a `status: archived` field (recommended,
   given the filter test above), or separate collections.
3. When the scheduled run comes: what it runs on its own (discover, fetch, diff, cross-check
   are free) and how it tells Ben a refresh awaits approval.
4. What the digest names for each page: title, URL or both. Needs one saved digest. If it
   mirrors the site's release log, it names titles, and the URLs come from its links.
5. ~~Whether the menu files can be fetched outside a browser.~~ Yes (above).
6. Whether to match release-log page titles to menu titles exactly or loosely (titles in
   the log can differ slightly from the menu, e.g. punctuation).
