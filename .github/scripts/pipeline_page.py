#!/usr/bin/env python3
"""Build the app's Pipeline page: what's in each stage and what's waiting.

Usage: pipeline_page.py <repo_dir> <owner/repo> <output.html>

<repo_dir> is a clone (bare is fine) with all four stage branches and tags.
The shared deploy runs this on every deploy and publishes the page at
https://<owner>.github.io/<repo>/pipeline/ so it's always current.

For each stage before Production it lists the changes waiting to move on
(dev -> alpha -> staging -> main):
- once changes have release notes (Alpha onwards), the notes' headlines,
  with issue pills; other changes in the same step fold under "+ n smaller";
- on Dev, which has no notes yet, the change titles.
Housekeeping commits (only .github/ or *.md files) are left out.
Production shows the live version (same name as the GitHub release), when it
was released, its headlines and a link to the GitHub release; a rollback is
shown as such. Open issues are listed underneath.

Env: APP (app name), C_MAIN/C_STAGING/C_ALPHA/C_DEV (stage colours),
RELEASE_TZ, GITHUB_REPOSITORY and GH_TOKEN (issue labels, open issues).
Anything that can't be looked up is simply left out.
"""
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release_notes import (FS, RS, git, is_housekeeping, issue_labels,  # noqa: E402
                           promotions, release_names, rollbacks)

STAGES = [("dev", "Dev"), ("alpha", "Alpha"), ("staging", "Staging"), ("main", "Production")]
ISSUE_REF = re.compile(r"\b(?:issues?|fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*:?\s*#(\d+)", re.I)
BULLET = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*.*?((?:\(#\d+\)\s*)*)\s*$")


def exists(repo, ref):
    try:
        git(repo, "rev-parse", "--verify", "-q", ref)
        return True
    except Exception:
        return False


def waiting_commits(repo, src, dst):
    """Non-housekeeping commits in src that aren't in dst, newest first."""
    log = git(repo, "log", "--no-merges", "--name-only", f"--format={RS}%H{FS}%cI{FS}%B{FS}", f"{dst}..{src}")
    out = []
    for entry in log.split(RS):
        if not entry.strip():
            continue
        sha, date, body, files = entry.split(FS, 3)
        files = [f for f in files.splitlines() if f.strip()]
        if is_housekeeping(files):
            continue
        title = body.strip().splitlines()[0]
        issues = sorted({int(n) for n in ISSUE_REF.findall(body)})
        out.append({"sha": sha, "date": date, "title": title, "issues": issues})
    return out


def note_headlines(notes):
    """[(headline, [issue numbers])] from release-note bullets like
    "- **Headline** — text. (#6)"."""
    out = []
    for line in notes.splitlines():
        m = BULLET.match(line)
        if m:
            out.append((m.group(1).strip(), [int(n) for n in re.findall(r"#(\d+)", m.group(2) or "")]))
    return out


def waiting(repo, src, dst):
    commits = waiting_commits(repo, src, dst)
    if not commits:
        return [], []
    # Release notes of promotions into `src` that `dst` doesn't have yet.
    heads = []
    for p in promotions(repo, ref=src):
        full = git(repo, "rev-parse", p["sha"]).strip()
        try:
            git(repo, "merge-base", "--is-ancestor", full, dst)
            continue                                  # already in dst
        except Exception:
            pass
        heads += note_headlines(p["notes"])
    if not heads:                                     # Dev: no notes yet
        return [{"t": c["title"], "i": c["issues"]} for c in commits], []
    covered = {n for _, ns in heads for n in ns}
    items = [{"t": h, "i": ns} for h, ns in heads]
    more = [c["title"] for c in commits if not (set(c["issues"]) & covered)]
    return items, more


def api(path):
    slug = os.environ.get("GITHUB_REPOSITORY")
    if not slug:
        return None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "app-playbook-deploy"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{slug}/{path}", headers=headers)
        return json.load(urllib.request.urlopen(req, timeout=10))
    except Exception as e:
        print(f"  (pipeline: couldn't read {path}: {e})")
        return None


def build(repo, slug):
    owner, name = slug.split("/", 1)
    base = f"https://{owner.lower()}.github.io/{name}/"
    colours = {"dev": os.environ.get("C_DEV") or "#7048e8", "alpha": os.environ.get("C_ALPHA") or "#c2255c",
               "staging": os.environ.get("C_STAGING") or "#e67700", "main": os.environ.get("C_MAIN") or "#3b5bdb"}
    stages, numbers = [], set()
    for i, (key, label) in enumerate(STAGES):
        if not exists(repo, key):
            continue
        head_date = git(repo, "log", "-1", "--format=%cI", key).strip()
        s = {"key": key, "name": label, "color": colours[key], "changed": head_date,
             "url": base if key == "main" else f"{base}{key}/"}
        if key != "main":
            nxt_key, nxt_label = STAGES[i + 1]
            s["next"] = nxt_label
            if exists(repo, nxt_key):
                items, more = waiting(repo, key, nxt_key)
                s["items"], s["more"] = items, more
                s["kind"] = "changes" if key == "dev" else "notes"
                numbers.update(n for it in items for n in it["i"])
        else:
            names = release_names(repo, ref="main")
            rbs = rollbacks(repo, ref="main")
            undone = {rb["rolled_back_commit"] for rb in rbs}
            live = next((p for p in promotions(repo, ref="main")
                         if git(repo, "rev-parse", p["sha"]).strip() not in undone), None)
            if live:
                full = git(repo, "rev-parse", live["sha"]).strip()
                version = names.get(full)
                s.update(version=version, released=live["date"],
                         release=f"https://github.com/{slug}/releases/tag/{version}" if version else None,
                         headline=[{"t": h, "i": ns} for h, ns in note_headlines(live["notes"])][:4])
                numbers.update(n for it in s["headline"] for n in it["i"])
            # Rolled back since that release?
            latest_rb = rbs[0] if rbs else None
            if latest_rb and (not live or latest_rb["date"] > live["date"]):
                s["rolledBack"] = {"date": latest_rb["date"], "from": latest_rb["rolled_back_release"]}
        stages.append(s)
    issues = api("issues?state=open&per_page=50") or []
    open_issues = [{"n": i["number"], "t": i["title"]} for i in issues if "pull_request" not in i]
    numbers.update(o["n"] for o in open_issues)
    labels = {k: [v["label"], v["color"]] for k, v in issue_labels([], numbers).items()}
    return {"app": os.environ.get("APP") or name, "slug": slug,
            "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stages": stages, "labels": labels, "open": open_issues}


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;font-family:system-ui,sans-serif;background:#f4f5f7;color:#1d1f23}
main{padding:1.5rem 1rem 3rem;max-width:1200px;margin:0 auto}
a.back{display:inline-flex;align-items:center;gap:.3rem;min-height:44px;margin:-.4rem 0 .2rem;font-size:.9rem;font-weight:600;color:#3b5bdb;text-decoration:none}a.back:hover{text-decoration:underline}
header.top{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:.5rem;margin-bottom:1.2rem}
header.top h1{margin:0;font-size:1.4rem;display:flex;align-items:center;gap:.5rem}
header.top .sub{color:#6c757d;font-size:.82rem}
.lanes{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.9rem}
.lane{background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06);display:flex;flex-direction:column;position:relative}
.lane .bar{height:6px;border-radius:12px 12px 0 0}
.lane .head{padding:.8rem .9rem .3rem;display:flex;justify-content:space-between;align-items:center}
.lane h2{margin:0;font-size:1.05rem}
.open-site{font-size:.78rem;color:#3b5bdb;text-decoration:none;font-weight:600}.open-site:hover{text-decoration:underline}
.lane .body{padding:.3rem .9rem .9rem;flex:1}
.label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#6c757d;margin:.4rem 0 .45rem}
.count{display:inline-block;background:#f1f3f5;color:#495057;border-radius:999px;padding:0 .45rem;margin-left:.25rem}
ul.items{list-style:none;margin:0;padding:0;display:grid;gap:.45rem}
ul.items li{font-size:.88rem;line-height:1.35;padding:.45rem .55rem;border:1px solid #e9ecef;border-radius:8px}
.pill{display:inline-block;margin-left:.2rem;padding:0 .45rem;border-radius:999px;font-size:.7rem;font-weight:600;line-height:1.55;white-space:nowrap;vertical-align:.08em}
.keep{white-space:nowrap}
.uptodate{color:#237032;font-size:.88rem;padding:.4rem 0}
.more{font:inherit;font-size:.78rem;color:#495057;background:none;border:0;padding:.1rem 0;margin-top:.5rem;cursor:pointer;border-radius:4px}
.more:focus-visible,.open-site:focus-visible,a:focus-visible{outline:2px solid #3b5bdb;outline-offset:2px}
.morelist{margin:.3rem 0 0;padding-left:1.1rem;font-size:.8rem;color:#495057}
.hint{font-size:.75rem;color:#6c757d;margin:.6rem 0 0}
.version{font-size:1.35rem;font-weight:800;margin:.1rem 0 .15rem}
.when{font-size:.8rem;color:#6c757d;margin-bottom:.6rem}
.rel{font-size:.78rem;color:#3b5bdb;font-weight:600;text-decoration:none}
.rb{background:#f3f0ff;color:#5f3dc4;border-radius:8px;padding:.45rem .55rem;font-size:.82rem;margin-bottom:.6rem}
.foot{border-top:1px solid #f1f3f5;padding:.5rem .9rem;font-size:.75rem;color:#6c757d}
.arrow{position:absolute;top:2.2rem;right:-.78rem;width:1.5rem;height:1.5rem;border-radius:50%;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.15);display:grid;place-items:center;font-size:.8rem;color:#6c757d;z-index:2}
.issues{margin-top:1.3rem;background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06);padding:.8rem .9rem}
.issues h2{margin:0 0 .5rem;font-size:.95rem}
.issues ul{list-style:none;margin:0;padding:0;display:grid;gap:.3rem;font-size:.85rem}
.issues a{color:#1d1f23;text-decoration:none}.issues a:hover{text-decoration:underline}
.num{color:#6c757d;margin-right:.3rem}
.legend{margin-top:1rem;font-size:.78rem;color:#6c757d}
.page-tabs{display:inline-flex;background:#e9ecef;border-radius:12px;padding:3px;margin:0 0 1rem}
.page-tabs button{font:inherit;font-size:.9rem;font-weight:600;border:0;background:none;border-radius:9px;padding:.45rem 1.1rem;min-height:40px;cursor:pointer;color:#495057}
.page-tabs button[aria-selected="true"]{background:#fff;color:#1d1f23;box-shadow:0 1px 3px rgba(0,0,0,.12)}
.compare{background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06);padding:.9rem}
.compare h2{margin:0;font-size:1.05rem}.cmp-sub{margin:.3rem 0 .7rem;font-size:.82rem;color:#495057;max-width:46rem}
.cmp-tools{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin-bottom:.8rem}
.seg{display:inline-flex;background:#f1f3f5;border-radius:10px;padding:3px}.seg button{font:inherit;font-size:.82rem;font-weight:600;border:0;background:none;border-radius:8px;padding:.35rem .8rem;cursor:pointer;color:#495057;min-height:34px}
.seg button[aria-pressed="true"]{background:#fff;color:#1d1f23;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.cmp-reset{font:inherit;font-size:.82rem;font-weight:600;border:1px solid #dee2e6;background:#fff;border-radius:10px;padding:.35rem .8rem;min-height:40px;cursor:pointer}
.frames{display:flex;gap:1rem;overflow-x:auto;padding-bottom:.5rem}
.frame{flex:none;width:390px;position:relative}.frame .cap{display:flex;align-items:center;gap:.45rem;font-weight:700;font-size:.85rem;margin:0 0 .4rem}
.dot{width:.7rem;height:.7rem;border-radius:50%;flex:none}
.frame iframe{width:390px;height:760px;border:1px solid #dee2e6;border-radius:18px;background:#fff;display:block}
.frame .nosupport{position:absolute;inset:1.9rem 0 0;display:grid;place-items:center;padding:1.5rem;text-align:center;background:rgba(248,249,250,.96);border-radius:18px;font-size:.88rem;color:#495057}
.cmp-tabs{display:none}
@media (max-width:760px){.cmp-tabs{display:flex;gap:.3rem;margin-bottom:.6rem;flex-wrap:wrap}
.cmp-tabs button{font:inherit;font-size:.82rem;font-weight:600;border:1px solid #dee2e6;background:#fff;border-radius:99px;padding:.3rem .75rem;min-height:38px;display:inline-flex;align-items:center;gap:.35rem;cursor:pointer}
.cmp-tabs button[aria-selected="true"]{background:#1d1f23;color:#fff;border-color:#1d1f23}
.frames{display:block;overflow:visible}.frame{width:auto}.frame:not(.on){display:none}.frame .cap{display:none}.frame iframe{width:100%;height:72vh}.frame .nosupport{inset:0}}
[hidden]{display:none!important}
@media (max-width:760px){.lanes{grid-template-columns:1fr}.arrow{top:auto;bottom:-.85rem;right:50%;transform:translateX(50%) rotate(90deg)}}
</style></head><body><main>
<a class="back" id="back" href="../">← Back to the app</a>
<header class="top"><h1>__TITLE__</h1><span class="sub" id="updated"></span></header>
<nav class="page-tabs" role="tablist" aria-label="View"><button type="button" role="tab" id="tab-pipeline" aria-selected="true">Pipeline</button><button type="button" role="tab" id="tab-compare" aria-selected="false">Compare</button></nav>
<div id="pipeline-view"><div class="lanes" id="lanes"></div>
<section class="issues" id="issues"><h2>Open issues <span class="count" id="opencount"></span></h2><ul id="open"></ul></section></div>
<section class="compare" id="compare" aria-labelledby="cmp-title" hidden>
<h2 id="cmp-title">Compare stages</h2>
<p class="cmp-sub">The same sample list on every stage, so only the design differs. Add or tick things in any window and the others update too. It's kept in this browser only: your real lists and account aren't touched.</p>
<div class="cmp-tools"><div class="seg" role="group" aria-label="Theme"><button type="button" data-theme="light" aria-pressed="true">Light</button><button type="button" data-theme="dark" aria-pressed="false">Dark</button></div>
<button type="button" class="cmp-reset" id="cmp-reset">Reset sample</button></div>
<div class="cmp-tabs" role="tablist" aria-label="Stage"></div>
<div class="frames" id="frames"></div>
</section>
<p class="legend">Waiting items come from release notes where they exist, otherwise from change titles. Housekeeping (screenshots, notes) is left out. This page is rebuilt automatically on every deploy.</p>
</main>
<script>
const D=__DATA__;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function ago(iso){const m=Math.max(0,Math.round((Date.now()-new Date(iso).getTime())/60000));if(m<1)return 'just now';if(m<60)return m+' min ago';const h=Math.round(m/60);if(h<24)return h+' h ago';const d=Math.round(h/24);return d+(d===1?' day ago':' days ago');}
const fmt=iso=>new Date(iso).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'});
function lum(h){return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255).map(c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4).reduce((a,c,i)=>a+c*[.2126,.7152,.0722][i],0);}
function pill(n,withNum=true){const [l,c]=D.labels[n]||['','e9ecef'];const col=/^[0-9a-f]{6}$/i.test(c)?c:'e9ecef';const L=lum(col);const t=(L+.05)/.0637>=1.05/(L+.05)?'#1d1f23':'#fff';
 return `<span class="pill" style="background:#${col};color:${t}">${l?esc(l):''}${withNum?(l?' ':'')+'#'+n:''}</span>`;}
function item(x){const words=esc(x.t).split(' ');const last=words.pop();const pills=(x.i||[]).map(n=>'&nbsp;'+pill(n)).join('');return `<li>${words.join(' ')} <span class="keep">${last}${pills}</span></li>`;}
const lanes=document.getElementById('lanes');
D.stages.forEach((s,idx)=>{const el=document.createElement('section');el.className='lane';el.setAttribute('aria-label',s.name);let body='';
 if(s.key==='main'){
  if(s.rolledBack)body+=`<div class="rb">↩️ Rolled back ${ago(s.rolledBack.date)}${s.rolledBack.from?' (undid '+esc(s.rolledBack.from)+')':''}</div>`;
  body+=s.version?`<div class="label">Live now</div><div class="version">${esc(s.version)}</div><div class="when">Released ${ago(s.released)} · ${fmt(s.released)}</div>`
   +(s.headline&&s.headline.length?`<ul class="items">${s.headline.map(item).join('')}</ul>`:'')
   +(s.release?`<p><a class="rel" href="${esc(s.release)}">GitHub release ↗</a></p>`:''):`<div class="label">Live now</div><p class="hint">No releases yet.</p>`;
 }else{const items=s.items||[],more=s.more||[],n=items.length+more.length;
  if(!n)body=`<div class="label">Waiting to go to ${esc(s.next)}</div><div class="uptodate">✓ Up to date: nothing waiting</div>`;
  else{body=`<div class="label">Waiting to go to ${esc(s.next)} <span class="count">${n}</span></div><ul class="items">${items.map(item).join('')}</ul>`;
   if(more.length)body+=`<button class="more" aria-expanded="false">▸ + ${more.length} smaller change${more.length>1?'s':''}</button><ul class="morelist" hidden>${more.map(m=>`<li>${esc(m)}</li>`).join('')}</ul>`;
   if(s.kind==='changes')body+=`<p class="hint">Not released yet: change titles</p>`;}}
 el.innerHTML=`<div class="bar" style="background:${esc(s.color)}"></div><div class="head"><h2>${esc(s.name)}</h2><a class="open-site" href="${esc(s.url)}">Open ↗</a></div><div class="body">${body}</div><div class="foot">Last change ${ago(s.changed)}</div>`+(idx<D.stages.length-1?'<div class="arrow" aria-hidden="true">→</div>':'');
 const mb=el.querySelector('.more');if(mb)mb.addEventListener('click',()=>{const l=el.querySelector('.morelist');l.hidden=!l.hidden;mb.setAttribute('aria-expanded',!l.hidden);mb.textContent=(l.hidden?'▸':'▾')+mb.textContent.slice(1);});
 lanes.append(el);});
// "Back to the app": the stage page you came from (same site, not this page), else Production.
(function(){try{const r=document.referrer&&new URL(document.referrer);const b=document.getElementById('back');
 if(r&&r.origin===location.origin&&!r.pathname.includes('/pipeline/')){b.href=r.href;
  const m=r.pathname.match(/\/(dev|alpha|staging)\//);b.textContent='← Back to '+(m?m[1][0].toUpperCase()+m[1].slice(1):'the app');}}catch(e){}})();
// Pipeline | Compare tabs. Compare shows every stage side by side (one at a time
// on a phone) in compare mode: the same shared sample data (compare.js, added to
// each stage by the deploy). Frames load only when Compare is first opened.
(function(){const S=D.stages.slice();let theme='light',cur=S[0]&&S[0].key;
const fr=document.getElementById('frames'),tabs=document.querySelector('.cmp-tabs');
const src=s=>s.url+(s.url.includes('?')?'&':'?')+'compare=1&theme='+theme;
fr.innerHTML=S.map(s=>`<div class="frame${s.key===cur?' on':''}" data-k="${esc(s.key)}"><p class="cap"><span class="dot" style="background:${esc(s.color)}"></span>${esc(s.name)}</p><iframe title="${esc(s.name)}, compare mode"></iframe></div>`).join('');
tabs.innerHTML=S.map(s=>`<button type="button" role="tab" data-k="${esc(s.key)}" aria-selected="${s.key===cur}"><span class="dot" style="background:${esc(s.color)}"></span>${esc(s.name)}</button>`).join('');
const frames=[...fr.querySelectorAll('iframe')];let loaded=false;
frames.forEach((f,i)=>f.addEventListener('load',()=>{const box=f.parentNode;if(!f.getAttribute('src')||f.getAttribute('src')==='about:blank'){const n0=box.querySelector('.nosupport');if(n0)n0.remove();return;}let ok=false;try{ok=!!f.contentWindow.COMPARE_READY;}catch(e){}
 let n=box.querySelector('.nosupport');if(!ok&&!n){n=document.createElement('div');n.className='nosupport';n.textContent='Compare mode isn\'t on this stage yet. It arrives with the stage\'s next deploy.';box.append(n);}else if(ok&&n)n.remove();}));
// On a phone only the chosen stage is loaded: iPhone Safari lays out a hidden
// frame wrongly (rows came out too tall) and doesn't fix it when it's shown.
const phone=()=>matchMedia('(max-width:760px)').matches;
const load=()=>{frames.forEach((f,i)=>{const want=(!phone()||S[i].key===cur)?src(S[i]):'about:blank';if(f.getAttribute('src')!==want)f.src=want;});loaded=true;};
matchMedia('(max-width:760px)').addEventListener('change',()=>{if(loaded)load();});
tabs.onclick=e=>{const b=e.target.closest('button');if(!b)return;cur=b.dataset.k;tabs.querySelectorAll('button').forEach(x=>x.setAttribute('aria-selected',x.dataset.k===cur));fr.querySelectorAll('.frame').forEach(x=>x.classList.toggle('on',x.dataset.k===cur));if(loaded)load();};
document.querySelector('.seg').onclick=e=>{const b=e.target.closest('button');if(!b)return;theme=b.dataset.theme;document.querySelectorAll('.seg button').forEach(x=>x.setAttribute('aria-pressed',x===b));if(loaded)load();};
document.getElementById('cmp-reset').onclick=()=>{const f=frames.find(x=>{try{return x.contentWindow.compareReset;}catch(e){return false;}});if(f)f.contentWindow.compareReset();if(loaded)setTimeout(load,150);};
const show=t=>{const c=t==='compare';document.getElementById('compare').hidden=!c;document.getElementById('pipeline-view').hidden=c;
 document.getElementById('tab-compare').setAttribute('aria-selected',c);document.getElementById('tab-pipeline').setAttribute('aria-selected',!c);
 if(c&&!loaded)load();try{localStorage.setItem('pipeline-tab:'+D.slug,t);}catch(e){}};
document.getElementById('tab-pipeline').onclick=()=>show('pipeline');document.getElementById('tab-compare').onclick=()=>show('compare');
let last='pipeline';try{last=localStorage.getItem('pipeline-tab:'+D.slug)||'pipeline';}catch(e){}show(last);})();
document.getElementById('updated').textContent='Updated '+ago(D.updated)+' · '+fmt(D.updated);
function showOpen(list){document.getElementById('issues').hidden=!list.length;
 document.getElementById('opencount').textContent=list.length;
 document.getElementById('open').innerHTML=list.map(o=>`<li><a href="https://github.com/${esc(D.slug)}/issues/${o.n}"><span class="num">#${o.n}</span>${esc(o.t)}</a> ${D.labels[o.n]?pill(o.n,false):''}</li>`).join('');}
showOpen(D.open);
// Open issues change after the page is built (e.g. the release closes them a
// minute later), so fetch the current list when the page is opened; keep the
// built-in list if GitHub can't be reached.
const TYPES=['bug','feature','tweak','performance'];
fetch(`https://api.github.com/repos/${D.slug}/issues?state=open&per_page=50`,{headers:{Accept:'application/vnd.github+json'}})
 .then(r=>r.ok?r.json():Promise.reject(r.status)).then(items=>{
  const list=items.filter(i=>!i.pull_request).map(i=>{const by=Object.fromEntries(i.labels.map(l=>[l.name,l]));
   const pick=TYPES.map(t=>by[t]).find(Boolean)||i.labels.find(l=>!l.name.startsWith('priority'));
   if(pick)D.labels[i.number]=[pick.name,pick.color];return {n:i.number,t:i.title};});
  showOpen(list);}).catch(()=>{});
</script></body></html>
"""


def main():
    repo, slug, out = sys.argv[1:4]
    data = build(repo, slug)
    title = html.escape(f"{data['app']} pipeline")
    page = PAGE.replace("__TITLE__", title).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    waiting_n = sum(len(s.get("items", [])) + len(s.get("more", [])) for s in data["stages"])
    print(f"Pipeline: {len(data['stages'])} stages, {waiting_n} waiting item(s), "
          f"{len(data['open'])} open issue(s) -> {out}")


if __name__ == "__main__":
    main()
