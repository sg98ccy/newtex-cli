import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "newtex"
CONFIG_FILE = CONFIG_DIR / "templates.yml"
ACM_TEMPLATE_ENV = "NEWTEX_TEMPLATE_ACM_PATH"
DEFAULT_TEMPLATE_ENV = "NEWTEX_DEFAULT_TEMPLATE"


def _load_environment() -> None:
    load_dotenv(override=False)
    load_dotenv(Path.cwd() / ".env.local", override=True)


def _default_config() -> dict:
    return {
        "default_template": os.getenv(DEFAULT_TEMPLATE_ENV, "acm"),
        "templates": {
            "acm": {
                "path": os.getenv(ACM_TEMPLATE_ENV, ""),
                "description": "ACM Conference Proceedings Primary Article",
            }
        },
    }


def _apply_env_overrides(config: dict) -> dict:
    default_template = os.getenv(DEFAULT_TEMPLATE_ENV)
    acm_path = os.getenv(ACM_TEMPLATE_ENV)

    if default_template:
        config["default_template"] = default_template

    templates = config.setdefault("templates", {})
    acm_template = templates.setdefault(
        "acm",
        {
            "path": "",
            "description": "ACM Conference Proceedings Primary Article",
        },
    )

    if acm_path:
        acm_template["path"] = acm_path

    return config


def ensure_config() -> None:
    _load_environment()
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
    _load_environment()
    config = load_persisted_config()

    return _apply_env_overrides(config)
