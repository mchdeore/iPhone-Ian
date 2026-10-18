"""Fictional iPhone sportsbook screens; DOM truth is a generator/evaluator channel."""

from __future__ import annotations

from html import escape

from ..benchmark import Refusal
from .contracts import PROVIDERS, quote_key, validate_quote

THEMES = {
    "provider-a": ("#1475d8", "#f2f5fa", "#ffffff", "#15263e", "Arial"),
    "provider-b": ("#7556ce", "#171923", "#282b3a", "#f5f4fa", "Georgia"),
    "provider-c": ("#107952", "#edf7f2", "#ffffff", "#153326", "Verdana"),
}


def _field(role, ident, text, css=""):
    return f'<span data-role="{role}" data-label="{ident}" class="field {css}">{escape(text)}</span>'


def _display_time(value):
    return value.replace("T", " ").replace("Z", " UTC")


def provider_page(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("schema") != "synthetic-provider-snapshot/1":
        raise Refusal("synthetic provider snapshot required")
    provider = snapshot.get("provider_id")
    quotes = snapshot.get("quotes")
    if provider not in PROVIDERS or not isinstance(quotes, list) or len(quotes) != 4:
        raise Refusal("four-row provider snapshot required")
    quotes = sorted((validate_quote(q) for q in quotes), key=quote_key)
    shared = ("provider_id", "event_id", "home", "away", "start_time", "quote_time")
    first = quotes[0]
    if first["provider_id"] != provider or any(any(q[k] != first[k] for k in shared) for q in quotes):
        raise Refusal("inconsistent visible snapshot metadata")
    if len({quote_key(q) for q in quotes}) != 4:
        raise Refusal("duplicate page row")
    primary, background, card, ink, font = THEMES[provider]
    provider_name = provider.replace("-", " ").title()
    cards = []
    for market in ("moneyline", "spread"):
        rows = [q for q in quotes if q["market"] == market]
        if len(rows) != 2:
            raise Refusal("two selections per market required")
        body = []
        for index, q in enumerate(rows):
            prefix = f"{market}-{index}"
            line = "—" if q["line"] is None else ("+" + q["line"] if not q["line"].startswith("-") else q["line"])
            body.append('<div class="row">' +
                        _field("selection", prefix + "-selection", q["selection"], "selection") +
                        _field("line", prefix + "-line", line, "line") +
                        _field("odds", prefix + "-odds", q["odds"] or "—", "odds") +
                        _field("status", prefix + "-status", q["status"].title(), "state") + '</div>')
        heading = "Moneyline" if market == "moneyline" else "Spread"
        cards.append('<section class="market"><header>' + _field("market", market + "-title", heading) +
                     _field("period", market + "-period", "Full game", "period") + '</header>' +
                     '<div class="columns"><span>Selection</span><span>Line</span><span>Odds</span><span>State</span></div>' +
                     "".join(body) + '</section>')
    navigation = ''.join(f'<a href="#markets">{_field("navigation", "nav-" + text.lower(), text)}</a>'
                         for text in ("Sports", "Live", "Bets", "Account"))
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{escape(provider_name)} · synthetic sports</title><style>
*{{box-sizing:border-box}}:root{{color-scheme:light;--primary:{primary};--bg:{background};--card:{card};--ink:{ink}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px {font},sans-serif;min-height:100vh}}
.screen{{max-width:600px;margin:auto;padding-bottom:100px}}.statusbar{{height:28px;padding:6px 24px;font:12px Arial;display:flex;justify-content:space-between}}
.brand{{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:var(--primary);color:white}}
.brand .field{{font-size:22px;font-weight:700}}.format{{font:11px Arial;border:1px solid #ffffff77;border-radius:16px;padding:6px}}
main{{padding:12px 16px}}.updated{{font-size:11px;margin-bottom:12px}}.event{{background:var(--card);padding:14px;border-radius:12px;margin-bottom:12px}}
.event-code{{font-size:12px;opacity:.8}}.participants{{display:flex;gap:10px;align-items:center;font-size:16px;font-weight:700;margin:12px 0}}
.start{{font-size:11px}}.field{{display:inline-block}}.market{{background:var(--card);padding:12px;border-radius:12px;margin:12px 0}}
.market header{{display:flex;justify-content:space-between;align-items:center;font-size:17px;font-weight:700;padding-bottom:10px}}
.period{{font-size:11px;font-weight:400;opacity:.8}}.columns,.row{{display:grid;grid-template-columns:minmax(0,1fr) 40px 58px 70px;gap:4px;align-items:center}}
.columns{{font-size:10px;opacity:.7;padding:5px 0}}.row{{padding:10px 0;border-top:1px solid #8899aa33;min-height:55px}}
.selection{{font-size:13px}}.line{{font-size:12px;text-align:center}}.odds{{display:block;padding:8px 3px;text-align:center;font:bold 17px Arial;background:var(--primary);color:white;border-radius:7px}}
.state{{font-size:10px;text-align:center}}.bottom{{position:fixed;bottom:22px;left:0;right:0;background:var(--card);border-top:1px solid #8899aa44;display:flex;justify-content:space-around;padding:15px 6px}}
.bottom a{{color:var(--ink);text-decoration:none;font-size:12px}}.bottom a:first-child{{color:var(--primary);font-weight:bold}}
.home{{position:fixed;bottom:8px;left:calc(50% - 50px);width:100px;height:5px;background:var(--ink);border-radius:8px}}
a:focus-visible{{outline:2px solid var(--primary);outline-offset:4px}}
</style><div class="screen"><div class="statusbar"><span>9:41</span><span>5G · 100%</span></div>
<div class="brand">{_field("provider", "provider", provider_name)}<span class="format">Decimal odds</span></div>
<main id="markets"><div class="updated">{_field("quote_time", "updated", "Updated " + _display_time(first["quote_time"]))}</div>
<section class="event"><div class="event-code">{_field("event", "event-code", "Event " + first["event_id"])}</div>
<div class="participants">{_field("participant", "away", first["away"])}<i>@</i>{_field("participant", "home", first["home"])}</div>
<div class="start">{_field("event_time", "start", "Start " + _display_time(first["start_time"]))}</div></section>
{''.join(cards)}</main></div><nav class="bottom">{navigation}</nav><div class="home"></div></html>'''
