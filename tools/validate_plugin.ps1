[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Plugin,

    [Parameter(Mandatory = $true)]
    [string] $Pluginval,

    [Parameter(Mandatory = $true)]
    [string] $Vst3Validator,

    [ValidateRange(1, 10)]
    [int] $Strictness = 10
)

$ErrorActionPreference = 'Stop'

function Resolve-RequiredPath([string] $Path, [string] $Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

$pluginPath = Resolve-RequiredPath $Plugin 'VST3 plug-in'
$pluginvalPath = Resolve-RequiredPath $Pluginval 'pluginval executable'
$validatorPath = Resolve-RequiredPath $Vst3Validator 'Steinberg VST3 validator executable'

Write-Host "pluginval strictness ${Strictness}: $pluginPath"
$pluginvalArguments = @(
    '--strictness-level', "$Strictness",
    '--sample-rates', '44100,48000,88200,96000,176400,192000',
    '--block-sizes', '1,2,3,7,16,31,64,127,256,511,1024',
    '--random-seed', '0x5453554b',
    '--timeout-ms', '60000',
    '--validate', "`"$pluginPath`""
)
# pluginval is a Windows GUI-subsystem executable even in headless mode.  A
# plain PowerShell invocation can return while its validation child is still
# running, producing a false green gate. Start-Process -Wait waits for the
# process tree and exposes the real exit code.
$pluginvalProcess = Start-Process -FilePath $pluginvalPath -ArgumentList $pluginvalArguments -Wait -PassThru
if ($pluginvalProcess.ExitCode -ne 0) {
    throw "pluginval failed with exit code $($pluginvalProcess.ExitCode)"
}

Write-Host "Steinberg VST3 validator: $pluginPath"
$validatorProcess = Start-Process -FilePath $validatorPath -ArgumentList @("`"$pluginPath`"") -Wait -PassThru -NoNewWindow
if ($validatorProcess.ExitCode -ne 0) {
    throw "Steinberg VST3 validator failed with exit code $($validatorProcess.ExitCode)"
}

Write-Host 'PLUGIN VALIDATION RESULT: PASS'
