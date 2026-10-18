"""Blue operator surface for logging contacts on frozen fictional provider pages."""

from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from ..benchmark import Refusal
from .arena import ArenaStore
from .behavior import BehaviorSessions
from .dataset import _inside


async def _body(request, fields=None, *, limit=1048576):
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > limit:
            raise HTTPException(413, "Provider request byte budget exceeded")
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise HTTPException(422, "JSON provider request required") from None
    if fields is not None and (not isinstance(value, dict) or set(value) != fields):
        raise HTTPException(422, "Exact provider request fields required")
    return value


def _access(root, arena, operation, *, status=422):
    store = ArenaStore(arena, root)
    try:
        return operation(BehaviorSessions(store))
    except Refusal as error:
        raise HTTPException(status, str(error)) from None
    finally:
        store.close()


def provider_board(state):
    options = "".join(f'<option value="{row["capture_id"]}">{escape(row["tags"]["provider"])} · seed {row["tags"]["seed"]} · phase {row["tags"]["phase"]} · {row["capture_id"][:8]}</option>' for row in state["captures"])
    rows = "".join(f'<tr><td><a href="/provider-session/{row["session_id"]}">{escape(row["session_id"][:12])}</a></td><td>{escape(row["state"])}</td><td>{row["score"]["features"]["contacts"] if row["score"] else "—"}</td><td>{escape(", ".join(row["score"]["flags"])) if row["score"] else escape(row["cancel_reason"] or "Pending")}</td><td>{escape(", ".join(row["attempt_links"])) or "Unlinked"}</td></tr>' for row in state["provider_sessions"])
    return f'''<h2>Provider behavior</h2><p>Blue records only contacts observed by the fictional page. Rules are frozen before new sessions. Flags describe patterns; human validation is pending and no sanctions apply.</p>
<label for="provider-capture">Capture for a new provider session</label><select id="provider-capture">{options}</select><button id="provider-start">Start provider session</button><p id="provider-status" role="status"></p>
<table><thead><tr><th>Session</th><th>State</th><th>Contacts</th><th>Pattern flags</th><th>Linked attempts</th></tr></thead><tbody>{rows}</tbody></table>
<script>document.querySelector('#provider-start').onclick=async()=>{{try{{const r=await fetch('/api/provider/sessions',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{capture_id:document.querySelector('#provider-capture').value}})}}),d=await r.json();if(!r.ok)throw Error(d.detail);location.assign('/provider-session/'+d.session_id)}}catch(e){{document.querySelector('#provider-status').textContent=String(e)}}}};</script>'''


def install_provider_routes(app, root, arena):
    root, arena = Path(root), Path(arena)

    @app.post("/api/provider/sessions")
    async def start(request: Request):
        data = await _body(request, {"capture_id"}, limit=1024)
        return _access(root, arena, lambda behavior: behavior.start(data["capture_id"]))

    @app.get("/api/provider/sessions")
    def sessions():
        return _access(root, arena, lambda behavior: {"provider_sessions": behavior.sessions()})

    @app.post("/api/provider/sessions/{session_id}/contacts")
    async def finish(session_id: str, request: Request):
        packet = await _body(request)
        return _access(root, arena, lambda behavior: behavior.finish(session_id, packet))

    @app.post("/api/provider/sessions/{session_id}/cancel")
    async def cancel(session_id: str, request: Request):
        data = await _body(request, {"reason"}, limit=4096)
        return _access(root, arena, lambda behavior: behavior.cancel(session_id, data["reason"]))

    @app.post("/api/provider/sessions/{session_id}/link")
    async def link(session_id: str, request: Request):
        data = await _body(request, {"attempt_id"}, limit=1024)
        return _access(root, arena, lambda behavior: behavior.link(session_id, data["attempt_id"]))

    @app.get("/provider-session/{session_id}/page", response_class=HTMLResponse)
    def page(session_id: str):
        def source(behavior):
            session = behavior._row(session_id)
            sample = behavior.arena.sample(session["capture_id"])
            path = _inside(root, sample["source_page"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != sample["sha256"]["source_page"]:
                raise Refusal("provider source changed after capture")
            return path.read_text(), session
        html, session = _access(root, arena, source, status=404)
        # This script exports only pointer contacts; field labels/text never enter a packet.
        script = f'''<script>(()=>{{const session={json.dumps(session_id)},active=new Map();function record(e){{if(!e.isTrusted)return;let kind={{pointerdown:'down',pointermove:'move',pointerup:'up',pointercancel:'cancel'}}[e.type];if(kind==='down'){{let slot=0;while([...active.values()].includes(slot))slot++;if(slot>99)return;active.set(e.pointerId,slot)}}if(!active.has(e.pointerId))return;const event={{kind,time_ms:performance.timeOrigin+e.timeStamp,x:e.clientX,y:e.clientY,pointer:active.get(e.pointerId)}};parent.postMessage({{type:'provider-contact-event',session_id:session,event}},location.origin);if(kind==='up'||kind==='cancel')active.delete(e.pointerId)}}for(const type of ['pointerdown','pointermove','pointerup','pointercancel'])document.addEventListener(type,record,true)}})();</script>'''
        target = "</body>" if "</body>" in html else "</html>"
        if target not in html:
            raise HTTPException(422, "Unsupported frozen provider page")
        return html.replace(target, script + target, 1)

    @app.get("/provider-session/{session_id}", response_class=HTMLResponse)
    def player(session_id: str):
        session = _access(root, arena, lambda behavior: behavior._row(session_id), status=404)
        closed = session["state"] != "open"
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blue provider session</title>
<style>body{{font:16px/24px system-ui;max-width:1100px;padding:20px;margin:30px auto;background:#f4f7ff;color:#182b46}}h1{{font-size:32px;line-height:40px;margin:0 0 20px}}p{{margin:0 0 16px}}.columns{{display:grid;grid-template-columns:390px minmax(0,1fr);gap:32px}}iframe{{display:block;width:390px;height:844px;border:0;border-radius:24px;background:white}}button,select{{padding:12px;margin:8px 8px 8px 0;border:1px solid #cbd8ec;border-radius:10px}}button{{background:#2858a3;color:white;cursor:pointer}}button:disabled{{opacity:.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;max-height:420px;overflow:auto}}[role=status]{{padding:14px;background:#fff4cd;border-radius:12px}}@media(max-width:800px){{.columns{{grid-template-columns:1fr}}}}</style>
<h1>Blue provider session</h1><p><a href="/arena/">Round review</a> · Training held</p><div class="columns"><iframe id="provider" title="Frozen fictional iPhone provider page" src="/provider-session/{session_id}/page"></iframe><section><h2>Observe page contacts</h2><p>Click or move within the phone. The page exports pointer timing and coordinates only. Save ends this contact window; cancelled sessions have no behavior score.</p><p>State: <span id="session-state">{escape(session["state"])}</span> · scorer {escape(session["policy"]["version"])}</p><p>Robot identity and human controls remain unmeasured. These flags trigger no sanctions.</p>
<p id="event-count">0 contact events collected in this view</p><button id="save" {'disabled' if closed else ''}>Save contacts</button><button id="cancel" {'disabled' if closed else ''}>Cancel session</button><pre id="result" role="status">{escape(json.dumps(session["score"],indent=2)) if session["score"] else 'Contact score pending.'}</pre>
<label for="attempt-link">Saved attempt ID on this capture</label><input id="attempt-link"><button id="link">Link saved attempt</button><p id="link-result"></p><details><summary>Frozen provenance</summary><pre>{escape(json.dumps(session["policy"],indent=2))}</pre></details></section></div>
<script>const sid={json.dumps(session_id)},events=[],frame=document.querySelector('#provider'),result=document.querySelector('#result');let recording={str(not closed).lower()},overflow=false;
function alignPhone(){{frame.style.transform='none';const r=frame.getBoundingClientRect();frame.style.transform='translate('+(Math.round(r.x)-r.x)+'px,'+(Math.round(r.y)-r.y)+'px)'}}document.fonts.ready.then(()=>requestAnimationFrame(alignPhone));window.addEventListener('resize',alignPhone);
window.addEventListener('message',e=>{{const d=e.data;if(!recording||e.origin!==location.origin||e.source!==frame.contentWindow||!d||d.type!=='provider-contact-event'||d.session_id!==sid)return;if(Object.keys(d.event||{{}}).sort().join(',')!=='kind,pointer,time_ms,x,y')return;if(events.length>=5000){{overflow=true;recording=false;document.querySelector('#save').disabled=true;result.textContent='Contact limit reached. Cancel the session; no score is saved.';return}}events.push(d.event);document.querySelector('#event-count').textContent=events.length+' contact events collected in this view'}});
async function send(suffix,payload){{const r=await fetch('/api/provider/sessions/'+sid+'/'+suffix,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}}),d=await r.json();if(!r.ok)throw Error(d.detail||'Request failed');return d}}
document.querySelector('#save').onclick=async()=>{{recording=false;try{{const d=await send('contacts',{{schema:'website-contact-session/1',run_id:sid,viewport:{json.dumps(session['viewport'])},events}});result.textContent=JSON.stringify(d,null,2);document.querySelector('#session-state').textContent='closed';document.querySelector('#save').disabled=true;document.querySelector('#cancel').disabled=true}}catch(e){{result.textContent=String(e)}}}};
document.querySelector('#cancel').onclick=async()=>{{recording=false;try{{result.textContent=JSON.stringify(await send('cancel',{{reason:overflow?'contact event limit reached':'operator cancelled this contact window'}}),null,2);document.querySelector('#session-state').textContent='cancelled';document.querySelector('#save').disabled=true;document.querySelector('#cancel').disabled=true}}catch(e){{result.textContent=String(e)}}}};
document.querySelector('#link').onclick=async()=>{{try{{document.querySelector('#link-result').textContent=JSON.stringify(await send('link',{{attempt_id:document.querySelector('#attempt-link').value}}))}}catch(e){{document.querySelector('#link-result').textContent=String(e)}}}};</script></html>'''
