#!/usr/bin/env bash
# Her geliştirici repo'yu klonladıktan sonra bir kez çalıştırır.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath hooks/git
chmod +x hooks/git/* hooks/claude/*.py scripts/*.py scripts/*.sh
mkdir -p .claude/state history logs reports/agents
echo "✔ git hook'ları bağlandı (core.hooksPath=hooks/git)"
echo "✔ Claude hook'ları .claude/settings.json ile otomatik yüklenir"
bash scripts/test_hooks.sh
