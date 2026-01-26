import os
import runpy
from pathlib import Path


def _read_first_line(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
        # Some editors may write a UTF-8 BOM at the start of the file.
        text = text.lstrip("\ufeff")
        return text if text else None
    except Exception:
        return None


def _maybe_set_env_from_marker(env_name: str, marker_path: Path) -> None:
    if os.environ.get(env_name, "").strip():
        return
    value = _read_first_line(marker_path)
    if value:
        os.environ[env_name] = value


def _main() -> None:
    # Repo root = <repo>/setup_windows/this_file.py -> parents[1]
    repo_root = Path(__file__).resolve().parents[1]

    # Prefer explicit local Kitchen Set stage if available.
    kitchen_marker = repo_root / "assets" / "kitchen_set" / "kitchen_set_usd_path.txt"
    _maybe_set_env_from_marker("UNITREE_STAGE_USD", kitchen_marker)

    # Fallback: ask the underlying loader to try the kitchen preset paths.
    if not os.environ.get("UNITREE_STAGE_USD", "").strip():
        os.environ.setdefault("UNITREE_STAGE_PRESET", "kitchen")

    # Prefer explicit local Unitree G1 USD if available.
    g1_marker = repo_root / "assets" / "unitree_g1" / "unitree_g1_usd_path.txt"
    _maybe_set_env_from_marker("UNITREE_G1_USD", g1_marker)

    # Delegate to the existing, battle-tested loader/spawner script.
    loader_path = Path(__file__).resolve().parent / "auto_load_unitree_g1.py"
    runpy.run_path(str(loader_path), run_name="__main__")


_main()
