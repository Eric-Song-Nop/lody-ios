"""Regenerate committed VectorDrawables from the local licensed SVG sources."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
output = root.parent / 'src/main/res/drawable'
output.mkdir(parents=True, exist_ok=True)
for record in json.loads((root / 'sources.json').read_text())['icons']:
    source = root / f'{record["name"]}.svg'
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError(f'Source checksum changed: {source}')
    svg = ET.fromstring(data)
    x, y, width, height = svg.attrib['viewBox'].split()
    if (x, y) != ('0', '0'):
        raise ValueError('Nonzero SVG origin requires explicit conversion')
    lines = [f'<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="{width}" android:viewportHeight="{height}">']
    for child in svg:
        if not child.tag.endswith('}path') or set(child.attrib) - {'fill', 'd'}:
            raise ValueError('Unsupported SVG feature requires explicit conversion')
        lines.append(f'    <path android:fillColor="#FF000000" android:pathData="{child.attrib["d"]}" />')
    lines.append('</vector>')
    target = output / f'lody_{record["name"].replace("-", "_")}.xml'
    target.write_text('\n'.join(lines) + '\n')
