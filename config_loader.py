import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+ standard library
except ModuleNotFoundError:
    import tomli as tomllib  # Fallback to tomli (unlikely for Python 3.12+ projects)


def load_config() -> dict:
    """Load config.toml, return empty config on error"""
    config_path = Path("config.toml")

    if not config_path.exists():
        print("Error: config.toml not found.")
        print("  Copy config.toml.example to config.toml and fill in your credentials.")
        return _empty_config()

    try:
        with open(config_path, "rb") as f:  # TOML requires binary mode
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"Error: config.toml is not valid TOML: {e}")
        return _empty_config()
    except Exception as e:
        print(f"Error loading config.toml: {e}")
        return _empty_config()


def _empty_config() -> dict:
    """Return empty config structure to prevent crashes"""
    return {
        "USE_PROXY": False,
        "proxies": {},
        "USER_CONFIGS": [],
        "INQUIRY_USER_DATA": {},
        "ENROLLMENT_DATA_API_PARAMS": {},
    }


# Module-level exports for compatibility
config = load_config()
USE_PROXY = config.get("USE_PROXY", False)
proxies = config.get("proxies", {})
USER_CONFIGS = config.get("USER_CONFIGS", [])
INQUIRY_USER_DATA = config.get("INQUIRY_USER_DATA", {})
ENROLLMENT_DATA_API_PARAMS = config.get("ENROLLMENT_DATA_API_PARAMS", {})
