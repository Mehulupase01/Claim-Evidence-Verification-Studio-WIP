param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$command = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($command) {
    $executable = $command.Source
} else {
    $installedPath = 'C:\Program Files (x86)\cloudflared\cloudflared.exe'
    if (-not (Test-Path -LiteralPath $installedPath)) {
        throw 'cloudflared is not installed. Follow the tunnel instructions in README.md before starting a tunnel.'
    }
    $executable = $installedPath
}

Write-Host "Opening a temporary public tunnel to http://127.0.0.1:$Port"
Write-Host 'Keep this window and the application running for as long as the review URL is needed.'
& $executable tunnel --url "http://127.0.0.1:$Port" --no-autoupdate
