"""Generate fictional iPhone pages, serve the curator, and score OCR-to-SQLite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phone_lab.sportsbook.app import create_app, create_red_app
from phone_lab.sportsbook.dataset import build_dataset
from phone_lab.sportsbook.pilot import evaluate_dataset, native_recognizer


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--chrome", required=True, type=Path)
    generate.add_argument("--seeds", type=Path, help="JSON train/validation/test seed lists")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--dataset", required=True, type=Path)
    evaluate.add_argument("--output", required=True, type=Path)
    evaluate.add_argument("--ocr", required=True, type=Path)
    evaluate.add_argument("--ocr-sha256", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--dataset", required=True, type=Path)
    serve.add_argument("--reports", type=Path)
    serve.add_argument("--port", type=int, default=8768)
    serve.add_argument("--surface", choices=("blue", "red"), default="blue")
    serve.add_argument("--arena", type=Path, help="Owned SQLite round shared by the separate local team surfaces")
    serve.add_argument("--jobs", type=Path, help="Optional owned Blue job storage")
    serve.add_argument("--chrome", type=Path, help="Operator-configured Chrome for capture jobs")
    serve.add_argument("--ocr", type=Path, help="Reviewed local native OCR for evaluation jobs")
    serve.add_argument("--ocr-sha256", help="Exact reviewed OCR executable digest")
    args = parser.parse_args()
    if args.command == "generate":
        result = build_dataset(args.output, args.chrome, seeds=json.loads(args.seeds.read_text()) if args.seeds else None)
        print(json.dumps({"dataset_id": result["dataset_id"], "samples": len(result["samples"])}))
    elif args.command == "evaluate":
        result = evaluate_dataset(args.dataset, args.output, recognize=native_recognizer(args.ocr.resolve(), args.ocr_sha256),
                                  provenance={"ocr_executable_sha256": args.ocr_sha256, "recognizer": "reviewed local OCR executable"})
        print(json.dumps({"final_database": result["final_database"], "report": str(args.output / "reports" / "index.html")}))
    else:
        if not 1024 <= args.port <= 65535:
            parser.error("port must be between 1024 and 65535")
        import uvicorn

        if args.surface == "red" and (args.arena is None or any((args.reports, args.jobs, args.chrome, args.ocr, args.ocr_sha256))):
            parser.error("red surface requires --arena and refuses Blue reports/jobs/executors")
        app = create_red_app(args.dataset, arena=args.arena) if args.surface == "red" else create_app(args.dataset, reports=args.reports, arena=args.arena, jobs=args.jobs, browser=args.chrome, ocr=args.ocr, ocr_sha256=args.ocr_sha256)
        uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
