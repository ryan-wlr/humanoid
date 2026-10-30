"""Static checks for the fruit-sorting USD setup.

Run this with Isaac Sim Kit after the main scene has been exported:
    set SCENE_PATH=C:\path\to\scene.usd
    C:\isaacsim\kit\kit.exe C:\isaacsim\apps\isaacsim.exp.full.kit --no-window --exec scripts\validate_fruit_sorting_scene.py
"""
import os
import sys

from pxr import Usd


def main() -> int:
    scene_path = sys.argv[1] if len(sys.argv) == 2 else os.getenv("SCENE_PATH")
    if not scene_path:
        print("Set SCENE_PATH or pass one USD path.")
        return 2

    stage = Usd.Stage.Open(scene_path)
    if stage is None:
        print("Could not open scene: " + scene_path)
        return 1

    expected_bins = ("Apple", "Orange", "Banana", "Lemon")
    failures = []
    for fruit in expected_bins:
        prim = stage.GetPrimAtPath("/World/SortingBins/" + fruit)
        if not prim.IsValid():
            failures.append("missing bin: " + fruit)
            continue
        if prim.GetAttribute("fruit_sorting:fruit").Get() != fruit.lower():
            failures.append("wrong fruit attribute: " + fruit)
        if prim.GetAttribute("fruit_sorting:drop_position").Get() is None:
            failures.append("missing drop position: " + fruit)

    apple = stage.GetPrimAtPath("/World/Apple")
    if not apple.IsValid():
        failures.append("missing animated apple")

    if failures:
        print("Fruit sorting scene is invalid:")
        for failure in failures:
            print("- " + failure)
        return 1

    print("Fruit sorting scene is valid.")
    return 0


if __name__ == "__main__":
    exit_code = main()
    try:
        import omni.kit.app

        omni.kit.app.get_app().post_quit()
    except ImportError:
        pass
    raise SystemExit(exit_code)
