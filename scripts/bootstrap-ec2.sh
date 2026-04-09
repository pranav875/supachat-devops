#!/usr/bin/env bash
# bootstrap-ec2.sh — Idempotent EC2 setup script for SupaChat
# Safe to run multiple times; each step checks before acting.
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — override via environment variables before running
# ---------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/your-org/supachat.git}"
REPO_DIR="${REPO_DIR:-/opt/supachat}"
ENV_SOURCE="${ENV_SOURCE:-}"   # path to a local .env file to copy in; optional

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*"; }
die()   { echo "[ERROR] $*" >&2; exit 1; }

require_root() {
  [[ $EUID -eq 0 ]] || die "This script must be run as root (or via sudo)."
}

# ---------------------------------------------------------------------------
# 1. Install Docker (idempotent)
# ---------------------------------------------------------------------------
install_docker() {
  if command -v docker &>/dev/null; then
    info "Docker already installed: $(docker --version)"
    return
  fi

  info "Installing Docker..."
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg lsb-release

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  systemctl enable --now docker
  info "Docker installed: $(docker --version)"
}

# ---------------------------------------------------------------------------
# 2. Install Docker Compose standalone (idempotent)
#    The compose plugin above covers `docker compose`; this also installs the
#    standalone `docker-compose` binary for compatibility with the CI pipeline.
# ---------------------------------------------------------------------------
install_docker_compose() {
  if command -v docker-compose &>/dev/null; then
    info "docker-compose already installed: $(docker-compose --version)"
    return
  fi

  info "Installing docker-compose standalone..."
  local version
  version=$(curl -fsSL https://api.github.com/repos/docker/compose/releases/latest \
    | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
  curl -fsSL \
    "https://github.com/docker/compose/releases/download/${version}/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
  info "docker-compose installed: $(docker-compose --version)"
}

# ---------------------------------------------------------------------------
# 3. Clone or update the repository (idempotent)
# ---------------------------------------------------------------------------
setup_repo() {
  if [[ -d "${REPO_DIR}/.git" ]]; then
    info "Repository already cloned at ${REPO_DIR}; pulling latest..."
    git -C "${REPO_DIR}" pull --ff-only
  else
    info "Cloning repository to ${REPO_DIR}..."
    git clone "${REPO_URL}" "${REPO_DIR}"
  fi
}

# ---------------------------------------------------------------------------
# 4. Copy .env file (idempotent — skips if already present unless source given)
# ---------------------------------------------------------------------------
setup_env() {
  local env_file="${REPO_DIR}/.env"

  if [[ -n "${ENV_SOURCE}" ]]; then
    info "Copying .env from ${ENV_SOURCE}..."
    cp "${ENV_SOURCE}" "${env_file}"
  elif [[ -f "${env_file}" ]]; then
    info ".env already exists at ${env_file}; skipping copy."
  else
    warn ".env not found and ENV_SOURCE not set."
    warn "Copying .env.example as a placeholder — fill in real values before starting."
    cp "${REPO_DIR}/.env.example" "${env_file}"
  fi
}

# ---------------------------------------------------------------------------
# 5. Start services with docker-compose (idempotent)
# ---------------------------------------------------------------------------
start_services() {
  info "Starting services with docker-compose..."
  docker-compose -f "${REPO_DIR}/docker-compose.yml" pull
  docker-compose -f "${REPO_DIR}/docker-compose.yml" up -d --remove-orphans
  info "Services started. Current status:"
  docker-compose -f "${REPO_DIR}/docker-compose.yml" ps
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  require_root
  install_docker
  install_docker_compose
  setup_repo
  setup_env
  start_services
  info "Bootstrap complete. SupaChat is running at http://$(curl -fsSL ifconfig.me 2>/dev/null || echo '<EC2-PUBLIC-IP>')"
}

main "$@"
