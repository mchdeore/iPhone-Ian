from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from .benchmark import TASKS, Refusal, Session
from .web import page

ROLES = ("button", "field", "handle", "destination", "list")
SPLITS = ("train", "val", "test")


def image_hash(path: Path) -> str:
    """Declared average-hash proxy, excluding frame marker/instruction text."""
    with Image.open(path) as im:
        crop = im.crop((0, min(110, im.height - 1), im.width, im.height)).convert("L")
        values = list(crop.resize((32, 32)).getdata())
    mean = sum(values) / len(values)
    bits = "".join("1" if v >= mean else "0" for v in values)
    return f"{int(bits, 2):0256x}"


def generate(
    destination: Path,
    seeds: list[int],
    *,
    executable: str | None = None,
    width: int = 390,
    height: int = 700,
) -> dict:
    """Actual browser render and measured DOM truth, exclusively in the evaluator dataset."""
    from playwright.sync_api import sync_playwright

    if destination.exists():
        raise Refusal("dataset destination already exists")
    if len(set(seeds)) != len(seeds) or not seeds or len(seeds) > 1000:
        raise Refusal("unique bounded seeds required")
    destination.mkdir(parents=True, mode=0o700)
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=executable, args=["--disable-gpu"]
        )
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                reduced_motion="reduce",
            )
            rendered = context.new_page()
            for seed in seeds:
                if type(seed) is not int or not 0 <= seed <= 2**31 - 1:
                    raise Refusal("seed bounds")
                split = SPLITS[seed % 3]
                device = f"generated-{split}"
                for task in TASKS:
                    phases = (0, 1) if task in {"menu", "overlay", "scroll"} else (0,)
                    for phase in phases:
                        sid = hashlib.sha256(f"{device}:{seed}:{task}".encode()).hexdigest()[:24]
                        s = Session(
                            sid,
                            device,
                            seed,
                            width,
                            height,
                            task,
                            "generated-no-dispatch",
                            phase=phase,
                            frame=phase + 1,
                        )
                        rendered.set_content(page(s), wait_until="load")
                        rendered.evaluate("document.fonts.ready")
                        rendered.evaluate(
                            "new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))"
                        )
                        labels = rendered.locator("[data-label]").evaluate_all("""els => els.map(el => {
const b=el.getBoundingClientRect();return {id:el.dataset.label,role:el.dataset.role,
box:{x:b.x,y:b.y,width:b.width,height:b.height},
text:el.dataset.role==='list'?null:(el.tagName==='INPUT'?el.value:el.innerText)}})""")
                        name = f"{seed:06d}-{task}-{phase}"
                        image_dir = destination / "images" / split
                        label_dir = destination / "labels" / split
                        image_dir.mkdir(parents=True, exist_ok=True)
                        label_dir.mkdir(parents=True, exist_ok=True)
                        image = image_dir / f"{name}.png"
                        previous = rendered.screenshot(animations="disabled")
                        attempts = [previous]
                        for attempt in range(3):
                            current = rendered.screenshot(animations="disabled")
                            attempts.append(current)
                            if current == previous:
                                break
                            previous = current
                        else:
                            rejected = destination / ".rejected"
                            rejected.mkdir(exist_ok=True)
                            for i, data in enumerate(attempts):
                                (rejected / f"{name}-{i}.png").write_bytes(data)
                            raise Refusal(
                                "browser pixels did not settle; rejected captures retained"
                            )
                        image.write_bytes(current)
                        normalized = []
                        for label in labels:
                            b = label["box"]
                            if not (
                                0 <= b["x"] < b["x"] + b["width"] <= width
                                and 0 <= b["y"] < b["y"] + b["height"] <= height
                            ):
                                raise Refusal("rendered label outside viewport")
                            normalized.append(
                                f"{ROLES.index(label['role'])} {(b['x'] + b['width'] / 2) / width:.9f} {(b['y'] + b['height'] / 2) / height:.9f} {b['width'] / width:.9f} {b['height'] / height:.9f}"
                            )
                        label_file = label_dir / f"{name}.txt"
                        label_file.write_text("\n".join(normalized) + "\n")
                        rows.append(
                            {
                                "id": name,
                                "source": "generated-browser",
                                "split": split,
                                "session": sid,
                                "device": device,
                                "layout_group": f"layout-{seed}",
                                "font_group": ("Arial", "Georgia", "Verdana")[seed % 3],
                                "seed": seed,
                                "task": task,
                                "phase": phase,
                                "frame": s.marker,
                                "viewport": [width, height],
                                "labels": labels,
                                "image": str(image.relative_to(destination)),
                                "yolo_label": str(label_file.relative_to(destination)),
                                "yolo_sha256": hashlib.sha256(label_file.read_bytes()).hexdigest(),
                                "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                                "average_hash": image_hash(image),
                                "render_recipe_sha256": hashlib.sha256(
                                    page(s).encode()
                                ).hexdigest(),
                            }
                        )
            context.close()
        finally:
            browser.close()
    manifest = {
        "schema": "phone-dataset/3",
        "capture_stability": "software compositor; fonts ready; two animation frames; two equal PNG captures within four attempts",
        "source": "owned-generated",
        "browser": "Chromium via Playwright",
        "roles": list(ROLES),
        "seeds": seeds,
        "rows": rows,
        "real_phone_holdout": "missing; no final real-device metric accepted",
    }
    data = json.dumps(manifest, sort_keys=True, indent=2)
    (destination / "manifest.json").write_text(data)
    manifest["manifest_sha256"] = hashlib.sha256(data.encode()).hexdigest()
    (destination / "dataset.yaml").write_text(
        f"path: {destination.resolve()}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n"
        + "".join(f"  {i}: {role}\n" for i, role in enumerate(ROLES))
    )
    return manifest


def audit(manifest: dict, root: Path, *, near_distance: int = 2) -> dict:
    """Fail closed on hash, alignment, leakage or declared near-duplicate proxy violations."""
    if type(near_distance) is not int or not 0 <= near_distance <= 1024:
        raise Refusal("near-duplicate distance bounds")
    if manifest.get("schema") != "phone-dataset/3":
        raise Refusal("older dataset recipe retained; generate a new stable capture set")
    errors = []
    seen_groups = {}
    rows = manifest["rows"]
    for row in rows:
        path = root / row["image"]
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise Refusal("dataset image escapes root")
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            errors.append(f"image hash:{row['id']}")
        if image_hash(path) != row["average_hash"]:
            errors.append(f"perceptual recipe:{row['id']}")
        label_file = root / row["yolo_label"]
        if label_file.is_symlink() or not label_file.resolve().is_relative_to(root.resolve()):
            raise Refusal("dataset label escapes root")
        if hashlib.sha256(label_file.read_bytes()).hexdigest() != row["yolo_sha256"]:
            errors.append(f"YOLO label hash:{row['id']}")
        for field in ("session", "device", "layout_group", "font_group"):
            key = (field, row[field])
            prior = seen_groups.setdefault(key, row["split"])
            if prior != row["split"]:
                errors.append(f"group crosses split:{key}")
        w, h = row["viewport"]
        for label in row["labels"]:
            b = label["box"]
            if label["role"] not in ROLES or not (
                0 <= b["x"] < b["x"] + b["width"] <= w and 0 <= b["y"] < b["y"] + b["height"] <= h
            ):
                errors.append(f"label bounds:{row['id']}")
    near = []
    for index, a in enumerate(rows):
        for b in rows[index + 1 :]:
            if a["split"] == b["split"]:
                continue
            distance = (int(a["average_hash"], 16) ^ int(b["average_hash"], 16)).bit_count()
            if a["sha256"] == b["sha256"] or distance <= near_distance:
                near.append({"a": a["id"], "b": b["id"], "distance": distance})
    return {
        "accepted": not errors and not near,
        "errors": errors,
        "near_duplicates": near,
        "near_proxy": "32x32 average hash; excludes first 110px; requires visual review",
        "near_distance": near_distance,
        "rows": len(rows),
    }
