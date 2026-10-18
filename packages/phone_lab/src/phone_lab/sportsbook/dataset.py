from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image
from playwright.sync_api import sync_playwright

from ..benchmark import Refusal
from .contracts import validate_quote
from .evaluation import SPORTS_ROLES, _objects
from .fixtures import provider_snapshot
from .pages import provider_page

SPLIT_PROVIDERS = {"train": "provider-a", "validation": "provider-b", "test": "provider-c"}
VIEWPORT = {"width": 390, "height": 844}


def _encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sample_identity(row, manifest):
    return _digest({"renderer": manifest["renderer"], "generator_sha256": manifest["generator_sha256"],
                    "tags": row["tags"], "files": row["sha256"]})[:24]


def _dataset_identity(manifest):
    return _digest({key: manifest[key] for key in ("schema", "renderer", "generator_sha256", "roles", "samples")})[:24]


def _inside(root, relative):
    if not isinstance(relative, str):
        raise Refusal("dataset relative path required")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise Refusal("unsafe dataset path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or any((root / Path(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts) + 1)):
        raise Refusal("dataset symlink/path escape")
    return root / path


def _seeds(value):
    if not isinstance(value, dict) or set(value) != set(SPLIT_PROVIDERS):
        raise Refusal("train, validation and test seeds required")
    seen = set()
    for seeds in value.values():
        if not isinstance(seeds, list) or not 1 <= len(seeds) <= 32:
            raise Refusal("bounded nonempty split seeds required")
        for seed in seeds:
            if type(seed) is not int or not 0 <= seed <= 999999 or seed in seen:
                raise Refusal("event seeds must be unique across all splits")
            seen.add(seed)
    return value


def build_dataset(output, browser_path, *, seeds=None):
    seeds = _seeds(seeds if seeds is not None else {"train": [17, 18, 19], "validation": [117, 118], "test": [217, 218]})
    output, browser_path = Path(output), Path(browser_path)
    if output.exists() or output.is_symlink():
        raise Refusal("dataset output exists; preserve earlier evidence")
    if not browser_path.is_absolute() or not browser_path.is_file():
        raise Refusal("owned browser executable unavailable")
    source = Path(__file__).parent
    generator = _digest({name: _file_digest(source / name) for name in ("dataset.py", "contracts.py", "fixtures.py", "pages.py")})
    renderer = {"browser_version": None, "executable_sha256": _file_digest(browser_path),
                "playwright_version": importlib.metadata.version("playwright"), "platform": platform.platform(),
                "viewport": VIEWPORT, "device_scale_factor": 1, "locale": "en-US", "timezone": "UTC",
                "capture": "fonts ready, two animation frames, repeated PNG equality"}
    manifest = {"schema": "synthetic-sportsbook-dataset/1", "generator_sha256": generator,
                "renderer": renderer, "roles": list(SPORTS_ROLES), "samples": [],
                "purpose": "synthetic development data; a split name does not establish an untouched holdout",
                "created_at_toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat()}
    output.mkdir(parents=True, mode=0o700)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=str(browser_path), headless=True)
            renderer["browser_version"] = browser.version
            context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale="en-US", timezone_id="UTC")
            page = context.new_page()
            for split, provider in SPLIT_PROVIDERS.items():
                for seed in seeds[split]:
                    for phase in range(3):
                        truth = provider_snapshot(seed, phase, provider=provider)
                        html = provider_page(truth)
                        page.set_content(html, wait_until="load")
                        page.evaluate("async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}")
                        fields = page.locator("[data-label]").evaluate_all('''elements=>elements.map(el=>{
const b=el.getBoundingClientRect();const r=document.createRange();r.selectNodeContents(el);const t=r.getBoundingClientRect();
return {id:el.dataset.label,role:el.dataset.role,text:el.textContent.trim(),box:{x:b.x,y:b.y,width:b.width,height:b.height},text_box:{x:t.x,y:t.y,width:t.width,height:t.height}}})''')
                        if page.evaluate("document.documentElement.scrollWidth>390 || document.documentElement.scrollHeight>844"):
                            raise Refusal("synthetic page overflows iPhone viewport")
                        _objects(fields, SPORTS_ROLES, "label")
                        for field in fields:
                            for key in ("box", "text_box"):
                                b = field[key]
                                if b["x"] + b["width"] > 390 or b["y"] + b["height"] > 844:
                                    raise Refusal("field border outside iPhone viewport")
                        image = page.screenshot(type="png", animations="disabled")
                        if page.screenshot(type="png", animations="disabled") != image:
                            raise Refusal("renderer produced unstable repeated pixels")
                        annotation = _encoded({"schema": "sportsbook-component-borders/1", "viewport": VIEWPORT, "fields": fields})
                        labels = []
                        for field in fields:
                            b = field["box"]
                            labels.append(f'{SPORTS_ROLES.index(field["role"])} {(b["x"] + b["width"] / 2) / 390:.10f} {(b["y"] + b["height"] / 2) / 844:.10f} {b["width"] / 390:.10f} {b["height"] / 844:.10f}')
                        payloads = {"image": image, "annotation": annotation, "labels": ("\n".join(labels) + "\n").encode(),
                                    "provider_truth": _encoded(truth), "source_page": html.encode()}
                        row = {"split": split, "sequence_group": truth["sequence_group"],
                               "tags": {"provider": provider, "layout": provider + "-iphone-v1", "event": truth["quotes"][0]["event_id"],
                                        "seed": seed, "phase": phase, "viewport": "390x844", "odds_format": "decimal"},
                               "sha256": {key: hashlib.sha256(data).hexdigest() for key, data in payloads.items()}}
                        sample_id = _sample_identity(row, manifest)
                        row["sample_id"] = sample_id
                        row.update({"image": f"images/{split}/{sample_id}.png", "labels": f"labels/{split}/{sample_id}.txt",
                                    "annotation": f"annotations/{sample_id}.json", "provider_truth": f"provider-truth/{sample_id}.json",
                                    "source_page": f"source-pages/{sample_id}.html"})
                        for key, data in payloads.items():
                            path = output / row[key]
                            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                            with path.open("xb") as handle:
                                handle.write(data)
                        manifest["samples"].append(row)
            context.close()
            browser.close()
        manifest["dataset_id"] = _dataset_identity(manifest)
        (output / "dataset.json").write_bytes(_encoded(manifest))
        yaml = "path: .\ntrain: images/train\nval: images/validation\ntest: images/test\nnames:\n" + "".join(f"  {i}: {role}\n" for i, role in enumerate(SPORTS_ROLES))
        (output / "dataset.yaml").write_text(yaml, encoding="utf-8")
        audit = audit_dataset(output)
        (output / "audit.json").write_bytes(_encoded(audit))
    except Exception as error:
        (output / "failure.json").write_bytes(_encoded({"accepted": False, "type": type(error).__name__, "reason": str(error)}))
        raise
    return manifest


def audit_dataset(root):
    root = Path(root)
    manifest = json.loads((root / "dataset.json").read_text())
    if manifest.get("schema") != "synthetic-sportsbook-dataset/1" or manifest.get("roles") != list(SPORTS_ROLES):
        raise Refusal("unsupported dataset schema/taxonomy")
    samples = manifest.get("samples")
    if not isinstance(samples, list) or not 1 <= len(samples) <= 288:
        raise Refusal("bounded dataset samples required")
    seen = set()
    groups = {split: {kind: set() for kind in ("sequence", "event", "provider", "layout", "pixels")} for split in SPLIT_PROVIDERS}
    for row in samples:
        split = row.get("split")
        if split not in SPLIT_PROVIDERS or row["tags"]["provider"] != SPLIT_PROVIDERS[split]:
            raise Refusal("provider/layout split contract")
        identity = _sample_identity(row, manifest)
        if row.get("sample_id") != identity or identity in seen:
            raise Refusal("changed or duplicate sample identity")
        seen.add(identity)
        for key in ("image", "annotation", "labels", "provider_truth", "source_page"):
            if _file_digest(_inside(root, row[key])) != row["sha256"][key]:
                raise Refusal("dataset file digest mismatch")
        with Image.open(_inside(root, row["image"])) as image:
            if image.format != "PNG" or image.size != (390, 844):
                raise Refusal("dataset PNG viewport mismatch")
        annotation = json.loads(_inside(root, row["annotation"]).read_text())
        _objects(annotation["fields"], SPORTS_ROLES, "label")
        truth = json.loads(_inside(root, row["provider_truth"]).read_text())
        for quote in truth["quotes"]:
            validate_quote(quote)
        if truth["sequence_group"] != row["sequence_group"]:
            raise Refusal("changed event sequence group")
        for kind, value in (("sequence", row["sequence_group"]), ("event", row["tags"]["event"]),
                            ("provider", row["tags"]["provider"]), ("layout", row["tags"]["layout"]), ("pixels", row["sha256"]["image"])):
            groups[split][kind].add(value)
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        for kind in groups[left]:
            if groups[left][kind] & groups[right][kind]:
                raise Refusal(f"cross-split {kind} leakage")
    if manifest.get("dataset_id") != _dataset_identity(manifest):
        raise Refusal("changed dataset identity")
    return {"schema": "sportsbook-dataset-audit/1", "accepted": True, "dataset_id": manifest["dataset_id"],
            "samples": len(samples), "sha256_verified_files": len(samples) * 5,
            "group_counts": {split: {kind: len(values) for kind, values in kinds.items()} for split, kinds in groups.items()},
            "limitations": ["three fictional provider layouts", "generated-only development data", "pixel checks do not prove perceptual diversity"]}
