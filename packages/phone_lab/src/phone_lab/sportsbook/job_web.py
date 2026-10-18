"""Blue-only local job controls and frozen generated dataset inspection."""

import json
from contextlib import asynccontextmanager

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from ..benchmark import Refusal
from .dataset import _inside
from .jobs import JobRunner, JobStore, prepare_executor


async def _body(request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            raise HTTPException(413, "Job request byte budget exceeded")
    try:
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeError):
        raise HTTPException(422, "JSON job object required") from None


def install_job_routes(app, root, dataset, *, browser=None, ocr=None, ocr_sha256=None, arena_available=False):
    store = JobStore(root)
    store.import_dataset(dataset)
    executor = prepare_executor(browser, ocr, ocr_sha256)
    runner = JobRunner(store)
    app.state.job_runner = runner

    @asynccontextmanager
    async def lifespan(app):
        runner.start()
        try:
            yield
        finally:
            runner.stop()

    app.router.lifespan_context = lifespan

    def guarded(operation):
        try:
            return operation()
        except (Refusal, OSError) as error:
            raise HTTPException(422, str(error) if isinstance(error, Refusal) else "Owned job artifact unavailable") from None

    @app.get("/api/jobs")
    def jobs():
        return {"jobs": store.rows(), "datasets": store.datasets(), "capture_available": executor["chrome"] is not None,
                "ocr_available": executor["ocr"] is not None, "active_limit": 1, "queue_limit": 16,
                "runtime_seconds": 120, "supervisor_error": runner.last_error, "training": "held"}

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        return guarded(lambda: store.get(job_id))

    @app.post("/api/jobs")
    async def enqueue(request: Request):
        body = await _body(request)
        return guarded(lambda: store.enqueue(body, executor))

    @app.post("/api/jobs/{job_id}/cancel")
    async def cancel(job_id: str, request: Request):
        if await _body(request) != {}:
            raise HTTPException(422, "Cancel requires an empty job object")
        return guarded(lambda: store.cancel(job_id))

    @app.post("/api/jobs/{job_id}/restart")
    async def restart(job_id: str, request: Request):
        body = await _body(request)
        if set(body) != {"request_id"}:
            raise HTTPException(422, "Restart requires only a replay key")
        return guarded(lambda: store.restart(job_id, body["request_id"]))

    @app.get("/jobs/artifacts/{job_id}/{relative:path}")
    def artifact(job_id: str, relative: str):
        return FileResponse(guarded(lambda: store.artifact(job_id, relative)), headers={"Cache-Control": "no-store"})

    def manifest(did):
        path = store.dataset_path(did)
        return path, json.loads((path / "dataset.json").read_text())

    @app.get("/api/jobs/datasets/{dataset_id}/samples")
    def samples(dataset_id: str):
        def read():
            path, data = manifest(dataset_id)
            return {"dataset_id": data["dataset_id"], "renderer": data["renderer"], "samples": [
                {"sample_id": row["sample_id"], "tags": row["tags"], "split": row["split"],
                 "image_url": f'/jobs/datasets/{dataset_id}/images/{row["sample_id"]}',
                 "fields": json.loads(_inside(path, row["annotation"]).read_text())["fields"]} for row in data["samples"]]}
        return guarded(read)

    @app.get("/jobs/datasets/{dataset_id}/images/{sample_id}")
    def image(dataset_id: str, sample_id: str):
        def read():
            path, data = manifest(dataset_id)
            row = next((r for r in data["samples"] if r["sample_id"] == sample_id), None)
            if row is None:
                raise Refusal("unknown frozen sample")
            return _inside(path, row["image"])
        return FileResponse(guarded(read), media_type="image/png", headers={"Cache-Control": "no-store"})

    @app.get("/jobs/datasets/{dataset_id}/", response_class=HTMLResponse)
    def dataset_page(dataset_id: str):
        guarded(lambda: store.dataset_path(dataset_id))
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Frozen fictional dataset</title>{STYLE}
<h1>Frozen fictional dataset</h1><p><a href="/jobs/">Dataset and evaluation jobs</a> · Training held</p><p>Inspect provider tags, text and borders against the actual saved pixels. These are generated development captures.</p>
<label for="sample">Capture</label><select id="sample"></select><label><input id="show-borders" type="checkbox" checked> Show component borders</label><div class="columns"><div class="phone"><img id="capture" alt="Saved fictional iPhone page"><canvas id="borders" width="390" height="844"></canvas></div><section><h2>Deterministic tags</h2><pre id="tags"></pre><h2>Identified fields and borders</h2><table><thead><tr><th>Role</th><th>Text</th><th>Border</th></tr></thead><tbody id="fields"></tbody></table></section></div><p id="status" role="status"></p>
<script>const sid={json.dumps(dataset_id)},select=document.querySelector('#sample'),canvas=document.querySelector('#borders');let rows=[];
function choose(){{const r=rows[select.selectedIndex];if(!r)return;document.querySelector('#capture').src=r.image_url;document.querySelector('#tags').textContent=JSON.stringify({{split:r.split,...r.tags}},null,2);const body=document.querySelector('#fields');body.replaceChildren();const ctx=canvas.getContext('2d');ctx.clearRect(0,0,390,844);for(const f of r.fields){{const tr=document.createElement('tr');for(const value of [f.role,f.text,[f.box.x,f.box.y,f.box.width,f.box.height].map(v=>Number(v.toFixed(2))).join(', ')]){{const td=document.createElement('td');td.textContent=value;tr.append(td)}}body.append(tr);if(document.querySelector('#show-borders').checked){{ctx.strokeStyle='#d51955';ctx.lineWidth=1;ctx.strokeRect(f.box.x,f.box.y,f.box.width,f.box.height)}}}}}}
select.onchange=choose;document.querySelector('#show-borders').onchange=choose;fetch('/api/jobs/datasets/'+sid+'/samples').then(async r=>{{const d=await r.json();if(!r.ok)throw Error(d.detail);rows=d.samples;for(const row of rows){{const o=document.createElement('option');o.textContent=row.tags.provider+' · seed '+row.tags.seed+' · phase '+row.tags.phase+' · '+row.split;select.append(o)}}choose()}}).catch(e=>document.querySelector('#status').textContent=String(e));</script></html>'''

    @app.get("/jobs/", response_class=HTMLResponse)
    def index():
        return JOB_PAGE.replace("__ROUND_LINK__", ' · <a href="/arena/">Round review</a>' if arena_available else '')


STYLE = '''<style>body{font:16px/1.5 system-ui;max-width:1160px;margin:30px auto;padding:20px;background:#f4f7ff;color:#192f4d}h1{font-size:36px}h2{font-size:24px}[role=status]{background:#fff4cd;padding:14px;border-radius:12px}button,input,select{font:inherit;margin:5px;padding:10px;border:1px solid #ccd9ed;border-radius:10px}button{background:#285ba8;color:white;cursor:pointer}button:disabled{opacity:.5;cursor:default}fieldset{border:1px solid #ccd9ed;border-radius:14px;margin:16px 0;background:white;padding:20px}label{display:inline-block;margin:5px}table{width:100%;border-collapse:collapse;background:white;border-radius:14px}td,th{text-align:left;padding:12px;border-bottom:1px solid #d7e1f2;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}.columns{display:grid;grid-template-columns:390px minmax(0,1fr);gap:32px;margin-top:20px}.phone{position:relative;width:390px;height:844px}.phone img,.phone canvas{position:absolute;inset:0;display:block;width:390px;height:844px}.phone canvas{pointer-events:none}.actions{display:flex;flex-wrap:wrap;gap:8px}progress{width:130px;display:block}@media(max-width:850px){.columns{grid-template-columns:1fr}body{padding:12px}table{font-size:14px}td,th{padding:8px}}</style>'''

JOB_PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blue data jobs</title>''' + STYLE + r'''
<h1>Dataset and evaluation jobs</h1><p><a href="/">Blue curator</a>__ROUND_LINK__</p><p role="status"><strong>Training held.</strong> Generate fictional iPhone captures and measure OCR/database errors. One job runs at a time; cancelled and failed artifacts remain preserved.</p>
<fieldset><legend>Generate a tagged dataset</legend><p>Choose unique event seeds across the three splits. Each seed produces three page phases. At most eight seeds per split.</p><label>Train seeds<input id="train" value="17,18,19"></label><label>Validation seeds<input id="validation" value="117,118"></label><label>Test seeds<input id="test" value="217,218"></label><button id="generate">Queue capture job</button></fieldset>
<fieldset><legend>Inspect or evaluate frozen captures</legend><label for="dataset">Frozen dataset</label><select id="dataset"></select><a id="inspect">Inspect tags and borders</a><button id="evaluate">Queue OCR evaluation</button><p id="availability"></p></fieldset><p id="message" role="status" aria-live="polite">Loading job history…</p><h2>Job history</h2><p>Progress counts saved captures or observations. A run becomes accepted after its final audit. Restart creates a new run and keeps the original.</p><table><thead><tr><th>Job</th><th>State</th><th>Progress</th><th>Toronto time</th><th>Actions and outcome</th></tr></thead><tbody id="history"></tbody></table>
<script>const dataset=document.querySelector('#dataset'),message=document.querySelector('#message');let pending=null,created=null,tracked=null;
async function send(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json();if(!r.ok)throw Error(d.detail||'Job request failed');return d}
function inspect(){document.querySelector('#inspect').href='/jobs/datasets/'+dataset.value+'/'}dataset.onchange=inspect;
async function queue(body){try{if(pending){const previous={...pending};delete previous.request_id;if(JSON.stringify(previous)!==JSON.stringify(body))throw Error('Retry the pending request before changing its inputs')}pending=pending||{request_id:crypto.randomUUID(),...body};const r=await send('/api/jobs',pending);created=tracked=r.job_id;pending=null;message.textContent='Job queued. Progress and outcomes appear below.';await refresh();await notice()}catch(e){message.textContent=String(e)+'. Retry submits the same pending request.'}}
document.querySelector('#generate').onclick=()=>{try{const seeds={};for(const split of ['train','validation','test']){seeds[split]=document.querySelector('#'+split).value.split(',').map(v=>{if(!/^\d{1,6}$/.test(v.trim()))throw Error('Use comma-separated numeric seeds');return Number(v.trim())})}queue({kind:'dataset',seeds})}catch(e){message.textContent=String(e)}};
document.querySelector('#evaluate').onclick=()=>queue({kind:'evaluation',dataset_id:dataset.value});
async function action(row,kind){try{const r=await send('/api/jobs/'+row.job_id+'/'+kind,kind==='cancel'?{}:{request_id:crypto.randomUUID()});tracked=r.job_id;if(kind==='restart')created=r.job_id;message.textContent=kind==='cancel'?'Stop requested; partial evidence is retained.':'Restart queued in a new run.';await refresh();await notice()}catch(e){message.textContent=String(e)}}
async function notice(){if(!tracked||pending)return;const response=await fetch('/api/jobs/'+tracked),r=await response.json();if(!response.ok)throw Error(r.detail);const name=r.kind==='dataset'?'Capture job':'OCR evaluation';if(r.state==='succeeded'){message.textContent=r.kind==='dataset'?'Capture complete: '+r.total+' frozen images are ready to inspect.':'Evaluation complete. Stored exactly '+r.result.final_database.correct_records+' / '+r.result.final_database.expected_records+' expected records. Open the error report for misses.';tracked=null}else if(['failed','cancelled','interrupted'].includes(r.state)){message.textContent=name+' '+r.state+'. Original evidence is preserved. '+(r.error||'');tracked=null}else{message.textContent=name+' '+r.state+': '+r.completed+' / '+r.total+'. Training remains held.'}}
async function refresh(){const response=await fetch('/api/jobs'),data=await response.json();if(!response.ok)throw Error(data.detail);const selected=dataset.value;dataset.replaceChildren();for(const d of data.datasets){const o=document.createElement('option');o.value=d.dataset_id;o.textContent=d.dataset_id.slice(0,12)+' · '+d.samples+' captures';dataset.append(o)}if([...dataset.options].some(o=>o.value===selected))dataset.value=selected;const completed=data.jobs.find(r=>r.job_id===created&&r.state==='succeeded'&&r.kind==='dataset');if(completed){dataset.value=completed.result.dataset_id;created=null}inspect();document.querySelector('#generate').disabled=!data.capture_available;document.querySelector('#evaluate').disabled=!data.ocr_available||!dataset.value;document.querySelector('#availability').textContent=data.ocr_available?'Native OCR is available. Each evaluation saves observations before measuring field and database errors.':'Native OCR is unavailable; configure a reviewed local executable to evaluate.';const history=document.querySelector('#history');history.replaceChildren();for(const row of data.jobs){const tr=document.createElement('tr');for(const value of [(row.kind==='dataset'?'Capture':'OCR evaluation')+' · '+row.job_id.slice(0,10),row.state,row.completed+' / '+row.total,row.created_at]){const td=document.createElement('td');td.textContent=value;if(tr.children.length===2){const p=document.createElement('progress');p.max=row.total;p.value=row.completed;td.append(p)}tr.append(td)}const td=document.createElement('td');td.className='actions';if(['queued','running'].includes(row.state)){const b=document.createElement('button');b.textContent='Cancel';b.onclick=()=>action(row,'cancel');td.append(b)}if(['failed','cancelled','interrupted'].includes(row.state)){const b=document.createElement('button');b.textContent='Restart';b.onclick=()=>action(row,'restart');td.append(b)}if(row.result){const a=document.createElement('a');a.textContent=row.kind==='dataset'?'Inspect dataset':'Open error report';a.href=row.kind==='dataset'?'/jobs/datasets/'+row.result.dataset_id+'/':'/jobs/artifacts/'+row.job_id+'/'+row.result.artifact.split('/').map(encodeURIComponent).join('/');td.append(a)}if(row.error){const p=document.createElement('span');p.textContent=row.error;td.append(p)}tr.append(td);history.append(tr)}if(data.supervisor_error)message.textContent='Job supervisor needs attention: '+data.supervisor_error;else if(message.textContent==='Loading job history…')message.textContent='Ready. Training remains held.'}
refresh().catch(e=>message.textContent=String(e));setInterval(async()=>{try{await refresh();await notice()}catch(e){message.textContent=String(e)}},1000);</script></html>'''
