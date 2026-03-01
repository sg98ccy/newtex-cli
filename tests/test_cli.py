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
            "default_template": "acm-conf",
            "templates": {"acm-conf": {"path": "/template", "description": "desc"}},
        },
    )
    monkeypatch.setattr(cli_module.Path, "exists", lambda self: True)

    captured = {}

    def _fake_scaffold(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(cli_module, "scaffold_project", _fake_scaffold)

    result = runner.invoke(cli_module.app, ["test-paper", "acm-conf", "--no-git"])

    assert result.exit_code == 0
    assert captured["project_name"] == "test-paper"
    assert captured["init_git"] is False


def test_cli_rejects_invalid_project_name(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm-conf",
            "templates": {"acm-conf": {"path": "/template", "description": "desc"}},
        },
    )

    result = runner.invoke(cli_module.app, ["Bad_Name", "acm-conf"])

    assert result.exit_code != 0
    assert "kebab-case" in result.output


def test_cli_interactive_uses_suggestion(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm-conf",
            "templates": {"acm-conf": {"path": "/template", "description": "desc"}},
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
    monkeypatch.setattr(cli_module.questionary, "select", lambda *args, **kwargs: _Prompt("acm-conf"))

    captured = {}

    def _fake_scaffold(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(cli_module, "scaffold_project", _fake_scaffold)

    result = runner.invoke(cli_module.app, [])

    assert result.exit_code == 0
    assert captured["project_name"] == "my-project"
    assert captured["template_path"] == "/template"


def test_cli_interactive_cancelled_before_scaffold(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm-conf",
            "templates": {"acm-conf": {"path": "/template", "description": "desc"}},
        },
    )
    monkeypatch.setattr(cli_module.Path, "exists", lambda self: True)

    class _Prompt:
        def __init__(self, value):
            self._value = value

        def ask(self):
            return self._value

    monkeypatch.setattr(cli_module.questionary, "text", lambda *args, **kwargs: _Prompt("my-project"))
    monkeypatch.setattr(cli_module.questionary, "select", lambda *args, **kwargs: _Prompt("acm-conf"))

    confirm_answers = iter([False])
    monkeypatch.setattr(
        cli_module.questionary,
        "confirm",
        lambda *args, **kwargs: _Prompt(next(confirm_answers)),
    )

    monkeypatch.setattr(
        cli_module,
        "scaffold_project",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("scaffold_project should not be called")),
    )

    result = runner.invoke(cli_module.app, [])

    assert result.exit_code == 1
    assert "Cancelled" in result.output


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
        ["--template-set", "acm-conf=/tmp/template", "--template-description", "ACM Template"],
    )

    assert result.exit_code == 0
    assert captured["alias"] == "acm-conf"
    assert captured["path"] == "/tmp/template"
    assert captured["description"] == "ACM Template"


def test_cli_default_template_set_handles_unknown(monkeypatch) -> None:
    def _raise(alias: str):
        raise KeyError(f"Unknown template alias: {alias}")

    monkeypatch.setattr(cli_module, "set_default_template", _raise)

    result = runner.invoke(cli_module.app, ["--default-template-set", "missing"])

    assert result.exit_code == 1
    assert "Unknown template alias" in result.output


def test_cli_set_default_template_alias_works(monkeypatch) -> None:
    captured = {}

    def _set_default(alias: str):
        captured["alias"] = alias

    monkeypatch.setattr(cli_module, "set_default_template", _set_default)

    result = runner.invoke(cli_module.app, ["--set-default-template", "acm-conf"])

    assert result.exit_code == 0
    assert captured["alias"] == "acm-conf"


def test_cli_default_template_flags_conflict() -> None:
    result = runner.invoke(
        cli_module.app,
        ["--default-template-set", "acm-conf", "--set-default-template", "ntu-report-template"],
    )

    assert result.exit_code != 0
    assert "Use only one of" in result.output


def test_cli_templates_list_outputs_aliases(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: {
            "default_template": "acm-conf",
            "templates": {
                "acm-conf": {"path": "/tmp/acm-conf", "description": "ACM"},
                "ieee": {"path": "https://example.com/template.git", "description": "IEEE"},
            },
        },
    )

    result = runner.invoke(cli_module.app, ["--templates-list"])

    assert result.exit_code == 0
    assert "acm-conf (default) -> /tmp/acm-conf" in result.output
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


def test_cli_version_flag(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_get_current_version", lambda: "0.1.4")

    result = runner.invoke(cli_module.app, ["--version"])

    assert result.exit_code == 0
    assert "Current version:" in result.output
    assert "0.1.4" in result.output


def test_cli_update_flag_success(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_self_update", lambda: 0)
    monkeypatch.setattr(cli_module, "_get_current_version", lambda: "0.1.5")

    result = runner.invoke(cli_module.app, ["--update"])

    assert result.exit_code == 0
    assert "Update completed" in result.output
    assert "0.1.5" in result.output


def test_cli_update_flag_failure(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_self_update", lambda: 2)

    result = runner.invoke(cli_module.app, ["--update"])

    assert result.exit_code == 2
    assert "Update failed" in result.output


def test_cli_upgrade_flag_alias_success(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_run_self_update", lambda: 0)
    monkeypatch.setattr(cli_module, "_get_current_version", lambda: "0.1.6")

    result = runner.invoke(cli_module.app, ["--upgrade"])

    assert result.exit_code == 0
    assert "Update completed" in result.output
    assert "0.1.6" in result.output


def test_cli_version_flag_rejects_positional_args() -> None:
    result = runner.invoke(cli_module.app, ["paper", "acm-conf", "--version"])

    assert result.exit_code != 0
    assert "Do not pass PROJECT_NAME or TEMPLATE with --version" in result.output


def test_cli_update_flag_rejects_positional_args() -> None:
    result = runner.invoke(cli_module.app, ["paper", "acm-conf", "--update"])

    assert result.exit_code != 0
    assert "Do not pass PROJECT_NAME or TEMPLATE with --update" in result.output
