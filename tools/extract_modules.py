"""Extract reading copies from the original bundled HTML; do not alter it."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
html = (root / 'app/index.html').read_text('utf-8-sig')
matches = list(re.finditer(r'^// ---- (\d[^\r\n]*?) ----\s*$', html, re.M))
out = root / 'work/source-modules'
out.mkdir(parents=True, exist_ok=True)
for i, match in enumerate(matches):
    label = match.group(1)
    name = re.match(r'[A-Za-z0-9_.-]+', label).group(0)
    end = matches[i + 1].start() if i + 1 < len(matches) else html.index('</script>', match.end())
    (out / name).write_text(html[match.start():end], 'utf-8')
print(f'Extracted {len(matches)} reading copies into {out}')
