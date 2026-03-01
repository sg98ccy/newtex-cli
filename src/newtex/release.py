from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


ROOT_MARKER = "pyproject.toml"


def _run(command: list[str]) -> None:
    print(f"$ {shlex.join(command)}")
    subprocess.run(command, check=True)


def _confirm_upload() -> bool:
    response = input("[7/7] Upload dist/* to PyPI now? [y/N] ").strip().lower()
    return response in {"y", "yes"}


def _dist_artifacts() -> list[str]:
    return [str(path) for path in sorted(Path("dist").glob("*")) if path.is_file()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local build + publish flow for newtex-cli")
    parser.add_argument("--no-upload", action="store_true", help="Run all checks/build steps but skip twine upload")
    args = parser.parse_args()

    if not Path(ROOT_MARKER).exists():
        raise SystemExit("Error: run build-local from the repository root")

    print("[1/7] Cleaning previous artifacts")
    _run(["rm", "-rf", "dist", "build", ".pytest_cache"])
    for egg_info in Path(".").glob("**/*.egg-info"):
        if egg_info.is_dir():
            _run(["rm", "-rf", str(egg_info)])

    print("[2/7] Installing publish tooling")
    _run([sys.executable, "-m", "pip", "install", "-e", ".[publish]"])

    print("[3/7] Running tests")
    _run([sys.executable, "-m", "pytest", "-q"])

    print("[4/7] Running publish checks")
    _run(["newtex", "--publish-check"])

    print("[5/7] Building distributions")
    _run([sys.executable, "-m", "build"])

    print("[6/7] Checking built artifacts")
    artifacts = _dist_artifacts()
    if not artifacts:
        raise SystemExit("Error: no artifacts found in dist/")
    _run([sys.executable, "-m", "twine", "check", *artifacts])

    if args.no_upload:
        print("[7/7] Upload skipped (--no-upload)")
        print("Done. Artifacts are ready in dist/")
        return

    if not os.getenv("TWINE_USERNAME") or not os.getenv("TWINE_PASSWORD"):
        print("Warning: TWINE_USERNAME and/or TWINE_PASSWORD is not set.")
        print("Expected token auth: TWINE_USERNAME=__token__ and TWINE_PASSWORD=<pypi-token>")

    if _confirm_upload():
        _run([sys.executable, "-m", "twine", "upload", *artifacts])
        print("Upload complete.")
    else:
        print("Upload skipped by user.")


if __name__ == "__main__":
    main()
