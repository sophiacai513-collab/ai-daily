#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日 AI 行业简报 → 静态站点生成器
用法: python3 generate.py <daily_md_path> <site_dir>

- 解析 YYYY-MM-DD-ai-daily.md
- 生成 YYYY-MM-DD.html（当天独立页，永久保留）
- 重新生成 index.html（最新一期 + 往期列表，固定网址入口）
- 往期列表通过扫描 site_dir 下所有 YYYY-MM-DD.html 自动累积，绝不覆盖历史
"""
import re
import os
import sys
import glob
import datetime

CAT_CLASS = {
    "产品": "product",
    "技术": "tech",
    "商业": "biz",
    "待核验": "verify",
}
CAT_LABEL = {
    "产品": "产品",
    "技术": "技术",
    "商业": "商业",
    "待核验": "待核验",
}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def parse_md(path: str):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")

    m = re.search(r"每日 AI 行业简报\s+(\d{4}-\d{2}-\d{2})", text)
    date = m.group(1) if m else datetime.date.today().isoformat()

    meta_lines = [l[1:].strip() for l in lines if l.startswith(">")]
    meta = " · ".join([x for x in meta_lines if x])

    sections = []
    sources = []
    cur_name = None
    cur_entries = []
    cur_entry = None
    mode = None

    for line in lines:
        if line.startswith("## "):
            # flush any pending entry into the previous section first
            if cur_entry is not None:
                cur_entries.append(cur_entry)
                cur_entry = None
            name = line[3:].strip()
            if name == "来源清单":
                mode = "sources"
                if cur_name is not None:
                    sections.append((cur_name, cur_entries))
                cur_name, cur_entries = None, []
            else:
                mode = "section"
                if cur_name is not None:
                    sections.append((cur_name, cur_entries))
                cur_name = name
                cur_entries = []
            continue

        if mode == "sources":
            sm = re.match(r"\d+\.\s*\[(.+?)\]\((.+?)\)", line.strip())
            if sm:
                sources.append((sm.group(1), sm.group(2)))
            continue

        if mode == "section":
            if line.startswith("### "):
                if cur_entry is not None:
                    cur_entries.append(cur_entry)
                cur_entry = {
                    "title": line[4:].strip(),
                    "summary": "",
                    "source": "",
                    "time": "",
                    "link": "",
                }
            elif re.match(r"-\s*\*\*", line):
                km = re.match(r"-\s*\*\*(.+?)\*\*[:：]\s*(.*)", line)
                if km and cur_entry is not None:
                    key = km.group(1).strip()
                    val = km.group(2).strip()
                    if key == "摘要":
                        cur_entry["summary"] = val
                    elif key == "来源":
                        cur_entry["source"] = val
                    elif key == "时间":
                        cur_entry["time"] = val
                    elif key == "链接":
                        cur_entry["link"] = val
    if cur_entry is not None:
        cur_entries.append(cur_entry)
    if cur_name is not None:
        sections.append((cur_name, cur_entries))

    return date, meta, sections, sources


def render_entry(e: dict) -> str:
    link = e["link"]
    link_html = (
        f'<a class="link" href="{esc(link)}" target="_blank" rel="noopener">'
        f'{esc(link)}</a>'
        if link
        else ""
    )
    meta_parts = []
    if e["source"]:
        meta_parts.append(f"<b>来源</b> {esc(e['source'])}")
    if e["time"]:
        meta_parts.append(f"<b>时间</b> {esc(e['time'])}")
    meta_html = f'<div class="meta">{" · ".join(meta_parts)}</div>' if meta_parts else ""
    return f"""      <div class="card">
        <h3>{esc(e['title'])}</h3>
        <div class="summary">{esc(e['summary'])}</div>
        {meta_html}
        {link_html}
      </div>"""


def render_brief(date: str, meta: str, sections: list, sources: list) -> str:
    out = []
    # category nav
    cats = [s[0] for s in sections]
    nav = "".join(
        f'<a href="#cat-{esc(c)}">{CAT_LABEL.get(c, c)}</a>' for c in cats
    )
    out.append(f'    <nav class="cat-nav">{nav}</nav>')

    for idx, (name, entries) in enumerate(sections):
        cls = CAT_CLASS.get(name, "")
        label = CAT_LABEL.get(name, name)
        cards = "\n".join(render_entry(e) for e in entries)
        out.append(
            f'    <section class="section {cls}" id="cat-{esc(name)}">\n'
            f'      <div class="section-title">{label}</div>\n{cards}\n'
            f"    </section>"
        )

    if sources:
        items = "\n".join(
            f'        <li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>'
            for t, u in sources
        )
        out.append(
            '    <section class="sources">\n'
            "      <h2>来源清单</h2>\n"
            f"      <ol>\n{items}\n      </ol>\n"
            "    </section>"
        )
    return "\n".join(out)


def page_shell(date: str, meta: str, inner: str, is_index: bool) -> str:
    home_link = "" if is_index else '<a class="home" href="index.html">← 返回首页</a>'
    brand_href = "index.html" if not is_index else "index.html"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>每日 AI 行业简报 {date}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="topbar"><div class="wrap">
  <a class="brand" href="index.html">AI 行业简报</a>
  {home_link}
</div></div>
<header class="site-header"><div class="wrap">
  <h1>每日 AI 行业简报</h1>
  <div class="sub">{esc(meta)}</div>
  <div class="date-badge">{date}</div>
</div></header>
<main class="wrap">
{inner}
</main>
<div class="foot">由 WorkBuddy 自动生成 · 每日 08:00 更新</div>
</body>
</html>
"""


def build_archive(site_dir: str, latest_date: str) -> str:
    files = glob.glob(os.path.join(site_dir, "????-??-??.html"))
    dates = []
    for f in files:
        base = os.path.basename(f)
        d = base[:-5]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            dates.append(d)
    dates = sorted(set(dates), reverse=True)
    items = []
    for d in dates:
        if d == latest_date:
            continue
        items.append(
            f'      <li><a href="{d}.html"><span>简报</span>'
            f'<span class="d">{d}</span></a></li>'
        )
    if not items:
        return ""
    return (
        '    <section class="archive">\n'
        "      <h2>往期回顾</h2>\n      <ul>\n"
        + "\n".join(items)
        + "\n      </ul>\n    </section>"
    )


def main():
    if len(sys.argv) < 3:
        print("usage: generate.py <daily_md> <site_dir>")
        sys.exit(1)
    md_path = sys.argv[1]
    site_dir = sys.argv[2]
    os.makedirs(site_dir, exist_ok=True)

    date, meta, sections, sources = parse_md(md_path)

    # dated page
    inner = render_brief(date, meta, sections, sources)
    dated_html = page_shell(date, meta, inner, is_index=False)
    with open(os.path.join(site_dir, f"{date}.html"), "w", encoding="utf-8") as f:
        f.write(dated_html)

    # index (latest + archive)
    archive_html = build_archive(site_dir, date)
    index_inner = inner + "\n" + archive_html if archive_html else inner
    index_html = page_shell(date, meta, index_inner, is_index=True)
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"OK: generated {date}.html and index.html (latest={date})")


if __name__ == "__main__":
    main()
