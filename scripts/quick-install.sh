#!/usr/bin/env bash
set -euo pipefail

REPO="${SING_BOX_GATEWAY_REPO:-hanigege/sing-box-gateway-ui}"
REF="${SING_BOX_GATEWAY_REF:-main}"

if [ "$(id -u)" -ne 0 ]; then
  echo "请用 root 权限运行，例如：" >&2
  echo "  curl -fsSL https://raw.githubusercontent.com/${REPO}/${REF}/scripts/quick-install.sh | sudo bash" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "缺少 curl，请先安装 curl。" >&2
  exit 1
fi

tmp="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT

archive="$tmp/source.tar.gz"
src="$tmp/source"
url="https://github.com/${REPO}/archive/refs/heads/${REF}.tar.gz"

echo "正在下载 sing-box-gateway-ui ${REPO}@${REF}..."
curl -fL "$url" -o "$archive"
mkdir -p "$src"
tar -xzf "$archive" -C "$src" --strip-components=1

exec bash "$src/scripts/install.sh"
