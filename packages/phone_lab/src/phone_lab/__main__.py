from __future__ import annotations

import argparse
import json
import os
import secrets
from pathlib import Path

from .benchmark import Benchmark, Refusal


def main() -> int:
    parser = argparse.ArgumentParser(prog="phone-lab")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--store", type=Path, default=Path(".local/runtime/phone-lab"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--device", default="owned-device")
    serve.add_argument("--seed", type=int, default=73)
    serve.add_argument("--task", default="tap")
    dataset = commands.add_parser("dataset")
    dataset.add_argument("destination", type=Path)
    dataset.add_argument("--seeds", type=int, default=12)
    dataset.add_argument("--browser-executable")
    check = commands.add_parser("audit")
    check.add_argument("directory", type=Path)
    data_web = commands.add_parser(
        "data-web", help="Curator app for deterministic synthetic datasets"
    )
    data_web.add_argument("--store", type=Path, default=Path(".local/synthetic-data"))
    data_web.add_argument("--browser-executable")
    data_web.add_argument("--port", type=int, default=8766)
    battle_web = commands.add_parser("battle-web", help="Read-only battle scoreboard")
    battle_web.add_argument("--store", type=Path, default=Path(".local/battles/latest"))
    battle_web.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    if args.command == "dataset":
        from .dataset import generate

        m = generate(args.destination, list(range(args.seeds)), executable=args.browser_executable)
        print(
            json.dumps(
                {
                    "rows": len(m["rows"]),
                    "manifest_sha256": m["manifest_sha256"],
                    "source": "generated-browser",
                    "real_phone_holdout": "missing",
                }
            )
        )
    elif args.command == "audit":
        from .dataset import audit

        m = json.loads((args.directory / "manifest.json").read_text())
        result = audit(m, args.directory)
        print(json.dumps(result))
        return 0 if result["accepted"] else 1
    elif args.command in {"data-web", "battle-web"}:
        import uvicorn

        if not 1024 <= args.port <= 65535:
            raise Refusal("local port bounds")
        if args.command == "data-web":
            from .catalog import create_dataset_app

            app = create_dataset_app(args.store, executable=args.browser_executable)
        else:
            from .battle import create_dashboard

            app = create_dashboard(args.store)
        print(f"Gantry lab: http://127.0.0.1:{args.port}", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, log_level="warning")
    else:
        import uvicorn

        from .web import create_app

        store = Benchmark(args.store)
        keys = args.store / "operator-config.json"
        if keys.exists():
            if keys.is_symlink():
                raise Refusal("configuration symlink refused")
            config = json.loads(keys.read_text())
        else:
            config = {"operator": secrets.token_urlsafe(32), "evaluator": secrets.token_urlsafe(32)}
            fd = os.open(keys, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(config, f)
        s = store.create(args.device, args.seed, 390, 700, args.task)
        print(f"Owned generated task: http://{args.host}:{args.port}/s/{s.id}", flush=True)
        uvicorn.run(
            create_app(store, config["operator"], config["evaluator"]),
            host=args.host,
            port=args.port,
            access_log=False,
            log_level="warning",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
