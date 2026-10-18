"""OCR-only baseline: explicit visible headers, row association and typed refusals."""

from __future__ import annotations

import re
from decimal import Decimal

from ..benchmark import Refusal, finite
from .contracts import QUOTE_SCHEMA, quote_key, timestamp, validate_quote


def _cy(row):
    return row["box"]["y"] + row["box"]["height"] / 2


def _cx(row):
    return row["box"]["x"] + row["box"]["width"] / 2


def ocr_regions(recognized):
    if not isinstance(recognized, list) or len(recognized) > 1000:
        raise Refusal("bounded OCR page required")
    texts = []
    for row in recognized:
        if not isinstance(row, dict) or set(row) != {"text", "confidence", "box"}:
            raise Refusal("OCR-only observation required")
        value = row["text"]
        if not isinstance(value, str) or not 1 <= len(value) <= 1000 or any(not c.isprintable() and not c.isspace() for c in value):
            raise Refusal("bounded OCR text required")
        box = row["box"]
        if not isinstance(box, dict) or set(box) != {"x", "y", "width", "height"}:
            raise Refusal("OCR box required")
        b = {k: finite(box[k], 0 if k in ("x", "y") else 0.000001, 4096, k) for k in box}
        if b["x"] + b["width"] > 4096 or b["y"] + b["height"] > 4096:
            raise Refusal("OCR box outside bounds")
        texts.append({"text": " ".join(value.split()), "confidence": finite(row["confidence"], 0, 1, "OCR confidence"), "box": b})
    texts.sort(key=lambda row: (_cy(row), _cx(row), row["text"]))
    for index, row in enumerate(texts):
        row["id"] = f"ocr-{index}"
    return texts


def parse_page(recognized, *, minimum_confidence=0.9):
    minimum_confidence = finite(minimum_confidence, 0.5, 1, "OCR confidence threshold")
    texts = ocr_regions(recognized)
    if not texts:
        raise Refusal("nonempty OCR page required")
    fields, refusals, quotes = [], [], []

    def find(pattern):
        return [row for row in texts if re.fullmatch(pattern, row["text"], re.IGNORECASE)]

    def one(pattern, label):
        candidates = find(pattern)
        if len(candidates) != 1 or candidates[0]["confidence"] < minimum_confidence:
            raise Refusal(f"missing/ambiguous/uncertain {label}")
        return candidates[0]

    def emit(role, row):
        fields.append({"id": row["id"], "role": role, "box": dict(row["box"]),
                       "confidence": row["confidence"], "text": row["text"]})

    provider = one(r"Provider\s*([ABC])", "provider")
    provider_id = "provider-" + re.fullmatch(r"Provider\s*([ABC])", provider["text"], re.IGNORECASE).group(1).lower()
    one(r"Decimal odds", "odds format")
    event = one(r"Event E[0-9]{6}", "event")
    event_id = event["text"].split()[-1].upper()
    updated = one(r"Updated [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} UTC", "quote time")
    started = one(r"Start [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} UTC", "start time")
    anchors = [row for row in texts if "@" in row["text"] and _cy(event) < _cy(row) < _cy(started)]
    if len(anchors) != 1:
        raise Refusal("missing/ambiguous event participants")
    fragments = sorted((row for row in texts if _cy(event) < _cy(row) < _cy(started)
                        and abs(_cy(row) - _cy(anchors[0])) <= 12), key=lambda row: row["box"]["x"])
    if len(fragments) > 6 or any(row["confidence"] < minimum_confidence for row in fragments) or any(
        not -2 <= right["box"]["x"] - left["box"]["x"] - left["box"]["width"] <= 32
        for left, right in zip(fragments, fragments[1:])
    ):
        raise Refusal("uncertain/disconnected event participant fragments")
    x = min(row["box"]["x"] for row in fragments)
    y = min(row["box"]["y"] for row in fragments)
    participants = {"id": "_".join(row["id"] for row in fragments),
                    "text": " ".join(row["text"] for row in fragments),
                    "confidence": min(row["confidence"] for row in fragments),
                    "box": {"x": x, "y": y,
                            "width": max(row["box"]["x"] + row["box"]["width"] for row in fragments) - x,
                            "height": max(row["box"]["y"] + row["box"]["height"] for row in fragments) - y}}
    parts = participants["text"].split("@")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise Refusal("ambiguous participant order")
    away, home = (part.strip() for part in parts)

    def utc(row):
        parts = row["text"].split()
        return timestamp(parts[1] + "T" + parts[2] + "Z")

    base = {"schema": QUOTE_SCHEMA, "provider_id": provider_id, "event_id": event_id,
            "home": home, "away": away, "start_time": utc(started), "quote_time": utc(updated),
            "odds_format": "decimal", "period": "full-game"}
    for role, row in (("provider", provider), ("event", event), ("participant", participants),
                      ("event_time", started), ("quote_time", updated)):
        emit(role, row)
    markets = sorted(find(r"Moneyline|Spread"), key=_cy)
    if not markets or len(markets) > 2 or len({m["text"].lower() for m in markets}) != len(markets):
        raise Refusal("missing/duplicate market headings")
    for index, market in enumerate(markets):
        market_name = market["text"].lower()
        stop = _cy(markets[index + 1]) - 10 if index + 1 < len(markets) else 4096
        try:
            period = [row for row in find(r"Full game") if abs(_cy(row) - _cy(market)) <= 15]
            if len(period) != 1 or period[0]["confidence"] < minimum_confidence or market["confidence"] < minimum_confidence:
                raise Refusal("missing/ambiguous/uncertain market period")
            headers = []
            for heading in ("Selection", "Line", "Odds", "State"):
                candidates = [row for row in find(heading) if _cy(market) + 10 <= _cy(row) <= _cy(market) + 75]
                if len(candidates) != 1 or candidates[0]["confidence"] < minimum_confidence:
                    raise Refusal("missing/ambiguous/uncertain column heading")
                headers.append(candidates[0])
            if sorted(headers, key=_cx) != headers:
                raise Refusal("unsupported column order; retained for improvement")
            boundaries = [(_cx(a) + _cx(b)) / 2 for a, b in zip(headers, headers[1:])]
            start = max(_cy(row) for row in headers) + 15
            eligible = [row for row in texts if start < _cy(row) < stop]
            groups = []
            for row in eligible:
                if not groups or abs(_cy(row) - sum(_cy(r) for r in groups[-1]) / len(groups[-1])) > 12:
                    groups.append([])
                groups[-1].append(row)
            emit("market", market)
            emit("period", period[0])
            for group in groups:
                columns = [[] for _ in range(4)]
                for row in group:
                    column = sum(_cx(row) > bound for bound in boundaries)
                    columns[column].append(row)
                # Navigation and other page text cannot create a candidate record.
                if not (any(r["text"] in (home, away) for r in columns[0]) or any(r["text"].lower() in ("open", "suspended") for r in columns[3])):
                    continue
                try:
                    values = []
                    for column in columns:
                        if not 1 <= len(column) <= 3 or any(r["confidence"] < minimum_confidence for r in column):
                            raise Refusal("missing/ambiguous/uncertain row field")
                        values.append(" ".join(r["text"] for r in sorted(column, key=_cx)))
                    selection, raw_line, raw_odds, status = values
                    status = status.lower()
                    line = None
                    if market_name == "moneyline":
                        if raw_line not in ("—", "–", "-"):
                            raise Refusal("unexpected moneyline line")
                    else:
                        raw_line = raw_line.replace("−", "-")
                        if not re.fullmatch(r"[+-]?(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?", raw_line):
                            raise Refusal("unreadable signed line")
                        number = Decimal(raw_line)
                        line = "0" if number == 0 else format(number.normalize(), "f")
                    if status == "suspended":
                        if raw_odds not in ("—", "–", "-"):
                            raise Refusal("suspended odds evidence ambiguous")
                        odds = None
                    else:
                        odds = raw_odds
                    quote = validate_quote(base | {"market": market_name, "selection": selection,
                                                   "line": line, "odds": odds, "status": status})
                    fields_before = len(fields)
                    for role, column in zip(("selection", "line", "odds", "status"), columns):
                        for row in column:
                            emit(role, row)
                    if fields_before == len(fields):
                        raise Refusal("record requires OCR evidence")
                    # Validation and storage use the observed values, never provider truth.
                    base_quote = quote
                    quotes.append(base_quote)
                except Refusal as error:
                    refusals.append({"operation": "extract-row", "market": market_name,
                                     "reason": str(error), "ocr_ids": [row["id"] for row in group]})
        except Refusal as error:
            refusals.append({"operation": "identify-market", "market": market_name, "reason": str(error)})
    return {"schema": "sportsbook-ocr-extraction/1", "quotes": sorted(quotes, key=quote_key),
            "fields": fields, "refusals": refusals,
            "inputs": "OCR text, confidence and observed boxes only", "parser_version": "visible-columns/2"}
