"""Closed historical runtime-facade artifact pins, shared by producer and live gate."""
import hashlib
import json
from pathlib import Path

LOCK_SHA='e4e416530d4dee347afd7c1acbe6d36b8baf3807f2eed2588250f1ca6b4a810f'
PROBE_SHA='c7bd1a15063e464ebc21bd09c38421d9196fbc2ae905cd4833cb7ded97b2e349'
CLIENT_FILES={'image_identity.py','python_environment.py','runtime_client.py','rx'}
ROOT_FILES={'client','HISTORICAL_CONSUMER_LOCK.json','historical_runtime_probe.py','ORIGIN.json','LICENSE','NOTICE'}


def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()


def validate_historical_bundle(root):
    root=Path(root).absolute()
    if root.resolve()!=root or root.is_symlink() or not root.is_dir():raise ValueError('Canonical historical artifact root required')
    if {p.name for p in root.iterdir()}!=ROOT_FILES:raise ValueError('Historical artifact closure differs')
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):raise ValueError('Historical artifact must contain regular files only')
    if sha(root/'HISTORICAL_CONSUMER_LOCK.json')!=LOCK_SHA or sha(root/'historical_runtime_probe.py')!=PROBE_SHA:
        raise ValueError('Historical lock/probe differs from reviewed pins')
    lock=json.loads((root/'HISTORICAL_CONSUMER_LOCK.json').read_bytes());origin=json.loads((root/'ORIGIN.json').read_bytes())
    if (lock['classification']!='PUBLISHED_INSTALLED_RUNTIME_CLIENT' or lock['runtime_compatibility_status']!='NOT_RUN'
            or origin['classification']!=lock['classification'] or origin['original_asset']!=lock['release']
            or origin['runtime_compatibility']!='NOT_RUN' or origin['new_sdk_relabelled_as_old'] is not False
            or origin['materialization']['runtime_executed'] is not False
            or origin['tools']['lock_sha256']!=LOCK_SHA or origin['tools']['probe_sha256']!=PROBE_SHA):
        raise ValueError('Historical materialization provenance differs')
    if {p.name for p in (root/'client').iterdir()}!=CLIENT_FILES or {row['name'] for row in lock['files']}!=CLIENT_FILES:
        raise ValueError('Exactly four original historical client files are required')
    files={}
    for row in lock['files']:
        file=root/'client'/row['name']
        if file.stat().st_size!=row['bytes'] or sha(file)!=row['sha256'] or file.stat().st_mode&0o222:
            raise ValueError('Historical client bytes or read-only mode differ')
        files[row['name']]=row['sha256']
    return {'classification':lock['classification'],'lock_sha256':LOCK_SHA,'probe_sha256':PROBE_SHA,
        'client_files':files,'original_release':lock['release'],'runtime_compatibility':'NOT_RUN'}


def validate_live_receipt(receipt,pins):
    if (receipt.get('schema')!='rx.historical-runtime-consumer-probe.v1' or receipt.get('status')!='PASS_FOR_REPORTED_SCOPE'
            or receipt.get('classification')!=pins['classification'] or receipt.get('lock_sha256')!=pins['lock_sha256']):
        raise ValueError('Historical live probe did not pass for the selected original bytes')
    for field in ['before_file_sha256','after_file_sha256','final_file_sha256']:
        if receipt.get(field)!=pins['client_files']:raise ValueError('Historical live file pins differ')
    if (receipt['public_before']!=receipt['public_after'] or receipt['public_before']['runs'] or receipt['public_before']['work']
            or receipt['negative'].get('refused') is not True or receipt['negative'].get('admitted_drafts_unchanged') is not True):
        raise ValueError('Historical probe changed execution state or admitted its negative draft')
    return True
