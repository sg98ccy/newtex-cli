<h1 align="center">newtex-cli</h1>

<p align="center">Scaffold local LaTeX projects from reusable templates.</p>

## 1. Installation

```bash
pipx install newtex-scaffold
```

## 2. Configuration

### 2.1 Local environment file

Create `.env.local` in the project root:

```bash
NEWTEX_DEFAULT_TEMPLATE=acm
NEWTEX_TEMPLATE_ACM_PATH=/path/to/your/acm-template
```

### 2.2 Global template config (recommended)

Configure templates once and use `newtex` from anywhere:

```bash
newtex --template-set acm=/absolute/path/or/url/to/template
newtex --set-default-template acm
newtex --templates-list
```

This writes to `~/.config/newtex/templates.yml`.

## 3. CLI Commands

### 3.1 Command reference

| Command | Description |
| --- | --- |
| `newtex --help` | Show CLI help |
| `newtex --tests` | Run the full test suite |
| `newtex --publish-check` | Validate build/upload prerequisites |
| `newtex --template-set <alias>=<path-or-url>` | Add or update a global template alias |
| `newtex --template-set <alias>=<path-or-url> --template-description "..."` | Add alias with description |
| `newtex --set-default-template <alias>` | Set the global default template alias |
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
newtex
newtex exlang-paper acm
newtex exlang-paper acm --no-git
newtex exlang-paper acm --track-pdf
newtex exlang-paper acm --no-vscode
newtex exlang-paper acm --open
```

<details>
<summary><strong>Advanced commands</strong></summary>

```bash
newtex --tests
newtex --publish-check
newtex --template-set acm=/absolute/path/to/template
newtex --set-default-template acm
newtex --templates-list
```

</details>

## 4. Notes

- Project names must be lowercase kebab-case (example: `exlang-paper`).
- If a template path is invalid, the CLI exits with an error message.

## 5. Build & Publish

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

### 5.3 Install on another Mac

```bash
pipx install newtex-scaffold
```

Then configure templates on that machine:

```bash
newtex --template-set acm=/absolute/path/or/url/to/template
newtex --set-default-template acm
```
