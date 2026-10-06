#!/usr/bin/env python3
"""Artifact-only native-helper component checks. Not Host/P admission or a registered Run."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []


def clock():
    return {'clock_id':'linux-boottime/'+str(uuid.UUID(Path('/proc/sys/kernel/random/boot_id').read_text().strip())),
            'ticks_ns':str(time.clock_gettime_ns(time.CLOCK_BOOTTIME))}


def request(session):
    now=clock();operation=str(uuid.uuid4());invocation=str(uuid.uuid4())
    # Synthetic native channel only. This is not a P-issued authority or a valid Host selection.
    selection={'intent_digest':'51'*32,'fixture_scope':'native-helper-component-only'}
    envelope={'primitive':'count','values':{'increment':{'unit':'unitless','data':{'kind':'NUMBER','range':{'min':1,'max':1}}}}}
    dispatch={'operation':operation,'invocation':invocation,'device_session':session,
        'expires_at':{'clock_id':now['clock_id'],'ticks_ns':str(int(now['ticks_ns'])+30_000_000_000)},
        'input':{'binding':{'selection':selection},'parameters':list(encoded(envelope))}}
    return {'schema':'rx.external-process-channel.v1','challenge':str(uuid.uuid4()),'profile_digest':'62'*32,
            'device_session':session,'now':now,'dispatch':dispatch,'sources':['ready','done']}


def invoke(sdk,simulation,native,mode,value,log):
    result=subprocess.run([sys.executable,'-I','-S','-B',str(sdk/'counter.py'),'--simulation-dir',str(simulation),mode,str(native)],
        input=encoded(value),capture_output=True,timeout=20)
    log.with_suffix('.stdout').write_bytes(result.stdout);log.with_suffix('.stderr').write_bytes(result.stderr)
    return result.returncode,[json.loads(x) for x in result.stdout.splitlines()]


def expected_record(value):
    return {'schema':'rx.external-native-request.v1','dispatch':value['dispatch'],
            'profile_digest':value['profile_digest'],'dispatch_digest':hashlib.sha256(encoded(value['dispatch'])).hexdigest()}


def check_completion(value,frame,completed):
    dispatch=value['dispatch'];record=expected_record(value)
    expected={'schema':'rx.external-native-completion.v1','challenge':value['challenge'],
        'dispatch_digest':record['dispatch_digest'],'operation':dispatch['operation'],'invocation':dispatch['invocation'],
        'intent_digest':dispatch['input']['binding']['selection']['intent_digest'],
        'profile_digest':value['profile_digest'],'device_session':value['device_session']}
    if set(frame)!=set(expected)|{'capture','current'} or any(frame[k]!=v for k,v in expected.items()):
        raise ValueError('actual native completion correlation differs')
    capture=frame['capture']
    if completed:
        if not isinstance(capture,dict) or set(capture)!={'native_id','status_schema','status','captured_at','device_session'}:
            raise ValueError('completed native capture missing/different')
        if capture['native_id']!=dispatch['invocation'] or capture['device_session']!=value['device_session'] or capture['status_schema']!='m5.counter.completed.v1' or type(capture['status']) is not int or capture['status']!=0:
            raise ValueError('native capture identity/status differs')
    elif capture is not None:raise ValueError('pre-effect fault acquired unsupported completion')
    current=frame['current']
    for key in ('challenge','profile_digest','device_session'):
        if current[key]!=value[key]:raise ValueError('passive snapshot correlation differs')
    if current['schema']!='rx.external-native-snapshot.v1' or set(current['samples'])!=set(value['sources']):
        raise ValueError('passive snapshot declaration differs')
    return capture


def check_markers(value,entries,effects,completions,completed):
    expected={'operation':value['dispatch']['operation'],'invocation':value['dispatch']['invocation'],
              'selection':value['dispatch']['input']['binding']['selection']}
    if len(entries)!=1 or len(effects)!=int(completed) or len(completions)!=int(completed):
        raise ValueError('native marker/effect counts differ')
    for row in entries+effects+completions:
        if any(row.get(k)!=v for k,v in expected.items()) or 'acquired_at' not in row:
            raise ValueError('native marker/effect correlation differs')
    if completed and any(effects[0].get(k)!=v for k,v in {'primitive':'count','increment':1,'count_before':0,'count_after':1}.items()):
        raise ValueError('native increment facts differ')


def check_frames(value,first,fault):
    expected_entry={'schema':'rx.external-native-entry.v1','challenge':value['challenge'],
        'request_sha256':hashlib.sha256(encoded(value)).hexdigest(),'operation':value['dispatch']['operation'],
        'invocation':value['dispatch']['invocation'],'intent_digest':value['dispatch']['input']['binding']['selection']['intent_digest'],
        'profile_digest':value['profile_digest'],'device_session':value['device_session']}
    if not first or first[0]!=expected_entry:raise ValueError('native entry correlation differs')
    if len(first)!=(2 if fault=='none' else 1):raise ValueError('expected completion frame missing or unexpected frame emitted')
    if fault=='none':check_completion(value,first[1],True)


def run_case(sdk,root,fault):
    root.mkdir();simulation=root/'simulation';simulation.mkdir();native=root/'native';native.mkdir(mode=0o700)
    session=str(uuid.uuid4());(native/'device-session').write_text(session)
    (simulation/'fault.json').write_bytes(encoded({'mode':fault}))
    value=request(session);(root/'original-request.json').write_bytes(encoded(value))
    rc,first=invoke(sdk,simulation,native,'execute',value,root/'execute')
    expected_rc={'none':0,'after_entry_exit':31,'drop_completion':32}[fault]
    assert rc==expected_rc,(fault,rc)
    completed=fault!='after_entry_exit'
    check_frames(value,first,fault)
    operation=native/value['dispatch']['operation']
    if json.loads((operation/'request.json').read_bytes())!=expected_record(value):raise ValueError('immutable native original differs')
    if completed:
        fact=json.loads((operation/'completion.json').read_bytes())
        if set(fact)!={'schema','original','capture'} or fact['schema']!='rx.external-native-fact.v1' or fact['original']!=expected_record(value):
            raise ValueError('durable native completion belongs to different original')
    elif (operation/'completion.json').exists():raise ValueError('pre-effect fault has completion record')
    entry=rows(simulation/'entries.jsonl');effects=rows(simulation/'effects.jsonl');complete=rows(simulation/'completions.jsonl')
    check_markers(value,entry,effects,complete,completed)
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in simulation.iterdir() if p.is_file()}
    retry=copy.deepcopy(value);retry['challenge']=str(uuid.uuid4());retry['now']=clock()
    rc,lookup=invoke(sdk,simulation,native,'lookup',retry,root/'lookup-new-process')
    assert rc==0 and len(lookup)==1
    actual=lookup[0]
    capture=check_completion(retry,actual,completed)
    if completed and capture!=fact['capture']:raise ValueError('passive lookup did not return durable original capture')
    rc,_=invoke(sdk,simulation,native,'execute',retry,root/'duplicate-execute-refused')
    assert rc!=0,'duplicate Execute must not create another native entry'
    wrong=copy.deepcopy(retry);wrong['dispatch']['invocation']=str(uuid.uuid4())
    rc,_=invoke(sdk,simulation,native,'lookup',wrong,root/'wrong-invocation-refused');assert rc!=0
    passive=copy.deepcopy(retry);passive['dispatch']=None
    rc,snapshot=invoke(sdk,simulation,native,'observe',passive,root/'passive-observe');assert rc==0
    assert set(snapshot[0]['samples'])=={'ready','done'}
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in simulation.iterdir() if p.is_file()}
    assert before==after,'lookup/refusal/observation changed simulated native effects'
    return {'fault':fault,'operation':value['dispatch']['operation'],'invocation':value['dispatch']['invocation'],
        'entry_count':len(entry),'effect_count':len(effects),'completion_count':len(complete),
        'passive_original_lookup':True,'duplicate_execute_refused':True,'wrong_invocation_refused':True,
        'unchanged_native_facts':before,'status':'PASS_FOR_COMPONENT_SCOPE'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sdk',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--execute-fresh-linux-ci',action='store_true')
    a=parser.parse_args()
    if not a.execute_fresh_linux_ci or sys.platform!='linux' or os.environ.get('CI')!='true':
        parser.error('execution requires explicit fresh Linux CI; do not run in preserved CP2 environment')
    sdk=a.sdk.resolve(strict=True);a.output.mkdir(parents=True,exist_ok=False)
    for name in ('rx_external_adapter.py','counter.py'):
        if (sdk/name).is_symlink() or not (sdk/name).is_file():raise ValueError('regular released SDK inputs required')
    before={name:hashlib.sha256((sdk/name).read_bytes()).hexdigest() for name in ('rx_external_adapter.py','counter.py')}
    result={'schema':'rx.m5.external-helper-conformance.v1','scope':'native helper component only; no authority, Host gate, registered Run or physical qualification',
            'sdk_sha256':before,'cases':[run_case(sdk,a.output/mode,mode) for mode in ('none','after_entry_exit','drop_completion')]}
    assert before=={name:hashlib.sha256((sdk/name).read_bytes()).hexdigest() for name in before}
    result['status']='PASS_FOR_COMPONENT_SCOPE';(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'cases':len(result['cases'])}))


if __name__=='__main__':main()
