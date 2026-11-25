#!/usr/bin/env python3
"""Run the public bootstrap with real SPTL source and isolated XDG paths."""
import ast
import hashlib
import fcntl
import io
import json
import os
import pty
import select
import shlex
import subprocess
import tarfile
import tempfile
import termios
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.2.1'
REPO = 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics'
HELPER = '''#!/usr/bin/python3
import json, os, shutil, sys
from pathlib import Path
root = Path(os.environ['SPTL_FIXTURE'])
command = Path(sys.argv[0]).name
args = sys.argv[1:]
with (root/'calls.jsonl').open('a') as stream: stream.write(json.dumps([command,*args])+'\\n')
if command == 'curl':
    url = next(arg for arg in args if arg.startswith('https://'))
    destination = args[args.index('--output')+1] if '--output' in args else None
    if 'api.github.com' in url:
        if os.environ.get('FAIL_API'): sys.exit(22)
        print((root/'release.json').read_text())
    elif url.endswith('/releases/latest'):
        print(os.environ.get('LATEST_URL', 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/tag/v1.2.1'))
    elif '/SHA256SUMS' in url: print((root/'checksums').read_text())
    else: shutil.copyfile(root/'source.tar.gz', destination)
elif command == 'systemctl':
    if os.environ.get('FAIL_INSTALL'): sys.exit(1)
    if os.environ.get('FAIL_STOP') and 'disable' in args: sys.exit(1)
elif command == 'kpackagetool6':
    sys.exit('Helper installer must not invoke kpackagetool')
'''


class Installer(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='sptl bootstrap ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'bin').mkdir()
        for command in ('curl', 'systemctl', 'kpackagetool6'):
            path = self.root / 'bin' / command
            path.write_text(HELPER)
            path.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.root / 'bin') + ':/usr/bin:/bin',
                    'SPTL_FIXTURE': str(self.root), 'KDE_SESSION_VERSION': '6',
                    'XDG_DATA_HOME': str(self.root / 'data'), 'XDG_CONFIG_HOME': str(self.root / 'config'),
                    'XDG_STATE_HOME': str(self.root / 'state'), 'TMPDIR': str(self.root)}
        (self.root / 'calls.jsonl').touch()
        self.write_archive()
        self.release = {'tag_name': 'v' + VERSION, 'draft': False, 'prerelease': False,
                        'assets': [{'name': name, 'browser_download_url': REPO + '/releases/download/v' + VERSION + '/' + name}
                                   for name in (f'sptl-source-{VERSION}.tar.gz', f'SHA256SUMS-{VERSION}')]}
        self.save_release()

    def save_release(self):
        (self.root / 'release.json').write_text(json.dumps(self.release))

    def write_archive(self, extra=None, metadata_version=VERSION):
        source_path = os.environ.get('SPTL_TEST_SOURCE_ARCHIVE')
        if source_path:
            source = Path(source_path)
        else:
            # The old public downloads were removed; keep their source only as a test fixture.
            path = f'public/projects/SPTL/sptl-{VERSION}-source.zip'
            commit = subprocess.check_output(
                ['git', 'log', '--all', '-1', '--format=%H', '--diff-filter=A', '--', path], cwd=ROOT,
            ).decode().strip()
            if not commit:
                raise RuntimeError('Set SPTL_TEST_SOURCE_ARCHIVE when Git history lacks the test source ZIP')
            source = io.BytesIO(subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT))
        with zipfile.ZipFile(source) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        metadata_path = f'SPTL-{VERSION}/plasmoid/metadata.json'
        metadata = json.loads(files[metadata_path])
        metadata['KPlugin']['Version'] = metadata_version
        files[metadata_path] = json.dumps(metadata).encode()
        if extra:
            files.update(extra)
        with tarfile.open(self.root / 'source.tar.gz', 'w:gz') as archive:
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
        checksum = hashlib.sha256((self.root / 'source.tar.gz').read_bytes()).hexdigest()
        (self.root / 'checksums').write_text(f'{checksum}  sptl-source-{VERSION}.tar.gz\n')

    def run_installer(self, *args, **env):
        result = subprocess.run(['/usr/bin/sh', str(ROOT / 'public/projects/SPTL/install.sh'), *args],
                                capture_output=True, text=True, env={**self.env, **env}, timeout=30,
                                start_new_session=True)
        return result

    def run_interactive(self, answer, piped=False):
        master, slave = pty.openpty()
        command = ['sh', '-s'] if piped else ['sh', str(ROOT / 'public/projects/SPTL/install.sh')]
        process = subprocess.Popen(command, stdin=subprocess.PIPE if piped else slave,
                                   stdout=slave, stderr=slave, env=self.env,
                                   start_new_session=True,
                                   preexec_fn=lambda: fcntl.ioctl(1, termios.TIOCSCTTY, 0))
        os.close(slave)
        output = bytearray()
        try:
            if piped:
                process.stdin.write((ROOT / 'public/projects/SPTL/install.sh').read_bytes())
                process.stdin.close()
            os.write(master, answer.encode())
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if select.select([master], [], [], .1)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output.extend(chunk)
                elif process.poll() is not None:
                    break
            returncode = process.wait(timeout=1)
            return subprocess.CompletedProcess(command, returncode, output.decode(errors='replace'), '')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)

    def calls(self):
        return [json.loads(line) for line in (self.root / 'calls.jsonl').read_text().splitlines()]

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_no_install(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / 'data/sptl').exists())
        self.assertFalse(any(call[0] == 'kpackagetool6' for call in self.calls()))
        self.assertFalse(list(self.root.glob('sptl-install-*')))

    def test_real_source_install_update_preserves_settings_and_paths(self):
        result = self.run_installer('--splayer-command', shlex.join(['/path with spaces/SPlayer.AppImage', '--flag']),
                                    '--splayer-config', '/path with spaces/settings.json')
        self.assert_success(result)
        self.assertIn('卸载请再次运行', result.stdout.splitlines()[-1])
        self.assertTrue((self.root / 'data/sptl/helper/sptl/server.py').is_file())
        self.assertFalse((self.root / 'data/sptl/zxaBinbina.sptl.js').exists())
        self.assertFalse((self.root / 'data/plasma/plasmoids/org.kde.plasma.sptl').exists())
        widget = self.root / 'data/plasma/plasmoids/org.kde.plasma.sptl'
        widget.mkdir(parents=True)
        (widget / 'store-file').write_text('store managed')
        plugin = self.root / 'data/sptl/zxaBinbina.sptl.js'
        plugin.write_text('legacy plugin')
        settings = self.root / 'state/sptl/settings.json'
        settings.parent.mkdir(parents=True)
        settings.write_text('{"fontSize": 24}')
        unit = self.root / 'config/systemd/user/sptl-bridge.service'
        previous = unit.read_text()
        result = self.run_installer('--upgrade')
        self.assert_success(result)
        self.assertEqual(settings.read_text(), '{"fontSize": 24}')
        self.assertEqual(unit.read_text(), previous)
        self.assertEqual(plugin.read_text(), 'legacy plugin')
        self.assertEqual((widget / 'store-file').read_text(), 'store managed')
        self.assertFalse(any(call[0].startswith('kpackagetool') for call in self.calls()))
        self.assertNotIn(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'], self.calls())
        subprocess.run(['/usr/bin/python3', '-c', "from sptl.model import DEFAULTS; assert DEFAULTS['lyricMode'] == 'double'"],
                       cwd=self.root / 'data/sptl/helper', check=True)
        self.assertFalse(list(self.root.glob('sptl-install-*')))

    def test_piped_script_runs_with_cli_options(self):
        result = subprocess.run(['sh', '-s', '--', '--dry-run'],
                                input=(ROOT / 'public/projects/SPTL/install.sh').read_text(),
                                capture_output=True, text=True, env=self.env, timeout=30)
        self.assert_success(result)
        self.assertIn('v1.2.1', result.stdout)
        self.assertFalse((self.root / 'data').exists())

    def test_api_rate_limit_falls_back_to_same_latest_release(self):
        self.assert_success(self.run_installer(FAIL_API='1'))

    def test_redirect_to_other_repository_is_rejected(self):
        self.assert_no_install(self.run_installer(FAIL_API='1', LATEST_URL='https://github.com/other/repo/releases/tag/v1.2.1'))

    def test_prerelease_is_rejected(self):
        self.release['prerelease'] = True
        self.save_release()
        self.assert_no_install(self.run_installer())

    def test_missing_or_foreign_asset_is_rejected(self):
        self.release['assets'][0]['browser_download_url'] = 'https://example.com/source.tar.gz'
        self.save_release()
        self.assert_no_install(self.run_installer())

    def test_corrupt_checksum_and_duplicates_are_rejected(self):
        (self.root / 'checksums').write_text('0' * 64 + f'  sptl-source-{VERSION}.tar.gz\n')
        self.assert_no_install(self.run_installer())
        self.write_archive()
        checksums = self.root / 'checksums'
        checksums.write_text(checksums.read_text() * 2)
        self.assert_no_install(self.run_installer())

    def test_unsafe_archive_and_version_mismatch_are_rejected(self):
        self.write_archive(extra={'../escaped.py': b'unsafe'})
        self.assert_no_install(self.run_installer())
        self.assertFalse((self.root / 'escaped.py').exists())
        self.write_archive(metadata_version='9.9.9')
        self.assert_no_install(self.run_installer())

    def test_install_failure_is_reported_without_success_message(self):
        result = self.run_installer(FAIL_INSTALL='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('安装完成', result.stdout)
        self.assertFalse(list(self.root.glob('sptl-install-*')))

    def test_legacy_flags_never_reload_or_install_widgets(self):
        self.assert_success(self.run_installer())
        (self.root / 'calls.jsonl').write_text('')
        self.assert_success(self.run_installer('--upgrade', '--plasma', '5', '--reload-plasma'))
        self.assertNotIn(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'], self.calls())
        self.assertFalse(any(call[0].startswith('kpackagetool') for call in self.calls()))

    def test_legacy_release_installer_is_not_executed(self):
        self.write_archive(extra={f'SPTL-{VERSION}/tools/install.py': b'raise RuntimeError("full installer must not run")'})
        self.assert_success(self.run_installer())

    def test_only_helper_files_are_extracted_to_disk(self):
        script = ROOT / 'public/projects/SPTL/install.sh'
        source = script.read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        module = ast.parse(source)
        self.assertIsInstance(module.body[-1], ast.Try)
        module.body.pop()  # Inspect extraction without running the interactive entry point.
        namespace = {}
        exec(compile(module, str(script), 'exec'), namespace)
        extracted = namespace['extract_source'](self.root / 'source.tar.gz', self.root / 'extracted', VERSION)
        files = [path.relative_to(extracted) for path in extracted.rglob('*') if path.is_file()]
        self.assertTrue(files)
        self.assertTrue(all(path.parts[0] in ('helper', 'shared', 'LICENSE', 'THIRD_PARTY.md') for path in files))
        for name in ('plasmoid', 'plugin', 'tools', 'dist', 'zxaBinbina.sptl.js'):
            self.assertFalse((extracted / name).exists(), name)

    def test_existing_install_prompts_for_upgrade(self):
        self.assert_success(self.run_installer())
        result = self.run_interactive('1\n')
        self.assert_success(result)
        self.assertIn('1. 升级', result.stdout)
        self.assertIn('2. 卸载', result.stdout)
        self.assertIn('正在更新', result.stdout)
        self.assertIn('卸载请再次运行', result.stdout)

    def test_piped_script_can_select_uninstall_from_the_terminal(self):
        self.assert_success(self.run_installer())
        (self.root / 'calls.jsonl').write_text('')
        result = self.run_interactive('2\n', piped=True)
        self.assert_success(result)
        self.assertIn('2. 卸载', result.stdout)
        self.assertIn('辅助程序已卸载', result.stdout)
        self.assertFalse((self.root / 'data/sptl/helper').exists())
        self.assertFalse((self.root / 'config/systemd/user/sptl-bridge.service').exists())
        self.assertFalse(any(call[0] == 'curl' for call in self.calls()))

    def test_cancel_and_missing_terminal_leave_installation_unchanged(self):
        self.assert_success(self.run_installer())
        unit = self.root / 'config/systemd/user/sptl-bridge.service'
        original = unit.read_bytes()
        (self.root / 'calls.jsonl').write_text('')
        self.assert_success(self.run_interactive('0\n'))
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--upgrade', result.stderr)
        self.assertIn('--uninstall', result.stderr)
        self.assertEqual(unit.read_bytes(), original)
        self.assertEqual(self.calls(), [])

    def test_offline_uninstall_preserves_store_files_and_settings(self):
        self.assert_success(self.run_installer())
        widget = self.root / 'data/plasma/plasmoids/org.kde.plasma.sptl'
        widget.mkdir(parents=True)
        (widget / 'store-file').write_text('store managed')
        plugin = self.root / 'data/sptl/zxaBinbina.sptl.js'
        plugin.write_text('legacy plugin')
        settings = self.root / 'state/sptl/settings.json'
        settings.parent.mkdir(parents=True)
        settings.write_text('{"fontSize": 24}')
        (self.root / 'calls.jsonl').write_text('')
        (self.root / 'bin/curl').unlink()
        (self.root / 'bin/python3').symlink_to('/usr/bin/python3')
        result = self.run_installer('--uninstall', PATH=str(self.root / 'bin'))
        self.assert_success(result)
        self.assertFalse((self.root / 'data/sptl/helper').exists())
        self.assertFalse((self.root / 'data/sptl/shared').exists())
        self.assertEqual(plugin.read_text(), 'legacy plugin')
        self.assertEqual((widget / 'store-file').read_text(), 'store managed')
        self.assertEqual(settings.read_text(), '{"fontSize": 24}')
        self.assertIn(['systemctl', '--user', 'disable', '--now', 'sptl-bridge.service'], self.calls())
        self.assert_success(self.run_installer('--uninstall', PATH=str(self.root / 'bin')))

    def test_failed_service_stop_keeps_helper_files(self):
        self.assert_success(self.run_installer())
        result = self.run_installer('--uninstall', FAIL_STOP='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('辅助程序已卸载', result.stdout)
        self.assertTrue((self.root / 'data/sptl/helper/sptl/server.py').exists())
        self.assertTrue((self.root / 'config/systemd/user/sptl-bridge.service').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
