from pathlib import Path
from importlib import resources

import yaml

CONFIG_DIR = Path.home() / ".config" / "newtex"
CONFIG_FILE = CONFIG_DIR / "templates.yml"
DEFAULT_TEMPLATE_ALIAS = "acm-conf"
TEMPLATE_METADATA_FILENAME = "newtex-template.yml"


def _format_template_description(alias: str) -> str:
    return alias.replace("-", " ").title()


def _packaged_template_path(alias: str) -> str:
    return f"package://{alias}"


def _load_template_metadata(template_dir) -> dict:
    metadata_file = template_dir / TEMPLATE_METADATA_FILENAME
    if not metadata_file.is_file():
        return {}

    try:
        loaded = yaml.safe_load(metadata_file.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}

    if not isinstance(loaded, dict):
        return {}

    return loaded


def discover_bundled_templates() -> dict:
    templates_root = resources.files("newtex.resources.templates")
    templates: dict[str, dict[str, str]] = {}

    for template_dir in sorted(templates_root.iterdir(), key=lambda entry: entry.name):
        if not template_dir.is_dir():
            continue

        alias = template_dir.name
        if alias.startswith(".") or alias.startswith("__"):
            continue

        metadata = _load_template_metadata(template_dir)
        description = str(metadata.get("description", "")).strip() or _format_template_description(alias)

        templates[alias] = {
            "path": _packaged_template_path(alias),
            "description": description,
        }

    return templates


def _normalize_template(alias: str, template: object, bundled_templates: dict) -> dict:
    bundled = bundled_templates.get(alias, {})
    normalized = template if isinstance(template, dict) else {}

    path = str(normalized.get("path", "")).strip()
    if not path:
        path = bundled.get("path", "")

    description = str(normalized.get("description", "")).strip()
    if not description:
        description = bundled.get("description", _format_template_description(alias))

    return {
        "path": path,
        "description": description,
    }


def _merge_with_bundled_templates(config: dict) -> dict:
    bundled_templates = discover_bundled_templates()

    templates: dict[str, dict] = {
        alias: _normalize_template(alias, template, bundled_templates)
        for alias, template in bundled_templates.items()
    }

    configured_templates = config.get("templates", {})
    if isinstance(configured_templates, dict):
        for alias, template in configured_templates.items():
            templates[alias] = _normalize_template(alias, template, bundled_templates)

    configured_default = config.get("default_template")
    if configured_default in templates:
        default_template = configured_default
    elif DEFAULT_TEMPLATE_ALIAS in templates:
        default_template = DEFAULT_TEMPLATE_ALIAS
    else:
        default_template = next(iter(templates), "")

    return {
        "default_template": default_template,
        "templates": templates,
    }


def _default_config() -> dict:
    return _merge_with_bundled_templates({})


def ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            yaml.safe_dump(_default_config(), file, sort_keys=False)


def load_persisted_config() -> dict:
    ensure_config()
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        yaml.safe_dump(config, file, sort_keys=False)


def upsert_template(alias: str, template_path: str, description: str | None = None) -> dict:
    config = load_persisted_config()
    templates = config.setdefault("templates", {})
    existing = templates.get(alias, {})

    templates[alias] = {
        "path": template_path,
        "description": description if description is not None else existing.get("description", ""),
    }

    if "default_template" not in config:
        config["default_template"] = alias

    save_config(config)
    return config


def set_default_template(alias: str) -> dict:
    config = load_persisted_config()
    templates = config.get("templates", {})
    if alias not in templates:
        raise KeyError(f"Unknown template alias: {alias}")

    config["default_template"] = alias
    save_config(config)
    return config


def load_config() -> dict:
    config = load_persisted_config()
    return _merge_with_bundled_templates(config)
