#!/usr/bin/env bash
set -euo pipefail

REPO="${SING_BOX_GATEWAY_REPO:-hanigege/sing-box-gateway-ui}"
REF="${SING_BOX_GATEWAY_REF:-main}"
ACTION="${1:-install}"
PROXY_PREFIX="${SING_BOX_GATEWAY_PROXY_PREFIX:-https://scg.jgaga.tk/}"
PROXY_PREFIXES="${SING_BOX_GATEWAY_PROXY_PREFIXES:-${PROXY_PREFIX},https://gh-proxy.com/,https://gh.llkk.cc/}"

if ! command -v curl >/dev/null 2>&1; then
  echo "缺少 curl，请先安装 curl。" >&2
  exit 1
fi

if [ "${SING_BOX_GATEWAY_DRY_RUN:-0}" != "1" ] && [ "$(id -u)" -ne 0 ]; then
  echo "请用 root 权限运行，例如：" >&2
  echo "  curl -fsSL ${PROXY_PREFIX}https://raw.githubusercontent.com/${REPO}/${REF}/scripts/quick-install.sh | sudo bash" >&2
  exit 1
fi

tmp="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT

archive="$tmp/source.tar.gz"
src="$tmp/source"

download_first() {
  local output="$1"
  shift
  local url
  for url in "$@"; do
    echo "尝试下载: $url"
    if curl -fL --connect-timeout 10 --max-time 120 "$url" -o "$output"; then
      return 0
    fi
  done
  return 1
}

download_urls() {
  local url="$1" prefix
  IFS=',' read -ra prefixes <<< "$PROXY_PREFIXES"
  for prefix in "${prefixes[@]}"; do
    [ -n "$prefix" ] || continue
    printf "%s%s\n" "$prefix" "$url"
  done
  printf "%s\n" "$url"
}

echo "正在下载 sing-box-gateway-ui ${REPO}@${REF}..."
archive_url="https://github.com/${REPO}/archive/refs/heads/${REF}.tar.gz"
archive_urls=($(download_urls "$archive_url"))
download_first "$archive" "${archive_urls[@]}"
mkdir -p "$src"
tar -xzf "$archive" -C "$src" --strip-components=1

if [ "${SING_BOX_GATEWAY_DRY_RUN:-0}" = "1" ]; then
  test -f "$src/scripts/install.sh"
  test -f "$src/scripts/bootstrap_config.py"
  test -f "$src/scripts/uninstall.sh"
  test -f "$src/systemd/sing-box.service"
  echo "一键安装链路检查通过。"
  echo "安装器位置: $src/scripts/install.sh"
  exit 0
fi

case "$ACTION" in
  install|"")
    target="$src/scripts/install.sh"
    args=()
    ;;
  uninstall|remove)
    target="$src/scripts/uninstall.sh"
    args=()
    ;;
  purge)
    target="$src/scripts/uninstall.sh"
    args=(--purge)
    ;;
  *)
    echo "未知操作: $ACTION" >&2
    echo "可用操作: install, uninstall, purge" >&2
    exit 1
    ;;
esac

if [ -r /dev/tty ]; then
  exec bash "$target" "${args[@]}" </dev/tty
fi

if [ "$ACTION" = "install" ] || [ -z "$ACTION" ]; then
  echo "未检测到可交互终端，将使用默认值继续安装。"
else
  args+=("--yes")
fi
exec bash "$target" "${args[@]}"
