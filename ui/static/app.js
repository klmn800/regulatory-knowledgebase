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

function authorShowProgress(steps) {
    var resultsArea = document.getElementById('author-results');
    var spinner = document.getElementById('author-spinner');

    /* Recreate the spinner if a view template replaced it */
    if (!spinner && resultsArea) {
        resultsArea.innerHTML =
            '<div id="author-spinner" class="author-loading" style="display:none;">' +
            '<div class="spinner"></div>' +
            '<p class="author-progress-text">Warming up...</p>' +
            '</div>';
        spinner = document.getElementById('author-spinner');
    }

    var textEl = spinner ? spinner.querySelector('.author-progress-text') : null;
    if (!spinner || !textEl) return;

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

function authorRun(action) {
    var nameEl = document.getElementById('author-name');
    var assignEl = document.getElementById('author-assignment');
    var name = nameEl ? nameEl.value.trim() : '';
    var assignment = assignEl ? assignEl.value.trim() : '';

    if (!name) {
        alert('Enter an assignment name.');
        if (nameEl) nameEl.focus();
        return;
    }

    var resultsArea = document.getElementById('author-results');
    var formData = new FormData();
    formData.append('name', name);
    formData.append('assignment', assignment);

    var url = '/author/' + action;

    if (action === 'research') {
        if (!assignment) {
            alert('Enter an assignment description for research.');
            if (assignEl) assignEl.focus();
            return;
        }
        authorShowProgress(RESEARCH_STEPS);
    } else if (action === 'draft') {
        authorShowProgress([
            "Composing authoring prompt...",
            "Launching Claude Code terminal...",
            "Opening new window..."
        ]);
    } else if (action === 'format') {
        authorShowProgress([
            "Converting markdown to .docx...",
            "Applying OLG template styles..."
        ]);
    } else if (action === 'resume') {
        authorShowProgress([
            "Looking up session ID...",
            "Opening Claude Code terminal..."
        ]);
    }

    /* Disable buttons during request */
    var buttons = document.querySelectorAll('.author-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch(url, { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
            htmx.ajax('GET', '/author/assignments', '#assignments-list');
        })
        .catch(function(err) {
            authorHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        })
        .finally(function() {
            buttons.forEach(function(b) { b.disabled = false; });
        });
}

/* Re-run a phase (called from view templates after confirm) */
function authorRerun(action) {
    if (!confirm('Run ' + action + ' again? This will create a new version.')) return;

    var nameEl = document.getElementById('author-name');
    var assignEl = document.getElementById('author-assignment');
    var name = nameEl ? nameEl.value.trim() : '';
    var assignment = assignEl ? assignEl.value.trim() : '';

    if (!name) {
        alert('Enter an assignment name.');
        return;
    }

    if (action === 'research' && !assignment) {
        alert('Enter an assignment description for research.');
        if (assignEl) assignEl.focus();
        return;
    }

    var resultsArea = document.getElementById('author-results');
    var formData = new FormData();
    formData.append('name', name);
    formData.append('assignment', assignment);
    formData.append('rerun', '1');

    var url = '/author/' + action;

    if (action === 'research') {
        authorShowProgress(RESEARCH_STEPS);
    } else if (action === 'draft') {
        authorShowProgress([
            "Composing authoring prompt...",
            "Launching Claude Code terminal...",
            "Opening new window..."
        ]);
    } else if (action === 'format') {
        authorShowProgress([
            "Converting markdown to .docx...",
            "Applying OLG template styles..."
        ]);
    }

    var buttons = document.querySelectorAll('.author-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch(url, { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
            htmx.ajax('GET', '/author/assignments', '#assignments-list');
        })
        .catch(function(err) {
            authorHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        })
        .finally(function() {
            buttons.forEach(function(b) { b.disabled = false; });
        });
}

/* Resume a specific Claude Code session (called from draft view template) */
function authorResume(sessionId) {
    var nameEl = document.getElementById('author-name');
    var name = nameEl ? nameEl.value.trim() : '';
    if (!name) {
        alert('Enter an assignment name.');
        return;
    }

    var resultsArea = document.getElementById('author-results');
    var formData = new FormData();
    formData.append('name', name);
    formData.append('session_id', sessionId);

    authorShowProgress([
        "Looking up session ID...",
        "Opening Claude Code terminal..."
    ]);

    var buttons = document.querySelectorAll('.author-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch('/author/resume', { method: 'POST', body: formData })
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            authorHideProgress();
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
        })
        .catch(function(err) {
            authorHideProgress();
            resultsArea.innerHTML = '<p>Error: ' + err.message + '</p>';
        })
        .finally(function() {
            buttons.forEach(function(b) { b.disabled = false; });
        });
}

/* Navigate to a specific version of a phase output */
function authorViewVersion(phase, versionNum) {
    var nameEl = document.getElementById('author-name');
    var name = nameEl ? nameEl.value.trim() : '';
    if (!name) return;

    var resultsArea = document.getElementById('author-results');
    var url = '/author/view/' + encodeURIComponent(name) + '/' + phase + '?v=' + versionNum;

    fetch(url)
        .then(function(resp) { return resp.text(); })
        .then(function(html) {
            resultsArea.innerHTML = html;
            htmx.process(resultsArea);
        });
}

function loadAssignment(name) {
    fetch('/author/load/' + encodeURIComponent(name))
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            var nameEl = document.getElementById('author-name');
            var assignEl = document.getElementById('author-assignment');
            if (nameEl) nameEl.value = data.name;
            if (assignEl) assignEl.value = data.assignment || '';

            /* Auto-show the most advanced phase output */
            var phase = null;
            if (data.has_docx) phase = 'format';
            else if (data.has_draft) phase = 'draft';
            else if (data.has_research) phase = 'research';

            if (phase) {
                var resultsArea = document.getElementById('author-results');
                fetch('/author/view/' + encodeURIComponent(name) + '/' + phase)
                    .then(function(resp) { return resp.text(); })
                    .then(function(html) {
                        resultsArea.innerHTML = html;
                        htmx.process(resultsArea);
                    });
            }
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

    if (steps) qcShowProgress(steps);

    var buttons = document.querySelectorAll('.qc-actions .btn');
    buttons.forEach(function(b) { b.disabled = true; });

    fetch('/qc/' + action, { method: 'POST', body: formData })
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

function qcRun(action) {
    var nameEl = document.getElementById('qc-name');
    var name = nameEl ? nameEl.value.trim() : '';

    var resultsArea = document.getElementById('qc-results');
    var url = '/qc/' + action;

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
            if (phase === 'fns_checked') {
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
