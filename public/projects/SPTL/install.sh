#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Download and verify the latest SPTL release, then install only its helper.
set -eu
command -v python3 >/dev/null 2>&1 || { printf '%s\n' '请先安装 Python 3.10+。' >&2; exit 1; }
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
        metadata_members = [member for member in members if member.isfile()
                            and PurePosixPath(member.name).parts[-2:] == ('plasmoid', 'metadata.json')]
        if len(metadata_members) != 1:
            raise ValueError('源码归档缺少唯一的版本元数据。')
        metadata_member = metadata_members[0]
        with archive.extractfile(metadata_member) as source:
            metadata = json.load(source)
        if metadata['KPlugin']['Version'] != version:
            raise ValueError('源码中的版本与最新 Release 不一致。')
        root_parts = PurePosixPath(metadata_member.name).parts[:-2]
        root = destination.joinpath(*root_parts)
        extracted = set()
        for member in members:
            parts = PurePosixPath(member.name).parts
            if parts[:len(root_parts)] != root_parts:
                continue
            relative = parts[len(root_parts):]
            if not relative or not (relative[0] in ('helper', 'shared') or
                                    relative in (('LICENSE',), ('THIRD_PARTY.md',))):
                continue
            if relative in extracted:
                raise ValueError('源码归档包含重复的辅助程序路径。')
            extracted.add(relative)
            path = root.joinpath(*relative)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, path.open('wb') as target:
                    shutil.copyfileobj(source, target)
    if not all((root / name).is_file() for name in
               ('helper/sptl/server.py', 'shared/settings.json', 'LICENSE', 'THIRD_PARTY.md')):
        raise ValueError('源码归档缺少辅助程序、共享设置或许可证。')
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

def session_environment():
    environment = dict(os.environ)
    runtime = Path(f'/run/user/{os.getuid()}')
    if not environment.get('XDG_RUNTIME_DIR') and runtime.is_dir() and runtime.stat().st_uid == os.getuid():
        environment['XDG_RUNTIME_DIR'] = str(runtime)
    runtime_dir = environment.get('XDG_RUNTIME_DIR')
    if not environment.get('DBUS_SESSION_BUS_ADDRESS') and runtime_dir:
        bus = Path(runtime_dir) / 'bus'
        if bus.is_socket() and bus.stat().st_uid == os.getuid():
            environment['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=' + str(bus)
    return environment

def unit_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'

def install_helper(root, data, config, options):
    systemctl = shutil.which('systemctl')
    if not systemctl:
        raise ValueError('请在具有 systemd 用户会话的桌面终端运行。')
    environment = session_environment()
    manager = subprocess.run([systemctl, '--user', 'show-environment'], env=environment,
                             capture_output=True, timeout=30)
    if manager.returncode:
        raise ValueError('无法连接 systemd 用户会话，请在桌面终端运行。')
    install = data / 'sptl'
    install.mkdir(parents=True, exist_ok=True)
    for directory in ('helper', 'shared'):
        target = install / directory
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(root / directory, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('LICENSE', 'THIRD_PARTY.md'):
        shutil.copy2(root / name, install / name)
    command = [sys.executable, '-m', 'sptl.server']
    if options.get('splayer_config'):
        command += ['--splayer-config', str(Path(options['splayer_config']).expanduser().resolve())]
    if options.get('splayer_command'):
        command += ['--splayer-command', *shlex.split(options['splayer_command'])]
    unit = config / 'systemd/user/sptl-bridge.service'
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(
        '[Unit]\nDescription=SPlayer Plasma Taskbar Lyrics bridge\nAfter=graphical-session.target\n'
        '\n[Service]\nType=simple\nWorkingDirectory=' + str(install / 'helper').replace('%', '%%') +
        '\nExecStart=' + ' '.join(unit_quote(value) for value in command) +
        '\nRestart=on-failure\nRestartSec=2\nUMask=0077\n'
        '\n[Install]\nWantedBy=default.target\n'
    )
    for action in (['daemon-reload'], ['enable', '--now', 'sptl-bridge.service'], ['restart', 'sptl-bridge.service']):
        subprocess.run([systemctl, '--user', *action], env=environment, check=True, timeout=30)

def choose_installed_action():
    try:
        reader = open('/dev/tty', 'r', encoding='utf-8')
        writer = open('/dev/tty', 'w', encoding='utf-8')
    except OSError as error:
        raise ValueError('已安装辅助程序。请在终端中再次运行，或指定 --upgrade 升级、--uninstall 卸载。') from error
    with reader, writer:
        writer.write('检测到已安装 SPTL 辅助程序。\n1. 升级\n2. 卸载\n0. 取消\n')
        while True:
            writer.write('请选择 [1/2/0]：')
            writer.flush()
            try:
                answer = reader.readline()
            except KeyboardInterrupt:
                return 'cancel'
            if not answer:
                return 'cancel'
            answer = answer.strip()
            if answer in ('1', '升级'):
                return 'upgrade'
            if answer in ('2', '卸载'):
                return 'uninstall'
            if answer in ('0', '取消'):
                return 'cancel'
            writer.write('请输入 1、2 或 0。\n')

def uninstall_helper(data, config):
    systemctl = shutil.which('systemctl')
    if not systemctl:
        raise ValueError('卸载需要 systemctl 和可用的 systemd 用户会话。')
    environment = session_environment()
    subprocess.run([systemctl, '--user', 'show-environment'], env=environment,
                   capture_output=True, check=True, timeout=30)
    unit = config / 'systemd/user/sptl-bridge.service'
    if unit.exists() or unit.is_symlink():
        subprocess.run([systemctl, '--user', 'disable', '--now', 'sptl-bridge.service'],
                       env=environment, check=True, timeout=30)
    install = data / 'sptl'
    unit.unlink(missing_ok=True)
    for name in ('helper', 'shared'):
        path = install / name
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    for name in ('LICENSE', 'THIRD_PARTY.md'):
        (install / name).unlink(missing_ok=True)
    if install.is_dir() and not any(install.iterdir()):
        install.rmdir()
    subprocess.run([systemctl, '--user', 'daemon-reload'], env=environment, check=True, timeout=30)
    print('SPTL 辅助程序已卸载。小组件、SPlayer 插件和共享设置已保留。')
    print('需要重新安装时，请再次运行脚本。')

def main():
    parser = argparse.ArgumentParser(description='安装 SPTL 辅助程序；已安装时选择升级或卸载，无需 sudo。')
    parser.add_argument('--dry-run', action='store_true', help='只读取最新版本与下载地址，不安装')
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('--upgrade', action='store_true', help='跳过菜单，直接安装或升级辅助程序')
    action_group.add_argument('--uninstall', action='store_true', help='卸载辅助程序，保留小组件、插件与共享设置')
    parser.add_argument('--plasma', choices=('5', '6'), help=argparse.SUPPRESS)
    parser.add_argument('--splayer-command', help='SPlayer 启动命令，例如 AppImage 路径')
    parser.add_argument('--splayer-config', help='SPlayer 的 settings.json 路径')
    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument('--reload-plasma', action='store_true', help=argparse.SUPPRESS)
    reload_group.add_argument('--no-reload-plasma', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.dry_run and args.uninstall:
        parser.error('--dry-run 不能与 --uninstall 同时使用')
    if sys.platform != 'linux':
        raise ValueError('请在 Linux 的 KDE 桌面终端运行。')
    if os.geteuid() == 0 and not args.dry_run:
        raise ValueError('请使用普通桌面用户运行，不要使用 sudo。')
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    unit = config / 'systemd/user/sptl-bridge.service'
    existing = (data / 'sptl/helper').is_dir() or unit.exists() or unit.is_symlink()
    action = 'uninstall' if args.uninstall else 'upgrade'
    if existing and not (args.upgrade or args.uninstall or args.dry_run):
        action = choose_installed_action()
    if action == 'cancel':
        print('已取消，未修改安装。')
        return
    if action == 'uninstall':
        if existing:
            uninstall_helper(data, config)
        else:
            print('未检测到已安装的 SPTL 辅助程序。')
        return
    if not shutil.which('curl'):
        raise ValueError('安装或升级需要 curl，请先安装。')
    version, source_url, checksum_url = latest_release()
    print(f'最新正式版：v{version}\n源码地址：{source_url}', flush=True)
    if args.dry_run:
        print('检查完成，未执行安装。')
        return

    saved = previous_options(config / 'systemd/user/sptl-bridge.service')
    options = {option: getattr(args, option) if getattr(args, option) is not None else saved.get(option)
               for option in ('splayer_command', 'splayer_config')}

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
        print('校验通过，正在' + ('更新' if existing else '安装') + f' SPTL v{version} 辅助程序…', flush=True)
        # Released 1.2.1 has a full installer; deploy helper files directly instead of executing it.
        install_helper(root, data, config, options)
    print(f'SPTL v{version} 辅助程序安装完成。')
    print('KDE 小组件请从面板的「添加或管理小部件 → 获取新小部件」入口安装。')
    print('打开 SPlayer 的全局设置 → 插件管理 → 插件市场，找到「SPTL 任务栏歌词」，点击安装。')
    print('卸载请再次运行此脚本，并选择「卸载」。')

try:
    main()
except (ValueError, KeyError, TypeError, IndexError, OSError, tarfile.TarError, subprocess.SubprocessError) as error:
    print('操作失败：' + str(error), file=sys.stderr)
    sys.exit(1)
PY
