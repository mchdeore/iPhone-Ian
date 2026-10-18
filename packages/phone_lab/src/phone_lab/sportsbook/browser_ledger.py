"""Trusted durable browser evidence; Red receives pixels and commit receipts only.

This ledger does not launch, recover or authenticate a browser worker. Its caller
must own the executor and expose only the public methods to its actor.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from PIL import Image

from ..benchmark import Refusal
from .arena import _hash, _text
from .behavior import _now
from .contracts import quote_key, validate_quote
from .dataset import _inside
from .evaluation import SPORTS_ROLES, _objects, confusion_report, finite, merge_confusions
from .extract import ocr_regions
from .pixel_browser import validate_action
from .reports import operation_registry, score_ocr_fields
from .storage import QuoteStore, encoded, identity, score_database

SCHEMA = 'owned-browser-ledger/1'
APPLICATION_ID = 0x42524C31
ATTEMPT_FIELDS = {'attempt_id', 'frame_id', 'image_sha256', 'actor_id', 'model_sha256',
                  'parser_version', 'latency_ms', 'quotes', 'refusals', 'retry_of',
                  'recognized', 'fields', 'objects'}
TABLES = {
    'ledger_meta': {'key', 'value'},
    'sessions': {'session_id', 'actor_id', 'engine_path', 'config', 'policy', 'spec_sha256', 'state', 'created_at'},
    'frames': {'seq', 'session_id', 'frame_id', 'image_sha256', 'payload', 'payload_sha256'},
}


def scorer_policy():
    root = Path(__file__).parents[1]
    names = ('__init__.py', 'training-policy.json', 'benchmark.py', 'sportsbook/arena.py',
             'sportsbook/behavior.py', 'sportsbook/browser_ledger.py', 'sportsbook/pixel_browser.py',
             'sportsbook/reports.py', 'sportsbook/evaluation.py', 'sportsbook/extract.py',
             'sportsbook/storage.py', 'sportsbook/contracts.py', 'sportsbook/dataset.py')
    return {'schema': 'browser-observation-scorer/1', 'version': 'committed-per-actor/1',
            'components': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names},
            'training': 'held', 'registry': operation_registry()}


def _sid(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{32}', value):
        raise Refusal('opaque browser session required')
    return value


def _read(root, relative, limit=262144):
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise Refusal('evidence root symlink refused')
    path = _inside(root, relative)
    if not path.is_file() or path.stat().st_size > limit:
        raise Refusal('bounded owned evidence file required')
    data = path.read_bytes()
    if len(data) > limit:
        raise Refusal('evidence byte budget exceeded')
    return data


def _json(root, relative, limit=262144):
    try:
        return json.loads(_read(root, relative, limit))
    except (ValueError, UnicodeError):
        raise Refusal('owned JSON evidence required') from None


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _boxes(values, *, text=False, truth=False):
    if not isinstance(values, list) or len(values) > 1000:
        raise Refusal('bounded visible objects required')
    required = {'id', 'role', 'box'} | ({'text'} if text else set())
    required |= {'text_box'} if truth else {'confidence'}
    if any(not isinstance(v, dict) or set(v) != required for v in values):
        raise Refusal('exact visible object fields required')
    normalized = _objects(values, SPORTS_ROLES, 'visible')
    if len({v['id'] for v in normalized}) != len(normalized):
        raise Refusal('unique visible object identifiers required')
    for value, box in zip(values, normalized):
        _viewport(box['box'])
        if text:
            value_text = value['text']
            if not isinstance(value_text, str) or not 1 <= len(value_text) <= 1000 or not value_text.isprintable():
                raise Refusal('bounded visible text required')
        if truth:
            _viewport(_objects([dict(value, box=value['text_box'])], SPORTS_ROLES, 'text')[0]['box'])
    return values


def _viewport(box):
    if box['x'] + box['width'] > 390 or box['y'] + box['height'] > 844:
        raise Refusal('observation box outside viewport')


def _attempt(payload):
    if not isinstance(payload, dict) or set(payload) != ATTEMPT_FIELDS:
        raise Refusal('exact browser observation fields required')
    for key in ('attempt_id', 'actor_id', 'parser_version'):
        _text(payload[key])
    for key in ('frame_id', 'image_sha256'):
        _hash(payload[key])
    if payload['model_sha256'] is not None:
        _hash(payload['model_sha256'])
    if payload['retry_of'] is not None:
        _text(payload['retry_of'])
    finite(payload['latency_ms'], 0, 600000, 'observation latency')
    if not isinstance(payload['quotes'], list) or len(payload['quotes']) > 1000:
        raise Refusal('bounded quote batch required')
    # Semantic quote failures are committed as refusals by the atomic ingester.
    if not isinstance(payload['refusals'], list) or len(payload['refusals']) > 100:
        raise Refusal('bounded operation refusals required')
    for value in payload['refusals']:
        if (not isinstance(value, dict) or set(value) != {'operation', 'reason'}
                or not isinstance(value['operation'], str) or value['operation'] not in operation_registry()):
            raise Refusal('typed operation refusal required')
        _text(value['reason'], 500)
    if payload['recognized'] is not None:
        for row in ocr_regions(payload['recognized']):
            _viewport(row['box'])
    if payload['fields'] is not None:
        _boxes(payload['fields'], text=True)
    if payload['objects'] is not None:
        if payload['model_sha256'] is None:
            raise Refusal('detector output requires a model commitment')
        _boxes(payload['objects'])
    try:
        raw = encoded(payload)
    except (ValueError, TypeError):
        raise Refusal('JSON observation required') from None
    if len(raw.encode()) > 262144:
        raise Refusal('observation byte budget exceeded')
    return json.loads(raw), raw


class _SavedRows:
    def __init__(self, rows):
        self.rows = rows

    def latest(self):
        return [validate_quote(q) for q in self.rows]


class BrowserLedger:
    """One separate observation database per actor-bound browser session."""

    def __init__(self, root):
        root = Path(root).absolute()
        if root.is_symlink() or any(p.is_symlink() for p in root.parents):
            raise Refusal('ledger root symlink refused')
        self.root = root
        self.path = root / 'sessions.sqlite'
        if self.path.is_symlink():
            raise Refusal('ledger database symlink refused')
        new = not self.path.exists()
        if not new:
            try:
                with self._db(readonly=True) as db:
                    if db.execute('PRAGMA application_id').fetchone()[0] != APPLICATION_ID or db.execute('PRAGMA user_version').fetchone()[0] != 1:
                        raise Refusal('foreign ledger database retained unchanged')
                    if dict(db.execute('SELECT key,value FROM ledger_meta')).get('schema') != SCHEMA:
                        raise Refusal('foreign ledger database retained unchanged')
                    if any({r[1] for r in db.execute(f'PRAGMA table_info({table})')} != columns for table, columns in TABLES.items()):
                        raise Refusal('foreign ledger tables retained unchanged')
            except sqlite3.Error:
                raise Refusal('foreign ledger database retained unchanged') from None
        else:
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
            _write(self.path, b'')
            with self._db() as db:
                db.executescript(f'''BEGIN IMMEDIATE;
PRAGMA application_id={APPLICATION_ID}; PRAGMA user_version=1;
CREATE TABLE ledger_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT INTO ledger_meta VALUES('schema','{SCHEMA}');
CREATE TABLE sessions(session_id TEXT PRIMARY KEY,actor_id TEXT NOT NULL,engine_path TEXT NOT NULL,
config TEXT NOT NULL,policy TEXT NOT NULL,spec_sha256 TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE frames(seq INTEGER NOT NULL,session_id TEXT NOT NULL REFERENCES sessions(session_id),
frame_id TEXT UNIQUE NOT NULL,image_sha256 TEXT NOT NULL,payload TEXT NOT NULL,payload_sha256 TEXT NOT NULL,
PRIMARY KEY(session_id,seq)); COMMIT;''')

    @contextmanager
    def _db(self, *, readonly=False):
        if self.root.is_symlink() or any(p.is_symlink() for p in self.root.parents) or self.path.is_symlink():
            raise Refusal('ledger database symlink refused')
        db = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=5) if readonly else sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        if not readonly:
            db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def _session(self, db, sid):
        row = db.execute('SELECT * FROM sessions WHERE session_id=?', (_sid(sid),)).fetchone()
        if row is None:
            raise Refusal('unknown browser session')
        if identity({'config': json.loads(row['config']), 'policy': json.loads(row['policy'])}) != row['spec_sha256']:
            raise Refusal('session commitment changed')
        return row

    def _run(self, sid):
        return _inside(self.root, f'runs/{_sid(sid)}')

    @contextmanager
    def _actor(self, row):
        path = _inside(self.root, f'runs/{row["session_id"]}/actor.sqlite')
        if not path.is_file():
            raise Refusal('committed actor database unavailable')
        store = QuoteStore(path)
        store.db.row_factory = sqlite3.Row
        store.db.execute('PRAGMA synchronous=FULL')
        try:
            meta = dict(store.db.execute('SELECT key,value FROM browser_meta'))
            if meta != {'schema': SCHEMA, 'session_id': row['session_id'], 'actor_id': row['actor_id'], 'spec_sha256': row['spec_sha256']}:
                raise Refusal('actor database commitment changed')
            yield store
        except sqlite3.Error:
            raise Refusal('actor database schema unavailable; original retained') from None
        finally:
            store.close()

    def attach(self, engine_output):
        """Operator-only import of a known, already-owned executor directory."""
        source = Path(engine_output).absolute()
        if source.is_symlink() or any(p.is_symlink() for p in source.parents):
            raise Refusal('executor symlink refused')
        config = _json(source, 'blue-private/config.json', 65536)
        if not isinstance(config, dict) or config.get('schema') != 'owned-pixel-browser/1' or config.get('training') != 'held' or config.get('viewport') != {'width': 390, 'height': 844}:
            raise Refusal('owned held-training pixel executor required')
        sid, actor = _sid(config.get('session_id')), _text(config.get('actor_id'))
        policy = scorer_policy()
        spec = identity({'config': config, 'policy': policy})
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT * FROM sessions WHERE session_id=?', (sid,)).fetchone()
            if prior:
                if prior['config'] != encoded(config) or prior['engine_path'] != str(source):
                    raise Refusal('conflicting executor session replay')
            else:
                if db.execute("SELECT COUNT(*) FROM sessions WHERE state IN ('prepared','open')").fetchone()[0] >= 16:
                    raise Refusal('open session budget exceeded')
                path = _inside(self.root, f'runs/{sid}/actor.sqlite')
                if path.exists():
                    raise Refusal('partial session artifacts retained; use a fresh executor session')
                store = QuoteStore(path)
                try:
                    with store.db:
                        store.db.execute('CREATE TABLE browser_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
                        store.db.executemany('INSERT INTO browser_meta VALUES (?,?)', [('schema', SCHEMA), ('session_id', sid), ('actor_id', actor), ('spec_sha256', spec)])
                        store.db.execute('CREATE TABLE browser_attempts(seq INTEGER PRIMARY KEY,attempt_id TEXT UNIQUE NOT NULL,frame_id TEXT NOT NULL,payload TEXT NOT NULL,payload_sha256 TEXT NOT NULL,result TEXT NOT NULL,stored_rows TEXT NOT NULL,receipt_sha256 TEXT NOT NULL,created_at TEXT NOT NULL)')
                        store.db.execute('CREATE TABLE browser_evaluations(snapshot_sha256 TEXT PRIMARY KEY,report TEXT NOT NULL,report_sha256 TEXT NOT NULL,created_at TEXT NOT NULL)')
                finally:
                    store.close()
                db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)', (sid, actor, str(source), encoded(config), encoded(policy), spec, 'prepared', _now()))
        self.sync(sid)
        return self.session(sid)

    def _evidence(self, source, metadata, seq):
        fields = _boxes(metadata['fields'], text=True, truth=True)
        quotes = [validate_quote(q) for q in metadata['expected_quotes']]
        if len(quotes) > 1000 or len({quote_key(q) for q in quotes}) != len(quotes):
            raise Refusal('bounded unique expected records required')
        count = metadata['contact_count']
        if type(count) is not int or not 0 <= count <= 5000:
            raise Refusal('contact count budget exceeded')
        contacts = []
        if count:
            lines = _read(source, 'blue-private/contact-events.jsonl', 2 * 1024 * 1024).splitlines()
            if len(lines) < count:
                raise Refusal('committed contact prefix unavailable')
            contacts = [json.loads(line) for line in lines[:count]]
            for contact in contacts:
                if (not isinstance(contact, dict) or set(contact) != {'kind', 'time_ms', 'x', 'y', 'pointer'}
                        or contact['kind'] not in {'down', 'move', 'up', 'cancel'}
                        or type(contact['pointer']) is not int or not 0 <= contact['pointer'] <= 9):
                    raise Refusal('coordinate-only contact evidence required')
                finite(contact['time_ms'], 0, 1e16, 'contact time')
                finite(contact['x'], 0, 390, 'contact x')
                finite(contact['y'], 0, 844, 'contact y')
        action = None
        if seq > 1:
            entries = [json.loads(line) for line in _read(source, 'actions.jsonl', 2 * 1024 * 1024).splitlines()]
            committed = [e for e in entries if e.get('state') == 'committed' and e.get('frame') == metadata['frame']]
            if len(committed) != 1:
                raise Refusal('frame action commitment unavailable')
            commit = committed[0]
            reserved = [e for e in entries if e.get('state') == 'reserved' and e.get('request_sha256') == commit['request_sha256']]
            if len(reserved) != 1 or identity(reserved[0]['request']) != commit['request_sha256'] or reserved[0]['request']['request_id'] != commit['request_id']:
                raise Refusal('reserved action commitment changed')
            action = json.loads(encoded(validate_action(reserved[0]['request'])))
        return {'executor_metadata': metadata, 'truth_fields': fields, 'expected_quotes': quotes,
                'contacts': contacts, 'action': action}

    def sync(self, sid):
        """Operator-only capture commit. Never infer worker death from an old state."""
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._session(db, sid)
            source = Path(row['engine_path'])
            if encoded(_json(source, 'blue-private/config.json', 65536)) != row['config']:
                raise Refusal('frozen executor configuration changed')
            folder = _inside(source, 'blue-private/frames')
            paths = sorted(folder.glob('*.json'))
            if len(paths) > 129 or [p.name for p in paths] != [f'{i:04d}.json' for i in range(1, len(paths) + 1)]:
                raise Refusal('bounded contiguous executor frames required')
            for seq, path in enumerate(paths, 1):
                metadata = _json(source, f'blue-private/frames/{path.name}')
                frame = metadata['frame']
                if (set(frame) != {'session_id', 'frame_id', 'image_sha256', 'image_file', 'viewport'}
                        or frame['session_id'] != sid or frame['viewport'] != [390, 844]
                        or frame['image_file'] != f'red-pixels/{seq:04d}.png'):
                    raise Refusal('exact executor frame commitment required')
                fid, digest = _hash(frame['frame_id']), _hash(frame['image_sha256'])
                if identity([sid, seq, digest]) != fid:
                    raise Refusal('frame sequence commitment changed')
                payload = self._evidence(source, metadata, seq)
                if seq > 1:
                    previous = db.execute('SELECT frame_id,image_sha256 FROM frames WHERE session_id=? AND seq=?', (sid, seq - 1)).fetchone()
                    if previous is None or payload['action']['frame_id'] != previous['frame_id'] or payload['action']['image_sha256'] != previous['image_sha256']:
                        raise Refusal('action does not reference the preceding committed frame')
                raw, pin = encoded(payload), identity(payload)
                if len(raw.encode()) > 2 * 1024 * 1024:
                    raise Refusal('frame evidence byte budget exceeded')
                prior = db.execute('SELECT * FROM frames WHERE session_id=? AND seq=?', (sid, seq)).fetchone()
                if prior:
                    if prior['payload_sha256'] != pin or prior['frame_id'] != fid:
                        raise Refusal('conflicting frozen frame replay')
                    continue
                png = _read(source, frame['image_file'], 2 * 1024 * 1024)
                if hashlib.sha256(png).hexdigest() != digest:
                    raise Refusal('executor pixel commitment mismatch')
                with Image.open(io.BytesIO(png)) as image:
                    if image.format != 'PNG' or image.size != (390, 844):
                        raise Refusal('owned PNG viewport required')
                    image.verify()
                target = _inside(self.root, f'runs/{sid}/pixels/{fid}.png')
                if target.exists():
                    if _read(self.root, str(target.relative_to(self.root)), 2 * 1024 * 1024) != png:
                        raise Refusal('partial pixel evidence differs; original retained')
                else:
                    _write(target, png)
                db.execute('INSERT INTO frames VALUES (?,?,?,?,?,?)', (seq, sid, fid, digest, raw, pin))
            state = _json(source, 'state.json', 65536)
            if state.get('session_id') != sid or state.get('actor_id') != row['actor_id'] or state.get('state') not in {'prepared', 'open', 'closed', 'cancelled', 'interrupted'}:
                raise Refusal('owned executor state required')
            if row['state'] in {'closed', 'cancelled', 'interrupted'} and state['state'] != row['state']:
                raise Refusal('terminal executor state cannot reopen')
            db.execute('UPDATE sessions SET state=? WHERE session_id=?', (state['state'], sid))
        return self.session(sid)

    def _frame(self, db, sid, fid):
        row = db.execute('SELECT * FROM frames WHERE session_id=? AND frame_id=?', (_sid(sid), _hash(fid))).fetchone()
        if row is None:
            raise Refusal('unknown committed browser frame')
        if identity(json.loads(row['payload'])) != row['payload_sha256']:
            raise Refusal('frame evidence commitment changed')
        original = json.loads(row['payload'])['executor_metadata']['frame']
        if original['session_id'] != sid or original['frame_id'] != fid or original['image_sha256'] != row['image_sha256'] or identity([sid, row['seq'], row['image_sha256']]) != fid:
            raise Refusal('frame columns differ from commitment')
        return row

    @staticmethod
    def _public_frame(row):
        return {'session_id': row['session_id'], 'frame_id': row['frame_id'],
                'image_sha256': row['image_sha256'], 'viewport': [390, 844],
                'image_file': f'pixels/{row["frame_id"]}.png'}

    def frame(self, sid, fid):
        with self._db(readonly=True) as db:
            self._session(db, sid)
            return self._public_frame(self._frame(db, sid, fid))

    def pixels(self, sid, fid):
        frame = self.frame(sid, fid)
        data = _read(self.root, f'runs/{sid}/{frame["image_file"]}', 2 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != frame['image_sha256']:
            raise Refusal('saved pixel commitment changed')
        return data

    def session(self, sid):
        with self._db(readonly=True) as db:
            row = self._session(db, sid)
            frame = db.execute('SELECT * FROM frames WHERE session_id=? ORDER BY seq DESC LIMIT 1', (sid,)).fetchone()
            with self._actor(row) as store:
                attempts = store.db.execute('SELECT COUNT(*) FROM browser_attempts').fetchone()[0]
            return {'session_id': sid, 'actor_id': row['actor_id'], 'state': row['state'],
                    'frames': db.execute('SELECT COUNT(*) FROM frames WHERE session_id=?', (sid,)).fetchone()[0],
                    'attempts': attempts, 'latest': self.frame(sid, frame['frame_id']) if frame else None}

    def submit(self, sid, payload):
        payload, raw = _attempt(payload)
        with self._db() as ledger:
            ledger.execute('BEGIN IMMEDIATE')
            row = self._session(ledger, sid)
            if payload['actor_id'] != row['actor_id']:
                raise Refusal('observation actor differs from session owner')
            frame = self._frame(ledger, sid, payload['frame_id'])
            if payload['image_sha256'] != frame['image_sha256']:
                raise Refusal('observation image commitment mismatch')
            self.pixels(sid, payload['frame_id'])
            with self._actor(row) as store, store.db:
                db = store.db
                db.execute('BEGIN IMMEDIATE')
                digest = identity(payload)
                prior = db.execute('SELECT * FROM browser_attempts WHERE attempt_id=?', (payload['attempt_id'],)).fetchone()
                if prior:
                    self._committed(prior)
                    if prior['payload_sha256'] != digest:
                        raise Refusal('conflicting observation replay')
                    result = json.loads(prior['result'])
                    result.pop('reason')
                    return dict(result, replayed=True)
                if db.execute('SELECT COUNT(*) FROM browser_attempts').fetchone()[0] >= 256 or store.path.stat().st_size + len(raw.encode()) > 128 * 1024 * 1024:
                    raise Refusal('session observation budget exceeded')
                if payload['retry_of'] is not None:
                    prior = db.execute('SELECT frame_id FROM browser_attempts WHERE attempt_id=?', (payload['retry_of'],)).fetchone()
                    if prior is None or prior[0] != payload['frame_id']:
                        raise Refusal('retry must reference this actor and frame')
                elif db.execute('SELECT 1 FROM browser_attempts WHERE frame_id=?', (payload['frame_id'],)).fetchone():
                    raise Refusal('another observation requires explicit retry')
                result = {'attempt_id': payload['attempt_id'], 'status': 'refused' if payload['refusals'] else 'empty', 'ingest': None, 'replayed': False}
                reason = None
                if payload['quotes']:
                    db.execute('SAVEPOINT quote_batch')
                    try:
                        result['ingest'] = store._ingest(identity([sid, payload['attempt_id']]), payload['quotes'],
                                                         model_sha256=payload['model_sha256'], parser_version=payload['parser_version'])
                        result['status'] = 'partial' if payload['refusals'] else 'accepted'
                    except (Refusal, ValueError, TypeError) as error:
                        db.execute('ROLLBACK TO quote_batch')
                        result['status'], reason = 'refused', str(error) if isinstance(error, Refusal) else 'malformed typed quote'
                    finally:
                        db.execute('RELEASE quote_batch')
                # Private error and actual DB rows are part of the same commit.
                saved_result = dict(result, reason=reason)
                rows = store.latest()
                receipt = identity({'payload': payload, 'result': saved_result, 'stored_rows': rows})
                db.execute('INSERT INTO browser_attempts(attempt_id,frame_id,payload,payload_sha256,result,stored_rows,receipt_sha256,created_at) VALUES (?,?,?,?,?,?,?,?)',
                           (payload['attempt_id'], payload['frame_id'], raw, digest, encoded(saved_result), encoded(rows), receipt, _now()))
        return result

    @staticmethod
    def _committed(row):
        payload, result, rows = (json.loads(row[key]) for key in ('payload', 'result', 'stored_rows'))
        if identity(payload) != row['payload_sha256'] or identity({'payload': payload, 'result': result, 'stored_rows': rows}) != row['receipt_sha256']:
            raise Refusal('actor observation commitment changed')
        return payload, result, rows

    def evaluate(self, sid):
        """Blue-only, after commit: reopen actor DB and pin an immutable report."""
        with self._db() as ledger:
            ledger.execute('BEGIN IMMEDIATE')
            row = self._session(ledger, sid)
            if json.loads(row['policy']) != scorer_policy():
                raise Refusal('frozen Blue scorer changed; original reports retained')
            frames = ledger.execute('SELECT * FROM frames WHERE session_id=? ORDER BY seq', (sid,)).fetchall()
            with self._actor(row) as store, store.db:
                store.db.execute('BEGIN IMMEDIATE')
                attempts = store.db.execute('SELECT * FROM browser_attempts ORDER BY seq').fetchall()
                for attempt in attempts:
                    self._committed(attempt)
                for frame in frames:
                    self._frame(ledger, sid, frame['frame_id'])
                    self.pixels(sid, frame['frame_id'])
                reopened = QuoteStore(store.path)
                try:
                    latest = reopened.latest()
                finally:
                    reopened.close()
                if latest != (self._committed(attempts[-1])[2] if attempts else []):
                    raise Refusal('persisted latest rows differ from committed actor snapshot')
                snapshot = identity({'session': row['spec_sha256'], 'state': row['state'],
                                     'frames': [f['payload_sha256'] for f in frames],
                                     'attempts': [a['receipt_sha256'] for a in attempts], 'latest': latest})
                prior = store.db.execute('SELECT * FROM browser_evaluations WHERE snapshot_sha256=?', (snapshot,)).fetchone()
                if prior:
                    if hashlib.sha256(prior['report'].encode()).hexdigest() != prior['report_sha256']:
                        raise Refusal('Blue evaluation commitment changed')
                    return json.loads(prior['report'])
                report = self._score(ledger, row, frames, attempts, latest)
                report.update(snapshot_sha256=snapshot, at=_now())
                raw = encoded(report)
                store.db.execute('INSERT INTO browser_evaluations VALUES (?,?,?,?)', (snapshot, raw, hashlib.sha256(raw.encode()).hexdigest(), _now()))
                return report

    def _score(self, db, session, frames, attempts, latest):
        expected, reviews, measured = {}, [], {'identify-ui': [], 'associate-fields': [], 'read-text': []}
        statuses = {'accepted': 0, 'partial': 0, 'refused': 0, 'empty': 0}
        counters = {'inserted': 0, 'updated': 0, 'stale_ignored': 0, 'unchanged': 0}
        refused = 0
        for frame in frames:
            self.pixels(session['session_id'], frame['frame_id'])
            evidence = json.loads(self._frame(db, session['session_id'], frame['frame_id'])['payload'])
            gold, fields = evidence['expected_quotes'], evidence['truth_fields']
            for quote in gold:
                key = quote_key(quote)
                if key not in expected or quote['quote_time'] > expected[key]['quote_time']:
                    expected[key] = quote
                elif quote['quote_time'] == expected[key]['quote_time'] and quote != expected[key]:
                    raise Refusal('conflicting frozen expected time')
            saved = []
            for attempt in attempts:
                if attempt['frame_id'] != frame['frame_id']:
                    continue
                payload, result, rows = self._committed(attempt)
                statuses[result['status']] += 1
                refused += sum(r['operation'] == 'parse-quote' for r in payload['refusals']) + bool(result['reason'])
                if result['ingest']:
                    for key in counters:
                        counters[key] += result['ingest'][key]
                operations = {}
                for key, output, truth in (
                    ('identify-ui', payload['objects'], fields),
                    ('associate-fields', payload['fields'], [dict(f, box=f['text_box']) for f in fields]),
                ):
                    value = None if output is None else confusion_report(truth, output, operation=key)
                    operations[key] = {'status': 'unmeasured' if value is None else 'measured', 'report': value}
                    if value is not None:
                        measured[key].append(value)
                value = None if payload['recognized'] is None else score_ocr_fields([dict(f, box=f['text_box']) for f in fields], payload['recognized'])
                operations['read-text'] = {'status': 'unmeasured' if value is None else 'measured', 'report': value}
                if value is not None:
                    measured['read-text'].append(value)
                database = score_database(_SavedRows(rows), gold)
                database['source'] = 'independently reopened SQLite database snapshot committed with this attempt'
                saved.append({'attempt_id': payload['attempt_id'], 'status': result['status'], 'reason': result['reason'],
                              'retry_of': payload['retry_of'], 'latency_ms': payload['latency_ms'], 'refusals': payload['refusals'],
                              'database': database, 'operations': operations, 'receipt_sha256': attempt['receipt_sha256']})
            reviews.append({'frame_id': frame['frame_id'], 'image_sha256': frame['image_sha256'],
                            'truth_fields': fields, 'expected_records': len(gold), 'contacts': len(evidence['contacts']),
                            'contact_sha256': identity(evidence['contacts']), 'action': evidence['action'], 'attempts': saved})
        operations = {}
        for key in ('identify-ui', 'associate-fields', 'read-text'):
            items = measured[key]
            report = _merge_ocr(items) if key == 'read-text' and items else merge_confusions(items) if items else None
            operations[key] = {'status': 'measured' if items else 'unmeasured', 'measured_attempts': len(items),
                               'unmeasured_attempts': len(attempts) - len(items), 'report': report}
        database = score_database(_SavedRows(latest), list(expected.values()))
        operations['parse-quote'] = {'status': 'measured' if attempts else 'unmeasured', **statuses, 'refusals': refused,
                                     'boundary': 'typed batches and explicit refusals; parse correctness is checked by independent persisted-row comparison'}
        operations['store-quote'] = {'status': 'measured' if attempts else 'unmeasured', **counters,
                                     'committed_attempts': len(attempts), 'boundary': 'atomic saved ingestion receipts; request replay does not create a new attempt'}
        operations['verify-database'] = {'status': 'measured' if frames else 'unmeasured', 'report': database}
        missed = [{'field': key, 'errors': database['field_errors'][key], 'missing': database['field_missing'][key],
                   'support': database['field_support'][key]} for key in database['field_support']
                  if database['field_errors'][key] or database['field_missing'][key]]
        missed.sort(key=lambda item: (-item['errors'] - item['missing'], -item['missing'], item['field']))
        return {'schema': 'browser-actor-score/1', 'session_id': session['session_id'], 'actor_id': session['actor_id'],
                'state': session['state'], 'attempts': len(attempts), 'frames': reviews,
                'unsubmitted_frames': sum(not frame['attempts'] for frame in reviews),
                'database': database, 'missed_database_fields': missed, 'operations': operations,
                'scorer': json.loads(session['policy']), 'training': 'held',
                'scope': 'one actor-bound session; expected latest quotes from every presented frame including refused, empty and unsubmitted frames; blank-view snapshots have zero expected rows'}

    def review(self, sid):
        """Blue-only durable state summary; does not trigger evaluation."""
        result = self.session(sid)
        with self._db(readonly=True) as db:
            row = self._session(db, sid)
            with self._actor(row) as store:
                result['evaluations'] = store.db.execute('SELECT COUNT(*) FROM browser_evaluations').fetchone()[0]
                result['database_counts'] = store.counts()
        return result


def _merge_ocr(reports):
    per_role = {role: {key: sum(r['per_role'][role][key] for r in reports)
                       for key in ('support', 'correct', 'missing', 'wrong', 'characters', 'character_errors')}
                for role in SPORTS_ROLES}
    for stats in per_role.values():
        stats['accuracy'] = stats['correct'] / stats['support'] if stats['support'] else None
    missed = [{'role': role, 'misses': s['missing'] + s['wrong'], 'support': s['support']}
              for role, s in per_role.items() if s['missing'] + s['wrong']]
    missed.sort(key=lambda item: (-item['misses'], item['role']))
    return {'schema': 'browser-ocr-aggregate/1',
            **{key: sum(s[key] for s in per_role.values()) for key in ('support', 'correct', 'missing', 'wrong', 'characters', 'character_errors')},
            'per_role': per_role, 'most_missed': missed, 'failures': [f for r in reports for f in r['failures']],
            'minimum_confidence': 0.9, 'overlap_coverage': 0.25}
