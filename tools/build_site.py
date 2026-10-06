#!/usr/bin/env python3
"""Builds index.html (the guide) and resources.html (the catalog) from site_data.json."""
import io, json, os, html, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_common import (RESOURCES_DATE, REPO, GHT, FOOTER, head, header, min_css, min_js, dumps,
                         slim_page, word)

D = json.load(io.open("site_data.json", encoding="utf-8"))
OUT = "."
os.makedirs(OUT, exist_ok=True)

CSS = """
:root{
  --w:68ch;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);
  font:17px/1.62 Charter,Georgia,"Iowan Old Style",serif;
  -webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,"DejaVu Sans Mono",monospace}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}

header{position:sticky;top:0;z-index:40;background:var(--hdr);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.bar{max-width:1500px;margin:0 auto;padding:13px 22px;display:flex;gap:20px;align-items:center}
.brand{font:600 15px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink);letter-spacing:-.01em}
.brand span{color:var(--accent)}
nav{display:flex;gap:18px;font-size:14.5px}
nav a{color:var(--soft)} nav a.on{color:var(--ink);font-weight:600}
.search{margin-left:auto;position:relative}
.search input{font:14px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink);
  background:var(--card);border:1px solid var(--rule);border-radius:3px;
  padding:8px 11px;width:210px}
.search input::placeholder{color:var(--faint)}
.hits{position:absolute;right:0;top:40px;width:430px;max-height:62vh;overflow:auto;
  background:var(--card);border:1px solid var(--rule);border-radius:3px;display:none}
.hits.open{display:block}
.hit .sn{display:block;font-size:13px;line-height:1.45;color:var(--soft);margin-top:4px}
.hit mark{background:rgba(255,196,0,.4);color:inherit;border-radius:2px;padding:0 1px}
.hit{display:block;padding:10px 13px;border-bottom:1px solid var(--rule);color:var(--ink)}
.hit:last-child{border:0}
.hit:hover{background:var(--accent-bg);text-decoration:none}
.hit b{font-weight:600;font-size:15px}
.hit i{display:block;font-style:normal;font-size:12.5px;color:var(--faint);
  font-family:ui-monospace,Menlo,monospace;margin-top:2px}

.wrap{max-width:1500px;margin:0 auto;padding:0 22px;display:grid;
  grid-template-columns:266px minmax(0,1fr) 210px;gap:44px;align-items:start}
@media(max-width:1180px){.wrap{grid-template-columns:240px minmax(0,1fr);gap:34px}.rail{display:none}}
.toc-btn{display:none;font:13px/1 ui-monospace,Menlo,monospace;background:var(--card);
  color:var(--ink);border:1px solid var(--rule);border-radius:3px;padding:8px 12px;cursor:pointer}
@media(max-width:860px){
  .bar{flex-wrap:wrap;gap:12px;padding:11px 16px}
  .brand{white-space:nowrap;font-size:14px}
  nav{gap:14px;font-size:14px}
  .toc-btn{display:block;margin-left:auto}
  nav a[href^="http"]{display:none}
  .search{margin-left:0;order:9;width:100%}
  .search input{width:100%}
  .hits{width:100%;left:0;right:auto}
  .wrap{grid-template-columns:1fr;gap:0;padding:0 16px}
  aside{position:static;height:auto;border-right:0;border-bottom:1px solid var(--rule);
    padding:14px 0 18px;display:none}
  aside.show{display:block}
  main{padding:24px 0 70px}
  body{font-size:16.5px}
}

aside{position:sticky;top:57px;height:calc(100vh - 57px);overflow:auto;
  padding:26px 18px 60px 0;border-right:1px solid var(--rule)}
.sec{margin-bottom:3px}
.sec>button{width:100%;text-align:left;background:none;border:0;cursor:pointer;
  font:600 14px/1.4 Charter,Georgia,serif;color:var(--ink);padding:6px 6px 6px 0;
  display:flex;gap:8px;align-items:baseline}
.sec>button .n{font:11px/1 ui-monospace,Menlo,monospace;color:var(--faint);margin-left:auto}
.sec>button .k{font:11px/1 ui-monospace,Menlo,monospace;color:var(--accent);width:20px}
.sec ol{list-style:none;padding:0 0 6px 28px;display:none}
.sec.open ol{display:block}
.sec ol a{display:block;padding:4px 6px 4px 10px;font-size:14px;color:var(--soft);
  border-left:1px solid var(--rule);line-height:1.35}
.sec ol a:hover{color:var(--ink);border-color:var(--accent);text-decoration:none}
.sec ol a.cur{color:var(--ink);font-weight:600;border-left:2px solid var(--accent);
  background:var(--accent-bg)}

main{padding:34px 0 90px;min-width:0}
.rail{position:sticky;top:80px;padding:38px 0;font-size:13px;color:var(--faint)}
.rail .rh{font:11px/1 ui-monospace,Menlo,monospace;color:var(--faint);
  letter-spacing:.08em;margin-bottom:9px;font-weight:600}
.rail a{display:block;color:var(--soft);padding:3px 0;font-size:13px;line-height:1.35}
.rail .grp{margin-bottom:24px}

/* hero */
.hero{max-width:var(--w)}
.hero h1{font:600 clamp(34px,4.6vw,52px)/1.05 Charter,Georgia,serif;letter-spacing:-.025em;margin-bottom:14px}
.hero p{font-size:19px;color:var(--soft);margin-bottom:8px}
.figure{margin:30px 0 34px;background:var(--card);border:1px solid var(--rule);border-radius:4px;
  padding:10px 10px 4px;max-width:820px}
.figure figcaption{font:11.5px/1.5 ui-monospace,Menlo,monospace;color:var(--faint);padding:6px 8px 8px}
svg .edge{stroke:var(--accent);fill:none}
svg .node circle{fill:var(--card);stroke:var(--accent);stroke-width:1.5;cursor:pointer;
  transition:fill .15s}
svg .node:hover circle,svg .node:focus circle{fill:var(--accent-bg)}
svg .node:focus-visible{outline:none}
svg .node:focus-visible circle{stroke-width:3.5}
svg .node text{font:12px ui-monospace,Menlo,monospace;fill:var(--ink);cursor:pointer}
svg .node .cnt{font-size:10px;fill:var(--faint)}
svg .node .idx{font-size:11px;fill:var(--accent);font-weight:600}
.stats{display:flex;flex-wrap:wrap;gap:26px;margin:26px 0 34px;padding-top:20px;border-top:1px solid var(--rule)}
.stat b{display:block;font:600 27px/1 Charter,Georgia,serif;color:var(--num)}
.stat span{font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--faint)}
.seclist{max-width:var(--w)}
.seclist article{padding:16px 0;border-top:1px solid var(--rule);content-visibility:auto;contain-intrinsic-size:auto 96px}
.seclist h3{font:600 18px/1.3 Charter,Georgia,serif;margin-bottom:3px}
.seclist p{font-size:15px;color:var(--soft)}
.seclist .pg{font:12px ui-monospace,Menlo,monospace;color:var(--faint);margin-top:5px}

/* article */
article.page{max-width:var(--w)}
.crumb{font:12px ui-monospace,Menlo,monospace;color:var(--faint);margin-bottom:10px}
article.page h1{font:600 clamp(28px,3.4vw,38px)/1.12 Charter,Georgia,serif;
  letter-spacing:-.02em;margin-bottom:22px}
article.page h2{font:600 21px/1.3 Charter,Georgia,serif;margin:34px 0 11px;
  padding-top:16px;border-top:1px solid var(--rule)}
article.page h3{font:600 17px/1.3 Charter,Georgia,serif;margin:22px 0 7px}
article.page p{margin-bottom:15px}
article.page ul,article.page ol{margin:0 0 16px 22px}
article.page li{margin-bottom:7px}
article.page blockquote{border-left:2px solid var(--accent);padding-left:16px;
  color:var(--soft);margin-bottom:16px}
article.page code{font-family:ui-monospace,Menlo,monospace;font-size:.86em;
  background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:1px 5px}
article.page pre{background:var(--card);border:1px solid var(--rule);border-radius:4px;
  padding:14px 16px;overflow:auto;margin-bottom:17px}
article.page pre code{background:none;border:0;padding:0;font-size:13.5px;line-height:1.55}
article.page table{width:100%;border-collapse:collapse;margin-bottom:18px;font-size:14.5px}
article.page th{text-align:left;font-weight:600;padding:7px 10px 7px 0;
  border-bottom:1px solid var(--ink)}
article.page td{padding:8px 10px 8px 0;border-bottom:1px solid var(--rule);vertical-align:top}
article.page p a,article.page li a,article.page td a,article.page blockquote a{text-decoration:underline;text-underline-offset:3px}
article.page a.wiki{color:var(--accent);white-space:normal}
article.page a.wiki::before{content:"[[";color:var(--faint)}
article.page a.wiki::after{content:"]]";color:var(--faint)}
.pager{display:flex;gap:16px;justify-content:space-between;margin-top:46px;
  padding-top:18px;border-top:1px solid var(--rule);font-size:14px}
.pager a{max-width:46%}
.pager .lbl{display:block;font:11px ui-monospace,Menlo,monospace;color:var(--faint)}
.src{margin-top:34px;font:12px ui-monospace,Menlo,monospace;color:var(--faint)}

/* resources */
.rwrap{max-width:1180px;margin:0 auto;padding:34px 22px 90px}
.rwrap h1{font:600 clamp(30px,4vw,44px)/1.08 Charter,Georgia,serif;letter-spacing:-.025em}
.lede{max-width:62ch;color:var(--soft);margin:12px 0 24px;font-size:17px}
.controls{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:8px;
  padding-bottom:18px;border-bottom:1px solid var(--rule)}
.chip{font:13px/1 ui-monospace,Menlo,monospace;background:var(--card);color:var(--soft);
  border:1px solid var(--rule);border-radius:20px;padding:7px 13px;cursor:pointer}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.controls input{margin-left:auto;font:14px ui-monospace,Menlo,monospace;
  background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:8px 11px;width:230px}
.count{font:12px ui-monospace,Menlo,monospace;color:var(--faint);padding:14px 0 4px}
.grp-h{font:600 15px/1 ui-monospace,Menlo,monospace;color:var(--faint);
  margin:26px 0 6px;padding-top:14px;border-top:1px solid var(--rule)}
.row{content-visibility:auto;contain-intrinsic-size:auto 52px;display:grid;grid-template-columns:minmax(180px,260px) 120px 1fr;gap:18px;
  padding:12px 0;border-bottom:1px solid var(--rule);align-items:baseline}
@media(max-width:760px){.row{grid-template-columns:1fr;gap:3px}}
.row .nm{font-weight:600;font-size:16px}
.row .mt{font:13px ui-monospace,Menlo,monospace;color:var(--num)}
.row .ds{color:var(--soft);font-size:15px}
.row .kd{font:11px ui-monospace,Menlo,monospace;color:var(--faint);display:block;margin-top:2px}
footer{border-top:1px solid var(--rule);padding:22px;text-align:center;
  font:12px ui-monospace,Menlo,monospace;color:var(--faint)}
"""

# styles for the course and handbook sections injected by scripts/build_tracks.py
GUIDE_CSS = """
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.sdiv{margin:16px 12px 4px;padding-top:12px;border-top:1px solid var(--rule);
  color:var(--faint);font:600 10px/1 ui-monospace,Menlo,monospace;
  letter-spacing:.14em;text-transform:uppercase}
.trkhead{margin-top:36px}
.trkhead h2{font-size:21px}
.trkhead p{color:var(--soft);margin:6px 0 14px;max-width:56ch}
.tracklist article{border-top:2px solid var(--accent)}
.courselist article{border-top:2px solid var(--num)}
article.page img{max-width:100%;height:auto;display:block;margin:20px auto}
.entr{max-width:var(--w);display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:34px 0 8px}@media(max-width:760px){.entr{grid-template-columns:1fr}}.ent{display:block;background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:20px 20px 16px;text-decoration:none;transition:border-color .15s}.ent:hover{border-color:var(--accent)}.ent .ek{font:11px/1 ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}.ent h2{font:600 20px/1.2 Charter,Georgia,serif;color:var(--ink);margin:9px 0 7px}.ent p{font-size:14px;line-height:1.5;color:var(--soft);margin:0 0 12px}.ent .em{font:12px ui-monospace,Menlo,monospace;color:var(--accent)}.ent.e2{border-top:3px solid var(--num)}.ent.e1{border-top:3px solid var(--accent)}.ent.e3{border-top:3px solid var(--rule)}
@media print{
  aside,.rail,.pager{display:none!important}
  .wrap,.rwrap{display:block;max-width:none;padding:0}
  main{padding:0}
  article.page{max-width:none}
  article a[href^="http"]::after{content:" (" attr(href) ")";font:.8em ui-monospace,Menlo,monospace;
    color:#444;word-break:break-all}
}"""

SEARCHBOX = ('<div class="search"><input id="q" type="search" '
             'placeholder="search the guide" aria-label="Search the guide" '
             'autocomplete="off">'
             '<div class="hits" id="hits" role="region" aria-label="Search results" '
             'aria-live="polite"></div></div>')

def page_header(active):
    extra = ""
    if active == "guide":
        extra = '<button class="toc-btn" id="toc" aria-controls="side" aria-expanded="false">Index</button>\n  ' + SEARCHBOX + "\n"
    return header(active, extra)

# ---------------- graph: sections on a ring in reading order, links as chords
import math
g = D["graph"]
order = list(D["sections"].keys())
CX, CY, RX, RY = 400, 232, 300, 150
pos = {}
for i, sec in enumerate(order):
    a = -math.pi/2 + 2*math.pi*i/len(order)
    pos[sec] = (CX + RX*math.cos(a), CY + RY*math.sin(a), a)

edges_svg = ""
for e in sorted(g["edges"], key=lambda e: e["w"]):
    x1, y1, _ = pos[e["a"]]; x2, y2, _ = pos[e["b"]]
    qx, qy = CX + (x1+x2-2*CX)*0.18, CY + (y1+y2-2*CY)*0.18
    edges_svg += (f'<path class="edge" d="M{x1:.0f},{y1:.0f} Q{qx:.0f},{qy:.0f} {x2:.0f},{y2:.0f}" '
                  f'stroke-width="{min(0.8+e["w"]*0.42, 3.4):.2f}" '
                  f'stroke-opacity="{min(0.35+e["w"]*0.12, 0.9):.2f}"/>')

nodes_svg = ""
for i, sec in enumerate(order):
    x, y, a = pos[sec]
    n = len([p for p in D["pages"] if p["section"] == sec])
    r = 8 + n*0.75
    cos = math.cos(a)
    anchor = "middle" if abs(cos) < 0.35 else ("start" if cos > 0 else "end")
    dx = 0 if anchor == "middle" else (r+9 if cos > 0 else -(r+9))
    dy = (r+18) if math.sin(a) > 0.35 else (-(r+12) if math.sin(a) < -0.35 else 5)
    nodes_svg += (f'<g class="node" data-sec="{sec}" tabindex="0" role="link">'
                  f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}"/>'
                  f'<text x="{x+dx:.0f}" y="{y+dy:.0f}" text-anchor="{anchor}">'
                  f'{D["sections"][sec]["title"]}</text>'
                  f'<text class="cnt" x="{x+dx:.0f}" y="{y+dy+13:.0f}" text-anchor="{anchor}">{n} pages</text>'
                  f'<text class="idx" x="{x:.0f}" y="{y+3.5:.0f}" text-anchor="middle">{i+1}</text>'
                  f'</g>')

GRAPH = (f'<figure class="figure"><svg viewBox="0 0 800 470" role="group" '
         f'aria-label="The {word(len(order))} sections of the guide and the links between them">'
         f'{edges_svg}{nodes_svg}</svg>'
         f'<figcaption>The {word(len(order))} sections, in reading order, with the '
         f'{len(g["edges"])} places they reference each other. Thicker where they lean on '
         f'each other hardest. Click one to start there.</figcaption></figure>')

s = D["stats"]
STATS = f"""<div class="stats">
 <div class="stat"><b>{s['pages']}</b><span>pages</span></div>
 <div class="stat"><b>{s['sections']}</b><span>sections</span></div>
 <div class="stat"><b>{s['words']//1000}k</b><span>words</span></div>
 <div class="stat"><b>{s['links']}</b><span>vetted links</span></div>
 <div class="stat"><b>0</b><span>lock-in</span></div>
</div>"""

import re as _re
def inline(t):
    t = html.escape(t)
    return _re.sub(r"`([^`]+)`", r"<code>\1</code>", t)

seclist = ""
for sec, meta in D["sections"].items():
    first = D["order"][sec][0]
    seclist += (f'<article><h3><a href="#{first}">{html.escape(meta["title"])}</a></h3>'
                f'<p>{inline(meta["blurb"])}</p>'
                f'<div class="pg">{len(D["order"][sec])} pages</div></article>')

NOSCRIPT = ('<h1>Second Brain OS</h1><p>The guide needs JavaScript. The same pages '
            'are plain markdown on GitHub:</p><ul>'
            + "".join(f'<li><a href="{GHT}docs/{sec}">{html.escape(m["title"])}</a></li>'
                      for sec, m in D["sections"].items())
            + f'</ul><p><a href="{GHT}docs">All of docs/</a></p>')

GUIDE = f"""{head("Second Brain OS - the guide", f"A {s['pages']}-page guide to building a knowledge base your AI agent maintains, in plain markdown you own.", "index.html", min_css(CSS + GUIDE_CSS))}
{page_header('guide')}
<template id="hero"><div class="hero"><h1>A knowledge base your agent maintains</h1>
<p>Everything you read, watched and wrote, turned into linked pages and kept current by an agent. Plain markdown on your own machine.</p>
{GRAPH}{STATS}</div><!--ENTRIES--><!--/ENTRIES--><div class="trkhead"><h2>the second-brain guide</h2><p>A path you follow once, in order: from the concept to a vault that maintains itself, one evening to set up.</p></div><div class="seclist">{seclist}</div><!--COURSE--><!--/COURSE--><!--TRACKS--><!--/TRACKS--></template>
<div class="wrap">
  <aside id="side" aria-label="Guide sections"></aside>
  <main id="main" tabindex="-1"><noscript>{NOSCRIPT}</noscript></main>
  <div class="rail" id="rail" role="complementary" aria-label="On this page"></div>
</div>
{FOOTER}
<script id="data" type="application/json">{dumps({'pages': [slim_page(p) for p in D['pages']], 'sections': D['sections'], 'order': D['order']})}</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const P={{}}; D.pages.forEach(p=>{{P[p.id]=p; p.section=p.id.split('/')[0]; p.section_title=D.sections[p.section].title; p.path='docs/'+p.id+'.md';}});
const T={{}};
const DEC=document.createElement('textarea');
const unhtml=h=>{{DEC.innerHTML=h.replace(/<[^>]+>/g,' ');return DEC.value.replace(/\s+/g,' ').trim();}};
// text, lowercase text and h2 texts of a page, derived once from its html
function idx(p){{if(!T[p.id]){{const t=unhtml(p.html);
  T[p.id]={{t,l:t.toLowerCase(),h:[...p.html.matchAll(/<h2[^>]*>([\s\S]*?)<\/h2>/g)].map(m=>unhtml(m[1]).toLowerCase())}};}}return T[p.id];}}
const esc=s=>s.replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';');
// escape text and wrap each occurrence of v (lowercase) in <mark>
function mark(s,v){{let o='',i=0,l=s.toLowerCase(),k;
  if(l.length!==s.length)return esc(s);
  while((k=l.indexOf(v,i))>=0){{o+=esc(s.slice(i,k))+'<mark>'+esc(s.slice(k,k+v.length))+'</mark>';i=k+v.length;}}
  return o+esc(s.slice(i));}}
function snippet(x,v){{const k=x.l.length===x.t.length?x.l.indexOf(v):-1;
  let a=Math.max(0,(k<0?0:k)-45), b=Math.min(x.t.length,(k<0?0:k)+v.length+90);
  if(a>0){{const j=x.t.indexOf(' ',a);if(j>=0&&j<k)a=j+1;}}
  if(b<x.t.length){{const j=x.t.lastIndexOf(' ',b);if(j>k+v.length)b=j;}}
  return (a>0?'\u2026':'')+mark(x.t.slice(a,b),v)+(b<x.t.length?'\u2026':'');}}
const FLAT=[]; Object.keys(D.order).forEach(s=>D.order[s].forEach(id=>FLAT.push(id)));
const HERO=document.getElementById('hero').innerHTML;

function side(cur){{
  const s=document.getElementById('side'); let h='';
  let mi=0, ti=0, ci=0, divT=false, divC=false;
  Object.keys(D.order).forEach((sec)=>{{
    const isT = sec.startsWith('track-'), isC = sec.startsWith('course-');
    if(isC && !divC){{ h+='<div class="sdiv">the agents course</div>'; divC=true; }}
    if(isT && !divT){{ h+='<div class="sdiv">handbooks</div>'; divT=true; }}
    const badge = isC ? 'C'+(ci++) : isT ? 'T'+(++ti) : String(++mi).padStart(2,'0');
    const open = cur && cur.startsWith(sec);
    h+=`<div class="sec ${{open?'open':''}}" data-sec="${{sec}}">
      <button aria-expanded="${{!!open}}"><span class="k">${{badge}}</span>
      ${{D.sections[sec].title}}<span class="n">${{D.order[sec].length}}</span></button><ol>`;
    D.order[sec].forEach(id=>{{
      h+=`<li><a href="#${{id}}" class="${{id===cur?'cur':''}}"${{id===cur?' aria-current="page"':''}}>${{P[id].title}}</a></li>`;
    }});
    h+='</ol></div>';
  }});
  s.innerHTML=h;
  s.querySelectorAll('.sec>button').forEach(b=>b.onclick=()=>{{
    const d=b.parentElement; d.classList.toggle('open');
    b.setAttribute('aria-expanded', d.classList.contains('open'));
  }});
}}

let first=true, last=location.pathname+location.search;
function render(){{
  if(location.hash==='#main'){{history.replaceState(null,'',last);if(!first)return;}}
  last=location.pathname+location.search+location.hash;
  const id=decodeURIComponent(location.hash.slice(1));
  const main=document.getElementById('main'), rail=document.getElementById('rail');
  if(!P[id]){{
    main.innerHTML=HERO; rail.innerHTML=''; side(null);
    main.querySelectorAll('svg .node').forEach(n=>{{
      const go=()=>{{location.hash=D.order[n.dataset.sec][0];}};
      n.onclick=go;
      n.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();go();}}}});
    }});
    document.title='Second Brain OS - the guide';
    window.scrollTo(0,0); done(); return;
  }}
  const p=P[id], i=FLAT.indexOf(id), prev=FLAT[i-1], next=FLAT[i+1];
  main.innerHTML=`<article class="page">
    <div class="crumb">${{p.section_title}} / page ${{D.order[p.section].indexOf(id)+1}} of ${{D.order[p.section].length}}</div>
    <h1>${{p.title}}</h1>${{p.html}}
    <div class="pager">
      ${{prev?`<a href="#${{prev}}"><span class="lbl">previous</span>${{P[prev].title}}</a>`:'<span></span>'}}
      ${{next?`<a href="#${{next}}" style="text-align:right"><span class="lbl">next</span>${{P[next].title}}</a>`:'<span></span>'}}
    </div>
    <div class="src">source: <a href="{REPO}/blob/main/${{p.path}}">${{p.path}}</a></div>
  </article>`;
  // rewrite internal links to hash routes, style them as wikilinks
  main.querySelectorAll('a[href]').forEach(a=>{{
    const href=a.getAttribute('href');
    if(/^([a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href)) return;
    const hashAt=href.search(/[#?]/), path=hashAt<0?href:href.slice(0,hashAt), tail=hashAt<0?'':href.slice(hashAt);
    let target=null;
    if(path.endsWith('.md')){{
      const parts=path.replace(/^\.\//,'').split('/');
      const file=parts[parts.length-1].replace('.md','');
      if(file==='README'){{
        const sec=parts[parts.length-2]; if(D.order[sec]) target=D.order[sec][0];
      }} else {{
        const sec = parts.length>1 ? parts[parts.length-2] : p.section;
        const cand = sec+'/'+file;
        target = P[cand] ? cand : (P[p.section+'/'+file] ? p.section+'/'+file : null);
      }}
    }}
    if(target){{ a.setAttribute('href','#'+target); a.className='wiki'; return; }}
    // anything else points into the repository: send it to GitHub
    const out=p.path.split('/').slice(0,-1);
    path.split('/').forEach(seg=>{{ if(seg==='..') out.pop(); else if(seg&&seg!=='.') out.push(seg); }});
    const last=out[out.length-1]||'';
    const kind=(path===''||path.endsWith('/')||last.indexOf('.')<0)?'tree':'blob';
    a.setAttribute('href','{REPO}/'+kind+'/main/'+out.join('/')+tail);
  }});
  main.querySelectorAll('pre').forEach(e=>e.tabIndex=0);
  main.querySelectorAll('th').forEach(h=>{{if(!h.textContent.trim())h.innerHTML='<span class="vh">Row label</span>';}});
  const heads=[...main.querySelectorAll('h2')];
  const outs=[...main.querySelectorAll('a.wiki')].slice(0,8);
  rail.innerHTML=(heads.length?`<div class="grp"><div class="rh">on this page</div>`+
      heads.map((h,n)=>{{h.id='h'+n;return `<a href="#${{id}}" onclick="document.getElementById('h${{n}}').scrollIntoView();return false">${{h.textContent}}</a>`}}).join('')+`</div>`:'')
    +(outs.length?`<div class="grp"><div class="rh">links out</div>`+
      outs.map(a=>`<a href="${{a.getAttribute('href')}}">${{a.textContent}}</a>`).join('')+`</div>`:'');
  side(id); document.title=p.title+' - Second Brain OS'; window.scrollTo(0,0); done();
}}
function done(){{ if(first){{first=false;return;}} document.getElementById('main').focus({{preventScroll:true}}); }}

// search
const q=document.getElementById('q'), hits=document.getElementById('hits');
q.addEventListener('input',()=>{{
  const v=q.value.trim().toLowerCase();
  if(v.length<2){{hits.classList.remove('open');return;}}
  // title 10 (+6 at the start) > an h2 8 > body at most 3
  const r=D.pages.map(p=>{{
    const x=idx(p); let sc=0; const t=p.title.toLowerCase();
    if(t.includes(v)) sc+=10; if(t.startsWith(v)) sc+=6;
    if(x.h.some(h=>h.includes(v))) sc+=8;
    sc+=Math.min(x.l.split(v).length-1,3);
    return {{p,x,sc}};
  }}).filter(x=>x.sc>0).sort((a,b)=>b.sc-a.sc).slice(0,9);
  hits.innerHTML=r.length?r.map(x=>`<a class="hit" href="#${{x.p.id}}"><b>${{mark(x.p.title,v)}}</b><i>${{esc(x.p.section_title)}}</i><span class="sn">${{snippet(x.x,v)}}</span></a>`).join('')
    :'<div class="hit"><i>nothing in the guide matches that</i></div>';
  hits.classList.add('open');
}});
q.addEventListener('keydown',e=>{{
  const f=hits.querySelector('a.hit');
  if(e.key==='ArrowDown'&&f&&hits.classList.contains('open')){{e.preventDefault();f.focus();}}
  if(e.key==='Enter'&&f&&hits.classList.contains('open')){{e.preventDefault();f.click();location.hash=f.getAttribute('href').slice(1);}}
}});
hits.addEventListener('keydown',e=>{{
  const a=[...hits.querySelectorAll('a.hit')], i=a.indexOf(document.activeElement);
  if(i<0)return;
  if(e.key==='ArrowDown'){{e.preventDefault();(a[i+1]||a[i]).focus();}}
  if(e.key==='ArrowUp'){{e.preventDefault();(i?a[i-1]:q).focus();}}
}});
q.addEventListener('keydown',e=>{{if(e.key==='Escape'){{q.value='';hits.classList.remove('open');q.blur();}}}});
document.addEventListener('click',e=>{{if(!e.target.closest('.search'))hits.classList.remove('open');}});
document.addEventListener('keydown',e=>{{
  const tg=e.target, typing=tg.closest&&tg.closest('input,textarea,select,[contenteditable]');
  if(e.key==='/'&&!typing&&!e.ctrlKey&&!e.metaKey&&!e.altKey){{e.preventDefault();q.focus();}}
  if(typing||e.ctrlKey||e.metaKey||e.altKey||e.shiftKey)return;
  if(!P[decodeURIComponent(location.hash.slice(1))])return;
  const i=FLAT.indexOf(decodeURIComponent(location.hash.slice(1)));
  if(e.key==='ArrowRight'&&FLAT[i+1])location.hash=FLAT[i+1];
  if(e.key==='ArrowLeft'&&FLAT[i-1])location.hash=FLAT[i-1];
}});
hits.addEventListener('click',()=>{{hits.classList.remove('open');q.value='';}});
const toc=document.getElementById('toc');
if(toc){{toc.onclick=()=>{{const o=document.getElementById('side').classList.toggle('show');toc.setAttribute('aria-expanded',o);}};}}
document.getElementById('side').addEventListener('click',e=>{{
  if(e.target.tagName==='A'&&innerWidth<=860){{ document.getElementById('side').classList.remove('show'); if(toc)toc.setAttribute('aria-expanded','false'); }}
}});
document.querySelector('.skip').addEventListener('click',e=>{{e.preventDefault();document.getElementById('main').focus();}});
addEventListener('hashchange',render); render();
</script></body></html>"""

import re as _re2
def _minjs(doc):
    return _re2.sub(r"(<script>\n)(.*?)(</script>)",
                    lambda m: m.group(1) + min_js(m.group(2)) + m.group(3), doc, flags=_re2.S)
GUIDE = _minjs(GUIDE)
io.open(f"{OUT}/index.html", "w", encoding="utf-8", newline="\n").write(GUIDE)

# ---------------- resources page
R = D["resources"]
kinds = []
for r in R:
    if r["kind"] not in kinds: kinds.append(r["kind"])

RES = f"""{head("Second Brain OS - resources", f"{len(R)} checked links: Obsidian plugins by installs, repositories by stars, papers, tools and reading.", "resources.html", min_css(CSS))}
{page_header('res')}
<main class="rwrap" id="main" tabindex="-1">
  <h1>Everything worth opening</h1>
  <p class="lede">{len(R)} links, each one checked. Plugins are ranked by installs from Obsidian's own community stats rather than by stars, because in this ecosystem the two disagree by an order of magnitude. Figures are from {RESOURCES_DATE} and will drift.</p>
  <div class="controls" id="ctl">
    <button class="chip on" data-k="all" aria-pressed="true">All</button>
    {"".join(f'<button class="chip" data-k="{html.escape(k)}" aria-pressed="false">{html.escape(k)}</button>' for k in kinds)}
    <input id="rq" type="search" placeholder="filter" aria-label="Filter resources" autocomplete="off">
  </div>
  <div class="count" id="count" role="status"></div>
  <div id="rows"></div>
</main>
{FOOTER}
<script id="rdata" type="application/json">{dumps(R)}</script>
<script>
const R=JSON.parse(document.getElementById('rdata').textContent);
let kind='all', term='';
function draw(){{
  const f=R.filter(r=>(kind==='all'||r.kind===kind) &&
    (!term || (r.name+' '+r.desc+' '+r.group).toLowerCase().includes(term)));
  document.getElementById('count').textContent=f.length+' of '+R.length+' shown';
  let h='', g=null;
  f.forEach(r=>{{
    const key=r.kind+' / '+r.group;
    if(key!==g){{g=key; h+=`<div class="grp-h">${{r.group||r.kind}}</div>`;}}
    h+=`<div class="row">
      <div><a class="nm" href="${{r.url}}">${{r.name}}</a><span class="kd">${{r.kind}}</span></div>
      <div class="mt">${{r.metric||''}}</div>
      <div class="ds">${{r.desc||''}}</div></div>`;
  }});
  document.getElementById('rows').innerHTML=h||'<div class="count">nothing matches that filter</div>';
}}
document.getElementById('ctl').addEventListener('click',e=>{{
  const b=e.target.closest('.chip'); if(!b)return;
  document.querySelectorAll('.chip').forEach(c=>{{c.classList.toggle('on',c===b);c.setAttribute('aria-pressed',c===b);}});
  kind=b.dataset.k; draw();
}});
document.getElementById('rq').addEventListener('input',e=>{{term=e.target.value.trim().toLowerCase();draw();}});
draw();
</script></body></html>"""

RES = _minjs(RES)
io.open(f"{OUT}/resources.html", "w", encoding="utf-8", newline="\n").write(RES)
print("index.html", os.path.getsize(f"{OUT}/index.html")//1024, "KB |",
      "resources.html", os.path.getsize(f"{OUT}/resources.html")//1024, "KB")
