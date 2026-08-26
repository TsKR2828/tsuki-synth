[CmdletBinding()]
param(
    [string] $BuildDirectory = 'build-asan',
    [string] $Configuration = 'RelWithDebInfo'
)

$ErrorActionPreference = 'Stop'
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere)) {
    throw "vswhere.exe not found: $vswhere"
}

$runtime = (& $vswhere -latest -products '*' -find '**\Hostx64\x64\clang_rt.asan_dynamic-x86_64.dll' |
    Select-Object -First 1)
if (-not $runtime) {
    throw 'MSVC x64 AddressSanitizer runtime DLL was not found'
}
$env:PATH = "$(Split-Path -Parent $runtime);$env:PATH"
Write-Host "ASan runtime: $runtime"

& ctest --test-dir $BuildDirectory -C $Configuration --output-on-failure
if ($LASTEXITCODE -ne 0) {
    throw "AddressSanitizer CTest failed with exit code $LASTEXITCODE"
}
