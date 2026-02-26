from pathlib import Path
import subprocess

from .gitignore_utils import apply_gitignore


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


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

    run_cmd(["copier", "copy", template_path, project_name])

    apply_gitignore(project_dir, track_pdf=track_pdf, share_vscode=share_vscode)

    if init_git:
        run_cmd(["git", "init"], cwd=project_dir)

    if open_code:
        try:
            run_cmd(["code", "."], cwd=project_dir)
        except (FileNotFoundError, RuntimeError):
            pass
