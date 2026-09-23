# Offline demonstration (Windows PowerShell). Run from the personal-wiki folder AFTER turning Wi-Fi off.
# Records everything to evidence/offline/transcript-<time>.txt.
#   powershell -ExecutionPolicy Bypass -File scripts\offline_demo.ps1
$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path evidence\offline | Out-Null
Start-Transcript -Path "evidence\offline\transcript-$stamp.txt"

function Step($title, $cmd) {
    Write-Host "`n==================== $title ====================" -ForegroundColor Cyan
    Write-Host "PS> $cmd"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Invoke-Expression $cmd
    Write-Host ("(exit {0}, {1:N1} s)" -f $LASTEXITCODE, $sw.Elapsed.TotalSeconds)
}

Step "0. Proof of offline"      "Test-NetConnection 1.1.1.1 -Port 443 -InformationLevel Quiet"
Step "0b. Device"               "Get-CimInstance Win32_Processor | Select-Object Name; Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM; '{0:N1} GB RAM' -f ((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"
Step "1. Help"                  "wiki --help"
Step "2. Status (model, quantization, runtime)" "wiki status"
Step "3. Ingest all sources"    "wiki ingest vault/raw"
Step "4. Re-ingest one source (must not create duplicates)" "wiki ingest vault/raw/ms-pacman-README.md"
Step "5. Wiki page list"        "Get-ChildItem -Recurse vault/wiki -Filter *.md | Select-Object -ExpandProperty FullName"
Step "6. Search (no model)"     "wiki search 'row level security policy' --save"
Step "7. Retrieval check"       "wiki eval --retrieval-only"
Step "8. Four ask-mode tests"   "wiki eval"
Step "9. Status after (loaded memory)" "wiki status"
Step "10. Chat mode checks"     "wiki chat --script evals/chat_script.txt"
Step "11. Ask after the chat claim (fresh process, must be insufficient)" "wiki ask 'What grade did I receive on the Ms. Pac-Man assignment?'"
Step "12. Ollama memory"        "ollama ps"

Stop-Transcript
