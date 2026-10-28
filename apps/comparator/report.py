#!/usr/bin/env python3
"""Generate HTML report from FNS vs OLG comparator results.

Usage:
    python apps/comparator/report.py                # Auto-detect CSVs, output to output/comparator/
    python apps/comparator/report.py -o report.html # Custom output path
    python apps/comparator/report.py --open         # Generate and open in browser
"""

import csv
import json
import argparse
import webbrowser
from pathlib import Path
from html import escape as _esc
from datetime import datetime
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "output" / "comparator"

CHAPTER_NAMES = {
    "7": "Budgeting",
    "8": "Non-Financial Eligibility",
    "9": "Resources",
    "10": "Income",
    "11": "Deductions",
}

# (text_color, bg_color, display_label)
CLASSIFICATION_STYLES = {
    "match":                              ("#166534", "#dcfce7", "Match"),
    "not_applicable":                     ("#374151", "#f3f4f6", "N/A"),
    "partial_match":                      ("#92400e", "#fef3c7", "Partial Match"),
    "confirmed_gap":                      ("#991b1b", "#fee2e2", "Confirmed Gap"),
    "different_standard":                 ("#9a3412", "#ffedd5", "Different Standard"),
    "policy_present_procedures_missing":  ("#6b21a8", "#f3e8ff", "Procedures Missing"),
}

PRIORITY_COLORS = {
    "HIGH":   "#dc2626",
    "MEDIUM": "#ea580c",
    "LOW":    "#6b7280",
}

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = r"""
/* ── Theme variables ──────────────────────────────────────── */
:root {
    --bg-page: #f9fafb;
    --bg-surface: #fff;
    --bg-surface-alt: #fafbfc;
    --bg-hover: #f3f4f6;
    --bg-expanded: #eff6ff;
    --bg-input: #f3f4f6;
    --bg-input-hover: #e5e7eb;
    --text-primary: #1f2937;
    --text-heading: #111827;
    --text-secondary: #374151;
    --text-muted: #6b7280;
    --text-faint: #9ca3af;
    --border: #e5e7eb;
    --border-light: #f3f4f6;
    --link: #2563eb;
    --expand-bg: #dbeafe;
    --expand-text: #2563eb;
    --toast-bg: #1f2937;
    --toast-text: #fff;
}

body.dark {
    --bg-page: #0f172a;
    --bg-surface: #1e293b;
    --bg-surface-alt: #162032;
    --bg-hover: #334155;
    --bg-expanded: #1e3a5f;
    --bg-input: #334155;
    --bg-input-hover: #475569;
    --text-primary: #e2e8f0;
    --text-heading: #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --text-faint: #64748b;
    --border: #334155;
    --border-light: #1e293b;
    --link: #60a5fa;
    --expand-bg: #1e3a5f;
    --expand-text: #93c5fd;
    --toast-bg: #f1f5f9;
    --toast-text: #0f172a;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
    background: var(--bg-page);
    line-height: 1.5;
    padding: 2rem 2.5rem;
    transition: background 0.2s, color 0.2s;
}

header { margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: flex-start; }
.header-left {}
h1 { font-size: 1.75rem; color: var(--text-heading); margin-bottom: 0.125rem; }
.subtitle { font-size: 1rem; color: var(--text-muted); margin-bottom: 0.125rem; }
.meta { font-size: 0.8125rem; color: var(--text-faint); }

/* ── Dark mode toggle ─────────────────────────────────────── */
.theme-toggle {
    background: var(--bg-input); border: 1px solid var(--border);
    border-radius: 0.5rem; padding: 0.375rem 0.75rem;
    font-size: 0.8125rem; color: var(--text-muted);
    cursor: pointer; transition: all 0.15s;
    display: flex; align-items: center; gap: 0.375rem;
    white-space: nowrap; margin-top: 0.25rem;
}
.theme-toggle:hover { background: var(--bg-input-hover); color: var(--text-primary); }

/* ── Summary cards ─────────────────────────────────────────── */
.summary {
    display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap;
}
.card {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 0.5rem; padding: 0.75rem 1.25rem; min-width: 100px;
    text-align: center; border-top: 3px solid var(--border);
    transition: background 0.2s;
}
.card.total       { border-top-color: #2563eb; }
.card.total .card-num { color: #2563eb; }
.card.actionable  { border-top-color: #dc2626; }
.card.actionable .card-num { color: #dc2626; }
.card-num   { font-size: 1.375rem; font-weight: 700; }
.card-label { font-size: 0.6875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Filters ───────────────────────────────────────────────── */
.filters { margin-bottom: 1rem; }
.filter-group {
    display: flex; align-items: center; gap: 0.375rem;
    margin-bottom: 0.375rem; flex-wrap: wrap;
}
.filter-label {
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; min-width: 90px;
}
.filter-btn {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 9999px; padding: 0.1875rem 0.625rem;
    font-size: 0.75rem; color: var(--text-secondary);
    cursor: pointer; transition: all 0.15s;
}
.filter-btn:hover { background: var(--bg-hover); }
.filter-btn.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.filter-btn.actionable-btn.active { background: #dc2626; border-color: #dc2626; }
.filter-btn.fav-filter-btn.active { background: #d97706; border-color: #d97706; }

/* ── Row count ─────────────────────────────────────────────── */
.row-count { font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 0.5rem; }

/* ── Expand/Collapse all ───────────────────────────────────── */
.toolbar {
    display: flex; gap: 0.5rem; align-items: center;
    margin-bottom: 0.5rem;
}
.toolbar-btn {
    background: none; border: 1px solid var(--border);
    border-radius: 0.375rem; padding: 0.25rem 0.625rem;
    font-size: 0.75rem; color: var(--text-muted); cursor: pointer;
}
.toolbar-btn:hover { background: var(--bg-hover); color: var(--text-primary); }

/* ── Table ─────────────────────────────────────────────────── */
table {
    width: 100%; border-collapse: collapse; background: var(--bg-surface);
    border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden;
    transition: background 0.2s;
}
thead { position: sticky; top: 0; z-index: 10; }
th {
    background: var(--bg-page); border-bottom: 2px solid var(--border);
    padding: 0.625rem 0.75rem; text-align: left;
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em;
    transition: background 0.2s;
}

/* Main row */
.main-row { cursor: pointer; transition: background 0.1s; }
.main-row:hover { background: var(--bg-hover); }
.main-row td {
    padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-light);
    font-size: 0.8125rem; vertical-align: top;
}
.main-row.expanded { background: var(--bg-expanded); }

/* Finding highlight (L3-escalated) */
.main-row[data-fnd="true"] td.col-fav {
    box-shadow: inset 3px 0 0 #dc2626;
}
/* Partial-match / needs-attention subtle highlight */
.main-row[data-act="true"][data-fnd="false"] td.col-fav {
    box-shadow: inset 3px 0 0 #f59e0b;
}

.col-fav    { width: 2rem; text-align: center; padding-left: 0.5rem !important; padding-right: 0 !important; }
.col-ch     { width: 2.5rem; text-align: center; }
.col-sec    { width: 4.5rem; font-weight: 600; }
.col-title  { width: 22%; }
.col-cls    { width: 9rem; }
.col-conf   { width: 3.5rem; text-align: center; }
.col-finding { font-size: 0.8125rem; color: var(--text-secondary); }
.col-expand { width: 2rem; text-align: center; }

/* Badge */
.badge {
    display: inline-block; padding: 0.0625rem 0.4375rem;
    border-radius: 9999px; font-size: 0.6875rem; font-weight: 600;
    white-space: nowrap;
}

/* Favorite star */
.fav-btn {
    background: none; border: none; cursor: pointer;
    font-size: 1rem; line-height: 1; padding: 0;
    color: var(--border); transition: color 0.15s, transform 0.1s;
}
.fav-btn:hover { color: #d97706; transform: scale(1.2); }
.fav-btn.active { color: #d97706; }

/* Expand icon */
.expand-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.375rem; height: 1.375rem; border-radius: 50%;
    background: var(--bg-input); color: var(--text-muted); font-size: 0.8125rem;
    font-weight: 600; transition: transform 0.2s, background 0.2s;
}
.main-row.expanded .expand-icon {
    transform: rotate(45deg); background: var(--expand-bg); color: var(--expand-text);
}

/* ── Detail row ────────────────────────────────────────────── */
.detail-row { display: none; }
.detail-row.visible { display: table-row; }
.detail-row > td { padding: 0; border-bottom: 2px solid var(--border); }

.detail-panel {
    display: grid; grid-template-columns: 1fr 280px;
    gap: 1.25rem; padding: 1.25rem; background: var(--bg-surface-alt);
    border-top: 1px solid var(--border); transition: background 0.2s;
}
.detail-notes {}
.detail-section { margin-bottom: 0.875rem; }
.detail-section h4 {
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;
    padding-bottom: 0.1875rem; border-bottom: 1px solid var(--border);
}
.detail-section p {
    font-size: 0.8125rem; line-height: 1.65; color: var(--text-secondary);
}

/* Detail meta sidebar */
.detail-meta {
    border-left: 1px solid var(--border); padding-left: 1.25rem;
}
.detail-meta > h4 {
    font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.625rem;
}
.meta-item { margin-bottom: 0.625rem; }
.meta-label {
    display: block; font-size: 0.625rem; font-weight: 600; color: var(--text-faint);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.0625rem;
}
.meta-value { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.5; }
.meta-value a { color: var(--link); text-decoration: none; }
.meta-value a:hover { text-decoration: underline; }

.session-id {
    font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
    font-size: 0.6875rem; background: var(--bg-input);
    padding: 0.0625rem 0.3125rem; border-radius: 0.25rem;
    cursor: pointer; word-break: break-all; transition: background 0.15s;
}
.session-id:hover { background: var(--bg-input-hover); }

.priority-badge { font-weight: 700; }
.muted { color: var(--text-faint); font-style: italic; }

/* ── Notes ─────────────────────────────────────────────────── */
.col-note { width: 1.5rem; text-align: center; padding: 0 !important; }
.note-indicator {
    font-size: 0.8125rem; color: var(--text-faint);
    visibility: hidden; cursor: default;
}
.main-row[data-note="true"] .note-indicator { visibility: visible; color: #d97706; }

.note-section { margin-top: 0.25rem; }
.note-section h4 { color: #d97706 !important; }
.note-area {
    width: 100%; min-height: 4rem; max-height: 12rem; resize: vertical;
    font-family: inherit; font-size: 0.8125rem; line-height: 1.5;
    padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.375rem;
    background: var(--bg-surface); color: var(--text-primary);
    transition: border-color 0.15s;
}
.note-area:focus { outline: none; border-color: #d97706; }
.note-saved {
    font-size: 0.6875rem; color: #d97706; opacity: 0;
    transition: opacity 0.3s; margin-left: 0.5rem;
}
.note-saved.show { opacity: 1; }

.filter-btn.note-filter-btn.active { background: #d97706; border-color: #d97706; color: #fff; }

/* ── Export button ────────────────────────────────────────── */
.export-btn {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 0.375rem; padding: 0.25rem 0.75rem;
    font-size: 0.75rem; color: var(--text-secondary); cursor: pointer;
    transition: all 0.15s; margin-left: auto;
}
.export-btn:hover { background: var(--bg-hover); color: var(--text-primary); border-color: var(--text-muted); }

/* Hidden (filtered) */
.main-row.hidden, .detail-row.hidden { display: none !important; }

/* ── Footer ────────────────────────────────────────────────── */
footer {
    margin-top: 1.5rem; padding: 1.25rem; background: var(--bg-surface);
    border: 1px solid var(--border); border-radius: 0.5rem;
    transition: background 0.2s;
}
footer h3 { font-size: 1rem; margin-bottom: 0.375rem; color: var(--text-heading); }
footer h4 { font-size: 0.875rem; margin-top: 0.75rem; margin-bottom: 0.25rem; color: var(--text-secondary); }
footer p, footer li { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.6; }
footer ul { padding-left: 1.25rem; }
footer li { margin-bottom: 0.1875rem; }

/* ── Toast ─────────────────────────────────────────────────── */
.toast {
    position: fixed; bottom: 2rem; right: 2rem;
    background: var(--toast-bg); color: var(--toast-text);
    padding: 0.625rem 1rem; border-radius: 0.5rem;
    font-size: 0.8125rem; opacity: 0; transition: opacity 0.3s; z-index: 1000;
    pointer-events: none;
}
.toast.show { opacity: 1; }

/* ── Print ─────────────────────────────────────────────────── */
@media print {
    body { background: #fff !important; padding: 0.5rem; color: #000 !important; }
    .filters, .summary, .toolbar, .theme-toggle, .fav-btn { display: none; }
    .detail-row.visible { display: table-row !important; }
    .expand-icon { display: none; }
    .main-row { cursor: default; }
    footer { break-before: page; }
}
"""

# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------
JS = r"""
/* ── Dark mode ──────────────────────────────────────────────── */
function initTheme() {
    var saved = localStorage.getItem('comparator_theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark');
    }
    updateThemeBtn();
}

function toggleTheme() {
    document.body.classList.toggle('dark');
    var isDark = document.body.classList.contains('dark');
    localStorage.setItem('comparator_theme', isDark ? 'dark' : 'light');
    updateThemeBtn();
}

function updateThemeBtn() {
    var btn = document.getElementById('theme-btn');
    var isDark = document.body.classList.contains('dark');
    btn.textContent = isDark ? '\u2600 Light mode' : '\u263E Dark mode';
}

/* ── Favorites ──────────────────────────────────────────────── */
var favorites = new Set(JSON.parse(localStorage.getItem('comparator_favorites') || '[]'));

function initFavorites() {
    favorites.forEach(function(key) {
        var btn = document.querySelector('.fav-btn[data-key="' + key + '"]');
        if (btn) btn.classList.add('active');
    });
    // Also mark main-rows with data-fav
    document.querySelectorAll('.main-row').forEach(function(r) {
        r.dataset.fav = favorites.has(r.dataset.key) ? 'true' : 'false';
    });
    updateFavCount();
}

function toggleFav(btn, evt) {
    evt.stopPropagation();
    var key = btn.dataset.key;
    if (favorites.has(key)) {
        favorites.delete(key);
        btn.classList.remove('active');
    } else {
        favorites.add(key);
        btn.classList.add('active');
    }
    // Sync data-fav on main-row
    var row = btn.closest('tr');
    if (row) row.dataset.fav = favorites.has(key) ? 'true' : 'false';
    // Also sync on detail-row
    var detail = row.nextElementSibling;
    if (detail && detail.classList.contains('detail-row')) {
        detail.dataset.fav = row.dataset.fav;
    }
    localStorage.setItem('comparator_favorites', JSON.stringify(Array.from(favorites)));
    updateFavCount();
}

function updateFavCount() {
    var el = document.getElementById('fav-count');
    if (el) el.textContent = favorites.size;
}

function filterFavorites(btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.fav === 'true'; });
}

/* ── Row expand/collapse ────────────────────────────────────── */
function toggleRow(i) {
    var detail = document.getElementById('detail-' + i);
    var mainRow = detail.previousElementSibling;
    if (detail.classList.contains('visible')) {
        detail.classList.remove('visible');
        mainRow.classList.remove('expanded');
    } else {
        detail.classList.add('visible');
        mainRow.classList.add('expanded');
    }
}

/* ── Filters ────────────────────────────────────────────────── */
function clearActive() {
    document.querySelectorAll('.filter-btn').forEach(function(b) {
        b.classList.remove('active');
    });
}

function applyFilter(showFn) {
    document.querySelectorAll('.main-row').forEach(function(r) {
        var show = showFn(r);
        r.classList.toggle('hidden', !show);
        if (!show) {
            var detail = r.nextElementSibling;
            if (detail && detail.classList.contains('detail-row')) {
                detail.classList.add('hidden');
                detail.classList.remove('visible');
                r.classList.remove('expanded');
            }
        } else {
            var detail = r.nextElementSibling;
            if (detail && detail.classList.contains('detail-row')) {
                detail.classList.remove('hidden');
            }
        }
    });
    updateCount();
    updateExportCount();
}

function filterAll(btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function() { return true; });
}

function filterFindings(btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.fnd === 'true'; });
}

function filterActionable(btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.act === 'true'; });
}

function filterChapter(ch, btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.ch === ch; });
}

function filterClass(cls, btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.cls === cls; });
}

function expandAll() {
    document.querySelectorAll('.main-row:not(.hidden)').forEach(function(r) {
        var detail = r.nextElementSibling;
        if (detail && detail.classList.contains('detail-row') && !detail.classList.contains('hidden')) {
            detail.classList.add('visible');
            r.classList.add('expanded');
        }
    });
}

function collapseAll() {
    document.querySelectorAll('.detail-row').forEach(function(d) {
        d.classList.remove('visible');
    });
    document.querySelectorAll('.main-row').forEach(function(r) {
        r.classList.remove('expanded');
    });
}

function updateCount() {
    var visible = document.querySelectorAll('.main-row:not(.hidden)').length;
    var total = document.querySelectorAll('.main-row').length;
    var el = document.getElementById('row-count');
    el.textContent = visible === total
        ? 'Showing all ' + total + ' sections'
        : 'Showing ' + visible + ' of ' + total + ' sections';
}

/* ── Clipboard ──────────────────────────────────────────────── */
function copyToClipboard(el, evt) {
    evt.stopPropagation();
    var sessionId = el.textContent;
    var cmd = 'claude --resume ' + sessionId;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(cmd).then(function() {
            showToast('Copied: ' + cmd);
        });
    } else {
        var ta = document.createElement('textarea');
        ta.value = cmd;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('Copied: ' + cmd);
    }
}

function showToast(msg) {
    var toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function() { toast.classList.remove('show'); }, 2500);
}

/* ── Notes ──────────────────────────────────────────────────── */
var notes = JSON.parse(localStorage.getItem('comparator_notes') || '{}');
var _noteTimers = {};

function initNotes() {
    Object.keys(notes).forEach(function(key) {
        var ta = document.querySelector('.note-area[data-key="' + key + '"]');
        if (ta) ta.value = notes[key];
    });
    document.querySelectorAll('.main-row').forEach(function(r) {
        var key = r.dataset.key;
        r.dataset.note = (notes[key] && notes[key].trim()) ? 'true' : 'false';
        var detail = r.nextElementSibling;
        if (detail && detail.classList.contains('detail-row')) {
            detail.dataset.note = r.dataset.note;
        }
    });
    updateNoteCount();
    updateExportCount();
}

function onNoteInput(ta) {
    var key = ta.dataset.key;
    clearTimeout(_noteTimers[key]);
    _noteTimers[key] = setTimeout(function() { saveNote(ta); }, 500);
}

function saveNote(ta) {
    var key = ta.dataset.key;
    var val = ta.value.trim();
    if (val) {
        notes[key] = ta.value;
    } else {
        delete notes[key];
    }
    localStorage.setItem('comparator_notes', JSON.stringify(notes));
    var mainRow = document.querySelector('.main-row[data-key="' + key + '"]');
    if (mainRow) {
        mainRow.dataset.note = val ? 'true' : 'false';
        var detail = mainRow.nextElementSibling;
        if (detail) detail.dataset.note = mainRow.dataset.note;
    }
    var saved = ta.parentElement.querySelector('.note-saved');
    if (saved) {
        saved.classList.add('show');
        clearTimeout(saved._timer);
        saved._timer = setTimeout(function() { saved.classList.remove('show'); }, 1500);
    }
    updateNoteCount();
}

function updateNoteCount() {
    var el = document.getElementById('note-count');
    if (el) {
        var count = Object.keys(notes).filter(function(k) { return notes[k] && notes[k].trim(); }).length;
        el.textContent = count;
    }
}

function filterNotes(btn) {
    clearActive();
    btn.classList.add('active');
    applyFilter(function(r) { return r.dataset.note === 'true'; });
}

/* ── CSV Export ─────────────────────────────────────────────── */
function exportCSV() {
    var rows = document.querySelectorAll('.main-row:not(.hidden)');
    if (rows.length === 0) { showToast('No rows to export'); return; }
    var headers = ['Chapter','Section','Title','Classification','Confidence',
        'FNS Summary','Layer 1 Note','Layer 2 Note','Layer 3 Note',
        'OLG Matches','OLG URLs','Action Needed','Priority','CMR Section',
        'Session ID','Tokens In','Tokens Out','Est Cost','My Notes'];
    var csvRows = [headers.map(csvEscape).join(',')];
    rows.forEach(function(r) {
        var d = JSON.parse(r.dataset.exp);
        var key = r.dataset.key;
        var note = notes[key] || '';
        var fields = [
            d.ch, d.sec, d.title, d.cls, d.conf, d.summary,
            d.l1, d.l2, d.l3, d.olg, d.urls, d.action, d.priority,
            d.cmr, d.sid, d.tin, d.tout, d.cost, note
        ];
        csvRows.push(fields.map(csvEscape).join(','));
    });
    var csv = csvRows.join('\r\n');
    var bom = '\uFEFF';
    var blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    var now = new Date();
    var ds = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
    a.href = url;
    a.download = 'policy_report_export_' + ds + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported ' + rows.length + ' rows');
}

function csvEscape(val) {
    if (val == null) val = '';
    val = String(val);
    if (val.indexOf(',') !== -1 || val.indexOf('"') !== -1 || val.indexOf('\n') !== -1 || val.indexOf('\r') !== -1) {
        return '"' + val.replace(/"/g, '""') + '"';
    }
    return val;
}

function updateExportCount() {
    var el = document.getElementById('export-count');
    if (el) {
        el.textContent = document.querySelectorAll('.main-row:not(.hidden)').length;
    }
}

/* ── Init ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initFavorites();
    initNotes();
});
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csvs(data_dir: Path) -> list[dict]:
    """Load comparator CSVs. Prefers compiled CSVs (full text) over per-chapter originals."""
    # Prefer compiled CSVs (have full fns_summary text)
    compiled = list(data_dir.glob("comparison_compiled_*.csv"))
    if compiled:
        compiled.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        files = [compiled[0]]  # Use most recent compiled CSV
    else:
        files = list(data_dir.glob("comparison_claude-code_*_FNS-*.csv"))
        files.sort(key=lambda f: int(f.stem.split("FNS-")[1]))
    rows = []
    for f in files:
        with open(f, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                rows.append(row)
    return rows


FINDING_CLASSIFICATIONS = {"confirmed_gap", "different_standard",
                           "policy_present_procedures_missing"}


def is_finding(row: dict) -> bool:
    """L3-escalated findings: confirmed_gap, different_standard, procedures_missing."""
    return row.get("classification", "") in FINDING_CLASSIFICATIONS


def is_actionable(row: dict) -> bool:
    """Any row with a non-'none' action_needed (includes partial_match)."""
    action = row.get("action_needed", "")
    return bool(action) and action.lower() != "none"


def row_key(row: dict) -> str:
    """Unique key for a row: 'ch_section'."""
    return f"{row['fns_chapter']}_{row['fns_section']}"


def truncate(text: str, n: int = 180) -> str:
    if not text or len(text) <= n:
        return text or ""
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "\u2026"


def esc(text: str) -> str:
    return _esc(text or "", quote=True)


def make_olg_links_html(matches_str: str, urls_str: str) -> str:
    if not matches_str:
        return '<span class="muted">None found</span>'
    names = [n.strip() for n in matches_str.split(";") if n.strip()]
    url_list = [u.strip() for u in (urls_str or "").split(";")] if urls_str else []
    while len(url_list) < len(names):
        url_list.append("")
    seen = set()
    links = []
    for name, url in zip(names, url_list):
        if name in seen:
            continue
        seen.add(name)
        if url:
            links.append(f'<a href="{esc(url)}" target="_blank">{esc(name)}</a>')
        else:
            links.append(f"<span>{esc(name)}</span>")
    return "<br>".join(links)


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

NCOLS = 9  # fav + note + ch + sec + title + cls + conf + finding + expand


def generate_html(rows: list[dict]) -> str:
    total = len(rows)
    by_class = Counter(r["classification"] for r in rows)
    by_chapter = Counter(r["fns_chapter"] for r in rows)
    findings_count = sum(1 for r in rows if is_finding(r))
    actionable_count = sum(1 for r in rows if is_actionable(r))
    chapters = sorted(by_chapter.keys(), key=lambda x: int(x))

    h = []  # html fragments
    h.append("<!DOCTYPE html>")
    h.append('<html lang="en">')
    h.append("<head>")
    h.append('<meta charset="UTF-8">')
    h.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h.append("<title>FNS vs OLG Policy Comparison Report</title>")
    h.append(f"<style>{CSS}</style>")
    h.append("</head>")
    h.append("<body>")

    # ── Header ──
    h.append("<header>")
    h.append('<div class="header-left">')
    h.append("<h1>FNS vs OLG Policy Comparison Report</h1>")
    h.append('<p class="subtitle">SNAP Quality Control Handbook (FNS 310) vs. '
             "the Online Guide</p>")
    h.append(f'<p class="meta">Generated {datetime.now().strftime("%B %d, %Y")} '
             f"&mdash; {total} sections across {len(chapters)} chapters "
             f"(Ch {', '.join(chapters)})</p>")
    h.append("</div>")
    h.append('<button class="theme-toggle" id="theme-btn" onclick="toggleTheme()">'
             "\u263E Dark mode</button>")
    h.append("</header>")

    # ── Summary cards ──
    h.append('<section class="summary">')
    h.append(f'<div class="card total"><div class="card-num">{total}</div>'
             '<div class="card-label">Total</div></div>')
    h.append(f'<div class="card actionable"><div class="card-num">{findings_count}</div>'
             '<div class="card-label">Findings</div></div>')
    for cls_key in ["match", "not_applicable", "partial_match",
                    "confirmed_gap", "different_standard",
                    "policy_present_procedures_missing"]:
        count = by_class.get(cls_key, 0)
        if count == 0:
            continue
        tc, bg, label = CLASSIFICATION_STYLES[cls_key]
        h.append(f'<div class="card" style="border-top-color:{tc}">'
                 f'<div class="card-num" style="color:{tc}">{count}</div>'
                 f'<div class="card-label">{label}</div></div>')
    h.append("</section>")

    # ── Filters ──
    h.append('<section class="filters">')

    h.append('<div class="filter-group">')
    h.append('<span class="filter-label">Show:</span>')
    h.append(f'<button class="filter-btn active" onclick="filterAll(this)">'
             f"All ({total})</button>")
    h.append(f'<button class="filter-btn actionable-btn" '
             f'onclick="filterFindings(this)">Findings ({findings_count})</button>')
    h.append(f'<button class="filter-btn" '
             f'onclick="filterActionable(this)">Needs Attention ({actionable_count})</button>')
    h.append('<button class="filter-btn fav-filter-btn" '
             'onclick="filterFavorites(this)">'
             '\u2605 Favorites (<span id="fav-count">0</span>)</button>')
    h.append('<button class="filter-btn note-filter-btn" '
             'onclick="filterNotes(this)">'
             '\u270E Has Notes (<span id="note-count">0</span>)</button>')
    h.append("</div>")

    h.append('<div class="filter-group">')
    h.append('<span class="filter-label">Chapter:</span>')
    for ch in chapters:
        name = CHAPTER_NAMES.get(ch, f"Ch {ch}")
        h.append(f'<button class="filter-btn" onclick="filterChapter(\'{ch}\',this)">'
                 f"Ch {ch}: {name} ({by_chapter[ch]})</button>")
    h.append("</div>")

    h.append('<div class="filter-group">')
    h.append('<span class="filter-label">Classification:</span>')
    for cls_key in ["match", "not_applicable", "partial_match",
                    "confirmed_gap", "different_standard",
                    "policy_present_procedures_missing"]:
        count = by_class.get(cls_key, 0)
        if count == 0:
            continue
        tc, bg, label = CLASSIFICATION_STYLES[cls_key]
        h.append(f'<button class="filter-btn" onclick="filterClass(\'{cls_key}\',this)"'
                 f' style="border-color:{tc}">{label} ({count})</button>')
    h.append("</div>")

    h.append("</section>")

    # ── Toolbar ──
    h.append('<div class="toolbar">')
    h.append('<span id="row-count" class="row-count">'
             f"Showing all {total} sections</span>")
    h.append('<button class="toolbar-btn" onclick="expandAll()">Expand visible</button>')
    h.append('<button class="toolbar-btn" onclick="collapseAll()">Collapse all</button>')
    h.append(f'<button class="export-btn" onclick="exportCSV()">'
             f'Export CSV (<span id="export-count">{total}</span> rows)</button>')
    h.append("</div>")

    # ── Table ──
    h.append('<table id="report-table">')
    h.append("<thead><tr>")
    h.append('<th class="col-fav"></th>')
    h.append('<th class="col-note"></th>')
    h.append('<th class="col-ch">Ch</th>')
    h.append('<th class="col-sec">Section</th>')
    h.append('<th class="col-title">Title</th>')
    h.append('<th class="col-cls">Classification</th>')
    h.append('<th class="col-conf">Conf.</th>')
    h.append('<th class="col-finding">Finding</th>')
    h.append('<th class="col-expand"></th>')
    h.append("</tr></thead>")
    h.append("<tbody>")

    for i, row in enumerate(rows):
        ch = row["fns_chapter"]
        sec = row["fns_section"]
        title = row["fns_title"]
        cls = row["classification"]
        conf = row["confidence"]
        summary = row.get("fns_summary", "")
        l1 = row.get("layer1_note", "")
        l2 = row.get("layer2_note", "")
        l3 = row.get("layer3_note", "")
        action = row.get("action_needed", "")
        priority = row.get("priority", "")
        session_id = row.get("session_id", "")
        tokens_in = row.get("tokens_in", "")
        tokens_out = row.get("tokens_out", "")
        cost = row.get("est_cost", "")
        olg_matches = row.get("olg_matches", "")
        olg_urls = row.get("olg_urls", "")
        cmr_section = row.get("cmr_section", "")
        cfr_classification = row.get("cfr_classification", "")
        cfr_section = row.get("cfr_section", "")
        cfr_note = row.get("cfr_note", "")

        act = "true" if is_actionable(row) else "false"
        fnd = "true" if is_finding(row) else "false"
        key = row_key(row)
        style = CLASSIFICATION_STYLES.get(cls, ("#333", "#eee", cls))
        tc, bg, label = style

        # Determine what to show as the "finding" in the main row
        finding_text = l2 or l1 or ""

        # Export data for CSV download
        export_data = json.dumps({
            "ch": ch, "sec": sec, "title": title, "cls": cls, "conf": conf,
            "summary": summary, "l1": l1, "l2": l2, "l3": l3,
            "olg": olg_matches, "urls": olg_urls, "action": action,
            "priority": priority, "cmr": cmr_section,
            "cfr_cls": cfr_classification, "cfr_sec": cfr_section, "cfr_note": cfr_note,
            "sid": session_id,
            "tin": tokens_in, "tout": tokens_out, "cost": cost,
        }, ensure_ascii=False)

        # ── Main row ──
        h.append(f'<tr class="main-row" data-ch="{ch}" data-cls="{cls}" '
                 f'data-act="{act}" data-fnd="{fnd}" data-key="{esc(key)}" '
                 f'data-fav="false" data-note="false" '
                 f'data-exp="{esc(export_data)}" '
                 f'onclick="toggleRow({i})">')
        h.append(f'<td class="col-fav"><button class="fav-btn" data-key="{esc(key)}" '
                 f'onclick="toggleFav(this,event)" title="Favorite">\u2606</button></td>')
        h.append(f'<td class="col-note"><span class="note-indicator" '
                 f'data-key="{esc(key)}">\u270E</span></td>')
        h.append(f'<td class="col-ch">{esc(ch)}</td>')
        h.append(f'<td class="col-sec">{esc(sec)}</td>')
        h.append(f'<td class="col-title">{esc(title)}</td>')
        h.append(f'<td class="col-cls"><span class="badge" '
                 f'style="color:{tc};background:{bg}">{label}</span></td>')
        h.append(f'<td class="col-conf">{esc(conf)}</td>')
        h.append(f'<td class="col-finding">{esc(truncate(finding_text))}</td>')
        h.append(f'<td class="col-expand"><span class="expand-icon" '
                 f'id="icon-{i}">+</span></td>')
        h.append("</tr>")

        # ── Detail row ──
        h.append(f'<tr class="detail-row" id="detail-{i}" '
                 f'data-ch="{ch}" data-cls="{cls}" data-act="{act}" '
                 f'data-fnd="{fnd}" data-fav="false" data-note="false">')
        h.append(f'<td colspan="{NCOLS}">')
        h.append('<div class="detail-panel">')

        # Left: notes
        h.append('<div class="detail-notes">')

        if summary:
            h.append('<div class="detail-section">')
            h.append("<h4>FNS Requirement</h4>")
            h.append(f"<p>{esc(summary)}</p>")
            h.append("</div>")

        if l1:
            h.append('<div class="detail-section">')
            h.append("<h4>Layer 1 &mdash; Triage</h4>")
            h.append(f"<p>{esc(l1)}</p>")
            h.append("</div>")

        if l2:
            h.append('<div class="detail-section">')
            h.append("<h4>Layer 2 &mdash; Investigation</h4>")
            h.append(f"<p>{esc(l2)}</p>")
            h.append("</div>")

        if l3:
            h.append('<div class="detail-section">')
            h.append("<h4>Layer 3 &mdash; CMR Cross-Check</h4>")
            h.append(f"<p>{esc(l3)}</p>")
            h.append("</div>")

        if cfr_note or cfr_classification:
            h.append('<div class="detail-section">')
            h.append("<h4>Layer 3 &mdash; CFR Cross-Check</h4>")
            if cfr_classification:
                h.append(f'<p><strong>{esc(cfr_classification)}</strong>')
                if cfr_section:
                    h.append(f' &mdash; {esc(cfr_section)}')
                h.append('</p>')
            if cfr_note:
                h.append(f"<p>{esc(cfr_note)}</p>")
            h.append("</div>")

        # My Notes textarea
        h.append('<div class="detail-section note-section">')
        h.append('<h4>My Notes <span class="note-saved">Saved</span></h4>')
        h.append(f'<textarea class="note-area" data-key="{esc(key)}" '
                 f'oninput="onNoteInput(this)" '
                 f'placeholder="Add your notes here..."></textarea>')
        h.append("</div>")

        h.append("</div>")  # detail-notes

        # Right: metadata sidebar
        h.append('<div class="detail-meta">')
        h.append("<h4>Sources &amp; Metadata</h4>")

        # OLG pages
        h.append('<div class="meta-item">')
        h.append('<span class="meta-label">OLG Pages Found</span>')
        h.append(f'<div class="meta-value">{make_olg_links_html(olg_matches, olg_urls)}</div>')
        h.append("</div>")

        # Action + Priority (only for actionable items)
        if is_actionable(row):
            h.append('<div class="meta-item">')
            h.append('<span class="meta-label">Action Needed</span>')
            h.append(f'<div class="meta-value"><strong>{esc(action)}</strong></div>')
            h.append("</div>")

            if priority:
                pc = PRIORITY_COLORS.get(priority.upper(), "#6b7280")
                h.append('<div class="meta-item">')
                h.append('<span class="meta-label">Priority</span>')
                h.append(f'<div class="meta-value"><span class="priority-badge" '
                         f'style="color:{pc}"><strong>{esc(priority)}</strong></span></div>')
                h.append("</div>")

        # CMR section
        if cmr_section:
            h.append('<div class="meta-item">')
            h.append('<span class="meta-label">CMR Section</span>')
            h.append(f'<div class="meta-value">{esc(cmr_section)}</div>')
            h.append("</div>")

        # CFR section
        if cfr_section:
            h.append('<div class="meta-item">')
            h.append('<span class="meta-label">7 CFR Section</span>')
            h.append(f'<div class="meta-value">{esc(cfr_section)}</div>')
            h.append("</div>")

        # Session ID
        if session_id:
            h.append('<div class="meta-item">')
            h.append('<span class="meta-label">Session ID (click to copy CLI command)</span>')
            h.append(f'<div class="meta-value"><code class="session-id" '
                     f'onclick="copyToClipboard(this,event)" title="Click to copy: '
                     f'claude --resume {esc(session_id)}">'
                     f"{esc(session_id)}</code></div>")
            h.append("</div>")

        # Tokens / Cost
        if tokens_in or tokens_out or (cost and cost != "$0.0000"):
            parts = []
            if tokens_in:
                parts.append(f"In: {tokens_in}")
            if tokens_out:
                parts.append(f"Out: {tokens_out}")
            if cost and cost != "$0.0000":
                parts.append(f"Cost: {cost}")
            if parts:
                h.append('<div class="meta-item">')
                h.append('<span class="meta-label">Tokens / Cost</span>')
                h.append(f'<div class="meta-value">{" &middot; ".join(parts)}</div>')
                h.append("</div>")

        h.append("</div>")  # detail-meta
        h.append("</div>")  # detail-panel
        h.append("</td>")
        h.append("</tr>")

    h.append("</tbody>")
    h.append("</table>")

    # ── Footer / Methodology ──
    h.append("<footer>")
    h.append("<h3>Methodology</h3>")
    h.append("<p>This report was generated by the <strong>Regulatory Knowledgebase Comparator</strong> "
             "&mdash; a multi-layer analysis pipeline that systematically compares FNS Handbook "
             "310 (federal SNAP Quality Control standards) against the agency Online "
             "Guide (OLG).</p>")
    h.append("<ul>")
    h.append("<li><strong>Layer 0</strong>: Pre-classification of FNS sections "
             "(QC-only vs. policy-relevant)</li>")
    h.append("<li><strong>Layer 1</strong>: Automated triage using vector search to find "
             "OLG matches for each FNS requirement</li>")
    h.append("<li><strong>Layer 2</strong>: Agentic investigation using Claude Code CLI "
             "sessions &mdash; deep analysis with iterative OLG searches</li>")
    h.append("<li><strong>Layer 3</strong>: CMR cross-check for actionable findings to "
             "determine whether gaps are state-level policy decisions</li>")
    h.append("</ul>")

    h.append("<h4>Classifications</h4>")
    h.append("<ul>")
    for cls_key, (tc, bg, label) in CLASSIFICATION_STYLES.items():
        descs = {
            "match": "OLG adequately covers the FNS requirement",
            "not_applicable": "FNS section is QC-specific or does not apply to Massachusetts",
            "partial_match": "OLG covers some but not all aspects of the requirement",
            "confirmed_gap": "FNS requirement has no OLG coverage",
            "different_standard": "Massachusetts implements a different standard than FNS requires",
            "policy_present_procedures_missing": "Policy exists but procedural guidance is "
                                                 "absent from OLG",
        }
        h.append(f'<li><span class="badge" style="color:{tc};background:{bg};'
                 f'font-size:0.75rem">{label}</span> &mdash; {descs[cls_key]}</li>')
    h.append("</ul>")

    h.append("<h4>Reading This Report</h4>")
    h.append("<ul>")
    h.append("<li>Click any row to expand full details (FNS requirement text, "
             "all layer notes, OLG sources, metadata)</li>")
    h.append('<li>Rows with a <span style="color:#dc2626;font-weight:600">red left border'
             "</span> are L3-escalated findings (gap, different standard, or missing "
             "procedures)</li>")
    h.append('<li>Rows with an <span style="color:#f59e0b;font-weight:600">amber left border'
             "</span> are partial matches that may need OLG updates</li>")
    h.append("<li>Click \u2606 to favorite a row &mdash; favorites persist across "
             "sessions and can be filtered</li>")
    h.append("<li>Expand a row to add notes in the <strong>My Notes</strong> textarea "
             "&mdash; notes auto-save to your browser and a \u270E icon appears on "
             "annotated rows</li>")
    h.append("<li>Click <strong>Export CSV</strong> to download the currently visible "
             "(filtered) rows as a CSV file, including your notes</li>")
    h.append("<li>Click a Session ID to copy the full CLI command "
             "(<code>claude --resume &lt;ID&gt;</code>) to your clipboard</li>")
    h.append("<li>Use the filter buttons to focus on specific chapters, classifications, "
             "favorites, or rows with notes</li>")
    h.append("<li>Toggle dark mode with the button in the top-right corner</li>")
    h.append("</ul>")
    h.append("</footer>")

    # Toast
    h.append('<div class="toast" id="toast"></div>')

    # JavaScript
    h.append(f"<script>{JS}</script>")

    h.append("</body>")
    h.append("</html>")

    return "\n".join(h)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML report from FNS vs OLG comparator results")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output HTML file path")
    parser.add_argument("--open", action="store_true",
                        help="Open report in default browser after generation")
    args = parser.parse_args()

    rows = load_csvs(DATA_DIR)
    if not rows:
        print("No CSV files found in", DATA_DIR)
        return

    html = generate_html(rows)

    if args.output:
        out_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = DATA_DIR / f"report_{timestamp}.html"

    out_path.write_text(html, encoding="utf-8")

    # Stats
    by_class = Counter(r["classification"] for r in rows)
    findings = sum(1 for r in rows if is_finding(r))
    actionable = sum(1 for r in rows if is_actionable(r))
    chapters = sorted(set(r["fns_chapter"] for r in rows), key=int)
    print(f"Report generated: {out_path}")
    print(f"  {len(rows)} sections across {len(chapters)} chapters "
          f"(Ch {', '.join(chapters)})")
    print(f"  {findings} findings (L3-escalated), "
          f"{actionable} total needing attention")
    for cls_key in ["match", "partial_match", "not_applicable",
                    "confirmed_gap", "different_standard",
                    "policy_present_procedures_missing"]:
        count = by_class.get(cls_key, 0)
        if count:
            label = CLASSIFICATION_STYLES[cls_key][2]
            print(f"    {label}: {count}")

    if args.open:
        webbrowser.open(str(out_path.resolve()))


if __name__ == "__main__":
    main()
