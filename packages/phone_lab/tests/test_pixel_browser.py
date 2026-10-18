from __future__ import annotations

import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.dataset import build_dataset
from phone_lab.sportsbook.pixel_browser import PixelBrowser

CHROME = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')


@pytest.fixture(scope='module')
def frozen(tmp_path_factory):
    if not CHROME.is_file():
        pytest.skip('configured local Chrome unavailable; real execution not verified')
    root = tmp_path_factory.mktemp('red-pixel-dataset') / 'dataset'
    manifest = build_dataset(root, CHROME, seeds={'train': [71], 'validation': [171], 'test': [271]})
    sample = next(x for x in manifest['samples'] if x['tags']['provider'] == 'provider-a' and x['tags']['phase'] == 0)
    return root, sample['sample_id'], hashlib.sha256(CHROME.read_bytes()).hexdigest()


def engine(frozen, output, **limits):
    root, sample_id, digest = frozen
    return PixelBrowser(root, sample_id, output, CHROME, digest, actor_id='red-local', **limits)


def action(browser, request_id, kind='tap', points=None, duration_ms=0):
    frame = browser.latest()
    return {'request_id': request_id, 'frame_id': frame['frame_id'],
            'image_sha256': frame['image_sha256'], 'kind': kind,
            'points': points if points is not None else [{'x': 80, 'y': 800}],
            'duration_ms': duration_ms}


def center(browser, selector):
    # Independent trusted test reads geometry; Red's executor accepts no selector.
    box = browser._page.locator(selector).bounding_box()
    return [{'x': box['x'] + box['width'] / 2, 'y': box['y'] + box['height'] / 2}]


def test_actual_refresh_navigation_fresh_pixels_and_provider_contacts(frozen, tmp_path):
    with engine(frozen, tmp_path / 'session') as browser:
        first = browser.latest()
        assert set(first) == {'session_id', 'frame_id', 'image_sha256', 'image_file', 'viewport'}
        assert first['viewport'] == [390, 844]
        assert browser.pixels(first['frame_id']) == browser._page.screenshot(animations='disabled')
        request = action(browser, 'refresh-1', points=center(browser, '#refresh'))
        updated = browser.action(request)
        assert updated['frame_id'] != first['frame_id']
        assert updated['image_sha256'] != first['image_sha256']
        assert '18:00:30 UTC' in browser._page.locator('.updated').inner_text()
        browser.action(action(browser, 'account', points=center(browser, '.bottom a:nth-child(4)')))
        assert browser._page.get_by_role('heading', name='Fictional account').count() == 1
        assert 'No real account or payment connection.' in browser._page.locator('main').inner_text()
        private = sorted((tmp_path / 'session/blue-private/frames').glob('*.json'))
        assert json.loads(private[-1].read_text())['expected_quotes'] == []
        browser.action(action(browser, 'sports', points=center(browser, '.bottom a:first-child')))
        assert '18:00:30 UTC' in browser._page.locator('.updated').inner_text()
        browser.action(action(browser, 'refresh-2', points=center(browser, '#refresh')))
        assert '18:01:00 UTC' in browser._page.locator('.updated').inner_text()
        result = browser.finish()
        assert result == {'session_id': first['session_id'], 'state': 'closed'}
        assert browser.finish() == result
    packet = json.loads((tmp_path / 'session/blue-private/contacts.json').read_text())
    assert all(set(e) == {'kind', 'time_ms', 'x', 'y', 'pointer'} for e in packet['events'])
    score = json.loads((tmp_path / 'session/blue-private/score.json').read_text())
    assert score['features']['contacts'] == 4
    assert not any('text' in e or 'label' in e for e in packet['events'])


def test_exact_replay_stale_commitments_and_typed_action_refusals(frozen, tmp_path):
    with engine(frozen, tmp_path / 'session') as browser:
        old = browser.latest()
        original = action(browser, 'first', points=center(browser, '#refresh'))
        new = browser.action(original)
        count = len(browser._contacts)
        assert browser.action(original) == new
        assert len(browser._contacts) == count
        later = browser.action(action(browser, 'wait', kind='wait', points=[], duration_ms=20))
        assert later['frame_id'] != new['frame_id']
        assert browser.action(original) == new  # Historical replay never advances state.
        invalid = [dict(original, request_id='stale'), dict(original, points=[{'x': 2, 'y': 3}]),
                   dict(action(browser, 'truth'), selector='#refresh'),
                   dict(action(browser, 'training'), kind='train'),
                   dict(action(browser, 'nan'), points=[{'x': float('nan'), 'y': 20}]),
                   dict(action(browser, 'bool'), points=[{'x': True, 'y': 20}]),
                   dict(action(browser, 'outside'), points=[{'x': 390, 'y': 20}]),
                   dict(action(browser, 'digest'), image_sha256='0' * 64),
                   dict(action(browser, 'duration'), duration_ms=True),
                   dict(action(browser, 'long'), duration_ms=2001),
                   dict(action(browser, 'swipe-count'), kind='swipe')]
        for request in invalid:
            with pytest.raises(Refusal):
                browser.action(request)
            assert len(browser._contacts) == count
            assert browser.latest() == later
        assert browser.pixels(old['frame_id'])
        with pytest.raises(Refusal):
            browser.pixels('../blue-private/contacts.json')


def test_real_swipe_has_trusted_contacts_and_cancel_never_scores(frozen, tmp_path):
    with engine(frozen, tmp_path / 'session') as browser:
        browser.action(action(browser, 'swipe', kind='swipe',
                              points=[{'x': 180, 'y': 450}, {'x': 180, 'y': 250}], duration_ms=120))
        events = browser._contacts
        assert events[0]['kind'] == 'down' and events[-1]['kind'] == 'up'
        assert sum(e['kind'] == 'move' for e in events) >= 2
        assert all(events[i]['time_ms'] <= events[i + 1]['time_ms'] for i in range(len(events) - 1))
    state = json.loads((tmp_path / 'session/state.json').read_text())
    assert state['state'] == 'cancelled'
    assert not (tmp_path / 'session/blue-private/score.json').exists()
    logged = [json.loads(x) for x in (tmp_path / 'session/blue-private/contact-events.jsonl').read_text().splitlines()]
    assert logged == events


def test_separate_contexts_and_external_requests_blocked(frozen, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    ready = Barrier(2)
    def worker(name):
        # Each engine owns a separate execution thread/event loop, as the future
        # supervised workers will. Nesting Playwright sync loops is unsupported.
        with engine(frozen, tmp_path / name) as browser:
            ready.wait(timeout=10)
            if name == 'one':
                browser.action(action(browser, 'refresh', points=center(browser, '#refresh')))
                assert browser._page.evaluate("fetch('https://example.com/private').then(()=>false).catch(()=>true)")
                browser._settle()
                assert browser._blocked_requests == 1
                browser._page.evaluate("window.__networkProbe=new WebSocket('wss://phone.invalid/socket');null")
                browser._page.wait_for_function('window.__networkProbe.readyState===WebSocket.CLOSED', timeout=3000)
                browser._settle()
                assert browser._blocked_requests == 2
            else:
                assert browser._page.locator('#refresh').get_attribute('href').endswith('/1/sports')
            assert not browser._page.evaluate('navigator.serviceWorker.controller')
            return browser.latest()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(worker, ['one', 'two']))
    assert first['session_id'] != second['session_id']
    assert first['image_sha256'] != second['image_sha256']


def test_browser_digest_existing_destination_and_mutated_source_refused(frozen, tmp_path):
    root, sample_id, digest = frozen
    with pytest.raises(Refusal, match='digest'):
        PixelBrowser(root, sample_id, tmp_path / 'bad-digest', CHROME, '0' * 64, actor_id='red-local')
    assert not (tmp_path / 'bad-digest').exists()
    output = tmp_path / 'existing'
    output.mkdir()
    marker = output / 'original'
    marker.write_bytes(b'keep')
    with pytest.raises(Refusal, match='exists'):
        engine(frozen, output)
    assert marker.read_bytes() == b'keep'
    import shutil
    copy = tmp_path / 'mutated'
    shutil.copytree(root, copy)
    manifest = json.loads((copy / 'dataset.json').read_text())
    source = copy / manifest['samples'][0]['source_page']
    source.write_bytes(source.read_bytes() + b'changed')
    with pytest.raises(Refusal):
        PixelBrowser(copy, sample_id, tmp_path / 'bad-source', CHROME, digest, actor_id='red-local')
    assert not (tmp_path / 'bad-source').exists()


def test_action_failure_records_uncertainty_and_cannot_reexecute(frozen, tmp_path, monkeypatch):
    with engine(frozen, tmp_path / 'session') as browser:
        request = action(browser, 'effect-before-failure', points=center(browser, '#refresh'))
        def fail():
            raise RuntimeError('observed capture failure')
        monkeypatch.setattr(browser, '_capture', fail)
        with pytest.raises(Refusal, match='interrupted'):
            browser.action(request)
        assert len(browser._contacts) == 2
        for _ in range(2):
            with pytest.raises(Refusal):
                browser.action(request)
        assert len(browser._contacts) == 2
    state = json.loads((tmp_path / 'session/state.json').read_text())
    assert state['state'] == 'interrupted'
    rows = [json.loads(x) for x in (tmp_path / 'session/actions.jsonl').read_text().splitlines()]
    assert [x['state'] for x in rows] == ['reserved', 'interrupted']
    assert rows[0]['request'] == request
    assert len(list((tmp_path / 'session/red-pixels').glob('*.png'))) == 1
    saved_contacts = (tmp_path / 'session/blue-private/contact-events.jsonl').read_text().splitlines()
    assert len(saved_contacts) == 2


def test_limits_and_pixel_corruption_stop_dispatch(frozen, tmp_path):
    with engine(frozen, tmp_path / 'count', max_actions=1) as browser:
        browser.action(action(browser, 'one', kind='wait', points=[], duration_ms=0))
        with pytest.raises(Refusal, match='budget'):
            browser.action(action(browser, 'too-many'))
        assert not browser._contacts
    with engine(frozen, tmp_path / 'runtime') as browser:
        browser._started = time.monotonic() - 121
        with pytest.raises(Refusal, match='budget'):
            browser.action(action(browser, 'too-late'))
        assert not browser._contacts
    with engine(frozen, tmp_path / 'pixels') as browser:
        frame = browser.latest()
        image = tmp_path / 'pixels' / frame['image_file']
        image.write_bytes(image.read_bytes() + b'changed')
        with pytest.raises(Refusal, match='pixels'):
            browser.action(action(browser, 'changed'))
        assert not browser._contacts


def test_frozen_dataset_change_refuses_dispatch_but_preserves_pixels(frozen, tmp_path):
    import shutil
    root, sample_id, digest = frozen
    copied = tmp_path / 'dataset'
    shutil.copytree(root, copied)
    with PixelBrowser(copied, sample_id, tmp_path / 'session', CHROME, digest, actor_id='red-local') as browser:
        frame = browser.latest()
        before = browser.pixels(frame['frame_id'])
        path = copied / 'dataset.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with pytest.raises(Refusal, match='changed'):
            browser.action(action(browser, 'input-drift'))
        assert not browser._contacts
        assert browser.pixels(frame['frame_id']) == before


def test_live_view_borders_and_bounded_refresh_come_from_actual_render(frozen, tmp_path):
    with engine(frozen, tmp_path / 'session') as browser:
        browser.action(action(browser, 'live', points=center(browser, '.bottom a:nth-child(2)')))
        assert browser._page.get_by_text('Synthetic live view', exact=True).count() == 1
        for request_id in ['update-1', 'update-2']:
            browser.action(action(browser, request_id, points=center(browser, '#refresh')))
        before = browser.latest()
        after = browser.action(action(browser, 'current-prices', points=center(browser, '#refresh')))
        assert after['frame_id'] != before['frame_id']
        assert after['image_sha256'] == before['image_sha256']
        evidence = json.loads(sorted((tmp_path / 'session/blue-private/frames').glob('*.json'))[-1].read_text())
        assert evidence['phase'] == 2 and evidence['tab'] == 'live'
        assert len(evidence['expected_quotes']) == 4
        for field in evidence['fields']:
            box = field['box']
            assert 0 <= box['x'] < box['x'] + box['width'] <= 390
            assert 0 <= box['y'] < box['y'] + box['height'] <= 844
        assert browser.pixels(after['frame_id']) == browser._page.screenshot(animations='disabled')


def console(frozen, output, stderr, *, seconds=120):
    root, sample_id, digest = frozen
    return subprocess.Popen([sys.executable, '-m', 'phone_lab.sportsbook.pixel_cli',
                             '--dataset', str(root), '--sample', sample_id, '--output', str(output),
                             '--chrome', str(CHROME), '--chrome-sha256', digest, '--actor', 'console-red',
                             '--seconds', str(seconds)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=stderr)


def line(process):
    assert select.select([process.stdout], [], [], 15)[0], 'bounded console response deadline'
    value = process.stdout.readline()
    assert value, 'console stopped before a response'
    return json.loads(value)


def send(process, message):
    process.stdin.write((json.dumps(message) + '\n').encode())
    process.stdin.flush()


def test_separate_console_process_only_accepts_coordinates_and_never_exports_blue(frozen, tmp_path):
    with (tmp_path / 'stderr.log').open('wb') as stderr:
        process = console(frozen, tmp_path / 'session', stderr)
        try:
            initial = line(process)
            assert initial['type'] == 'frame'
            frame = initial['frame']
            send(process, {'command': 'truth'})
            assert line(process)['type'] == 'refused'
            request = {'request_id': 'console-refresh', 'frame_id': frame['frame_id'],
                       'image_sha256': frame['image_sha256'], 'kind': 'tap',
                       'points': [{'x': 100, 'y': 725}], 'duration_ms': 0}
            send(process, {'command': 'action', 'payload': request})
            refreshed = line(process)
            assert refreshed['type'] == 'frame'
            assert refreshed['frame']['image_sha256'] != frame['image_sha256']
            send(process, {'command': 'action', 'payload': request})
            assert line(process) == refreshed
            send(process, {'command': 'finish'})
            final = line(process)
            assert final == {'type': 'state', 'session_id': frame['session_id'], 'state': 'closed'}
            assert process.wait(timeout=10) == 0
            assert (tmp_path / 'session/red-pixels/0002.png').exists()
            score = json.loads((tmp_path / 'session/blue-private/score.json').read_text())
            assert score['features']['contacts'] == 1
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)


def test_partial_console_message_cannot_bypass_idle_deadline(frozen, tmp_path):
    with (tmp_path / 'stderr.log').open('wb') as stderr:
        process = console(frozen, tmp_path / 'session', stderr, seconds=0.3)
        try:
            assert line(process)['type'] == 'frame'
            os.write(process.stdin.fileno(), b'{')  # No newline; ordinary readline would hang.
            result = line(process)
            assert result == {'type': 'refused', 'reason': 'session input deadline'}
            assert process.wait(timeout=10) == 124
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    assert json.loads((tmp_path / 'session/state.json').read_text())['state'] == 'cancelled'
    assert not (tmp_path / 'session/blue-private/score.json').exists()


def test_other_thread_cannot_reserve_or_dispatch_an_action(frozen, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    with engine(frozen, tmp_path / 'session') as browser:
        request = action(browser, 'wrong-owner')
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(browser.action, request)
            with pytest.raises(Refusal):
                future.result(timeout=5)
        assert browser._state == 'open'
        assert browser._action_count == 0
        assert not browser._contacts
        assert not (tmp_path / 'session/actions.jsonl').exists()
