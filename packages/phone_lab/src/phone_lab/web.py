from __future__ import annotations

import html
import json
import secrets

from fastapi import FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from .benchmark import Benchmark, Refusal, Session


class Create(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device: StrictStr
    seed: StrictInt
    width: StrictInt = 390
    height: StrictInt = 700
    task: StrictStr = "tap"
    cohort: StrictStr = "generated"
    participant: StrictStr = "generated"
    consent_ref: StrictStr | None = None


def page(s: Session) -> str:
    instruction = {
        "tap": "Tap Continue",
        "drag": "Move Grip to Goal",
        "entry": f"Enter {s.expected_value} then press Check",
        "menu": "Open Menu then choose Orange",
        "overlay": "Dismiss Overlay then tap Continue",
        "scroll": "Scroll down the list then tap Finish",
    }[s.task]
    targets = []
    for t in s.targets():
        b = t.box
        style = f"left:{b.x}px;top:{b.y}px;width:{b.width}px;height:{b.height}px"
        attrs = f'data-label="{t.id}" data-role="{t.role}" style="{style}"'
        label = html.escape(t.text)
        if t.role == "field":
            node = f'<input {attrs} aria-label="Value" inputmode="numeric" maxlength="8" value="{html.escape(s.value)}">'
        elif t.role == "list":
            node = (
                f'<div {attrs} class="list" tabindex="0" aria-label="Scroll list">'
                + "".join(f"<p>Item {i}</p>" for i in range(20))
                + "</div>"
            )
        elif t.role in {"handle", "destination"}:
            node = f'<div {attrs} class="{t.role}" role="button" tabindex="0" aria-label="{label}">{label}</div>'
        else:
            node = f"<button {attrs}>{label}</button>"
        targets.append(node)
    config = json.dumps(
        {
            "id": s.id,
            "device": s.device,
            "frame": s.marker,
            "capability": s.capability,
            "seq": s.last_seq,
            "phase": s.phase,
        }
    )
    bg, fg = ("#f4f6fa", "#132238") if s.seed % 2 else ("#172233", "#f4f6fa")
    font = ("Arial", "Georgia", "Verdana")[s.seed % 3]
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Owned phone benchmark</title><style>
*{{box-sizing:border-box}}html,body{{margin:0;background:{bg};color:{fg};font-family:{font},sans-serif}}
main{{position:relative;width:{s.width}px;height:{s.height}px;overflow:hidden}}
h1{{font-size:20px;margin:0;padding:16px 20px}}p.instruction{{padding:0 20px;font-size:17px}}
#marker{{font:11px monospace;padding:4px 20px;overflow-wrap:anywhere}}
[data-label]{{position:absolute;font-family:inherit;font-size:17px;border:2px solid #6193cd;border-radius:8px}}
[data-label]:focus-visible{{outline:4px solid #ee9b22;outline-offset:3px}}
button,input,.handle,.destination{{background:#e4edf9;color:#142c49;padding:8px}}
button,.handle{{touch-action:none}}.handle,.destination{{display:flex;align-items:center;justify-content:center}}
.destination{{border-style:dashed;background:#d9eddd}}.list{{overflow:auto;background:#e4edf9;color:#142c49;padding:0 12px;touch-action:pan-y}}
.list p{{height:45px;border-bottom:1px solid #71869a}}#error{{color:#c83535;padding:16px}}
</style><main><h1>Owned phone benchmark</h1><p class="instruction">{instruction}</p>
<div id="marker" data-frame="{s.marker}">{s.marker}</div>
{"".join(targets)}<p id="result">{"Complete" if s.complete else ""}</p><p id="error" role="alert"></p></main>
<script>const C={config};let seq=C.seq,chain=Promise.resolve(),stopped=false;
function send(kind,e,value=''){{if(stopped)return;chain=chain.then(async()=>{{if(stopped)return;
const payload={{device:C.device,frame:C.frame,seq:++seq,event_id:crypto.randomUUID(),kind,
x:Math.max(0,Math.min({s.width},e.clientX||0)),y:Math.max(0,Math.min({s.height},e.clientY||0)),
time_ms:performance.timeOrigin+performance.now(),pointer:e.pointerId||1,value,
pressure:typeof e.pressure==='number'?e.pressure:null,contact_width:typeof e.width==='number'?e.width:null,
contact_height:typeof e.height==='number'?e.height:null}};
const r=await fetch('/api/touch/'+C.id,{{method:'POST',headers:{{'Content-Type':'application/json',
'X-Session-Capability':C.capability}},body:JSON.stringify(payload)}});
if(!r.ok){{stopped=true;document.querySelector('#error').textContent='Observation refused. Reset from the operator.';return}}
const o=await r.json();if(o.frame!==C.frame){{if(o.phase!==C.phase||o.complete){{stopped=true;location.reload()}}
else{{C.frame=o.frame;const m=document.querySelector('#marker');m.textContent=o.frame;m.dataset.frame=o.frame}}}}
}}).catch(()=>{{stopped=true;document.querySelector('#error').textContent='Connection lost. Observation stopped.'}})}}
document.addEventListener('pointerdown',e=>send('down',e));
document.addEventListener('pointermove',e=>{{if(e.buttons)send('move',e)}});
document.addEventListener('pointerup',e=>send('up',e));
document.addEventListener('pointercancel',()=>{{stopped=true;document.querySelector('#error').textContent='Contact interrupted. Reset from the operator.'}});
let keyboard=false;
document.addEventListener('keydown',e=>{{if(e.key==='Tab')keyboard=true;const el=e.target.closest('[data-label]');
if(!el||e.repeat||!['Enter',' '].includes(e.key)||el.tagName==='INPUT'||el.classList.contains('list'))return;
e.preventDefault();const b=el.getBoundingClientRect(),p={{clientX:b.x+b.width/2,clientY:b.y+b.height/2,pointerId:1}};
if(el.classList.contains('handle'))send('down',p);else if(el.classList.contains('destination'))send('up',p);
else{{send('down',p);send('up',p)}}}});
document.addEventListener('pointerdown',()=>{{keyboard=false}});
document.querySelectorAll('input').forEach(el=>el.addEventListener('focus',()=>{{if(keyboard){{const b=el.getBoundingClientRect(),p={{clientX:b.x+b.width/2,clientY:b.y+b.height/2,pointerId:1}};send('down',p);send('up',p)}}}}));
document.querySelectorAll('input').forEach(el=>el.addEventListener('input',()=>{{const b=el.getBoundingClientRect();send('input',{{clientX:b.x+b.width/2,clientY:b.y+b.height/2}},el.value)}}));
document.querySelectorAll('.list').forEach(el=>el.addEventListener('scroll',()=>{{if(el.scrollTop>=100){{const b=el.getBoundingClientRect();send('scroll',{{clientX:b.x+b.width/2,clientY:b.y+b.height/2}},String(Math.floor(el.scrollTop)))}}}}));
</script></html>'''


def create_app(store: Benchmark, operator_key: str, evaluator_key: str) -> FastAPI:
    if len(operator_key) < 16 or len(evaluator_key) < 16 or operator_key == evaluator_key:
        raise Refusal("separate operator/evaluator capabilities required")
    app = FastAPI(title="Owned phone benchmark", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def body_budget(request: Request, call_next):
        if request.method == "POST":
            length = request.headers.get("content-length")
            try:
                size = int(length) if length is not None else -1
            except ValueError:
                size = -1
            if size < 0 or size > 65536:
                return JSONResponse({"refused": "request byte budget"}, status_code=413)
        return await call_next(request)

    @app.exception_handler(Refusal)
    async def refused(_request: Request, exc: Refusal):
        return JSONResponse({"refused": str(exc)}, status_code=409)

    def check(value: str, expected: str):
        if not secrets.compare_digest(value, expected):
            raise Refusal("operator/evaluator capability refused")

    @app.get("/health")
    def health():
        return {"schema": "phone-lab/1", "mode": "owned-site", "physical_control": False}

    @app.post("/api/session")
    def create(body: Create, x_operator_key: str = Header(default="")):
        check(x_operator_key, operator_key)
        s = store.create(**body.model_dump())
        return {"session": s.id, "device": s.device, "frame": s.marker, "url": f"/s/{s.id}"}

    @app.get("/s/{sid}", response_class=HTMLResponse)
    def rendered(sid: str):
        return page(store.get(sid))

    @app.post("/api/reset/{sid}")
    def reset(sid: str, x_operator_key: str = Header(default="")):
        check(x_operator_key, operator_key)
        store.reset(sid)
        return store.outcome(sid)

    @app.post("/api/touch/{sid}")
    def observe(sid: str, body: dict, x_session_capability: str = Header(default="")):
        store.authorize(sid, x_session_capability)
        return store.observe(sid, body)

    @app.get("/api/outcome/{sid}")
    def outcome(sid: str, x_evaluator_key: str = Header(default="")):
        check(x_evaluator_key, evaluator_key)
        return store.outcome(sid)

    @app.get("/api/labels/{sid}")
    def labels(sid: str, x_evaluator_key: str = Header(default="")):
        check(x_evaluator_key, evaluator_key)
        s = store.get(sid)
        return {
            "session": s.id,
            "frame": s.marker,
            "targets": [
                {"id": t.id, "role": t.role, "text": t.text, "box": vars(t.box)}
                for t in s.targets()
            ],
        }

    @app.get("/api/events/{sid}")
    def events(sid: str):
        s = store.get(sid)
        data = json.dumps({"frame": s.marker, "complete": s.complete})
        return StreamingResponse(
            iter([f"id: {s.frame}\nevent: render\ndata: {data}\n\n"]),
            media_type="text/event-stream",
        )

    return app
