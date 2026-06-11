param(
    [string]$RootPath = (Resolve-Path "$PSScriptRoot/..")
)

Write-Host "=== Wave 2b: remaining GOGETA_* env vars and sentinels ==="

# Focus on env var names in code (not backups)
$files = Get-ChildItem -Path $RootPath -Recurse -Filter "*.py" | Where-Object {
    $_.FullName -notmatch '\\__pycache__\\' -and
    $_.FullName -notmatch '\\node_modules\\' -and
    $_.FullName -notmatch '\\venv\\' -and
    $_.FullName -notmatch '\\.venv\\' -and
    $_.FullName -notmatch '\\.git\\' -and
    $_.FullName -notmatch '\\website\\' -and
    $_.FullName -notmatch '\\\\.pytest_cache\\\\'
}

$replacements = @(
    # These are exact string matches for GOGETA_* env var names
    @('GOGETA_QUIET', 'GOGETA_QUIET'),
    @('GOGETA_PREFILL_MESSAGES_FILE', 'GOGETA_PREFILL_MESSAGES_FILE'),
    @('GOGETA_IGNORE_USER_CONFIG', 'GOGETA_IGNORE_USER_CONFIG'),
    @('"_GOGETA_GATEWAY"', '"_GOGETA_GATEWAY"'),
    @("'_GOGETA_GATEWAY'", "'_GOGETA_GATEWAY'"),
    @('GOGETA_REDACT_SECRETS', 'GOGETA_REDACT_SECRETS'),
    @('GOGETA_DEFER_AGENT_STARTUP', 'GOGETA_DEFER_AGENT_STARTUP'),
    @('GOGETA_ACCEPT_HOOKS', 'GOGETA_ACCEPT_HOOKS'),
    @('GOGETA_LIGHT', 'GOGETA_LIGHT'),
    @('GOGETA_FAST_STARTUP_BANNER', 'GOGETA_FAST_STARTUP_BANNER'),
    @('GOGETA_MAX_TOKENS', 'GOGETA_MAX_TOKENS'),
    @('GOGETA_INFERENCE_PROVIDER', 'GOGETA_INFERENCE_PROVIDER'),
    @('GOGETA_MAX_ITERATIONS', 'GOGETA_MAX_ITERATIONS'),
    @('GOGETA_IGNORE_RULES', 'GOGETA_IGNORE_RULES'),
    @('GOGETA_EPHEMERAL_SYSTEM_PROMPT', 'GOGETA_EPHEMERAL_SYSTEM_PROMPT'),
    @('GOGETA_YOLO_MODE', 'GOGETA_YOLO_MODE'),
    @('GOGETA_DEV_CREDITS_FIXTURE', 'GOGETA_DEV_CREDITS_FIXTURE'),
    @('GOGETA_SIGTERM_GRACE', 'GOGETA_SIGTERM_GRACE'),
    @('GOGETA_KANBAN_GOAL_MODE', 'GOGETA_KANBAN_GOAL_MODE'),
    @('GOGETA_KANBAN_TASK', 'GOGETA_KANBAN_TASK'),
    @('GOGETA_INTERACTIVE', 'GOGETA_INTERACTIVE'),
    @('GOGETA_SESSION_SOURCE', 'GOGETA_SESSION_SOURCE'),
    @('GOGETA_DISABLE_FTS_TRIGRAM', 'GOGETA_DISABLE_FTS_TRIGRAM'),
    @('GOGETA_AGENT_LOGO', 'GOGETA_AGENT_LOGO'),
    @('GOGETA_CADUCEUS', 'GOGETA_CADUCEUS'),
    # Generic GOGETA_HOME in comments/docstrings (specific enough to avoid collisions)
    @('{GOGETA_HOME}', '{GOGETA_HOME}'),
    @('this GOGETA_HOME.', 'this GOGETA_HOME.'),
    @('the standard GOGETA_HOME,', 'the standard GOGETA_HOME,'),
    # Unquoted sentinel references
    @('_GOGETA_GATEWAY marker', '_GOGETA_GATEWAY marker')
)

$totalFiles = 0
$modifiedFiles = 0

foreach ($file in $files) {
    $totalFiles++
    try {
        $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop
    } catch { continue }
    $original = $content

    foreach ($pair in $replacements) {
        $content = $content.Replace($pair[0], $pair[1])
    }

    if ($content -ne $original) {
        Set-Content -LiteralPath $file.FullName -Value $content -NoNewline
        $modifiedFiles++
        if ($modifiedFiles -le 20) {
            Write-Host "  [M] $($file.FullName)"
        }
    }
}

Write-Host "`nDone. Scanned $totalFiles files, modified $modifiedFiles files."
