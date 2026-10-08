"""Read-only original Host dispatch metadata; never a replay or authority writer."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from common import save

MAX_OPERATIONS = 64
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024


def _original_operations(site):
    operations, sources, errors = set(), [], []
    selected_run = getattr(site, 'run', None)

    def record(work, run, cell):
        if cell != site.cell or selected_run is not None and run != selected_run:
            return
        identifier = work['operation']['operation_id']
        if not isinstance(identifier, str) or str(uuid.UUID(identifier)) != identifier:
            raise ValueError('original operation UUID is not canonical')
        operations.add(identifier)
        if len(operations) > MAX_OPERATIONS:
            raise ValueError('original operation count exceeds diagnostic bound')

    for filename in ('final-execution-receipt.json', 'final-run-receipt.json', 'final-overview.json'):
        path = Path(site.evidence) / filename
        if not path.exists():
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARTIFACT_BYTES:
                raise ValueError('bounded regular public artifact required')
            document = json.loads(path.read_bytes())
            if filename != 'final-overview.json':
                result = document['result']
                run = result['run']['value']
                for work in result['work']:
                    record(work, run['id'], run['cell'])
            else:
                for row in document['cells']:
                    cell = row['cell']['value']['id']
                    for work in row['work']:
                        record(work, work['run'], cell)
            sources.append(filename)
        except Exception as error:
            errors.append({'inspection': 'original-operation selection: ' + filename,
                           'error': type(error).__name__ + ': ' + str(error)})
    return sorted(operations), sources, errors


# Runs inside the existing owned Linux Host after the case. Importing product
# storage libraries, opening a writer, checkpoints, migrations and DB copies are
# deliberately absent. Native metadata inspection acquires no native owner lock.
_READER = r'''
import hashlib,json,os,signal,sqlite3,stat,sys,time,uuid
from pathlib import Path

MAX_DOCUMENT=1048576
MAX_HISTORY=1024
MAX_TOTAL=8*1048576
MAX_FILES=64
operations=json.loads(sys.argv[1])
if (not isinstance(operations,list) or len(operations)>64
        or len(set(operations))!=len(operations)
        or any(not isinstance(x,str) or str(uuid.UUID(x))!=x for x in operations)):
    raise ValueError('bounded original operation UUIDs required')
requested=set(operations)
report={'schema':'rx.m1-host-dispatch-diagnostic.v1','status':'COMPLETE',
    'operations':operations,'database':'/data/host/host.db',
    'records':{},'history':[],'native_directories':{},'errors':[],
    'history_truncated':False,'native_metadata_only':True,
    'limitations':['Host DB rows share one read transaction; native filesystem metadata is a later read.',
                   'Missing exported native facts do not prove that execution never entered.',
                   'No native owner lock was acquired or probed; metadata is not a custody verdict.']}

def fail(message):
    raise ValueError(message)

def real_directory(path):
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or path.resolve()!=path:
        fail('owned real directory required')

def regular(path):
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid():
        fail('owned regular database/file required')
    return info

def key(kind,operation):
    raw=json.dumps(operation,ensure_ascii=False,separators=(',',':')).encode()
    return kind+'/'+hashlib.sha256(b'RX-HOST-KEY-v1\n'+raw).hexdigest()

def decode(row,expected,operation=None):
    global total
    name,revision,raw=row
    if not isinstance(raw,bytes) or len(raw)>MAX_DOCUMENT:
        fail('stored document exceeds diagnostic bound')
    total+=len(raw)
    if total>MAX_TOTAL:
        fail('aggregate stored document bound exceeded')
    document=json.loads(raw)
    if set(document)!= {'schema','value'} or document['schema']!=expected:
        fail('stored Host document schema differs')
    value=document['value']
    if operation is not None and value.get('operation')!=operation:
        fail('stored Host operation differs from exact requested key')
    return {'key':name,'revision':str(revision),'document_sha256':hashlib.sha256(raw).hexdigest(),
            'document_size_bytes':len(raw),'schema':expected},value

def delivery(row,operation=None):
    metadata,value=decode(row,'rx.host.delivery.v1',operation)
    if value.get('operation') not in requested:
        return None
    fields=('operation','digest','invocation','state','journal_seq','prepared_boot','prepare_until',
            'cell','permit','device_session','evidence_ids','permit_digest')
    metadata['value']={name:value[name] for name in fields}
    return metadata

def native_entry(row,operation):
    metadata,value=decode(row,'rx.host.native-entry.v2',operation)
    fields=('operation','invocation','intent_digest','device_session','profile_digest','evidence')
    metadata['value']={name:value[name] for name in fields}
    payload=value['payload']
    if (not isinstance(payload,list) or len(payload)>65536
            or any(type(x) is not int or not 0<=x<=255 for x in payload)):
        fail('native-entry payload bound/type differs')
    raw=bytes(payload)
    proof=json.loads(raw)
    if (proof.get('schema')!='rx.external-native-entry.v1' or proof.get('operation')!=operation
            or proof.get('invocation')!=value['invocation']):
        fail('native-entry payload identity differs')
    metadata['entry']={name:proof[name] for name in ('schema','challenge','request_sha256','operation',
        'invocation','intent_digest','profile_digest','device_session')}
    metadata['payload_sha256']=hashlib.sha256(raw).hexdigest()
    metadata['payload_size_bytes']=len(raw)
    metadata['payload_matches_reference']=(metadata['payload_sha256']==value['evidence']['sha256']
        and str(len(raw))==value['evidence']['size_bytes'])
    if not metadata['payload_matches_reference']:
        fail('native-entry payload reference differs')
    return metadata

def alarm(signum,frame):
    raise TimeoutError('read-only diagnostic elapsed-time bound exceeded')

signal.signal(signal.SIGALRM,alarm)
signal.alarm(12)
total=0
connection=None
try:
    directory=Path('/data/host'); real_directory(directory)
    database=directory/'host.db'
    if regular(database).st_size>256*1048576:
        fail('Host database exceeds diagnostic size bound')
    # mode=ro observes the existing WAL; immutable=1 would incorrectly ignore it.
    connection=sqlite3.connect('file:/data/host/host.db?mode=ro',uri=True,timeout=1)
    connection.execute('PRAGMA query_only=ON')
    deadline=time.monotonic()+5
    connection.set_progress_handler(lambda: int(time.monotonic()>=deadline),1000)
    def authorize(action,arg1,arg2,database,trigger):
        if action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_TRANSACTION):
            return sqlite3.SQLITE_OK
        if action==sqlite3.SQLITE_READ and arg1=='entities' and arg2 in ('key','revision','document'):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    connection.set_authorizer(authorize)
    connection.execute('BEGIN')
    for operation in operations:
        result={}
        for prefix,project in [('delivery',delivery),('native-entry',native_entry)]:
            name=key(prefix,operation)
            row=connection.execute('SELECT key,revision,document FROM entities WHERE key=?',(name,)).fetchone()
            result[prefix]={'present':False,'key':name} if row is None else {
                'present':True,**project(row,operation)}
        report['records'][operation]=result
    rows=connection.execute('SELECT key,revision,document FROM entities WHERE key>=? AND key<? ORDER BY key LIMIT ?',
        ('delivery-history/','delivery-history0',MAX_HISTORY+1))
    for index,row in enumerate(rows):
        if index==MAX_HISTORY:
            report['history_truncated']=True
            break
        projected=delivery(row)
        if projected is not None:
            report['history'].append(projected)
    connection.execute('ROLLBACK')
except Exception as error:
    report['errors'].append({'inspection':'read-only Host entities','error':type(error).__name__+': '+str(error)})
finally:
    if connection is not None:
        connection.close()

try:
    root=Path('/data/host/native-external'); real_directory(root)
    for operation in operations:
        path=root/operation
        if not path.exists() and not path.is_symlink():
            report['native_directories'][operation]={'present':False}
            continue
        real_directory(path)
        info=path.lstat()
        item={'present':True,'uid':info.st_uid,'inode':info.st_ino,'mode':oct(stat.S_IMODE(info.st_mode)),
              'mtime_ns':str(info.st_mtime_ns),'files':[],'truncated':False}
        report['native_directories'][operation]=item
        with os.scandir(path) as entries:
            for index,entry in enumerate(entries):
                if index==MAX_FILES:
                    item['truncated']=True
                    break
                meta=entry.stat(follow_symlinks=False)
                kind=('regular' if stat.S_ISREG(meta.st_mode) else 'directory' if stat.S_ISDIR(meta.st_mode)
                      else 'symlink' if stat.S_ISLNK(meta.st_mode) else 'other')
                item['files'].append({'name':entry.name,'kind':kind,'uid':meta.st_uid,
                    'owned':meta.st_uid==os.getuid(),'size_bytes':meta.st_size,'inode':meta.st_ino,
                    'mode':oct(stat.S_IMODE(meta.st_mode)),'mtime_ns':str(meta.st_mtime_ns)})
        item['files'].sort(key=lambda v:v['name'])
        names={v['name'] for v in item['files']}
        item['owner_lock_present']='owner.lock' in names
        item['request_present']='request.json' in names
        item['completion_present']='completion.json' in names
        item['empty']=not item['files'] and not item['truncated']
except Exception as error:
    report['errors'].append({'inspection':'native original directory metadata','error':type(error).__name__+': '+str(error)})
finally:
    signal.alarm(0)
if report['errors'] or report['history_truncated'] or any(v.get('truncated') for v in report['native_directories'].values()):
    report['status']='PARTIAL'
print(json.dumps(report,sort_keys=True,separators=(',',':')))
'''


def preserve_host_dispatch(site):
    """Return inspection errors without masking the original scenario failure.

    Call after final-execution-receipt.json and/or final-overview.json are saved.
    Only existing public artifacts and original owned Host facts are inspected.
    """
    errors = []
    try:
        operations, sources, selection_errors = _original_operations(site)
        errors.extend(selection_errors)
        if not operations:
            save(Path(site.evidence) / 'host-dispatch-diagnostics.json', {
                'schema': 'rx.m1-host-dispatch-diagnostic.v1', 'status': 'NO_PUBLIC_OPERATION_IDENTITIES',
                'selection_sources': sources, 'operations': [], 'errors': selection_errors,
                'limitation': 'Public snapshots supplied no operation IDs; this is not proof that no operation exists. No diagnostic command was issued.'})
        elif 'h' not in getattr(site, 'services', {}):
            errors.append({'inspection': 'original Host dispatch', 'error': 'owned Host container is unavailable'})
        else:
            raw = site.d.run('exec', site.services['h'], '/opt/rx/python/python', '-I', '-S', '-B',
                             '-c', _READER, json.dumps(operations, separators=(',', ':')))
            if len(raw.encode()) > MAX_ARTIFACT_BYTES:
                raise ValueError('Host diagnostic output exceeds artifact bound')
            result = json.loads(raw)
            if result.get('schema') != 'rx.m1-host-dispatch-diagnostic.v1' or result.get('operations') != operations:
                raise ValueError('Host diagnostic scope differs from original operation selection')
            result['selection_sources'] = sources
            errors.extend(result.get('errors', []))
            save(Path(site.evidence) / 'host-dispatch-diagnostics.json', result)
    except Exception as error:
        errors.append({'inspection': 'original Host dispatch diagnostics',
                       'error': type(error).__name__ + ': ' + str(error)})
    if errors:
        try:
            save(Path(site.evidence) / 'host-dispatch-diagnostics-errors.json', errors)
        except Exception as error:
            errors.append({'inspection': 'persist diagnostic errors',
                           'error': type(error).__name__ + ': ' + str(error)})
    return errors
