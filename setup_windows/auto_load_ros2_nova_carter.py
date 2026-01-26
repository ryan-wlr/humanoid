import asyncio
import os
from datetime import datetime

import carb
import omni.timeline
import omni.usd


STAGE_REL_PATH = "/Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd"


def _append_marker(message: str) -> None:
    try:
        marker_path = os.path.join(os.path.dirname(__file__), "auto_load_ros2_nova_carter.status.txt")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(marker_path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        # Intentionally swallow to avoid breaking startup.
        pass


async def _load_and_play() -> None:
    try:
        _append_marker("Script started")
        from isaacsim.storage.native import get_assets_root_path

        assets_root = get_assets_root_path()
        if not assets_root:
            carb.log_error("Could not resolve Isaac Sim assets root path")
            _append_marker("ERROR: get_assets_root_path() returned empty")
            return

        stage_path = assets_root + STAGE_REL_PATH
        carb.log_info(f"Opening stage: {stage_path}")
        _append_marker(f"Assets root: {assets_root}")
        _append_marker(f"Stage path: {stage_path}")

        await omni.usd.get_context().open_stage_async(stage_path)
        carb.log_info("Stage opened; starting simulation (timeline.play)")
        _append_marker("Stage opened")

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        _append_marker("Timeline play() called")
    except Exception as exc:
        carb.log_error(f"Auto-load ROS2 sample failed: {exc}")
        _append_marker(f"ERROR: {exc!r}")


asyncio.ensure_future(_load_and_play())
