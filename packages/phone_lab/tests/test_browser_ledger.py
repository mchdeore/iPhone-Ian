from __future__ import annotations

import copy
import hashlib
import io
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from PIL import Image

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.browser_ledger import BrowserLedger
from phone_lab.sportsbook.fixtures import provider_snapshot
from phone_lab.sportsbook.storage import QuoteStore, encoded, identity, score_database


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded(value) + '\n')


def exported(tmp_path, actor='red-one', session='1' * 32, phase=0, blank=False):
    """Unit-only executor export; real Chrome acceptance is tested separately."""
    out = tmp_path / session
    config = {'schema': 'owned-pixel-browser/1', 'session_id': session, 'actor_id': actor,
              'training': 'held', 'viewport': {'width': 390, 'height': 844},
              'source_fingerprints': {'unit-fixture': 'a' * 64}, 'browser_sha256': 'b' * 64,
              'dataset_sha256': 'c' * 64, 'max_actions': 64}
    write_json(out / 'blue-private/config.json', config)
    write_json(out / 'state.json', {'session_id': session, 'actor_id': actor, 'state': 'open'})
    return out, append_frame(out, phase=phase, blank=blank)


def append_frame(out, phase=0, blank=False):
    seq = len(list((out / 'blue-private/frames').glob('*.json'))) + 1
    buffer = io.BytesIO()
    Image.new('RGB', (390, 844), (30 + seq, 40 + phase, 50)).save(buffer, format='PNG')
    png = buffer.getvalue()
    sid = json.loads((out / 'blue-private/config.json').read_text())['session_id']
    fid = identity([sid, seq, hashlib.sha256(png).hexdigest()])
    frame = {'session_id': sid, 'frame_id': fid, 'image_sha256': hashlib.sha256(png).hexdigest(),
             'image_file': f'red-pixels/{seq:04d}.png', 'viewport': [390, 844]}
    fields = [] if blank else [{'id': 'price', 'role': 'odds', 'text': '1.90',
                               'box': {'x': 30, 'y': 100, 'width': 80, 'height': 30},
                               'text_box': {'x': 40, 'y': 104, 'width': 40, 'height': 18}}]
    write_json(out / f'blue-private/frames/{seq:04d}.json', {
        'frame': frame, 'at': '2026-10-18T00:00:00-04:00', 'phase': phase,
        'tab': 'account' if blank else 'sports', 'contact_count': 0, 'fields': fields,
        'expected_quotes': [] if blank else provider_snapshot(71, phase)['quotes']})
    path = out / frame['image_file']
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(png)
    if seq > 1:
        prior = json.loads((out / f'blue-private/frames/{seq - 1:04d}.json').read_text())['frame']
        request = {'request_id': f'wait-{seq}', 'frame_id': prior['frame_id'],
                   'image_sha256': prior['image_sha256'], 'kind': 'wait', 'points': [], 'duration_ms': 0}
        with (out / 'actions.jsonl').open('a') as handle:
            handle.write(encoded({'request': request, 'request_sha256': identity(request), 'state': 'reserved'}) + '\n')
            handle.write(encoded({'request_id': request['request_id'], 'request_sha256': identity(request),
                                  'state': 'committed', 'frame': frame}) + '\n')
    return frame


def attempt(frame, actor='red-one', aid='first', quotes=None, **changes):
    value = {'attempt_id': aid, 'frame_id': frame['frame_id'], 'image_sha256': frame['image_sha256'],
             'actor_id': actor, 'model_sha256': None, 'parser_version': 'unit-parser/1',
             'latency_ms': 10, 'quotes': quotes or [], 'refusals': [], 'retry_of': None,
             'recognized': None, 'fields': None, 'objects': None}
    return dict(value, **changes)


def test_committed_observations_replay_retry_and_independent_reopen(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    quotes = provider_snapshot(71, 0)['quotes']
    first = attempt(frame, quotes=quotes)
    receipt = ledger.submit(sid, first)
    assert set(receipt) == {'attempt_id', 'status', 'ingest', 'replayed'}
    assert receipt['status'] == 'accepted' and receipt['ingest']['inserted'] == 4
    replay = ledger.submit(sid, first)
    assert replay['replayed'] and set(replay) == set(receipt)
    with pytest.raises(Refusal, match='conflicting'):
        ledger.submit(sid, dict(first, latency_ms=11))
    with pytest.raises(Refusal, match='retry'):
        ledger.submit(sid, dict(first, attempt_id='second'))
    assert ledger.submit(sid, dict(first, attempt_id='second', retry_of='first'))['ingest']['unchanged'] == 4
    fresh = BrowserLedger(tmp_path / 'ledger')
    report = fresh.evaluate(sid)
    assert report['database']['correct_records'] == 4
    assert report['attempts'] == 2 and report['actor_id'] == 'red-one'
    assert report['operations']['identify-ui']['status'] == 'unmeasured'
    assert fresh.evaluate(sid) == report
    assert fresh.review(sid)['evaluations'] == 1


def test_actor_databases_do_not_hide_empty_or_refused_actor_misses(tmp_path):
    ledger = BrowserLedger(tmp_path / 'ledger')
    reports = []
    for actor, sid, quotes in [('good', '1' * 32, provider_snapshot(71, 0)['quotes']), ('miss', '2' * 32, [])]:
        out, frame = exported(tmp_path, actor=actor, session=sid)
        ledger.attach(out)
        ledger.submit(sid, attempt(frame, actor=actor, quotes=quotes,
                                  refusals=[] if quotes else [{'operation': 'parse-quote', 'reason': 'no readable rows'}]))
        reports.append(ledger.evaluate(sid))
    assert reports[0]['database']['correct_records'] == 4
    assert reports[1]['database']['missing_records'] == 4
    assert reports[1]['frames'][0]['attempts'][0]['status'] == 'refused'
    assert reports[1]['operations']['parse-quote']['refusals'] == 1
    assert all(v == 4 for v in reports[1]['database']['field_missing'].values())


def test_blank_unsubmitted_and_refused_frames_have_explicit_support(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    report = ledger.evaluate(sid)
    assert report['unsubmitted_frames'] == 1 and report['database']['missing_records'] == 4
    ledger.submit(sid, attempt(frame))
    blank = append_frame(out, blank=True)
    ledger.sync(sid)
    ledger.submit(sid, attempt(blank, aid='blank'))
    report = ledger.evaluate(sid)
    assert report['database']['expected_records'] == 4
    assert report['frames'][1]['attempts'][0]['database']['score'] is None
    assert report['frames'][1]['attempts'][0]['database']['expected_records'] == 0
    assert report['frames'][1]['attempts'][0]['database']['stored_records'] == 0
    assert report['operations']['parse-quote']['empty'] == 2


def test_database_accepts_an_explicit_empty_expected_view(tmp_path):
    store = QuoteStore(tmp_path / 'quotes.sqlite')
    try:
        report = score_database(store, [])
        assert report['score'] is None and report['row_recall'] is None
        assert report['field_support']['status'] == 0
        store.ingest('a' * 64, provider_snapshot(71, 0)['quotes'])
        report = score_database(store, [])
        assert report['unexpected_records'] == 4 and report['score'] is None
    finally:
        store.close()


def test_detector_ocr_and_field_association_are_separate_operations(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    box = {'x': 40, 'y': 104, 'width': 40, 'height': 18}
    raw = [{'text': '1.90', 'confidence': 0.99, 'box': box}]
    fields = [{'id': 'recognized-price', 'role': 'odds', 'confidence': 0.99, 'box': box, 'text': '1.90'}]
    ledger.submit(sid, attempt(frame, recognized=raw, fields=fields))
    report = ledger.evaluate(sid)
    assert report['operations']['read-text']['report']['correct'] == 1
    assert report['operations']['associate-fields']['report']['per_class']['odds']['true_positive'] == 1
    assert report['operations']['identify-ui']['status'] == 'unmeasured'
    ledger.submit(sid, attempt(frame, aid='empty-detector', retry_of='first', objects=[], model_sha256='d' * 64,
                              recognized=[], fields=[]))
    report = ledger.evaluate(sid)
    assert report['operations']['identify-ui']['report']['most_missed'][0]['class'] == 'odds'
    assert report['operations']['read-text']['report']['missing'] == 1
    assert report['operations']['identify-ui']['measured_attempts'] == 1
    assert report['operations']['read-text']['measured_attempts'] == 2


def test_failed_ingestion_retains_observation_and_rolls_back_partial_quotes(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    quotes = provider_snapshot(71, 0)['quotes']
    broken = copy.deepcopy(quotes)
    broken[-1]['home'] = 'Changed Team'
    if broken[-1]['selection'] == quotes[-1]['home']:
        broken[-1]['selection'] = 'Changed Team'
    receipt = ledger.submit(sid, attempt(frame, quotes=broken))
    assert receipt['status'] == 'refused' and receipt['ingest'] is None
    report = ledger.evaluate(sid)
    assert report['database']['stored_records'] == 0
    assert report['database']['missing_records'] == 4
    assert report['attempts'] == 1 and report['frames'][0]['attempts'][0]['reason']


def test_frame_database_snapshots_do_not_change_after_later_updates(tmp_path):
    out, first = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    ledger.submit(sid, attempt(first, quotes=provider_snapshot(71, 0)['quotes']))
    second = append_frame(out, phase=2)
    ledger.sync(sid)
    # Explicitly reproduce the suspended-row stale-state failure, without training.
    later = provider_snapshot(71, 2)['quotes']
    visible = [q for q in later if q['status'] != 'suspended']
    ledger.submit(sid, attempt(second, aid='later', quotes=visible,
                              refusals=[{'operation': 'parse-quote', 'reason': 'suspended row refused'}]))
    report = ledger.evaluate(sid)
    assert report['frames'][0]['attempts'][0]['database']['correct_records'] == 4
    assert report['frames'][1]['attempts'][0]['database']['correct_records'] == 3
    assert report['database']['wrong_records'] == 1
    assert report['database']['field_errors']['status'] == 1
    assert report['database']['field_errors']['odds'] == 1
    assert report['missed_database_fields'][0]['errors'] == 1
    assert report['frames'][1]['action']['kind'] == 'wait'


@pytest.mark.parametrize('change', [
    {'actor_id': 'other'}, {'frame_id': 'f' * 64}, {'image_sha256': 'f' * 64},
    {'latency_ms': float('nan')}, {'latency_ms': True}, {'objects': []}, {'extra': 'not permitted'},
    {'recognized': [{'text': 'x', 'confidence': 1, 'box': {'x': 389, 'y': 0, 'width': 2, 'height': 1}}]},
    {'fields': [{'id': 'x', 'role': 'odds', 'confidence': 1, 'text': 'x', 'box': {'x': 0, 'y': 0, 'width': True, 'height': 1}}]},
    {'refusals': [{'operation': [], 'reason': 'malformed operation'}]},
])
def test_bad_observations_are_refused_before_commit(tmp_path, change):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    with pytest.raises(Refusal):
        ledger.submit(sid, attempt(frame, **change))
    assert ledger.review(sid)['attempts'] == 0


def test_simultaneous_replay_has_exactly_one_durable_observation(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    payload = attempt(frame, quotes=provider_snapshot(71, 0)['quotes'])
    with ThreadPoolExecutor(2) as pool:
        receipts = list(pool.map(lambda _: ledger.submit(sid, payload), range(2)))
    assert sorted(r['replayed'] for r in receipts) == [False, True]
    assert ledger.review(sid)['attempts'] == 1


def test_frozen_png_metadata_and_observation_tampering_refused(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    ledger.submit(sid, attempt(frame))
    ledger.evaluate(sid)
    stored = ledger.root / f'runs/{sid}/pixels/{frame["frame_id"]}.png'
    original = stored.read_bytes()
    stored.write_bytes(original + b'tampered')
    with pytest.raises(Refusal, match='pixel'):
        ledger.pixels(sid, frame['frame_id'])
    with pytest.raises(Refusal, match='pixel'):
        ledger.evaluate(sid)
    stored.write_bytes(original)
    with sqlite3.connect(ledger.root / f'runs/{sid}/actor.sqlite') as db:
        db.execute("UPDATE browser_attempts SET stored_rows='[]', receipt_sha256='bad'")
    with pytest.raises(Refusal, match='commitment'):
        ledger.evaluate(sid)


def test_database_latest_tampering_is_not_scored_as_an_actor_result(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    ledger.submit(sid, attempt(frame, quotes=provider_snapshot(71, 0)['quotes']))
    with sqlite3.connect(ledger.root / f'runs/{sid}/actor.sqlite') as db:
        db.execute('DELETE FROM latest')
    with pytest.raises(Refusal, match='snapshot'):
        ledger.evaluate(sid)


def test_frozen_scorer_and_executor_change_refused(tmp_path, monkeypatch):
    import phone_lab.sportsbook.browser_ledger as module
    out, _ = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    before = module.scorer_policy()
    monkeypatch.setattr(module, 'scorer_policy', lambda: dict(before, version='changed'))
    with pytest.raises(Refusal, match='scorer'):
        ledger.evaluate(sid)
    write_json(out / 'blue-private/config.json', {'schema': 'changed'})
    with pytest.raises(Refusal, match='executor'):
        ledger.sync(sid)


def test_foreign_database_symlinks_and_conflicting_frame_preserved(tmp_path):
    foreign = tmp_path / 'foreign'
    foreign.mkdir()
    db_path = foreign / 'sessions.sqlite'
    with sqlite3.connect(db_path) as db:
        db.execute('CREATE TABLE user_work(value TEXT)')
        db.execute("INSERT INTO user_work VALUES('keep')")
    before = db_path.read_bytes()
    with pytest.raises(Refusal, match='foreign'):
        BrowserLedger(foreign)
    assert db_path.read_bytes() == before
    link = tmp_path / 'linked'
    link.symlink_to(foreign)
    with pytest.raises(Refusal, match='symlink'):
        BrowserLedger(link)
    out, _ = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    path = out / 'blue-private/frames/0001.json'
    value = json.loads(path.read_text())
    value['fields'][0]['text'] = '2.00'
    write_json(path, value)
    with pytest.raises(Refusal, match='frame'):
        ledger.sync(sid)


def test_incoming_action_requires_the_preceding_frame_commitment(tmp_path):
    out, _ = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    append_frame(out, phase=1)
    entries = [json.loads(line) for line in (out / 'actions.jsonl').read_text().splitlines()]
    entries[0]['request']['frame_id'] = 'f' * 64
    for entry in entries:
        entry['request_sha256'] = identity(entries[0]['request'])
    (out / 'actions.jsonl').write_text('\n'.join(encoded(e) for e in entries) + '\n')
    with pytest.raises(Refusal, match='preceding'):
        ledger.sync(sid)
    assert ledger.session(sid)['frames'] == 1


def test_elapsed_observation_does_not_infer_an_executor_exit(tmp_path):
    out, _ = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    sid = ledger.attach(out)['session_id']
    assert BrowserLedger(tmp_path / 'ledger').sync(sid)['state'] == 'open'
    # This ledger deliberately delegates confirmed-exit recovery to the future supervisor.
    write_json(out / 'state.json', {'session_id': sid, 'actor_id': 'red-one', 'state': 'cancelled'})
    assert ledger.sync(sid)['state'] == 'cancelled'
    write_json(out / 'state.json', {'session_id': sid, 'actor_id': 'red-one', 'state': 'open'})
    with pytest.raises(Refusal, match='terminal'):
        ledger.sync(sid)


def test_public_receipts_and_pixels_exclude_blue_private_data(tmp_path):
    out, frame = exported(tmp_path)
    ledger = BrowserLedger(tmp_path / 'ledger')
    public = ledger.attach(out)
    sid = public['session_id']
    receipt = ledger.submit(sid, attempt(frame))
    combined = encoded([public, receipt, ledger.frame(sid, frame['frame_id'])])
    for private in ('source_fingerprints', 'expected_quotes', 'blue-private', str(tmp_path), 'text_box', 'database', 'score'):
        assert private not in combined
    assert ledger.pixels(sid, frame['frame_id']).startswith(b'\x89PNG')


def test_real_chrome_frames_text_borders_contacts_and_blue_scoring(tmp_path):
    from phone_lab.sportsbook.dataset import build_dataset
    from phone_lab.sportsbook.pixel_browser import PixelBrowser
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    if not chrome.is_file():
        pytest.skip('configured local Chrome missing; acceptance unverified')
    root = tmp_path / 'dataset'
    manifest = build_dataset(root, chrome, seeds={'train': [71], 'validation': [171], 'test': [271]})
    sample = next(row for row in manifest['samples'] if row['tags']['provider'] == 'provider-a' and row['tags']['phase'] == 0)
    digest = hashlib.sha256(chrome.read_bytes()).hexdigest()
    out = tmp_path / 'browser'
    ledger = BrowserLedger(tmp_path / 'ledger')
    with PixelBrowser(root, sample['sample_id'], out, chrome, digest, actor_id='red-one') as browser:
        sid = ledger.attach(out)['session_id']
        first = browser.latest()
        ledger.submit(sid, attempt(first, quotes=provider_snapshot(71, 0)['quotes']))
        browser.action({'request_id': 'refresh', 'frame_id': first['frame_id'], 'image_sha256': first['image_sha256'],
                        'kind': 'tap', 'points': [{'x': 100, 'y': 725}], 'duration_ms': 0})
        ledger.sync(sid)
        browser.finish()
        ledger.sync(sid)
    report = ledger.evaluate(sid)
    assert report['frames'][1]['action']['kind'] == 'tap'
    assert report['frames'][1]['contacts'] == 2
    assert report['unsubmitted_frames'] == 1
    assert report['database']['wrong_records'] == 4
    assert ledger.review(sid)['state'] == 'closed'
    for field in report['frames'][0]['truth_fields']:
        b = field['text_box']
        assert b['width'] > 0 and b['height'] > 0 and b['x'] + b['width'] <= 390 and b['y'] + b['height'] <= 844
