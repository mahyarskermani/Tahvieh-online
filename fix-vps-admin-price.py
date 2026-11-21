"""Align the v84 VPS admin product table with storefront starting prices."""
import base64
import json
from pathlib import Path
import re
import shutil
import sys
from tempfile import NamedTemporaryFile

path = Path(sys.argv[1])
prefix = "const assets = "
first, worker = path.read_text(encoding="utf-8").split("\n", 1)
if not first.startswith(prefix) or not first.endswith(";"):
    raise SystemExit("Unexpected worker bundle format.")
assets = json.loads(first[len(prefix):-1])
entry = assets["/admin-demo.html"]
html = base64.b64decode(entry[1]).decode("utf-8")
new_price = "    const price = TahviehPricing.startingPrice(product, prices);"
new_cell = """<td>${price ? TahviehPricing.format(price.current) : 'تماس بگیرید'}</td>"""
old_cell = """<td title="${esc(details)}">${price.toLocaleString('fa-IR')}</td>"""
if new_price in html and new_cell in html:
    print("Price fix already applied.")
    sys.exit(0)

html, count = re.subn(
    r"    const price = product\.body != null \? computedPrice\(product\).*?\n(?=    return )",
    new_price + "\n", html, count=1, flags=re.S
)
if count != 1 or html.count(old_cell) != 1:
    raise SystemExit("Unexpected admin page format. Bundle untouched.")
html = html.replace(old_cell, new_cell, 1)
html = re.sub(r"^function computedPrice\(p, code\) \{[\s\S]*?^\}\n\n", "", html, count=1, flags=re.M)
entry[1] = base64.b64encode(html.encode()).decode()
backup = path.with_suffix(".before-github-price-fix")
if not backup.exists():
    shutil.copy2(path, backup)
with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
    temporary = Path(handle.name)
    handle.write(prefix + json.dumps(assets) + ";\n" + worker)
try:
    shutil.copystat(path, temporary)
    temporary.replace(path)
finally:
    temporary.unlink(missing_ok=True)
print("Price fix applied.")
