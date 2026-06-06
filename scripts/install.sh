#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SING_BOX_BUNDLED_VERSION="${SING_BOX_BUNDLED_VERSION:-1.13.13}"
SING_BOX_ARCH="${SING_BOX_ARCH:-auto}"
INSTALL_DIR="/opt/singbox-rule-ui"
CONFIG_DIR="/etc/sing-box"
MANAGER_DIR="$CONFIG_DIR/manager"
RULE_DIR="$CONFIG_DIR/custom-rules"
CLASH_UI_DIR="$CONFIG_DIR/ui"
PROXY_PREFIX="${SING_BOX_GATEWAY_PROXY_PREFIX:-https://scg.jgaga.tk/}"
PROXY_PREFIXES="${SING_BOX_GATEWAY_PROXY_PREFIXES:-${PROXY_PREFIX},https://gh-proxy.com/,https://gh.llkk.cc/}"

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
  local arch="${1:-${SING_BOX_ARCH}}"
  if [ "$arch" = "auto" ] || [ -z "$arch" ]; then
    arch="$(uname -m)"
  fi
  case "$arch" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
  esac
}

ask() {
  local prompt="$1" default="${2:-}" value suffix=""
  [ -n "$default" ] && suffix=" [$default]"
  if [ "${SING_BOX_GATEWAY_ASSUME_DEFAULTS:-0}" = "1" ]; then
    printf "%s\n" "$default"
    return
  fi
  if [ -r /dev/tty ]; then
    printf "%s%s: " "$prompt" "$suffix" > /dev/tty
    IFS= read -r value < /dev/tty || value=""
  else
    value=""
  fi
  printf "%s\n" "${value:-$default}"
}

choose_sing_box_runtime() {
  if [ "${SING_BOX_GATEWAY_ASSUME_DEFAULTS:-0}" = "1" ]; then
    SING_BOX_ARCH="${SING_BOX_ARCH:-auto}"
    return
  fi
  if [ ! -r /dev/tty ]; then
    echo "No interactive terminal detected; using bundled sing-box ${SING_BOX_BUNDLED_VERSION} and auto architecture."
    SING_BOX_ARCH="${SING_BOX_ARCH:-auto}"
    return
  fi
  echo
  echo "sing-box binary: bundled ${SING_BOX_BUNDLED_VERSION} (repository-tested)"
  SING_BOX_ARCH="$(ask "CPU architecture: auto/amd64/arm64" "$SING_BOX_ARCH")"
}

download_urls() {
  local url="$1" prefix
  case "$url" in
    https://*) ;;
    *) printf "%s\n" "$url"; return ;;
  esac
  IFS=',' read -ra prefixes <<< "$PROXY_PREFIXES"
  for prefix in "${prefixes[@]}"; do
    [ -n "$prefix" ] || continue
    printf "%s%s\n" "$prefix" "$url"
  done
  printf "%s\n" "$url"
}

curl_first() {
  local output="$1"
  shift
  local url
  for url in "$@"; do
    echo "尝试下载: $url"
    if curl -fL --connect-timeout 10 --max-time 180 "$url" -o "$output"; then
      return 0
    fi
  done
  return 1
}

curl_text_first() {
  local url tmp
  tmp="$(mktemp)"
  for url in "$@"; do
    echo "尝试下载: $url" >&2
    if curl -fsSL --connect-timeout 10 --max-time 60 "$url" -o "$tmp"; then
      cat "$tmp"
      rm -f "$tmp"
      return 0
    fi
  done
  rm -f "$tmp"
  return 1
}

install_sing_box() {
  if command -v /usr/local/bin/sing-box >/dev/null 2>&1; then
    echo "sing-box already installed: $(/usr/local/bin/sing-box version | head -n 1)"
    return
  fi
  arch="$(detect_arch)"
  archive="$PROJECT_DIR/third_party/sing-box/v${SING_BOX_BUNDLED_VERSION}/sing-box-${SING_BOX_BUNDLED_VERSION}-linux-${arch}.tar.gz"
  sums="$PROJECT_DIR/third_party/sing-box/v${SING_BOX_BUNDLED_VERSION}/SHA256SUMS"
  if [ ! -r "$archive" ]; then
    echo "Bundled sing-box archive not found: $archive" >&2
    exit 1
  fi
  if [ -r "$sums" ]; then
    archive_name="$(basename "$archive")"
    expected="$(awk -v name="$archive_name" '$2 == name { print $1 }' "$sums")"
    if [ -z "$expected" ]; then
      echo "No checksum entry for bundled archive: $archive_name" >&2
      exit 1
    fi
    actual="$(sha256sum "$archive" | awk '{ print $1 }')"
    if [ "$actual" != "$expected" ]; then
      echo "Checksum mismatch for bundled archive: $archive_name" >&2
      exit 1
    fi
  fi
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  echo "Installing bundled sing-box ${SING_BOX_BUNDLED_VERSION} (${arch})"
  tar -xzf "$archive" -C "$tmp"
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
  api_url="https://api.github.com/repos/Zephyruso/zashboard/releases/latest"
  api_urls=($(download_urls "$api_url"))
  if asset_url="$(curl_text_first "${api_urls[@]}" \
      | python3 -c 'import json,sys; assets=json.load(sys.stdin)["assets"]; print(next(item["browser_download_url"] for item in assets if item["name"] == "dist.zip"))')" \
    && asset_urls=($(download_urls "$asset_url")) \
    && curl_first "$tmp/zashboard.zip" "${asset_urls[@]}"; then
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

port53_conflicts() {
  python3 - <<'PY'
import ipaddress
import json
import re
import subprocess
from pathlib import Path

config = json.loads(Path("/etc/sing-box/config.json").read_text(encoding="utf-8"))
targets = set()
for inbound in config.get("inbounds", []) or []:
    if isinstance(inbound, dict) and inbound.get("listen_port") == 53:
        listen = str(inbound.get("listen") or "").strip()
        if listen:
            targets.add(listen)

if not targets:
    raise SystemExit(0)

def normalize(address):
    address = address.strip("[]")
    if "%" in address:
        address = address.split("%", 1)[0]
    try:
        return str(ipaddress.ip_address(address))
    except ValueError:
        return address

targets = {normalize(item) for item in targets}
wildcards = {"0.0.0.0", "::", "*"}
conflicts = set()
for command in (["ss", "-H", "-lunp", "sport = :53"], ["ss", "-H", "-ltnp", "sport = :53"]):
    result = subprocess.run(command, text=True, capture_output=True)
    for line in result.stdout.splitlines():
        owner_match = re.search(r'users:\(\("([^"]+)"', line)
        owner = owner_match.group(1) if owner_match else "unknown"
        if owner == "sing-box":
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[4]
        if local.startswith("["):
            address = local.rsplit("]:", 1)[0].lstrip("[")
        else:
            address = local.rsplit(":", 1)[0]
        address = normalize(address)
        if address in wildcards or address in targets:
            conflicts.add(owner)

if conflicts:
    print(",".join(sorted(conflicts)))
PY
}

port53_owners() {
  ss -H -ltnup 'sport = :53' 2>/dev/null | awk '
    match($0, /users:\(\("([^"]+)"/, m) { print m[1] }
  ' | sort -u | paste -sd, -
}

disable_systemd_resolved_stub() {
  if ! systemctl list-unit-files systemd-resolved.service >/dev/null 2>&1; then
    return
  fi
  mkdir -p "$MANAGER_DIR"
  if [ -e /etc/systemd/resolved.conf ] && [ ! -e "$MANAGER_DIR/resolved.conf.before-sing-box" ]; then
    cp -a /etc/systemd/resolved.conf "$MANAGER_DIR/resolved.conf.before-sing-box" || true
  fi
  if [ -e /etc/resolv.conf ] && [ ! -e "$MANAGER_DIR/resolv.conf.before-sing-box" ]; then
    cp -a /etc/resolv.conf "$MANAGER_DIR/resolv.conf.before-sing-box" || true
  fi
  touch /etc/systemd/resolved.conf
  if grep -qE '^[#[:space:]]*DNSStubListener=' /etc/systemd/resolved.conf; then
    sed -i 's/^[#[:space:]]*DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
  else
    printf '\nDNSStubListener=no\n' >> /etc/systemd/resolved.conf
  fi
  systemctl reload-or-restart systemd-resolved.service >/dev/null 2>&1 || true
  echo "systemd-resolved DNS stub disabled; port 53 is reserved for sing-box."
}

ensure_dns_port_available() {
  all_owners="$(port53_owners)"
  case "$all_owners" in
    *systemd-resolve*|*systemd-resolved*)
      disable_systemd_resolved_stub
      ;;
  esac
  owner="$(port53_conflicts)"
  if [ -z "$owner" ]; then
    return
  fi
  case "$owner" in
    *sing-box*)
      return
      ;;
    *)
      echo "Port 53 is already in use by: $owner" >&2
      echo "Please stop that DNS service first, or free port 53 before installing." >&2
      echo "The installer will not modify /etc/resolv.conf or replace your DNS upstreams automatically." >&2
      exit 1
      ;;
  esac
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
  choose_sing_box_runtime
  install_packages
  install_files
  bootstrap_config
  install_sing_box
  install_clash_ui
  install_initial_rules
  install_tproxy_setup
  ensure_dns_port_available
  /usr/local/bin/sing-box check -c /etc/sing-box/config.json
  enable_services
  refresh_tproxy_after_start
  echo
  echo "Installed."
  echo "Host DNS was not changed. Configure client/router DNS manually if needed."
  sing-box-gateway-info
}

main "$@"
