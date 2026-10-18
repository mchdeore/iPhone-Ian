from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from ..benchmark import Refusal
from .contracts import PROVIDERS, QUOTE_SCHEMA, quote_key, validate_quote

TEAMS = ("North Owls", "Bay Bears", "South Foxes", "Lake Wolves", "East Hawks", "West Lynx")


def provider_snapshot(seed, phase, *, provider="provider-a"):
    """Fictional records and known update/suspension states; evaluator channel."""
    if type(seed) is not int or not 0 <= seed <= 999999 or type(phase) is not int or not 0 <= phase <= 2:
        raise Refusal("synthetic seed/phase bounds")
    if provider not in PROVIDERS:
        raise Refusal("synthetic provider required")
    rng = random.Random(seed)
    home, away = rng.sample(TEAMS, 2)
    start = datetime(2026, 1, 1, 20, tzinfo=timezone.utc) + timedelta(days=seed % 100)
    quoted = start - timedelta(hours=2) + timedelta(seconds=phase * 30)
    base = {"schema": QUOTE_SCHEMA, "provider_id": provider, "event_id": f"E{seed:06d}",
            "home": home, "away": away, "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "period": "full-game", "odds_format": "decimal", "status": "open",
            "quote_time": quoted.strftime("%Y-%m-%dT%H:%M:%SZ")}
    quotes = []
    for market in ("moneyline", "spread"):
        for index, selection in enumerate(sorted((home, away))):
            price_cents = 170 + rng.randrange(40) + phase * 3
            quote = base | {"market": market, "selection": selection,
                            "line": None if market == "moneyline" else ("-2.5" if index == 0 else "2.5"),
                            "odds": f"{price_cents // 100}.{price_cents % 100:02d}"}
            quotes.append(validate_quote(quote))
    quotes.sort(key=quote_key)
    if phase == 2:
        quotes[1] = validate_quote(quotes[1] | {"status": "suspended", "odds": None})
    return {"schema": "synthetic-provider-snapshot/1", "provider_id": provider,
            "seed": seed, "phase": phase, "sequence_group": f"{provider}-event-{seed}",
            "quotes": quotes, "source": "fictional owned generator; evaluator only"}
