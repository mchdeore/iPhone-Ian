"""Trusted software executor. Red receives committed PNGs and sends coordinates only.

This engine is synchronous and belongs in a supervised worker, not an actor process.
It never controls a phone or motor. Durable server ownership is a separate layer.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import re
import secrets
import threading
import time
from pathlib import Path

from playwright.sync_api import Error as BrowserError
from playwright.sync_api import sync_playwright

from ..benchmark import Refusal
from ..blue import score_contacts
from .arena import _hash, _text
from .behavior import _now, frozen_scorer
from .dataset import _inside, audit_dataset
from .storage import encoded

ACTION_FIELDS = {'request_id', 'frame_id', 'image_sha256', 'kind', 'points', 'duration_ms'}
TABS = ('sports', 'live', 'bets', 'account')
VIEWPORT = {'width': 390, 'height': 844}
CONTENT_POLICY = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"

# Binding exports only trusted contacts. Navigation waits until contacts reach the
# executor, so a document change cannot discard its final pointer-up observation.
CONTACT_SCRIPT = """(()=>{
const active=new Map();window.__contactChain=Promise.resolve();window.__violationChain=Promise.resolve();
document.addEventListener('securitypolicyviolation',e=>{
 if(e.effectiveDirective==='connect-src')window.__violationChain=window.__violationChain.then(()=>window.__ownedViolation());
});
function record(e){
 if(!e.isTrusted)return;
 const kind={pointerdown:'down',pointermove:'move',pointerup:'up',pointercancel:'cancel'}[e.type];
 if(kind==='down'){let slot=0;while([...active.values()].includes(slot))slot++;active.set(e.pointerId,slot)}
 if(!active.has(e.pointerId))return;
 const event={kind,time_ms:performance.timeOrigin+e.timeStamp,x:e.clientX,y:e.clientY,pointer:active.get(e.pointerId)};
 window.__contactChain=window.__contactChain.then(()=>window.__ownedContact(event));
 if(kind==='up'||kind==='cancel')active.delete(e.pointerId);
}
for(const type of ['pointerdown','pointermove','pointerup','pointercancel'])document.addEventListener(type,record,true);
document.addEventListener('click',e=>{
 const link=e.target.closest('a');if(!link)return;
 e.preventDefault();const destination=link.href;
 window.__contactChain.then(()=>location.assign(destination));
},true);
})();"""


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sources():
    root = Path(__file__).parents[1]
    names = ('__init__.py', 'training-policy.json', 'sportsbook/pixel_browser.py', 'sportsbook/pixel_cli.py', 'sportsbook/pages.py', 'sportsbook/fixtures.py',
             'sportsbook/contracts.py', 'sportsbook/dataset.py', 'sportsbook/behavior.py',
             'sportsbook/storage.py', 'sportsbook/arena.py', 'blue.py', 'benchmark.py', 'metrics.py')
    return {name: _digest(root / name) for name in names}


def validate_action(request):
    if not isinstance(request, dict) or set(request) != ACTION_FIELDS:
        raise Refusal('exact coordinate action fields required')
    _text(request['request_id'])
    _hash(request['frame_id'])
    _hash(request['image_sha256'])
    kind, points, duration = request['kind'], request['points'], request['duration_ms']
    if kind not in ('tap', 'swipe', 'wait'):
        raise Refusal('only tap, swipe and wait coordinate actions are supported')
    if type(duration) is not int or not 0 <= duration <= 2000:
        raise Refusal('action duration budget')
    if not isinstance(points, list) or len(points) != {'tap': 1, 'swipe': 2, 'wait': 0}[kind]:
        raise Refusal('typed coordinate action points required')
    if kind == 'swipe' and not 16 <= duration <= 1000:
        raise Refusal('swipe duration budget')
    for point in points:
        if not isinstance(point, dict) or set(point) != {'x', 'y'}:
            raise Refusal('coordinate fields required')
        for key, bound in [('x', 390), ('y', 844)]:
            value = point[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value < bound:
                raise Refusal('finite coordinates inside the committed viewport required')
    return request


class PixelBrowser:
    def __init__(self, root, sample_id, output, browser_path, browser_sha256, *, actor_id,
                 max_actions=64, runtime_seconds=120, max_bytes=64 * 1024 * 1024):
        self.root, self.output, self.browser_path = Path(root), Path(output), Path(browser_path)
        _text(actor_id)
        _hash(browser_sha256)
        if (not self.browser_path.is_absolute() or not self.browser_path.is_file()
                or _digest(self.browser_path) != browser_sha256):
            raise Refusal('configured browser executable digest mismatch or unavailable')
        if self.output.exists() or self.output.is_symlink():
            raise Refusal('session output exists; preserve prior artifacts and choose a fresh directory')
        if any(parent.is_symlink() for parent in self.output.parents):
            raise Refusal('session output symlink parent refused')
        if (type(max_actions) is not int or not 1 <= max_actions <= 128
                or type(runtime_seconds) not in (int, float) or not math.isfinite(runtime_seconds)
                or not 0 < runtime_seconds <= 120
                or type(max_bytes) is not int or not 1024 <= max_bytes <= 64 * 1024 * 1024):
            raise Refusal('session execution budget configuration')
        audit_dataset(self.root)
        self._manifest_sha = _digest(self.root / 'dataset.json')
        manifest = json.loads((self.root / 'dataset.json').read_text())
        selected = next((row for row in manifest['samples'] if row['sample_id'] == sample_id), None)
        if selected is None:
            raise Refusal('frozen dataset sample required')
        group = [row for row in manifest['samples'] if row['sequence_group'] == selected['sequence_group']]
        if len(group) != 3 or {row['tags']['phase'] for row in group} != {0, 1, 2}:
            raise Refusal('complete frozen three-phase provider sequence required')
        if sum(_inside(self.root, row[key]).stat().st_size for row in group
               for key in ('source_page', 'provider_truth')) > max_bytes:
            raise Refusal('frozen provider input byte budget')
        self.session_id, self.actor_id = secrets.token_hex(16), actor_id
        self._phase = selected['tags']['phase']
        self._sources, self._policy = _sources(), frozen_scorer()
        self._browser_sha = browser_sha256
        self._max_actions, self._runtime_seconds, self._max_bytes = max_actions, runtime_seconds, max_bytes
        self._contacts, self._frames, self._cache = [], {}, {}
        self._blocked_requests, self._action_count, self._frame_seq, self._state_seq = 0, 0, 0, 0
        self._started, self._state = None, 'prepared'
        self._owner = None
        self._pw = self._browser = self._context = self._page = None
        self._base = f'https://phone.invalid/owned/{self.session_id}'
        self.output.mkdir(parents=True, mode=0o700)
        self._pages, self._truth = {}, {}
        for row in sorted(group, key=lambda value: value['tags']['phase']):
            phase = row['tags']['phase']
            payloads = {}
            for key in ('source_page', 'provider_truth'):
                path = _inside(self.root, row[key])
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != row['sha256'][key]:
                    raise Refusal('frozen provider source changed; partial copy retained')
                payloads[key] = data
                self._write(f'blue-private/frozen/{phase}-{key}', data)
            self._truth[phase] = json.loads(payloads['provider_truth'])
            for tab in TABS:
                self._pages[f'{self._base}/{phase}/{tab}'] = self._html(payloads['source_page'].decode(), phase, tab)
        self._write_json('blue-private/config.json', {
            'schema': 'owned-pixel-browser/1', 'session_id': self.session_id, 'actor_id': actor_id,
            'dataset_sha256': self._manifest_sha, 'sample_id': sample_id, 'source_fingerprints': self._sources,
            'browser_sha256': browser_sha256, 'playwright_version': importlib.metadata.version('playwright'),
            'blue_policy': self._policy, 'viewport': VIEWPORT, 'runtime_seconds': runtime_seconds,
            'max_actions': max_actions, 'max_bytes': max_bytes, 'training': 'held',
            'boundary': 'trusted software executor; PNG/coordinate actor interface; no physical control',
        })
        self._set_state('prepared')

    def _write(self, relative, data):
        path = self.output / relative
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open('xb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

    def _write_json(self, relative, value):
        self._write(relative, (encoded(value) + '\n').encode())

    def _set_state(self, state):
        self._state = state
        self._state_seq += 1
        value = {'schema': 'owned-pixel-browser-state/1', 'session_id': self.session_id,
                 'actor_id': self.actor_id, 'state': state, 'at': _now(), 'actions': self._action_count,
                 'frames': self._frame_seq, 'blocked_requests': self._blocked_requests}
        name = f'blue-private/states/{self._state_seq:04d}.json'
        self._write_json(name, value)
        temporary = self.output / f'.state-{self._state_seq}.json'
        with temporary.open('xb') as handle:
            handle.write((encoded(value) + '\n').encode())
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(self.output / 'state.json')

    def _html(self, html, phase, tab):
        count = 0
        def navigation(match):
            nonlocal count
            target = TABS[count]
            count += 1
            return match.group(0).replace('href="#markets"', f'href="{self._base}/{phase}/{target}" class="{ "current" if target == tab else "" }"')
        html = re.sub(r'<a href="#markets">.*?</a>', navigation, html)
        if count != 4 or '</html>' not in html:
            raise Refusal('unsupported frozen provider navigation source')
        if tab in ('account', 'bets'):
            content = ('<h2>Fictional account</h2><p>Local demo profile. No real account or payment connection.</p>'
                       if tab == 'account' else '<h2>Fictional bets</h2><p>No selections saved. This demo places no bets.</p>')
            html = re.sub(r'<main id="markets">.*?</main>', '<main id="markets"><section class="event">' + content + '</section></main>', html, flags=re.S)
        elif tab == 'live':
            html = html.replace('<main id="markets">', '<main id="markets"><p>Synthetic live view</p>', 1)
        style = '<style>.bottom a{font-weight:normal;color:var(--ink)}.bottom a.current{font-weight:bold;color:var(--primary)}#refresh{position:fixed;bottom:100px;left:18px;padding:10px 14px;border-radius:10px;background:var(--card);color:var(--ink);border:1px solid #8899aa77;text-decoration:none;font:14px Arial}</style>'
        refresh = (f'<a id="refresh" data-role="navigation" data-label="refresh" href="{self._base}/{phase + 1}/{tab}">Refresh fictional prices</a>'
                   if phase < 2 else '<span id="refresh">Prices current</span>') if tab in ('sports', 'live') else ''
        return html.replace('</html>', style + refresh + '</html>', 1)

    def _serve(self, route):
        request = route.request
        if request.method == 'GET' and request.url in self._pages:
            route.fulfill(status=200, content_type='text/html; charset=utf-8', body=self._pages[request.url],
                          headers={'Cache-Control': 'no-store', 'Content-Security-Policy': CONTENT_POLICY})
        else:
            self._blocked_requests += 1
            route.abort('blockedbyclient')

    def _record_contact(self, _source, event):
        if not isinstance(event, dict) or set(event) != {'kind', 'time_ms', 'x', 'y', 'pointer'}:
            raise Refusal('provider contact boundary')
        if len(self._contacts) >= 5000:
            raise Refusal('provider contact budget')
        with (self.output / 'blue-private/contact-events.jsonl').open('ab') as handle:
            handle.write((encoded(event) + '\n').encode())
            handle.flush()
            os.fsync(handle.fileno())
        self._contacts.append(event)

    def _connection_violation(self, _source):
        self._blocked_requests += 1

    def __enter__(self):
        if self._state != 'prepared':
            raise Refusal('browser session cannot reopen; start a fresh session')
        self._owner = threading.get_ident()
        try:
            self._check_sources()
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(executable_path=str(self.browser_path), headless=True, timeout=15000)
            self._context = self._browser.new_context(viewport=VIEWPORT, device_scale_factor=1,
                                                     locale='en-US', timezone_id='UTC', service_workers='block')
            self._context.route('**/*', self._serve)
            self._context.expose_binding('__ownedContact', self._record_contact)
            self._context.expose_binding('__ownedViolation', self._connection_violation)
            self._context.add_init_script(CONTACT_SCRIPT)
            self._page = self._context.new_page()
            self._page.set_default_timeout(5000)
            self._page.goto(f'{self._base}/{self._phase}/sports', wait_until='load')
            self._write_json('blue-private/renderer.json', {
                'browser_version': self._browser.version, 'viewport': VIEWPORT,
                'device_scale_factor': 1, 'locale': 'en-US', 'timezone': 'UTC',
                'network': 'owned in-memory documents only; browser connect-src none; unmatched navigation routes aborted',
                'content_security_policy': CONTENT_POLICY,
            })
            self._capture()
            self._started = time.monotonic()
            self._set_state('open')
            return self
        except Exception as error:
            self._interrupt(error)
            self._teardown()
            raise Refusal('browser startup interrupted; original artifacts retained') from error

    def _check_sources(self):
        try:
            changed = (_sources() != self._sources or frozen_scorer() != self._policy
                       or _digest(self.browser_path) != self._browser_sha
                       or _digest(self.root / 'dataset.json') != self._manifest_sha)
        except OSError:
            raise Refusal('frozen executor or dataset unavailable; no new action dispatched') from None
        if changed:
            raise Refusal('frozen executor or dataset changed; start a reviewed fresh session')

    def _require_owner(self):
        if self._owner != threading.get_ident():
            raise Refusal('coordinate executor requires its owning worker thread')

    def _budget(self, *, new_action=False):
        size = sum(path.stat().st_size for path in self.output.rglob('*') if path.is_file())
        if (size > self._max_bytes or (new_action and self._action_count >= self._max_actions)
                or (self._started is not None and time.monotonic() - self._started > self._runtime_seconds)):
            raise Refusal('session execution budget exceeded; no new action dispatched')

    def _settle(self):
        # A real navigation may replace the document while awaiting font/contact
        # readiness. Only that explicit context-change error is retried.
        for retry in range(3):
            try:
                self._page.wait_for_load_state('load')
                self._page.evaluate('async()=>{await document.fonts.ready;await window.__contactChain;await window.__violationChain;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}')
                break
            except BrowserError as error:
                if retry == 2 or 'Execution context was destroyed' not in str(error):
                    raise

    def _capture(self):
        self._settle()
        url = self._page.url
        if url not in self._pages:
            raise Refusal('browser left the owned application')
        phase, tab = url.rsplit('/', 2)[-2:]
        phase = int(phase)
        pixels = self._page.screenshot(type='png', animations='disabled')
        if pixels != self._page.screenshot(type='png', animations='disabled'):
            raise Refusal('fresh browser pixels were unstable')
        self._frame_seq += 1
        digest = hashlib.sha256(pixels).hexdigest()
        fid = hashlib.sha256(encoded([self.session_id, self._frame_seq, digest]).encode()).hexdigest()
        relative = f'red-pixels/{self._frame_seq:04d}.png'
        fields = self._page.locator('[data-label]').evaluate_all('''elements=>elements.map(el=>{const b=el.getBoundingClientRect();return {id:el.dataset.label,role:el.dataset.role,text:el.textContent.trim(),box:{x:b.x,y:b.y,width:b.width,height:b.height}}})''')
        self._write(relative, pixels)
        metadata = {'session_id': self.session_id, 'frame_id': fid, 'image_sha256': digest,
                    'image_file': relative, 'viewport': [390, 844]}
        self._write_json(f'blue-private/frames/{self._frame_seq:04d}.json', {
            'frame': metadata, 'at': _now(), 'phase': phase, 'tab': tab, 'fields': fields,
            'expected_quotes': self._truth[phase]['quotes'] if tab in ('sports', 'live') else [],
        })
        self._budget()
        self._frames[fid] = metadata
        self._latest = metadata
        return self.latest()

    def latest(self):
        if not self._frames:
            raise Refusal('no committed browser frame')
        return json.loads(encoded(self._latest))

    def pixels(self, frame_id):
        _hash(frame_id)
        frame = self._frames.get(frame_id)
        if frame is None:
            raise Refusal('unknown committed frame')
        data = _inside(self.output, frame['image_file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != frame['image_sha256']:
            raise Refusal('committed pixels changed; original evidence required')
        return data

    def _journal(self, value):
        with (self.output / 'actions.jsonl').open('ab') as handle:
            handle.write((encoded(dict(value, at=_now())) + '\n').encode())
            handle.flush()
            os.fsync(handle.fileno())

    def _interrupt(self, error):
        self._write_json(f'blue-private/failure-{self._state_seq + 1:04d}.json', {
            'type': type(error).__name__, 'reason': str(error), 'state': 'interrupted',
            'effect': 'dispatch or capture may be incomplete; do not re-execute the request', 'at': _now(),
        })
        self._set_state('interrupted')

    def action(self, request):
        self._require_owner()
        request = json.loads(encoded(validate_action(request)))
        raw = encoded(request)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        prior = self._cache.get(request['request_id'])
        if prior:
            if prior['sha256'] != digest:
                raise Refusal('conflicting coordinate action replay')
            self.pixels(prior['frame']['frame_id'])
            return json.loads(encoded(prior['frame']))
        if self._state != 'open':
            raise Refusal('browser session is not open; interrupted requests cannot re-execute')
        self._budget(new_action=True)
        self._check_sources()
        if (request['frame_id'] != self._latest['frame_id']
                or request['image_sha256'] != self._latest['image_sha256']):
            raise Refusal('stale frame or image commitment; no action dispatched')
        self.pixels(request['frame_id'])
        self._journal({'request': request, 'request_sha256': digest, 'state': 'reserved'})
        self._action_count += 1
        try:
            kind, points, duration = request['kind'], request['points'], request['duration_ms']
            if kind == 'wait':
                self._page.wait_for_timeout(duration)
            else:
                self._page.mouse.move(points[0]['x'], points[0]['y'])
                self._page.mouse.down()
                if kind == 'swipe':
                    steps = min(20, max(2, duration // 16))
                    for step in range(1, steps + 1):
                        fraction = step / steps
                        self._page.mouse.move(points[0]['x'] + (points[1]['x'] - points[0]['x']) * fraction,
                                              points[0]['y'] + (points[1]['y'] - points[0]['y']) * fraction)
                        self._page.wait_for_timeout(duration / steps)
                elif duration:
                    self._page.wait_for_timeout(duration)
                self._page.mouse.up()
            self._settle()
            frame = self._capture()
            self._journal({'request_id': request['request_id'], 'request_sha256': digest, 'state': 'committed', 'frame': frame})
            self._cache[request['request_id']] = {'sha256': digest, 'frame': frame}
            self._set_state('open')
            return frame
        except Exception as error:
            self._journal({'request_id': request['request_id'], 'request_sha256': digest, 'state': 'interrupted'})
            self._interrupt(error)
            raise Refusal('coordinate action interrupted; original evidence retained; start a fresh session') from error

    def finish(self):
        self._require_owner()
        if self._state == 'closed':
            return {'session_id': self.session_id, 'state': 'closed'}
        if self._state != 'open':
            raise Refusal('only an open session can save provider contacts')
        self._check_sources()
        self._budget()
        packet = {'schema': 'website-contact-session/1', 'run_id': self.session_id,
                  'viewport': [390, 844], 'events': self._contacts}
        self._write_json('blue-private/contacts.json', packet)
        try:
            score = score_contacts(packet)
            self._write_json('blue-private/score.json', score)
            self._set_state('closed')
        except Exception as error:
            self._interrupt(error)
            raise Refusal('provider scoring interrupted; contact evidence retained') from error
        finally:
            self._teardown()
        return {'session_id': self.session_id, 'state': 'closed'}

    def _teardown(self):
        try:
            if self._browser is not None:
                self._browser.close()
        finally:
            if self._pw is not None:
                self._pw.stop()
            self._page = self._context = self._browser = self._pw = None

    def close(self):
        if self._owner is not None:
            self._require_owner()
        if self._state in ('prepared', 'open'):
            self._set_state('cancelled')
        self._teardown()

    def __exit__(self, *_exc):
        self.close()
