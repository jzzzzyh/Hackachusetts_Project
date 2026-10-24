# watch-and-sync.ps1
# Watches the project folder and auto-commits + pushes any change.
# Run this in a terminal: powershell -ExecutionPolicy Bypass -File watch-and-sync.ps1

$projectPath = $PSScriptRoot
$debounceSeconds = 5   # wait 5s after last change before committing

Write-Host "Watching $projectPath for changes. Press Ctrl+C to stop."

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $projectPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor
                        [System.IO.NotifyFilters]::FileName -bor
                        [System.IO.NotifyFilters]::DirectoryName

$global:lastEvent = [datetime]::MinValue
$global:pendingSync = $false

$action = {
    $path = $Event.SourceEventArgs.FullPath
    # Ignore git internals and the script itself
    if ($path -match '\\\.git\\' -or $path -match 'watch-and-sync\.ps1') { return }
    $global:lastEvent = [datetime]::Now
    $global:pendingSync = $true
}

Register-ObjectEvent $watcher Changed -Action $action | Out-Null
Register-ObjectEvent $watcher Created -Action $action | Out-Null
Register-ObjectEvent $watcher Deleted -Action $action | Out-Null
Register-ObjectEvent $watcher Renamed -Action $action | Out-Null

try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($global:pendingSync) {
            $elapsed = ([datetime]::Now - $global:lastEvent).TotalSeconds
            if ($elapsed -ge $debounceSeconds) {
                $global:pendingSync = $false
                Set-Location $projectPath
                git add -A
                $status = git status --porcelain
                if ($status) {
                    $msg = "auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
                    git commit -m $msg
                    git pull --rebase origin dev 2>&1 | Write-Host
                    git push origin dev 2>&1 | Write-Host
                    Write-Host "Synced at $(Get-Date -Format 'HH:mm:ss')"
                }
            }
        }
    }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Get-EventSubscriber | Unregister-Event
}
