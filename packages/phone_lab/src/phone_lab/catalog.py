"""Immutable generated datasets with reproducible tags and pixel borders."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from .benchmark import Refusal
from .dataset import generate

RECIPE = "owned-synthetic-catalog/1"


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def dataset_spec(seeds, tags=(), *, width=390, height=700):
    if (
        not isinstance(seeds, list)
        or not 1 <= len(seeds) <= 12
        or any(type(s) is not int or not 0 <= s <= 1_000_000 for s in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise Refusal("1 to 12 unique integer seeds required")
    if (
        not isinstance(tags, (list, tuple))
        or len(tags) > 16
        or any(not isinstance(t, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", t) for t in tags)
    ):
        raise Refusal("up to 16 lowercase tags required")
    if (
        type(width) is not int
        or type(height) is not int
        or not 320 <= width <= 1080
        or not 640 <= height <= 1920
    ):
        raise Refusal("supported viewport bounds")
    source = b"".join(
        (Path(__file__).parent / name).read_bytes()
        for name in ("benchmark.py", "web.py", "dataset.py", "catalog.py")
    )
    return {
        "recipe": RECIPE,
        "generator_source_sha256": hashlib.sha256(source).hexdigest(),
        "seeds": sorted(seeds),
        "tags": sorted(set(tags)),
        "viewport": [width, height],
    }


def spec_id(spec):
    return hashlib.sha256(_json(spec)).hexdigest()[:24]


def build_catalog(destination, seeds, *, tags=(), executable=None, width=390, height=700):
    spec = dataset_spec(seeds, tags, width=width, height=height)
    destination = Path(destination)
    manifest = generate(
        destination, spec["seeds"], executable=executable, width=width, height=height
    )
    samples = []
    for row in manifest["rows"]:
        sid = hashlib.sha256(
            _json({"spec": spec, "seed": row["seed"], "task": row["task"], "phase": row["phase"]})
        ).hexdigest()[:24]
        borders = [
            {
                "id": label["id"],
                "role": label["role"],
                "left": label["box"]["x"],
                "top": label["box"]["y"],
                "right": label["box"]["x"] + label["box"]["width"],
                "bottom": label["box"]["y"] + label["box"]["height"],
            }
            for label in row["labels"]
        ]
        sample_tags = sorted(
            set(
                spec["tags"]
                + [
                    f"task:{row['task']}",
                    f"phase:{row['phase']}",
                    f"font:{row['font_group']}",
                    "source:generated",
                ]
                + [f"role:{b['role']}" for b in borders]
            )
        )
        annotation = {
            "schema": "owned-ui-annotation/1",
            "id": sid,
            "viewport": row["viewport"],
            "coordinate_space": "CSS pixels; origin top-left; device scale 1",
            "provenance": "measured DOM component borders, evaluator only",
            "tags": sample_tags,
            "borders": borders,
        }
        rel = f"annotations/{row['split']}/{sid}.json"
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _json(annotation)
        path.write_bytes(data)
        samples.append(
            {
                "id": sid,
                "seed": row["seed"],
                "task": row["task"],
                "phase": row["phase"],
                "split": row["split"],
                "layout_group": row["layout_group"],
                "font_group": row["font_group"],
                "tags": sample_tags,
                "borders": borders,
                "viewport": row["viewport"],
                "image": row["image"],
                "image_sha256": row["sha256"],
                "yolo_label": row["yolo_label"],
                "yolo_sha256": row["yolo_sha256"],
                "annotation": rel,
                "annotation_sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    catalog = {
        "schema": RECIPE,
        "id": spec_id(spec),
        "spec": spec,
        "samples": samples,
        "manifest_sha256": manifest["manifest_sha256"],
        "labels_channel": "curator/evaluator only",
        "real_phone_holdout": "pending; generated samples are not real-device evidence",
    }
    data = _json(catalog)
    (destination / "catalog.json").write_bytes(data)
    (destination / "catalog.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n")
    # Portable config: run training from this dataset directory, or supply its absolute path.
    (destination / "dataset-portable.yaml").write_text(
        (destination / "dataset.yaml")
        .read_text()
        .replace(f"path: {destination.resolve()}", "path: .", 1)
    )
    return catalog


def _file(root, relative):
    if not isinstance(relative, str) or len(relative) > 240:
        raise Refusal("dataset file path")
    path = Path(root) / relative
    if (
        Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or path.is_symlink()
        or not path.resolve().is_relative_to(Path(root).resolve())
    ):
        raise Refusal("dataset file escapes root")
    if not path.is_file() or path.stat().st_size > 5_000_000:
        raise Refusal("dataset file unavailable or byte budget")
    return path


def load_catalog(root):
    root = Path(root)
    if root.is_symlink():
        raise Refusal("dataset root symlink")
    data = _file(root, "catalog.json").read_bytes()
    expected = _file(root, "catalog.sha256").read_text().strip()
    if hashlib.sha256(data).hexdigest() != expected:
        raise Refusal("catalog hash mismatch")
    try:
        catalog = json.loads(data)
        if catalog["schema"] != RECIPE or catalog["id"] != spec_id(catalog["spec"]):
            raise Refusal("catalog identity")
        samples = catalog["samples"]
        if not isinstance(samples, list) or not 1 <= len(samples) <= 108:
            raise Refusal("catalog sample budget")
        for sample in samples:
            for field, digest in (
                ("image", "image_sha256"),
                ("yolo_label", "yolo_sha256"),
                ("annotation", "annotation_sha256"),
            ):
                if (
                    hashlib.sha256(_file(root, sample[field]).read_bytes()).hexdigest()
                    != sample[digest]
                ):
                    raise Refusal("dataset artifact hash mismatch")
        if (
            hashlib.sha256(_file(root, "manifest.json").read_bytes()).hexdigest()
            != catalog["manifest_sha256"]
        ):
            raise Refusal("dataset manifest hash mismatch")
        return catalog
    except (ValueError, KeyError, TypeError) as e:
        raise Refusal("invalid dataset catalog") from e


def dataset_html():
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gantry synthetic data</title><style>
:root{color-scheme:dark;font:16px system-ui;background:#10151e;color:#e8edf5}body{max-width:1200px;margin:auto;padding:24px}
input,button,select{font:inherit;padding:9px;background:#263246;color:inherit;border:1px solid #62718a;border-radius:6px}
label{display:inline-block;margin:8px}button{cursor:pointer}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px}
.sample{border:1px solid #536079;border-radius:10px;padding:12px}.frame{position:relative}.frame img{width:100%;display:block}
.box{position:absolute;border:2px solid #ffad5b;box-sizing:border-box;pointer-events:none}.box span{font-size:10px;background:#1b202a;color:#ffd5a0}
.muted{color:#b7c1d0}a{color:#a5c9ff}
</style><h1>Synthetic data</h1><p class="muted">Seeded phone layouts · measured pixel borders · deterministic tags and YOLO labels</p>
<form id="create"><label>Seeds <input id="seeds" value="0,1,2" size="12"></label><label>Tags <input id="tags" value="pilot,ui" size="16"></label>
<label>Width <input id="width" type="number" value="390" min="320" max="1080" style="width:80px"></label>
<label>Height <input id="height" type="number" value="700" min="640" max="1920" style="width:80px"></label><button>Generate dataset</button></form>
<p class="muted">Tags use lowercase letters, numbers and hyphens. Reuse the same seeds and tags to reopen the immutable dataset. Change tags to create a new version.</p>
<label>Dataset <select id="datasets"></select></label><label>Task <select id="task"><option value="">All tasks</option></select></label>
<label>Split <select id="split"><option value="">All splits</option><option>train</option><option>val</option><option>test</option></select></label>
<label>Show borders <input id="borders" type="checkbox" checked></label><p id="state" role="status"></p><div id="downloads"></div><div id="grid"></div>
<p class="muted">Curator/evaluator view. Labels are excluded from red vision actions and blue contact scoring. Real phone holdout pending.</p><script>
let current=null;const $=id=>document.getElementById(id);
function file(id,path){return '/files/'+id+'/'+path.split('/').map(encodeURIComponent).join('/')}
function render(){const grid=$('grid');grid.replaceChildren();if(!current)return;
for(const s of current.samples){if(($('task').value&&s.task!==$('task').value)||($('split').value&&s.split!==$('split').value))continue;
const card=document.createElement('article');card.className='sample';const title=document.createElement('h3');title.textContent=s.task+' / phase '+s.phase+' / seed '+s.seed;card.append(title);
const frame=document.createElement('div');frame.className='frame';const img=document.createElement('img');img.src=file(current.id,s.image);img.alt=s.task+' generated layout';frame.append(img);
if($('borders').checked)for(const b of s.borders){const box=document.createElement('div');box.className='box';box.style.left=100*b.left/s.viewport[0]+'%';box.style.top=100*b.top/s.viewport[1]+'%';
box.style.width=100*(b.right-b.left)/s.viewport[0]+'%';box.style.height=100*(b.bottom-b.top)/s.viewport[1]+'%';const text=document.createElement('span');text.textContent=b.role;box.append(text);frame.append(box)}card.append(frame);
const meta=document.createElement('p');meta.textContent=s.split+' · '+s.tags.join(', ');card.append(meta);const link=document.createElement('a');link.href=file(current.id,s.annotation);link.textContent='Pixel borders + tags JSON';card.append(link);grid.append(card)}}
async function openData(id){const r=await fetch('/api/datasets/'+id);if(!r.ok)throw Error('Dataset verification failed');current=await r.json();$('task').replaceChildren(new Option('All tasks',''));
for(const t of [...new Set(current.samples.map(s=>s.task))])$('task').add(new Option(t,t));$('downloads').replaceChildren();
for(const p of ['catalog.json','manifest.json','dataset-portable.yaml']){const a=document.createElement('a');a.href=file(id,p);a.textContent=p+' ';a.download='';$('downloads').append(a)}render();$('state').textContent=current.samples.length+' verified samples · '+id;}
async function refresh(id){const r=await fetch('/api/datasets');const all=await r.json();$('datasets').replaceChildren();for(const d of all)$('datasets').add(new Option(d.id,d.id));if(id)$('datasets').value=id;if($('datasets').value)await openData($('datasets').value)}
$('create').onsubmit=async e=>{e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;$('state').textContent='Rendering and checking dataset…';
try{const r=await fetch('/api/datasets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seeds:$('seeds').value.split(',').map(Number),tags:$('tags').value.split(',').map(s=>s.trim()).filter(Boolean),width:Number($('width').value),height:Number($('height').value)})});if(!r.ok)throw Error((await r.json()).detail);const d=await r.json();await refresh(d.id)}catch(e){$('state').textContent=e.message}finally{button.disabled=false}};
$('datasets').onchange=()=>openData($('datasets').value).catch(e=>$('state').textContent=e.message);for(const id of ['task','split','borders'])$(id).onchange=render;
refresh().catch(e=>$('state').textContent=e.message);
</script></html>"""


def create_dataset_app(root, *, executable=None):
    root = Path(root)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    lock = threading.Lock()

    def locate(dataset_id):
        if not re.fullmatch(r"[0-9a-f]{24}", dataset_id):
            raise HTTPException(404, "Dataset unavailable")
        path = root / dataset_id
        if path.is_symlink() or not path.is_dir():
            raise HTTPException(404, "Dataset unavailable")
        return path

    @app.get("/", response_class=HTMLResponse)
    def home():
        return dataset_html()

    @app.get("/api/datasets")
    def datasets():
        return [
            {"id": p.name}
            for p in sorted(root.glob("*"))
            if p.is_dir()
            and not p.is_symlink()
            and re.fullmatch(r"[0-9a-f]{24}", p.name)
            and (p / "catalog.json").is_file()
        ]

    @app.get("/api/datasets/{dataset_id}")
    def detail(dataset_id: str):
        try:
            return load_catalog(locate(dataset_id))
        except (Refusal, OSError):
            raise HTTPException(503, "Dataset verification failed; originals retained") from None

    @app.post("/api/datasets")
    async def create(request: Request):
        if len(await request.body()) > 8192:
            raise HTTPException(422, "Dataset request budget")
        try:
            body = await request.json()
            if not isinstance(body, dict) or set(body) - {"seeds", "tags", "width", "height"}:
                raise Refusal("dataset parameters only")
            spec = dataset_spec(
                body.get("seeds"),
                body.get("tags", []),
                width=body.get("width", 390),
                height=body.get("height", 700),
            )
        except (ValueError, TypeError):
            raise HTTPException(422, "Use bounded seeds, tags and viewport") from None
        # Playwright's sync renderer runs in a worker thread, outside the ASGI loop.
        from starlette.concurrency import run_in_threadpool

        def render():
            with lock:
                path = root / spec_id(spec)
                if path.exists():
                    return load_catalog(path)
                return build_catalog(
                    path,
                    spec["seeds"],
                    tags=spec["tags"],
                    executable=executable,
                    width=spec["viewport"][0],
                    height=spec["viewport"][1],
                )

        try:
            return await run_in_threadpool(render)
        except (Refusal, OSError):
            raise HTTPException(
                503, "Dataset rendering failed; partial evidence retained"
            ) from None

    @app.get("/files/{dataset_id}/{relative:path}")
    def artifact(dataset_id: str, relative: str):
        try:
            path = locate(dataset_id)
            catalog = load_catalog(path)
            allowed = {"catalog.json", "manifest.json", "dataset-portable.yaml"}
            for sample in catalog["samples"]:
                allowed.update(sample[key] for key in ("image", "annotation", "yolo_label"))
            if relative not in allowed:
                raise HTTPException(404, "Dataset artifact unavailable")
            return FileResponse(_file(path, relative))
        except (Refusal, OSError):
            raise HTTPException(503, "Dataset verification failed") from None

    return app
