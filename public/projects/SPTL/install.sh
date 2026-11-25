#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Download and verify the latest SPTL release, then run its user-level installer.
set -eu
command -v python3 >/dev/null 2>&1 || { printf '%s\n' '请先安装 Python 3.10+。' >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { printf '%s\n' '请先安装 curl。' >&2; exit 1; }
exec python3 - "$@" <<'PY'
import sys
if sys.version_info < (3, 10):
    sys.exit('安装失败：需要 Python 3.10+。')

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

REPO = 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics'
API = 'https://api.github.com/repos/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/latest'

def download(url, destination=None):
    command = ['curl', '--fail', '--silent', '--show-error', '--location',
               '--retry', '2', '--connect-timeout', '10', '--max-time', '120', url]
    if destination is not None:
        command += ['--output', str(destination)]
    return subprocess.check_output(command, timeout=400)

def validate_tag(tag):
    match = re.fullmatch(r'v?(\d+\.\d+\.\d+)', tag)
    if not match:
        raise ValueError('无法识别最新正式版的版本号。')
    return match.group(1)

def latest_release():
    print('正在读取 GitHub 最新正式版…', flush=True)
    try:
        release = json.loads(download(API))
    except (subprocess.SubprocessError, json.JSONDecodeError):
        print('GitHub API 暂不可用，改从最新发行页读取。', flush=True)
        url = subprocess.check_output([
            'curl', '--fail', '--silent', '--show-error', '--location',
            '--retry', '2', '--connect-timeout', '10', '--max-time', '120',
            '--output', os.devnull, '--write-out', '%{url_effective}', REPO + '/releases/latest',
        ], text=True, timeout=400).strip()
        prefix = REPO + '/releases/tag/'
        if not url.startswith(prefix):
            raise ValueError('最新发行页地址与 SPTL 仓库不匹配。')
        tag = url[len(prefix):]
        version = validate_tag(tag)
        base = REPO + '/releases/download/' + tag + '/'
        return version, base + f'sptl-source-{version}.tar.gz', base + f'SHA256SUMS-{version}'

    if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
        raise ValueError('GitHub 返回的不是公开正式版。')
    tag = release.get('tag_name', '')
    version = validate_tag(tag)
    base = REPO + '/releases/download/' + tag + '/'
    assets = release.get('assets', [])
    selected = []
    for name in (f'sptl-source-{version}.tar.gz', f'SHA256SUMS-{version}'):
        matches = [asset for asset in assets if asset.get('name') == name]
        if len(matches) != 1 or matches[0].get('browser_download_url') != base + name:
            raise ValueError(f'正式版缺少唯一且有效的下载文件：{name}')
        selected.append(matches[0]['browser_download_url'])
    return version, *selected

def extract_source(archive_path, destination, version):
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) > 10000 or sum(member.size for member in members) > 100 * 1024 * 1024:
            raise ValueError('源码归档过大。')
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or not (member.isdir() or member.isfile()):
                raise ValueError('源码归档包含不安全的路径或链接。')
        for member in members:
            path = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, path.open('wb') as target:
                    shutil.copyfileobj(source, target)
    roots = [path.parent.parent for path in destination.rglob('tools/install.py')]
    if len(roots) != 1:
        raise ValueError('源码归档缺少唯一的 tools/install.py。')
    root = roots[0]
    metadata = json.loads((root / 'plasmoid/metadata.json').read_text())
    if metadata['KPlugin']['Version'] != version:
        raise ValueError('源码中的版本与最新 Release 不一致。')
    return root

def previous_options(unit):
    if not unit.is_file():
        return {}
    lines = [line[len('ExecStart='):] for line in unit.read_text().splitlines() if line.startswith('ExecStart=')]
    if len(lines) != 1:
        raise ValueError('无法读取已有辅助服务配置，请检查 ' + str(unit))
    arguments = shlex.split(lines[0].replace('%%', '%'))
    result = {}
    if '--splayer-config' in arguments:
        position = arguments.index('--splayer-config')
        result['splayer_config'] = arguments[position + 1]
    if '--splayer-command' in arguments:
        position = arguments.index('--splayer-command')
        end = next((index for index in range(position + 1, len(arguments))
                    if arguments[index] == '--splayer-config'), len(arguments))
        result['splayer_command'] = shlex.join(arguments[position + 1:end])
    return result

def main():
    parser = argparse.ArgumentParser(description='自动下载、校验并安装或更新 GitHub 最新 SPTL 正式版，无需 sudo。')
    parser.add_argument('--dry-run', action='store_true', help='只读取最新版本与下载地址，不安装')
    parser.add_argument('--plasma', choices=('5', '6'), help='手动选择 Plasma 主版本')
    parser.add_argument('--splayer-command', help='SPlayer 启动命令，例如 AppImage 路径')
    parser.add_argument('--splayer-config', help='SPlayer 的 settings.json 路径')
    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument('--reload-plasma', action='store_true', help='安装后重载正在运行的 Plasma 面板')
    reload_group.add_argument('--no-reload-plasma', action='store_true', help='更新后不重载面板，请注销后重新登录')
    args = parser.parse_args()
    if sys.platform != 'linux':
        raise ValueError('请在 Linux 的 KDE 桌面终端运行。')
    if os.geteuid() == 0 and not args.dry_run:
        raise ValueError('请使用普通桌面用户运行，不要使用 sudo。')
    version, source_url, checksum_url = latest_release()
    print(f'最新正式版：v{version}\n源码地址：{source_url}', flush=True)
    if args.dry_run:
        print('检查完成，未执行安装。')
        return

    data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    existing = (data / 'plasma/plasmoids/org.kde.plasma.sptl').exists()
    saved = previous_options(config / 'systemd/user/sptl-bridge.service')
    installer_args = []
    for option in ('plasma', 'splayer_command', 'splayer_config'):
        value = getattr(args, option) or saved.get(option)
        if value:
            installer_args += ['--' + option.replace('_', '-'), value]

    with tempfile.TemporaryDirectory(prefix='sptl-install-') as temporary:
        directory = Path(temporary)
        archive = directory / 'source.tar.gz'
        print('正在下载源码与 SHA-256 校验文件…', flush=True)
        download(source_url, archive)
        checksums = download(checksum_url).decode()
        source_name = source_url.rsplit('/', 1)[1]
        matches = []
        for line in checksums.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip('*') == source_name:
                matches.append(parts[0])
        if len(matches) != 1 or not re.fullmatch(r'[0-9a-fA-F]{64}', matches[0]):
            raise ValueError('SHA-256 清单中缺少或重复列出了源码文件。')
        if hashlib.sha256(archive.read_bytes()).hexdigest() != matches[0].lower():
            raise ValueError('源码 SHA-256 校验失败，未执行安装。')
        root = extract_source(archive, directory / 'source', version)
        if args.reload_plasma:
            installer_args.append('--reload-plasma')
        elif existing and not args.no_reload_plasma and shutil.which('systemctl'):
            # Reuse the release installer's recovery of the current user's session bus.
            sys.path.insert(0, str(root / 'tools'))
            from install import session_environment
            active = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'plasma-plasmashell.service'],
                                    env=session_environment(), timeout=15).returncode == 0
            if active:
                installer_args.append('--reload-plasma')
        if '--reload-plasma' in installer_args:
            print('更新后会短暂重载 Plasma 面板，应用窗口保留。', flush=True)
        print('校验通过，正在' + ('更新' if existing else '安装') + f' SPTL v{version}…', flush=True)
        subprocess.run([sys.executable, str(root / 'tools/install.py'), *installer_args], cwd=root, check=True)
    print(f'SPTL v{version} 安装完成。')
    print(f'请在 SPlayer 插件管理中导入或重新导入 {data / "sptl/zxaBinbina.sptl.js"}，允许 network、control、api 权限。')
    if existing and '--reload-plasma' not in installer_args:
        print('请注销后重新登录，让已添加的小组件加载新版代码。')
    if not existing:
        print('最后在横向 Plasma 面板添加「SPTL — SPlayer 任务栏歌词」。')

try:
    main()
except (ValueError, KeyError, TypeError, IndexError, OSError, tarfile.TarError, subprocess.SubprocessError) as error:
    print('安装失败：' + str(error), file=sys.stderr)
    sys.exit(1)
PY
