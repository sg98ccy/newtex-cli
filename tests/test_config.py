from pathlib import Path

import yaml

import newtex.config as config_module


def test_load_environment_prefers_env_local(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_local_file = tmp_path / ".env.local"
    env_file.write_text("NEWTEX_TEMPLATE_ACM_PATH=/from-env\n", encoding="utf-8")
    env_local_file.write_text("NEWTEX_TEMPLATE_ACM_PATH=/from-env-local\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path / "cfg")
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "cfg" / "templates.yml")

    loaded = config_module.load_config()

    assert loaded["templates"]["acm"]["path"] == "/from-env-local"


def test_ensure_config_creates_file(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(config_module.ACM_TEMPLATE_ENV, raising=False)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)

    config_module.ensure_config()

    assert cfg_file.exists()
    content = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert "templates" in content
    assert "acm" in content["templates"]
    assert content["templates"]["acm"]["path"] == "package://acm"


def test_load_config_backfills_empty_acm_path(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(
        yaml.safe_dump(
            {
                "default_template": "acm",
                "templates": {
                    "acm": {
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
    monkeypatch.delenv(config_module.ACM_TEMPLATE_ENV, raising=False)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)

    loaded = config_module.load_config()

    assert loaded["templates"]["acm"]["path"] == "package://acm"


def test_upsert_template_and_set_default(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_file = cfg_dir / "templates.yml"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_file)

    config_module.upsert_template(alias="ieee", template_path="/tmp/ieee", description="IEEE")
    saved = config_module.load_persisted_config()
    assert saved["templates"]["ieee"]["path"] == "/tmp/ieee"

    config_module.set_default_template("ieee")
    updated = config_module.load_persisted_config()
    assert updated["default_template"] == "ieee"
