#!/bin/sh
# SPDX-FileCopyrightText: 2026 zxabinbina
# SPDX-License-Identifier: GPL-3.0-or-later
# 中文版发行附件按系统打包；只使用最新发行版中匹配当前系统的压缩包。
set -eu

{
ZH_REPO="zxaBinbina/gaze-zh"
OFFICIAL_INSTALLER="https://gaze.gundulabs.com/install.sh"
work=""
cleanup() { [ -z "$work" ] || rm -rf -- "$work"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
say() { printf '%s\n' "$*"; }
die() { say "安装失败：$*" >&2; exit 1; }

fallback() {
    say "最新发行版暂无适配当前系统的中文版自动安装包，转用官方安装器。"
    work="$(mktemp -d "${TMPDIR:-/tmp}/gaze-install-XXXXXX")"
    curl -fsSL "$OFFICIAL_INSTALLER" -o "$work/official-install.sh" || die "无法下载官方安装器。"
    sh "$work/official-install.sh" "$@"
}

# 软件包的本地库依赖与发行版绑定，不能仅凭 rpm/deb 扩展名选择。
detect_target() {
    [ ! -e /run/ostree-booted ] || return 1
    [ "$(uname -m)" = x86_64 ] || return 1
    [ -r /etc/os-release ] || return 1
    . /etc/os-release
    case "${ID:-}:${VERSION_ID:-}" in
        fedora:45) echo fedora-45-x86_64 ;;
        ubuntu:24.04|linuxmint:22|linuxmint:22.*) echo ubuntu-24.04-amd64 ;;
        opensuse-tumbleweed:*) echo opensuse-tumbleweed-x86_64 ;;
        *) return 1 ;;
    esac
}

choose_desktop() {
    desktop="$(printf '%s' "${XDG_CURRENT_DESKTOP:-} ${DESKTOP_SESSION:-}" | tr '[:upper:]' '[:lower:]')"
    case "$desktop" in
        *cinnamon*) echo gaze-cinnamon-extension ;;
        *gnome*) echo gaze-gnome-extension ;;
        *kde*|*plasma*) echo gaze-kde ;;
        *hyprland*)
            if command -v omarchy >/dev/null 2>&1; then echo gaze-omarchy
            elif command -v hyprlock >/dev/null 2>&1; then echo gaze-hyprlock; fi
            ;;
    esac
}

main() {
    command -v curl >/dev/null 2>&1 || die "请先安装 curl。"
    no_pam=false
    for arg in "$@"; do
        case "$arg" in
            --yes|-y) ;;
            --no-pam) no_pam=true ;;
            --help|-h)
                say "Gaze 中文版安装器：--yes / --no-pam；其他参数转交上游安装器。"
                return 0 ;;
            *) fallback "$@"; return ;;
        esac
    done
    target="$(detect_target)" || { fallback "$@"; return; }
    assets="$(curl -fsSL "https://api.github.com/repos/${ZH_REPO}/releases/latest")" || die "无法读取最新发行版，请稍后重试。"
    bundle_url="$(printf '%s\n' "$assets" | sed -n 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | grep -E "/gaze-zh-[0-9][^/]*-${target}\.tar\.gz$" | head -n 1)"
    [ -n "$bundle_url" ] || { fallback "$@"; return; }
    case "$bundle_url" in
        "https://github.com/${ZH_REPO}/releases/download/"*) ;;
        *) die "下载地址与项目仓库不匹配。" ;;
    esac
    command -v tar >/dev/null 2>&1 || die "请先安装 tar。"
    command -v sha256sum >/dev/null 2>&1 || die "请先安装 coreutils（sha256sum）。"
    work="$(mktemp -d "${TMPDIR:-/tmp}/gaze-install-XXXXXX")"
    bundle="${bundle_url##*/}"
    say "下载中文版：$bundle"
    curl -fL "$bundle_url" -o "$work/$bundle" || die "下载失败。"
    curl -fsSL "${bundle_url%/*}/SHA256SUMS" -o "$work/release-checksums" || die "无法下载校验文件。"
    awk -v name="$bundle" '$2 == name { print }' "$work/release-checksums" > "$work/selected-checksum"
    [ "$(wc -l < "$work/selected-checksum")" -eq 1 ] || die "发行校验文件中缺少或重复列出了此压缩包。"
    (cd "$work" && sha256sum -c selected-checksum) || die "压缩包校验失败。"
    tar -xzf "$work/$bundle" --no-same-owner --no-same-permissions -C "$work" || die "解压失败。"
    package_dir="$work/${bundle%.tar.gz}"
    (cd "$package_dir" && sha256sum -c SHA256SUMS) || die "组件校验失败。"

    SUDO=""
    if [ "$(id -u)" -ne 0 ]; then
        command -v sudo >/dev/null 2>&1 || die "需要 sudo 或 root 权限。"
        SUDO="sudo"
    fi
    if "$no_pam"; then
        $SUDO mkdir -p /etc/gaze
        $SUDO touch /etc/gaze/pam.optout
    fi
    case "$target" in
        ubuntu-*) extension=deb ;;
        *) extension=rpm ;;
    esac
    components="gaze-zh gaze-gui $(choose_desktop)"
    set --
    for component in $components; do
        count=0
        for file in "$package_dir/$component"[-_][0-9]*."$extension"; do
            [ -f "$file" ] || continue
            set -- "$@" "$file"
            count=$((count + 1))
        done
        [ "$count" -eq 1 ] || die "组件 $component 的安装包缺失或不唯一。"
    done
    say "安装主程序、图形界面与当前桌面的集成组件。"
    case "$target" in
        fedora-*) $SUDO dnf install -y "$@" ;;
        ubuntu-*) $SUDO apt-get install -y "$@" ;;
        opensuse-*) $SUDO zypper --non-interactive install "$@" ;;
    esac
    say "安装完成。录入人脸：gaze add-face default；测试认证：gaze auth"
    say "桌面扩展的启用步骤：https://zxabinbina.cc.cd/projects/gaze/guide/installation"
}

main "$@"
}
