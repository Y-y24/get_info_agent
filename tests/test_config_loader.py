import tempfile
import os
from config_loader import load_config


def test_load_config_parses_yaml():
    yaml_content = """
news:
  sources: ["weibo"]
email:
  to_address: "test@qq.com"
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert config["news"]["sources"] == ["weibo"]
        assert config["email"]["to_address"] == "test@qq.com"
    finally:
        os.unlink(tmp_path)


def test_load_config_defaults():
    yaml_content = "news:\n  sources: []"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert "email" in config
        assert "deepseek" in config
        assert config["email"]["smtp_host"] == "smtp.qq.com"
    finally:
        os.unlink(tmp_path)
