#!/bin/sh
# Resets the local preview to the seed data, then runs the admin end-to-end test. Usage: tests/run_e2e.sh <scratch-dir-with-pepper.png>
cd "$(dirname "$0")/.." || exit 1
pkill -f dev-server.mjs 2>/dev/null; sleep 1; rm -f "$1/kv-test.json"
python3 build/build.py >/dev/null
(DEV_KV_FILE="$1/kv-test.json" PORT=8788 node dev-server.mjs > "$1/dev.log" 2>&1 &)
sleep 2; python3 tests/admin_e2e.py "$1"; rc=$?; pkill -f dev-server.mjs; python3 build/build.py >/dev/null; exit $rc
