from pathlib import Path
from importlib import resources
import shutil
import subprocess

from .gitignore_utils import apply_gitignore


PACKAGE_TEMPLATE_PREFIX = "package://"
REMOTE_TEMPLATE_PREFIXES = ("http://", "https://", "ssh://", "git@", "gh:", "gl:")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def _copy_packaged_template(template_key: str, project_dir: Path) -> None:
    if not template_key:
        raise ValueError("Package template key cannot be empty")

    traversable = resources.files("newtex.resources").joinpath("templates", template_key)
    if not traversable.exists() or not traversable.is_dir():
        raise FileNotFoundError(f"Packaged template not found: {template_key}")

    with resources.as_file(traversable) as resolved_path:
        shutil.copytree(resolved_path, project_dir)


def _resolve_template_source(template_path: str) -> tuple[str, str | Path]:
    if template_path.startswith(PACKAGE_TEMPLATE_PREFIX):
        template_key = template_path[len(PACKAGE_TEMPLATE_PREFIX) :].strip()
        return "package", template_key

    local_template = Path(template_path).expanduser()
    if local_template.is_dir():
        return "local", local_template

    if local_template.exists() and not local_template.is_dir():
        raise NotADirectoryError(f"Template path is not a directory: {local_template}")

    if template_path.startswith(REMOTE_TEMPLATE_PREFIXES):
        return "copier", template_path

    raise FileNotFoundError(
        f"Template folder not found: {local_template}. Use an existing local folder, a remote template URL, or package://<name>."
    )


def scaffold_project(
    template_path: str,
    project_name: str,
    init_git: bool = True,
    track_pdf: bool = False,
    share_vscode: bool = True,
    open_code: bool = False,
) -> None:
    project_dir = Path.cwd() / project_name

    if project_dir.exists():
        raise FileExistsError(f"Target folder already exists: {project_dir}")

    source_mode, source_value = _resolve_template_source(template_path)

    if source_mode == "local":
        shutil.copytree(source_value, project_dir)
    elif source_mode == "package":
        _copy_packaged_template(source_value, project_dir)
    else:
        run_cmd(["copier", "copy", source_value, project_name])

    apply_gitignore(project_dir, track_pdf=track_pdf, share_vscode=share_vscode)

    if init_git:
        run_cmd(["git", "init"], cwd=project_dir)

    if open_code:
        try:
            run_cmd(["code", "."], cwd=project_dir)
        except (FileNotFoundError, RuntimeError):
            pass
