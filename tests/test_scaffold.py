from pathlib import Path

import pytest

import newtex.scaffold as scaffold_module


def test_scaffold_project_copies_local_template(monkeypatch, tmp_path: Path) -> None:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "main.tex").write_text("hello", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    calls = {"apply_gitignore": False}

    def _fake_apply_gitignore(project_dir: Path, track_pdf: bool, share_vscode: bool) -> None:
        calls["apply_gitignore"] = True
        assert project_dir == tmp_path / "paper"
        assert track_pdf is False
        assert share_vscode is True

    monkeypatch.setattr(scaffold_module, "apply_gitignore", _fake_apply_gitignore)
    monkeypatch.setattr(scaffold_module, "run_cmd", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("run_cmd should not be called")))

    scaffold_module.scaffold_project(
        template_path=str(template_dir),
        project_name="paper",
        init_git=False,
        open_code=False,
    )

    assert (tmp_path / "paper" / "main.tex").read_text(encoding="utf-8") == "hello"
    assert calls["apply_gitignore"] is True


def test_scaffold_project_copies_packaged_template(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    calls = {"copied": False}

    def _fake_copy_packaged_template(template_key: str, project_dir: Path) -> None:
        calls["copied"] = True
        assert template_key == "acm"
        project_dir.mkdir(parents=True, exist_ok=False)
        (project_dir / "README.md").write_text("packaged", encoding="utf-8")

    monkeypatch.setattr(scaffold_module, "_copy_packaged_template", _fake_copy_packaged_template)
    monkeypatch.setattr(scaffold_module, "apply_gitignore", lambda *args, **kwargs: None)
    monkeypatch.setattr(scaffold_module, "run_cmd", lambda *args, **kwargs: None)

    scaffold_module.scaffold_project(
        template_path="package://acm",
        project_name="paper",
        init_git=False,
        open_code=False,
    )

    assert calls["copied"] is True
    assert (tmp_path / "paper" / "README.md").read_text(encoding="utf-8") == "packaged"


def test_scaffold_project_rejects_missing_local_template(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        scaffold_module.scaffold_project(
            template_path="missing-template-folder",
            project_name="paper",
            init_git=False,
            open_code=False,
        )
