#!/usr/bin/env python3
"""Run the public bootstrap with real SPTL source and isolated XDG paths."""
import hashlib
import io
import json
import os
import shlex
import subprocess
import tarfile
import tempfile
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
    if 'is-active' in args and os.environ.get('INACTIVE_SHELL'): sys.exit(3)
elif command == 'kpackagetool6':
    if os.environ.get('FAIL_INSTALL'): sys.exit(1)
    source = Path(args[-1])
    target = Path(os.environ['XDG_DATA_HOME'])/'plasma/plasmoids/org.kde.plasma.sptl'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(source,target)
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
        with zipfile.ZipFile(ROOT / f'public/projects/SPTL/sptl-{VERSION}-source.zip') as archive:
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
        result = subprocess.run(['sh', str(ROOT / 'public/projects/SPTL/install.sh'), *args],
                                capture_output=True, text=True, env={**self.env, **env}, timeout=30)
        return result

    def calls(self):
        return [json.loads(line) for line in (self.root / 'calls.jsonl').read_text().splitlines()]

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_no_install(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / 'data/sptl').exists())
        self.assertFalse(any(call[0] == 'kpackagetool6' for call in self.calls()))

    def test_real_source_install_update_preserves_settings_and_paths(self):
        result = self.run_installer('--splayer-command', shlex.join(['/path with spaces/SPlayer.AppImage', '--flag']),
                                    '--splayer-config', '/path with spaces/settings.json')
        self.assert_success(result)
        self.assertTrue((self.root / 'data/sptl/helper/sptl/server.py').is_file())
        plugin = (self.root / 'data/sptl/zxaBinbina.sptl.js').read_text()
        self.assertIn('@version 1.2.1', plugin)
        self.assertIn('@apiLevel 5', plugin)
        settings = self.root / 'state/sptl/settings.json'
        settings.parent.mkdir(parents=True)
        settings.write_text('{"fontSize": 24}')
        unit = self.root / 'config/systemd/user/sptl-bridge.service'
        previous = unit.read_text()
        result = self.run_installer()
        self.assert_success(result)
        self.assertEqual(settings.read_text(), '{"fontSize": 24}')
        self.assertEqual(unit.read_text(), previous)
        self.assertTrue(any('--upgrade' in call for call in self.calls()))
        self.assertIn(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'], self.calls())
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

    def test_update_can_skip_reload(self):
        self.assert_success(self.run_installer())
        (self.root / 'calls.jsonl').write_text('')
        self.assert_success(self.run_installer('--no-reload-plasma'))
        self.assertNotIn(['systemctl', '--user', 'restart', 'plasma-plasmashell.service'], self.calls())


if __name__ == '__main__':
    unittest.main(verbosity=2)
