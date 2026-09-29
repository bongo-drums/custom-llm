# Re-run of the chat mode checks only (after the router fix). Run from the personal-wiki folder with Wi-Fi OFF.
#   powershell -ExecutionPolicy Bypass -File scripts\offline_chat_check.ps1
$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path evidence\offline | Out-Null
$log = "evidence\offline\chat-rerun-$stamp.txt"

function Step($title, $cmd) {
    "`n==================== $title ====================" | Tee-Object -FilePath $log -Append | Write-Host -ForegroundColor Cyan
    "PS> $cmd" | Tee-Object -FilePath $log -Append | Write-Host
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Invoke-Expression "$cmd 2>&1" | Out-String -Stream | Tee-Object -FilePath $log -Append | Write-Host
    ("(exit {0}, {1:N1} s)" -f $LASTEXITCODE, $sw.Elapsed.TotalSeconds) | Tee-Object -FilePath $log -Append | Write-Host
}

Step "0. Proof of offline"  "Test-NetConnection 1.1.1.1 -Port 443 -InformationLevel Quiet"
Step "1. Status"            "wiki status"
Step "2. Chat mode checks (re-run after the router fix)" "wiki chat --script evals/chat_script.txt"
Step "3. Ask after the chat claim (fresh process, must be insufficient)" "wiki ask 'Who was my head football coach at Moreau Catholic?'"
"log: $log" | Write-Host
