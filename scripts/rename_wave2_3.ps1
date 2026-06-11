param(
    [string]$RootPath = (Resolve-Path "$PSScriptRoot/..")
)

Write-Host "=== Wave 2+3: env vars, functions, paths, sentinels ==="

# Collect files (exclude old gogeta_cli backup, website, node_modules, etc.)
$files = Get-ChildItem -Path $RootPath -Recurse -Filter "*.py" | Where-Object {
    $_.FullName -notmatch '\\__pycache__\\' -and
    $_.FullName -notmatch '\\node_modules\\' -and
    $_.FullName -notmatch '\\venv\\' -and
    $_.FullName -notmatch '\\.venv\\' -and
    $_.FullName -notmatch '\\.git\\' -and
    $_.FullName -notmatch '\\website\\' -and
    $_.FullName -notmatch '\\\\.pytest_cache\\\\'
}

Write-Host "Scanning $($files.Count) .py files..."

$totalFiles = 0
$modifiedFiles = 0

# Replacement table (literal .Replace, no regex)
$replacements = @(
    # --- Env vars ---
    @('_GOGETA_HOME_OVERRIDE', '_GOGETA_HOME_OVERRIDE'),
    @('GOGETA_OPTIONAL_SKILLS', 'GOGETA_OPTIONAL_SKILLS'),
    @('GOGETA_OPTIONAL_MCPS', 'GOGETA_OPTIONAL_MCPS'),
    @('GOGETA_BUNDLED_SKILLS', 'GOGETA_BUNDLED_SKILLS'),
    @('GOGETA_KANBAN_BOARD', 'GOGETA_KANBAN_BOARD'),
    @('GOGETA_BACKGROUND_NOTIFICATIONS', 'GOGETA_BACKGROUND_NOTIFICATIONS'),
    @('GOGETA_TUI', 'GOGETA_TUI'),
    @('GOGETA_ISOLATE_CHILD', 'GOGETA_ISOLATE_CHILD'),
    @('GOGETA_CORE_TOOLS', 'GOGETA_CORE_TOOLS'),
    # Config path references
    @('Base directory: ~/.gogeta', 'Base directory: ~/.gogeta'),
    @('"~/.gogeta"', '"~/.gogeta"'),
    # Function names
    @('set_gogeta_home_override', 'set_gogeta_home_override'),
    @('reset_gogeta_home_override', 'reset_gogeta_home_override'),
    @('get_gogeta_home_override', 'get_gogeta_home_override'),
    @('_get_platform_default_gogeta_home', '_get_platform_default_gogeta_home'),
    @('get_default_gogeta_root', 'get_default_gogeta_root'),
    @('display_gogeta_home', 'display_gogeta_home'),
    @('get_gogeta_dir', 'get_gogeta_dir'),
    @('"get_gogeta_home"', '"get_gogeta_home"'),
    @("'get_gogeta_home'", "'get_gogeta_home'"),
    @('from get_gogeta_home', 'from get_gogeta_home'),
    @('in get_gogeta_home', 'in get_gogeta_home'),
    @('of get_gogeta_home', 'of get_gogeta_home'),
    @('get_gogeta_home.', 'get_gogeta_home.'),
    @('get_gogeta_home)', 'get_gogeta_home)'),
    @('get_gogeta_home,', 'get_gogeta_home,'),
    @(' get_gogeta_home()', ' get_gogeta_home()'),
    @('(get_gogeta_home()', '(get_gogeta_home()'),
    @('"get_gogeta_home()', '"get_gogeta_home()'),
    @("'get_gogeta_home()", "'get_gogeta_home()"),
    # Paths
    @('~/.gogeta/', '~/.gogeta/'),
    @('base / "gogeta"', 'base / "gogeta"'),
    @('Path.home() / ".gogeta"', 'Path.home() / ".gogeta"'),
    @('%LOCALAPPDATA%\\gogeta', '%LOCALAPPDATA%\\gogeta'),
    @('%LOCALAPPDATA%/gogeta', '%LOCALAPPDATA%/gogeta'),
    # GitHub URLs
    @('NousResearch/gogeta-agent', 'NousResearch/gogeta'),
    # Sentinel attrs
    @('_gogeta_ipv4_patched', '_gogeta_ipv4_patched'),
    @('_gogeta_bp_timeout_patched', '_gogeta_bp_timeout_patched'),
    @('_gogeta_verbose', '_gogeta_verbose'),
    # Cookie/session names
    @('gogeta_session_', 'gogeta_session_'),
    @('gogeta-session-', 'gogeta-session-')
)

foreach ($file in $files) {
    $totalFiles++
    try {
        $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop
    } catch {
        continue
    }
    $original = $content

    foreach ($pair in $replacements) {
        $content = $content.Replace($pair[0], $pair[1])
    }

    if ($content -ne $original) {
        Set-Content -LiteralPath $file.FullName -Value $content -NoNewline
        $modifiedFiles++
        if ($modifiedFiles -le 30) {
            Write-Host "  [M] $($file.FullName)"
        }
    }
}

Write-Host "`nDone. Scanned $totalFiles files, modified $modifiedFiles files."

# Targeted fixes for specific gogeta_* modules
Write-Host "`n=== Targeted fixes in gogeta modules ==="

$targetFiles = @(
    @("$RootPath/gogeta_logging.py", @(
        @('from gogeta_constants import', 'from gogeta_constants import'),
        @('get_gogeta_home', 'get_gogeta_home'),
        @('~/.gogeta/', '~/.gogeta/'),
        @('~/.gogeta"', '~/.gogeta"')
    )),
    @("$RootPath/gogeta_time.py", @(
        @('from gogeta_constants import', 'from gogeta_constants import'),
        @('get_gogeta_home', 'get_gogeta_home'),
        @('~/.gogeta/', '~/.gogeta/')
    )),
    @("$RootPath/gogeta_state.py", @(
        @('from gogeta_constants import', 'from gogeta_constants import'),
        @('from gogeta_time import', 'from gogeta_time import'),
        @('get_gogeta_home', 'get_gogeta_home'),
        @('~/.gogeta/', '~/.gogeta/')
    ))
)

foreach ($entry in $targetFiles) {
    $filePath = $entry[0]
    if (-not (Test-Path $filePath)) { continue }
    $content = Get-Content -LiteralPath $filePath -Raw
    $original = $content
    foreach ($pair in $entry[1]) {
        $content = $content.Replace($pair[0], $pair[1])
    }
    if ($content -ne $original) {
        Set-Content -LiteralPath $filePath -Value $content -NoNewline
        Write-Host "  [FIXED] $(Split-Path $filePath -Leaf)"
    }
}

Write-Host "`nWave 2+3 complete."
