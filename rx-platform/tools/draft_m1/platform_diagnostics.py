"""Bounded, read-only P dispatch metadata for original operations after a case.

Source contracts:
  rx-platformd/tests/support/delivery/finalize.rs: /data/platform data directory;
  rx-platformd/src/lib.rs: data_directory/platform.db;
  rx-storage/migrations/0001.sql and 0002.sql: entities and outbox columns;
  rx-application/src/persistence.rs: RX-ENTITY-KEY-v1 entity keys;
  rx-application/src/engine/delivery.rs: RX-DELIVERY-ID-v1 authorization IDs,
      durable outbox CAS states and exact delivery-attention references.

There are no persisted outbox attempt/available timestamps in these schemas.
Inspection never manufactures them from UUIDs, row order or wall-clock guesses.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import save
from diagnostics import MAX_ARTIFACT_BYTES, _original_operations


_READER = r'''
import hashlib,json,os,signal,sqlite3,stat,sys,time,uuid
from pathlib import Path

operations=json.loads(sys.argv[1])
selected_cell=sys.argv[2]
selected_run=sys.argv[3] or None
if (not isinstance(operations,list) or len(operations)>64 or len(set(operations))!=len(operations)
        or any(not isinstance(v,str) or str(uuid.UUID(v))!=v for v in operations)
        or not selected_cell or len(selected_cell)>256
        or selected_run is not None and str(uuid.UUID(selected_run))!=selected_run):
    raise ValueError('bounded original operation/Run scope required')

report={'schema':'rx.m1-platform-dispatch-diagnostic.v1','status':'COMPLETE',
    'database':'/data/platform/platform.db','operations':operations,
    'selected_cell':selected_cell,'selected_run':selected_run,'work':{},'errors':[],
    'outbox_columns':['id','state','document'],
    'retry_timing':{'status':'NOT_RECORDED_IN_DATABASE','attempt_count':None,
        'last_attempt_at':None,'available_at':None,
        'reason':'OutboxRecord stores id/state/document only; sender retries and not_before are in-memory.'},
    'limitations':['Projected rows share one existing SQLite read transaction; no writer or RPC is opened.',
        'Expiry checks describe the diagnostic read interval, not the first rejected emission attempt.',
        'Current outbox state is a durable emission marker, not a per-attempt timing trace.',
        'No full document bytes, credential/session records, signatures or bearer material are exported.']}

def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def key(kind,value):
    return kind+'/'+hashlib.sha256(b'RX-ENTITY-KEY-v1\n'+encoded(value)).hexdigest()

def authorize_id(operation):
    raw=bytearray(hashlib.sha256(b'RX-DELIVERY-ID-v1\n'+encoded([operation,'authorize'])).digest()[:16])
    raw[6]=(raw[6]&15)|0x80
    raw[8]=(raw[8]&63)|0x80
    return str(uuid.UUID(bytes=bytes(raw)))

def now():
    boot=str(uuid.UUID(Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
    return {'clock_id':'linux-boottime/'+boot,
            'ticks_ns':str(time.clock_gettime_ns(time.CLOCK_BOOTTIME))}

def ticks(point):
    if not isinstance(point,dict) or set(point)!= {'clock_id','ticks_ns'}:
        raise ValueError('stored clock shape differs')
    value=point['ticks_ns']
    if (not isinstance(point['clock_id'],str) or not isinstance(value,str)
            or not value.isascii() or not value.isdigit() or str(int(value))!=value
            or not 0<=int(value)<=18446744073709551615):
        raise ValueError('stored clock counter differs')
    return int(value)

def fail(message):
    raise ValueError(message)

total=0
cache={}
connection=None

def document(raw,expected):
    global total
    if not isinstance(raw,bytes) or len(raw)>1048576:
        fail('bounded stored document required')
    total+=len(raw)
    if total>8*1048576:
        fail('aggregate diagnostic document bound exceeded')
    value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!= {'schema','value'} or value['schema']!=expected:
        fail('stored P document schema differs')
    return {'schema':expected,'document_sha256':hashlib.sha256(raw).hexdigest(),
            'document_size_bytes':len(raw)},value['value']

def entity(kind,identity,schema):
    name=key(kind,identity)
    if name not in cache:
        row=connection.execute('SELECT key,revision,document FROM entities WHERE key=?',(name,)).fetchone()
        if row is None:
            cache[name]=({'present':False,'key':name},None)
        else:
            metadata,value=document(row[2],schema)
            metadata.update(present=True,key=row[0],revision=str(row[1]))
            cache[name]=(metadata,value)
    return cache[name]

def required(kind,identity,schema):
    metadata,value=entity(kind,identity,schema)
    if value is None:
        fail('required original '+kind+' record absent')
    return dict(metadata),value

def pick(value,names):
    return {name:value[name] for name in names}

def attention(message,host):
    metadata,value=entity('deliveryattention',message,'rx.internal.delivery-attention.v1')
    output=dict(metadata)
    if value is not None:
        if value.get('message')!=message or value.get('host')!=host:
            fail('delivery-attention identity differs')
        output['value']=pick(value,('message','host','issue'))
    return output

def outbox(message,kind,operation,host,permit,invocation):
    row=connection.execute('SELECT id,state,document FROM outbox WHERE id=?',(message,)).fetchone()
    if row is None:
        return {'present':False,'id':message,'expected_kind':kind}
    metadata,payload=document(row[2],'rx.internal.delivery.v1')
    if row[1] not in ('NEW','EMIT_ENTERED','VOIDED','DELIVERED'):
        fail('unsupported original outbox state')
    if (payload.get('kind')!=kind or payload.get('operation')!=operation
            or payload.get('host')!=host or payload.get('permit')!=permit):
        fail('original dispatch outbox payload identity differs')
    fields=['kind','operation','host','permit']
    if kind=='AUTHORIZE':
        if payload.get('invocation')!=invocation or invocation is None:
            fail('original authorization invocation differs')
        fields.append('invocation')
    metadata.update(present=True,id=row[0],state=row[1],value=pick(payload,fields),
        attempt_count=None,last_attempt_at=None,available_at=None,
        timing_status='NOT_RECORDED_IN_DATABASE',attention=attention(message,host))
    metadata['emission_marker']={
        'NEW':'NO_EMIT_ENTERED_CAS_RECORDED',
        'EMIT_ENTERED':'ORIGINAL_EMISSION_CAS_RECORDED_OUTCOME_NOT_INFERRED',
        'VOIDED':'VOIDED_BEFORE_EMISSION',
        'DELIVERED':'DELIVERY_RECEIPT_COMMITTED_NOT_NATIVE_COMPLETION',
    }[row[1]]
    return metadata

def inspect_operation(operation):
    work_meta,work=required('work',operation,'rx.internal.work.v1')
    if (work['operation']['operation_id']!=operation or work['cell']!=selected_cell
            or selected_run is not None and work['run']!=selected_run):
        fail('stored Work differs from original public selection')
    work_meta['value']=pick(work,('cell','run','part','host','permit','invocation','activation','slot','host_journal'))
    work_meta['value']['operation']=pick(work['operation'],('operation_id','revision','intent_digest','phase',
        'execution_knowledge','outcome','integrity','disposition','evidence_ids'))
    execution=work.get('execution')
    if execution is not None:
        # Only selection identity; neither parameters nor a replayable provider input is exported.
        work_meta['value']['execution_identity']={'operation':execution['operation'],'mandate':execution['mandate'],
            'selection':pick(execution['selection'],('run','part','node','ordinal','slot','slot_ordinal',
                'candidate','authority_generation','configuration_digest','intent_digest'))}
    permit_meta,permit=required('permit',work['permit'],'rx.internal.permit.v1')
    if (permit['id']!=work['permit'] or permit['operation']!=operation
            or permit['cell']!=work['cell'] or permit['host']!=work['host']
            or permit['intent_digest']!=work['operation']['intent_digest']
            or permit['state'] not in ('ISSUED','CONSUMED','VOIDED','EXPIRED')):
        fail('original Permit correlation/state differs')
    permit_meta['value']=pick(permit,('id','operation','intent_digest','cell','mandate','epoch','scopes',
        'host','host_boot','issued_at','expires_at','state','qualification','qualification_revision',
        'envelope_digest','purpose','condition_ids','condition_revision'))
    permit_meta['value']['grant']=pick(permit['grant'],('id','fence','valid_until','ttl_ms'))
    ticks(permit['issued_at']); ticks(permit['expires_at']); ticks(permit['grant']['valid_until'])
    run_meta,run=required('run',work['run'],'rx.internal.run.v1')
    if run['id']!=work['run'] or run['cell']!=work['cell']:
        fail('original Run correlation differs')
    run_meta['value']=pick(run,('id','cell','state','mandate','part_ids','recipe_digest','envelope_digest'))
    cell_meta,cell=required('cell',work['cell'],'rx.internal.cell.v1')
    if cell['configuration']['id']!=work['cell']:
        fail('current cell correlation differs')
    cell_meta['value']={'id':work['cell'],'epoch':cell['epoch'],'scope_epochs':cell['scope_epochs'],
        'configuration_limits':pick(cell['configuration'],('permit_ttl_ns','start_timeout_ns')),
        'mode':cell.get('mode'),'commissioning':cell.get('commissioning'),
        'blocks':[pick(block,('id','reason','latched','scopes')) for block in cell['blocks']],
        'qualification':None if cell['qualification'] is None else
            pick(cell['qualification'],('id','revision','envelope_digest'))}
    mandate_meta,mandate=required('mandate',permit['mandate'],'rx.internal.mandate.v1')
    if mandate['id']!=permit['mandate'] or mandate['run']!=work['run'] or mandate['cell']!=work['cell']:
        fail('original mandate correlation differs')
    mandate_meta['value']=pick(mandate,('id','run','cell','epoch','scopes','state'))
    same_clock=permit['expires_at']['clock_id']==report['read_started_at']['clock_id']
    at_start={'scope':'DIAGNOSTIC_READ_START_ONLY','state_not_issued':permit['state']!='ISSUED',
        'permit_state':permit['state'],'clock_mismatch':not same_clock,
        'expired':None if not same_clock else ticks(permit['expires_at'])<=ticks(report['read_started_at']),
        'remaining_ns':None if not same_clock else str(ticks(permit['expires_at'])-ticks(report['read_started_at'])),
        'issued_expiry_same_clock':permit['issued_at']['clock_id']==permit['expires_at']['clock_id'],
        'issued_to_expiry_ns':None if permit['issued_at']['clock_id']!=permit['expires_at']['clock_id']
            else str(ticks(permit['expires_at'])-ticks(permit['issued_at'])),
        'expiry_equals_grant_end':permit['expires_at']==permit['grant']['valid_until'],
        'grant_remaining_at_issue_ns':None if permit['issued_at']['clock_id']!=permit['grant']['valid_until']['clock_id']
            else str(ticks(permit['grant']['valid_until'])-ticks(permit['issued_at'])),
        'declared_permit_ttl_ns':cell['configuration']['permit_ttl_ns'],
        'cell_epoch_matches_permit':cell['epoch']==permit['epoch'],
        'cell_scopes_match_permit':cell['scope_epochs']==permit['scopes'],
        'run_mandate_matches_permit':run['mandate']==permit['mandate'],
        'mandate_active':mandate['state']=='ACTIVE'}
    return {'work':work_meta,'permit':permit_meta,'run':run_meta,'cell':cell_meta,'mandate':mandate_meta,
        'emission_checks_at_read':at_start,
        'prepare':outbox(operation,'PREPARE',operation,work['host'],work['permit'],work['invocation']),
        'authorize':outbox(authorize_id(operation),'AUTHORIZE',operation,work['host'],work['permit'],work['invocation'])}

def alarm(signum,frame):
    raise TimeoutError('read-only P diagnostic elapsed-time bound exceeded')

signal.signal(signal.SIGALRM,alarm)
signal.alarm(12)
try:
    directory=Path('/data/platform')
    info=directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or directory.resolve()!=directory:
        fail('owned real P data directory required')
    database=directory/'platform.db'
    info=database.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_size>256*1048576:
        fail('bounded owned existing P database required')
    connection=sqlite3.connect('file:/data/platform/platform.db?mode=ro',uri=True,timeout=1)
    connection.execute('PRAGMA query_only=ON')
    deadline=time.monotonic()+5
    connection.set_progress_handler(lambda: int(time.monotonic()>=deadline),1000)
    def authorize(action,arg1,arg2,database,trigger):
        if action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_TRANSACTION):
            return sqlite3.SQLITE_OK
        columns={'entities':('key','revision','document'),'outbox':('id','state','document')}
        if action==sqlite3.SQLITE_READ and arg1 in columns and arg2 in columns[arg1]:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    connection.set_authorizer(authorize)
    report['read_started_at']=now()
    connection.execute('BEGIN')
    for operation in operations:
        try:
            report['work'][operation]=inspect_operation(operation)
        except Exception as error:
            report['errors'].append({'inspection':'original operation '+operation,
                'error':type(error).__name__+': '+str(error)})
    connection.execute('ROLLBACK')
    report['read_finished_at']=now()
except Exception as error:
    report['errors'].append({'inspection':'read-only P entities/outbox',
        'error':type(error).__name__+': '+str(error)})
finally:
    if connection is not None:
        connection.close()
    signal.alarm(0)
if report['errors']:
    report['status']='PARTIAL'
print(json.dumps(report,sort_keys=True,separators=(',',':')))
'''


def preserve_platform_dispatch(site):
    """Persist diagnostic-only metadata and return errors without masking failure."""
    errors = []
    try:
        operations, sources, selection_errors = _original_operations(site)
        errors.extend(selection_errors)
        if not operations:
            result = {'schema': 'rx.m1-platform-dispatch-diagnostic.v1',
                'status': 'NO_PUBLIC_OPERATION_IDENTITIES', 'operations': [],
                'errors': selection_errors,
                'limitation': 'No public operation IDs available; absence does not prove no operation exists.'}
        elif 'p' not in getattr(site, 'services', {}):
            raise ValueError('owned P container is unavailable')
        else:
            raw = site.d.run('exec', site.services['p'], '/opt/rx/python/python', '-I', '-S', '-B',
                '-c', _READER, json.dumps(operations, separators=(',', ':')),
                site.cell, getattr(site, 'run', None) or '')
            if len(raw.encode()) > MAX_ARTIFACT_BYTES:
                raise ValueError('P diagnostic output exceeds artifact bound')
            result = json.loads(raw)
            if (result.get('schema') != 'rx.m1-platform-dispatch-diagnostic.v1'
                    or result.get('operations') != operations):
                raise ValueError('P diagnostic scope differs from original public operation selection')
            errors.extend(result.get('errors', []))
        result['selection_sources'] = sources
        save(Path(site.evidence) / 'platform-dispatch-diagnostics.json', result)
    except Exception as error:
        errors.append({'inspection': 'original P dispatch diagnostics',
                       'error': type(error).__name__ + ': ' + str(error)})
    if errors:
        try:
            save(Path(site.evidence) / 'platform-dispatch-diagnostics-errors.json', errors)
        except Exception as error:
            errors.append({'inspection': 'persist P diagnostic errors',
                           'error': type(error).__name__ + ': ' + str(error)})
    return errors
