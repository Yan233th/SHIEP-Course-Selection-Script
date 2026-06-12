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


def add_course_to_config(label: str, profile_id: str, course_id: str) -> bool:
    """
    Add a course ID to the specified user's config.toml configuration.

    Args:
        label: User label (label in USER_CONFIGS)
        profile_id: Course table ID (profileId in tables)
        course_id: Course ID (to be added to course_ids list)

    Returns:
        True if added successfully, False if failed (not found or already exists)
    """
    try:
        import tomli_w
    except ImportError:
        print("Error: tomli_w not installed. Run: uv sync")
        return False

    config_path = Path("config.toml")
    if not config_path.exists():
        print("Error: config.toml not found.")
        return False

    # Read current config
    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
    except Exception as e:
        print(f"Error reading config.toml: {e}")
        return False

    # Find corresponding user config
    user_config = None
    for user in config_data.get("USER_CONFIGS", []):
        if user.get("label") == label:
            user_config = user
            break

    if not user_config:
        print(f"Error: User '{label}' not found in config.toml")
        return False

    # Find corresponding table (profileId match)
    target_table = None
    for table in user_config.get("tables", []):
        if str(table.get("profileId")) == str(profile_id):
            target_table = table
            break

    if not target_table:
        print(f"Error: Table with profileId '{profile_id}' not found for user '{label}'")
        return False

    # Check if course ID already exists
    course_ids = target_table.get("course_ids", [])
    if course_id in [str(cid) for cid in course_ids]:
        print(f"Course ID {course_id} already exists in user '{label}', table '{profile_id}'")
        return False

    # Add course ID
    course_ids.append(course_id)
    target_table["course_ids"] = course_ids

    # Write back to TOML
    try:
        with open(config_path, "wb") as f:
            tomli_w.dump(config_data, f)
        print(f"✓ Successfully added course {course_id} to user '{label}', table '{profile_id}'")
        return True
    except Exception as e:
        print(f"Error writing config.toml: {e}")
        return False


def list_user_configs() -> list[dict]:
    """
    List all users and their tables in USER_CONFIGS for interactive selection.

    Returns:
        [{"label": "User_Alice", "tables": [{"profileId": "114514"}, ...]}, ...]
    """
    user_configs = config.get("USER_CONFIGS", [])
    return [
        {
            "label": user.get("label", "Unknown"),
            "tables": [
                {"profileId": str(table.get("profileId", ""))}
                for table in user.get("tables", [])
            ]
        }
        for user in user_configs
    ]
