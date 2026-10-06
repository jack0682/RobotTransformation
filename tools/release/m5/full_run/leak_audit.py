"""Exact-secret leak refusal for fresh CI evidence. Never emits secret values.

API: inventory = collect_private([private_root], required_minimums={...});
     receipt = approve_public(inventory, raw_evidence, approved_directory,
                              extra_documents={'result.json': public_result}).
Only approved_directory may be uploaded. A refusal publishes only LEAK_AUDIT.json.
Raw inputs and secrets stay outside that directory. No product authority is added.
"""
from __future__ import annotations
import argparse
import base64
import contextlib
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import stat
import sys
import tarfile
import tempfile
import uuid
import zipfile

PEM=re.compile(rb'-----BEGIN ([A-Z0-9 ]*PRIVATE KEY)-----\s*([A-Za-z0-9+/=\r\n\t ]+)-----END \1-----')
PEM_HEADER=re.compile(rb'-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----')
SECRET_FILENAMES={'client-token','worker-token','password','password.txt','signing-fixtures.json','credentials.json'}
VALUE_FIELDS={'password':'PASSWORD','password_hash':'PASSWORD_HASH','private_seed_hex':'PRIVATE_SEED',
    'private_seed':'PRIVATE_SEED','client_token':'TOKEN','worker_token':'TOKEN','access_token':'TOKEN',
    'refresh_token':'TOKEN','session_token':'TOKEN','token':'TOKEN'}


class AuditIncomplete(ValueError):
    """The code is a fixed category; no private source paths or values in errors."""


def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def _der_children(raw):
    result=[];position=0
    while position<len(raw):
        tag=raw[position];position+=1
        length=raw[position];position+=1
        if length&128:
            width=length&127
            if width==0 or width>4:raise ValueError('DER length')
            length=int.from_bytes(raw[position:position+width],'big');position+=width
        value=raw[position:position+length]
        if len(value)!=length:raise ValueError('DER bound')
        result.append((tag,value));position+=length
    return result


def _private_parts(der):
    """Private PKCS8/EC/RSA pieces only; excludes public EC point/RSA modulus."""
    try:
        top=_der_children(der)
        if len(top)==1 and top[0][0]==0x04:return [top[0][1]]  # Ed25519 seed wrapper.
        if len(top)!=1 or top[0][0]!=0x30:return []
        fields=_der_children(top[0][1])
        if len(fields)>=3 and fields[0][0]==2 and fields[1][0]==0x30 and fields[2][0]==4:
            payload=fields[2][1]
            return [payload,*_private_parts(payload)]
        if len(fields)>=2 and fields[0][0]==2 and fields[1][0]==4:return [fields[1][1]]
        if len(fields)>=9 and all(tag==2 for tag,_ in fields[:9]):return [v.lstrip(b'\0') for _,v in fields[3:9]]
    except (ValueError,IndexError):return []
    return []


class SecretInventory:
    def __init__(self,roots):
        self.roots=tuple(roots);self._patterns={};self._short={};self._compact={};self._values={}
    def __repr__(self):return '<SecretInventory values redacted>'
    @property
    def counts(self):return {kind:len(values) for kind,values in sorted(self._values.items())}
    def add(self,raw,kind,*,compact=False):
        if isinstance(raw,str):raw=raw.encode()
        if not raw:return
        if len(raw)>1024*1024:raise AuditIncomplete('SECRET_VALUE_BOUND')
        self._values.setdefault(kind,set()).add(raw)
        variants={raw}
        try:variants.add(json.dumps(raw.decode(),ensure_ascii=False)[1:-1].encode())
        except UnicodeError:pass
        if len(raw)>=24:variants.add(base64.b64encode(raw))
        target=self._short if len(raw)<8 else self._patterns
        for value in variants:target.setdefault(value,set()).add(kind)
        if compact:self._compact.setdefault(re.sub(rb'\s+',b'',raw),set()).add(kind)
    def key(self,raw):
        for found in PEM.finditer(raw):
            whole=found.group(0);body=re.sub(rb'\s+',b'',found.group(2))
            self.add(whole,'PRIVATE_KEY');self.add(body,'PRIVATE_KEY',compact=True)
            try:der=base64.b64decode(body,validate=True)
            except ValueError:raise AuditIncomplete('PRIVATE_PEM_ENCODING') from None
            self.der(der)
    def der(self,der):
        self.add(der,'PRIVATE_KEY')
        for part in _private_parts(der):
            if len(part)<16:continue
            self.add(part,'PRIVATE_KEY');self.add(part.hex(),'PRIVATE_KEY');self.add(part.hex().upper(),'PRIVATE_KEY')
    def require(self,minimums):
        if any(self.counts.get(kind,0)<count for kind,count in minimums.items()):
            raise AuditIncomplete('REQUIRED_PRIVATE_CLASS_NOT_OBSERVED')


def _private_json(value,inventory):
    if isinstance(value,dict):
        for key,child in value.items():
            normalized=key.lower().replace('-','_')
            if normalized in VALUE_FIELDS and isinstance(child,str) and child:
                kind=VALUE_FIELDS[normalized];inventory.add(child,kind)
                if kind=='PRIVATE_SEED' and re.fullmatch('[0-9a-fA-F]{64}',child):
                    inventory.add(bytes.fromhex(child),kind);inventory.add(child.lower(),kind);inventory.add(child.upper(),kind)
            elif normalized=='credentials' and isinstance(child,dict):
                for password in child.values():
                    if isinstance(password,str) and password:inventory.add(password,'PASSWORD')
            if isinstance(child,str) and 'PRIVATE KEY-----' in child:inventory.key(child.encode())
            _private_json(child,inventory)
    elif isinstance(value,list):
        for item in value:_private_json(item,inventory)


def collect_private(roots,*,required_minimums=None):
    roots=[Path(root).resolve() for root in roots]
    if not roots or any(not root.is_dir() or root.is_symlink() for root in roots):
        raise AuditIncomplete('PRIVATE_ROOT_UNAVAILABLE')
    result=SecretInventory(roots)
    for root in roots:
        for file in sorted(root.rglob('*')):
            if file.is_symlink():
                # A public SDK tree may have internal library symlinks. Do not
                # follow them to find secrets, especially outside the private root.
                if not file.resolve().is_relative_to(root):raise AuditIncomplete('PRIVATE_SYMLINK_ESCAPE')
                continue
            if not file.is_file():continue
            name=file.name.lower();size=file.stat().st_size
            with file.open('rb') as stream:prefix=stream.read(4096)
            token=name in ('client-token','worker-token','client_token','worker_token')
            password=name in ('password','password.txt') or name.endswith('.password')
            key=name.endswith(('.key','.pkcs8')) or bool(PEM_HEADER.search(prefix))
            json_file=file.suffix.lower()=='.json'
            if not (token or password or key or json_file):continue
            if size>32*1024*1024:raise AuditIncomplete('PRIVATE_RECORD_BOUND')
            raw=file.read_bytes()
            if token:result.add(raw.strip(),'TOKEN')
            if password:result.add(raw.rstrip(b'\r\n'),'PASSWORD')
            if PEM_HEADER.search(raw):result.key(raw)
            elif key:
                if name.endswith('.pkcs8') or raw.startswith(b'\x30'):result.der(raw)
                elif raw.strip():result.add(raw.strip(),'PRIVATE_KEY')
            if json_file:
                try:value=json.loads(raw)
                except (ValueError,UnicodeError):continue
                _private_json(value,result)
    if not result.counts:raise AuditIncomplete('NO_PRIVATE_VALUES_OBSERVED')
    result.require(required_minimums or {})
    return result


class _Scanner:
    def __init__(self,secrets,max_bytes,max_member_bytes):
        self.secrets=secrets;self.max_bytes=max_bytes;self.max_member=max_member_bytes
        self.total=0;self.serial=0;self.findings=[];self.spool_root=secrets.roots[0]
    def _matches(self,data):
        kinds=set()
        for pattern,labels in self.secrets._patterns.items():
            if pattern in data:kinds.update(labels)
        for pattern,labels in self.secrets._short.items():
            if re.search(rb'(?<![A-Za-z0-9_])'+re.escape(pattern)+rb'(?![A-Za-z0-9_])',data):kinds.update(labels)
        compact=re.sub(rb'\s+|\\n|\\r',b'',data)
        for pattern,labels in self.secrets._compact.items():
            if pattern in compact:kinds.update(labels)
        return kinds
    def scan(self,stream,name,size=None):
        self.serial+=1;identifier='public-file-'+str(self.serial).zfill(6);kinds=self._matches(name.encode())
        if size is not None and size>self.max_member:raise AuditIncomplete('PUBLIC_MEMBER_BOUND')
        overlap=max([4096,*map(len,self.secrets._patterns),*map(len,self.secrets._short),*map(len,self.secrets._compact)])*2
        tail=b'';count=0;digest=hashlib.sha256()
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:break
            count+=len(chunk);self.total+=len(chunk)
            if count>self.max_member or self.total>self.max_bytes:raise AuditIncomplete('PUBLIC_SCAN_BOUND')
            digest.update(chunk);data=tail+chunk;kinds.update(self._matches(data));tail=data[-overlap:]
        if kinds:self.findings.append({'file_id':identifier,'secret_classes':sorted(kinds)})
        return {'sha256':digest.hexdigest(),'bytes':count}
    def _nested(self,stream,size,name,depth):
        if size>self.max_member:raise AuditIncomplete('ARCHIVE_MEMBER_BOUND')
        with tempfile.SpooledTemporaryFile(max_size=8*1024*1024,dir=self.spool_root) as spool:
            copied=0
            while True:
                chunk=stream.read(1024*1024)
                if not chunk:break
                copied+=len(chunk)
                if copied>self.max_member:raise AuditIncomplete('ARCHIVE_MEMBER_BOUND')
                spool.write(chunk)
            spool.seek(0);self.archives(spool,name,depth+1)
    def archives(self,path,logical_name,depth=0):
        if depth>3:raise AuditIncomplete('ARCHIVE_DEPTH_BOUND')
        lower=logical_name.lower()
        if isinstance(path,(str,Path)):
            with Path(path).open('rb') as probe:magic=probe.read(512)
        else:
            position=path.tell();magic=path.read(512);path.seek(position)
        is_zip=magic.startswith(b'PK\x03\x04')
        is_gzip=magic.startswith(b'\x1f\x8b')
        is_tar=len(magic)>=262 and magic[257:262]==b'ustar'
        nested=lambda name,head: name.lower().endswith(('.tar','.tar.gz','.tgz','.zip','.gz')) or head.startswith((b'PK\x03\x04',b'\x1f\x8b')) or len(head)>=262 and head[257:262]==b'ustar'
        if lower.endswith(('.tar','.tar.gz','.tgz')) or is_tar or is_gzip:
            try:
                options={'name':path} if isinstance(path,(str,Path)) else {'fileobj':path}
                with tarfile.open(mode='r:*',**options) as archive:
                    for member in archive:
                        if member.isdir():continue
                        if member.name.startswith('/') or '..' in Path(member.name).parts:raise AuditIncomplete('ARCHIVE_MEMBER_UNSAFE')
                        if member.issym() or member.islnk():
                            self.scan(io.BytesIO(member.linkname.encode()),logical_name+'!'+member.name)
                            continue  # Metadata only; links are never followed or extracted.
                        if not member.isfile():raise AuditIncomplete('ARCHIVE_MEMBER_UNSAFE')
                        with archive.extractfile(member) as stream:self.scan(stream,logical_name+'!'+member.name,member.size)
                        with archive.extractfile(member) as probe:head=probe.read(512)
                        if nested(member.name,head):
                            with archive.extractfile(member) as stream:self._nested(stream,member.size,member.name,depth)
            except tarfile.TarError:
                if not is_gzip:raise AuditIncomplete('ARCHIVE_UNREADABLE') from None
                if not isinstance(path,(str,Path)):path.seek(0)
                try:
                    with gzip.open(path,'rb') as stream:self.scan(stream,logical_name+'!uncompressed')
                except (OSError,EOFError):raise AuditIncomplete('ARCHIVE_UNREADABLE') from None
            except OSError:raise AuditIncomplete('ARCHIVE_UNREADABLE') from None
        elif lower.endswith('.zip') or is_zip:
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():continue
                        if member.filename.startswith('/') or '..' in Path(member.filename).parts:raise AuditIncomplete('ARCHIVE_MEMBER_UNSAFE')
                        with archive.open(member) as stream:self.scan(stream,logical_name+'!'+member.filename,member.file_size)
                        with archive.open(member) as probe:head=probe.read(512)
                        if nested(member.filename,head):
                            with archive.open(member) as stream:self._nested(stream,member.file_size,member.filename,depth)
            except (zipfile.BadZipFile,OSError):raise AuditIncomplete('ARCHIVE_UNREADABLE') from None
        elif lower.endswith('.gz'):
            try:
                with gzip.open(path,'rb') as stream:self.scan(stream,logical_name+'!uncompressed')
            except (OSError,EOFError):raise AuditIncomplete('ARCHIVE_UNREADABLE') from None


def approve_public(secrets,public_root,approved_root,*,extra_documents=None,max_bytes=2*1024**3,max_member_bytes=512*1024**2):
    """Return a redacted receipt and publish only an audited byte-for-byte tree.

    On refusal approved_root contains LEAK_AUDIT.json alone. On approval it also
    contains evidence/. Original raw evidence is never modified. No secret value,
    derived secret hash, password hash, or private filename is returned.
    """
    approved_root=Path(approved_root).absolute();public_root=Path(public_root).resolve() if public_root is not None else None
    if approved_root.exists() or approved_root.is_symlink():raise ValueError('Fresh approved directory required')
    if public_root is not None and (approved_root.is_relative_to(public_root) or public_root.is_relative_to(approved_root)):
        raise ValueError('Raw and approved public trees must not overlap')
    if any(approved_root.is_relative_to(root) for root in secrets.roots):raise ValueError('Approved output cannot be private data')
    scanner=_Scanner(secrets,max_bytes,max_member_bytes);source_files={};extras={};stage=None
    receipt={'schema':'rx.private-value-leak-audit.v1','status':'PUBLIC_EVIDENCE_REFUSED',
        'secret_classes_observed':secrets.counts,'values_disclosed':False,'raw_evidence_uploaded':False}
    try:
        if public_root is not None:
            if not public_root.is_dir():raise AuditIncomplete('PUBLIC_ROOT_UNAVAILABLE')
            for file in sorted(public_root.rglob('*')):
                if file.is_symlink():raise AuditIncomplete('PUBLIC_SYMLINK_REFUSED')
                if file.is_dir():continue
                if not file.is_file():raise AuditIncomplete('PUBLIC_SPECIAL_FILE_REFUSED')
                relative=file.relative_to(public_root).as_posix()
                with file.open('rb') as stream:source_files[relative]=scanner.scan(stream,relative,file.stat().st_size)
                scanner.archives(file,relative)
        for relative,value in (extra_documents or {}).items():
            if (Path(relative).is_absolute() or '..' in Path(relative).parts or '\\' in relative
                    or not relative or relative in source_files):raise AuditIncomplete('EXTRA_DOCUMENT_PATH')
            raw=_json(value)+b'\n';extras[relative]=raw
            scanner.scan(io.BytesIO(raw),relative,len(raw))
        if scanner.findings:
            receipt.update(reason='ACTUAL_PRIVATE_VALUE_FOUND',findings=scanner.findings)
        else:
            stage=secrets.roots[0]/('.leak-approved-stage-'+uuid.uuid4().hex);(stage/'evidence').mkdir(parents=True)
            for relative,observed in source_files.items():
                source=public_root/relative;target=stage/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True)
                if source.is_symlink():raise AuditIncomplete('PUBLIC_CHANGED_AFTER_SCAN')
                shutil.copyfile(source,target)
                with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
                if actual!=observed['sha256'] or target.stat().st_size!=observed['bytes']:
                    raise AuditIncomplete('PUBLIC_CHANGED_AFTER_SCAN')
            for relative,raw in extras.items():
                target=stage/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            receipt.update(status='PUBLIC_EVIDENCE_APPROVED',reason='ALL_SELECTED_BYTES_AND_ARCHIVE_CONTENTS_SCANNED',
                files_scanned=scanner.serial,bytes_scanned=scanner.total)
            (stage/'LEAK_AUDIT.json').write_bytes(_json(receipt)+b'\n')
            approved_root.parent.mkdir(parents=True,exist_ok=True);os.rename(stage,approved_root);stage=None
            return receipt
    except AuditIncomplete as error:
        receipt.update(reason=str(error),status='PUBLIC_EVIDENCE_REFUSED')
    except Exception:
        receipt.update(reason='AUDIT_INTERNAL_FAILURE',status='PUBLIC_EVIDENCE_REFUSED')
    finally:
        if stage is not None:shutil.rmtree(stage)
    approved_root.mkdir(parents=True,exist_ok=False)
    (approved_root/'LEAK_AUDIT.json').write_bytes(_json(receipt)+b'\n')
    return receipt


def refuse_public(approved_root,reason='PRIVATE_INVENTORY_INCOMPLETE'):
    """Fail-safe receipt when inventory itself could not be established."""
    if not re.fullmatch('[A-Z_]{1,64}',reason):reason='AUDIT_UNAVAILABLE'
    path=Path(approved_root);path.mkdir(parents=True,exist_ok=False)
    value={'schema':'rx.private-value-leak-audit.v1','status':'PUBLIC_EVIDENCE_REFUSED',
           'reason':reason,'values_disclosed':False,'raw_evidence_uploaded':False}
    (path/'LEAK_AUDIT.json').write_bytes(_json(value)+b'\n')
    return value


def retained_tempdir_type(original,root):
    """Keep only the original acceptance test's explicitly named temporary root."""
    class RetainedTemporaryDirectory(original):
        def __init__(self,*args,**kwargs):
            prefix=kwargs.get('prefix',args[1] if len(args)>1 else None)
            self._retain_for_audit=prefix=='rx-installed-acceptance-'
            if self._retain_for_audit:
                args=list(args)
                if len(args)>2:args[2]=str(root);kwargs.pop('dir',None)
                else:kwargs['dir']=str(root)
            super().__init__(*args,**kwargs)
            if self._retain_for_audit:self._finalizer.detach()
        def cleanup(self):
            if self._retain_for_audit:self._finalizer.detach()
            else:super().cleanup()
    return RetainedTemporaryDirectory


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    retain=sub.add_parser('retain-tempdirs',help='Run unchanged LOCAL_SIM test; retain credential files privately for audit')
    retain.add_argument('--root',type=Path,required=True);retain.add_argument('--script',type=Path,required=True)
    retain.add_argument('arguments',nargs=argparse.REMAINDER)
    a=parser.parse_args()
    root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
    source=a.script.resolve();original=tempfile.TemporaryDirectory
    tempfile.TemporaryDirectory=retained_tempdir_type(original,root)
    sys.path.insert(0,str(source.parent));sys.argv=[str(source),*(a.arguments[1:] if a.arguments[:1]==['--'] else a.arguments)]
    try:runpy.run_path(str(source),run_name='__main__')
    finally:tempfile.TemporaryDirectory=original


if __name__=='__main__':main()
