/* Policy Navigator — minimal client-side JS */

/* Copy answer text to clipboard */
function copyAnswer() {
    var body = document.querySelector('.answer-body');
    if (!body) return;
    navigator.clipboard.writeText(body.innerText).then(function() {
        var btn = document.querySelector('.copy-btn');
        if (btn) {
            var orig = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(function() { btn.textContent = orig; }, 1500);
        }
    });
}

/* Ctrl+Enter to submit */
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        var form = document.querySelector('.ask-form');
        if (form) {
            form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            htmx.trigger(form, 'submit');
        }
    }
});


/* ============================================================
   AUTHOR PAGE
   ============================================================ */

var RESEARCH_STEPS = [
    "Searching policy sources...",
    "Reading through results...",
    "Cross-referencing three entire regulatory frameworks...",
    "Finding that one paragraph buried in Chapter 10...",
    "[insert actual progress status here]...",
    "Analyzing relevance (for real this time)...",
    "Organizing findings by theme...",
    "Composing structured evidence report...",
    "Almost there. Probably.",
    "Still going. Policy is complicated.",
    "Wrapping up..."
];

var _authorInterval = null;
var _currentAuthorName = '';

function authorShowProgress(steps) {
    var spinner = document.getElementById('author-spinner');
    if (!spinner) return;

    var textEl = spinner.querySelector('.author-progress-text');
    if (!textEl) return;

    spinner.style.display = 'block';
    textEl.textContent = steps[0];
    var i = 0;

    if (_authorInterval) clearInterval(_authorInterval);
    _authorInterval = setInterval(function() {
        i++;
        if (i < steps.length) {
            textEl.style.opacity = 0;
            setTimeout(function() {
                textEl.textContent = steps[i];
                textEl.style.opacity = 1;
            }, 200);
        }
    }, 4000);
}

function authorHideProgress() {
    var spinner = document.getElementById('author-spinner');
    if (spinner) spinner.style.display = 'none';
    if (_authorInterval) {
        clearInterval(_authorInterval);
        _authorInterval = null;
    }
}

/* Tab switching */
function authorSwitchTab(phase) {
    var tabs = document.querySelectorAll('.phase-tab');
    tabs.forEach(function(t) { t.classList.remove('active'); });
    document.getElementById('tab-' + phase).classList.add('active');

    var panels = document.querySelectorAll('.phase-panel');
    panels.forEach(function(p) { p.style.display = 'none'; });
    document.getElementById('panel-' + phase).style.display = 'block';
}

/* Save assignment text */
function authorSaveAssignment() {
    var nameEl = document.getElementById('author-name');
    var assignEl = document.getElementById('author-assignment');
    var name = nameEl ? nameEl.value.trim() : '';
    var assignment = assignEl ? assignEl.value.trim() : '';

    if (!name) {
        alert('Enter an assignment name.');
        if (nameEl) nameEl.focus();
        return;
    }

    var formData = new FormData();
    formData.append('name', name);
    formData.append('assignment', assignment);

    fetch('/author/save-assignment', { method: 'POST', body: formData })
        .then(function(resp) { return resp.json(); })
        .then(function() {
            _currentAuthorName = name;
            htmx.ajax('GET', '/author/assignments', '#assignments-list');
            authorLoadVersionLists(name);
        });
}

/* Load an assignment from the sidebar */
function loadAssignment(name) {
    fetch('/author/load/' + encodeURIComponent(name))
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            var nameEl = document.getElementById('author-name');
            var assignEl = document.getElementById('author-assignment');
            if (nameEl) nameEl.value = data.name;
            if (assignEl) assignEl.value = data.assignment || '';
            _currentAuthorName = name;

            authorLoadVersionLists(name);

            /* Auto-switch to the most advanced tab with versions */
            if (data.format_count > 0) authorSwitchTab('formats');
            else if (data.draft_count > 0) authorSwitchTab('drafts');
            else authorSwitchTab('research');
        });
}

/* Load all version lists for an assignment */
function authorLoadVersionLists(name) {
    fetch('/author/' + encodeURIComponent(name) + '/research')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('research-versions').innerHTML = html;
            htmx.process(document.getElementById('research-versions'));
        });

    fetch('/author/' + encodeURIComponent(name) + '/drafts')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('drafts-versions').innerHTML = html;
            htmx.process(document.getElementById('drafts-versions'));
            authorPopulateDraftSelect(name);
        });

    fetch('/author/' + encodeURIComponent(name) + '/formats')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('formats-versions').innerHTML = html;
            htmx.process(document.getElementById('formats-versions'));
            authorPopulateDraftSelect(name);
        });

    /* Clear detail areas */
    document.getElementById('research-detail').innerHTML = '';
    document.getElementById('drafts-detail').innerHTML = '';
    document.getElementById('formats-detail').innerHTML = '';
}

/* Populate the draft selector in the Format panel */
function authorPopulateDraftSelect(name) {
    var select = document.getElementById('format-draft-select');
    if (!select) return;

    fetch('/author/' + encodeURIComponent(name) + '/drafts')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            /* Parse version entries from the HTML to extract draft nums */
            var container = document.createElement('div');
            container.innerHTML = html;
            var entries = container.querySelectorAll('.version-entry');

            select.innerHTML = '<option value="">-- choose draft --</option>';
            entries.forEach(function(entry) {
                var numEl = entry.querySelector('.version-num');
                var tsEl = entry.querySelector('.version-ts');
                var draftBadge = entry.querySelector('.phase-done');
                if (numEl) {
                    var numText = numEl.textContent.trim();
                    var num = parseInt(numText.replace('v', ''), 10);
                    var ts = tsEl ? tsEl.textContent.trim() : '';
                    var hasDraft = !!draftBadge;
                    var label = numText + ' (' + ts + ')' + (hasDraft ? '' : ' [no draft yet]');
                    var opt = document.createElement('option');
                    opt.value = num;
                    opt.textContent = label;
                    if (!hasDraft) opt.disabled = true;
                    select.appendChild(opt);
                }
            });
        });
}

/* ---- Research ---- */

function authorViewResearch(num) {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) return;

    fetch('/author/' + encodeURIComponent(name) + '/research/' + num)
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('research-detail').innerHTML = html;
            htmx.process(document.getElementById('research-detail'));
        });
}

function authorShowResearchPrompt() {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) {
        alert('Enter an assignment name first.');
        return;
    }

    fetch('/author/' + encodeURIComponent(name) + '/research/prompt')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('research-detail').innerHTML = html;
            htmx.process(document.getElementById('research-detail'));
        });
}

function authorRunResearch() {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) { alert('Enter an assignment name.'); return; }

    var assignEl = document.getElementById('author-assignment');
    var assignment = assignEl ? assignEl.value.trim() : '';
    if (!assignment) { alert('Enter an assignment description.'); return; }

    var promptEl = document.getElementById('author-prompt-textarea');
    var prompt = promptEl ? promptEl.value : '';

    /* Collect selected sources */
    var sourceCbs = document.querySelectorAll('.research-source-cb:checked');
    var sources = [];
    sourceCbs.forEach(function(cb) { sources.push(cb.value); });
    if (sources.length === 0) {
        alert('Select at least one source to search.');
        return;
    }

    authorShowProgress(RESEARCH_STEPS);

    var formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('assignment', assignment);
    formData.append('sources', sources.join(','));

    fetch('/author/' + encodeURIComponent(name) + '/research/run', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            document.getElementById('research-detail').innerHTML = html;
            htmx.process(document.getElementById('research-detail'));
            authorLoadVersionLists(name);
        })
        .catch(function(err) {
            authorHideProgress();
            document.getElementById('research-detail').innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}

function authorRunResearchAgain(versionNum) {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) return;

    /* Capture focus text and sources from the current detail view before replacing it */
    var detailArea = document.getElementById('research-detail');
    var promptPre = detailArea ? detailArea.querySelector('.author-input-text') : null;
    var promptText = promptPre ? promptPre.textContent : '';

    var runAgainBtn = detailArea ? detailArea.querySelector('[data-sources]') : null;
    var prevSources = runAgainBtn ? runAgainBtn.getAttribute('data-sources') : 'olg,cmr,fns';

    /* Show prompt editor, then pre-fill */
    fetch('/author/' + encodeURIComponent(name) + '/research/prompt')
        .then(function(resp) { return resp.text(); })
        .then(function(editorHtml) {
            document.getElementById('research-detail').innerHTML = editorHtml;
            htmx.process(document.getElementById('research-detail'));

            /* Pre-fill focus text */
            var textarea = document.getElementById('author-prompt-textarea');
            if (textarea && promptText) textarea.value = promptText;

            /* Pre-check sources from previous version */
            var prevList = prevSources.split(',');
            var cbs = document.querySelectorAll('.research-source-cb');
            cbs.forEach(function(cb) {
                cb.checked = prevList.indexOf(cb.value) !== -1;
            });
        });
}

function authorCancelPrompt(phase) {
    document.getElementById(phase + '-detail').innerHTML = '';
}

/* ---- Drafts ---- */

function authorViewDraft(num) {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) return;

    fetch('/author/' + encodeURIComponent(name) + '/drafts/' + num)
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('drafts-detail').innerHTML = html;
            htmx.process(document.getElementById('drafts-detail'));
        });
}

function authorShowDraftPrompt() {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) {
        alert('Enter an assignment name first.');
        return;
    }

    fetch('/author/' + encodeURIComponent(name) + '/drafts/prompt')
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('drafts-detail').innerHTML = html;
            htmx.process(document.getElementById('drafts-detail'));

            /* Populate research checkboxes */
            fetch('/author/' + encodeURIComponent(name) + '/research')
                .then(function(resp) { return resp.text(); })
                .then(function(listHtml) {
                    var container = document.createElement('div');
                    container.innerHTML = listHtml;
                    var entries = container.querySelectorAll('.version-entry');

                    var checkboxArea = document.getElementById('research-checkboxes');
                    if (!checkboxArea) return;

                    if (entries.length === 0) {
                        checkboxArea.innerHTML = '<p class="text-muted">No research versions available.</p>';
                        return;
                    }

                    var html = '';
                    entries.forEach(function(entry) {
                        var numEl = entry.querySelector('.version-num');
                        var tsEl = entry.querySelector('.version-ts');
                        if (numEl) {
                            var numText = numEl.textContent.trim();
                            var num = parseInt(numText.replace('v', ''), 10);
                            var ts = tsEl ? tsEl.textContent.trim() : '';
                            html += '<label class="checkbox-label" style="display:block; margin-bottom:0.3rem;">' +
                                '<input type="checkbox" class="research-version-cb" value="' + num + '" checked> ' +
                                numText + ' (' + ts + ')' +
                                '</label>';
                        }
                    });
                    checkboxArea.innerHTML = html;
                });
        });
}

function authorRunDraft() {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) { alert('Enter an assignment name.'); return; }

    var assignEl = document.getElementById('author-assignment');
    var assignment = assignEl ? assignEl.value.trim() : '';

    var promptEl = document.getElementById('author-prompt-textarea');
    var prompt = promptEl ? promptEl.value : '';

    /* Collect selected research versions */
    var checkboxes = document.querySelectorAll('.research-version-cb:checked');
    var researchVersions = [];
    checkboxes.forEach(function(cb) { researchVersions.push(cb.value); });

    authorShowProgress([
        "Composing authoring prompt...",
        "Launching Claude Code terminal...",
        "Opening new window..."
    ]);

    var formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('assignment', assignment);
    formData.append('research_versions', researchVersions.join(','));

    fetch('/author/' + encodeURIComponent(name) + '/drafts/run', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            document.getElementById('drafts-detail').innerHTML = html;
            htmx.process(document.getElementById('drafts-detail'));
            authorLoadVersionLists(name);
        })
        .catch(function(err) {
            authorHideProgress();
            document.getElementById('drafts-detail').innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}

function authorResumeDraft(num) {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) return;

    authorShowProgress([
        "Looking up session ID...",
        "Opening Claude Code terminal..."
    ]);

    fetch('/author/' + encodeURIComponent(name) + '/drafts/' + num + '/resume', { method: 'POST' })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            document.getElementById('drafts-detail').innerHTML = html;
            htmx.process(document.getElementById('drafts-detail'));
        })
        .catch(function(err) {
            authorHideProgress();
            document.getElementById('drafts-detail').innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}

/* ---- Formats ---- */

function authorViewFormat(num) {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) return;

    fetch('/author/' + encodeURIComponent(name) + '/formats/' + num)
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            document.getElementById('formats-detail').innerHTML = html;
            htmx.process(document.getElementById('formats-detail'));
        });
}

function authorRunFormat() {
    var name = _currentAuthorName || (document.getElementById('author-name') ? document.getElementById('author-name').value.trim() : '');
    if (!name) { alert('Enter an assignment name.'); return; }

    var select = document.getElementById('format-draft-select');
    var draftVersion = select ? select.value : '';
    if (!draftVersion) {
        alert('Select a draft version to format.');
        return;
    }

    authorShowProgress([
        "Converting markdown to .docx...",
        "Applying OLG template styles..."
    ]);

    var formData = new FormData();
    formData.append('draft_version', draftVersion);

    fetch('/author/' + encodeURIComponent(name) + '/formats/run', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            document.getElementById('formats-detail').innerHTML = html;
            htmx.process(document.getElementById('formats-detail'));
            authorLoadVersionLists(name);
        })
        .catch(function(err) {
            authorHideProgress();
            document.getElementById('formats-detail').innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}


/* ============================================================
   QC ANALYSIS PAGE
   ============================================================ */

var EXTRACT_STEPS = [
    "Sending findings to extractor...",
    "Identifying policy issues in each row...",
    "Generating search queries...",
    "Saving extraction results...",
    "Almost there...",
];

var INVESTIGATE_STEPS = [
    "Initializing OLG search client...",
    "Running seed searches...",
    "Judge is reading OLG results...",
    "Searching for more evidence...",
    "Still searching. Policy is complicated.",
    "Assessing OLG coverage...",
    "One more row to go (maybe)...",
    "Compiling investigation results...",
    "Wrapping up...",
];

var CMR_CHECK_STEPS = [
    "Initializing CMR search client...",
    "Searching state regulations...",
    "Cross-checking against 106 CMR...",
    "Classifying regulatory coverage...",
];

var FNS_CHECK_STEPS = [
    "Initializing FNS search client...",
    "Searching federal handbook...",
    "Cross-checking against FNS 310...",
    "Classifying federal requirements...",
];

var CFR_CHECK_STEPS = [
    "Initializing CFR search client...",
    "Searching federal SNAP regulations...",
    "Cross-checking against 7 CFR...",
    "Classifying federal regulatory coverage...",
];

var _qcInterval = null;

function qcShowProgress(steps) {
    var resultsArea = document.getElementById('qc-results');
    var spinner = document.getElementById('qc-spinner');

    if (!spinner && resultsArea) {
        resultsArea.innerHTML =
            '<div id="qc-spinner" class="author-loading" style="display:none;">' +
            '<div class="spinner"></div>' +
            '<p class="qc-progress-text">Warming up...</p>' +
            '</div>';
        spinner = document.getElementById('qc-spinner');
    }

    var textEl = spinner ? spinner.querySelector('.qc-progress-text') : null;
    if (!spinner || !textEl) return;

    spinner.style.display = 'block';
    textEl.textContent = steps[0];
    var i = 0;

    if (_qcInterval) clearInterval(_qcInterval);
    _qcInterval = setInterval(function() {
        i++;
        if (i < steps.length) {
            textEl.style.opacity = 0;
            setTimeout(function() {
                textEl.textContent = steps[i];
                textEl.style.opacity = 1;
            }, 200);
        }
    }, 4000);
}

function qcHideProgress() {
    var spinner = document.getElementById('qc-spinner');
    if (spinner) spinner.style.display = 'none';
    if (_qcInterval) {
        clearInterval(_qcInterval);
        _qcInterval = null;
    }
}

var QC_PHASE_LABELS = {
    extract: 'extraction',
    investigate: 'investigation',
    cmr_check: 'CMR cross-check',
    fns_check: 'FNS cross-check',
    cfr_check: 'CFR cross-check',
};

function qcRerun(action) {
    var label = QC_PHASE_LABELS[action] || action;
    if (!confirm('Run ' + label + ' again? This will overwrite existing results.')) return;

    var nameEl = document.getElementById('qc-name');
    var name = nameEl ? nameEl.value.trim() : '';
    if (!name) return;

    var resultsArea = document.getElementById('qc-results');
    var formData = new FormData();
    formData.append('name', name);
    formData.append('rerun', '1');

    var steps;
    if (action === 'extract') steps = EXTRACT_STEPS;
    else if (action === 'investigate') steps = INVESTIGATE_STEPS;
    else if (action === 'cmr_check') steps = CMR_CHECK_STEPS;
    else if (action === 'fns_check') steps = FNS_CHECK_STEPS;
    else if (action === 'cfr_check') steps = CFR_CHECK_STEPS;

    if (steps) qcShowProgress(steps);

    var buttons = document.querySelectorAll('.qc-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch(qcActionUrl(action), { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            qcHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
            htmx.ajax('GET', '/qc/analyses', '#qc-analyses-list');
        })
        .catch(function(err) {
            qcHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        })
        .finally(function() {
            buttons.forEach(function(b) { b.disabled = false; });
        });
}

function qcActionUrl(action) {
    /* Cross-check actions route through /qc/source_check/{source};
       extract / investigate / upload keep their direct routes. */
    var m = /^(cmr|fns|cfr)_check$/.exec(action);
    if (m) return '/qc/source_check/' + m[1];
    return '/qc/' + action;
}

function qcRun(action) {
    var nameEl = document.getElementById('qc-name');
    var name = nameEl ? nameEl.value.trim() : '';

    var resultsArea = document.getElementById('qc-results');
    var url = qcActionUrl(action);

    if (action === 'upload') {
        var fileEl = document.getElementById('qc-file');
        if (!fileEl || !fileEl.files.length) {
            alert('Select a CSV file to upload.');
            return;
        }
        if (!name) {
            name = fileEl.files[0].name.replace(/\.csv$/i, '');
            if (nameEl) nameEl.value = name;
        }
        var formData = new FormData();
        formData.append('name', name);
        formData.append('file', fileEl.files[0]);

        qcShowProgress(["Uploading CSV...", "Validating columns...", "Building preview..."]);

    } else {
        if (!name) {
            alert('Enter an analysis name or load one from the sidebar.');
            if (nameEl) nameEl.focus();
            return;
        }
        var formData = new FormData();
        formData.append('name', name);

        if (action === 'extract') {
            qcShowProgress(EXTRACT_STEPS);
        } else if (action === 'investigate') {
            /* Collect selected row indices from checkboxes */
            var checkboxes = document.querySelectorAll('.qc-row-checkbox:checked');
            var indices = [];
            checkboxes.forEach(function(cb) { indices.push(cb.value); });
            formData.append('row_indices', indices.join(','));
            qcShowProgress(INVESTIGATE_STEPS);
        } else if (action === 'cmr_check') {
            qcShowProgress(CMR_CHECK_STEPS);
        } else if (action === 'fns_check') {
            qcShowProgress(FNS_CHECK_STEPS);
        } else if (action === 'cfr_check') {
            qcShowProgress(CFR_CHECK_STEPS);
        }
    }

    var buttons = document.querySelectorAll('.qc-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch(url, { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            qcHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
            if (action === 'upload') {
                var container = resultsArea.querySelector('[data-analysis-name]');
                if (container && nameEl) {
                    nameEl.value = container.dataset.analysisName;
                }
            }
            htmx.ajax('GET', '/qc/analyses', '#qc-analyses-list');
        })
        .catch(function(err) {
            qcHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        })
        .finally(function() {
            buttons.forEach(function(b) { b.disabled = false; });
        });
}

function loadQcAnalysis(name) {
    var nameEl = document.getElementById('qc-name');
    if (nameEl) nameEl.value = name;

    fetch('/qc/load/' + encodeURIComponent(name))
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            var resultsArea = document.getElementById('qc-results');
            var phase = data.latest_phase;

            /* Map meta phase names to view endpoint names */
            var viewPhase = null;
            if (phase === 'cfr_checked') {
                viewPhase = 'cfr_check';
            } else if (phase === 'fns_checked') {
                viewPhase = 'fns_check';
            } else if (phase === 'cmr_checked') {
                viewPhase = 'cmr_check';
            } else if (phase === 'investigated') {
                viewPhase = 'investigate';
            } else if (phase === 'extracted') {
                viewPhase = 'extract';
            } else if (phase === 'uploaded') {
                viewPhase = 'upload';
            }

            if (viewPhase) {
                fetch('/qc/view/' + encodeURIComponent(name) + '/' + viewPhase)
                    .then(function(resp) { return resp.text(); })
                    .then(function(html) {
                        resultsArea.innerHTML = html;
                        htmx.process(resultsArea);
                    });
            }
        });
}

function qcToggleAll(masterCheckbox) {
    var checkboxes = document.querySelectorAll('.qc-row-checkbox');
    checkboxes.forEach(function(cb) { cb.checked = masterCheckbox.checked; });
    qcUpdateSelectionCount();
}

function qcUpdateSelectionCount() {
    var total = document.querySelectorAll('.qc-row-checkbox').length;
    var selected = document.querySelectorAll('.qc-row-checkbox:checked').length;
    var countEl = document.getElementById('qc-selection-count');
    if (countEl) countEl.textContent = selected + ' of ' + total + ' selected';
}

function qcToggleDetail(rowIndex) {
    var detail = document.getElementById('qc-detail-' + rowIndex);
    if (detail) {
        detail.style.display = detail.style.display === 'none' ? 'table-row' : 'none';
    }
}

function sendToAuthor(analysisName, rowIndex, gapSummary) {
    /* Navigate to Author tab with pre-filled fields */
    var assignmentName = 'qc_' + analysisName + '_row' + rowIndex;
    var assignment = 'Write OLG guidance for the policy gap identified in:\n' +
        'output/qc_analysis/' + analysisName + '/results/row_' + String(rowIndex).padStart(3, '0') + '.json\n\n' +
        'The gap: ' + gapSummary;

    window.location.href = '/author';
    setTimeout(function() {
        var nameEl = document.getElementById('author-name');
        var assignEl = document.getElementById('author-assignment');
        if (nameEl) nameEl.value = assignmentName;
        if (assignEl) assignEl.value = assignment;
    }, 500);
}


/* ============================================================
   CONVERT TAB
   ============================================================ */

var _convertProgressInterval = null;

function convertShowProgress(steps) {
    var spinner = document.getElementById('convert-spinner');
    if (!spinner) return;
    spinner.style.display = 'block';
    var textEl = spinner.querySelector('.convert-progress-text');
    if (textEl) textEl.textContent = steps[0];
    var i = 0;
    _convertProgressInterval = setInterval(function() {
        i++;
        if (i < steps.length && textEl) {
            textEl.style.opacity = 0;
            setTimeout(function() {
                textEl.textContent = steps[i];
                textEl.style.opacity = 1;
            }, 200);
        }
    }, 3000);
}

function convertHideProgress() {
    var spinner = document.getElementById('convert-spinner');
    if (spinner) spinner.style.display = 'none';
    if (_convertProgressInterval) {
        clearInterval(_convertProgressInterval);
        _convertProgressInterval = null;
    }
}

function convertUpload() {
    var fileEl = document.getElementById('convert-file');
    if (!fileEl || !fileEl.files.length) {
        alert('Select a .docx file to upload.');
        return;
    }

    var modeEl = document.querySelector('input[name="change_mode"]:checked');
    var changeMode = modeEl ? modeEl.value : 'accept';

    var formData = new FormData();
    formData.append('file', fileEl.files[0]);
    formData.append('change_mode', changeMode);

    var resultsArea = document.getElementById('convert-results');
    convertShowProgress([
        "Reading document...",
        "Resolving tracked changes...",
        "Classifying tables...",
        "Generating markdown..."
    ]);

    fetch('/convert/upload', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            convertHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
        })
        .catch(function(err) {
            convertHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}

function convertToggleMode(newMode) {
    var modeRadios = document.querySelectorAll('input[name="change_mode"]');
    modeRadios.forEach(function(r) { r.checked = (r.value === newMode); });
    convertUpload();
}

function convertFormat() {
    var mdEl = document.getElementById('convert-markdown');
    var stemEl = document.getElementById('convert-filename');
    if (!mdEl || !stemEl) return;

    var formData = new FormData();
    formData.append('markdown', mdEl.value);
    formData.append('stem', stemEl.value);

    var resultsArea = document.getElementById('convert-results');
    convertShowProgress(["Applying OLG template styles...", "Generating .docx..."]);

    fetch('/convert/format', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            convertHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
        })
        .catch(function(err) {
            convertHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        });
}
