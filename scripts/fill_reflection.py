"""Fill the Reflection tab of `output/desk_tickets.html`.

Written in the first person because it is the owner's reflection, not the
assistant's. Every claim is tied to something on the Tickets or Cash tabs of
this same page, or to a figure in `output/resolved_tickets.json` /
`output/audit_trail.json` -- the costs below are real token counts from the
run, not estimates.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "output/desk_tickets.html"

from reflection_text import REFLECTION  # noqa: E402



def main() -> int:
    html = PAGE.read_text(encoding="utf-8")

    start = html.index('<section class="panel" id="reflection">')
    end = html.index("</section>", start)
    html = (
        html[:start]
        + '<section class="panel" id="reflection">\n'
        + REFLECTION
        + "\n"
        + html[end:]
    )

    html = html.replace(
        '<button role="tab" aria-selected="false" data-tab="reflection">Reflection<span class="sub">later</span></button>',
        '<button role="tab" aria-selected="false" data-tab="reflection">Reflection<span class="sub">what I learned</span></button>',
    )

    PAGE.write_text(html, encoding="utf-8")
    print(f"filled the Reflection tab in {PAGE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
