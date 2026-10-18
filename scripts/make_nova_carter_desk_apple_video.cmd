@echo off
setlocal

set ISAAC_SIM_DIR=C:\isaacsim
set SCRIPT_PATH=C:\Users\ryan_\Documents\github\humanoid\scripts\nova_carter_desk_apple.py
set NOVA_CARTER_USD=C:\Users\ryan_\OneDrive\Documents\isaac_world\nova_carter.usd
set VIDEO_OUTPUT=%~dp0..\docs\output\nova_carter_desk_apple.mp4
set AUTO_EXIT=1

cd /d "%ISAAC_SIM_DIR%"
call "%ISAAC_SIM_DIR%\kit\kit.exe" "%ISAAC_SIM_DIR%\apps\isaacsim.exp.full.kit" --/renderer/graphicsApi=Direct3D12 --/app/renderer/activeRenderer=HydraStorm --/renderer/forceRayTracing=0 --exec "%SCRIPT_PATH%"

endlocal
