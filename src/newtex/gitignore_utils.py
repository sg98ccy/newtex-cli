from pathlib import Path
import importlib.resources as pkg_resources


def _read_base_gitignore() -> str:
    from newtex import resources

    return pkg_resources.files(resources).joinpath("gitignore/tex-base.gitignore").read_text(encoding="utf-8")


def apply_gitignore(project_dir: Path, track_pdf: bool, share_vscode: bool) -> None:
    gitignore_path = project_dir / ".gitignore"

    base_content = _read_base_gitignore().strip() + "\n"

    extras = []
    if not track_pdf:
        extras.append("*.pdf")
    if not share_vscode:
        extras.append(".vscode/")

    extra_content = ""
    if extras:
        extra_content = "\n# newtex preferences\n" + "\n".join(extras) + "\n"

    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        merged = existing.rstrip() + "\n\n# --- newtex additions ---\n" + base_content + extra_content
        gitignore_path.write_text(merged, encoding="utf-8")
    else:
        gitignore_path.write_text(base_content + extra_content, encoding="utf-8")
