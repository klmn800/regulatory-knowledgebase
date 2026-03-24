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
