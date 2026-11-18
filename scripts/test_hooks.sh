#!/usr/bin/env bash
# Guardrail'lerin gerçekten çalıştığını kanıtlar: her hook'a örnek olay verir, beklenen sonucu doğrular.
# Test kayıtları ayrı bir dizine yazılır; gerçek logs/ ve history/ kirlenmez.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$SANDBOX/tasks" "$SANDBOX/logs" "$SANDBOX/history" "$SANDBOX/.claude/state"
cp "$ROOT/tasks/TASK-005.md" "$SANDBOX/tasks/"
cp "$ROOT/logs/pricing.json" "$SANDBOX/logs/"
export CLAUDE_PROJECT_DIR="$SANDBOX"
G="$ROOT/hooks/claude/pre_tool_guard.py"
pass=0; fail=0

expect() { # $1=beklenen exit, $2=açıklama, $3=json
  out=$(echo "$3" | python3 "$G" 2>&1); code=$?
  if [ "$code" = "$1" ]; then echo "  ✔ $2"; pass=$((pass+1)); else echo "  ✘ $2 (exit=$code) $out"; fail=$((fail+1)); fi
}

echo "pre_tool_guard:"
expect 2 "G1 secret içeren yazma reddedilir" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$SANDBOX/apps/api/x.py\",\"content\":\"KEY='ghp_$(printf 'a%.0s' {1..36})'\"}}"
expect 2 "G2 .env yazımı reddedilir"           "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$SANDBOX/.env\",\"content\":\"X=1\"}}"
expect 2 "G2 history/ elle yazılamaz"          "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$SANDBOX/history/a.jsonl\",\"new_string\":\"x\"}}"
expect 2 "G4 force push reddedilir"            '{"tool_name":"Bash","tool_input":{"command":"git push origin task/x --force"}}'
expect 2 "G4 --no-verify reddedilir"           '{"tool_name":"Bash","tool_input":{"command":"git commit -m x --no-verify"}}'
expect 0 "Normal komut izinli"                 '{"tool_name":"Bash","tool_input":{"command":"uv run pytest -q"}}'
echo "TASK-005" > "$SANDBOX/.claude/state/active-task"
expect 0 "G3 owned_paths içi yazma izinli"     "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$SANDBOX/apps/api/app/modules/tasks/service.py\",\"content\":\"x=1\"}}"
expect 2 "G3 owned_paths dışı yazma reddedilir" "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$SANDBOX/apps/web/src/App.tsx\",\"content\":\"x\"}}"
expect 0 "G3 TASK dosyası her zaman yazılabilir" "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$SANDBOX/tasks/TASK-005.md\",\"new_string\":\"x\"}}"

echo "prompt_log + stop_log:"
echo '{"session_id":"testsess1","prompt":"TASK-005 implement et, token ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}' | python3 "$ROOT/hooks/claude/prompt_log.py"
if grep -q "REDACTED" "$SANDBOX"/history/*.jsonl && ! grep -q "ghp_a" "$SANDBOX"/history/*.jsonl; then echo "  ✔ prompt kaydedildi, secret redakte"; pass=$((pass+1)); else echo "  ✘ prompt redaksiyonu"; fail=$((fail+1)); fi
T="$SANDBOX/transcript.jsonl"
cat > "$T" <<'EOF'
{"message":{"role":"assistant","id":"m1","model":"claude-opus-5-5","usage":{"input_tokens":1000,"output_tokens":500,"cache_read_input_tokens":20000,"cache_creation_input_tokens":2000},"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"apps/api/app/modules/tasks/service.py"}},{"type":"text","text":"TASK-005 AC-1 testi yeşil."}]}}
EOF
echo "{\"session_id\":\"testsess1\",\"transcript_path\":\"$T\",\"hook_event_name\":\"Stop\"}" | python3 "$ROOT/hooks/claude/stop_log.py"
cost=$(python3 -c "import json;print(json.loads(open('$SANDBOX/logs/ai-usage.jsonl').readline())['cost_usd'])")
# beklenen: (1000*4 + 500*20 + 2000*5 + 20000*0.2)/1e6 = 0.028
if [ "$cost" = "0.028" ]; then echo "  ✔ token ve maliyet loglandı (\$$cost)"; pass=$((pass+1)); else echo "  ✘ maliyet $cost"; fail=$((fail+1)); fi
echo "{\"session_id\":\"testsess1\",\"transcript_path\":\"$T\",\"hook_event_name\":\"Stop\"}" | python3 "$ROOT/hooks/claude/stop_log.py"
n=$(wc -l < "$SANDBOX/logs/ai-usage.jsonl" | tr -d ' ')
if [ "$n" = "1" ]; then echo "  ✔ aynı mesaj iki kez sayılmadı"; pass=$((pass+1)); else echo "  ✘ çift sayım ($n satır)"; fail=$((fail+1)); fi

echo "git commit-msg:"
cd "$ROOT"
printf 'yanlis mesaj\n' > "$SANDBOX/m1"; if ! bash hooks/git/commit-msg "$SANDBOX/m1" 2>/dev/null; then echo "  ✔ TASK'sız mesaj reddedilir"; pass=$((pass+1)); else echo "  ✘"; fail=$((fail+1)); fi
printf 'TASK-005: task gecislerini ekle\n' > "$SANDBOX/m2"; if bash hooks/git/commit-msg "$SANDBOX/m2"; then echo "  ✔ geçerli mesaj kabul"; pass=$((pass+1)); else echo "  ✘"; fail=$((fail+1)); fi
printf 'TASK-999: olmayan task\n' > "$SANDBOX/m3"; if ! bash hooks/git/commit-msg "$SANDBOX/m3" 2>/dev/null; then echo "  ✔ olmayan TASK reddedilir"; pass=$((pass+1)); else echo "  ✘"; fail=$((fail+1)); fi

echo "SONUÇ: $pass geçti, $fail kaldı"
[ "$fail" = 0 ]
