"""
🪝 Webhook Debugger — Flask API
- Catches ALL paths (any random URL)
- Left panel: live request list (auto-refreshes only the list)
- Right panel: selected request detail (never auto-refreshes)
- Always returns 200 OK for every webhook

Run:
    pip install flask
    python webhook_debugger.py

Send to ANY path:
    curl -X POST http://localhost:5000/anything/you/want -d '{"hi":1}'
"""

from flask import Flask, request, jsonify, render_template_string
import json, time, uuid
from datetime import datetime
from collections import deque

app = Flask(__name__)
MAX_REQUESTS = 200
webhook_log = deque(maxlen=MAX_REQUESTS)

METHODS = ["GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"]

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>🪝 Webhook Debugger</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet"/>
<style>
:root{
  --bg:#0a0c10;--surface:#0e1117;--card:#13181f;--card2:#181e27;
  --border:#1e2530;--border2:#252d3a;
  --accent:#00f5a0;--accent2:#00d9e8;--warn:#f7b731;--err:#ff4757;--purple:#a859ff;
  --muted:#3d4654;--text:#dde4ed;--text2:#7a8799;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;overflow:hidden;}
body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;display:flex;flex-direction:column;}
body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,245,160,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,245,160,.025) 1px,transparent 1px);
  background-size:44px 44px;pointer-events:none;z-index:0;}

.topbar{position:relative;z-index:2;display:flex;align-items:center;gap:14px;padding:0 18px;
  height:52px;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0;}
.topbar h1{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;
  background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.live-dot{width:7px;height:7px;background:var(--accent);border-radius:50%;
  box-shadow:0 0 8px var(--accent);animation:pulse 2s infinite;flex-shrink:0;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.topbar-meta{font-size:11px;color:var(--text2);margin-left:auto;}
.topbar-meta span{color:var(--accent);font-weight:700;}
.clear-btn{border:1px solid var(--border2);background:none;color:var(--text2);
  border-radius:6px;padding:5px 13px;font-family:inherit;font-size:11px;cursor:pointer;transition:.15s;}
.clear-btn:hover{border-color:var(--err);color:var(--err);}

.hint-bar{background:var(--card);border-bottom:1px solid var(--border);padding:7px 18px;
  font-size:11px;color:var(--text2);display:flex;align-items:center;gap:8px;flex-shrink:0;z-index:1;position:relative;}
.hint-bar code{background:var(--surface);border:1px solid var(--border2);border-radius:3px;
  padding:1px 6px;color:var(--accent);font-size:11px;}

.main{position:relative;z-index:1;display:flex;flex:1;overflow:hidden;}

/* LEFT */
.left{width:320px;flex-shrink:0;border-right:1px solid var(--border);display:flex;flex-direction:column;background:var(--surface);}
.left-head{padding:10px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;}
#filter{flex:1;background:var(--card);border:1px solid var(--border2);color:var(--text);
  border-radius:6px;padding:6px 11px;font-family:inherit;font-size:11px;outline:none;}
#filter:focus{border-color:var(--accent2);}
.req-count{font-size:10px;color:var(--muted);white-space:nowrap;}
.req-list{flex:1;overflow-y:auto;}
.req-list::-webkit-scrollbar{width:3px;}
.req-list::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}

.req-item{padding:10px 12px;border-bottom:1px solid var(--border);cursor:pointer;transition:.1s;display:flex;flex-direction:column;gap:4px;}
.req-item:hover{background:var(--card);}
.req-item.selected{background:var(--card2);border-left:2px solid var(--accent2);padding-left:10px;}
.req-item.new-flash{animation:nf .5s ease;}
@keyframes nf{0%{background:rgba(0,245,160,.13)}100%{background:transparent}}
.ri-row1{display:flex;align-items:center;gap:7px;}
.ri-method{font-size:10px;font-weight:700;border-radius:3px;padding:2px 7px;letter-spacing:.04em;white-space:nowrap;}
.m-GET   {background:rgba(0,245,160,.12);color:var(--accent);}
.m-POST  {background:rgba(0,217,232,.12);color:var(--accent2);}
.m-PUT   {background:rgba(247,183,49,.12);color:var(--warn);}
.m-DELETE{background:rgba(255,71,87,.12);color:var(--err);}
.m-PATCH {background:rgba(168,89,255,.12);color:var(--purple);}
.m-OTHER {background:rgba(122,135,153,.12);color:var(--text2);}
.ri-path{font-size:12px;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;}
.ri-time{font-size:10px;color:var(--muted);white-space:nowrap;}
.ri-row2{display:flex;gap:8px;font-size:10px;color:var(--muted);}
.empty-left{text-align:center;padding:48px 16px;color:var(--muted);font-size:11px;line-height:1.9;}
.empty-left .big{font-size:30px;margin-bottom:8px;}

/* RIGHT */
.right{flex:1;overflow:hidden;display:flex;flex-direction:column;}
.detail-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--muted);font-size:12px;gap:10px;}
.detail-empty .icon{font-size:44px;}
.detail-wrap{display:flex;flex-direction:column;height:100%;overflow:hidden;}
.detail-topbar{padding:12px 18px;border-bottom:1px solid var(--border);background:var(--surface);
  display:flex;align-items:center;gap:10px;flex-shrink:0;flex-wrap:wrap;}
.detail-method{font-size:11px;font-weight:700;border-radius:4px;padding:3px 9px;letter-spacing:.04em;}
.detail-url{font-size:12px;color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.detail-ts{font-size:10px;color:var(--muted);white-space:nowrap;}
.detail-id{font-size:10px;color:var(--muted);background:var(--card);border:1px solid var(--border2);border-radius:4px;padding:2px 7px;}

.tabs{display:flex;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0;overflow-x:auto;}
.tabs::-webkit-scrollbar{height:0;}
.tab-btn{padding:9px 16px;background:none;border:none;border-bottom:2px solid transparent;
  color:var(--text2);font-family:inherit;font-size:11px;cursor:pointer;white-space:nowrap;transition:.12s;}
.tab-btn:hover{color:var(--text);}
.tab-btn.active{color:var(--accent2);border-bottom-color:var(--accent2);}

.tab-content{flex:1;overflow-y:auto;padding:18px;}
.tab-content::-webkit-scrollbar{width:4px;}
.tab-content::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
.tab-pane{display:none;}
.tab-pane.active{display:block;}

table{width:100%;border-collapse:collapse;font-size:12px;}
th{text-align:left;color:var(--muted);font-size:10px;letter-spacing:.07em;text-transform:uppercase;padding:5px 10px;border-bottom:1px solid var(--border);}
td{padding:7px 10px;border-bottom:1px solid rgba(30,37,48,.5);vertical-align:top;word-break:break-all;}
td:first-child{color:var(--text2);width:32%;white-space:nowrap;}
td:last-child{color:var(--text);}
tr:last-child td{border-bottom:none;}
.empty-row{color:var(--muted);font-style:italic;font-size:11px;}

pre{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:14px;overflow-x:auto;font-size:11px;line-height:1.7;color:var(--text);white-space:pre-wrap;word-break:break-all;}
.copy-btn{border:1px solid var(--border2);background:var(--card);color:var(--text2);
  border-radius:5px;padding:5px 13px;font-family:inherit;font-size:11px;cursor:pointer;transition:.12s;margin-bottom:10px;display:inline-block;}
.copy-btn:hover{border-color:var(--accent2);color:var(--accent2);}
.sec-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin:16px 0 7px;}
.sec-label:first-child{margin-top:0;}

#toast{position:fixed;bottom:22px;right:22px;background:var(--card);border:1px solid var(--accent);
  border-radius:7px;padding:9px 16px;font-size:11px;color:var(--accent);z-index:999;
  opacity:0;transform:translateY(10px);transition:.2s;pointer-events:none;}
#toast.show{opacity:1;transform:translateY(0);}
</style>
</head>
<body>

<div class="topbar">
  <div class="live-dot"></div>
  <h1>🪝 Webhook Debugger</h1>
  <div class="topbar-meta">Captured: <span id="total-count">0</span></div>
  <button class="clear-btn" onclick="clearAll()">🗑 Clear All</button>
</div>
<div class="hint-bar">
  Send to <strong>any</strong> path →
  <code id="base-url-hint"></code><code>/stripe/events</code>
  <code>/github/push</code>
  <code>/anything</code>
  &nbsp;— always returns <code>200 OK</code>
</div>

<div class="main">
  <!-- LEFT -->
  <div class="left">
    <div class="left-head">
      <input id="filter" type="text" placeholder="Filter path, method, IP…" oninput="applyFilter()"/>
      <span class="req-count" id="req-count">0</span>
    </div>
    <div class="req-list" id="req-list">
      <div class="empty-left"><div class="big">📭</div>No requests yet.<br>Send to any path on this host.</div>
    </div>
  </div>

  <!-- RIGHT -->
  <div class="right">
    <div id="detail-empty" class="detail-empty">
      <div class="icon">👈</div>
      <div>Click a request to inspect it</div>
    </div>
    <div id="detail-wrap" class="detail-wrap" style="display:none;">
      <div class="detail-topbar">
        <span class="detail-method" id="d-method"></span>
        <span class="detail-url"    id="d-url"></span>
        <span class="detail-ts"     id="d-ts"></span>
        <span class="detail-id"     id="d-id"></span>
      </div>
      <div class="tabs">
        <button class="tab-btn active" data-tab="overview" onclick="switchTab('overview')">Overview</button>
        <button class="tab-btn" data-tab="headers"  onclick="switchTab('headers')">Headers</button>
        <button class="tab-btn" data-tab="params"   onclick="switchTab('params')">Query Params</button>
        <button class="tab-btn" data-tab="body"     onclick="switchTab('body')">Body</button>
        <button class="tab-btn" data-tab="form"     onclick="switchTab('form')">Form / Files</button>
        <button class="tab-btn" data-tab="cookies"  onclick="switchTab('cookies')">Cookies</button>
        <button class="tab-btn" data-tab="raw"      onclick="switchTab('raw')">Raw JSON</button>
      </div>
      <div class="tab-content">
        <div class="tab-pane active" id="tab-overview"></div>
        <div class="tab-pane"        id="tab-headers"></div>
        <div class="tab-pane"        id="tab-params"></div>
        <div class="tab-pane"        id="tab-body"></div>
        <div class="tab-pane"        id="tab-form"></div>
        <div class="tab-pane"        id="tab-cookies"></div>
        <div class="tab-pane"        id="tab-raw"></div>
      </div>
    </div>
  </div>
</div>

<div id="toast">✓ Copied!</div>

<script>
document.getElementById('base-url-hint').textContent = location.origin;

let allData = [], filtered = [], selectedId = null, knownIds = new Set();

const MC = {GET:'m-GET',POST:'m-POST',PUT:'m-PUT',DELETE:'m-DELETE',PATCH:'m-PATCH'};
function mc(m){ return MC[(m||'').toUpperCase()]||'m-OTHER'; }
function esc(s){ return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function ago(ts){
  const s=Math.round(Date.now()/1000-ts);
  if(s<5)return 'just now'; if(s<60)return s+'s ago';
  if(s<3600)return Math.floor(s/60)+'m ago'; return Math.floor(s/3600)+'h ago';
}
function toast(){ const t=document.getElementById('toast'); t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),1500); }
function copyText(t){ navigator.clipboard.writeText(t).then(toast); }

function tbl(obj){
  if(!obj||!Object.keys(obj).length) return '<table><tr><td colspan="2" class="empty-row">— none —</td></tr></table>';
  return '<table><tr><th>Key</th><th>Value</th></tr>'
    +Object.entries(obj).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${esc(typeof v==='object'?JSON.stringify(v):v)}</td></tr>`).join('')
    +'</table>';
}
function hl(str){
  try{
    const s=JSON.stringify(JSON.parse(str),null,2);
    return s.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,m=>{
      let c='color:#79c0ff';
      if(/^"/.test(m)) c=/:$/.test(m)?'color:#ff7b72':'color:#a5d6ff';
      else if(/true|false/.test(m)) c='color:#79c0ff';
      else if(/null/.test(m)) c='color:#6e7681';
      return `<span style="${c}">${m}</span>`;
    });
  }catch{return esc(str);}
}

/* ── LEFT LIST (auto-updates) ── */
function applyFilter(){
  const q=(document.getElementById('filter').value||'').toLowerCase();
  filtered=q?allData.filter(r=>r.method.toLowerCase().includes(q)||r.path.toLowerCase().includes(q)||(r.remote_addr||'').includes(q)):allData;
  renderList();
}
function renderList(){
  document.getElementById('total-count').textContent=allData.length;
  document.getElementById('req-count').textContent=filtered.length;
  const el=document.getElementById('req-list');
  if(!filtered.length){
    el.innerHTML=allData.length
      ?'<div class="empty-left"><div class="big">🔍</div>No matches.</div>'
      :'<div class="empty-left"><div class="big">📭</div>No requests yet.<br>Send to any path.</div>';
    return;
  }
  el.innerHTML=filtered.map(r=>`
<div class="req-item${r.id===selectedId?' selected':''}" id="item-${r.id}" onclick="selectReq('${r.id}')">
  <div class="ri-row1">
    <span class="ri-method ${mc(r.method)}">${esc(r.method)}</span>
    <span class="ri-path">${esc(r.path)}</span>
    <span class="ri-time">${ago(r.timestamp)}</span>
  </div>
  <div class="ri-row2">
    <span>${esc(r.remote_addr||'')}</span>
    ${r.content_type?`<span>${esc(r.content_type.split(';')[0])}</span>`:''}
    ${r.content_length?`<span>${r.content_length}B</span>`:''}
  </div>
</div>`).join('');
}

/* ── RIGHT DETAIL (only on click — never auto-updates) ── */
function selectReq(id){
  selectedId=id;
  const r=allData.find(x=>x.id===id); if(!r) return;
  document.querySelectorAll('.req-item').forEach(el=>el.classList.toggle('selected',el.id==='item-'+id));

  document.getElementById('detail-empty').style.display='none';
  document.getElementById('detail-wrap').style.display='flex';

  const dm=document.getElementById('d-method');
  dm.textContent=r.method; dm.className='detail-method '+mc(r.method);
  document.getElementById('d-url').textContent=r.url;
  document.getElementById('d-ts').textContent=r.datetime;
  document.getElementById('d-id').textContent='#'+r.id;

  // Overview
  document.getElementById('tab-overview').innerHTML=`<table>
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Request ID</td><td>${esc(r.id)}</td></tr>
    <tr><td>Timestamp</td><td>${esc(r.datetime)}</td></tr>
    <tr><td>Method</td><td>${esc(r.method)}</td></tr>
    <tr><td>Full URL</td><td>${esc(r.url)}</td></tr>
    <tr><td>Path</td><td>${esc(r.path)}</td></tr>
    <tr><td>Query String</td><td>${esc(r.query_string||'—')}</td></tr>
    <tr><td>Remote IP</td><td>${esc(r.remote_addr||'—')}</td></tr>
    <tr><td>Host</td><td>${esc(r.host||'—')}</td></tr>
    <tr><td>Scheme</td><td>${esc(r.scheme||'—')}</td></tr>
    <tr><td>Content-Type</td><td>${esc(r.content_type||'—')}</td></tr>
    <tr><td>Content-Length</td><td>${r.content_length!=null?esc(r.content_length)+' bytes':'—'}</td></tr>
    <tr><td>User-Agent</td><td>${esc(r.user_agent||'—')}</td></tr>
  </table>`;

  document.getElementById('tab-headers').innerHTML=tbl(r.headers);
  document.getElementById('tab-params').innerHTML=tbl(r.query_params);

  // Body
  let bHtml='';
  if(r.json_body!==null&&r.json_body!==undefined){
    bHtml=`<button class="copy-btn" onclick="copyText(${JSON.stringify(JSON.stringify(r.json_body,null,2))})">Copy JSON</button><pre>${hl(JSON.stringify(r.json_body))}</pre>`;
  } else if(r.body_raw&&r.body_raw.length){
    bHtml=`<button class="copy-btn" onclick="copyText(${JSON.stringify(r.body_raw)})">Copy Raw</button><pre>${esc(r.body_raw)}</pre>`;
  } else { bHtml='<p style="color:var(--muted);font-size:12px;">— No body —</p>'; }
  document.getElementById('tab-body').innerHTML=bHtml;

  // Form / Files
  document.getElementById('tab-form').innerHTML=
    `<p class="sec-label">Form Fields</p>${tbl(r.form_data)}`
    +`<p class="sec-label">Uploaded Files</p>`
    +(r.files&&r.files.length
      ?'<table><tr><th>Field</th><th>Filename</th><th>Type</th></tr>'
        +r.files.map(f=>`<tr><td>${esc(f.field)}</td><td>${esc(f.filename)}</td><td>${esc(f.content_type)}</td></tr>`).join('')+'</table>'
      :'<table><tr><td class="empty-row">— none —</td></tr></table>');

  document.getElementById('tab-cookies').innerHTML=tbl(r.cookies);

  const raw=JSON.stringify(r,null,2);
  document.getElementById('tab-raw').innerHTML=
    `<button class="copy-btn" onclick="copyText(${JSON.stringify(raw)})">Copy Full JSON</button><pre>${hl(raw)}</pre>`;

  switchTab('overview');
}

function switchTab(name){
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  document.getElementById('tab-'+name).classList.add('active');
}

/* ── POLL — only updates left list ── */
async function poll(){
  try{
    const data=await(await fetch('/api/requests')).json();
    const newIds=data.map(r=>r.id).filter(id=>!knownIds.has(id));
    data.forEach(r=>knownIds.add(r.id));
    allData=data;
    applyFilter();
    newIds.forEach(id=>{
      const el=document.getElementById('item-'+id);
      if(el){el.classList.remove('new-flash');void el.offsetWidth;el.classList.add('new-flash');}
    });
  }catch(e){console.error(e);}
}

async function clearAll(){
  if(!confirm('Clear all requests?')) return;
  await fetch('/api/clear',{method:'POST'});
  allData=[];filtered=[];selectedId=null;knownIds=new Set();
  document.getElementById('detail-empty').style.display='flex';
  document.getElementById('detail-wrap').style.display='none';
  renderList();
}

poll();
setInterval(poll, 2500);
</script>
</body>
</html>
"""

# ── capture helper ──
def capture():
    ts = time.time()
    json_body = None
    try: json_body = request.get_json(force=False, silent=True)
    except: pass
    try: body_raw = request.get_data(as_text=True)
    except: body_raw = ""
    return {
        "id":             str(uuid.uuid4())[:8],
        "timestamp":      ts,
        "datetime":       datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "method":         request.method,
        "url":            request.url,
        "path":           request.path,
        "query_string":   request.query_string.decode("utf-8","replace"),
        "query_params":   dict(request.args),
        "host":           request.host,
        "scheme":         request.scheme,
        "remote_addr":    request.remote_addr,
        "content_type":   request.content_type,
        "content_length": request.content_length,
        "user_agent":     request.headers.get("User-Agent",""),
        "headers":        dict(request.headers),
        "form_data":      dict(request.form),
        "files":          [{"field":k,"filename":f.filename,"content_type":f.content_type} for k,f in request.files.items()],
        "json_body":      json_body,
        "body_raw":       body_raw,
        "cookies":        dict(request.cookies),
    }

# ── routes ──
@app.route("/")
def dashboard():
    return render_template_string(HTML)

@app.route("/api/requests")
def api_requests():
    return jsonify(list(webhook_log))

@app.route("/api/clear", methods=["POST"])
def api_clear():
    webhook_log.clear()
    return jsonify({"status": "cleared"})

# catch-all — every other path
@app.route("/<path:any_path>", methods=METHODS)
def catch_all(any_path=None):
    entry = capture()
    webhook_log.appendleft(entry)
    print(f"[{entry['datetime']}] {entry['method']:7s} {entry['path']}  —  {entry['remote_addr']}")
    return jsonify({"status":"captured","request_id":entry["id"],"message":"Received. Open http://localhost:5000 to inspect."}), 200

if __name__ == "__main__":
    print("="*56)
    print("  🪝  Webhook Debugger")
    print("="*56)
    print("  Dashboard  →  http://localhost:5000/")
    print("  Any path   →  http://localhost:5000/<anything>")
    print()
    print("  curl -X POST http://localhost:5000/stripe/webhook \\")
    print('       -H "Content-Type: application/json" \\')
    print("       -d '{\"event\":\"payment.success\"}'")
    print("="*56)
    app.run(debug=True, port=5000)
