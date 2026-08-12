#!/bin/sh
set -eu

VERSION="${CODEX_RELAY_VERSION:-0.2.0}"
REPOSITORY="DamonKoy/codex-session-relay"
ASSET="codex-relay-${VERSION}.pyz"
RELEASE_BASE="${CODEX_RELAY_RELEASE_BASE:-https://github.com/${REPOSITORY}/releases/download/v${VERSION}}"
INSTALL_DIR="${CODEX_RELAY_INSTALL_DIR:-${HOME}/.local/bin}"
RC_FILE="${CODEX_RELAY_RC_FILE:-${HOME}/.zshrc}"
PATH_MARKER="# Added by Codex Session Relay installer"

say() {
    printf '%s\n' "$*"
}

fail() {
    printf 'codex-session-relay installer: %s\n' "$*" >&2
    exit 1
}

case "${RELEASE_BASE}" in
    https://*) ;;
    file://*)
        [ "${CODEX_RELAY_TEST_MODE:-0}" = "1" ] || fail "release URL 必须使用 HTTPS"
        ;;
    *) fail "release URL 必须使用 HTTPS" ;;
esac

[ "$(uname -s)" = "Darwin" ] || fail "v${VERSION} 一键安装仅支持 macOS"
command -v curl >/dev/null 2>&1 || fail "缺少 curl"
command -v shasum >/dev/null 2>&1 || fail "缺少 shasum"
command -v python3 >/dev/null 2>&1 || fail "缺少 Python 3.9+"

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' \
    || fail "需要 Python 3.9 或更高版本"

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/codex-relay-install.XXXXXX")"
trap 'rm -rf "$TEMP_DIR"' EXIT HUP INT TERM

fetch() {
    source_url="$1"
    destination="$2"
    if [ "${CODEX_RELAY_TEST_MODE:-0}" = "1" ]; then
        curl -fsSL "${source_url}" -o "${destination}"
    else
        curl --proto '=https' --tlsv1.2 -fsSL "${source_url}" -o "${destination}"
    fi
}

fetch "${RELEASE_BASE}/SHA256SUMS" "${TEMP_DIR}/SHA256SUMS"
fetch "${RELEASE_BASE}/${ASSET}" "${TEMP_DIR}/${ASSET}"

EXPECTED="$(awk -v asset="${ASSET}" '$2 == asset {print $1}' "${TEMP_DIR}/SHA256SUMS")"
[ -n "${EXPECTED}" ] || fail "校验清单中缺少 ${ASSET}"
[ "$(printf '%s' "${EXPECTED}" | wc -c | tr -d ' ')" = "64" ] \
    || fail "SHA-256 格式无效"
ACTUAL="$(shasum -a 256 "${TEMP_DIR}/${ASSET}" | awk '{print $1}')"
[ "${ACTUAL}" = "${EXPECTED}" ] || fail "SHA-256 校验失败；未安装任何文件"

mkdir -p "${INSTALL_DIR}"
chmod 700 "${INSTALL_DIR}" 2>/dev/null || true

backup_target() {
    target="$1"
    if [ -e "${target}" ] || [ -L "${target}" ]; then
        backup="${target}.previous"
        suffix=1
        while [ -e "${backup}" ] || [ -L "${backup}" ]; do
            backup="${target}.previous.${suffix}"
            suffix=$((suffix + 1))
        done
        mv "${target}" "${backup}"
        say "已备份原文件：${backup}"
    fi
}

backup_target "${INSTALL_DIR}/codex-relay"
backup_target "${INSTALL_DIR}/codex-model"

chmod 755 "${TEMP_DIR}/${ASSET}"
mv "${TEMP_DIR}/${ASSET}" "${INSTALL_DIR}/codex-relay"
ln -sfn "codex-relay" "${INSTALL_DIR}/codex-model"

if [ "${CODEX_RELAY_SKIP_PATH_UPDATE:-0}" != "1" ]; then
    touch "${RC_FILE}"
    if ! grep -F "${PATH_MARKER}" "${RC_FILE}" >/dev/null 2>&1; then
        {
            printf '\n%s\n' "${PATH_MARKER}"
            printf 'export PATH="%s:$PATH"\n' "${INSTALL_DIR}"
        } >> "${RC_FILE}"
        say "已更新 PATH：${RC_FILE}"
    fi
fi

"${INSTALL_DIR}/codex-relay" --version >/dev/null
"${INSTALL_DIR}/codex-model" --version >/dev/null

say "Codex Session Relay v${VERSION} 安装完成。"
say "安装目录：${INSTALL_DIR}"
say "新开终端后可运行：codex-model gpt"
say "首次使用 DeepSeek：codex-model deepseek"
say "安全检查：codex-relay doctor"
