"""Three repeated native scroll runs; report performance without a fake FPS gate."""
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
from driver import UI

ui = UI(sys.argv[1], sys.argv[2])
container = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', ui.udid, 'app.innei.lody', 'data'], text=True).strip())
reports = []
for run in range(3):
    existing = set((container / 'tmp').glob('lody-chat-performance-*.json'))
    ui.axe('tap', '--label', 'Run Chat Benchmark', '--post-delay', '.2')
    deadline = time.monotonic() + 110
    while not (paths := set((container / 'tmp').glob('lody-chat-performance-*.json')) - existing):
        assert time.monotonic() < deadline, 'Native benchmark did not complete'
        time.sleep(1)
    path = next(iter(paths))
    report = json.loads(path.read_text())
    shutil.copy2(path, ui.output / f'run-{run + 1}.json')
    assert report['entries'] == 10_000 and report['rows'] == 10_000, 'Incomplete dataset'
    assert 20 <= report['seconds'] < 30, 'Incomplete measurement interval'
    samples = report['samples']
    offsets = [s['offset'] for s in samples]
    assert max(offsets) - min(offsets) > 70_000, 'Scroll did not cover the requested distance'
    deltas = [b - a for a, b in zip(offsets, offsets[1:])]
    assert sum(d < -1 for d in deltas) > 20 and sum(d > 1 for d in deltas) > 20, 'Missing bidirectional motion'
    assert all(s['mib'] > 0 for s in report['memory']), 'Memory sampling failed'
    assert abs(report['fps'] - len(samples) / report['seconds']) < .001
    intervals = sorted(s['dt'] * 1000 for s in samples)
    report['p95FrameMs'] = intervals[int((len(intervals) - 1) * .95)]
    report['maxFrameMs'] = max(intervals)
    report['overBudgetPercent'] = 100 * sum(s['dt'] > s['budget'] * 1.5 for s in samples) / len(samples)
    report['visitedSectionRange'] = [min(s['firstSection'] for s in samples), max(s['lastSection'] for s in samples)]
    reports.append({k: v for k, v in report.items() if k not in ['samples', 'memory']})
    ui.capture(f'run-{run + 1}-complete')
summary = {'runs': reports, 'medianFPS': statistics.median(r['fps'] for r in reports)}
(ui.output / 'performance-summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
