#!/bin/sh
# SPDX-FileCopyrightText: 2026 zxabinbina
# SPDX-License-Identifier: GPL-3.0-or-later

# Gaze 中文版一键安装脚本: https://zxabinbina.cc.cd/projects/gaze/install.sh
# 用法: curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh
#
# 安装优先级：
# 1. 在 zxaBinbina/gaze-zh 的 GitHub Releases 中查找匹配当前系统与架构的
#    中文版核心安装包（包名 gaze-zh，支持 rpm / deb），自动安装。
# 2. Releases 中暂无适配的安装包时，自动转用官方安装器（支持 Ubuntu、
#    Debian、Arch、openSUSE 等发行版），原有参数会原样透传，例如：
#    curl -fsSL https://zxabinbina.cc.cd/projects/gaze/install.sh | sh -s -- --yes
#
# 期望的资产命名（便于脚本识别）：
#   rpm: gaze-zh-<版本>.<标识>.<arch>.rpm      arch: x86_64 / aarch64
#   deb: gaze-zh_<版本>_<arch>.deb             arch: amd64 / arm64
set -e

{
ZH_REPO="zxaBinbina/gaze-zh"
PKG_PREFIX="gaze-zh"
OFFICIAL_INSTALLER="https://gaze.gundulabs.com/install.sh"
RELEASES_PAGE="https://github.com/${ZH_REPO}/releases"

ESC="$(printf '\033')"
if [ -t 1 ] && [ "${TERM:-}" != "dumb" ] && [ -z "${NO_COLOR:-}" ]; then
    BOLD="${ESC}[1m" DIM="${ESC}[2m" RED="${ESC}[31m" GREEN="${ESC}[32m" YELLOW="${ESC}[33m" RESET="${ESC}[0m"
else
    BOLD="" DIM="" RED="" GREEN="" YELLOW="" RESET=""
fi

say() { printf '%s\n' "$*"; }
ok() { printf '%s\n' "${GREEN}==>${RESET} $*"; }
warn() { printf '%s\n' "${YELLOW}警告:${RESET} $*" 1>&2; }
die() { printf '%s\n' "${RED}安装失败:${RESET} $*" 1>&2; exit 1; }

command -v curl >/dev/null 2>&1 || die "未找到 curl，请先安装 curl 后重试。"

# deb 的架构命名与 uname 不同：x86_64→amd64、aarch64→arm64。
deb_arch() {
    case "$1" in
        x86_64) echo amd64 ;;
        aarch64) echo arm64 ;;
        *) echo "$1" ;;
    esac
}

# 包格式：有 dnf/zypper 用 rpm，有 apt-get/dpkg 用 deb。
detect_format() {
    if command -v dnf >/dev/null 2>&1 || command -v zypper >/dev/null 2>&1; then
        echo rpm
    elif command -v apt-get >/dev/null 2>&1 || command -v dpkg >/dev/null 2>&1; then
        echo deb
    else
        echo unknown
    fi
}

# 列出 Releases（最近 20 个）中的全部下载地址，每行一个。
list_assets() {
    curl -fsSL "https://api.github.com/repos/${ZH_REPO}/releases?per_page=20" 2>/dev/null |
        sed -n 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

# 用法: find_package <格式> <架构>；只匹配中文版核心包，避免误装组件包。
find_package() {
    format="$1"
    arch="$2"
    assets="$(list_assets)"
    [ -n "$assets" ] || return 1
    case "$format" in
        rpm) pattern="\\.${arch}\\.rpm$" ;;
        deb) pattern="_${arch}\\.deb$" ;;
        *) return 1 ;;
    esac
    echo "$assets" | grep -E "/${PKG_PREFIX}[^/]*${pattern}" | head -n 1
}

install_package() {
    format="$1"
    file="$2"
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=""
    elif command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        die "需要 root 权限安装软件包：请用 sudo 运行，或手动从 ${RELEASES_PAGE} 下载安装。"
    fi
    case "$format" in
        rpm)
            if command -v dnf >/dev/null 2>&1; then
                $SUDO dnf install -y "$file"
            else
                $SUDO zypper --non-interactive install "$file"
            fi
            ;;
        deb)
            if command -v apt-get >/dev/null 2>&1; then
                $SUDO apt-get install -y "$file" || $SUDO apt-get -f install -y
            else
                $SUDO dpkg -i "$file" || { $SUDO apt-get update; $SUDO apt-get -f install -y; }
            fi
            ;;
    esac
}

need_fallback() {
    say "Releases 中暂无适配当前系统（$1）的中文版安装包。"
    say "正在转用官方安装器（支持 Ubuntu、Debian、Arch、openSUSE 等发行版）…"
    say ""
    curl -fsSL "$OFFICIAL_INSTALLER" | sh -s -- "$@"
}

main() {
    say "${BOLD}Gaze 中文版一键安装${RESET}"
    say "仓库: https://github.com/${ZH_REPO}"

    arch="$(uname -m)"
    format="$(detect_format)"
    if [ "$format" = "unknown" ]; then
        need_fallback "未识别的包管理格式 / ${arch}" "$@"
        return 0
    fi

    pkg_arch="$arch"
    [ "$format" = "deb" ] && pkg_arch="$(deb_arch "$arch")"

    ok "在 Releases 中查找 ${format} / ${pkg_arch} 的中文版安装包…"
    rpm_url="$(find_package "$format" "$pkg_arch")" || rpm_url=""
    if [ -z "$rpm_url" ]; then
        need_fallback "${format} / ${pkg_arch}" "$@"
        return 0
    fi
    ok "找到安装包: $rpm_url"

    tmp_pkg="$(mktemp "${TMPDIR:-/tmp}/gaze-zh-XXXXXX.${format}")"
    trap 'rm -f "$tmp_pkg"' EXIT INT TERM
    curl -fL --progress-bar "$rpm_url" -o "$tmp_pkg" ||
        die "下载失败，请检查网络后重试，或手动从 ${RELEASES_PAGE} 下载。"

    ok "安装中文版软件包（含中文提示与 KRDP 修复）…"
    install_package "$format" "$tmp_pkg" ||
        die "安装失败。可手动从 ${RELEASES_PAGE} 下载后安装。"

    say ""
    ok "安装完成。中文版软件包已包含中文提示与 KRDP 修复。"
    say "建议重启一次以应用全部系统级改动：${BOLD}sudo reboot${RESET}"
    say "录入人脸：${BOLD}gaze add-face default${RESET}    测试认证：${BOLD}gaze auth${RESET}"
    say "中文文档：https://zxabinbina.cc.cd/projects/gaze/guide/getting-started"
}

main "$@"
}
