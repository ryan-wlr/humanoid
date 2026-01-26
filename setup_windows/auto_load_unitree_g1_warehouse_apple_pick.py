from __future__ import annotations

import asyncio
import os
import re
import traceback
from datetime import datetime
from pathlib import Path

import carb
import omni.timeline
import omni.usd


# ROS2 sample warehouse used by Nova Carter tutorial.
# This is a good default “warehouse” environment shipped with Isaac Sim.
STAGE_REL_PATH = "/Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd"

ROBOT_USD_CANDIDATES_REL = [
    "/Isaac/Robots/Unitree/G1/g1.usd",
    "/Isaac/Robots/Unitree/G1/unitree_g1.usd",
    "/Isaac/Robots/Unitree/UnitreeG1/g1.usd",
    "/Isaac/Robots/Unitree/UnitreeG1/unitree_g1.usd",
]

ROBOT_PRIM_PATH = "/World/UnitreeG1"  # Parent Xform we move/animate.
ROBOT_REF_PRIM_PATH = f"{ROBOT_PRIM_PATH}/Robot"  # Where the USD reference is applied.
FRAME_TARGET_PRIM_PATH = "/World/UnitreeG1_FrameTarget"
SAFE_CAMERA_PRIM_PATH = "/World/UnitreeG1_SafeCamera"
PROPS_ROOT = "/World/Props"
TABLE_PRIM_PATH = f"{PROPS_ROOT}/Table"
APPLE_PRIM_PATH = f"{PROPS_ROOT}/Apple"
HELD_ROOT = f"{ROBOT_PRIM_PATH}/HandHold"
HELD_APPLE_PRIM_PATH = f"{HELD_ROOT}/Apple"

SPAWN_MARKER_PRIM_PATH = f"{PROPS_ROOT}/SpawnMarker"


def _append_marker(message: str) -> None:
    try:
        marker_path = os.path.join(os.path.dirname(__file__), "auto_load_unitree_g1_warehouse_apple_pick.status.txt")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(marker_path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        pass


def _reset_marker_log() -> None:
    try:
        marker_path = os.path.join(os.path.dirname(__file__), "auto_load_unitree_g1_warehouse_apple_pick.status.txt")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write(f"[{stamp}] (log reset)\n")
    except Exception:
        pass


def _omniverse_path_exists(path: str) -> bool:
    try:
        import omni.client

        result, _entry = omni.client.stat(path)
        return result == omni.client.Result.OK
    except Exception:
        return False


def _path_exists(path: str) -> bool:
    try:
        if path.lower().startswith("omniverse://"):
            return _omniverse_path_exists(path)
        return Path(path).exists()
    except Exception:
        return False


def _to_usd_asset_path(path: str) -> str:
    """Convert a local filesystem path into a USD-friendly asset identifier.

    On Windows, passing backslash paths to USD references can be flaky.
    Converting to a file:// URI is the most robust.
    """
    p = path.strip()
    if not p:
        return p
    if p.lower().startswith("omniverse://"):
        return p
    try:
        return Path(p).resolve().as_uri()
    except Exception:
        # Fallback: best-effort normalization.
        return p.replace("\\", "/")


def _resolve_user_robot_usd() -> str | None:
    override = os.environ.get("UNITREE_G1_USD", "").strip()
    if override:
        return override

    # Repo-local drop-in location (kept out of git).
    repo_root = Path(__file__).resolve().parents[1]
    local_usd = repo_root / "assets" / "unitree_g1" / "g1.usd"
    if local_usd.exists():
        return str(local_usd)

    # Marker file created by download_unitree_g1_from_unitree_model.ps1
    marker = repo_root / "assets" / "unitree_g1" / "unitree_g1_usd_path.txt"
    if marker.exists():
        try:
            p = marker.read_text(encoding="utf-8").strip().lstrip("\ufeff")
            if p:
                return p
        except Exception:
            pass

    return None


def _resolve_isaac_robot_usd() -> str | None:
    try:
        from isaacsim.storage.native import get_assets_root_path

        assets_root = get_assets_root_path()
        if not assets_root:
            return None

        for rel in ROBOT_USD_CANDIDATES_REL:
            candidate = assets_root + rel
            if _omniverse_path_exists(candidate):
                return candidate

        return None
    except Exception:
        return None


def _discover_robot_asset_root(robot_usd_path: str) -> str | None:
    """Return a prim path inside the robot USD that should be referenced.

    Some vendor USDs ship without a defaultPrim. Referencing the file without a
    prim path can yield an empty reference in those cases.
    """
    try:
        from pxr import Usd

        asset_stage = Usd.Stage.Open(_to_usd_asset_path(robot_usd_path))
        if asset_stage is None:
            return None

        dp = asset_stage.GetDefaultPrim()
        if dp and dp.IsValid():
            return dp.GetPath().pathString

        roots = [p for p in asset_stage.GetPseudoRoot().GetChildren() if p.IsValid()]
        if not roots:
            return None

        return roots[0].GetPath().pathString
    except Exception:
        return None


async def _open_warehouse_stage() -> None:
    from isaacsim.storage.native import get_assets_root_path

    assets_root = get_assets_root_path()
    if not assets_root:
        raise RuntimeError("Could not resolve Isaac Sim assets root path")

    stage_path = assets_root + STAGE_REL_PATH
    _append_marker(f"Opening warehouse stage: {stage_path}")
    carb.log_info(f"Opening stage: {stage_path}")

    await omni.usd.get_context().open_stage_async(stage_path)
    await asyncio.sleep(0.25)


def _ensure_props_root(stage) -> None:
    from pxr import Sdf, UsdGeom

    if not stage.GetPrimAtPath("/World").IsValid():
        UsdGeom.Xform.Define(stage, Sdf.Path("/World"))

    if not stage.GetPrimAtPath(PROPS_ROOT).IsValid():
        UsdGeom.Xform.Define(stage, Sdf.Path(PROPS_ROOT))


def _spawn_table_and_apple(stage, table_center=(2.2, 0.0, 0.0)) -> None:
    """Create a simple table (cube) and an apple (sphere) on it."""
    from pxr import Gf, Sdf, UsdGeom

    _ensure_props_root(stage)

    # Table: a scaled cube.
    table = UsdGeom.Cube.Define(stage, Sdf.Path(TABLE_PRIM_PATH))
    table.CreateSizeAttr(1.0)
    table_xf = UsdGeom.XformCommonAPI(table)

    # Dimensions (meters-ish).
    table_size = Gf.Vec3f(1.2, 0.7, 0.75)
    table_pos = Gf.Vec3d(table_center[0], table_center[1], table_center[2] + float(table_size[2] * 0.5))
    table_xf.SetScale(table_size)
    table_xf.SetTranslate(table_pos)

    # Apple: a small red sphere on top of the table.
    apple = UsdGeom.Sphere.Define(stage, Sdf.Path(APPLE_PRIM_PATH))
    apple.CreateRadiusAttr(0.06)
    apple_xf = UsdGeom.XformCommonAPI(apple)
    apple_pos = Gf.Vec3d(table_center[0], table_center[1], table_center[2] + float(table_size[2] + 0.06 + 0.01))
    apple_xf.SetTranslate(apple_pos)

    # Color it red.
    apple.CreateDisplayColorAttr([(1.0, 0.1, 0.1)])

    _append_marker(f"Table created at {tuple(table_pos)}")
    _append_marker(f"Apple created at {tuple(apple_pos)}")


def _spawn_marker(stage, pos=(1.2, 0.0, 0.05)) -> None:
    """Spawn a large visual marker to make the spawn location obvious."""
    from pxr import Gf, Sdf, UsdGeom

    _ensure_props_root(stage)
    m = UsdGeom.Cube.Define(stage, Sdf.Path(SPAWN_MARKER_PRIM_PATH))
    m.CreateSizeAttr(1.0)
    x = UsdGeom.XformCommonAPI(m)
    x.SetScale(Gf.Vec3f(0.25, 0.25, 0.25))
    x.SetTranslate(Gf.Vec3d(*pos))
    m.CreateDisplayColorAttr([(1.0, 0.0, 0.0)])
    _append_marker(f"Spawn marker created at {pos}")


def _spawn_g1(stage, robot_usd_path: str, spawn_pos=(1.2, 0.0, 0.02)) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom

    robot_root = stage.GetPrimAtPath(ROBOT_PRIM_PATH)
    if not robot_root.IsValid():
        robot_root = UsdGeom.Xform.Define(stage, Sdf.Path(ROBOT_PRIM_PATH)).GetPrim()

    robot_ref = stage.GetPrimAtPath(ROBOT_REF_PRIM_PATH)
    if not robot_ref.IsValid():
        robot_ref = UsdGeom.Xform.Define(stage, Sdf.Path(ROBOT_REF_PRIM_PATH)).GetPrim()

    # Apply reference (with best-effort primPath).
    asset_path = _to_usd_asset_path(robot_usd_path)
    prim_path = _discover_robot_asset_root(robot_usd_path)
    if prim_path:
        robot_ref.GetReferences().AddReference(assetPath=asset_path, primPath=prim_path)
        _append_marker(f"Referenced robot USD with primPath={prim_path} assetPath={asset_path}")
    else:
        robot_ref.GetReferences().AddReference(assetPath=asset_path)
        _append_marker(f"Referenced robot USD (no primPath) assetPath={asset_path}")

    # Some assets use payloads; ensure they're loaded so geometry appears.
    try:
        robot_ref.Load()
        _append_marker("Requested payload load on /World/UnitreeG1")
    except Exception as exc:
        _append_marker(f"NOTE: Could not call Load() on robot prim: {exc!r}")

    # Many complex robot assets can report pathological bounds (very large or otherwise
    # invalid), which makes framing unstable. Provide a conservative extentsHint.
    try:
        model_api = UsdGeom.ModelAPI.Apply(robot_ref)
        model_api.SetExtentsHint([Gf.Vec3f(-1.0, -1.0, 0.0), Gf.Vec3f(1.0, 1.0, 2.2)])
        _append_marker("Applied extentsHint on /World/UnitreeG1")
    except Exception as exc:
        _append_marker(f"WARNING: Could not apply extentsHint: {exc!r}")

    xfc = UsdGeom.XformCommonAPI(robot_root)
    xfc.SetTranslate(Gf.Vec3d(*spawn_pos))
    # Face roughly +X (towards the table by default).
    xfc.SetRotate(Gf.Vec3f(0.0, 0.0, 0.0), UsdGeom.XformCommonAPI.RotationOrderXYZ)

    _append_marker(f"Spawned robot at {spawn_pos}")

    # Diagnostics: confirm we actually got renderable prims.
    try:
        mesh_count = 0
        gprim_count = 0
        point_instancer_count = 0
        for p in Usd.PrimRange(robot_ref, Usd.TraverseInstanceProxies()):
            if p.IsA(UsdGeom.Mesh):
                mesh_count += 1
            if p.IsA(UsdGeom.Gprim):
                gprim_count += 1
            if p.IsA(UsdGeom.PointInstancer):
                point_instancer_count += 1
        _append_marker(
            f"Robot prim descendants: gprims={gprim_count} meshes={mesh_count} pointInstancers={point_instancer_count}"
        )
        if mesh_count == 0 and gprim_count == 0 and point_instancer_count == 0:
            _append_marker("WARNING: Robot reference appears empty (no Gprims/Meshes)")
    except Exception as exc:
        _append_marker(f"WARNING: Could not count robot prims: {exc!r}")

    # Log computed bounds for debugging (helps explain framing issues).
    try:
        bbox_cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            includedPurposes=[UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
            useExtentsHint=True,
        )
        world_bbox = bbox_cache.ComputeWorldBound(robot_ref)
        box = world_bbox.ComputeAlignedBox()
        mn = box.GetMin()
        mx = box.GetMax()
        _append_marker(
            f"UnitreeG1 bounds min={mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f} max={mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f}"
        )
    except Exception as exc:
        _append_marker(f"WARNING: Could not compute bounds: {exc!r}")


def _lift_robot_above_floor(stage, floor_z: float = 0.0, clearance: float = 0.02) -> None:
    """Adjust the robot root translate so its lowest bound sits above the floor."""
    try:
        from pxr import Gf, Usd, UsdGeom

        robot_root = stage.GetPrimAtPath(ROBOT_PRIM_PATH)
        robot_ref = stage.GetPrimAtPath(ROBOT_REF_PRIM_PATH)
        if not robot_root.IsValid() or not robot_ref.IsValid():
            _append_marker("WARNING: Cannot lift robot; prims invalid")
            return

        bbox_cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            includedPurposes=[UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
            useExtentsHint=True,
        )
        box = bbox_cache.ComputeWorldBound(robot_ref).ComputeAlignedBox()
        mn = box.GetMin()

        desired_min_z = floor_z + clearance
        if mn[2] >= desired_min_z:
            _append_marker(f"Robot already above floor: minZ={mn[2]:.3f}")
            return

        dz = float(desired_min_z - mn[2])
        xfc = UsdGeom.XformCommonAPI(robot_root)

        # Different Kit/PXR builds expose different accessors; GetXformVectors is the most stable.
        try:
            t, _r, _s, _p, _ro = xfc.GetXformVectors(Usd.TimeCode.Default())
            cur = Gf.Vec3d(float(t[0]), float(t[1]), float(t[2]))
        except Exception:
            cur = Gf.Vec3d(0.0, 0.0, 0.0)
        new_t = Gf.Vec3d(cur[0], cur[1], cur[2] + dz)
        xfc.SetTranslate(new_t)
        _append_marker(f"Lifted robot by dz={dz:.3f} to translate={tuple(new_t)}")
    except Exception as exc:
        _append_marker(f"WARNING: Could not lift robot above floor: {exc!r}")


def _stabilize_robot_for_demo(stage) -> None:
    """Make the robot stable for the scripted demo.

    The vendor USD often contains full rigid-body articulation. When we translate the
    robot root for a visual "walk", physics can topple it. For this demo we pin the
    robot by making rigid bodies kinematic and (best-effort) disabling gravity.
    """
    try:
        from pxr import Sdf, Usd, UsdPhysics

        robot_prim = stage.GetPrimAtPath(ROBOT_REF_PRIM_PATH)
        if not robot_prim.IsValid():
            _append_marker("WARNING: Robot prim not valid; cannot stabilize")
            return

        kin_attr_name = "physics:kinematicEnabled"
        # Common PhysX attribute name on composed prims.
        disable_gravity_attr_name = "physxRigidBody:disableGravity"

        affected = 0
        for p in Usd.PrimRange(robot_prim, Usd.TraverseInstanceProxies()):
            try:
                # Only touch prims that already participate in physics.
                has_rb = p.HasAPI(UsdPhysics.RigidBodyAPI)
                if not has_rb:
                    continue

                # Kinematic enabled (USD Physics).
                a = p.GetAttribute(kin_attr_name)
                if not a or not a.IsValid():
                    a = p.CreateAttribute(kin_attr_name, Sdf.ValueTypeNames.Bool)
                a.Set(True)

                # Disable gravity (PhysX). This attribute may not exist on all builds.
                g = p.GetAttribute(disable_gravity_attr_name)
                if g and g.IsValid():
                    g.Set(True)

                affected += 1
            except Exception:
                continue

        _append_marker(f"Stabilized robot for demo: set kinematic on {affected} rigid bodies")
    except Exception as exc:
        _append_marker(f"WARNING: Could not stabilize robot physics: {exc!r}")


def _setup_view_helpers(stage, robot_spawn=(1.2, 0.0, 0.02)) -> None:
    """Create a safe camera + a stable frame target near the robot."""
    from pxr import Gf, Sdf, UsdGeom

    # A stable target prim you can select and press F.
    try:
        cube = UsdGeom.Cube.Define(stage, Sdf.Path(FRAME_TARGET_PRIM_PATH))
        cube.CreateSizeAttr(1.0)
        xf = UsdGeom.XformCommonAPI(cube)
        xf.SetScale(Gf.Vec3f(0.25, 0.25, 0.25))
        xf.SetTranslate(Gf.Vec3d(robot_spawn[0], robot_spawn[1], robot_spawn[2] + 1.2))
        cube.CreateDisplayColorAttr([(1.0, 0.0, 0.0)])
        _append_marker(f"Created frame target prim: {FRAME_TARGET_PRIM_PATH}")
    except Exception as exc:
        _append_marker(f"WARNING: Could not create frame target prim: {exc!r}")

    # A safe camera that looks roughly at the robot spawn area.
    try:
        cam = UsdGeom.Camera.Define(stage, Sdf.Path(SAFE_CAMERA_PRIM_PATH))
        cam_xf = UsdGeom.Xformable(cam.GetPrim())
        cam_xf.ClearXformOpOrder()
        cam_xf.AddTranslateOp().Set(Gf.Vec3d(robot_spawn[0] + 4.0, robot_spawn[1] - 4.0, robot_spawn[2] + 2.2))
        cam_xf.AddRotateXYZOp().Set(Gf.Vec3f(15.0, 0.0, 45.0))
        cam.CreateClippingRangeAttr().Set(Gf.Vec2f(0.01, 100000.0))
        _append_marker(f"Created safe camera: {SAFE_CAMERA_PRIM_PATH}")

        try:
            import importlib

            kit_commands = importlib.import_module("omni.kit.commands")
            for cmd_name in ("SetViewportCamera", "ChangeViewportCamera"):
                try:
                    kit_commands.execute(cmd_name, camera_path=SAFE_CAMERA_PRIM_PATH)
                    _append_marker(f"Activated safe camera via {cmd_name}")
                    break
                except Exception:
                    continue
        except Exception as exc:
            _append_marker(f"NOTE: Could not auto-activate safe camera: {exc!r}")
    except Exception as exc:
        _append_marker(f"WARNING: Could not create safe camera: {exc!r}")


async def _frame_robot_best_effort(retries: int = 20, delay_s: float = 0.5) -> None:
    """Try to frame the robot in the viewport (best-effort; varies by Kit version)."""
    try:
        import importlib

        kit_commands = importlib.import_module("omni.kit.commands")
    except Exception:
        return

    for _ in range(retries):
        try:
            kwargs = {"prim_paths": [ROBOT_PRIM_PATH]}
            for key in ("prim_paths", "primPaths"):
                try:
                    kit_commands.execute("FramePrimsCommand", **{key: [ROBOT_PRIM_PATH]})
                    _append_marker("Viewport framed on robot")
                    return
                except Exception:
                    continue
        except Exception:
            pass
        await asyncio.sleep(delay_s)

    _append_marker("WARNING: Could not frame robot in viewport")


async def _walk_robot_root(stage, start_xyz: tuple[float, float, float], end_xyz: tuple[float, float, float], duration_s: float = 6.0) -> None:
    """Best-effort 'walk' by translating the robot root over time.

    This is not real locomotion; it's a visual demo that the robot approaches the table.
    """
    from pxr import Gf, UsdGeom

    prim = stage.GetPrimAtPath(ROBOT_PRIM_PATH)
    if not prim.IsValid():
        _append_marker("WARNING: Robot prim not valid; cannot animate approach")
        return

    xfc = UsdGeom.XformCommonAPI(prim)

    steps = max(10, int(duration_s * 20.0))
    for i in range(steps + 1):
        t = i / float(steps)
        x = start_xyz[0] + (end_xyz[0] - start_xyz[0]) * t
        y = start_xyz[1] + (end_xyz[1] - start_xyz[1]) * t
        z = start_xyz[2] + (end_xyz[2] - start_xyz[2]) * t
        xfc.SetTranslate(Gf.Vec3d(x, y, z))
        await asyncio.sleep(duration_s / float(steps))

    _append_marker(f"Robot root moved to {end_xyz}")


async def _pickup_apple_animated(stage, duration_s: float = 1.5) -> None:
    """Pick animation: reach down first, then attach and lift.

    This avoids the "apple teleports upward" look by keeping the table apple still
    until a "contact" moment. Best-effort, we author a temporary translate op on a
    discovered wrist/hand prim to make the hand visually move down/up. If that
    fails, we fall back to moving a visible marker Xform (HandHold).
    """
    from pxr import Gf, Sdf, Usd, UsdGeom

    robot_root = stage.GetPrimAtPath(ROBOT_PRIM_PATH)
    if not robot_root.IsValid():
        _append_marker("WARNING: Robot prim not valid; cannot pick")
        return

    src = stage.GetPrimAtPath(APPLE_PRIM_PATH)
    if not src.IsValid():
        _append_marker("WARNING: Apple prim not valid; cannot pick")
        return

    # Read current world positions.
    try:
        robot_xfc = UsdGeom.XformCommonAPI(robot_root)
        rt, _rr, _rs, _rp, _rro = robot_xfc.GetXformVectors(Usd.TimeCode.Default())
        robot_world = Gf.Vec3d(float(rt[0]), float(rt[1]), float(rt[2]))
    except Exception:
        robot_world = Gf.Vec3d(0.0, 0.0, 0.0)

    try:
        apple_xfc = UsdGeom.XformCommonAPI(src)
        at, _ar, _as, _ap, _aro = apple_xfc.GetXformVectors(Usd.TimeCode.Default())
        apple_world = Gf.Vec3d(float(at[0]), float(at[1]), float(at[2]))
    except Exception:
        # If we can't read it, just bail rather than doing something surprising.
        _append_marker("WARNING: Could not read apple transform; cannot pick")
        return

    _append_marker(f"Pick animation start (duration={duration_s}s)")

    # Ensure the hold Xform exists.
    if not stage.GetPrimAtPath(HELD_ROOT).IsValid():
        UsdGeom.Xform.Define(stage, Sdf.Path(HELD_ROOT))

    hold_prim = stage.GetPrimAtPath(HELD_ROOT)
    hold_xf = UsdGeom.XformCommonAPI(hold_prim)

    def _find_best_hand_target() -> tuple[str, Gf.Vec3d] | None:
        """Best-effort: locate a right hand/wrist prim and return (primPath, worldPos)."""
        try:
            robot_ref = stage.GetPrimAtPath(ROBOT_REF_PRIM_PATH)
            if not robot_ref.IsValid():
                return None

            # Name-based hints (vendor assets vary a lot).
            patterns = [
                re.compile(r"(?i)(right|r)[_\- ]*(hand|wrist)$"),
                re.compile(r"(?i)(hand|wrist)[_\- ]*(right|r)$"),
                re.compile(r"(?i)r(hand|wrist)$"),
                re.compile(r"(?i)(right).*?(hand|wrist)"),
                re.compile(r"(?i)(hand|wrist).*?(right)"),
            ]

            cache = UsdGeom.XformCache(Usd.TimeCode.Default())

            candidates: list[tuple[int, float, str, Gf.Vec3d]] = []
            for p in Usd.PrimRange(robot_ref, Usd.TraverseInstanceProxies()):
                name = p.GetName() or ""
                if not name:
                    continue

                score = 0
                for pat in patterns:
                    if pat.search(name):
                        score += 10
                        break
                if score == 0 and re.search(r"(?i)(hand|wrist)", name):
                    score += 2
                if score == 0:
                    continue

                try:
                    m = cache.GetLocalToWorldTransform(p)
                    t = m.ExtractTranslation()
                    pos = Gf.Vec3d(float(t[0]), float(t[1]), float(t[2]))
                except Exception:
                    continue

                # Prefer plausible hand heights.
                z = float(pos[2])
                if 0.6 <= z <= 1.8:
                    score += 3

                # Prefer being roughly near the robot (not far off in the scene).
                dist = (pos - apple_world).GetLength()
                candidates.append((score, dist, p.GetPath().pathString, pos))

            if not candidates:
                return None

            # Highest score, then closest to the apple.
            candidates.sort(key=lambda x: (-x[0], x[1]))
            best = candidates[0]
            _append_marker(f"Hand target prim: {best[2]} world={tuple(best[3])} score={best[0]} dist={best[1]:.3f}")
            return (best[2], best[3])
        except Exception:
            return None

    # Where should the "hand" be relative to the robot root?
    # Prefer an actual hand/wrist prim if we can find one.
    hand_info = _find_best_hand_target()
    if hand_info is not None:
        hand_path, hand_world = hand_info
        hand_rel = Gf.Vec3d(hand_world[0] - robot_world[0], hand_world[1] - robot_world[1], hand_world[2] - robot_world[2])
    else:
        hand_path = ""
        hand_world = None
        # Fallback: approximate humanoid right-hand.
        hand_rel = Gf.Vec3d(0.35, -0.20, 1.05)

    # Positions relative to the robot root.
    apple_rel = Gf.Vec3d(apple_world[0] - robot_world[0], apple_world[1] - robot_world[1], apple_world[2] - robot_world[2])

    # Visual marker so you can see where the "grasp point" is moving.
    # If we can identify a hand link, attach a small marker under it.
    if hand_path:
        try:
            marker_path = f"{hand_path}/GripperMarker"
            gm = UsdGeom.Cube.Define(stage, Sdf.Path(marker_path))
            gm.CreateSizeAttr(1.0)
            gm_xf = UsdGeom.XformCommonAPI(gm)
            gm_xf.SetScale(Gf.Vec3f(0.03, 0.03, 0.06))
            gm_xf.SetTranslate(Gf.Vec3d(0.0, 0.0, 0.0))
            gm.CreateDisplayColorAttr([(0.2, 0.9, 0.2)])
        except Exception:
            pass
    else:
        # Marker under our fallback HandHold xform.
        try:
            GRIPPER_MARKER_PATH = f"{HELD_ROOT}/GripperMarker"
            gm = UsdGeom.Cube.Define(stage, Sdf.Path(GRIPPER_MARKER_PATH))
            gm.CreateSizeAttr(1.0)
            gm_xf = UsdGeom.XformCommonAPI(gm)
            gm_xf.SetScale(Gf.Vec3f(0.05, 0.05, 0.10))
            gm_xf.SetTranslate(Gf.Vec3d(0.0, 0.0, 0.0))
            gm.CreateDisplayColorAttr([(0.2, 0.9, 0.2)])
        except Exception:
            pass

    # Two-stage motion to look like a grasp:
    #  1) move the hand down toward the apple (apple stays put)
    #  2) at contact, hide table apple and spawn a held apple under the hand
    #  3) lift the hand back up carrying the held apple

    def _ease(t: float) -> float:
        # Smoothstep-ish.
        return t * t * (3.0 - 2.0 * t)

    reach_s = max(0.8, duration_s * 0.55)
    lift_s = max(0.7, duration_s * 0.45)

    # Prefer moving the actual discovered hand link (visual reach) by authoring a local translate op.
    use_hand_link_reach = False
    hand_reach_op = None
    reach_offset = None
    if hand_path and hand_world is not None:
        try:
            # Compute a conservative reach offset primarily in Z (down/up in world).
            dz = float(apple_world[2] - hand_world[2])
            dz = max(-0.25, min(0.0, dz))  # only move down, clamp magnitude
            reach_offset = Gf.Vec3d(0.0, 0.0, dz)

            hand_over = stage.OverridePrim(hand_path)
            xformable = UsdGeom.Xformable(hand_over)
            # Add or find a uniquely-named translate op so we don't fight the robot's authored ops.
            existing = None
            for op in xformable.GetOrderedXformOps():
                try:
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate and op.GetName() == "xformOp:translate:reach":
                        existing = op
                        break
                except Exception:
                    continue

            if existing is None:
                hand_reach_op = xformable.AddTranslateOp(
                    opSuffix="reach",
                    precision=UsdGeom.XformOp.PrecisionDouble,
                )
            else:
                hand_reach_op = existing

            hand_reach_op.Set(Gf.Vec3d(0.0, 0.0, 0.0))
            use_hand_link_reach = True
            _append_marker(f"Reach phase (hand link): offset={tuple(reach_offset)}")
        except Exception as exc:
            _append_marker(f"NOTE: Could not author reach op on hand link; falling back to marker: {exc!r}")
            use_hand_link_reach = False

    if not use_hand_link_reach:
        _append_marker(f"Reach phase (marker): apple_rel={tuple(apple_rel)} hand_rel={tuple(hand_rel)}")
        # Start with the hold at the hand (so it looks like the hand is above the apple).
        hold_xf.SetTranslate(hand_rel)

    # Reach down.
    steps1 = max(14, int(reach_s * 30.0))
    for i in range(steps1 + 1):
        t = _ease(i / float(steps1))
        if use_hand_link_reach and hand_reach_op is not None and reach_offset is not None:
            cur = Gf.Vec3d(reach_offset[0] * t, reach_offset[1] * t, reach_offset[2] * t)
            hand_reach_op.Set(cur)
        else:
            cur = Gf.Vec3d(
                hand_rel[0] + (apple_rel[0] - hand_rel[0]) * t,
                hand_rel[1] + (apple_rel[1] - hand_rel[1]) * t,
                hand_rel[2] + (apple_rel[2] - hand_rel[2]) * t,
            )
            hold_xf.SetTranslate(cur)
        await asyncio.sleep(reach_s / float(steps1))

    # Contact pause.
    await asyncio.sleep(0.25)

    # At contact: hide original apple and spawn held apple at the hand/marker origin.
    try:
        UsdGeom.Imageable(src).GetVisibilityAttr().Set("invisible")
    except Exception:
        pass

    held_path = HELD_APPLE_PRIM_PATH
    if hand_path:
        held_path = f"{hand_path}/HeldApple"
    held = UsdGeom.Sphere.Define(stage, Sdf.Path(held_path))
    held.CreateRadiusAttr(0.06)
    held.CreateDisplayColorAttr([(1.0, 0.1, 0.1)])
    UsdGeom.XformCommonAPI(held).SetTranslate(Gf.Vec3d(0.0, 0.0, 0.0))
    _append_marker(f"Contact: attached apple under {held_path}")

    # Lift back up (now the held apple moves with the hand).
    steps2 = max(12, int(lift_s * 30.0))
    for i in range(steps2 + 1):
        t = _ease(i / float(steps2))
        if use_hand_link_reach and hand_reach_op is not None and reach_offset is not None:
            # Return reach op to zero.
            cur = Gf.Vec3d(reach_offset[0] * (1.0 - t), reach_offset[1] * (1.0 - t), reach_offset[2] * (1.0 - t))
            hand_reach_op.Set(cur)
        else:
            cur = Gf.Vec3d(
                apple_rel[0] + (hand_rel[0] - apple_rel[0]) * t,
                apple_rel[1] + (hand_rel[1] - apple_rel[1]) * t,
                apple_rel[2] + (hand_rel[2] - apple_rel[2]) * t,
            )
            hold_xf.SetTranslate(cur)
        await asyncio.sleep(lift_s / float(steps2))

    _append_marker("Pick animation complete: reached down, attached, lifted")


async def _main() -> None:
    try:
        _reset_marker_log()
        _append_marker("Script started")

        await _open_warehouse_stage()

        # Resolve robot USD.
        robot_usd = _resolve_user_robot_usd() or _resolve_isaac_robot_usd()
        if not robot_usd:
            raise RuntimeError(
                "Could not resolve Unitree G1 USD. Set UNITREE_G1_USD or place assets/unitree_g1/g1.usd"
            )
        if not _path_exists(robot_usd):
            raise RuntimeError(f"Robot USD path does not exist: {robot_usd}")

        stage = omni.usd.get_context().get_stage()
        if stage is None:
            raise RuntimeError("Stage not available")

        # Table+apple first, so we can spawn robot facing it.
        table_center = (2.2, 0.0, 0.0)
        _spawn_table_and_apple(stage, table_center=table_center)

        # Start slightly above the floor; we'll adjust precisely once bounds compose.
        robot_spawn = (1.2, 0.0, 0.50)
        _spawn_marker(stage, pos=(robot_spawn[0], robot_spawn[1], robot_spawn[2] + 0.15))
        _spawn_g1(stage, robot_usd, spawn_pos=robot_spawn)

        # Allow USD composition/payloads to resolve, then lift to sit on the floor.
        await asyncio.sleep(1.0)
        _lift_robot_above_floor(stage, floor_z=0.0, clearance=0.02)

        # Now that the robot is in a sane spot, set up camera + frame helpers.
        try:
            from pxr import Usd

            xfc_now = UsdGeom.XformCommonAPI(stage.GetPrimAtPath(ROBOT_PRIM_PATH))
            t_now, _r, _s, _p, _ro = xfc_now.GetXformVectors(Usd.TimeCode.Default())
            robot_spawn_now = (float(t_now[0]), float(t_now[1]), float(t_now[2]))
        except Exception:
            robot_spawn_now = robot_spawn
        _setup_view_helpers(stage, robot_spawn=robot_spawn_now)

        # Keep physics from toppling the robot while we do the scripted motion.
        # We'll start the timeline after the pick.
        _stabilize_robot_for_demo(stage)

        # Give Kit UI a moment, then move the robot up to the table.
        await asyncio.sleep(0.5)
        await _frame_robot_best_effort()

        # Move to just in front of the table.
        # Use current translate as the start so we move even if we adjusted height.
        from pxr import Gf, Usd, UsdGeom

        xfc = UsdGeom.XformCommonAPI(stage.GetPrimAtPath(ROBOT_PRIM_PATH))
        try:
            t, _r, _s, _p, _ro = xfc.GetXformVectors(Usd.TimeCode.Default())
            cur = Gf.Vec3d(float(t[0]), float(t[1]), float(t[2]))
        except Exception:
            cur = Gf.Vec3d(robot_spawn[0], robot_spawn[1], robot_spawn[2])

        start = (float(cur[0]), float(cur[1]), float(cur[2]))
        # Get close to the table so the pick looks plausible.
        target = (table_center[0] - 0.20, table_center[1], start[2])
        await _walk_robot_root(stage, start_xyz=start, end_xyz=target, duration_s=4.0)

        # Then perform the pick (animated).
        # Brief pause at the table, then reach down + lift.
        await asyncio.sleep(1.0)
        await _pickup_apple_animated(stage, duration_s=3.2)

        # Start simulation after everything is placed.
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        _append_marker("Timeline play() called")

        _append_marker("Done")

    except Exception as exc:
        carb.log_error(f"Warehouse+Apple pick autoload failed: {exc}")
        _append_marker(f"ERROR: {exc!r}")
        _append_marker(traceback.format_exc())


asyncio.ensure_future(_main())
