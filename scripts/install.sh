#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SING_BOX_VERSION="${SING_BOX_VERSION:-latest}"
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
    apt-get install -y curl ca-certificates tar gzip unzip python3 nftables iproute2 rsync util-linux radvd
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
  if [ "$SING_BOX_VERSION" = "latest" ]; then
    api_url="https://api.github.com/repos/SagerNet/sing-box/releases/latest"
    api_urls=($(download_urls "$api_url"))
    version="$(curl_text_first "${api_urls[@]}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))')"
  else
    version="$SING_BOX_VERSION"
  fi
  url="https://github.com/SagerNet/sing-box/releases/download/v${version}/sing-box-${version}-linux-${arch}.tar.gz"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  urls=($(download_urls "$url"))
  curl_first "$tmp/sing-box.tar.gz" "${urls[@]}"
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

write_fallback_resolver() {
  rm -f /etc/resolv.conf
  {
    echo "nameserver 223.5.5.5"
    echo "nameserver 1.1.1.1"
    echo "options timeout:2 attempts:2"
  } > /etc/resolv.conf
}

resolver_has_external_nameserver() {
  awk '
    /^nameserver[[:space:]]+/ &&
    $2 !~ /^127\./ &&
    $2 != "::1" &&
    $2 != "0.0.0.0" &&
    $2 != "::" { found=1 }
    END { exit found ? 0 : 1 }
  ' /etc/resolv.conf 2>/dev/null
}

ensure_bootstrap_resolver() {
  if resolver_has_external_nameserver; then
    return
  fi
  echo "No usable external DNS resolver found in /etc/resolv.conf; writing temporary public resolvers."
  write_fallback_resolver
}

port53_owner() {
  ss -H -ltnup 'sport = :53' 2>/dev/null | awk '
    match($0, /users:\(\("([^"]+)"/, m) { print m[1] }
  ' | sort -u | paste -sd, -
}

ensure_dns_port_available() {
  owner="$(port53_owner)"
  if [ -z "$owner" ]; then
    return
  fi
  case "$owner" in
    *systemd-resolve*|*systemd-resolved*)
      disable_systemd_resolved_stub
      ;;
    *sing-box*)
      return
      ;;
    *)
      echo "Port 53 is already in use by: $owner" >&2
      echo "Please stop that DNS service first, or free port 53 before installing." >&2
      exit 1
      ;;
  esac
}

install_tproxy_setup() {
  python3 "$PROJECT_DIR/scripts/sync_tproxy_setup.py"
}

collect_host_nameservers() {
  {
    if [ -r /run/systemd/resolve/resolv.conf ]; then
      awk '/^nameserver[[:space:]]+/ {print $2}' /run/systemd/resolve/resolv.conf
    fi
    if [ -r /etc/resolv.conf ]; then
      awk '/^nameserver[[:space:]]+/ {print $2}' /etc/resolv.conf
    fi
    if command -v resolvectl >/dev/null 2>&1; then
      resolvectl dns 2>/dev/null | tr ' ' '\n'
    fi
  } | awk '
    /^[0-9a-fA-F:.]+$/ &&
    $0 !~ /^127\./ &&
    $0 != "::1" &&
    $0 != "0.0.0.0" &&
    $0 != "::" &&
    !seen[$0]++ { print "nameserver " $0 }
  '
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
  nameservers="$(collect_host_nameservers)"
  touch /etc/systemd/resolved.conf
  if grep -qE '^[#[:space:]]*DNSStubListener=' /etc/systemd/resolved.conf; then
    sed -i 's/^[#[:space:]]*DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
  else
    printf '\nDNSStubListener=no\n' >> /etc/systemd/resolved.conf
  fi
  systemctl reload-or-restart systemd-resolved.service >/dev/null 2>&1 || true
  if [ -L /etc/resolv.conf ] || ! awk '
    /^nameserver[[:space:]]+/ &&
    $2 !~ /^127\./ &&
    $2 != "::1" { found=1 }
    END { exit found ? 0 : 1 }
  ' /etc/resolv.conf 2>/dev/null; then
    rm -f /etc/resolv.conf
    {
      if [ -n "$nameservers" ]; then
        printf "%s\n" "$nameservers"
      else
        echo "nameserver 223.5.5.5"
        echo "nameserver 1.1.1.1"
      fi
      echo "options timeout:2 attempts:2"
    } > /etc/resolv.conf
  fi
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
  ensure_bootstrap_resolver
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
  sing-box-gateway-info
}

main "$@"
