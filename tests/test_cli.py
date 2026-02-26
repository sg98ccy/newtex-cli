from pathlib import Path

from typer.testing import CliRunner

import newtex.cli as cli_module


runner = CliRunner()


def test_cli_noninteractive_success(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm",
            "templates": {"acm": {"path": "/template", "description": "desc"}},
        },
    )
    monkeypatch.setattr(cli_module.Path, "exists", lambda self: True)

    captured = {}

    def _fake_scaffold(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(cli_module, "scaffold_project", _fake_scaffold)

    result = runner.invoke(cli_module.app, ["test-paper", "acm", "--no-git"])

    assert result.exit_code == 0
    assert captured["project_name"] == "test-paper"
    assert captured["init_git"] is False


def test_cli_rejects_invalid_project_name(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm",
            "templates": {"acm": {"path": "/template", "description": "desc"}},
        },
    )

    result = runner.invoke(cli_module.app, ["Bad_Name", "acm"])

    assert result.exit_code != 0
    assert "kebab-case" in result.output


def test_cli_interactive_uses_suggestion(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm",
            "templates": {"acm": {"path": "/template", "description": "desc"}},
        },
    )
    monkeypatch.setattr(cli_module.Path, "exists", lambda self: True)

    class _Prompt:
        def __init__(self, value):
            self._value = value

        def ask(self):
            return self._value

    monkeypatch.setattr(cli_module.questionary, "text", lambda *args, **kwargs: _Prompt("My Project"))
    monkeypatch.setattr(cli_module.questionary, "confirm", lambda *args, **kwargs: _Prompt(True))
    monkeypatch.setattr(cli_module.questionary, "select", lambda *args, **kwargs: _Prompt("acm"))

    captured = {}

    def _fake_scaffold(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(cli_module, "scaffold_project", _fake_scaffold)

    result = runner.invoke(cli_module.app, [])

    assert result.exit_code == 0
    assert captured["project_name"] == "my-project"
    assert captured["template_path"] == "/template"


def test_cli_tests_option_runs_and_exits_success(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_tests", lambda: 0)
    monkeypatch.setattr(cli_module, "load_config", lambda: (_ for _ in ()).throw(AssertionError("load_config should not run")))

    result = runner.invoke(cli_module.app, ["--tests"])

    assert result.exit_code == 0
    assert "All tests passed" in result.output


def test_cli_tests_option_propagates_failure_code(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_tests", lambda: 2)

    result = runner.invoke(cli_module.app, ["--tests"])

    assert result.exit_code == 2
    assert "Test run failed" in result.output


def test_cli_template_set_updates_config(monkeypatch) -> None:
    captured = {}

    def _fake_upsert(alias: str, template_path: str, description: str | None = None):
        captured["alias"] = alias
        captured["path"] = template_path
        captured["description"] = description

    monkeypatch.setattr(cli_module, "upsert_template", _fake_upsert)

    result = runner.invoke(
        cli_module.app,
        ["--template-set", "acm=/tmp/template", "--template-description", "ACM Template"],
    )

    assert result.exit_code == 0
    assert captured["alias"] == "acm"
    assert captured["path"] == "/tmp/template"
    assert captured["description"] == "ACM Template"


def test_cli_set_default_template_handles_unknown(monkeypatch) -> None:
    def _raise(alias: str):
        raise KeyError(f"Unknown template alias: {alias}")

    monkeypatch.setattr(cli_module, "set_default_template", _raise)

    result = runner.invoke(cli_module.app, ["--set-default-template", "missing"])

    assert result.exit_code == 1
    assert "Unknown template alias" in result.output


def test_cli_templates_list_outputs_aliases(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm",
            "templates": {
                "acm": {"path": "/tmp/acm", "description": "ACM"},
                "ieee": {"path": "https://example.com/template.git", "description": "IEEE"},
            },
        },
    )

    result = runner.invoke(cli_module.app, ["--templates-list"])

    assert result.exit_code == 0
    assert "acm (default) -> /tmp/acm" in result.output
    assert "ieee -> https://example.com/template.git" in result.output


def test_cli_publish_check_success(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_publish_check", lambda: 0)

    result = runner.invoke(cli_module.app, ["--publish-check"])

    assert result.exit_code == 0
    assert "Running publish readiness checks" in result.output


def test_cli_publish_check_failure_code(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_publish_check", lambda: 1)

    result = runner.invoke(cli_module.app, ["--publish-check"])

    assert result.exit_code == 1
