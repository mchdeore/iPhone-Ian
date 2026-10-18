"""Generate fictional iPhone pages, serve the curator, and score OCR-to-SQLite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phone_lab.sportsbook.app import create_app
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

        uvicorn.run(create_app(args.dataset, reports=args.reports), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
