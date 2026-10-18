"""Bounded coordinate/PNG console for a separately running local Red actor.

Operator arguments select the owned input/output/executable. Actor stdin accepts
only exact action, finish and cancel messages; stdout contains no Blue data.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
import time
from pathlib import Path

from ..benchmark import Refusal
from .pixel_browser import PixelBrowser


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False), flush=True)


def _message(pending, deadline):
    """Deadline applies to incomplete lines too; never block in stdin.readline."""
    while b'\n' not in pending:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('session input deadline')
        if len(pending) >= 4096:
            raise Refusal('console message byte budget')
        if not select.select([sys.stdin.fileno()], [], [], remaining)[0]:
            raise TimeoutError('session input deadline')
        data = os.read(sys.stdin.fileno(), 4096 - len(pending))
        if not data:
            if pending:
                raise Refusal('incomplete console message')
            return None, pending
        pending += data
    raw, pending = pending.split(b'\n', 1)
    try:
        return json.loads(raw), pending
    except (ValueError, UnicodeError):
        raise Refusal('JSON console message required') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--sample', required=True, help='Frozen sample identity; selected by the operator')
    parser.add_argument('--output', required=True, type=Path, help='Fresh private session directory')
    parser.add_argument('--chrome', required=True, type=Path)
    parser.add_argument('--chrome-sha256', required=True)
    parser.add_argument('--actor', required=True)
    parser.add_argument('--seconds', type=float, default=120, help='Session action/input budget, at most 120 seconds')
    args = parser.parse_args()
    try:
        with PixelBrowser(args.dataset, args.sample, args.output, args.chrome, args.chrome_sha256,
                          actor_id=args.actor, runtime_seconds=args.seconds) as browser:
            _emit({'type': 'frame', 'frame': browser.latest()})
            deadline, pending = time.monotonic() + args.seconds, b''
            for _ in range(256):
                try:
                    message, pending = _message(pending, deadline)
                except TimeoutError:
                    _emit({'type': 'refused', 'reason': 'session input deadline'})
                    return 124
                except Refusal as error:
                    _emit({'type': 'refused', 'reason': str(error)})
                    return 2
                if message is None:
                    _emit({'type': 'state', 'session_id': browser.session_id, 'state': 'cancelled'})
                    return 0
                try:
                    if not isinstance(message, dict):
                        raise Refusal('exact console message required')
                    if set(message) == {'command', 'payload'} and message['command'] == 'action':
                        _emit({'type': 'frame', 'frame': browser.action(message['payload'])})
                    elif set(message) == {'command'} and message['command'] == 'finish':
                        _emit(dict(type='state', **browser.finish()))
                        return 0
                    elif set(message) == {'command'} and message['command'] == 'cancel':
                        browser.close()
                        _emit({'type': 'state', 'session_id': browser.session_id, 'state': 'cancelled'})
                        return 0
                    else:
                        raise Refusal('only action, finish and cancel console messages are supported')
                except Refusal as error:
                    _emit({'type': 'refused', 'reason': str(error)})
                    if browser._state != 'open':
                        return 2
            _emit({'type': 'refused', 'reason': 'console message count budget'})
            return 2
    except Refusal as error:
        _emit({'type': 'refused', 'reason': str(error)})
        return 2
    except KeyboardInterrupt:
        _emit({'type': 'refused', 'reason': 'operator interrupted the local console'})
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
