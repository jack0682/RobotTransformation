"""Test-only native result link: forward real entry, retain and withhold completion.

This installed/pinned wrapper is used only in a fresh completion-loss case. It
never changes provider status, calls execute a second time, edits native facts,
or fabricates a Host receipt. Passive observations still pass through unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    args = sys.argv[1:]
    mode = args[-2]
    if mode not in ('execute', 'lookup', 'observe'):
        raise ValueError('Host-owned mode required')
    raw = sys.stdin.buffer.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError('bounded native request required')
    child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '/config/host/adapter.py', *args],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    child.stdin.write(raw)
    child.stdin.close()
    if mode == 'execute':
        entry = child.stdout.readline(1_048_577)
        value = json.loads(entry)
        if value.get('schema') != 'rx.external-native-entry.v1':
            raise ValueError('actual provider native entry was not observed')
        sys.stdout.buffer.write(entry)
        sys.stdout.buffer.flush()
    output = child.stdout.read(1_048_577)
    error = child.stderr.read(1_048_577)
    code = child.wait()
    if code:
        sys.stderr.buffer.write(error)
        raise SystemExit(code)
    if mode == 'observe':
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()
        return
    request = json.loads(raw)
    operation = request['dispatch']['operation']
    record = {'mode': mode, 'operation': operation, 'invocation': request['dispatch']['invocation'],
              'request_sha256': hashlib.sha256(raw).hexdigest(),
              'withheld_sha256': hashlib.sha256(output).hexdigest(), 'withheld_bytes': len(output),
              'native_entry_forwarded': mode == 'execute', 'provider_exit': code}
    descriptor = os.open('/data/material-alignment/withheld.jsonl',
                         os.O_APPEND | os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'ab') as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(',', ':')).encode() + b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    # EOF without completion is actual channel loss after original native entry.


if __name__ == '__main__':
    main()
