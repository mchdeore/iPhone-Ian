from __future__ import annotations

import json
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from ..benchmark import Refusal
from ..training_policy import read_policy
from .arena import ArenaStore
from .behavior import BehaviorSessions
from .contracts import PROVIDERS
from .dataset import _inside, audit_dataset
from .fixtures import provider_snapshot
from .pages import provider_page
from .provider import install_provider_routes, provider_board


def _status(surface):
    return {"surface": surface, "training": read_policy(), "deployment": "local development; team surfaces require access isolation before shared hosting"}


def _hold_banner():
    policy = read_policy()
    return f'<p role="status"><strong>Training {escape(policy["state"])}</strong> · {escape(policy["reason"])}</p>'


def create_red_app(root, *, arena):
    root, arena = Path(root), Path(arena)
    store = ArenaStore(arena, root)
    store.close()
    app = FastAPI(title="Red team pixel console")

    @app.get("/api/status")
    def status():
        return _status("red")

    @app.get("/api/captures")
    def captures():
        store = ArenaStore(arena, root)
        try:
            return {"captures": store.captures()}
        finally:
            store.close()

    @app.get("/images/{capture_id}")
    def image(capture_id: str):
        store = ArenaStore(arena, root)
        try:
            return FileResponse(store.image(capture_id), media_type="image/png", headers={"Cache-Control": "no-store"})
        except Refusal as error:
            raise HTTPException(404, str(error)) from None
        finally:
            store.close()

    @app.post("/api/attempts")
    async def submit(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 262144:
                raise HTTPException(413, "Attempt byte budget exceeded")
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeError):
            raise HTTPException(422, "JSON attempt required") from None
        store = ArenaStore(arena, root)
        try:
            return store.submit(payload)
        except Refusal as error:
            raise HTTPException(422, str(error)) from None
        finally:
            store.close()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Red team pixel console</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:30px auto;padding:20px;background:#fff4f5;color:#30212a}}h1{{font-size:36px}}[role=status]{{background:#fff4cd;padding:14px;border-radius:12px}}.console{{display:grid;grid-template-columns:390px minmax(0,1fr);gap:32px}}img{{width:390px;max-width:100%;border-radius:24px}}textarea{{box-sizing:border-box;display:block;width:100%;height:420px;margin:16px 0;padding:16px;border:1px solid #dcc5cc;border-radius:12px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}button,select{{padding:12px;border:1px solid #dcc5cc;border-radius:10px}}select{{width:100%}}button{{background:#982548;color:white;cursor:pointer}}@media(max-width:800px){{.console{{grid-template-columns:1fr}}}}</style>
<h1>Red team pixel console</h1>{_hold_banner()}<p>Select a capture, inspect its pixels, and submit an observation or refusal. Saved attempts remain in the round history.</p>
<select id="captures" aria-label="Capture"></select><div class="console"><p><img id="phone" alt="Round capture"></p><section><h2>Save an attempt</h2><p>Use observed values, or record a refusal. Use an explicit retry reference for another attempt on the same capture.</p><label for="attempt">Attempt JSON</label><textarea id="attempt"></textarea><button id="submit">Save attempt</button><pre id="result" role="status"></pre></section></div>
<script>let rows=[];const select=document.querySelector('#captures'),editor=document.querySelector('#attempt'),result=document.querySelector('#result');
function choose(){{const c=rows[select.selectedIndex];document.querySelector('#phone').src=c.image_url;editor.value=JSON.stringify({{attempt_id:crypto.randomUUID(),capture_id:c.capture_id,image_sha256:c.image_sha256,actor_id:'manual',model_sha256:null,parser_version:'manual/1',latency_ms:0,quotes:[],refusals:[],retry_of:null}},null,2)}}
fetch('/api/captures').then(r=>r.json()).then(data=>{{rows=data.captures;for(const c of rows){{const o=document.createElement('option');o.textContent=c.capture_id;select.append(o)}}if(rows.length)choose()}}).catch(e=>result.textContent=String(e));select.onchange=choose;
document.querySelector('#submit').onclick=async()=>{{try{{const response=await fetch('/api/attempts',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:editor.value}});result.textContent=JSON.stringify(await response.json(),null,2)}}catch(e){{result.textContent=String(e)}}}};</script></html>'''

    return app


def create_app(root, *, reports=None, arena=None, jobs=None, browser=None, ocr=None, ocr_sha256=None):
    root = Path(root)
    audit_dataset(root)
    manifest = json.loads((root / "dataset.json").read_text())
    samples = {row["sample_id"]: row for row in manifest["samples"]}
    app = FastAPI(title="Synthetic sportsbook training lab")
    job_link = '<p><a href="/jobs/">Dataset and evaluation jobs</a></p>' if jobs is not None else ''
    if jobs is not None:
        from .job_web import install_job_routes
        install_job_routes(app, jobs, root, browser=browser, ocr=ocr, ocr_sha256=ocr_sha256, arena_available=arena is not None)
    @app.get("/api/status")
    def status():
        return _status("blue")

    if arena is not None:
        arena = Path(arena)
        store = ArenaStore(arena, root)
        store.close()
        install_provider_routes(app, root, arena)

        @app.get("/api/arena")
        def arena_state():
            store = ArenaStore(arena, root)
            try:
                captures = [dict(row, tags=store.sample(row["capture_id"])["tags"],
                                 image_url="/images/" + store.sample(row["capture_id"])["sample_id"]) for row in store.captures()]
                return {"round": store.meta, "attempts": store.attempts(), "evaluations": store.evaluations(),
                        "captures": captures, "provider_sessions": BehaviorSessions(store).sessions()}
            finally:
                store.close()

        @app.post("/api/arena/evaluate")
        def evaluate():
            store = ArenaStore(arena, root)
            try:
                return store.evaluate()
            except Refusal as error:
                raise HTTPException(422, str(error)) from None
            finally:
                store.close()

        @app.get("/arena/", response_class=HTMLResponse)
        def arena_board():
            state = arena_state()
            attempts = "".join(f'<tr><td>{row["seq"]}</td><td>{escape(row["payload"]["actor_id"])}</td><td>{escape(row["result"]["status"])}</td><td>{escape(row["created_at"])}</td><td><details><summary>Details</summary><pre>{escape(json.dumps(row["result"]))}\n{escape(json.dumps(row["payload"]["refusals"]))}\nRetry of: {escape(str(row["payload"]["retry_of"]))}</pre></details></td></tr>' for row in state["attempts"])
            scores = state["evaluations"]
            latest = escape(json.dumps(scores[-1]["score"], indent=2)) if scores else "Evaluation pending. Save actor attempts, then score the persisted database."
            stale = bool(scores and scores[-1]["attempt_seq"] != (state["attempts"][-1]["seq"] if state["attempts"] else 0))
            database = scores[-1]["score"]["database"] if scores else None
            exact = f'{database["correct_records"]} / {database["expected_records"]}' if database else "Pending"
            missing, wrong, unexpected = (database[key] if database else "—" for key in ("missing_records", "wrong_records", "unexpected_records"))
            return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blue team round review</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:30px auto;padding:20px;background:#f4f7ff;color:#182b46}}h1{{font-size:36px}}[role=status]{{background:#fff4cd;padding:14px;border-radius:12px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px;margin:24px 0}}.metrics article{{padding:20px;background:white;border:1px solid #d7e1f0;border-radius:16px}}.metrics strong{{display:block;font-size:30px;margin-top:10px}}table{{width:100%;background:white;border-radius:14px;text-align:left}}td,th{{padding:12px;border-bottom:1px solid #dde5f0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;max-height:480px;overflow:auto}}button{{padding:14px;border:0;border-radius:10px;background:#2858a3;color:white;cursor:pointer}}details{{margin:16px 0}}summary{{cursor:pointer}}</style>
<h1>Blue team round review</h1>{_hold_banner()}{job_link}<p><a href="/">Provider pages and border annotations</a></p><p>Round {escape(state["round"]["run_id"])}. Actor submissions are saved before evaluation. Empty and refused attempts count.</p>
<div class="metrics"><article>Stored exactly<strong id="exact">{exact}</strong></article><article>Missing records<strong id="missing">{missing}</strong></article><article>Wrong records<strong id="wrong">{wrong}</strong></article><article>Unexpected records<strong id="unexpected">{unexpected}</strong></article></div>
<p id="freshness">{'New attempts are pending evaluation; the displayed score is older.' if stale else 'Score reflects its saved attempt snapshot.'}</p><button id="evaluate">Score saved database</button><details><summary>Database error details</summary><pre id="score">{latest}</pre></details><h2>Attempt history</h2><table><thead><tr><th>Attempt</th><th>Actor</th><th>Result</th><th>Toronto time</th><th>Details</th></tr></thead><tbody>{attempts}</tbody></table>
{provider_board(state)}
<script>document.querySelector('#evaluate').onclick=async()=>{{try{{const r=await fetch('/api/arena/evaluate',{{method:'POST'}}),data=await r.json();document.querySelector('#score').textContent=JSON.stringify(data,null,2);if(!r.ok)throw Error(data.detail||'Evaluation failed');const d=data.database;document.querySelector('#exact').textContent=d?d.correct_records+' / '+d.expected_records:'Pending';for(const key of ['missing','wrong','unexpected'])document.querySelector('#'+key).textContent=d?d[key+'_records']:'—';document.querySelector('#freshness').textContent='Saved score covers '+data.attempts+' attempts. Refresh to update the history table.'}}catch(e){{document.querySelector('#freshness').textContent=String(e)}}}};</script></html>'''
    if reports is not None:
        reports = Path(reports)
        report = json.loads((reports / "report.json").read_text())
        if report.get("schema") != "sportsbook-evaluation/1" or report.get("provenance", {}).get("dataset_id") != manifest["dataset_id"]:
            raise ValueError("evaluation belongs to a different dataset")

        @app.get("/evaluation/")
        def evaluation_index():
            return FileResponse(_inside(reports, "index.html"), media_type="text/html")

        @app.get("/evaluation/{asset:path}")
        def evaluation_asset(asset: str):
            allowed = asset in {"report.json", "association-heatmap.svg", "identification-heatmap.svg"}
            crop = Path(asset)
            allowed = allowed or (len(crop.parts) == 2 and crop.parts[0] == "error-crops" and crop.suffix == ".png")
            if not allowed:
                raise HTTPException(404, "Unknown evaluation asset")
            path = _inside(reports, asset)
            if not path.is_file():
                raise HTTPException(404, "Unknown evaluation asset")
            return FileResponse(path)

    def sample(identity):
        if identity not in samples:
            raise HTTPException(404, "Unknown generated sample")
        return samples[identity]

    @app.get("/", response_class=HTMLResponse)
    def index():
        cards = "".join(f'<a class="card" href="/samples/{row["sample_id"]}"><img src="/images/{row["sample_id"]}" alt="Synthetic iPhone sportsbook page"><strong>{escape(row["tags"]["provider"])} · {row["split"]}</strong><span>Seed {row["tags"]["seed"]}, phase {row["tags"]["phase"]}</span></a>' for row in samples.values())
        previews = " ".join(f'<a href="/providers/{provider}">{escape(provider)}</a>' for provider in PROVIDERS)
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synthetic sportsbook training lab</title><style>body{{font:16px system-ui;max-width:1200px;margin:30px auto;padding:20px;background:#f5f6fa}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px}}.card{{background:white;padding:12px;border-radius:14px;text-decoration:none;color:#18223c;display:flex;flex-direction:column;gap:8px}}img{{width:100%;border-radius:12px}}</style>
<h1>Blue team synthetic sportsbook lab</h1>{_hold_banner()}{job_link}<p>Fictional providers, iPhone pages, tagged borders and reproducible samples.</p><p>Provider previews: {previews}</p>
{'<p><a href="/arena/">Round attempts and database score</a></p>' if arena is not None else ''}
{'<p><a href="/evaluation/">Training errors and database score</a></p>' if reports is not None else ''}
<p>Dataset {escape(manifest["dataset_id"])} · {len(samples)} captures · event sequences and provider layouts stay in their own splits.</p><div class="grid">{cards}</div></html>'''

    @app.get("/providers/{provider}", response_class=HTMLResponse)
    def preview(provider: str, seed: int = Query(17, ge=0, le=999999), phase: int = Query(0, ge=0, le=2)):
        if provider not in PROVIDERS:
            raise HTTPException(404, "Unknown fictional provider")
        return provider_page(provider_snapshot(seed, phase, provider=provider))

    @app.get("/images/{identity}")
    def image(identity: str):
        row = sample(identity)
        return FileResponse(_inside(root, row["image"]), media_type="image/png")

    @app.get("/api/samples/{identity}")
    def detail(identity: str):
        row = sample(identity)
        annotation = json.loads(_inside(root, row["annotation"]).read_text())
        return {"sample_id": identity, "tags": row["tags"], "split": row["split"], "sha256": row["sha256"],
                "fields": annotation["fields"], "boundary": "Blue-team/evaluator labels; pixel-only actor receives PNG"}

    @app.get("/samples/{identity}", response_class=HTMLResponse)
    def inspect(identity: str):
        row = sample(identity)
        annotation = json.loads(_inside(root, row["annotation"]).read_text())
        boxes = "".join(f'<g><rect x="{field["box"]["x"]}" y="{field["box"]["y"]}" width="{field["box"]["width"]}" height="{field["box"]["height"]}" fill="none" stroke="#ff375f" stroke-width="1"/><title>{escape(field["id"])} · {escape(field["role"])} · {escape(field["text"])}</title></g>' for field in annotation["fields"])
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Generated sample borders</title>
<style>body{{font:16px system-ui;padding:20px}}.phone{{position:relative;width:390px;max-width:100%}}img{{width:100%}}svg{{position:absolute;inset:0;width:100%;height:100%}}#borders:not(:checked)~.phone svg{{display:none}}</style>
<p><a href="/">All samples</a> · {escape(row["tags"]["provider"])} · seed {row["tags"]["seed"]} · phase {row["tags"]["phase"]} · {row["split"]}</p>
<input id="borders" type="checkbox" checked><label for="borders"> Show component borders</label><div class="phone"><img src="/images/{identity}" alt="Synthetic iPhone page"><svg viewBox="0 0 390 844">{boxes}</svg></div><p><a href="/api/samples/{identity}">Tags and border data</a></p></html>'''

    return app
