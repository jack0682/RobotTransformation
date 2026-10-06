"""Deterministic SDK artifact inventory and checksum verification; stdlib only."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import gzip


def sha(data): return hashlib.sha256(data).hexdigest()

def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def safe_name(name):
    if (not name or name.startswith('/') or '\\' in name or ':' in name or
            any(ord(c)<32 or ord(c)==127 for c in name) or
            any(p in ('','.','..') or p.casefold()=='.git' for p in name.split('/'))):
        raise ValueError('unsafe artifact path: '+repr(name))
    return name


def inventory(root):
    root=Path(root).resolve(); result={}
    for path in sorted(root.rglob('*')):
        relative=safe_name(path.relative_to(root).as_posix());info=path.lstat()
        if stat.S_ISDIR(info.st_mode):continue
        if stat.S_ISLNK(info.st_mode):
            target=os.readlink(path)
            if os.path.isabs(target) or not path.resolve(strict=True).is_relative_to(root):raise ValueError('artifact symlink escapes package')
            result[relative]={'type':'symlink','target':target,'sha256':sha(target.encode()),'mode':oct(stat.S_IMODE(info.st_mode))}
        elif stat.S_ISREG(info.st_mode):
            if info.st_nlink!=1:raise ValueError('unreviewed artifact hardlink')
            result[relative]={'type':'file','bytes':info.st_size,'sha256':sha_file(path),'mode':oct(stat.S_IMODE(info.st_mode))}
        else:raise ValueError('nonregular artifact input')
    return result


def archive(root,target,prefix):
    root=Path(root).resolve();target=Path(target);safe_name(prefix)
    files=inventory(root)
    with target.open('xb') as output:
        with gzip.GzipFile(fileobj=output,mode='wb',mtime=0,filename='') as compressed:
            with tarfile.open(fileobj=compressed,mode='w',format=tarfile.PAX_FORMAT) as stream:
                for path in [root,*sorted(root.rglob('*'))]:
                    name=prefix if path==root else prefix+'/'+path.relative_to(root).as_posix()
                    info=stream.gettarinfo(str(path),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                    if info.isreg():
                        with path.open('rb') as source:stream.addfile(info,source)
                    elif info.isdir() or info.issym():stream.addfile(info)
                    else:raise ValueError('unsupported archive member')
    return {'path':target.name,'sha256':sha_file(target),'bytes':target.stat().st_size,'prefix':prefix,'inventory':files}


def validate_tar(path):
    """Validate closure before a separate extraction; never extracts in this function."""
    with tarfile.open(path,'r:*') as stream:
        seen=set();members=stream.getmembers()
        for item in members:
            name=safe_name(item.name.rstrip('/'))
            if name in seen:raise ValueError('duplicate archive path')
            seen.add(name)
            if not (item.isfile() or item.isdir() or item.issym()):raise ValueError('archive hardlink/device/FIFO refused')
            if item.mode & 0o7000:raise ValueError('special archive permission bits')
            if item.issym():
                if item.linkname.startswith('/') or '\\' in item.linkname:raise ValueError('unsafe symlink')
                import posixpath
                resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),item.linkname))
                if resolved.startswith('../') or resolved.split('/')[0]!=name.split('/')[0]:raise ValueError('symlink escapes archive prefix')
        for item in members:
            parents=list(PurePosixPath(item.name).parents)
            if any(next((x for x in members if x.name.rstrip('/')==str(parent)),None) is not None and
                   next(x for x in members if x.name.rstrip('/')==str(parent)).issym() for parent in parents):
                raise ValueError('archive member beneath symlink')
    return len(members)


def checksums(root,files):
    rows=[]
    for name in sorted(files):
        safe_name(name);path=Path(root)/name
        if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('checksum path has symlink ancestor')
        if not path.is_file() or path.is_symlink():raise ValueError('checksum payload must be a regular file')
        rows.append(sha_file(path)+'  '+name+'\n')
    return ''.join(rows).encode()


def verify_checksums(root,raw,*,allowed_extras=()):
    root=Path(root).resolve();expected={}
    for line in raw.decode('utf-8').splitlines():
        digest,separator,name=line.partition('  ')
        if not separator or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('invalid CHECKSUMS format')
        safe_name(name)
        if name in expected:raise ValueError('duplicate checksum path')
        expected[name]=digest
        path=root/name
        if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('checksum path has symlink ancestor')
        if path.is_symlink() or not path.is_file() or sha_file(path)!=digest:raise ValueError('checksum mismatch: '+name)
    if not expected:raise ValueError('empty artifact checksum set')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    if actual!=set(expected)|set(allowed_extras):raise ValueError('extra/missing artifact file')
    return expected


def extract_new(path,destination,prefix):
    """Extract one validated package into a fresh root, preserving safe SDK symlinks."""
    path=Path(path);destination=Path(destination);safe_name(prefix)
    validate_tar(path)
    with tarfile.open(path,'r:*') as stream:
        members=stream.getmembers()
        if not members or any(m.name.rstrip('/').split('/')[0]!=prefix for m in members):
            raise ValueError('archive prefix differs from selected artifact')
        destination.mkdir(parents=True,exist_ok=False)
        for member in members:
            target=destination/member.name
            target.parent.mkdir(parents=True,exist_ok=True)
            if member.isdir():target.mkdir(exist_ok=True)
            elif member.isfile():
                with stream.extractfile(member) as source,target.open('xb') as output:
                    import shutil
                    shutil.copyfileobj(source,output)
                target.chmod(member.mode & 0o777)
            else:target.symlink_to(member.linkname)
        package=destination/prefix
        # Resolve the entire symlink chain after creating leaves. Dangling/cyclic
        # or escaping chains are invalid artifact inputs; no linked file is read.
        for member in members:
            target=destination/member.name
            if member.issym() and not target.resolve(strict=True).is_relative_to(package.resolve()):
                raise ValueError('artifact symlink chain escapes prefix')
    return package
