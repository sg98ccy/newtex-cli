from pathlib import Path

import yaml

import newtex.config as config_module


def _bundled_templates() -> dict:
    return {
        "acm-conf": {
            "path": "package://acm-conf",
            "description": "ACM Conference Proceedings Primary Article",
        },
        "ntu-report-template": {
            "path": "package://ntu-report-template",
            "description": "NTU Report Template",
        },
    }


def test_ensure_config_creates_file(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config_module, "discover_bundled_templates", _bundled_templates)

    config_module.ensure_config()

    assert cfg_file.exists()
    content = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert "templates" in content
    assert "acm-conf" in content["templates"]
    assert "ntu-report-template" in content["templates"]
    assert content["templates"]["acm-conf"]["path"] == "package://acm-conf"


def test_load_config_backfills_empty_bundled_path(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(
        yaml.safe_dump(
            {
                "default_template": "acm-conf",
                "templates": {
                    "acm-conf": {
                        "path": "",
                        "description": "ACM Conference Proceedings Primary Article",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config_module, "discover_bundled_templates", _bundled_templates)

    loaded = config_module.load_config()

    assert loaded["templates"]["acm-conf"]["path"] == "package://acm-conf"


def test_load_config_includes_new_bundled_templates(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(
        yaml.safe_dump(
            {
                "default_template": "acm-conf",
                "templates": {
                    "acm-conf": {
                        "path": "package://acm-conf",
                        "description": "ACM Conference Proceedings Primary Article",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config_module, "discover_bundled_templates", _bundled_templates)

    loaded = config_module.load_config()

    assert "ntu-report-template" in loaded["templates"]
    assert loaded["templates"]["ntu-report-template"]["path"] == "package://ntu-report-template"


def test_load_config_user_alias_wins_over_bundled(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(
        yaml.safe_dump(
            {
                "default_template": "acm-conf",
                "templates": {
                    "acm-conf": {
                        "path": "/custom/acm",
                        "description": "Custom ACM",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config_module, "discover_bundled_templates", _bundled_templates)

    loaded = config_module.load_config()

    assert loaded["templates"]["acm-conf"]["path"] == "/custom/acm"
    assert loaded["templates"]["acm-conf"]["description"] == "Custom ACM"


def test_upsert_template_and_set_default(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config_module, "discover_bundled_templates", _bundled_templates)

    config_module.upsert_template(alias="ieee", template_path="/tmp/ieee", description="IEEE")
    saved = config_module.load_persisted_config()
    assert saved["templates"]["ieee"]["path"] == "/tmp/ieee"

    config_module.set_default_template("ieee")
    updated = config_module.load_persisted_config()
    assert updated["default_template"] == "ieee"
