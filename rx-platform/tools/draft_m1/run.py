#!/usr/bin/env python3
"""One new isolated Linux M1 installation and an actual browser/runtime roundtrip."""
from __future__ import annotations

import argparse
import traceback

from common import *


def main():
    linux_only()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform-image', required=True)
    parser.add_argument('--solutions-image', required=True)
    parser.add_argument('--workspace', type=Path, required=True, help='New PRIVATE directory; contains fresh TLS and signing keys')
    parser.add_argument('--evidence-dir', type=Path, required=True, help='New PUBLIC evidence directory; safe artifact scope')
    parser.add_argument('--case', choices=['normal', 'changed-material', 'groove-missing', 'completion-loss', 'lost-start-response'], required=True)
    parser.add_argument('--prepare-only', action='store_true', help='Install and qualify the bounded domain, but make no UI/runtime acceptance claim')
    args = parser.parse_args()
    workspace, evidence = args.workspace.resolve(), args.evidence_dir.resolve()
    if workspace == evidence or workspace.is_relative_to(evidence) or evidence.is_relative_to(workspace):
        parser.error('private workspace and public evidence must be disjoint directories')
    if workspace.exists() or evidence.exists():
        parser.error('fresh workspace and evidence directories required; existing cases are never reset')
    workspace.mkdir(parents=True, mode=0o700)
    evidence.mkdir(parents=True, mode=0o700)
    from installation import Installation
    from authoring import author
    from configure import compile_process, qualification_policy, start_services
    from commission import commission
    from execution_client import ExecutionClient
    from runtime_client import Terminal
    source = source_identity()
    save(evidence / 'source.json', source)
    site = None
    try:
        site = Installation(workspace, evidence, args.platform_image, args.solutions_image, args.case)
        save(evidence / 'environment.json', {**source, 'case': args.case, 'platform_image': site.p,
            'solutions_image': site.s, 'image_architecture': site.simage['Architecture'],
            'scope': 'Actual separate P/Host/Executor containers; external finite FILE_SIMULATION provider; no physical devices'})
        site.prepare(read(SOLUTIONS / 'examples/process/material-alignment/scenario.json'))
        author(site)
        compile_process(site)
        qualification_policy(site)
        start_services(site)
        commission(site)
        client = ExecutionClient(Terminal(site.connections['engineer']), workspace / 'initial-inventory-client')
        pool = client.command('initialize-slots', {'cell': site.cell, 'resource': site.refs['resource.shelf'],
            'rule': site.refs['pattern.shelf'], 'expected_generation': None,
            'reason': 'One fresh simulation shelf seat; original UNKNOWN cases are never reinitialized'}, uid())
        save(evidence / 'initial-slot-pool.json', pool)
        save(workspace / 'browser-ready.json', {'origin': site.origin, 'principal': 'engineer',
            'credentials_file': str(workspace / 'engineer.password'),
            'browser_fixture': str(site.final / 'browser-fixture.json'), 'cell': site.cell,
            'workflow': site.workflow['workflow'], 'publication': site.publication['reference'],
            'requests': site.requests, 'objects': {key: site.refs['object.' + key] for key in ('a', 'b')},
            'catalog': site.workflow['workflow']['catalog'], 'owner_acceptance': 'USER_ACCEPTANCE_PENDING'})
        if args.prepare_only:
            save(evidence / 'result.json', {'status': 'PREPARED_NOT_BROWSER_VERIFIED', 'case': args.case,
                'source_sha': source['source_sha'], 'owner_acceptance': 'USER_ACCEPTANCE_PENDING'})
        else:
            from browser import exercise
            exercise(site)
            save(evidence / 'result.json', {'status': 'PASS_FOR_REPORTED_SCOPE', 'case': args.case,
                'source_sha': source['source_sha'], 'run': site.run,
                'evidence': 'browser/result.json', 'owner_acceptance': 'USER_ACCEPTANCE_PENDING'})
    except Exception as error:
        (evidence / 'failure.log').write_text(traceback.format_exc())
        save(evidence / 'failure.json', {'status': 'FAILED', 'case': args.case,
            'source_sha': source['source_sha'], 'error': str(error),
            'owner_acceptance': 'NOT_ACCEPTED', 'original_state': 'PRESERVED'})
        raise
    finally:
        if site is not None:
            site.preserve()


if __name__ == '__main__':
    main()
