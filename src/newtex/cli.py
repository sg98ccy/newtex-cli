import os
import shutil
import subprocess
import sys
from pathlib import Path

import questionary
import typer
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import load_config, set_default_template, upsert_template
from .scaffold import scaffold_project
from .validators import is_kebab_case, suggest_kebab_case

app = typer.Typer(help="Create local LaTeX projects from templates.")
console = Console()
PROMPT_STYLE = Style(
    [
        ("qmark", "fg:#8b5cf6 bold"),
        ("question", "bold"),
        ("answer", "fg:#22c55e bold"),
        ("pointer", "fg:#06b6d4 bold"),
        ("highlighted", "fg:#06b6d4 bold"),
        ("selected", "fg:#22c55e"),
    ]
)


def _show_banner() -> None:
    title = Text("newtex", style="bold magenta")
    subtitle = Text("Create local LaTeX projects from templates", style="cyan")
    console.print(Panel.fit(Text.assemble(title, "\n", subtitle), border_style="magenta"))


def _info(message: str) -> None:
    console.print(f"[cyan]•[/cyan] {message}")


def _success(message: str) -> None:
    console.print(f"[green]✔[/green] {message}")


def _error(message: str) -> None:
    console.print(f"[bold red]✖ {message}[/bold red]")


def _run_tests() -> int:
    local_venv_python = Path(".venv/bin/python")
    command = [str(local_venv_python), "-m", "pytest", "-q"] if local_venv_python.exists() else ["pytest", "-q"]

    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], check=False)

    return result.returncode


def _run_publish_check() -> int:
    checks_ok = True

    python_candidates = []
    local_venv_python = Path(".venv/bin/python")
    if local_venv_python.exists():
        python_candidates.append(str(local_venv_python))
    python_candidates.append(sys.executable)

    if shutil.which("pipx"):
        _success("pipx is available")
    else:
        _error("pipx is not available (recommended for global install)")
        checks_ok = False

    build_available = False
    for python_exec in python_candidates:
        try:
            build_check = subprocess.run([python_exec, "-m", "build", "--version"], check=False)
            if build_check.returncode == 0:
                build_available = True
                break
        except Exception:
            continue

    if build_available:
        _success("python -m build is available")
    else:
        _error("python -m build is not available (install with: python -m pip install -e '.[publish]')")
        checks_ok = False

    twine_available = False
    for python_exec in python_candidates:
        try:
            twine_check = subprocess.run([python_exec, "-m", "twine", "--version"], check=False)
            if twine_check.returncode == 0:
                twine_available = True
                break
        except Exception:
            continue

    if twine_available:
        _success("twine is available")
    else:
        _error("twine is not available (install with: python -m pip install -e '.[publish]')")
        checks_ok = False

    token_present = bool(os.getenv("TWINE_PASSWORD"))
    username = os.getenv("TWINE_USERNAME", "")
    trusted_publishing = bool(os.getenv("PYPI_API_TOKEN"))

    if token_present and username == "__token__":
        _success("Twine token credentials detected (TWINE_USERNAME/TWINE_PASSWORD)")
    elif trusted_publishing:
        _info("PYPI_API_TOKEN found (if your flow uses this env var)")
    else:
        _info("No publish token detected. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<pypi-token> before upload")

    if checks_ok:
        _success("Publish check passed")
        return 0

    _error("Publish check failed")
    return 1


def _parse_template_set(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise typer.BadParameter("--template-set must be in the form <alias>=<path-or-url>")

    alias, template_value = value.split("=", 1)
    alias = alias.strip()
    template_value = template_value.strip()

    if not alias:
        raise typer.BadParameter("Template alias cannot be empty")
    if not template_value:
        raise typer.BadParameter("Template path/url cannot be empty")

    return alias, template_value


def _pick_template(cfg: dict, template_arg: str | None) -> str:
    templates = cfg["templates"]
    if not templates:
        raise typer.BadParameter("No templates are configured")

    if template_arg:
        if template_arg not in templates:
            raise typer.BadParameter(f"Unknown template '{template_arg}'. Available: {', '.join(templates.keys())}")
        return template_arg

    choices = [
        questionary.Choice(title=f"{alias} ({meta.get('description', '')})", value=alias)
        for alias, meta in templates.items()
    ]

    default_alias = cfg.get("default_template")
    if default_alias not in templates:
        default_alias = next(iter(templates), None)

    selected = questionary.select(
        "Which template should I use?",
        choices=choices,
        default=default_alias,
        style=PROMPT_STYLE,
    ).ask()

    if not selected:
        raise typer.Exit(code=1)

    return selected


def _get_project_name(name_arg: str | None) -> str:
    if name_arg:
        if not is_kebab_case(name_arg):
            raise typer.BadParameter("Project name must be lowercase kebab-case (e.g. exlang-paper)")
        return name_arg

    while True:
        raw = questionary.text("What is your project name?", style=PROMPT_STYLE).ask()
        if not raw:
            raise typer.Exit(code=1)

        if is_kebab_case(raw):
            return raw

        suggested = suggest_kebab_case(raw)
        use_suggested = questionary.confirm(f'Use "{suggested}" instead?', style=PROMPT_STYLE).ask()

        if use_suggested:
            return suggested


@app.command()
def main(
    project_name: str | None = typer.Argument(None, help="Project folder name (kebab-case)"),
    template: str | None = typer.Argument(None, help="Template alias, e.g. acm-conf"),
    tests: bool = typer.Option(False, "--tests", help="Run full test suite and exit"),
    publish_check: bool = typer.Option(False, "--publish-check", help="Validate publishing prerequisites and exit"),
    templates_list: bool = typer.Option(False, "--templates-list", help="List configured templates and exit"),
    template_set: str | None = typer.Option(None, "--template-set", help="Set template alias/path using alias=path-or-url"),
    default_template_set: str | None = typer.Option(None, "--default-template-set", help="Set default template alias and exit"),
    set_default: str | None = typer.Option(None, "--set-default-template", help="Deprecated alias for --default-template-set"),
    template_desc: str | None = typer.Option(None, "--template-description", help="Description used with --template-set"),
    no_git: bool = typer.Option(False, "--no-git", help="Do not run git init"),
    track_pdf: bool = typer.Option(False, "--track-pdf", help="Track compiled PDFs in git"),
    no_vscode: bool = typer.Option(False, "--no-vscode", help="Do not keep shared .vscode settings"),
    open_code: bool = typer.Option(False, "--open", help="Open in VS Code after creation"),
) -> None:
    _show_banner()

    if tests:
        if project_name or template:
            raise typer.BadParameter("Do not pass PROJECT_NAME or TEMPLATE with --tests")

        _info("Running full test suite")
        test_exit_code = _run_tests()
        if test_exit_code == 0:
            _success("All tests passed")
            return

        _error("Test run failed")
        raise typer.Exit(code=test_exit_code)

    if publish_check:
        if project_name or template:
            raise typer.BadParameter("Do not pass PROJECT_NAME or TEMPLATE with --publish-check")

        _info("Running publish readiness checks")
        publish_exit_code = _run_publish_check()
        if publish_exit_code != 0:
            raise typer.Exit(code=publish_exit_code)
        return

    if template_set:
        if project_name or template:
            raise typer.BadParameter("Do not pass PROJECT_NAME or TEMPLATE with --template-set")

        alias, template_value = _parse_template_set(template_set)
        upsert_template(alias=alias, template_path=template_value, description=template_desc)
        _success(f"Saved template alias '{alias}'")
        return

    if default_template_set and set_default and default_template_set != set_default:
        raise typer.BadParameter("Use only one of --default-template-set or --set-default-template")

    requested_default_template = default_template_set or set_default

    if requested_default_template:
        if project_name or template:
            raise typer.BadParameter("Do not pass PROJECT_NAME or TEMPLATE with --default-template-set")

        try:
            set_default_template(requested_default_template)
        except KeyError as error:
            _error(str(error))
            raise typer.Exit(code=1)

        _success(f"Default template set to '{requested_default_template}'")
        return

    if templates_list:
        if project_name or template:
            raise typer.BadParameter("Do not pass PROJECT_NAME or TEMPLATE with --templates-list")

        cfg = load_config()
        templates = cfg.get("templates", {})
        default_alias = cfg.get("default_template")

        if not templates:
            _info("No templates configured")
            return

        _info("Configured templates")
        for alias, meta in templates.items():
            marker = " (default)" if alias == default_alias else ""
            path_value = meta.get("path", "")
            description = meta.get("description", "")
            _info(f"{alias}{marker} -> {path_value} ({description})")
        return

    cfg = load_config()

    name = _get_project_name(project_name)
    template_alias = _pick_template(cfg, template)
    template_path = cfg["templates"][template_alias]["path"]
    _info(f"Template: [bold]{template_alias}[/bold]")
    _info(f"Target project: [bold]{name}[/bold]")

    try:
        with console.status("[bold cyan]Scaffolding project...[/bold cyan]"):
            scaffold_project(
                template_path=template_path,
                project_name=name,
                init_git=not no_git,
                track_pdf=track_pdf,
                share_vscode=not no_vscode,
                open_code=open_code,
            )
    except Exception as error:
        _error(f"Error: {error}")
        raise typer.Exit(code=1)

    _success(f"Done. Created ./{name} using template '{template_alias}'")


if __name__ == "__main__":
    app()
