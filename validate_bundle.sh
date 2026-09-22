#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$PROJECT_DIR/setup_sd.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

[ -f "$INSTALLER" ] || fail "setup_sd.sh is missing"
[ -x "$INSTALLER" ] || fail "setup_sd.sh is not executable"
pass "setup_sd.sh is executable"

bash -n "$INSTALLER" || fail "setup_sd.sh failed Bash syntax validation"
pass "setup_sd.sh Bash syntax"

GUI_FILE="$TMP_DIR/sd_gui_app.py"
awk '
  /cat <<'"'"'EOF'"'"' > "\$INSTALL_ROOT\/\.sd_gui_app\.py"/ {capture=1; next}
  capture && /^EOF$/ {exit}
  capture {print}
' "$INSTALLER" > "$GUI_FILE"
[ -s "$GUI_FILE" ] || fail "embedded GUI Python could not be extracted"
python3 -m py_compile "$GUI_FILE" || fail "embedded GUI Python failed syntax validation"
pass "embedded GUI Python syntax"

grep -Fq 'VENV_DIR="$INSTALL_ROOT/stable-diffusion-env"' "$INSTALLER" || fail "final virtual-environment path is missing"
grep -Fq 'python3 -m venv "$VENV_DIR"' "$INSTALLER" || fail "virtual environment is not created directly at its final path"
if grep -Fq 'STAGE_VENV_DIR=' "$INSTALLER"; then
  fail "a staged virtual-environment path is still defined"
fi
pass "final-path virtual-environment creation"

grep -Fq 'sha256sum "$temporary"' "$INSTALLER" || fail "model SHA-256 calculation is missing"
grep -Fq 'expected_hash' "$INSTALLER" || fail "expected model hash comparison is missing"
grep -Fq 'SHA-256 verification failed' "$INSTALLER" || fail "model hash mismatch handling is missing"
pass "model SHA-256 verification"

grep -Fq 'RUNTIME_DIR="$INSTALL_ROOT/.sd-runtime"' "$INSTALLER" || fail "installation-scoped runtime directory is missing"
grep -Fq 'WEBUI_PID_FILE="\$RUNTIME_DIR/webui.pid"' "$INSTALLER" || fail "installation-scoped WebUI PID file is missing"
grep -Fq 'GUI_PID_FILE="\$RUNTIME_DIR/gui.pid"' "$INSTALLER" || fail "installation-scoped GUI PID file is missing"
if grep -Eq '/tmp/(sd_webui|sd_gui)\.pid' "$INSTALLER"; then
  fail "shared /tmp PID files are still referenced"
fi
pass "installation-scoped runtime PID files"

grep -Fq 'git rev-parse HEAD' "$INSTALLER" || fail "pinned WebUI commit verification is missing"
grep -Fq 'import clip' "$INSTALLER" || fail "OpenAI CLIP import verification is missing"
pass "pinned dependency verification"

printf '\nBundle validation passed.\n'
