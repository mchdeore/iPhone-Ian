from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from ..benchmark import Refusal

QUOTE_SCHEMA = "synthetic-sportsbook-quote/1"
PROVIDERS = ("provider-a", "provider-b", "provider-c")
FIELDS = {"schema", "provider_id", "event_id", "home", "away", "start_time", "market",
          "period", "selection", "line", "odds_format", "odds", "status", "quote_time"}


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        raise Refusal("explicit UTC timestamp required")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise Refusal("invalid calendar timestamp") from None
    return value


def name(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 80 or value != value.strip()
            or any(not c.isprintable() for c in value)):
        raise Refusal("bounded visible name required")
    return value


def quote_key(quote):
    return (quote["provider_id"], quote["event_id"], quote["market"], quote["period"], quote["selection"])


def validate_quote(quote):
    """Validate already-normalized observations; never guess missing price digits."""
    if not isinstance(quote, dict) or set(quote) != FIELDS or quote["schema"] != QUOTE_SCHEMA:
        raise Refusal("typed quote schema required")
    if quote["provider_id"] not in PROVIDERS:
        raise Refusal("known synthetic provider required")
    if not isinstance(quote["event_id"], str) or not re.fullmatch(r"E[0-9]{6}", quote["event_id"]):
        raise Refusal("visible event identity required")
    home, away, selection = (name(quote[k]) for k in ("home", "away", "selection"))
    if home == away or selection not in (home, away):
        raise Refusal("selection/event association invalid")
    timestamp(quote["start_time"])
    timestamp(quote["quote_time"])
    if quote["market"] not in ("moneyline", "spread") or quote["period"] != "full-game":
        raise Refusal("supported synthetic market/period required")
    line = quote["line"]
    if quote["market"] == "moneyline":
        if line is not None:
            raise Refusal("moneyline has no signed line")
    elif (not isinstance(line, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?", line)
          or not -200 <= Decimal(line) <= 200 or Decimal(line) * 2 != int(Decimal(line) * 2)
          or (line.startswith("-") and Decimal(line) == 0)
          or format(Decimal(line).normalize(), "f") != line):
        raise Refusal("canonical signed half-point line required")
    if quote["odds_format"] != "decimal" or quote["status"] not in ("open", "suspended"):
        raise Refusal("supported odds format/status required")
    odds = quote["odds"]
    if quote["status"] == "suspended":
        if odds is not None:
            raise Refusal("suspended quote must explicitly omit current odds")
    elif (not isinstance(odds, str) or not re.fullmatch(r"[1-9][0-9]{0,2}\.[0-9]{2}", odds)
          or not Decimal("1.01") <= Decimal(odds) <= Decimal("100.00")):
        raise Refusal("exact two-decimal price required")
    return dict(quote)
