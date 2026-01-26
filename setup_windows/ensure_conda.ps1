param(
  # Conda environment name to activate in the current PowerShell session.
  [string]$EnvName = "base",

  # Only loads Conda's PowerShell hook (makes `conda` available) without activating an env.
  [switch]$HookOnly
)

$ErrorActionPreference = "Stop"

function Resolve-CondaExe {
  $candidates = @()

  if ($env:CONDA_EXE -and (Test-Path $env:CONDA_EXE)) {
    $candidates += $env:CONDA_EXE
  }

  $user = $env:USERPROFILE
  $programData = $env:ProgramData
  $localAppData = $env:LOCALAPPDATA

  $candidates += @(
    (Join-Path $user "anaconda3\Scripts\conda.exe")
    (Join-Path $user "Anaconda3\Scripts\conda.exe")
    (Join-Path $user "miniconda3\Scripts\conda.exe")
    (Join-Path $localAppData "Programs\anaconda3\Scripts\conda.exe")
    (Join-Path $localAppData "Programs\Anaconda3\Scripts\conda.exe")
    (Join-Path $localAppData "Programs\miniconda3\Scripts\conda.exe")
    (Join-Path $localAppData "Continuum\anaconda3\Scripts\conda.exe")
    (Join-Path $programData "anaconda3\Scripts\conda.exe")
    (Join-Path $programData "Anaconda3\Scripts\conda.exe")
    (Join-Path $programData "miniconda3\Scripts\conda.exe")
  )

  foreach ($path in $candidates) {
    if ($path -and (Test-Path $path)) {
      return $path
    }
  }

  return ""
}

function Enable-CondaInThisSession {
  if (Get-Command conda -ErrorAction SilentlyContinue) {
    return
  }

  $condaExe = Resolve-CondaExe
  if (-not $condaExe) {
    throw @(
      "Conda isn't available in this PowerShell session, and conda.exe wasn't found in common Anaconda locations.",
      "\n\nFix options:",
      "  1) Open 'Anaconda Prompt' and run: conda init powershell",
      "  2) Restart VS Code, then try again.",
      "\nIf Anaconda is installed somewhere non-standard, set CONDA_EXE to its conda.exe path before running this script."
    ) -join "\n"
  }

  # Load Conda's PowerShell function into the current session.
  & $condaExe shell.powershell hook | Out-String | Invoke-Expression

  if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda hook executed, but `conda` is still not available in this session. Try running: conda init powershell (from Anaconda Prompt), then restart VS Code."
  }
}

Enable-CondaInThisSession

if (-not $HookOnly) {
  Write-Host "Activating conda env: $EnvName" -ForegroundColor Cyan
  conda activate $EnvName
}
