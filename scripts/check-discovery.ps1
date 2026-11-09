param([switch]$RefreshInventory)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    function Get-Disposition([string]$Path) {
        switch -Regex ($Path) {
            '(^|/)\.env($|\.)' { return @('configuration-private','do-not-copy','R03') }
            '/(media|logs|data|static|__pypackages__)/' { return @('legacy-assets-data','review-no-copy','R15') }
            '/migrations/' { return @('legacy-migrations','reference-no-copy','R15') }
            '^osmBack/apps/(tenants|users|branches)/' { return @('identity-tenancy','rewrite-after-review','R04') }
            '^osmBack/apps/hrm/' { return @('human-resources','defer-full-module','R04') }
            '^osmBack/apps/(crm|prescriptions)/' { return @('customers-prescriptions','rewrite-after-review','R06') }
            '^osmBack/apps/products/' { return @('catalog-inventory','rewrite-after-review','R07') }
            '^osmBack/apps/accounting/' { return @('accounting','rewrite-after-review','R09') }
            '^osmBack/apps/sales/' { return @('sales','rewrite-after-review','R10') }
            '^osmBack/scripts/' { return @('legacy-operations','do-not-execute-review','R03') }
            '^osmFront/' { return @('legacy-frontend','extract-ux-then-replace','R05') }
            '^generate-zod-form\.ts$' { return @('legacy-form-generator','retire-after-reference-check','R05') }
            default { return @('legacy-infrastructure','review-before-replacement','R03') }
        }
    }
    $paths = @(git -c core.quotepath=false ls-files -- osmBack osmFront generate-zod-form.ts docker-compose.yml)
    if ($LASTEXITCODE -ne 0 -or $paths.Count -eq 0) { throw 'Unable to enumerate tracked legacy files.' }
    $rows = @($paths | Sort-Object | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | ForEach-Object {
        $choice = Get-Disposition $_
        [pscustomobject]@{ path = $_; category = $choice[0]; disposition = $choice[1]; review_by = $choice[2] }
    })
    $csv = @($rows | ConvertTo-Csv -NoTypeInformation)
    $target = 'docs/rebuild/legacy-inventory.csv'
    if ($RefreshInventory) { $csv | Set-Content -LiteralPath $target -Encoding utf8 }
    if (-not (Test-Path -LiteralPath $target)) { throw 'Inventory missing; run with -RefreshInventory.' }
    $actual = @(Get-Content -LiteralPath $target)
    if (Compare-Object $csv $actual -SyncWindow 0) { throw 'Inventory is stale; review changes and refresh.' }
    foreach ($row in $rows) {
        if ($row.review_by -notmatch '^R\d{2}$' -or -not $row.disposition) { throw "Unclassified file: $($row.path)" }
    }
    foreach ($required in @('DISCOVERY.md','OPEN_QUESTIONS.md','INSURANCE_WORKFLOW.md','decisions/0002-pdm-and-configuration.md')) {
        if (-not (Test-Path -LiteralPath "docs/rebuild/$required")) { throw "Missing discovery deliverable: $required" }
    }
    $spec = Get-Content docs/rebuild/SCENARIOS.json -Raw | ConvertFrom-Json
    if ($spec.kind -ne 'acceptance_specification_not_executed_business_tests') { throw 'Scenario execution status must be explicit.' }
    $ids = @($spec.scenarios | ForEach-Object { $_.id })
    if ($ids.Count -ne 10 -or @($ids | Select-Object -Unique).Count -ne 10) { throw 'Expected 10 unique acceptance scenarios.' }
    $questions = Get-Content docs/rebuild/OPEN_QUESTIONS.md -Raw
    foreach ($scenario in $spec.scenarios) {
        foreach ($field in @('id','stage','source','anchor','given','when','then','tests')) {
            if (-not $scenario.$field) { throw "Incomplete scenario: $($scenario.id) / $field" }
        }
        if ($scenario.stage -notmatch '^R(0[4-9]|1[0-3])$') { throw 'Invalid target stage.' }
        $source = Get-Content -LiteralPath $scenario.source -Raw
        if (-not $source.Contains($scenario.anchor)) { throw "Unverified source anchor: $($scenario.id)" }
        if ($scenario.unresolved -and -not $questions.Contains($scenario.unresolved)) { throw 'Untracked open question.' }
    }
    # Classification boundaries: private config and migrations must never become code to copy.
    $fixtures = @(
        @{ path='osmBack/.env.development'; expected='do-not-copy' },
        @{ path='osmBack/apps/sales/migrations/0001_initial.py'; expected='reference-no-copy' },
        @{ path='osmBack/scripts/delete_db.py'; expected='do-not-execute-review' },
        @{ path='osmBack/apps/products/models/product.py'; expected='rewrite-after-review' },
        @{ path='osmFront/src/app/page.tsx'; expected='extract-ux-then-replace' },
        @{ path='osmBack/data/csv/Users.csv'; expected='review-no-copy' }
    )
    foreach ($fixture in $fixtures) {
        if ((Get-Disposition $fixture.path)[1] -ne $fixture.expected) { throw "Classification failed: $($fixture.path)" }
    }
    Write-Output "PASS: $($rows.Count) tracked legacy files classified; 10 source-linked acceptance specifications; 6 classification boundary checks."
    Write-Output 'LIMIT: static discovery checks only; no ERP business scenario was executed.'
} finally { Pop-Location }
