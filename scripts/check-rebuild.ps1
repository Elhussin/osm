param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'

function Assert-RebuildState {
    param($State, [string]$Log, [string]$Plan)
    $ids = @($State.tasks | ForEach-Object { $_.id })
    if ($ids.Count -ne 16 -or @($ids | Select-Object -Unique).Count -ne 16) { throw 'Expected 16 unique task IDs.' }
    foreach ($number in 0..15) {
        if (('R{0:D2}' -f $number) -notin $ids) { throw 'Missing planned task.' }
    }
    if ($State.updated -notmatch '^\d{4}-\d{2}-\d{2}$') { throw 'Missing update date.' }
    if ($State.current_task -notin $ids -or $State.next_task -notin $ids) { throw 'Invalid current or next task.' }
    foreach ($task in $State.tasks) {
        if ($task.status -notin @('pending','in_progress','blocked','done')) { throw "Invalid status: $($task.id)" }
        if ($Plan -notmatch "\| $($task.id) \|") { throw "Task missing from plan: $($task.id)" }
        foreach ($dependency in $task.depends_on) {
            if ($dependency -notin $ids -or $dependency -eq $task.id) { throw "Invalid dependency: $($task.id)" }
            # IDs encode the approved order; reject cycles and forward dependencies.
            if ([int]$dependency.Substring(1) -ge [int]$task.id.Substring(1)) { throw 'Dependency order is invalid.' }
            $parent = $State.tasks | Where-Object id -eq $dependency
            if ($task.status -in @('in_progress','done') -and $parent.status -ne 'done') { throw "Unfinished dependency: $($task.id)" }
        }
        if ($task.status -eq 'done') {
            if (@($task.evidence).Count -eq 0) { throw "Missing evidence: $($task.id)" }
            foreach ($entry in $task.evidence) {
                if ($entry -notmatch '^T\d{3,}$') { throw 'Invalid evidence ID.' }
                $pattern = '(?m)^## ' + [regex]::Escape($entry) + ' \| passed\r?$'
                if ($Log -notmatch $pattern) { throw "No passing evidence: $entry" }
                $section = ($Log -split $pattern, 2)[1] -split '(?m)^## ', 2 | Select-Object -First 1
                if ($section -notmatch "(?m)^Task: $($task.id)\r?$" -or $section -notmatch '(?m)^Command: .+' -or $section -notmatch '(?m)^Date: \d{4}-\d{2}-\d{2}') {
                    throw "Incomplete or mismatched evidence: $entry"
                }
            }
        }
    }
}

foreach ($file in @('AGENTS.md','README.md','rebuild/README.md','docs/rebuild/README.md','docs/rebuild/PLAN.md','docs/rebuild/STATUS.json','docs/rebuild/ACCEPTANCE.md','docs/rebuild/TEST_LOG.md','docs/rebuild/CHANGELOG.md','docs/rebuild/CLEANUP.md','docs/rebuild/decisions/0001-architecture.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $file) -PathType Leaf)) { throw "Required file missing: $file" }
}
$state = Get-Content -LiteralPath (Join-Path $Root 'docs/rebuild/STATUS.json') -Raw | ConvertFrom-Json
$log = Get-Content -LiteralPath (Join-Path $Root 'docs/rebuild/TEST_LOG.md') -Raw
$plan = Get-Content -LiteralPath (Join-Path $Root 'docs/rebuild/PLAN.md') -Raw
Assert-RebuildState $state $log $plan
foreach ($obsolete in @('osmBack/romve_cash.py','osmBack/romve_migratian.py','osmBack/scripts/romve_cash.py','osmBack/scripts/romve_migratian.py')) {
    if (Test-Path -LiteralPath (Join-Path $Root $obsolete)) { throw "Obsolete reset tool still present: $obsolete" }
}
Write-Output 'PASS: rebuild plan, dependency order, completion evidence, and cleanup checks.'

# Exercise failure paths in memory; never alter the real task registry.
$cases = @(
    @{ Name = 'completion without evidence'; Mutate = { param($s) $s.tasks[0].status = 'done'; $s.tasks[0].evidence = @() } },
    @{ Name = 'unknown dependency'; Mutate = { param($s) $s.tasks[1].depends_on = @('R99') } },
    @{ Name = 'unfinished dependency'; Mutate = { param($s) $s.tasks[0].status = 'pending'; $s.tasks[1].status = 'in_progress' } },
    @{ Name = 'cycle'; Mutate = { param($s) $s.tasks[0].depends_on = @('R01') } },
    @{ Name = 'duplicate ID'; Mutate = { param($s) $s.tasks[1].id = 'R00' } },
    @{ Name = 'unknown status'; Mutate = { param($s) $s.tasks[0].status = 'finished' } },
    @{ Name = 'missing test result'; Mutate = { param($s) $s.tasks[0].status = 'done'; $s.tasks[0].evidence = @('T999999') } }
)
foreach ($case in $cases) {
    $copy = $state | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    & $case.Mutate $copy
    $rejected = $false
    try { Assert-RebuildState $copy $log $plan } catch { $rejected = $true }
    if (-not $rejected) { throw "Validator accepted invalid state: $($case.Name)" }
    Write-Output "PASS: rejects $($case.Name)."
}
$positive = $state | ConvertTo-Json -Depth 10 | ConvertFrom-Json
$positive.tasks[0].status = 'done'
$positive.tasks[0].evidence = @('T999998')
$sample = "## T999998 | passed`nTask: R00`nDate: 2026-11-09`nCommand: sample test`n"
Assert-RebuildState $positive $sample $plan
Write-Output 'PASS: accepts completion with matching passing evidence.'
$mismatched = "## T999998 | passed`nTask: R01`nDate: 2026-11-09`nCommand: sample test`n"
$rejected = $false
try { Assert-RebuildState $positive $mismatched $plan } catch { $rejected = $true }
if (-not $rejected) { throw 'Validator accepted evidence for another task.' }
Write-Output 'PASS: rejects evidence belonging to another task.'
