#!/usr/bin/env python3
"""One new Linux M1 installation; automated browser checks require Linux."""
from __future__ import annotations

import argparse
import ipaddress
import traceback

from common import *


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform-image', required=True)
    parser.add_argument('--solutions-image', required=True)
    parser.add_argument('--workspace', type=Path, required=True, help='New PRIVATE directory; contains fresh TLS and signing keys')
    parser.add_argument('--evidence-dir', type=Path, required=True, help='New PUBLIC evidence directory; safe artifact scope')
    parser.add_argument('--case', choices=['normal', 'changed-material', 'groove-missing', 'completion-loss', 'lost-start-response'], required=True)
    parser.add_argument('--prepare-only', action='store_true', help='Install and qualify the bounded domain, but make no UI/runtime acceptance claim')
    parser.add_argument('--macos-docker-prepare', action='store_true',
        help='Explicitly authorized Darwin API/deployment controller only; requires --prepare-only --case normal and a Linux Docker daemon')
    parser.add_argument('--network-subnet', help='Optional unused RFC1918 /24-/28 for the new internal Docker network; requires --terminal-subnet')
    parser.add_argument('--terminal-subnet', help='Optional separate unused RFC1918 /24-/28 for the new terminal Docker network')
    args = parser.parse_args()
    if bool(args.network_subnet) != bool(args.terminal_subnet):
        parser.error('--network-subnet and --terminal-subnet must be supplied together')
    if args.network_subnet:
        try:
            subnets = [ipaddress.ip_network(value, strict=True)
                       for value in (args.network_subnet, args.terminal_subnet)]
            private = [ipaddress.ip_network(value) for value in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
            if any(net.version != 4 or not 24 <= net.prefixlen <= 28
                   or not any(net.subnet_of(pool) for pool in private) for net in subnets):
                raise ValueError('new network subnets must be RFC1918 IPv4 /24-/28')
            if subnets[0].overlaps(subnets[1]):
                raise ValueError('new internal and terminal subnets must not overlap')
        except ValueError as error:
            parser.error(str(error))
    daemon_os_type = None
    if args.macos_docker_prepare:
        if platform.system() != 'Darwin' or not args.prepare_only or args.case != 'normal':
            parser.error('--macos-docker-prepare requires Darwin, --prepare-only and --case normal')
        os.umask(0o077)
        daemon_os_type = command(['docker', 'info', '--format', '{{.OSType}}']).strip()
        if daemon_os_type != 'linux':
            parser.error('--macos-docker-prepare requires the selected Docker daemon OSType=linux')
    else:
        linux_only()
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
    source.update(controller_source_sha=source['source_sha'],
        controller_os=platform.system(), controller_architecture=platform.machine(),
        runtime_os='Linux', macos_docker_prepare=args.macos_docker_prepare)
    if args.macos_docker_prepare:
        source.update(docker_daemon_os_type=daemon_os_type,
            controller_scope='Darwin API/deployment controller; product binaries execute only in new Linux Docker containers')
    if args.network_subnet:
        source['docker_network_subnets'] = {'internal': args.network_subnet, 'terminal': args.terminal_subnet}
    save(evidence / 'source.json', source)
    stage = 'created'
    def progress(value):
        nonlocal stage
        stage = value
        print(json.dumps({'event': 'm1-stage', 'case': args.case,
                          'source_sha': source['source_sha'], 'stage': value}), flush=True)
    site = None
    try:
        progress('installing')
        site = Installation(workspace, evidence, args.platform_image, args.solutions_image, args.case,
            network_subnet=args.network_subnet, terminal_subnet=args.terminal_subnet)
        save(evidence / 'environment.json', {**source, 'case': args.case, 'platform_image': site.p,
            'solutions_image': site.s, 'image_architecture': site.simage['Architecture'],
            'runtime_image_os': site.simage['Os'], 'runtime_architecture': site.simage['Architecture'],
            'platform_image_source_revision': (site.pimage.get('Config', {}).get('Labels') or {}).get('org.opencontainers.image.revision'),
            'solutions_image_source_revision': (site.simage.get('Config', {}).get('Labels') or {}).get('org.opencontainers.image.revision'),
            'scope': 'Actual separate P/Host/Executor containers; external finite FILE_SIMULATION provider; no physical devices'})
        site.prepare(read(SOLUTIONS / 'examples/process/material-alignment/scenario.json'))
        progress('authoring')
        author(site)
        compile_process(site)
        qualification_policy(site)
        progress('starting-services')
        start_services(site)
        progress('qualifying')
        commission(site)
        progress('qualified')
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
            site.arm_loss_link()
            progress('browser')
            exercise(site)
            save(evidence / 'result.json', {'status': 'PASS_FOR_REPORTED_SCOPE', 'case': args.case,
                'source_sha': source['source_sha'], 'run': site.run,
                'evidence': 'browser/result.json', 'owner_acceptance': 'USER_ACCEPTANCE_PENDING'})
        progress('finished')
    except Exception as error:
        print(json.dumps({'event': 'm1-stage', 'case': args.case, 'source_sha': source['source_sha'],
                          'stage': 'failed', 'failed_stage': stage}), flush=True)
        (evidence / 'failure.log').write_text(traceback.format_exc())
        save(evidence / 'failure.json', {'status': 'FAILED', 'case': args.case,
            'source_sha': source['source_sha'], 'error': str(error),
            'owner_acceptance': 'NOT_ACCEPTED', 'original_state': 'PRESERVED'})
        raise
    finally:
        if site is not None:
            progress('preserving')
            site.preserve()
            progress('preserved')


if __name__ == '__main__':
    main()
