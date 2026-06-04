#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SING_BOX_VERSION="${SING_BOX_VERSION:-latest}"
INSTALL_DIR="/opt/singbox-rule-ui"
CONFIG_DIR="/etc/sing-box"
MANAGER_DIR="$CONFIG_DIR/manager"
RULE_DIR="$CONFIG_DIR/custom-rules"
CLASH_UI_DIR="$CONFIG_DIR/ui"

need_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root." >&2
    exit 1
  fi
}

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y curl ca-certificates tar gzip unzip python3 nftables iproute2 rsync util-linux
  else
    echo "Only apt-based systems are supported by this MVP installer." >&2
    exit 1
  fi
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
  esac
}

install_sing_box() {
  if command -v /usr/local/bin/sing-box >/dev/null 2>&1; then
    echo "sing-box already installed: $(/usr/local/bin/sing-box version | head -n 1)"
    return
  fi
  arch="$(detect_arch)"
  if [ "$SING_BOX_VERSION" = "latest" ]; then
    version="$(curl -fsSL https://api.github.com/repos/SagerNet/sing-box/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))')"
  else
    version="$SING_BOX_VERSION"
  fi
  url="https://github.com/SagerNet/sing-box/releases/download/v${version}/sing-box-${version}-linux-${arch}.tar.gz"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fL "$url" -o "$tmp/sing-box.tar.gz"
  tar -xzf "$tmp/sing-box.tar.gz" -C "$tmp"
  install -m 0755 "$tmp"/sing-box-*/sing-box /usr/local/bin/sing-box
}

install_files() {
  mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$MANAGER_DIR" "$RULE_DIR"
  rsync -a --delete "$PROJECT_DIR/singbox-rule-ui/" "$INSTALL_DIR/"
  install -m 0755 "$PROJECT_DIR/scripts/sing-box-gateway-info" /usr/local/bin/sing-box-gateway-info
  install -m 0755 "$PROJECT_DIR/scripts/uninstall.sh" /usr/local/bin/sing-box-gateway-uninstall
  install -m 0755 "$PROJECT_DIR/scripts/refresh_runtime_config.py" /usr/local/sbin/refresh-sing-box-runtime-config
  install -m 0644 "$PROJECT_DIR/systemd/singbox-rule-ui.service" /etc/systemd/system/singbox-rule-ui.service
  install -m 0755 "$PROJECT_DIR/scripts/update-sing-box-rules-jsdelivr" /usr/local/sbin/update-sing-box-rules-jsdelivr
  install -m 0644 "$PROJECT_DIR/systemd/update-sing-box-rules-jsdelivr.service" /etc/systemd/system/update-sing-box-rules-jsdelivr.service
  install -m 0644 "$PROJECT_DIR/systemd/update-sing-box-rules-jsdelivr.timer" /etc/systemd/system/update-sing-box-rules-jsdelivr.timer
  install -m 0644 "$PROJECT_DIR/systemd/sing-box.service" /etc/systemd/system/sing-box.service
  install -m 0644 "$PROJECT_DIR/systemd/sing-box-tproxy.service" /etc/systemd/system/sing-box-tproxy.service
}

install_clash_ui() {
  mkdir -p "$CLASH_UI_DIR"
  tmp="$(mktemp -d)"
  if curl -fsSL https://api.github.com/repos/Zephyruso/zashboard/releases/latest \
    | python3 -c 'import json,sys; assets=json.load(sys.stdin)["assets"]; print(next(item["browser_download_url"] for item in assets if item["name"] == "dist.zip"))' \
    | xargs curl -fL -o "$tmp/zashboard.zip"; then
    unzip -oq "$tmp/zashboard.zip" -d "$tmp/zashboard"
    if [ -d "$tmp/zashboard/dist" ]; then
      rsync -a --delete "$tmp/zashboard/dist/" "$CLASH_UI_DIR/"
    else
      rsync -a --delete "$tmp/zashboard/" "$CLASH_UI_DIR/"
    fi
    echo "zashboard installed to $CLASH_UI_DIR"
  else
    echo "WARN: zashboard download failed; sing-box will still run, and port 9090 API remains available." >&2
  fi
  rm -rf "$tmp"
}

bootstrap_config() {
  python3 "$PROJECT_DIR/scripts/bootstrap_config.py"
}

install_initial_rules() {
  RULE_UPDATE_RESTART=0 /usr/local/sbin/update-sing-box-rules-jsdelivr
}

install_tproxy_setup() {
  python3 "$PROJECT_DIR/scripts/sync_tproxy_setup.py"
}

enable_services() {
  systemctl daemon-reload
  systemctl enable --now sing-box-tproxy.service
  systemctl enable --now sing-box.service
  systemctl enable --now singbox-rule-ui.service
  systemctl enable --now update-sing-box-rules-jsdelivr.timer
}

refresh_tproxy_after_start() {
  python3 "$PROJECT_DIR/scripts/sync_tproxy_setup.py"
  systemctl restart sing-box-tproxy.service
}

main() {
  case "${1:-install}" in
    install|"") ;;
    uninstall|remove)
      exec bash "$PROJECT_DIR/scripts/uninstall.sh" "${@:2}"
      ;;
    purge)
      exec bash "$PROJECT_DIR/scripts/uninstall.sh" --purge "${@:2}"
      ;;
    *)
      echo "Unknown action: $1" >&2
      echo "Usage: sudo bash scripts/install.sh [install|uninstall|purge]" >&2
      exit 1
      ;;
  esac
  need_root
  install_packages
  install_sing_box
  install_files
  install_clash_ui
  bootstrap_config
  install_initial_rules
  install_tproxy_setup
  /usr/local/bin/sing-box check -c /etc/sing-box/config.json
  enable_services
  refresh_tproxy_after_start
  echo
  echo "Installed."
  sing-box-gateway-info
}

main "$@"
