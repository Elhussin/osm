# Local convenience wrapper. Install PDM normally or use the isolated tool venv.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PdmArgs)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force .tools/tmp | Out-Null
    $env:TEMP = (Resolve-Path .tools/tmp).Path
    $env:TMP = $env:TEMP
    $env:PDM_CACHE_DIR = Join-Path (Resolve-Path .tools).Path 'pdm-cache'
    $env:VIRTUALENV_OVERRIDE_APP_DATA = Join-Path (Resolve-Path .tools).Path 'virtualenv'
    $env:PDM_CHECK_UPDATE = 'false'
    $pdmExecutable = Join-Path $PSScriptRoot '.tools/pdm/Scripts/pdm.exe'
    if (-not (Test-Path -LiteralPath $pdmExecutable)) {
        $pdmExecutable = (Get-Command pdm -ErrorAction Stop).Source
    }
    & $pdmExecutable @PdmArgs
    exit $LASTEXITCODE
} finally { Pop-Location }
