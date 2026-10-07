"""Linux-only, fresh-case integration helpers; never a product authority service."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import uuid
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[2]
REPOSITORY = PLATFORM.parent
SOLUTIONS = REPOSITORY / 'rx-solutions'
sys.path.insert(0, str(PLATFORM / 'tools'))
sys.path.insert(0, str(SOLUTIONS / 'deployment/local-skills'))
from cell_delivery.api import encoded, publish_new


def linux_only():
    if platform.system() != 'Linux':
        raise SystemExit('DRAFT-M1 runtime preparation and browser checks require isolated Linux.')
    os.umask(0o077)


def uid():
    return str(uuid.uuid4())


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def artifact(raw, schema):
    return {'schema_id': schema, 'sha256': digest(raw), 'size_bytes': str(len(raw))}


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    publish_new(path, value)


def replace_generated(path, value):
    """Only generated, disposable installation configuration may use this helper."""
    Path(path).write_bytes(encoded(value))


def command(args, *, cwd=None, env=None, log=None):
    result = subprocess.run(list(map(str, args)), cwd=cwd, env=env,
                            capture_output=True, text=True)
    if log:
        Path(log).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}); retained log: {log}')
    return result.stdout.strip()


def source_identity():
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return {'source_sha': command(['git', 'rev-parse', 'HEAD'], cwd=REPOSITORY, env=env),
            'source_status': command(['git', 'status', '--porcelain'], cwd=REPOSITORY, env=env),
            'executing_agent': 'Codex DRAFT-M1 integration',
            'host': platform.node(), 'os': platform.system(), 'arch': platform.machine(),
            'github_run_id': os.environ.get('GITHUB_RUN_ID'),
            'github_run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT')}
