#!/usr/bin/env python3
"""Verify exact release checksums with an explicitly trusted public OpenPGP keyring.

No key generation/import/network retrieval/private signing. The trusted keyring
hash comes from the operator's reviewed policy, never from the unsigned artifact.
This verifies release-file provenance, not rx.release.v1 custody or qualification.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from artifacts import sha,verify_checksums


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--signature',type=Path,required=True)
    p.add_argument('--trusted-keyring',type=Path,required=True)
    p.add_argument('--trusted-keyring-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.artifacts.resolve(strict=True)
    if a.trusted_keyring.is_symlink() or sha(a.trusted_keyring.read_bytes())!=a.trusted_keyring_sha256:
        raise ValueError('trusted keyring differs from external reviewed policy')
    checksum_file=root/'CHECKSUMS.sha256'
    if checksum_file.is_symlink() or a.signature.is_symlink() or not a.signature.is_file():raise ValueError('regular checksum and detached signature inputs required')
    raw=checksum_file.read_bytes();signature_raw=a.signature.read_bytes();keyring_raw=a.trusted_keyring.read_bytes()
    # gpgv's explicit keyring suppresses default keyrings. The owner selects a
    # current trusted keyring; gpgv itself is not a revocation/expiry discovery service.
    with tempfile.TemporaryDirectory(prefix='rx-m5-gpgv-') as home:
        frozen=Path(home)
        for name,content in [('CHECKSUMS.sha256',raw),('signature.asc',signature_raw),('trusted.gpg',keyring_raw)]:
            (frozen/name).write_bytes(content);(frozen/name).chmod(0o600)
        result=subprocess.run(['gpgv','--homedir',home,'--keyring',str(frozen/'trusted.gpg'),
            '--status-fd','1',str(frozen/'signature.asc'),str(frozen/'CHECKSUMS.sha256')],capture_output=True,text=True)
    if result.returncode or '[GNUPG:] VALIDSIG ' not in result.stdout:raise ValueError('detached checksum signature did not verify: '+result.stderr[-1500:])
    extras={'CHECKSUMS.sha256'}
    if a.signature.resolve().is_relative_to(root):extras.add(a.signature.resolve().relative_to(root).as_posix())
    entries=verify_checksums(root,raw,allowed_extras=extras)
    if checksum_file.read_bytes()!=raw or a.signature.read_bytes()!=signature_raw or a.trusted_keyring.read_bytes()!=keyring_raw:
        raise ValueError('provenance input changed during verification')
    value={'schema':'rx.release-provenance-verification.v1','status':'EXACT_CHECKSUMS_SIGNATURE_VERIFIED',
        'checksums_sha256':sha(raw),'signature_sha256':sha(signature_raw),
        'trusted_keyring_sha256':a.trusted_keyring_sha256,'gpg_status':result.stdout,
        'files':entries,'scope':'operator-trusted OpenPGP provenance over exact delivered files; not product signing custody, runtime authority or physical qualification'}
    if a.output.resolve().is_relative_to(root):raise ValueError('verification receipt must be outside immutable artifact set')
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'status':value['status'],'files':len(entries),'receipt':str(a.output)}))


if __name__=='__main__':main()
