import os
import omni
from omni.isaac.kit import SimulationApp

simulation_app = None
try:
    import omni.kit.app

    kit_app = omni.kit.app.get_app()
    if kit_app is None or not kit_app.is_running():
        simulation_app = SimulationApp({"headless": True})
except Exception:
    simulation_app = SimulationApp({"headless": True})

scenario_url = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/ROS2/Scenario/"

out_path = os.path.join(os.path.dirname(__file__), "scenario_usd_list.txt")

with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"Listing: {scenario_url}\n")

result, entries = omni.client.list(scenario_url)
with open(out_path, "a", encoding="utf-8") as f:
    f.write(f"Result: {result}\n")
    for e in entries or []:
        name = (
            getattr(e, "relative_path", None)
            or getattr(e, "path", None)
            or getattr(e, "name", None)
            or str(e)
        )
        f.write(f"ENTRY: {name}\n")
        if isinstance(name, str) and name.lower().endswith(".usd"):
            f.write(f"USD: {name}\n")

if simulation_app is not None:
    simulation_app.close()
