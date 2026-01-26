import asyncio
import os
from pathlib import Path
from datetime import datetime

import carb
import omni.timeline
import omni.usd


# Tries a few likely USD locations under the Isaac Sim assets root.
# The exact path varies by Isaac Sim version / asset pack.
ROBOT_USD_CANDIDATES_REL = [
    "/Isaac/Robots/Unitree/G1/g1.usd",
    "/Isaac/Robots/Unitree/G1/unitree_g1.usd",
    "/Isaac/Robots/Unitree/UnitreeG1/g1.usd",
    "/Isaac/Robots/Unitree/UnitreeG1/unitree_g1.usd",
]

# Optional: load a warehouse stage first, then spawn the robot into it.
# If you want a specific stage, set UNITREE_STAGE_USD to a local path or omniverse:// url.
STAGE_USD_CANDIDATES_REL = [
    "/Isaac/Environments/Simple_Warehouse/warehouse.usd",
    "/Isaac/Environments/Simple_Warehouse/simple_warehouse.usd",
    "/Isaac/Environments/Warehouse/warehouse.usd",
    "/Isaac/Environments/Warehouse/warehouse_with_forklifts.usd",
]

# Kitchen-like environments (varies by asset pack / Isaac version).
KITCHEN_STAGE_USD_CANDIDATES_REL = [
    "/Isaac/Environments/Kitchen/kitchen.usd",
    "/Isaac/Environments/Kitchen/chef_kitchen.usd",
    "/Isaac/Environments/Simple_Kitchen/kitchen.usd",
    "/Isaac/Environments/Simple_Kitchen/simple_kitchen.usd",
    "/Isaac/Environments/Office_Kitchen/office_kitchen.usd",
]

ROBOT_PRIM_PATH = "/World/UnitreeG1"
FRAME_TARGET_PRIM_PATH = "/World/UnitreeG1_FrameTarget"
SAFE_CAMERA_PRIM_PATH = "/World/UnitreeG1_SafeCamera"


def _discover_robot_asset_root(robot_usd_path: str) -> str | None:
    """Return a prim path inside the robot USD that should be referenced.

    Some vendor USDs ship without a defaultPrim. In that case, adding a
    reference without specifying a prim path can yield an "empty" reference.
    """
    try:
        from pxr import Usd

        asset_stage = Usd.Stage.Open(robot_usd_path)
        if asset_stage is None:
            _append_marker("WARNING: Could not open robot USD for inspection")
            return None

        dp = asset_stage.GetDefaultPrim()
        if dp and dp.IsValid():
            p = dp.GetPath().pathString
            _append_marker(f"Robot asset defaultPrim: {p}")
            return p

        # Fallback: first root prim under pseudo-root.
        roots = [p for p in asset_stage.GetPseudoRoot().GetChildren() if p.IsValid()]
        if not roots:
            _append_marker("WARNING: Robot USD has no root prim children")
            return None

        p = roots[0].GetPath().pathString
        _append_marker(f"Robot asset root prim (fallback): {p}")
        return p
    except Exception as exc:
        _append_marker(f"WARNING: Could not inspect robot USD: {exc!r}")
        return None


def _append_marker(message: str) -> None:
    try:
        marker_path = os.path.join(os.path.dirname(__file__), "auto_load_unitree_g1.status.txt")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(marker_path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        # Intentionally swallow to avoid breaking startup.
        pass


def _omniverse_path_exists(path: str) -> bool:
    # Isaac assets root is typically an omniverse:// URL; use omni.client to stat.
    try:
        import omni.client

        result, _entry = omni.client.stat(path)
        return result == omni.client.Result.OK
    except Exception:
        return False


def _try_discover_environment_usd(assets_root: str, keyword: str) -> str | None:
    """Best-effort discovery of an environment USD by keyword.

    This is used when we don't know the exact environment path for a given Isaac
    asset pack/version. It lists the top-level Environments folder and then
    looks inside folders whose names contain the keyword.

    Returns a fully-qualified URL/path to a .usd if found, else None.
    """
    try:
        import omni.client

        env_root = assets_root + "/Isaac/Environments"
        result, entries = omni.client.list(env_root)
        if result != omni.client.Result.OK:
            return None

        keyword_lower = keyword.lower()

        # Prefer directories with keyword in the name.
        candidate_dirs = [
            e
            for e in entries
            if getattr(e, "is_folder", False)
            and keyword_lower in getattr(e, "relative_path", "").lower()
        ]

        for d in candidate_dirs:
            dir_url = env_root + "/" + d.relative_path.strip("/")
            r2, inner = omni.client.list(dir_url)
            if r2 != omni.client.Result.OK:
                continue

            # Pick the first USD-like file.
            for e in inner:
                if getattr(e, "is_folder", False):
                    continue
                name = getattr(e, "relative_path", "")
                if name.lower().endswith(".usd"):
                    return dir_url + "/" + name.strip("/")

        return None
    except Exception:
        return None


def _resolve_user_robot_usd() -> str | None:
    # Highest priority: explicit override.
    override = os.environ.get("UNITREE_G1_USD", "").strip()
    if override:
        return override

    # Next: repo-local drop-in location (kept out of git).
    # Example: <repo>/assets/unitree_g1/g1.usd
    repo_root = Path(__file__).resolve().parents[1]
    local_usd = repo_root / "assets" / "unitree_g1" / "g1.usd"
    if local_usd.exists():
        return str(local_usd)

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


def _resolve_user_stage_usd() -> str | None:
    override = os.environ.get("UNITREE_STAGE_USD", "").strip()
    if override:
        return override
    return None


def _resolve_stage_preset() -> str:
    # Allows choosing a stage category without hardcoding a URL.
    # Supported values: "warehouse" (default), "kitchen".
    preset = os.environ.get("UNITREE_STAGE_PRESET", "").strip().lower()
    if preset in ("kitchen", "warehouse"):
        return preset
    return "warehouse"


def _path_exists(path: str) -> bool:
    # Supports local file paths and omniverse:// urls.
    try:
        if path.lower().startswith("omniverse://"):
            return _omniverse_path_exists(path)
        return Path(path).exists()
    except Exception:
        return False


async def _frame_robot_best_effort(retries: int = 20, delay_s: float = 0.5) -> None:
    for i in range(retries):
        try:
            import importlib

            kit_commands = importlib.import_module("omni.kit.commands")
            # The argument name for FramePrimsCommand varies by Kit version.
            # Try a small set of common variants.
            for kwargs in (
                {"prim_paths": [ROBOT_PRIM_PATH]},
                {"primPaths": [ROBOT_PRIM_PATH]},
                {"paths": [ROBOT_PRIM_PATH]},
                {"path": ROBOT_PRIM_PATH},
            ):
                try:
                    kit_commands.execute("FramePrimsCommand", **kwargs)
                    _append_marker("Viewport framed on robot")
                    return
                except TypeError:
                    continue
        except Exception as exc:
            if i == 0:
                _append_marker(f"FramePrimsCommand not ready yet: {exc!r}")
            await asyncio.sleep(delay_s)
    _append_marker("WARNING: Could not frame robot in viewport")


async def _new_stage_with_ground() -> None:
    # Create a new empty stage.
    await omni.usd.get_context().new_stage_async()


async def _open_stage(stage_path: str) -> None:
    # Load an existing stage (local file path or omniverse:// url).
    await omni.usd.get_context().open_stage_async(stage_path)
    # Give Kit a moment to finish populating the stage.
    await asyncio.sleep(0.2)


def _compute_stage_anchor() -> tuple[float, float, float]:
    """Return a reasonable (x,y,z_floor) anchor for spawning in the current stage.

    Many environment stages (including the OpenUSD Kitchen Set) are not centered
    at world origin. Spawning at (0,0,*) can put the robot far outside the
    visible area.
    """
    try:
        from pxr import Usd, UsdGeom

        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return (0.0, 0.0, 0.0)

        target_prim = stage.GetDefaultPrim()
        if not target_prim or not target_prim.IsValid():
            # Fallback: first child under pseudo-root.
            root_children = stage.GetPseudoRoot().GetChildren()
            if not root_children:
                return (0.0, 0.0, 0.0)
            target_prim = root_children[0]

        bbox_cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            includedPurposes=[UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
            useExtentsHint=True,
        )
        world_bbox = bbox_cache.ComputeWorldBound(target_prim)
        box = world_bbox.ComputeAlignedBox()
        mn = box.GetMin()
        mx = box.GetMax()

        cx = float((mn[0] + mx[0]) * 0.5)
        cy = float((mn[1] + mx[1]) * 0.5)
        zf = float(mn[2])

        _append_marker(
            f"Stage anchor from bounds: center={cx:.3f},{cy:.3f} floor_z={zf:.3f}"
        )
        return (cx, cy, zf)
    except Exception as exc:
        _append_marker(f"WARNING: Could not compute stage anchor: {exc!r}")
        return (0.0, 0.0, 0.0)


async def _spawn_robot(robot_usd_path: str, anchor_xyz: tuple[float, float, float]) -> None:
    # Avoid omni.isaac.core utilities here since they're deprecated in newer Isaac.
    # Use raw USD APIs to create an Xform and add a reference.
    from pxr import Gf, Usd, UsdGeom

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("USD stage is not available")

    ax, ay, az_floor = anchor_xyz
    xform = UsdGeom.Xform.Define(stage, ROBOT_PRIM_PATH)
    # Spawn near the environment center, slightly above the environment floor.
    xform.AddTranslateOp().Set(Gf.Vec3d(ax, ay, az_floor + 0.80))
    xform_prim = xform.GetPrim()

    # Reference the robot USD. If the asset lacks a defaultPrim, reference a
    # specific root prim path inside the asset.
    asset_root = _discover_robot_asset_root(robot_usd_path)
    try:
        if asset_root:
            try:
                xform_prim.GetReferences().AddReference(robot_usd_path, primPath=asset_root)
            except TypeError:
                xform_prim.GetReferences().AddReference(robot_usd_path, asset_root)
            _append_marker(f"Added robot reference with primPath={asset_root}")
        else:
            xform_prim.GetReferences().AddReference(robot_usd_path)
            _append_marker("Added robot reference (no primPath)")
    except Exception as exc:
        _append_marker(f"ERROR: Failed to add robot reference: {exc!r}")
        raise

    # Some assets use payloads; ensure they're loaded so geometry appears.
    try:
        xform_prim.Load()
        _append_marker("Requested payload load on /World/UnitreeG1")
    except Exception as exc:
        _append_marker(f"NOTE: Could not call Load() on robot prim: {exc!r}")

    # Give USD a moment to compose referenced layers/payloads (especially when
    # the referenced asset is remote and needs fetching).
    await asyncio.sleep(0.5)
    # Many complex robot assets can report pathological bounds (very large or
    # otherwise invalid), which makes "Frame Selection" (F) move the camera to
    # a nonsense pose and the viewport appears black. Provide a conservative
    # extents hint on the root prim to keep framing stable.
    try:
        model_api = UsdGeom.ModelAPI.Apply(xform_prim)
        # Approximate humanoid bounds in meters, centered around the root.
        model_api.SetExtentsHint(
            [Gf.Vec3f(-1.0, -1.0, 0.0), Gf.Vec3f(1.0, 1.0, 2.2)]
        )
        _append_marker("Applied extentsHint on /World/UnitreeG1")
    except Exception as exc:
        _append_marker(f"WARNING: Could not apply extentsHint: {exc!r}")

    # Create a small, stable prim near the robot that you can safely frame.
    # If framing the robot root still causes a black viewport, select this prim
    # instead and press F.
    try:
        cube = UsdGeom.Cube.Define(stage, FRAME_TARGET_PRIM_PATH)
        cube_xf = UsdGeom.Xformable(cube.GetPrim())
        cube_xf.ClearXformOpOrder()
        cube_xf.AddTranslateOp().Set(Gf.Vec3d(ax, ay, az_floor + 1.20))
        cube_xf.AddScaleOp().Set(Gf.Vec3f(1.0, 1.0, 1.0))
        try:
            # Bright red debug color.
            cube.CreateDisplayColorAttr().Set([Gf.Vec3f(1.0, 0.0, 0.0)])
        except Exception:
            pass
        _append_marker(f"Created frame target prim: {FRAME_TARGET_PRIM_PATH}")
    except Exception as exc:
        _append_marker(f"WARNING: Could not create frame target prim: {exc!r}")

    # Best-effort: create a safe camera with wide clip range that looks at the
    # scene origin. Even if we can't auto-activate it, it will be available in
    # the stage camera list.
    try:
        cam = UsdGeom.Camera.Define(stage, SAFE_CAMERA_PRIM_PATH)
        cam_xf = UsdGeom.Xformable(cam.GetPrim())
        cam_xf.ClearXformOpOrder()
        cam_xf.AddTranslateOp().Set(Gf.Vec3d(ax + 4.0, ay - 4.0, az_floor + 2.2))
        cam_xf.AddRotateXYZOp().Set(Gf.Vec3f(15.0, 0.0, 45.0))
        cam.CreateClippingRangeAttr().Set(Gf.Vec2f(0.01, 100000.0))
        _append_marker(f"Created safe camera: {SAFE_CAMERA_PRIM_PATH}")

        # Best-effort: make this camera active in the main viewport.
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

    # Log computed bounds for debugging (helps explain framing issues).
    try:
        bbox_cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            includedPurposes=[UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
            useExtentsHint=True,
        )
        world_bbox = bbox_cache.ComputeWorldBound(xform_prim)
        box = world_bbox.ComputeAlignedBox()
        mn = box.GetMin()
        mx = box.GetMax()
        _append_marker(
            f"UnitreeG1 bounds min={mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f} max={mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f}"
        )
    except Exception as exc:
        _append_marker(f"WARNING: Could not compute bounds: {exc!r}")

    # Diagnostics: confirm we actually got renderable prims.
    try:
        mesh_count = 0
        gprim_count = 0
        imageable_count = 0
        point_instancer_count = 0
        type_hist: dict[str, int] = {}
        for p in Usd.PrimRange(xform_prim, Usd.TraverseInstanceProxies()):
            if p.IsA(UsdGeom.Mesh):
                mesh_count += 1
            if p.IsA(UsdGeom.Gprim):
                gprim_count += 1
            if p.IsA(UsdGeom.Imageable):
                imageable_count += 1
            if p.IsA(UsdGeom.PointInstancer):
                point_instancer_count += 1

            tn = p.GetTypeName() or "(empty)"
            type_hist[tn] = type_hist.get(tn, 0) + 1

        top_types = sorted(type_hist.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        top_types_str = ", ".join([f"{k}={v}" for k, v in top_types])
        _append_marker(
            f"Robot prim descendants: imageables={imageable_count} gprims={gprim_count} meshes={mesh_count} pointInstancers={point_instancer_count}"
        )
        _append_marker(f"Robot prim type histogram (top): {top_types_str}")
        if mesh_count == 0 and gprim_count == 0 and point_instancer_count == 0:
            _append_marker("WARNING: Robot reference appears empty (no Gprims/Meshes)")
    except Exception as exc:
        _append_marker(f"WARNING: Could not count robot prims: {exc!r}")

    # If the vendor USD has no visuals, try Isaac Sim's built-in Unitree G1.
    try:
        if mesh_count == 0 and gprim_count == 0 and point_instancer_count == 0:
            isaac_usd = _resolve_isaac_robot_usd()
            if isaac_usd and isaac_usd != robot_usd_path:
                _append_marker(f"Attempting fallback to Isaac Unitree G1 USD: {isaac_usd}")
                try:
                    xform_prim.GetReferences().ClearReferences()
                except Exception:
                    # Some Kit builds may not expose ClearReferences; ignore.
                    pass

                asset_root2 = _discover_robot_asset_root(isaac_usd)
                if asset_root2:
                    try:
                        xform_prim.GetReferences().AddReference(isaac_usd, primPath=asset_root2)
                    except TypeError:
                        xform_prim.GetReferences().AddReference(isaac_usd, asset_root2)
                    _append_marker(f"Added Isaac robot reference with primPath={asset_root2}")
                else:
                    xform_prim.GetReferences().AddReference(isaac_usd)
                    _append_marker("Added Isaac robot reference (no primPath)")

                try:
                    xform_prim.Load()
                except Exception:
                    pass

                # Wait/retry for remote assets + payloads to compose.
                mesh2 = 0
                gprim2 = 0
                pi2 = 0
                for _ in range(12):
                    mesh2 = 0
                    gprim2 = 0
                    pi2 = 0
                    for p in Usd.PrimRange(xform_prim, Usd.TraverseInstanceProxies()):
                        if p.IsA(UsdGeom.Mesh):
                            mesh2 += 1
                        if p.IsA(UsdGeom.Gprim):
                            gprim2 += 1
                        if p.IsA(UsdGeom.PointInstancer):
                            pi2 += 1
                    if mesh2 > 0 or gprim2 > 0 or pi2 > 0:
                        break
                    await asyncio.sleep(0.5)

                _append_marker(f"Fallback robot prim descendants: gprims={gprim2} meshes={mesh2} pointInstancers={pi2}")
            else:
                _append_marker("NOTE: No Isaac Unitree G1 USD found for fallback")
    except Exception as exc:
        _append_marker(f"WARNING: Fallback to Isaac Unitree G1 failed: {exc!r}")

    _append_marker(f"Spawned robot prim: {ROBOT_PRIM_PATH}")


async def _load_and_play() -> None:
    try:
        _append_marker("Script started")

        # Resolve G1 USD path.
        robot_usd_path = _resolve_user_robot_usd()
        if robot_usd_path:
            _append_marker(f"Robot USD (user): {robot_usd_path}")
            if not _path_exists(robot_usd_path):
                carb.log_error(f"UNITREE_G1_USD/local asset path does not exist: {robot_usd_path}")
                _append_marker("ERROR: User-provided robot USD path missing")
                return
        else:
            from isaacsim.storage.native import get_assets_root_path

            assets_root = get_assets_root_path()
            if not assets_root:
                carb.log_error("Could not resolve Isaac Sim assets root path")
                _append_marker("ERROR: get_assets_root_path() returned empty")
                return

            _append_marker(f"Assets root: {assets_root}")

            for rel in ROBOT_USD_CANDIDATES_REL:
                candidate = assets_root + rel
                if _omniverse_path_exists(candidate):
                    robot_usd_path = candidate
                    break

        if not robot_usd_path:
            carb.log_error(
                "Unitree G1 USD not found under assets root. Tried:\n"
                + "\n".join(["<assets_root>" + r for r in ROBOT_USD_CANDIDATES_REL])
                + "\n\nTip: set UNITREE_G1_USD to a local path or omniverse:// url."
            )
            _append_marker("ERROR: Unitree G1 USD not found")
            return

        _append_marker(f"Robot USD: {robot_usd_path}")
        carb.log_info(f"Spawning Unitree G1 from: {robot_usd_path}")

        # Load a warehouse stage if we can find one; otherwise create a new blank stage.
        stage_usd_path = _resolve_user_stage_usd()
        if stage_usd_path:
            _append_marker(f"Stage USD (user): {stage_usd_path}")
            if not _path_exists(stage_usd_path):
                carb.log_error(f"UNITREE_STAGE_USD path does not exist: {stage_usd_path}")
                _append_marker("ERROR: User-provided stage USD path missing")
                return
            await _open_stage(stage_usd_path)
        else:
            try:
                from isaacsim.storage.native import get_assets_root_path

                assets_root = get_assets_root_path()
            except Exception:
                assets_root = ""

            stage_candidate = None
            if assets_root:
                preset = _resolve_stage_preset()
                _append_marker(f"Stage preset: {preset}")

                stage_rel_candidates = (
                    KITCHEN_STAGE_USD_CANDIDATES_REL
                    if preset == "kitchen"
                    else STAGE_USD_CANDIDATES_REL
                )

                for rel in stage_rel_candidates:
                    candidate = assets_root + rel
                    if _omniverse_path_exists(candidate):
                        stage_candidate = candidate
                        break

                # If kitchen preset is requested but our known paths didn't exist,
                # try to discover a kitchen-like environment by listing Environments.
                if not stage_candidate and preset == "kitchen":
                    discovered = _try_discover_environment_usd(assets_root, keyword="kitchen")
                    if discovered:
                        _append_marker(f"Stage USD (discovered): {discovered}")
                        stage_candidate = discovered

            if stage_candidate:
                _append_marker(f"Stage USD: {stage_candidate}")
                await _open_stage(stage_candidate)
            else:
                _append_marker("Stage USD: (new empty stage)")
                await _new_stage_with_ground()

        anchor = _compute_stage_anchor()
        await _spawn_robot(robot_usd_path, anchor)
        await _frame_robot_best_effort()

        carb.log_info("Stage ready; starting simulation (timeline.play)")
        _append_marker("Stage ready")

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        _append_marker("Timeline play() called")

    except Exception as exc:
        carb.log_error(f"Auto-load Unitree G1 failed: {exc}")
        _append_marker(f"ERROR: {exc!r}")


asyncio.ensure_future(_load_and_play())
