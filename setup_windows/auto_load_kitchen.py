import asyncio
import os
from datetime import datetime

import carb
import omni.timeline
import omni.usd


KITCHEN_STAGE_USD_CANDIDATES_REL = [
    "/Isaac/Environments/Kitchen/kitchen.usd",
    "/Isaac/Environments/Kitchen/chef_kitchen.usd",
    "/Isaac/Environments/Simple_Kitchen/kitchen.usd",
    "/Isaac/Environments/Simple_Kitchen/simple_kitchen.usd",
    "/Isaac/Environments/Office_Kitchen/office_kitchen.usd",
]


def _append_marker(message: str) -> None:
    try:
        import os

        marker_path = os.path.join(os.path.dirname(__file__), "auto_load_kitchen.status.txt")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(marker_path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        pass


def _omniverse_path_exists(path: str) -> bool:
    try:
        import omni.client

        result, _entry = omni.client.stat(path)
        return result == omni.client.Result.OK
    except Exception:
        return False


async def _open_stage(stage_path: str) -> None:
    await omni.usd.get_context().open_stage_async(stage_path)
    await asyncio.sleep(0.2)


async def _load_and_play() -> None:
    try:
        _append_marker("Script started")

        stage_override = os.environ.get("KITCHEN_STAGE_USD", "").strip()
        if stage_override:
            _append_marker(f"Kitchen USD (user): {stage_override}")
            await _open_stage(stage_override)
        else:
            from isaacsim.storage.native import get_assets_root_path

            assets_root = get_assets_root_path()
            if not assets_root:
                _append_marker("ERROR: get_assets_root_path() returned empty")
                return

            _append_marker(f"Assets root: {assets_root}")

            stage_candidate = None
            for rel in KITCHEN_STAGE_USD_CANDIDATES_REL:
                candidate = assets_root + rel
                if _omniverse_path_exists(candidate):
                    stage_candidate = candidate
                    break

            if not stage_candidate:
                _append_marker("ERROR: No kitchen USD found under assets root")
                carb.log_error(
                    "No kitchen USD found. Tried:\n"
                    + "\n".join(["<assets_root>" + r for r in KITCHEN_STAGE_USD_CANDIDATES_REL])
                    + "\n\nTip: set KITCHEN_STAGE_USD to a local path or omniverse:// url."
                )
                return

            _append_marker(f"Kitchen USD: {stage_candidate}")
            await _open_stage(stage_candidate)

        _append_marker("Stage ready")
        omni.timeline.get_timeline_interface().play()
        _append_marker("Timeline play() called")

    except Exception as exc:
        _append_marker(f"ERROR: {exc!r}")
        carb.log_error(f"Auto-load kitchen failed: {exc}")


asyncio.ensure_future(_load_and_play())
