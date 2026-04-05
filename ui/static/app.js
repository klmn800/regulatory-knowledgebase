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
    var spinner = document.getElementById('author-spinner');
    var textEl = spinner ? spinner.querySelector('.author-progress-text') : null;
    if (!spinner || !textEl) return;

    /* Clear any previous result */
    var prev = document.querySelector('.author-result-container');
    if (prev) prev.remove();

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
            /* Refresh assignments list */
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

function loadAssignment(name) {
    fetch('/author/load/' + encodeURIComponent(name))
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            var nameEl = document.getElementById('author-name');
            var assignEl = document.getElementById('author-assignment');
            if (nameEl) nameEl.value = data.name;
            if (assignEl) assignEl.value = data.assignment || '';
        });
}
