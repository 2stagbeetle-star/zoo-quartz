[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex', 'both')]
    [string]$Engine = 'both',

    [string]$SkillDirectory = '.claude/skills',
    [string]$LogDirectory = '_drafts/automation-logs',

    [string[]]$ExcludeSkills = @(
        'auto-run-all-prompts'
    ),

    [switch]$DryRun,
    [switch]$StopOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ToolPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ToolName,
        [string[]]$FallbackPaths = @()
    )

    $command = Get-Command $ToolName -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in $FallbackPaths) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Could not find '$ToolName'. Add it to PATH or install it first."
}

function New-CodexPrompt {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$SkillFile
    )

    $skillBody = Get-Content -LiteralPath $SkillFile.FullName -Raw

@"
Execute the following workflow exactly once in the current repository.
If a required tool, credential, or external service is missing, report the blocker and stop.

Skill name: $($SkillFile.BaseName)

Workflow instructions:
$skillBody
"@
}

function Invoke-ClaudeSkill {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ClaudeCommand,
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$SkillFile,
        [Parameter(Mandatory = $true)]
        [string]$LogRoot,
        [switch]$DryRunMode
    )

    $skillName = $SkillFile.BaseName
    $slashPrompt = "/$skillName"
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $logPath = Join-Path $LogRoot "claude-$timestamp-$skillName.log"

    if ($DryRunMode) {
        Write-Host "[dry-run][claude] $slashPrompt"
        return [pscustomobject]@{
            engine  = 'claude'
            skill   = $skillName
            status  = 'dry-run'
            log     = $logPath
            message = ''
        }
    }

    & $ClaudeCommand -p $slashPrompt 2>&1 | Tee-Object -FilePath $logPath | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Claude failed for '$slashPrompt' (exit: $exitCode)."
    }

    return [pscustomobject]@{
        engine  = 'claude'
        skill   = $skillName
        status  = 'ok'
        log     = $logPath
        message = ''
    }
}

function Invoke-CodexSkill {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CodexCommand,
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$SkillFile,
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$LogRoot,
        [switch]$DryRunMode
    )

    $skillName = $SkillFile.BaseName
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $rawLogPath = Join-Path $LogRoot "codex-$timestamp-$skillName.log"
    $lastMessagePath = Join-Path $LogRoot "codex-$timestamp-$skillName-last-message.txt"
    $prompt = New-CodexPrompt -SkillFile $SkillFile

    if ($DryRunMode) {
        Write-Host "[dry-run][codex] $skillName"
        return [pscustomobject]@{
            engine  = 'codex'
            skill   = $skillName
            status  = 'dry-run'
            log     = $rawLogPath
            message = ''
        }
    }

    $prompt | & $CodexCommand exec --full-auto --cd $RepoRoot --output-last-message $lastMessagePath - 2>&1 |
        Tee-Object -FilePath $rawLogPath | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Codex failed for '$skillName' (exit: $exitCode)."
    }

    return [pscustomobject]@{
        engine  = 'codex'
        skill   = $skillName
        status  = 'ok'
        log     = $rawLogPath
        message = ''
    }
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$resolvedSkillDirectory = Join-Path $repoRoot $SkillDirectory
if (-not (Test-Path -LiteralPath $resolvedSkillDirectory)) {
    throw "Skill directory not found: $resolvedSkillDirectory"
}

$logRoot = Join-Path $repoRoot $LogDirectory
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
}

$skillFiles = Get-ChildItem -LiteralPath $resolvedSkillDirectory -File -Filter '*.md' |
    Sort-Object Name |
    Where-Object { $ExcludeSkills -notcontains $_.BaseName }

if (-not $skillFiles -or $skillFiles.Count -eq 0) {
    throw "No skill files found in $resolvedSkillDirectory after exclusions."
}

$runClaude = $Engine -eq 'claude' -or $Engine -eq 'both'
$runCodex = $Engine -eq 'codex' -or $Engine -eq 'both'

$claudeCommand = $null
$codexCommand = $null

if ($runClaude) {
    $claudeCommand = Get-ToolPath -ToolName 'claude' -FallbackPaths @(
        (Join-Path $env:USERPROFILE 'AppData\Roaming\npm\claude.cmd'),
        (Join-Path $env:USERPROFILE '.npm\claude.cmd')
    )
}

if ($runCodex) {
    $codexCommand = Get-ToolPath -ToolName 'codex'
}

$results = New-Object System.Collections.Generic.List[object]
$hasFailure = $false

foreach ($skillFile in $skillFiles) {
    Write-Host "=== Running skill: $($skillFile.BaseName) ==="

    if ($runClaude) {
        try {
            $results.Add((Invoke-ClaudeSkill -ClaudeCommand $claudeCommand -SkillFile $skillFile -LogRoot $logRoot -DryRunMode:$DryRun))
        } catch {
            $hasFailure = $true
            $results.Add([pscustomobject]@{
                    engine  = 'claude'
                    skill   = $skillFile.BaseName
                    status  = 'failed'
                    log     = ''
                    message = $_.Exception.Message
                })
            Write-Warning $_.Exception.Message
            if ($StopOnError) {
                break
            }
        }
    }

    if ($runCodex) {
        try {
            $results.Add((Invoke-CodexSkill -CodexCommand $codexCommand -SkillFile $skillFile -RepoRoot $repoRoot -LogRoot $logRoot -DryRunMode:$DryRun))
        } catch {
            $hasFailure = $true
            $results.Add([pscustomobject]@{
                    engine  = 'codex'
                    skill   = $skillFile.BaseName
                    status  = 'failed'
                    log     = ''
                    message = $_.Exception.Message
                })
            Write-Warning $_.Exception.Message
            if ($StopOnError) {
                break
            }
        }
    }
}

$results | Sort-Object engine, skill | Format-Table -AutoSize

if (-not $DryRun) {
    $summaryPath = Join-Path $logRoot ("summary-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
    $results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Host "Summary written to: $summaryPath"
}

if ($hasFailure) {
    exit 1
}

exit 0
