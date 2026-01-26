# Windows Isaac Sim + WSL Ubuntu 24.04 ROS 2 (fastest reliable path)

You have WSL2 Ubuntu 24.04 available:

```powershell
wsl -l -v
```

This guide sets up **ROS 2 in WSL** and runs **Isaac Sim on Windows**. This is typically far more reliable than trying to run Isaac Sim inside WSL.

Important: many Windows-based Isaac Sim / Isaac ROS tutorials assume **ROS 2 Humble on Ubuntu 22.04**. If you follow a Humble tutorial while running **Jazzy on Ubuntu 24.04**, you can hit compatibility and discovery issues.

For cross-machine discovery and ROS graph visibility, the most reliable setup is: **Windows Isaac Sim bridge distro matches your WSL distro** (Jazzy↔Jazzy). Isaac Sim ships bridge libraries for multiple distros.

## 1) Start WSL Ubuntu

From PowerShell:

```powershell
wsl -d Ubuntu-24.04
```

## 2) (Recommended) Enable mirrored networking (helps ROS 2 discovery)

On Windows, edit `%UserProfile%\\.wslconfig` and add:

```
[wsl2]
networkingMode=mirrored
```

Then restart WSL:

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

## 3) Install ROS 2 Jazzy in WSL (Ubuntu 24.04)

Inside WSL:

```bash
# If /mnt/c doesn't exist in your WSL, first check mounts:
ls /mnt

# Typical path to this repo from WSL:
cd /mnt/c/Users/ryan_/Documents/github/ros2_ws

bash setup_wsl/chmod_all.sh

# If apt is currently broken with a PGP key block error, repair it first:
bash setup_wsl/05_repair_apt_sources.sh

bash setup_wsl/10_install_ros2_jazzy.sh
```

Open a new WSL shell and verify:

```bash
bash setup_wsl/30_ros2_sanity_check.sh
```

## 4) Install Docker (optional)

If you want containers, the easiest Windows+WSL setup is:

- Install **Docker Desktop** on Windows
- Settings → Resources → WSL Integration → enable for `Ubuntu-24.04`

Then inside WSL:

```bash
docker version
```

(You usually do *not* want to install the Docker daemon inside WSL if you already have Docker Desktop.)

## 5) Run Isaac Sim on Windows

Install Isaac Sim on Windows (NVIDIA/Omniverse method).

Recommended: launch Isaac Sim from PowerShell so it definitely inherits the DDS env vars. See:

- setup_windows/RUN_WINDOWS_POWERSHELL.md

If the ROS 2 bridge fails to start on Windows with an error like `rmw_fastrtps_cpp.dll` / `LoadLibrary error 126`, use the provided launcher:

```powershell
cd C:\Users\ryan_\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\launch_isaac_sim_with_ros2.ps1
```

That script sets ROS/DDS env vars **and** prepends Isaac Sim’s shipped ROS2 bridge DLL directory to `PATH` so the bridge can load.

### One-command launcher (recommended)

You can also use the orchestration helper that (optionally) starts the WSL discovery server + your WSL stack, then launches Isaac Sim detached:

```powershell
cd C:\Users\ryan_\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\start_everything.ps1
```

Useful switches:

- `-SkipDiscoveryServer` / `-SkipDiffDriveStack` / `-SkipIsaacSim`
- `-NoRviz`
- `-FixBlackViewport` (forces renderer present on)
- `-ResetKitUserConfig` (backs up and resets `user.config.json` to clear broken layouts/settings)
- `-OpenRoboticsExamples` (auto-opens the **Robotics Examples** browser window at startup)
- `-EnsureFirewallRules` (prompts for UAC and installs Windows Firewall UDP allow rules for `kit.exe`, plus DDS UDP port-range rules as a fallback)

If you are using ROS 2 Jazzy in WSL (Ubuntu 24.04), launch Isaac Sim with its bridge set to Jazzy as well:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows\start_everything.ps1 -IsaacAppKit isaacsim.exp.full.kit -IsaacRosDistro jazzy
```

If `ros2 node list` stays empty in WSL, a common root cause is: **the ROS 2 bridge extension is not enabled**.

- In Isaac Sim UI: Window → Extensions → search `ros2` → enable `isaacsim.ros2.bridge` (and/or `omni.isaac.ros2_bridge`) → restart Isaac Sim.
- Or launch via the PowerShell helper (it auto-enables the bridge by default).

## 6) Make ROS 2 talk between Windows and WSL

### Option A (try first): mirrored networking + same `ROS_DOMAIN_ID`

In *both* Windows (where Isaac Sim runs) and WSL (where ROS2 runs), set:

- `ROS_DOMAIN_ID` to the same value (e.g., `0`)

In WSL:

```bash
export ROS_DOMAIN_ID=0
```

Also force Fast DDS to use UDP-only to avoid shared-memory transport issues across WSL:

```bash
bash setup_wsl/50_fastdds_udp_only.sh
```

On Windows (Environment Variables), add a **User variable**:

- `FASTDDS_BUILTIN_TRANSPORTS` = `UDPv4`

### Option B (if discovery is flaky): use a Discovery Server (Fast DDS)

If topics don’t show up across Windows↔WSL, tell me and I’ll generate an exact FastDDS Discovery Server config for your ROS 2 RMW.

Quick start (WSL runs the server):

```bash
bash setup_wsl/70_run_fastdds_discovery_server.sh
```

Then set a Windows **User variable** and a WSL env var to the same value:

- `ROS_DISCOVERY_SERVER` = `<server_ip>:11812`

Restart Isaac Sim after changing Windows env vars.

### If WSL still doesn’t see Isaac topics: allow UDP for kit.exe

If `ros2 topic list -t` in WSL only shows `/rosout` and `/parameter_events` while Isaac’s ROS2 bridge is running, the most common cause is **Windows Firewall blocking inbound UDP replies** from WSL.

Run this once from an **elevated PowerShell** (Run as Administrator):

```powershell
cd C:\Users\ryan_\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\add_firewall_rules_for_isaacsim_ros2.ps1 -IsaacRoot C:\isaacsim
```

If that still doesn’t help on a locked-down machine, also allow the default DDS/RTPS port range (more general, but effective for troubleshooting):

```powershell
cd C:\Users\ryan_\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\add_firewall_rules_for_dds_ports.ps1
```

## 7) Quick sanity check

In WSL:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
```

When Isaac Sim + ROS2 bridge are running, you should see topics.

Important: the ROS2 bridge starting successfully does *not* automatically mean topics will appear. In Isaac Sim, topics typically only exist after you load a USD stage (or an OmniGraph) that contains ROS2 publishers/subscribers.

### Quick validation: load a shipped ROS2 sample scene

1) In Isaac Sim, open the **Robotics Examples** browser.
	- Menu path: **Window → Examples → Robotics Examples**
	- If you can’t find it, launch with `-OpenRoboticsExamples` to show it on startup.
2) Navigate to **ROS2/Navigation** and pick a sample (e.g., **Nova Carter**).
3) Click **Load Sample Scene**.
4) Press **Play** in the timeline (some graphs only publish while sim is running).

Then in WSL:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export ROS_DISCOVERY_SERVER=192.168.1.200:11812

ros2 daemon stop || true
ros2 daemon start

ros2 node list
ros2 topic list
```

If you still only see `/rosout` and `/parameter_events`, the bridge may be up but the loaded scene hasn’t created any ROS2 publishers yet (or discovery between Windows↔WSL is still blocked).

---

## Humble path (matches most tutorials)

Install a separate WSL distro:

```powershell
wsl --install -d Ubuntu-22.04
```

Then inside the Ubuntu-22.04 WSL shell:

```bash
cd /mnt/c/Users/ryan_/Documents/github/ros2_ws
bash setup_wsl_2204/chmod_all.sh
bash setup_wsl_2204/10_install_ros2_humble.sh
bash setup_wsl_2204/30_ros2_sanity_check.sh
```

Use the same env vars as above (`ROS_DOMAIN_ID`, `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`, and optionally `ROS_DISCOVERY_SERVER`).

---

If you want, I can also add scripts to run your ROS 2 stack from WSL and set recommended DDS env vars.
