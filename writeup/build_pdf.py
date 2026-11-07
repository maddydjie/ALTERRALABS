"""Turn writeup/writeup.md into writeup/writeup.pdf.

Markdown -> a temporary HTML page -> Google Chrome prints that page to PDF.
Run from the repo root: make pdf. Set CHROME to the browser path if yours is elsewhere.
"""
import os
import subprocess
import tempfile

import markdown

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

CSS = """
@page { size: Letter; margin: 0.6in 0.7in; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 8.9pt; line-height: 1.26; color: #1e2430; }
h1 { font-size: 15pt; margin: 0 0 4pt; }
h2 { font-size: 11.5pt; margin: 8pt 0 3pt; break-after: avoid; }
h3 { font-size: 10pt; margin: 6pt 0 3pt; }
p { margin: 3pt 0; }
ul, ol { margin: 3pt 0; padding-left: 15pt; }
li { margin: 1.5pt 0; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0; }
th, td { border-bottom: 1px solid #d8d8d8; padding: 1.8pt 4pt; text-align: left; vertical-align: top; }
th { border-bottom: 1.2px solid #1e2430; }
code { font-family: Menlo, monospace; font-size: 7.9pt; }
.fig { display: block; width: 58%; margin: 3pt auto; }
.pagebreak { page-break-before: always; }
"""

with open("writeup/writeup.md") as f:
    body = markdown.markdown(f.read(), extensions=["tables", "sane_lists"])
page = "<!doctype html><html><head><meta charset='utf-8'><style>%s</style></head><body>%s</body></html>" % (CSS, body)

# The HTML sits in writeup/ so that its ../figures/ image paths resolve
html_path = os.path.abspath("writeup/.writeup_build.html")
with open(html_path, "w") as f:
    f.write(page)
try:
    with tempfile.TemporaryDirectory() as profile:  # separate profile, so an open Chrome window is not disturbed
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--user-data-dir=" + profile, "--print-to-pdf=" + os.path.abspath("writeup/writeup.pdf"),
                        "file://" + html_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
finally:
    os.remove(html_path)
print("wrote writeup/writeup.pdf")
