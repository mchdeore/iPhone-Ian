from __future__ import annotations

import json
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from .contracts import PROVIDERS
from .dataset import _inside, audit_dataset
from .fixtures import provider_snapshot
from .pages import provider_page


def create_app(root, *, reports=None):
    root = Path(root)
    audit_dataset(root)
    manifest = json.loads((root / "dataset.json").read_text())
    samples = {row["sample_id"]: row for row in manifest["samples"]}
    app = FastAPI(title="Synthetic sportsbook training lab")
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
<h1>Synthetic sportsbook training lab</h1><p>Fictional providers, iPhone pages, tagged borders and reproducible samples.</p><p>Provider previews: {previews}</p>
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
