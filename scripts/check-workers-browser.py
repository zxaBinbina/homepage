"""Run existing regressions against isolated Workers and Vite previews."""
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

worker = os.environ.get('HOMEPAGE_WORKER_TEST_URL', 'http://127.0.0.1:8788')
dev = os.environ.get('HOMEPAGE_DEV_TEST_URL', 'http://127.0.0.1:5283')
logs = Path('artifacts/rooms/regressions'); logs.mkdir(parents=True, exist_ok=True)
checks = [
    ('check-games-classics.py', worker),
    ('check-games-chess-go.py', worker), ('check-games-doudizhu.py', worker),
    ('check-games-junqi.py', worker), ('check-games-junqi-challenge.py', worker),
    ('check-games-fullscreen.py', worker), ('check-sharing.py', worker),
    ('check-seo.py', worker), ('check-errors.py', worker), ('check-loading.py', worker),
    ('check-theme.py', worker), ('check-theme-motion.py', worker),
    ('check-office-editor-browser.py', worker), ('check-pdf-convert-browser.py', worker),
    ('check-browser.py', dev), ('check-navigation.py', dev),
    ('check-games-motion.py', dev), ('check-games-options-motion.py', dev),
    ('check-games-classics-motion.py', dev), ('check-games-chess-go-motion.py', dev),
    ('check-segmented-controls.py', dev), ('check-disclosures.py', dev),
    ('check-games-browser.py', worker),
]
if len(sys.argv) > 1:
    by_name = dict(checks)
    checks = [(name, by_name[name]) for name in dict.fromkeys(sys.argv[1:]) if name in by_name]
    if not checks: raise SystemExit('No matching regression names.')
for url in {item[1] for item in checks}:
    try:
        with urllib.request.urlopen(url + '/game', timeout=5) as response:
            if response.status != 200: raise RuntimeError('Unexpected preview status')
    except Exception as error:
        raise SystemExit('Preview unavailable at ' + url + ': ' + str(error))
def run(item):
    name, url = item
    with urllib.request.urlopen(url + '/game', timeout=5) as response:
        if response.status != 200: raise RuntimeError('Preview unavailable before ' + name)
    env = {**os.environ, 'HOMEPAGE_TEST_URL': url}
    result = subprocess.run(['python3', 'scripts/' + name], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (logs / (name + '.log')).write_text(result.stdout)
    print(name + ': ' + ('passed' if result.returncode == 0 else 'FAILED; see ' + str(logs / (name + '.log'))), flush=True)
    return name if result.returncode else None
failures = [name for name in map(run, checks) if name]
if failures: raise SystemExit('Failed checks: ' + ', '.join(failures))
print('Workers migration and affected game/navigation/theme/Office regressions: passed.')
