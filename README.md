<h1 align="center">newtex-cli</h1>

<p align="center">Scaffold local LaTeX projects from reusable templates.</p>

## 1. Installation

```bash
pipx install newtex-cli
```

Common `pip` install alternative:

```bash
python -m pip install newtex-cli
```

Works on macOS, Linux, and Windows (with Python/pipx).

## 2. Configuration

Bundled templates are discovered dynamically from `src/newtex/resources/templates`.
By default, `acm-conf` and `ntu-report-template` are included and resolve to `package://<template-name>`.

### 2.2 Global template config (recommended)

Configure templates once and use `newtex` from anywhere:

```bash
newtex --template-set acm-conf=/absolute/path/or/url/to/template
newtex --default-template-set acm-conf
newtex --templates-list
```

This writes to `~/.config/newtex/templates.yml`.

## 3. CLI Commands

### 3.0 Terminal UX

- `newtex` interactive mode now uses an adaptive Rich landing design with a retro ASCII-style banner.
- The layout auto-adjusts to terminal width (wide vs compact rendering).
- Utility workflows (`--version`, `--tests`, `--publish-check`, template management flags) keep concise output with light visual polish.

### 3.1 Command reference

| Command | Description |
| --- | --- |
| `newtex --help` | Show CLI help |
| `newtex --version` | Show current installed version |
| `newtex --update` | Update to the latest published version |
| `newtex --upgrade` | Alias of `--update` |
| `newtex --tests` | Run the full test suite |
| `newtex --publish-check` | Validate build/upload prerequisites |
| `newtex --template-set <alias>=<path-or-url>` | Add or update a global template alias |
| `newtex --template-set <alias>=<path-or-url> --template-description "..."` | Add alias with description |
| `newtex --default-template-set <alias>` | Set the global default template alias |
| `newtex --set-default-template <alias>` | Backward-compatible alias for `--default-template-set` |
| `newtex --templates-list` | Show configured global templates |
| `newtex` | Start interactive project creation |
| `newtex <project-name> <template>` | Create a project in non-interactive mode |
| `newtex <project-name> <template> --no-git` | Skip `git init` |
| `newtex <project-name> <template> --track-pdf` | Keep compiled PDFs tracked |
| `newtex <project-name> <template> --no-vscode` | Exclude shared `.vscode/` settings |
| `newtex <project-name> <template> --open` | Open generated project in VS Code |

### 3.2 Quick examples

```bash
newtex --help
newtex --version
newtex --update
newtex --upgrade
newtex
newtex exlang-paper acm-conf
newtex exlang-paper acm-conf --no-git
newtex exlang-paper acm-conf --track-pdf
newtex exlang-paper acm-conf --no-vscode
newtex exlang-paper acm-conf --open
```

Interactive flow now shows a scaffold plan summary before generation and asks for confirmation.

<details>
<summary><strong>Advanced commands</strong></summary>

```bash
newtex --tests
newtex --publish-check
newtex --template-set acm-conf=/absolute/path/to/template
newtex --default-template-set acm-conf
newtex --templates-list
```

</details>

## 4. Notes

- Project names must be lowercase kebab-case (example: `exlang-paper`).
- If a template path is invalid, the CLI exits with an error message.
- Template sources support three modes:
	- local directory path (copied as-is)
	- `package://<name>` (copied from bundled package resources)
	- remote template URL (scaffolded via Copier)

## 5. Maintainer Release (optional)

End users can skip this section.

### 5.1 Build distributions

```bash
python -m pip install -e ".[publish]"
newtex --publish-check
python -m build
```

### 5.2 Upload to PyPI

You need a PyPI account to publish public packages.

Set token-based auth (recommended):

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-api-token>
```

```bash
python -m twine upload dist/*
```

### 5.3 Install on another machine (cross-platform)

```bash
pipx install newtex-cli
python -m pip install newtex-cli
```

Then configure templates on that machine:

```bash
newtex --template-set acm-conf=/absolute/path/or/url/to/template
newtex --default-template-set acm-conf
```
