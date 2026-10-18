"""Bounded CPU development pilot; generated data cannot accept a real-phone model."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from phone_lab.dataset import ROLES, audit
from phone_lab.metrics import detection_metrics, latency, ocr_metrics
from phone_lab.training_policy import assert_training_allowed
from phone_lab.workflow import color_candidates


def stamp():
    return datetime.now(ZoneInfo("America/Toronto")).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--epochs", type=int, choices=range(1, 51), default=2)
    args = parser.parse_args()
    assert_training_allowed()
    dataset = args.dataset.resolve()
    root = args.output.resolve()
    ocr = args.ocr.resolve()
    if root.exists():
        raise RuntimeError("new immutable experiment directory required")
    manifest = json.loads((dataset / "manifest.json").read_text())
    checked = audit(manifest, dataset)
    if not checked["accepted"]:
        raise RuntimeError("dataset audit refused training")
    root.mkdir(parents=True, mode=0o700)
    os.environ["YOLO_CONFIG_DIR"] = str(root / "config")
    os.environ["TORCH_HOME"] = str(root / "torch")
    os.environ["MPLCONFIGDIR"] = str(root / "matplotlib")
    os.chdir(root)
    result = {
        "schema": "owned-vision-pilot/1",
        "start_Toronto": stamp(),
        "dataset_sha256": sha(dataset / "manifest.json"),
        "dataset_audit": checked,
        "device": "cpu",
        "FP32": True,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "actual_GTX1080_tested": False,
        "hypothetical_16GB_GPU_tested": False,
        "real_phone_holdout": "missing",
        "distributed_or_hosted_license_acceptance": "pending; local research only",
        "versions": {
            p: importlib.metadata.version(p)
            for p in ["torch", "torchvision", "ultralytics", "numpy", "onnx", "onnxruntime"]
        },
    }

    def save():
        (root / "result.json").write_text(
            json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )

    save()
    try:
        license_url = "https://raw.githubusercontent.com/ultralytics/ultralytics/v8.3.0/LICENSE"
        with urllib.request.urlopen(license_url, timeout=30) as response:
            license_bytes = response.read(200000)
        (root / "ultralytics-AGPL-3.0.txt").write_bytes(license_bytes)
        result["upstream_license"] = {
            "url": license_url,
            "sha256": hashlib.sha256(license_bytes).hexdigest(),
            "fetched_Toronto": stamp(),
        }
        import numpy as np
        import torch
        from ultralytics import YOLO

        torch.set_num_threads(2)
        result["torch_inventory"] = {
            "cuda_available": torch.cuda.is_available(),
            "compiled_cuda": torch.version.cuda,
            "compiled_arches": torch.cuda.get_arch_list() if torch.cuda.is_available() else [],
            "threads": torch.get_num_threads(),
        }
        model = YOLO("yolo11n.pt")
        result["pretrained_checkpoint_sha256"] = sha(root / "yolo11n.pt")
        proof = copy.deepcopy(model.model).float().to("cpu").train().requires_grad_(True)
        before = next(proof.parameters()).detach().clone()
        optimizer = torch.optim.SGD(proof.parameters(), lr=0.001)
        outputs = proof(torch.rand(2, 3, 64, 64))
        loss = sum(t.square().mean() for t in outputs)
        loss.backward()
        optimizer.step()
        result["optimizer_proof"] = {
            "finite_loss": bool(torch.isfinite(loss)),
            "weights_changed": bool(torch.any(next(proof.parameters()).detach() != before)),
            "unmodified_pretrained_preserved": True,
        }
        del proof, optimizer, outputs, loss
        rows = [r for r in manifest["rows"] if r["split"] == "test"]
        phases = {}

        def measure(name, model=None):
            totals = {}
            times = []
            ocr_times = []
            ocr_total = {}
            records = []
            for row in rows:
                image = dataset / row["image"]
                start = time.perf_counter()
                if model is None:
                    predictions = color_candidates(image)
                else:
                    pred = model.predict(
                        str(image), device="cpu", imgsz=640, conf=0.25, verbose=False
                    )[0]
                    predictions = []
                    for coords, confidence, cls in zip(
                        pred.boxes.xyxy.cpu().tolist(),
                        pred.boxes.conf.cpu().tolist(),
                        pred.boxes.cls.cpu().tolist(),
                    ):
                        x, y, x2, y2 = coords
                        predictions.append(
                            {
                                "box": {"x": x, "y": y, "width": x2 - x, "height": y2 - y},
                                "confidence": confidence,
                                "role": ROLES[int(cls)] if name == "fine_tuned" else "unknown",
                            }
                        )
                times.append((time.perf_counter() - start) * 1000)
                metrics = detection_metrics(
                    row["labels"], predictions, class_aware=name == "fine_tuned"
                )
                for key, value in metrics.items():
                    if isinstance(value, int) and not isinstance(value, bool):
                        totals[key] = totals.get(key, 0) + value
                ocr_start = time.perf_counter()
                process = subprocess.run(
                    [str(ocr), str(image)], capture_output=True, text=True, timeout=20, check=True
                )
                texts = json.loads(process.stdout)
                ocr_times.append((time.perf_counter() - ocr_start) * 1000)
                om = ocr_metrics(row["labels"], texts)
                for key, value in om.items():
                    ocr_total[key] = ocr_total.get(key, 0) + value
                records.append(
                    {"id": row["id"], "prediction": predictions, "detection": metrics, "ocr": om}
                )
            totals["precision"] = totals["true_positive"] / max(1, totals["predictions"])
            totals["recall"] = totals["true_positive"] / max(1, totals["truth"])
            ocr_total["CER"] = ocr_total["character_errors"] / max(1, ocr_total["characters"])
            report = {
                "images": len(rows),
                "class_aware": name == "fine_tuned",
                "metrics": totals,
                "inference_including_decode": latency(times),
                "OCR_with_process_start": latency(ocr_times),
                "ocr": ocr_total,
                "task_success": "not measured by static detector evaluation",
                "real_device_acceptance": False,
            }
            (root / f"{name}-frames.json").write_text(json.dumps(records, indent=2))
            phases[name] = report
            result["phases"] = phases
            save()

        measure("pixel_border")
        measure("unchanged_pretrained", model)
        train_args = {
            "data": str(dataset / "dataset.yaml"),
            "device": "cpu",
            "imgsz": 640,
            "epochs": args.epochs,
            "patience": 10,
            "batch": 2,
            "workers": 0,
            "amp": False,
            "seed": 17,
            "close_mosaic": 0,
            "mosaic": 0,
            "fliplr": 0,
            "flipud": 0,
            "degrees": 0,
            "shear": 0,
            "perspective": 0,
            "translate": 0.02,
            "scale": 0.1,
            "hsv_h": 0,
            "hsv_s": 0,
            "hsv_v": 0.2,
            "plots": False,
            "project": str(root / "training"),
            "name": "bounded-pilot",
            "exist_ok": False,
            "cache": False,
            "verbose": False,
        }
        result["training_args"] = train_args
        save()
        start = time.perf_counter()
        model.train(**train_args)
        result["training_seconds"] = time.perf_counter() - start
        checkpoint = root / "training/bounded-pilot/weights/best.pt"
        fine = YOLO(str(checkpoint))
        result["fine_checkpoint_sha256"] = sha(checkpoint)
        measure("fine_tuned", fine)
        validation = fine.val(
            data=str(dataset / "dataset.yaml"),
            split="test",
            device="cpu",
            imgsz=640,
            batch=2,
            workers=0,
            plots=False,
            verbose=False,
        )
        result["generated_test_native_metrics"] = {
            k: float(v) for k, v in validation.results_dict.items()
        }
        save()
        exported = Path(
            fine.export(
                format="onnx",
                imgsz=640,
                batch=1,
                dynamic=False,
                half=False,
                simplify=False,
                opset=17,
                device="cpu",
            )
        )
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        session = ort.InferenceSession(str(exported), options, providers=["CPUExecutionProvider"])
        parity = []
        import cv2
        from ultralytics.data.augment import LetterBox

        for row in rows[:3]:
            im = LetterBox((640, 640), auto=False)(image=cv2.imread(str(dataset / row["image"])))
            data = (
                np.ascontiguousarray(im[:, :, ::-1].transpose(2, 0, 1)[None]).astype(np.float32)
                / 255
            )
            fine.model.eval()
            with torch.no_grad():
                expected = fine.model(torch.from_numpy(data))
            if isinstance(expected, (tuple, list)):
                expected = expected[0]
            expected = expected.cpu().numpy()
            actual = session.run(None, {session.get_inputs()[0].name: data})[0]
            parity.append(
                {
                    "frame": row["id"],
                    "shape_match": expected.shape == actual.shape,
                    "max_abs_error": float(np.max(np.abs(expected - actual))),
                    "allclose_atol_rtol_1e-3": bool(
                        np.allclose(expected, actual, atol=1e-3, rtol=1e-3)
                    ),
                }
            )
        result["onnx"] = {
            "sha256": sha(exported),
            "parity": parity,
            "raw_output_parity_passed": all(p["allclose_atol_rtol_1e-3"] for p in parity),
            "optimized_action_parity": "not accepted; no deployed policy",
            "CPU_runtime": ort.__version__,
        }
        result["local_generated_pipeline_passed"] = (
            all(result["optimizer_proof"][k] for k in ["finite_loss", "weights_changed"])
            and result["onnx"]["raw_output_parity_passed"]
        )
        result["end_Toronto"] = stamp()
        save()
        print(
            json.dumps(
                {
                    "local_generated_pipeline_passed": result["local_generated_pipeline_passed"],
                    "result": str(root / "result.json"),
                    "real_phone_accepted": False,
                }
            )
        )
    except Exception as error:
        result["failure"] = {
            "type": type(error).__name__,
            "message": str(error),
            "Toronto": stamp(),
        }
        result["local_generated_pipeline_passed"] = False
        save()
        raise


if __name__ == "__main__":
    main()
