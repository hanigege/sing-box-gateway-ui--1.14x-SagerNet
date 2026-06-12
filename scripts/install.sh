#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SING_BOX_BUNDLED_VERSION="${SING_BOX_BUNDLED_VERSION:-1.13.13}"
SING_BOX_ARCH="${SING_BOX_ARCH:-auto}"
INSTALL_DIR="/opt/singbox-rule-ui"
CONFIG_DIR="/etc/sing-box"
MANAGER_DIR="$CONFIG_DIR/manager"
RULE_DIR="$CONFIG_DIR/custom-rules"
INSTALL_STATE_FILE="$MANAGER_DIR/install-state"
RADVD_STATE_FILE="$MANAGER_DIR/radvd-state.before-sing-box"
APT_PACKAGES=(curl ca-certificates tar gzip python3 nftables iproute2 rsync util-linux)
PROXY_PREFIX="${SING_BOX_GATEWAY_PROXY_PREFIX:-https://scg.jgaga.tk/}"
PROXY_PREFIXES="${SING_BOX_GATEWAY_PROXY_PREFIXES:-${PROXY_PREFIX},https://gh-proxy.com/,https://gh.llkk.cc/}"

need_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root." >&2
    exit 1
  fi
}

state_get() {
  local key="$1"
  [ -r "$INSTALL_STATE_FILE" ] || return 0
  awk -F= -v key="$key" '$1 == key { value = substr($0, length(key) + 2) } END { print value }' "$INSTALL_STATE_FILE"
}

state_set() {
  local key="$1" value="$2" tmp
  mkdir -p "$MANAGER_DIR"
  tmp="$(mktemp)"
  if [ -r "$INSTALL_STATE_FILE" ]; then
    awk -F= -v key="$key" '$1 != key { print }' "$INSTALL_STATE_FILE" > "$tmp"
  fi
  printf "%s=%s\n" "$key" "$value" >> "$tmp"
  install -m 0600 "$tmp" "$INSTALL_STATE_FILE"
  rm -f "$tmp"
}

record_preinstall_state() {
  mkdir -p "$MANAGER_DIR"
  if [ "$(state_get state_version)" != "1" ]; then
    : > "$INSTALL_STATE_FILE"
    chmod 0600 "$INSTALL_STATE_FILE"
    state_set state_version 1
    if [ -e /usr/local/bin/sing-box ]; then
      state_set sing_box_binary preexisting
    else
      state_set sing_box_binary absent
    fi
    for package in "${APT_PACKAGES[@]}"; do
      if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
        state_set "apt_${package}" preexisting
      else
        state_set "apt_${package}" absent
      fi
    done
    # 记录安装前 53 端口归属，卸载时只恢复原本就打开的 stub listener。
    state_set port53_owners "$(port53_owners 2>/dev/null || true)"
  fi
}

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y "${APT_PACKAGES[@]}"
  else
    echo "Only apt-based systems are supported by this MVP installer." >&2
    exit 1
  fi
}

enable_radvd_requested() {
  case "${SING_BOX_GATEWAY_ENABLE_RADVD:-${RULE_UI_ENABLE_RADVD:-0}}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

disable_unrequested_radvd() {
  if enable_radvd_requested; then
    return
  fi
  if systemctl list-unit-files radvd.service >/dev/null 2>&1; then
    if [ ! -e "$RADVD_STATE_FILE" ]; then
      {
        printf "enabled=%s\n" "$(systemctl is-enabled radvd.service 2>/dev/null || true)"
        printf "active=%s\n" "$(systemctl is-active radvd.service 2>/dev/null || true)"
      } > "$RADVD_STATE_FILE"
    fi
    # 默认不允许旁路机广播 IPv6 默认网关，避免客户端选错 RA 出口。
    systemctl disable --now radvd.service >/dev/null 2>&1 || true
    systemctl mask radvd.service >/dev/null 2>&1 || true
    echo "IPv6 router advertisement is disabled by default; radvd.service was stopped and masked."
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
  state_set sing_box_binary installed
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
  # 清理旧版 helper；旧脚本会无条件写入 radvd.conf 并启动 RA 广播。
  rm -f /usr/local/sbin/refresh-sing-box-tproxy-setup
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
  echo "53 端口被 systemd-resolved 本地 stub 占用，正在关闭 DNSStubListener..."
  mkdir -p "$MANAGER_DIR"
  if [ -e /etc/systemd/resolved.conf ] && [ ! -e "$MANAGER_DIR/resolved.conf.before-sing-box" ]; then
    cp -a /etc/systemd/resolved.conf "$MANAGER_DIR/resolved.conf.before-sing-box" || true
  fi
  if [ -e /etc/resolv.conf ] && [ ! -e "$MANAGER_DIR/resolv.conf.before-sing-box" ]; then
    cp -a /etc/resolv.conf "$MANAGER_DIR/resolv.conf.before-sing-box" || true
  fi
  python3 - <<'PY'
from pathlib import Path

path = Path("/etc/systemd/resolved.conf")
text = path.read_text(encoding="utf-8") if path.exists() else ""
lines = text.splitlines()
out = []
in_resolve = False
resolve_seen = False
stub_written = False

for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        if in_resolve and not stub_written:
            out.append("DNSStubListener=no")
            stub_written = True
        in_resolve = stripped.lower() == "[resolve]"
        resolve_seen = resolve_seen or in_resolve
        out.append(line)
        continue
    if in_resolve and stripped.split("=", 1)[0].strip().lstrip("#").strip() == "DNSStubListener":
        if not stub_written:
            out.append("DNSStubListener=no")
            stub_written = True
        continue
    out.append(line)

if resolve_seen:
    if in_resolve and not stub_written:
        out.append("DNSStubListener=no")
else:
    if out and out[-1].strip():
        out.append("")
    out.extend(["[Resolve]", "DNSStubListener=no"])

path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
PY
  # 只关闭 systemd-resolved 的本地 53 端口 stub，不能改写 /etc/resolv.conf 或替换用户原有上游 DNS。
  systemctl restart systemd-resolved.service >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5; do
    sleep 1
    case "$(port53_conflicts)" in
      *systemd-resolve*|*systemd-resolved*) ;;
      *) echo "53 端口已释放，sing-box 可以监听 DNS。"; return ;;
    esac
  done
  echo "WARN: systemd-resolved 重启后仍占用 53 端口。" >&2
}

ensure_dns_port_available() {
  echo "正在检查 53 端口，确保 sing-box DNS 可以启动..."
  all_owners="$(port53_owners)"
  if [ -z "$all_owners" ]; then
    echo "53 端口当前未被占用。"
  else
    echo "53 端口当前占用进程: $all_owners"
  fi
  case "$all_owners" in
    *systemd-resolve*|*systemd-resolved*)
      disable_systemd_resolved_stub
      ;;
  esac
  owner="$(port53_conflicts)"
  if [ -z "$owner" ]; then
    echo "53 端口检查通过。"
    return
  fi
  case "$owner" in
    *sing-box*)
      echo "53 端口已由 sing-box 使用，继续安装。"
      return
      ;;
    *)
      echo "53 端口仍被占用: $owner" >&2
      echo "请先释放 53 端口再安装。如果占用者是 systemd-resolved，安装器已经尝试设置 DNSStubListener=no 并重启服务。" >&2
      echo "安装器不会自动改写 /etc/resolv.conf，也不会替换你的 DNS 上游。" >&2
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
  record_preinstall_state
  choose_sing_box_runtime
  install_packages
  install_files
  bootstrap_config
  install_sing_box
  install_initial_rules
  disable_unrequested_radvd
  install_tproxy_setup
  ensure_dns_port_available
  /usr/local/bin/sing-box check -c /etc/sing-box/config.json
  enable_services
  refresh_tproxy_after_start
  echo
  echo "Installed."
  echo "Host resolver was left unchanged. Configure client/router resolver manually if needed."
  sing-box-gateway-info
}

main "$@"
