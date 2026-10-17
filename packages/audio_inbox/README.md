# Audio inbox

Run from the iPhone project root. The default drop folder is `.local/runtime/audio/inbox`; runtime stores and recordings stay ignored. The package preserves immutable source/transcript versions, reviewed suggested goals and Markdown exports. Per-chunk checkpoints reuse finished work after a known refusal and hold uncertain submissions for review.

Install development dependencies from `packages/audio_inbox` with `uv sync --locked --group dev`. From the project root, run `uv run --project packages/audio_inbox python -m audio_inbox --help`. Use `--fake` for generated-data checks. Live processing requires a private provider JSON passed with `--providers`; transcription and goal generation have separate endpoints and deferred credential references. Never store credentials or recordings in this package.

Run `uv run --project packages/audio_inbox pytest packages/audio_inbox/tests`, Ruff and Pyright before changes. A fake-provider pass does not prove live speech recognition.
