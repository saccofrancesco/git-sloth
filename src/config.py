from pathlib import Path
from platformdirs import user_config_dir
import tomli
import tomli_w

CONFIG_DIR = Path(user_config_dir("gitsloth"))
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_config() -> dict[str, str]:
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "rb") as f:
        return tomli.load(f)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(config, f)


def set_api_key(key: str) -> None:
    config = load_config()

    if "openai" not in config:
        config["openai"] = {}

    config["openai"]["api_key"] = key

    save_config(config)


def get_api_key() -> str | None:
    config = load_config()
    return config.get("openai", {}).get("api_key")
