# Unitree G1 asset drop-in

Put your Unitree G1 USD here as:
- `assets/unitree_g1/g1.usd`

This repo does not ship the robot model itself (licensing varies). Obtain it from an official/licensed source and/or import it from URDF into USD using Isaac Sim.

## Option A: Use a USD you already have
- Export/copy your model to `assets/unitree_g1/g1.usd`.
- Launch Isaac Sim via `run_unitree_g1_windows.cmd`.

## Option B: Import URDF into USD (Isaac Sim)
1. Get a Unitree G1 URDF + mesh package from a legitimate source.
2. In Isaac Sim, enable the URDF Importer extension (commonly `omni.isaac.urdf`).
3. Use the URDF Importer UI to import the URDF and save/export as USD.
4. Save the resulting USD to `assets/unitree_g1/g1.usd` (or set env var `UNITREE_G1_USD` to its path).

## Override path
You can also set an environment variable:
- `UNITREE_G1_USD` = absolute local path (e.g. `C:\path\to\g1.usd`) or an `omniverse://...` url.
