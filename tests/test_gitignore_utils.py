from pathlib import Path

import newtex.gitignore_utils as gitignore_utils


def test_apply_gitignore_new_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(gitignore_utils, "_read_base_gitignore", lambda: "*.aux\n*.log\n")

    gitignore_utils.apply_gitignore(tmp_path, track_pdf=False, share_vscode=False)

    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "*.aux" in content
    assert "*.pdf" in content
    assert ".vscode/" in content


def test_apply_gitignore_merges_existing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(gitignore_utils, "_read_base_gitignore", lambda: "*.aux\n")

    path = tmp_path / ".gitignore"
    path.write_text("node_modules/\n", encoding="utf-8")

    gitignore_utils.apply_gitignore(tmp_path, track_pdf=True, share_vscode=True)

    content = path.read_text(encoding="utf-8")
    assert "node_modules/" in content
    assert "# --- newtex additions ---" in content
    assert "*.aux" in content
