"""Private controller configuration with one deferred credential reference."""

import json
from pathlib import Path

from .providers import AzureGoalSuggester, AzureTranscriber, ProviderAdapterError


def providers(path: Path, *, db_path: Path | None = None):
    if path.is_symlink():
        raise ValueError("unsafe_configuration")
    config = json.loads(path.read_text())
    reference = config["key_ref"]
    filename, field = reference.split(":", 1)
    if Path(filename).name != filename or not filename or not field:
        raise ValueError("invalid_key_reference")
    key_path = path.parent / filename

    def key():
        if key_path.is_symlink():
            raise ProviderAdapterError("unsafe_key_reference")
        values = dict(
            line.split("=", 1)
            for line in key_path.read_text().splitlines()
            if "=" in line and not line.startswith("#")
        )
        return values.get(field, "")

    transcription = config.get("transcription")
    goals = config.get("goals")
    transcriber = AzureTranscriber(key_provider=key, **transcription) if transcription else None
    suggester = AzureGoalSuggester(key_provider=key, **goals) if goals else None
    chunks = config.get("chunking")
    if chunks is not None:
        if transcriber is None or db_path is None or not isinstance(chunks, dict):
            raise ValueError("invalid_chunking_configuration")
        from .chunk_store import ChunkedTranscriber

        transcriber = ChunkedTranscriber(
            db_path, transcriber, transcriber.model, "pcm-window-v1", chunks
        )
    return transcriber, suggester
