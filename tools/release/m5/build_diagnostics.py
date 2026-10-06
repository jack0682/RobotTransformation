#!/usr/bin/env python3
"""Closed build-failure facts. Never publish raw logs, arguments or exception text.

Locations must belong to the exact committed public candidate. Resource fields
are post-command snapshots, not peak usage or evidence that an OOM caused exit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

SCHEMA='rx.m5.closed-build-failure.v1'
VOCAB_SCHEMA='rx.m5.public-build-vocabulary.v1'
PREFIX='M5_CLOSED_BUILD_DIAGNOSTIC '
PHASES={'DISTRIBUTION_BUILD','SDK_BUILD','SEALED_TEST'}
KINDS={'UNCLASSIFIED','RUST_ERROR','SOURCE_ERROR','TEST_FAILED','PANIC_AT_SOURCE',
       'LINK_FAILURE','CMAKE_FAILURE','DISK_FULL_MESSAGE','ALLOCATION_FAILURE_MESSAGE',
       'SIGKILL_MESSAGE','CHILD_EXIT_137','NETWORK_FAILURE_MESSAGE','SDK_WRAPPER_FAILURE',
       'LOG_BOUND','EVENT_BOUND'}
MAX_LOG=32*1024*1024
MAX_HASH=256*1024*1024
MAX_EVENTS=64
HASH=re.compile('[0-9a-f]{64}')


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(value).hexdigest()
def require(ok):
    if not ok:raise ValueError('CLOSED_DIAGNOSTIC_INVALID')


def vocabulary(repo,expected_head):
    repo=Path(repo).resolve();env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    for key in list(env):
        if key.startswith('GIT_') and key not in ('GIT_OPTIONAL_LOCKS','GIT_NO_REPLACE_OBJECTS'):env.pop(key)
    def git(*args):return subprocess.check_output(['git','--no-replace-objects','-C',str(repo),*args],env=env)
    head=git('rev-parse','HEAD').decode().strip();require(bool(re.fullmatch('[0-9a-f]{40}',expected_head)) and head==expected_head)
    rows=[]
    for record in git('ls-tree','-r','-z','HEAD','--','rx-platform','rx-solutions','tools/release/m5').split(b'\0'):
        if not record:continue
        header,name=record.split(b'\t',1);mode,kind,oid=header.decode().split();name=name.decode();path=Path(name)
        if path.suffix not in ('.rs','.py','.cpp','.cc','.h','.hpp','.cmake','.toml','.ts','.tsx') and path.name!='CMakeLists.txt':continue
        require(mode in ('100644','100755') and kind=='blob' and not (repo/path).is_symlink())
        raw=(repo/path).read_bytes();require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid)
        lines=raw.decode('utf-8').splitlines();require(0<=len(lines)<=200000)
        tests={}
        for number,line in enumerate(lines,1):
            found=re.search(r'\bfn ([A-Za-z_][A-Za-z0-9_]*)\s*\(',line)
            if found:tests.setdefault(found[1],[]).append(number)
        rows.append({'path':name,'lines':len(lines),'functions':tests})
    require(bool(rows));return {'schema':VOCAB_SCHEMA,'commit':head,'files':rows}


def validate_vocab(value):
    require(set(value)=={'schema','commit','files'} and value['schema']==VOCAB_SCHEMA)
    require(bool(re.fullmatch('[0-9a-f]{40}',value['commit'])) and isinstance(value['files'],list) and 0<len(value['files'])<10000)
    seen=set()
    for row in value['files']:
        require(set(row)=={'path','lines','functions'} and type(row['lines']) is int and 0<=row['lines']<=200000)
        name=row['path'];require(isinstance(name,str) and not name.startswith('/') and '\\' not in name and '..' not in Path(name).parts)
        require(name.startswith(('rx-platform/','rx-solutions/','tools/release/m5/')) and name not in seen);seen.add(name)
        require(isinstance(row['functions'],dict))
        for fn,numbers in row['functions'].items():
            require(bool(re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}',fn)) and isinstance(numbers,list))
            require(all(type(n) is int and 0<n<=row['lines'] for n in numbers))
    return value


def event(kind,code=None,file=None,line=None):return {'kind':kind,'code':code,'file':file,'line':line}


def validate_event(value,vocab):
    require(isinstance(value,dict) and set(value)=={'kind','code','file','line'} and value['kind'] in KINDS)
    require(value['code'] is None or isinstance(value['code'],str) and bool(re.fullmatch('E[0-9]{4}',value['code'])))
    if value['file'] is None:require(value['line'] is None)
    else:
        require(type(value['file']) is int and 0<=value['file']<len(vocab['files']))
        require(type(value['line']) is int and 0<value['line']<=vocab['files'][value['file']]['lines'])
    return value


def resources(root):
    disk=shutil.disk_usage(root)
    value={'disk_total_bytes':disk.total,'disk_free_bytes':disk.free,'memory_total_bytes':None,'memory_available_bytes':None}
    try:
        text=Path('/proc/meminfo').read_text()
        for key,name in [('MemTotal','memory_total_bytes'),('MemAvailable','memory_available_bytes')]:
            found=re.search(r'^'+key+r':\s+(\d+) kB$',text,re.M)
            if found:value[name]=int(found[1])*1024
    except OSError:pass
    return value


def aliases(vocab,component):
    result={};functions={}
    for index,row in enumerate(vocab['files']):
        path=row['path'];names=[path]
        prefix='rx-'+('platform' if component=='sdk' else component)+'/'
        if path.startswith(prefix):
            rel=path[len(prefix):];names += [rel,'/source/'+rel]
            if rel.startswith('native/executor/'):names.append('/executor/'+rel[len('native/executor/'):])
            if rel.startswith('apps/operator/'):names.append('/ui/'+rel[len('apps/operator/'):])
        for name in names:result[name]=(index,row['lines'])
        for fn,lines in row['functions'].items():
            if path.startswith(prefix):functions.setdefault(fn,[]).extend((index,n) for n in lines)
    return result,functions


def parse_text(text,vocab,component):
    known,functions=aliases(vocab,component);events=[];code=None
    def add(value):
        validate_event(value,vocab)
        if value not in events and len(events)<MAX_EVENTS:events.append(value)
    for line in text.splitlines():
        line=re.sub(r'^#\d+\s+(?:\d+(?:\.\d+)?\s+)?','',line)
        if len(line)>16384:add(event('LOG_BOUND'));continue
        if PREFIX in line:
            try:
                nested=json.loads(line.split(PREFIX,1)[1]);validate_report(nested,vocab)
                for value in nested['events']:add(value)
            except (ValueError,TypeError,KeyError):pass
            continue
        match=re.search(r'\berror\[(E[0-9]{4})\]',line)
        if match:code=match[1];add(event('RUST_ERROR',code))
        for marker,kind in [('no space left on device','DISK_FULL_MESSAGE'),('cannot allocate memory','ALLOCATION_FAILURE_MESSAGE'),
            ('signal: 9, sigkill','SIGKILL_MESSAGE'),('exit code: 137','CHILD_EXIT_137'),
            ('temporary failure in name resolution','NETWORK_FAILURE_MESSAGE'),('could not resolve host','NETWORK_FAILURE_MESSAGE'),
            ('failed to download','NETWORK_FAILURE_MESSAGE'),('undefined reference','LINK_FAILURE'),('linking with','LINK_FAILURE'),
            ('cmake error','CMAKE_FAILURE')]:
            if marker in line.lower():add(event(kind))
        # Recognized compiler/panic/CMake location grammar; never emit its message.
        location=re.search(r'(?:-->|at |^\s*)\s*([^\s\'"<>]+?):(\d{1,6})(?::\d{1,6})?',line)
        if not location:location=re.search(r'File "([^"]+)", line (\d{1,6})',line)
        if location:
            name=location[1].removeprefix('./')
            if name not in known:
                candidates=[key for key in known if not key.startswith('/') and name.endswith('/'+key)]
                if len(candidates)==1:name=candidates[0]
            if name in known:
                index,bound=known[name];number=int(location[2])
                if 0<number<=bound:add(event('PANIC_AT_SOURCE' if 'panicked' in line else 'SOURCE_ERROR',None,index,number))
        failed=re.search(r'\btest ([A-Za-z0-9_:]+) \.\.\. FAILED\b',line)
        if failed:
            fn=failed[1].rsplit('::',1)[-1]
            matches=functions.get(fn,[])
            if len(matches)==1:
                index,number=matches[0];add(event('TEST_FAILED',None,index,number))
            else:add(event('TEST_FAILED'))
    return events or [event('UNCLASSIFIED')]


def make_report(vocab,phase,component,returncode,logs,resource_root):
    validate_vocab(vocab);require(phase in PHASES and component in ('platform','solutions','sdk'))
    require(type(returncode) is int and -255<=returncode<=255 and returncode!=0)
    events=[];records=[]
    for role,path in logs:
        require(role in ('stdout','stderr','test'));path=Path(path);require(path.is_file() and not path.is_symlink())
        size=path.stat().st_size;record={'role':role,'bytes':size}
        records.append(record)
        if size>MAX_LOG:events.append(event('LOG_BOUND'));continue
        for value in parse_text(path.read_text(errors='replace'),vocab,component):
            if value not in events:events.append(value)
    if len(events)>MAX_EVENTS:events=events[:MAX_EVENTS-1]+[event('EVENT_BOUND')]
    report={'schema':SCHEMA,'phase':phase,'component':component,'source_commit':vocab['commit'],'vocabulary_sha256':digest(encoded(vocab)),
        'status':'FAILED_DIAGNOSTICS_ONLY','returncode':returncode,'events':events or [event('UNCLASSIFIED')],'logs':records,
        'resources':resources(resource_root),'resource_scope':'POST_COMMAND_SNAPSHOT_NOT_PEAK_OR_OOM_PROOF','raw_content_published':False}
    validate_report(report,vocab);return report


def validate_report(value,vocab):
    validate_vocab(vocab)
    require(isinstance(value,dict) and set(value)=={'schema','phase','component','source_commit','vocabulary_sha256','status','returncode','events','logs','resources','resource_scope','raw_content_published'})
    require(value['schema']==SCHEMA and value['phase'] in PHASES and value['component'] in ('platform','solutions','sdk'))
    require(value['source_commit']==vocab['commit'] and value['vocabulary_sha256']==digest(encoded(vocab)))
    require(value['status']=='FAILED_DIAGNOSTICS_ONLY' and type(value['returncode']) is int and -255<=value['returncode']<=255 and value['returncode']!=0)
    require(value['raw_content_published'] is False and value['resource_scope']=='POST_COMMAND_SNAPSHOT_NOT_PEAK_OR_OOM_PROOF')
    require(isinstance(value['events'],list) and 0<len(value['events'])<=MAX_EVENTS)
    for item in value['events']:validate_event(item,vocab)
    require(isinstance(value['logs'],list) and len(value['logs'])<=2)
    for row in value['logs']:
        require(set(row)=={'role','bytes'} and row['role'] in ('stdout','stderr','test'))
        require(type(row['bytes']) is int and 0<=row['bytes']<2**40)
    require(set(value['resources'])=={'disk_total_bytes','disk_free_bytes','memory_total_bytes','memory_available_bytes'})
    require(all(v is None or type(v) is int and 0<=v<2**63 for v in value['resources'].values()))
    return value


def render_report(value,vocab):
    validate_report(value,vocab);result=json.loads(json.dumps(value))
    # Only candidate-verified public source paths are introduced at publication.
    for row in result['events']:
        row['source_path']=None if row['file'] is None else vocab['files'][row['file']]['path']
    return result


def save_failure(path,vocab,phase,component,returncode,logs,resource_root):
    value=make_report(vocab,phase,component,returncode,logs,resource_root)
    private=Path(path).parent/'private-build-diagnostics';private.mkdir(mode=0o700,exist_ok=True)
    records=[]
    for role,file in logs:
        file=Path(file);row={'role':role,'bytes':file.stat().st_size,'sha256':None}
        if row['bytes']<=MAX_HASH:
            with file.open('rb') as stream:row['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        records.append(row)
    with (private/'raw-log-hashes.json').open('xb') as stream:stream.write(encoded({'scope':'PRIVATE_ONLY_NOT_PUBLICLY_REHASHABLE','logs':records})+b'\n')
    with Path(path).open('xb') as stream:stream.write(encoded(value)+b'\n')
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vocabulary',type=Path,required=True)
    p.add_argument('--log',type=Path,required=True);p.add_argument('--returncode',type=int,required=True);a=p.parse_args()
    try:
        vocab=json.loads(a.vocabulary.read_bytes());value=make_report(vocab,'SEALED_TEST','solutions',a.returncode,[('test',a.log)],a.log.parent)
        print(PREFIX+encoded(value).decode())
    except Exception:
        # No error text, raw key material or unvalidated input enters stdout.
        print('M5_CLOSED_BUILD_DIAGNOSTIC_UNAVAILABLE')
    # Diagnostic availability never converts the original failed test into success.
    raise SystemExit(1)


if __name__=='__main__':main()
