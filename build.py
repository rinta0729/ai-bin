"""AI便: issues/<日付>/issue.json から公開ページ(docs/)を作る。AIは使わない。
使い方: python3 build.py            … 全号を作り直し、一覧ページも更新
"""
from __future__ import annotations
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ISSUES = ROOT / "issues"
DOCS = ROOT / "docs"
SITE = "https://rinta0729.github.io/ai-bin"

CSS = """
:root{--bg:#F3F5F7;--surface:#FFFFFF;--ink:#16191D;--muted:#5D6670;--line:#D9DEE3;--accent:#20466B;--accent-ink:#FFFFFF;--soft:#E3EBF3;--warn:#9A3B16;--warn-bg:#FBEDE6;--code:#F7F8FA;color-scheme:light}
@media (prefers-color-scheme: dark){:root{--bg:#111418;--surface:#181C21;--ink:#E7ECF1;--muted:#97A2AD;--line:#2A3139;--accent:#8DB8E3;--accent-ink:#0D1218;--soft:#1B2836;--warn:#F2A07C;--warn-bg:#35221A;--code:#14181D;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans JP","Hiragino Sans","Yu Gothic UI","Meiryo",sans-serif;font-size:15.5px;line-height:1.8}
.wrap{max-width:760px;margin:0 auto;padding-inline:18px;padding-block:30px 80px}
.eyebrow{font-size:12.5px;letter-spacing:.08em;color:var(--muted)}
h1{font-size:26px;margin:4px 0 8px;line-height:1.35}
.lede{margin:0;color:var(--muted)}
.toc{display:grid;gap:6px;margin:20px 0 6px;padding:0;list-style:none;counter-reset:t}
.toc li{counter-increment:t}
.toc a{display:flex;gap:10px;align-items:baseline;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 14px;color:var(--ink);text-decoration:none;font-weight:500}
.toc a::before{content:counter(t);flex:none;display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--soft);color:var(--accent);font-weight:700;font-size:12.5px}
.toc a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
article{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 18px 16px;margin-top:22px}
.tag{display:inline-block;font-size:12px;font-weight:500;color:var(--accent);background:var(--soft);border-radius:999px;padding:1px 10px}
h2{font-size:19px;margin:8px 0 6px;line-height:1.45}
h3{font-size:13.5px;margin:16px 0 4px;color:var(--muted);font-weight:500;letter-spacing:.04em}
p{margin:6px 0}
ul,ol{margin:6px 0;padding-left:22px}li{margin:3px 0}
.pbox{position:relative;background:var(--code);border:1px solid var(--line);border-radius:10px;margin-top:6px}
pre{margin:0;padding:12px 14px;white-space:pre-wrap;word-break:break-word;font-family:"IBM Plex Mono","IBM Plex Sans JP",monospace;font-size:13.5px;line-height:1.7}
button{font:inherit;font-size:13.5px;font-weight:500;border:0;border-radius:8px;padding:7px 14px;background:var(--accent);color:var(--accent-ink);cursor:pointer;margin-top:8px}
.toast{font-size:13px;color:var(--accent);margin-left:8px}
.caution{background:var(--warn-bg);border-left:3px solid var(--warn);padding:8px 12px;border-radius:0 8px 8px 0;font-size:14px;margin-top:12px}
.src{font-size:12.5px;color:var(--muted);margin-top:12px;word-break:break-all}
.src a{color:var(--muted)}
.foot{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.foot a,.list a{color:var(--accent)}
.list{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:8px}
.list a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none}
.list small{display:block;color:var(--muted)}
"""

JS = """
document.querySelectorAll('button[data-copy]').forEach(b=>b.addEventListener('click',()=>{
 const pre=document.getElementById(b.dataset.copy), t=b.nextElementSibling;
 const fb=()=>{const r=document.createRange();r.selectNodeContents(pre);const s=getSelection();s.removeAllRanges();s.addRange(r);t.textContent='選択しました。コピーしてください';};
 try{navigator.clipboard.writeText(pre.textContent).then(()=>{t.textContent='コピーしました';setTimeout(()=>t.textContent='',2500)}).catch(fb)}catch(e){fb()}
}));
"""

HEAD = """<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style></head><body><div class="wrap">"""

e = html.escape


def jdate(d: str) -> str:
    y, m, dd = d.split("-")
    return f"{int(y)}年{int(m)}月{int(dd)}日"


def lis(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{e(x)}</li>" for x in items) + f"</{tag}>"


def sources(srcs: list[dict]) -> str:
    if not srcs:
        return ""
    links = " ／ ".join(f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["label"])}</a>' for s in srcs)
    return f'<p class="src">出典：{links}</p>'


def topic_html(i: int, t: dict) -> str:
    parts = [f'<article id="t{i}"><span class="tag">{e(t["for"])}</span><h2>{e(t["title"])}</h2>']
    parts.append(f'<h3>何が出たか</h3><p>{e(t["what"])}</p>')
    parts.append("<h3>仕事でどう使えるか</h3>" + lis(t["use"]))
    if t.get("try"):
        parts.append("<h3>試し方</h3>" + lis(t["try"], ordered=True))
    if t.get("prompt"):
        parts.append(
            f'<h3>そのまま貼れる文</h3><div class="pbox"><pre id="p{i}">{e(t["prompt"])}</pre></div>'
            f'<button type="button" data-copy="p{i}">コピー</button><span class="toast" aria-live="polite"></span>'
        )
    if t.get("caution"):
        parts.append(f'<p class="caution"><b>気をつける点</b>：{e(t["caution"])}</p>')
    parts.append(sources(t.get("sources", [])))
    parts.append("</article>")
    return "".join(parts)


def build_issue(issue: dict) -> None:
    d = issue["date"]
    out = [HEAD.format(title=e(f'AI便 第{issue["no"]}号'), css=CSS)]
    out.append(f'<div class="eyebrow">AI便 第{issue["no"]}号 ・ {jdate(d)}</div><h1>{e(issue["title"])}</h1><p class="lede">{e(issue["lead"])}</p>')
    out.append('<ol class="toc">' + "".join(f'<li><a href="#t{i}">{e(t["title"])}</a></li>' for i, t in enumerate(issue["topics"], 1)) + "</ol>")
    out += [topic_html(i, t) for i, t in enumerate(issue["topics"], 1)]
    tip = issue.get("tip")
    if tip:
        out.append(f'<article><span class="tag">今週のひとこと</span><h2>{e(tip["title"])}</h2><p>{e(tip["body"])}</p>{sources(tip.get("sources", []))}</article>')
    out.append(
        '<p class="foot">AI便は、新しく出たAIの機能や使い方を、仕事でどう使えるかに絞ってお届けするお便りです。'
        "内容は発行日時点の公式発表と報道にもとづいています。仕様や料金は変わることがあります。<br>"
        f'発行：ALL RUNS 越智琳太 ・ <a href="{SITE}/">これまでの号</a></p>'
    )
    out.append(f"</div><script>{JS}</script></body></html>")
    dest = DOCS / d
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text("".join(out), encoding="utf-8")


def build_index(issues: list[dict]) -> None:
    out = [HEAD.format(title="AI便", css=CSS)]
    out.append('<div class="eyebrow">ALL RUNS</div><h1>AI便</h1><p class="lede">新しく出たAIの機能や使い方を、仕事でどう使えるかに絞ってお届けします。</p><ul class="list">')
    for it in sorted(issues, key=lambda x: x["date"], reverse=True):
        out.append(f'<li><a href="{it["date"]}/"><small>第{it["no"]}号 ・ {jdate(it["date"])}</small>{e(it["title"])}</a></li>')
    out.append("</ul></div></body></html>")
    (DOCS / "index.html").write_text("".join(out), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    issues = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ISSUES.glob("*/issue.json"))]
    for it in issues:
        build_issue(it)
        print(f'第{it["no"]}号 {it["date"]} → docs/{it["date"]}/index.html  公開後のURL: {SITE}/{it["date"]}/')
    build_index(issues)


if __name__ == "__main__":
    main()
