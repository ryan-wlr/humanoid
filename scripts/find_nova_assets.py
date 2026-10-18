import os
import omni
import carb
from omni.isaac.kit import SimulationApp

# Only create SimulationApp when running standalone
simulation_app = None
try:
    import omni.kit.app

    kit_app = omni.kit.app.get_app()
    if kit_app is None or not kit_app.is_running():
        simulation_app = SimulationApp({"headless": True})
except Exception:
    simulation_app = SimulationApp({"headless": True})

from omni.isaac.core.utils.nucleus import get_assets_root_path

out_path = os.path.join(os.path.dirname(__file__), "nova_asset_probe.txt")


def log(msg: str):
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


assets_root = get_assets_root_path()
log(f"assets_root: {assets_root}")

candidate_roots = [
    assets_root,
    "omniverse://localhost/NVIDIA/Assets/Isaac",
    "omniverse://localhost/NVIDIA/Assets/Isaac/5.1",
    "omniverse://localhost/NVIDIA/Assets/Isaac/4.5",
]

log(f"candidate_roots: {candidate_roots}")

candidate_paths = []
for root in candidate_roots:
    if not root:
        continue
    candidate_paths.extend(
        [
            f"{root}/Isaac/Environments/Nova_Carter_Warehouse/nova_carter_warehouse.usd",
            f"{root}/Isaac/Environments/Nova_Carter/warehouse.usd",
            f"{root}/Isaac/Environments/Nova_Carter/nova_carter_warehouse.usd",
        ]
    )

log("Checking candidate paths:")
for path in candidate_paths:
    try:
        result, _ = omni.client.stat(path)
        log(f"{path} -> {result}")
    except Exception as exc:
        log(f"{path} -> EXCEPTION: {exc}")

if simulation_app is not None:
    simulation_app.close()
