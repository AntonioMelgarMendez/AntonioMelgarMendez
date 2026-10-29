#!/usr/bin/env python3
"""Local-only, live README preview. Run: python3 scripts/preview.py."""
import hashlib
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
MD = MarkdownIt("commonmark", {"html": True}).enable("table")


def revision():
    files = [ROOT / "README.md", *sorted((ROOT / "assets").glob("*"))]
    fingerprint = "|".join(f"{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}"
                           for p in files if p.is_file())
    return hashlib.sha256(fingerprint.encode()).hexdigest()


PAGE = """<!doctype html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Daniel Méndez · README preview</title>
<style>
:root{color-scheme:dark;--bg:#0d1117;--panel:#0d1117;--text:#e6edf3;--muted:#9198a1;--border:#30363d;--soft:#151b23;--link:#7ce8bf}
[data-theme=light]{color-scheme:light;--bg:#f6f8fa;--panel:#fff;--text:#1f2328;--muted:#59636e;--border:#d1d9e0;--soft:#f6f8fa;--link:#0969da}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.toolbar{position:sticky;top:0;z-index:2;border-bottom:1px solid var(--border);background:var(--panel);padding:13px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;font-size:13px}
.brand{font-family:ui-monospace,monospace}.live{color:#36bc8b}button{border:1px solid var(--border);background:var(--soft);color:var(--text);padding:6px 12px;border-radius:6px;cursor:pointer}
main{max-width:912px;margin:32px auto 60px;border:1px solid var(--border);border-radius:8px;background:var(--panel)}
.file{padding:12px 24px;border-bottom:1px solid var(--border);font:12px ui-monospace,monospace;color:var(--muted)}
article{padding:32px;overflow-wrap:break-word}article>:first-child{margin-top:0}article>:last-child{margin-bottom:0}
article img{max-width:100%;box-sizing:content-box;height:auto;vertical-align:middle}article p{margin:0 0 16px}article h1,article h2,article h3{line-height:1.25;margin:24px 0 16px;font-weight:600}
article h1{font-size:2em}article h2{font-size:1.5em;padding-bottom:.3em;border-bottom:1px solid var(--border)}article h3{font-size:1.25em}
article a{color:var(--link);text-decoration:none}article a:hover{text-decoration:underline}article hr{height:1px;border:0;background:var(--border);margin:24px 0}
article table{border-spacing:0;border-collapse:collapse;display:block;width:max-content;max-width:100%;overflow:auto;margin-bottom:16px}article table tr{border-top:1px solid var(--border)}article table tr:nth-child(2n){background:var(--soft)}article th,article td{border:1px solid var(--border);padding:10px 16px}article code{font:85% ui-monospace,monospace;background:var(--soft);border-radius:6px;padding:.2em .4em}
article blockquote{margin:0 0 16px;padding:0 1em;color:var(--muted);border-left:.25em solid var(--border)}article ul{padding-left:2em}article li+li{margin-top:.25em}article details{margin-bottom:16px}article summary{cursor:pointer}
.note{font-size:12px;color:var(--muted);text-align:center;padding:0 16px 24px}
@media(max-width:640px){.toolbar{padding:10px 14px}.brand{font-size:11px}.live{display:none}main{margin:16px 8px}article{padding:16px}.file{padding:12px 16px}}
</style></head><body>
<header class="toolbar"><span class="brand">AntonioMelgarMendez <span style="color:var(--muted)">/ README.md</span></span><span class="live">● Live preview</span><button id="theme">Light mode</button></header>
<main><div class="file">README.md · Profile</div><article>__README__</article></main>
<p class="note">Local preview · GitHub-compatible Markdown · GitHub's exact spacing may differ</p>
<script>
const root=document.documentElement, button=document.querySelector('#theme');
function theme(value){root.dataset.theme=value;button.textContent=value==='dark'?'Light mode':'Dark mode';localStorage.setItem('theme',value)}
theme(localStorage.getItem('theme')||'dark');button.onclick=()=>theme(root.dataset.theme==='dark'?'light':'dark');
let current=__REVISION__;
setInterval(async()=>{try{const next=await(await fetch('/__revision')).text();if(next!==current){sessionStorage.setItem('scroll',scrollY);location.reload()}}catch{}},1200);
const scroll=sessionStorage.getItem('scroll');if(scroll!==null){window.scrollTo(0,Number(scroll));sessionStorage.removeItem('scroll')}
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/__revision":
            self.respond(revision(), "text/plain")
        elif path in ("/", "/MAINTENANCE.md", "/ART-DIRECTION.md"):
            filename = "README.md" if path == "/" else "MAINTENANCE.md"
            self.respond(PAGE.replace("__README__", MD.render((ROOT / filename).read_text()))
                         .replace("__REVISION__", json.dumps(revision())), "text/html")
        elif path.startswith("/assets/") and ".." not in path:
            super().do_GET()
        else:
            self.send_error(404)

    def respond(self, body, content_type):
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 4173), Handler)
    print("Live README preview: http://127.0.0.1:4173", flush=True)
    server.serve_forever()
