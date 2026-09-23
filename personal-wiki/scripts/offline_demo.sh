#!/usr/bin/env bash
# Offline demonstration (macOS/Linux). Run from the personal-wiki folder AFTER turning Wi-Fi off.
set -u
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p evidence/offline
log="evidence/offline/transcript-$stamp.txt"
step() {
  printf '\n==================== %s ====================\n$ %s\n' "$1" "$2" | tee -a "$log"
  start=$(date +%s)
  bash -c "$2" 2>&1 | tee -a "$log"
  printf '(exit %s, %ss)\n' "${PIPESTATUS[0]}" "$(( $(date +%s) - start ))" | tee -a "$log"
}
step "0. Proof of offline" "curl -sS -m 5 https://www.google.com -o /dev/null && echo ONLINE || echo 'OFFLINE: no internet'"
step "0b. Device" "uname -a; (sysctl -n machdep.cpu.brand_string hw.memsize 2>/dev/null || lscpu | head -20; free -g)"
step "1. Help" "wiki --help"
step "2. Status" "wiki status"
step "3. Ingest all sources" "wiki ingest vault/raw"
step "4. Re-ingest one source (no duplicates)" "wiki ingest vault/raw/ms-pacman-README.md"
step "5. Wiki page list" "find vault/wiki -name '*.md' | sort"
step "6. Search (no model)" "wiki search 'row level security policy' --save"
step "7. Retrieval check" "wiki eval --retrieval-only"
step "8. Four ask-mode tests" "wiki eval"
step "9. Status after" "wiki status"
step "10. Chat mode checks" "wiki chat --script evals/chat_script.txt"
step "11. Ask after chat claim (fresh process)" "wiki ask 'What grade did I receive on the Ms. Pac-Man assignment?'"
step "12. Ollama memory" "ollama ps"
echo "transcript: $log"
