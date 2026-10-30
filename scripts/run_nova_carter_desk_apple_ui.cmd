@echo off
setlocal

set ISAAC_SIM_DIR=C:\isaacsim
set SCRIPT_PATH=C:\Users\ryan_\Documents\github\humanoid\scripts\nova_carter_desk_apple.py
set NOVA_CARTER_USD=C:\Users\ryan_\OneDrive\Documents\isaac_world\nova_carter.usd
set AUTO_EXIT=0

cd /d "%ISAAC_SIM_DIR%"
set NOVA_CARTER_USD=%NOVA_CARTER_USD%
call "%ISAAC_SIM_DIR%\kit\kit.exe" "%ISAAC_SIM_DIR%\apps\isaacsim.exp.full.kit" --/renderer/graphicsApi=Direct3D12 --/app/renderer/activeRenderer=HydraStorm --/renderer/forceRayTracing=0 --exec "%SCRIPT_PATH%"

endlocal
