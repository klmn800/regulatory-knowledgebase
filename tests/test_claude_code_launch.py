"""Tests for the project-Python PATH line in Claude Code launchers.

Draft sessions run `python rag/query.py`. Where the dependencies live only in
`.venv`, the launcher must put the venv first on PATH. No terminal opens here:
subprocess.Popen is replaced."""

import os
import subprocess

import pytest

import apps.author.author as author_mod
import apps.qc.judge_claude_code as judge_mod
import apps.qc.ppt_generator as ppt_mod
import tools.claude_code_runner as runner
from tools.claude_code_runner import bat_python_path_line, project_python_dir


def _fake_venv(root, sub="Scripts", exe="python.exe"):
    folder = root / ".venv" / sub
    folder.mkdir(parents=True)
    (folder / exe).write_bytes(b"")
    return folder


def test_windows_venv_found(tmp_path):
    folder = _fake_venv(tmp_path)
    assert project_python_dir(tmp_path) == folder
    assert bat_python_path_line(tmp_path) == f'set "PATH={folder};%PATH%"\n'


def test_posix_venv_found(tmp_path):
    folder = _fake_venv(tmp_path, sub="bin", exe="python")
    assert project_python_dir(tmp_path) == folder


def test_no_venv_leaves_path_alone(tmp_path):
    assert project_python_dir(tmp_path) is None
    assert bat_python_path_line(tmp_path) == ""


def test_empty_scripts_folder_is_not_a_venv(tmp_path):
    (tmp_path / ".venv" / "Scripts").mkdir(parents=True)
    assert project_python_dir(tmp_path) is None


@pytest.fixture
def launcher_env(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    data = root / "output" / "author"
    data.mkdir(parents=True)
    monkeypatch.setattr(author_mod, "PROJECT_ROOT", root)
    monkeypatch.setattr(author_mod, "DATA_DIR", data)
    launched = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: launched.append(a))
    return root, data, launched


def _bat_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def test_draft_launcher_puts_venv_first_before_claude(launcher_env):
    root, data, launched = launcher_env
    folder = _fake_venv(root)
    draft_dir = data / "demo" / "drafts" / "001"
    draft_dir.mkdir(parents=True)

    author_mod.launch_draft("full prompt", draft_dir, "instructions", None,
                            "demo", "00000000-0000-0000-0000-000000000000", [])

    lines = _bat_lines(data / ".run_draft.bat")
    path_line = f'set "PATH={folder};%PATH%"'
    assert path_line in lines
    claude_line = next(i for i, l in enumerate(lines) if l.startswith("claude "))
    assert lines.index(path_line) < claude_line
    assert launched, "launcher should have been started"


def test_resume_launcher_puts_venv_first(launcher_env):
    root, data, _ = launcher_env
    folder = _fake_venv(root)

    author_mod.launch_resume("00000000-0000-0000-0000-000000000000", "demo")

    assert f'set "PATH={folder};%PATH%"' in _bat_lines(data / ".run_resume.bat")


def test_runner_env_puts_venv_first(tmp_path, monkeypatch):
    folder = _fake_venv(tmp_path)
    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("PATH", "C:\\elsewhere")

    env = runner._merged_env(None)
    assert env["PATH"] == f"{folder}{os.pathsep}C:\\elsewhere"

    env = runner._merged_env({"CLAUDE_X": "1"})
    assert env["CLAUDE_X"] == "1"
    assert env["PATH"].startswith(str(folder) + os.pathsep)


def test_runner_env_without_venv_inherits(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)
    assert runner._merged_env(None) is None
    assert runner._merged_env({"CLAUDE_X": "1"})["CLAUDE_X"] == "1"


def test_qc_judge_resume_launcher_puts_venv_first(tmp_path, monkeypatch):
    folder = _fake_venv(tmp_path)
    monkeypatch.setattr(judge_mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)

    judge_mod.launch_judge_resume("00000000-0000-0000-0000-000000000000", "5.1")

    bat = tmp_path / "output" / "qc_analysis" / ".run_judge_resume.bat"
    assert f'set "PATH={folder};%PATH%"' in _bat_lines(bat)


def test_qc_ppt_launcher_puts_venv_first(tmp_path, monkeypatch):
    folder = _fake_venv(tmp_path)
    monkeypatch.setattr(ppt_mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    ppt_mod._launch_windowed(run_dir, "00000000-0000-0000-0000-000000000000",
                             "kickoff", "demo", "new")

    lines = _bat_lines(run_dir / ".run_new.bat")
    path_line = f'set "PATH={folder};%PATH%"'
    claude_line = next(i for i, l in enumerate(lines) if l.startswith("claude "))
    assert lines.index(path_line) < claude_line


def test_draft_launcher_without_venv_has_no_path_line(launcher_env):
    root, data, _ = launcher_env
    draft_dir = data / "demo" / "drafts" / "001"
    draft_dir.mkdir(parents=True)

    author_mod.launch_draft("full prompt", draft_dir, "instructions", None,
                            "demo", "00000000-0000-0000-0000-000000000000", [])

    assert not any(l.startswith("set \"PATH=") for l in _bat_lines(data / ".run_draft.bat"))
