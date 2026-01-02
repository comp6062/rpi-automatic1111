#!/bin/bash
set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

say()  { echo -e "${GREEN}$*${NC}"; }
warn() { echo -e "${YELLOW}$*${NC}"; }
die()  { echo -e "${RED}$*${NC}"; exit 1; }
progress() { echo -e "${RED}$*${NC}"; sleep 0.25; }

USER_HOME="$(eval echo ~$USER)"
WEBUI_DIR="$USER_HOME/stable-diffusion-webui"
VENV_DIR="$USER_HOME/stable-diffusion-env"

DOWNLOAD_MODELS=1

OLD_URL_1="https://github.com/Stability-AI/stablediffusion.git"
OLD_URL_2="https://github.com/Stability-AI/stablediffusion"
NEW_URL="https://github.com/comp6062/Stability-AI-stablediffusion.git"

LOG_FILE="$USER_HOME/sd_install_$(date +%F_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# -----------------------------
# OS detect
# -----------------------------
OS_ID="unknown"
OS_CODENAME="unknown"
if [ -f /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-unknown}"
  OS_CODENAME="${VERSION_CODENAME:-unknown}"
fi

say "Log: $LOG_FILE"
say "Detected OS: ${OS_ID} (${OS_CODENAME})"
say "Kernel: $(uname -a)"
say "Arch: $(uname -m)"
df -h "$USER_HOME" || true
free -h || true
echo ""

# -----------------------------
# Cleanup on real failure
# -----------------------------
CLEANUP_ON_FAIL=1
cleanup_partial_install() {
  [ "$CLEANUP_ON_FAIL" = "1" ] || return 0
  warn "Installer failed. Cleaning up partial install..."
  rm -rf "$WEBUI_DIR" 2>/dev/null || true
  rm -rf "$VENV_DIR" 2>/dev/null || true
}

on_error() {
  local ec=$?
  local line=${BASH_LINENO[0]:-unknown}
  local cmd=${BASH_COMMAND:-unknown}
  echo ""
  echo -e "${RED}ERROR (exit=$ec) at line $line:${NC} $cmd"
  echo ""
  echo "---- last 120 log lines ----"
  tail -n 120 "$LOG_FILE" 2>/dev/null || true
  echo "----------------------------"
  echo ""
  echo -e "${YELLOW}Log saved at:${NC} $LOG_FILE"
  cleanup_partial_install
  exit "$ec"
}
trap on_error ERR

# -----------------------------
# Helpers
# -----------------------------
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }

wait_for_apt() {
  progress "Waiting for apt/dpkg locks (if any)..."
  local i=0
  while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
        fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || \
        fuser /var/cache/apt/archives/lock >/dev/null 2>&1; do
    i=$((i+1))
    [ "$i" -le 120 ] || die "apt/dpkg lock held too long."
    sleep 2
  done
}

retry() {
  # retry <attempts> <sleep_seconds> -- command...
  local attempts="$1"; shift
  local delay="$1"; shift
  local n=1
  until "$@"; do
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    warn "Retry $n/$attempts failed: $*"
    n=$((n+1))
    sleep "$delay"
  done
}

# SAFE network probe: warn-only; NEVER fails install
net_probe() {
  progress "Network probe (warn-only)..."
  if curl -fsS --max-time 8 https://pypi.org/simple/pip/ >/dev/null 2>&1; then
    say "Network probe OK."
  else
    warn "Network probe failed (this does NOT stop install)."
    warn "If downloads fail later, it’s likely DNS/proxy/CDN blocking."
  fi
}

# -----------------------------
# Preflight
# -----------------------------
require_cmd sudo
require_cmd curl
require_cmd git
require_cmd tee

net_probe

# -----------------------------
# deps
# -----------------------------
wait_for_apt
progress "Updating apt..."
sudo apt update
sudo apt upgrade -y

progress "Installing dependencies..."
sudo apt install -y \
  git wget curl ca-certificates \
  build-essential pkg-config \
  libssl-dev libffi-dev \
  zlib1g-dev libjpeg-dev libtiff5-dev libopenjp2-7-dev \
  libpng-dev libfreetype6-dev liblcms2-dev libwebp-dev \
  libavif-dev \
  libgl1 libglib2.0-0 \
  rustc cargo \
  python3 python3-venv python3-pip

# -----------------------------
# uv + python 3.10
# -----------------------------
progress "Ensuring uv is installed..."
if ! command -v uv >/dev/null 2>&1; then
  retry 3 2 curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$USER_HOME/.local/bin:$PATH"
require_cmd uv

progress "Installing Python 3.10 via uv..."
retry 3 3 uv python install 3.10

progress "Creating venv (Python 3.10)..."
rm -rf "$VENV_DIR" 2>/dev/null || true
uv venv --python 3.10 "$VENV_DIR"

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

progress "Bootstrapping pip..."
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# -----------------------------
# clone webui
# -----------------------------
progress "Cloning Stable Diffusion WebUI..."
rm -rf "$WEBUI_DIR" 2>/dev/null || true
retry 3 3 git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git "$WEBUI_DIR"
cd "$WEBUI_DIR"

# -----------------------------
# universal Stability-AI URL patch
# -----------------------------
apply_repo_patch() {
  progress "Applying Stability-AI URL patch (universal)..."

  local files=()
  while IFS= read -r f; do files+=("$f"); done < <(
    (grep -RIl --exclude-dir=.git --exclude-dir=venv --exclude='*.pyc' "$OLD_URL_1" . 2>/dev/null || true)
    (grep -RIl --exclude-dir=.git --exclude-dir=venv --exclude='*.pyc' "$OLD_URL_2" . 2>/dev/null || true)
  )

  # de-dupe
  local uniq=()
  for f in "${files[@]}"; do
    [ -f "$f" ] || continue
    local seen=0
    for u in "${uniq[@]}"; do [ "$u" = "$f" ] && seen=1 && break; done
    [ "$seen" = "1" ] && continue
    uniq+=("$f")
  done

  local patched=0
  for f in "${uniq[@]}"; do
    if grep -q "$OLD_URL_1" "$f" || grep -q "$OLD_URL_2" "$f"; then
      cp -a "$f" "$f.bak.$(date +%F_%H%M%S)"
      sed -i "s#${OLD_URL_1}#${NEW_URL}#g" "$f"
      sed -i "s#${OLD_URL_2}#${NEW_URL}#g" "$f"
      say "Patched: $f"
      patched=1
    fi
  done

  rm -rf "repositories/stable-diffusion-stability-ai" 2>/dev/null || true

  if [ "$patched" = "1" ]; then
    say "Patch applied."
  else
    warn "No Stability-AI URL found to patch (may already be updated)."
  fi
}
apply_repo_patch

# -----------------------------
# torch + requirements
# -----------------------------
progress "Installing PyTorch (CPU)..."
retry 3 5 python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

progress "Installing WebUI requirements..."
retry 3 5 python -m pip install -r requirements.txt

# -----------------------------
# models (optional)
# -----------------------------
download_if_missing() {
  local url="$1"
  local path="$2"
  if [ -f "$path" ]; then
    say "Model exists: $path"
    return 0
  fi
  mkdir -p "$(dirname "$path")"
  progress "Downloading model: $url"
  retry 3 5 wget -O "$path" "$url"
}

if [ "$DOWNLOAD_MODELS" = "1" ]; then
  progress "Downloading model files..."
  MODEL1_PATH="$WEBUI_DIR/models/Stable-diffusion/CyberRealistic_V7.0_FP16.safetensors"
  MODEL1_URL="https://huggingface.co/cyberdelia/CyberRealistic/resolve/main/CyberRealistic_V7.0_FP16.safetensors"
  MODEL2_PATH="$WEBUI_DIR/models/Stable-diffusion/Realistic_Vision_V5.1-inpainting.safetensors"
  MODEL2_URL="https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1-inpainting.safetensors"
  download_if_missing "$MODEL1_URL" "$MODEL1_PATH"
  download_if_missing "$MODEL2_URL" "$MODEL2_PATH"
else
  warn "Skipping model downloads (DOWNLOAD_MODELS=0)."
fi

# -----------------------------
# run script (includes last-chance remote fix)
# -----------------------------
progress "Creating run_sd.sh..."
cat <<'EOF' > "$USER_HOME/run_sd.sh"
#!/bin/bash
set -eEuo pipefail

USER_HOME="$(eval echo ~$USER)"
WEBUI_DIR="$USER_HOME/stable-diffusion-webui"
VENV_DIR="$USER_HOME/stable-diffusion-env"

OLD_URL_1="https://github.com/Stability-AI/stablediffusion.git"
OLD_URL_2="https://github.com/Stability-AI/stablediffusion"
NEW_URL="https://github.com/comp6062/Stability-AI-stablediffusion.git"

source "$VENV_DIR/bin/activate"
cd "$WEBUI_DIR"

REPO_DIR="$WEBUI_DIR/repositories/stable-diffusion-stability-ai"
if [ -d "$REPO_DIR/.git" ]; then
  cur="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
  if [ "$cur" = "$OLD_URL_1" ] || [ "$cur" = "$OLD_URL_2" ]; then
    echo "Fixing stable-diffusion-stability-ai remote URL..."
    git -C "$REPO_DIR" remote set-url origin "$NEW_URL"
  fi
fi

python launch.py --skip-torch-cuda-test --no-half --listen
EOF
chmod +x "$USER_HOME/run_sd.sh"

# -----------------------------
# remove.sh
# -----------------------------
progress "Creating remove.sh..."
cat <<'EOF' > "$USER_HOME/remove.sh"
#!/bin/bash
set -eEuo pipefail
USER_HOME="$(eval echo ~$USER)"
rm -f "$USER_HOME/run_sd.sh" || true
rm -rf "$USER_HOME/stable-diffusion-webui" || true
rm -rf "$USER_HOME/stable-diffusion-env" || true
rm -f "$USER_HOME/remove.sh" || true
echo "Cleanup complete."
EOF
chmod +x "$USER_HOME/remove.sh"

# Success
CLEANUP_ON_FAIL=0
say "Setup complete. Start with: ~/run_sd.sh"
