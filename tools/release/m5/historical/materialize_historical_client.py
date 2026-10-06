#!/usr/bin/env python3
"""Statically recover four exact published client files. Never executes their code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile

ASSET_SHA256 = 'f9c237a3a79c5912f8243d948e26f9cda8748fdeda440838bd2d391b342ed8c5'
ASSET_BYTES = 93780538
NESTED_MEMBER = 'rx-linux-dev/runtime-images.tar.gz'
NESTED_SHA256 = '94f97e7a9a9f2c0a522e47f3815ef0052a98d7b64a5e92747c824ad3d6024580'
LAYER_MEMBER = 'blobs/sha256/62e7aca781e61dc19e510ad03093e68993b5e6c47eeaab0eb5cf52f530fad886'
FILES = {
    'image_identity.py': (2614, 'd6b8ba9a3a0ba0dfdb4c5c1d5f8338eb8b3958259c4fc9c9f43a30b20bf8ad75'),
    'python_environment.py': (6835, 'b1fb5f488dcfd34453f3143ef3d543393d33ff411a80c17ff636a8b75bdf4006'),
    'runtime_client.py': (19947, '161514ed9afac8699dabafd5bdf24659c451d1dce4223df6fa0d2597af33616f'),
    'rx': (18933, '5f7b565cab21e3b6258dafd1d295bab8f426d1d2b43983603e4e44a7aeb77bf0'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(stream):
    return hashlib.file_digest(stream, 'sha256').hexdigest()


def unique_file(archive, name):
    found = [member for member in archive.getmembers() if member.name == name]
    require(len(found) == 1 and found[0].isfile(), 'Expected one regular member: ' + name)
    return found[0]


def verify_files(values):
    require(set(values) == set(FILES), 'Historical client file set differs')
    for name, raw in values.items():
        size, sha = FILES[name]
        require(len(raw) == size and hashlib.sha256(raw).hexdigest() == sha,
                'Historical client bytes differ: ' + name)


def fresh_output(path):
    require(path.is_absolute() and '..' not in path.parts, 'Absolute canonical output required')
    require(not path.exists() and not path.is_symlink(), 'Fresh output required')
    require(path.parent.is_dir(), 'Existing output parent required')
    require(path.parent.resolve() == path.parent, 'Symlink output parent refused')
    return path


def recover(asset, temp_parent):
    require(asset.is_file() and not asset.is_symlink(), 'Regular archive required')
    with asset.open('rb') as stream:
        require(asset.stat().st_size == ASSET_BYTES and digest(stream) == ASSET_SHA256,
                'Published archive identity differs')
    with tarfile.open(asset, 'r:gz') as outer, tempfile.TemporaryFile(dir=temp_parent) as nested:
        member = unique_file(outer, NESTED_MEMBER)
        with outer.extractfile(member) as source:
            shutil.copyfileobj(source, nested, 1024 * 1024)
        nested.seek(0)
        require(digest(nested) == NESTED_SHA256, 'Nested image archive differs')
        nested.seek(0)
        with tarfile.open(fileobj=nested, mode='r:*') as images, tempfile.TemporaryFile(dir=temp_parent) as layer:
            member = unique_file(images, LAYER_MEMBER)
            with images.extractfile(member) as source:
                shutil.copyfileobj(source, layer, 1024 * 1024)
            layer.seek(0)
            require(digest(layer) == LAYER_MEMBER.rsplit('/', 1)[1], 'Layer digest differs')
            layer.seek(0)
            with tarfile.open(fileobj=layer, mode='r:*') as contents:
                values = {}
                for name, (size, _) in FILES.items():
                    member = unique_file(contents, 'opt/rx/client/' + name)
                    require(member.size == size, 'Historical file size differs')
                    values[name] = contents.extractfile(member).read()
    verify_files(values)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = fresh_output(args.output)
    values = recover(args.asset, output.parent)
    output.mkdir(mode=0o755)
    for name, raw in values.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
        (output / name).chmod(0o444)
    # stdout is a receipt; callers preserve it beside, never inside, frozen code.
    print(json.dumps({'classification': 'PUBLISHED_INSTALLED_RUNTIME_CLIENT',
                      'release_tag': 'v0.4.0-rc.1', 'asset_sha256': ASSET_SHA256,
                      'nested_sha256': NESTED_SHA256, 'layer': LAYER_MEMBER,
                      'files': {name: {'bytes': size, 'sha256': sha} for name, (size, sha) in FILES.items()},
                      'runtime_executed': False}, indent=2))


if __name__ == '__main__':
    main()
