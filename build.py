#!/usr/bin/env python3
"""Build docs/index.html (served by GitHub Pages) from source.md (an FMHY "Stream Aggregators" list).

Keeps each site's own links and numbered mirrors; drops everything else
(Discord / Telegram / Status / Note / guide links, wiki cross-references).
Run from anywhere: paths resolve from this file.
"""
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "docs"
KRYL = Path.home() / "personal" / "kryl"

LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
TIERS = (("🌟", "top"), ("⭐", "good"))
SECTIONS = (("top", "top picks"), ("good", "recommended"), ("rest", "everything else"))
# Links that are not a place to watch something.
SKIP_HOSTS = ("reddit.com", "github.com", "rentry.co", "discord.", "t.me", "telegram.me")


def parse(line):
    """One markdown bullet -> {tier, sites: [{name, url, mirrors}], tags} or None."""
    body = line.lstrip("* ").strip()
    tier = "rest"
    for mark, name in TIERS:
        if body.startswith(mark):
            tier, body = name, body[len(mark):].strip()
    left, _, right = body.partition(" - ")
    sites = []
    for text, url in LINK.findall(left):
        if any(h in url for h in SKIP_HOSTS):
            continue
        if text.isdigit():
            if not sites:
                raise ValueError(f"mirror before a named site: {line}")
            sites[-1]["mirrors"].append(url)
        else:
            sites.append({"name": text, "url": url, "mirrors": []})
    if not sites:
        return None
    tags = [t.strip() for t in right.split(" / ") if t.strip() and not LINK.search(t)]
    return {"tier": tier, "sites": sites, "tags": tags}


def render_row(entry):
    e = html.escape
    parts = []
    for i, s in enumerate(entry["sites"]):
        cls = "name primary" if i == 0 else "name"
        links = f'<a class="{cls}" href="{e(s["url"])}">{e(s["name"])}</a>'
        links += "".join(
            f'<a class="mirror" href="{e(u)}" title="{e(s["name"])} mirror {n}">{n}</a>'
            for n, u in enumerate(s["mirrors"], start=2)
        )
        parts.append(f'<span class="site">{links}</span>')
    tags = "".join(
        f'<span class="tag{" hot" if t == "4K" else ""}">{e(t)}</span>' for t in entry["tags"]
    )
    search = " ".join([s["name"] for s in entry["sites"]] + entry["tags"]).lower()
    return (
        f'<li data-search="{e(search)}" data-tags="{e("|".join(entry["tags"]).lower())}"><div class="sites">'
        + '<span class="or">or</span>'.join(parts)
        + f'</div><div class="tags">{tags}</div></li>'
    )


def main():
    entries = []
    for line in (ROOT / "source.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("* "):
            entry = parse(line)
            if entry:
                entries.append(entry)

    sections = []
    for key, title in SECTIONS:
        rows = [render_row(x) for x in entries if x["tier"] == key]
        sections.append(
            f'<section data-tier="{key}"><h2><span class="prompt">~/</span>{title}'
            f'<span class="count">{len(rows)}</span></h2><ol>{"".join(rows)}</ol></section>'
        )

    page = (ROOT / "template.html").read_text(encoding="utf-8")
    page = page.replace("{{sections}}", "\n".join(sections))
    page = page.replace("{{total}}", str(len(entries)))

    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(page, encoding="utf-8")
    (SITE / "fonts").mkdir(exist_ok=True)
    for ttf in (KRYL / "fonts").glob("JetBrainsMono-*.ttf"):
        shutil.copy2(ttf, SITE / "fonts" / ttf.name)
    shutil.copy2(KRYL / "kryl-avatar-32.png", SITE / "favicon.png")

    links = sum(1 + len(s["mirrors"]) for x in entries for s in x["sites"])
    print(f"{len(entries)} entries, {links} links -> {SITE / 'index.html'}")


if __name__ == "__main__":
    main()
