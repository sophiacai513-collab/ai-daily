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
                    "title": re.sub(r'^(?:\d+|[A-Za-z])\.\s*', '', line[4:].strip()),
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


def render_entry(e: dict, idx: int) -> str:
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
    return f"""      <div class="card" id="item-{idx}">
        <h3>{esc(e['title'])}</h3>
        <div class="summary">{esc(e['summary'])}</div>
        {meta_html}
        {link_html}
      </div>"""


def render_brief(date: str, meta: str, sections: list, sources: list, is_index: bool = True) -> str:
    out = []
    # category nav
    cats = [s[0] for s in sections]
    nav = "".join(
        f'<a href="#cat-{esc(c)}">{CAT_LABEL.get(c, c)}</a>' for c in cats
    )
    archive_href = "#archive" if is_index else "index.html#archive"
    nav += f'<a class="nav-archive" href="{archive_href}">往期</a>'
    out.append(f'    <nav class="cat-nav">{nav}</nav>')

    # flat list with a global index (for digest links + card anchors)
    flat = []
    gi = 0
    for name, entries in sections:
        for e in entries:
            gi += 1
            flat.append((name, e, gi))
    idx_of = {id(e): gi for name, e, gi in flat}

    # digest overview list: one-line headline per item, click jumps to detail
    if flat:
        items = []
        for name, e, gi in flat:
            cls = CAT_CLASS.get(name, "")
            items.append(
                f'      <li><a href="#item-{gi}">'
                f'<span class="dot {cls}"></span>'
                f'<span class="t">{esc(e["title"])}</span></a></li>'
            )
        out.append(
            '    <div class="digest" id="digest">\n'
            '      <div class="digest-title">速览清单 · 点击跳转到详情</div>\n'
            '      <ul>\n' + "\n".join(items) + "\n      </ul>\n"
            "    </div>"
        )

    for name, entries in sections:
        cls = CAT_CLASS.get(name, "")
        label = CAT_LABEL.get(name, name)
        cards = "\n".join(render_entry(e, idx_of[id(e)]) for e in entries)
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
<button class="to-top" id="toTop" type="button" aria-label="回到顶部">&#8593;</button>
<script>
(function(){{
  function findAnchor(node){{
    node = node && node.nodeType !== 1 ? node.parentNode : node;
    while(node && node !== document){{
      if(node.tagName === 'A'){{
        var href = node.getAttribute('href') || '';
        if(href.charAt(0) === '#') return node;
      }}
      node = node.parentNode;
    }}
    return null;
  }}
  function offset(){{
    var tb = document.querySelector('.topbar');
    var cn = document.querySelector('.cat-nav');
    var h = tb ? tb.offsetHeight : 0;
    if(cn) h += cn.offsetHeight;
    return h + 10;
  }}
  document.addEventListener('click', function(e){{
    var a = findAnchor(e.target);
    if(!a) return;
    var href = a.getAttribute('href');
    var id = href.slice(1);
    if(!id) return;
    var el = document.getElementById(id);
    if(!el) return;
    e.preventDefault();
    var top = el.getBoundingClientRect().top + (window.pageYOffset || window.scrollY) - offset();
    if(window.scrollTo){{ window.scrollTo({{top: Math.max(0, top), behavior: 'smooth'}}); }}
    else {{ window.scrollTo(0, Math.max(0, top)); }}
  }});
  var btn = document.getElementById('toTop');
  if(btn){{
    function onScroll(){{
      var oneScreen = window.innerHeight || 600;
      if((window.pageYOffset || window.scrollY) > oneScreen) btn.className = 'to-top show';
      else btn.className = 'to-top';
    }}
    window.addEventListener('scroll', onScroll, false);
    btn.addEventListener('click', function(){{
      if(window.scrollTo) window.scrollTo({{top: 0, behavior: 'smooth'}});
      else window.scrollTo(0, 0);
    }});
    onScroll();
  }}
}})();
</script>
</body>
</html>
"""


SEARCH_SCRIPT = """    <script>
    (function(){
      var inp = document.getElementById('archive-search');
      if(!inp) return;
      var groups = document.querySelectorAll('.archive-list > li.month-group');
      inp.addEventListener('input', function(){
        var q = inp.value.trim().toLowerCase();
        groups.forEach(function(g){
          var lis = g.querySelectorAll('ul > li[data-search]');
          var vis = 0;
          lis.forEach(function(li){
            var s = (li.getAttribute('data-search')||'').toLowerCase();
            var hit = !q || s.indexOf(q) !== -1;
            li.style.display = hit ? '' : 'none';
            if(hit) vis++;
          });
          g.style.display = vis ? '' : 'none';
        });
      });
    })();
    </script>"""


def extract_headlines(html_path: str) -> list:
    try:
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
    except Exception:
        return []
    titles = re.findall(r'<div class="card">\s*<h3>(.*?)</h3>', html, re.S)
    clean = []
    for t in titles:
        t = re.sub(r"<.*?>", "", t)
        t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        t = t.strip()
        if t:
            clean.append(t)
    return clean


def build_archive(site_dir: str, latest_date: str) -> str:
    files = glob.glob(os.path.join(site_dir, "????-??-??.html"))
    items = []
    for f in files:
        base = os.path.basename(f)
        d = base[:-5]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            continue
        if d == latest_date:
            continue
        headlines = extract_headlines(f)
        search = (d + " " + " ".join(headlines)).lower()
        items.append({
            "date": d,
            "month": d[:7],
            "search": search,
            "preview": headlines[0] if headlines else "",
        })
    items.sort(key=lambda x: x["date"], reverse=True)

    if not items:
        return (
            '    <section class="archive" id="archive">\n'
            '      <h2>往期回顾</h2>\n'
            '      <ul class="archive-list">\n'
            '        <li class="empty">暂无往期简报，每日 08:00 自动累积</li>\n'
            "      </ul>\n    </section>"
        )

    # group by month, newest first
    groups = {}
    for it in items:
        groups.setdefault(it["month"], []).append(it)
    months = sorted(groups.keys(), reverse=True)

    parts = []
    for m in months:
        y, mo = m.split("-")
        label = f"{y}年{int(mo)}月"
        lis = []
        for it in groups[m]:
            preview_html = (
                f'<span class="preview">{esc(it["preview"])}</span>'
                if it["preview"]
                else ""
            )
            lis.append(
                f'        <li data-search="{esc(it["search"])}">'
                f'<a href="{it["date"]}.html">'
                f'<span class="d">{it["date"]}</span>'
                f'{preview_html}</a></li>'
            )
        parts.append(
            f'        <li class="month-group" data-month="{m}">\n'
            f'          <div class="month-label">{label}</div>\n'
            "          <ul>\n" + "\n".join(lis) + "\n          </ul>\n"
            "        </li>"
        )
    body = "\n".join(parts)

    return (
        '    <section class="archive" id="archive">\n'
        '      <h2>往期回顾</h2>\n'
        '      <div class="search-box">\n'
        '        <input id="archive-search" type="search" '
        'placeholder="搜索日期或关键词，如 Grok、2026-07" '
        'autocomplete="off" aria-label="搜索往期简报">\n'
        "      </div>\n"
        '      <ul class="archive-list">\n'
        + body
        + "\n      </ul>\n"
        + SEARCH_SCRIPT
        + "\n    </section>"
    )


def main():
    if len(sys.argv) < 3:
        print("usage: generate.py <daily_md> <site_dir>")
        sys.exit(1)
    md_path = sys.argv[1]
    site_dir = sys.argv[2]
    os.makedirs(site_dir, exist_ok=True)

    date, meta, sections, sources = parse_md(md_path)

    # dated page (its "往期" link points to index.html#archive)
    inner_dated = render_brief(date, meta, sections, sources, is_index=False)
    dated_html = page_shell(date, meta, inner_dated, is_index=False)
    with open(os.path.join(site_dir, f"{date}.html"), "w", encoding="utf-8") as f:
        f.write(dated_html)

    # index (latest + always-visible archive section)
    inner_index = render_brief(date, meta, sections, sources, is_index=True)
    archive_html = build_archive(site_dir, date)
    index_inner = inner_index + "\n" + archive_html
    index_html = page_shell(date, meta, index_inner, is_index=True)
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"OK: generated {date}.html and index.html (latest={date})")


if __name__ == "__main__":
    main()
