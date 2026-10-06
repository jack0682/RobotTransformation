"""Pure unit checks only. These do not claim installed-product Run acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid
from fixtures import (fresh_definitions,execution_target,assert_success,assert_unknown_held,encoded,accepted_start,assert_native_snapshot,pin)
from infrastructure import Author,PublicApi,owned_docker_type,installed_materials_type,mutation_targets


def receipt(unknown=False):
    operation='11111111-1111-4111-8111-111111111111';invocation='22222222-2222-4222-8222-222222222222'
    run='33333333-3333-4333-8333-333333333333';selection={'node':'count','parameter':{'sha256':'a'*64}}
    value={'environment':'SIMULATION','binding':{'run':run},'result':{'details_truncated':False,
        'current_binding_matches':True,'run':{'value':{'id':run,'state':'RECOVERY_REQUIRED' if unknown else 'COMPLETED','part_ids':['part-one']}},'parts':[{'value':{'id':'part-one','run':run,'ordinal':'1','disposition':'IN_PROGRESS' if unknown else 'CONFIRMED_COMPLETED'}}],
        'work':[{'part':'part-one','invocation':invocation,'execution':{'selection':selection},'operation':{
            'operation_id':operation,'integrity':'VALID','execution_knowledge':'UNKNOWN' if unknown else 'ENDED',
            'phase':'RECONCILING' if unknown else 'SETTLED','outcome':'NONE' if unknown else 'SUCCEEDED',
            'disposition':'QUARANTINED' if unknown else 'RELEASED'},
            'resources':[{'value':{'id':'controller/simulation','holder':operation if unknown else None}}]}]}}
    effect={'operation':operation,'invocation':invocation,'selection':selection,'increment':1,'count_before':0,'count_after':1}
    return value,effect


class AcceptanceTests(unittest.TestCase):
    def test_success_requires_original_effect_and_release(self):
        result,effect=receipt();assert_success(result,[effect])
        for field,value in [('operation','another'),('invocation','another'),('selection',{})]:
            altered=dict(effect,**{field:value})
            with self.assertRaises(AssertionError):assert_success(result,[altered])
        for count in [[],[effect,effect]]:
            with self.assertRaises(AssertionError):assert_success(result,count)
        result['result']['work'][0]['resources'][0]['value']['holder']='still-held'
        with self.assertRaises(AssertionError):assert_success(result,[effect])

    def test_success_refuses_foreign_part_or_membership(self):
        for mutant in ['id','run','ordinal','membership','work-part']:
            result,effect=receipt()
            if mutant in ['id','run','ordinal']:result['result']['parts'][0]['value'][mutant]='foreign'
            elif mutant=='membership':result['result']['run']['value']['part_ids']=['foreign']
            else:result['result']['work'][0]['part']='foreign'
            with self.subTest(mutant=mutant),self.assertRaises(AssertionError):assert_success(result,[effect])

    def test_unknown_does_not_need_a_native_effect(self):
        before,effect=receipt(True);current=copy.deepcopy(before)
        assert_unknown_held(current,before,[],0)
        assert_unknown_held(current,before,[effect],1)
        with self.assertRaises(AssertionError):assert_unknown_held(current,before,[effect],0)

    def test_false_unknown_promotion_rejected(self):
        before,_=receipt(True)
        for mutation in ['release','settle','identity','empty-resources','completed-part','empty-parts','resource-swap','run-completed','known-terminal','part-swap']:
            current=copy.deepcopy(before);work=current['result']['work'][0]
            if mutation=='release':work['resources'][0]['value']['holder']=None
            elif mutation=='settle':work['operation']['execution_knowledge']='ENDED'
            elif mutation=='identity':work['invocation']='new'
            elif mutation=='empty-resources':work['resources']=[]
            elif mutation=='empty-parts':current['result']['parts']=[]
            elif mutation=='resource-swap':work['resources'][0]['value']['id']='another-resource'
            elif mutation=='run-completed':current['result']['run']['value']['state']='COMPLETED'
            elif mutation=='known-terminal':work['operation'].update(phase='SETTLED',outcome='SUCCEEDED',integrity='DISPUTED')
            elif mutation=='part-swap':current['result']['parts'][0]['value']['id']='another-part'
            else:current['result']['parts'][0]['value']['disposition']='CONFIRMED_COMPLETED'
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):assert_unknown_held(current,before,[],0)

    def test_nonterminal_start_exit_two_is_a_receipt_not_retry_trigger(self):
        body={'schema':'rx.execution-cli-receipt.v2','request_id':'original',
              'binding':{'run':'same-run'},'start_attempt':'same-attempt'}
        self.assertEqual(accepted_start(json.dumps(body),2,'original','same-run'),body)
        for code in [1,125,137]:
            with self.assertRaises(ValueError):accepted_start(json.dumps(body),code,'original','same-run')
        with self.assertRaises(ValueError):accepted_start(json.dumps(body),2,'replacement','same-run')

    def test_physical_and_truncated_are_not_accepted(self):
        for mutation in ['physical','truncated','new-run','multiple-work','incomplete','stale','disputed']:
            result,effect=receipt()
            if mutation=='physical':result['environment']='PHYSICAL'
            elif mutation=='truncated':result['result']['details_truncated']=True
            elif mutation=='new-run':result['binding']['run']='different'
            elif mutation=='incomplete':result['result']['run']['value']['state']='EXECUTING'
            elif mutation=='stale':result['result']['current_binding_matches']=False
            elif mutation=='disputed':result['result']['work'][0]['operation']['integrity']='DISPUTED'
            else:result['result']['work']*=2
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):assert_success(result,[effect])


class NativeFactsTests(unittest.TestCase):
    def data(self,has_completion=True):
        result,_=receipt();work=result['result']['work'][0]
        profile='d'*64;program='e'*64;session='44444444-4444-4444-8444-444444444444'
        parameters=encoded({'primitive':'count','values':{'increment':1}})
        work['operation']['intent_digest']='f'*64
        work['execution']['selection'].update(intent_digest='f'*64,parameter=pin(parameters,'rx.workflow-parameters.v2'))
        template={'profile_digest':profile,'completion_rule':'m5.counter.completed.v1','resource_set':['controller/simulation'],
                  'body':{'program':{'program':{'sha256':program},'parameter_set':{'placeholder':True}}}}
        intent=copy.deepcopy(template);intent['body']['program']['parameter_set']=work['execution']['selection']['parameter']
        dispatch={'operation':work['operation']['operation_id'],'invocation':work['invocation'],'device_session':session,
            'intent':intent,'input':{'binding':work['execution'],'parameters':list(parameters)},
            'admitted_at':{'clock_id':'test','ticks_ns':'1'},'expires_at':{'clock_id':'test','ticks_ns':'2'}}
        request={'schema':'rx.external-native-request.v1','profile_digest':profile,'dispatch':dispatch,
                 'dispatch_digest':__import__('hashlib').sha256(encoded(dispatch)).hexdigest()}
        documents={'installation':encoded({'native':{'kind':'EXTERNAL_PROCESS','program_digest':program,'device_session':session}}),
                   'device_session':session.encode(),'request':encoded(request)}
        if has_completion:documents['completion']=encoded({'schema':'rx.external-native-fact.v1','original':request,
            'capture':{'native_id':work['invocation'],'device_session':session,'status_schema':template['completion_rule'],'status':0}})
        snapshot={'files':{k:{'raw_hex':v.hex(),'sha256':__import__('hashlib').sha256(v).hexdigest(),'bytes':len(v)} for k,v in documents.items()}}
        return snapshot,work,profile,program,template

    def test_immutable_full_tuple_and_completion_identity(self):
        for present in [True,False]:
            data=self.data(present);verified=assert_native_snapshot(*data,present)
            self.assertIn('dispatch_digest',verified)
        original=self.data()
        for mutant in ['profile','session','dispatch','parameters','completion-original','completion-native','completion-missing','resource']:
            snapshot,work,profile,program,template=copy.deepcopy(original)
            if mutant=='completion-missing':del snapshot['files']['completion']
            elif mutant=='resource':work['resources'][0]['value']['id']='other'
            else:
                key='completion' if mutant.startswith('completion') else 'request'
                document=json.loads(bytes.fromhex(snapshot['files'][key]['raw_hex']))
                if mutant=='profile':document['profile_digest']='0'*64
                elif mutant=='session':document['dispatch']['device_session']='55555555-5555-4555-8555-555555555555'
                elif mutant=='dispatch':document['dispatch_digest']='0'*64
                elif mutant=='parameters':document['dispatch']['input']['parameters']=[123,125]
                elif mutant=='completion-original':document['original']['profile_digest']='0'*64
                else:document['capture']['native_id']='another'
                raw=encoded(document);snapshot['files'][key]={'raw_hex':raw.hex(),'sha256':__import__('hashlib').sha256(raw).hexdigest(),'bytes':len(raw)}
            with self.subTest(mutant=mutant),self.assertRaises(AssertionError):assert_native_snapshot(snapshot,work,profile,program,template,True)

    def test_normal_wait_observes_all_final_conditions(self):
        import run_registered_counter as runner
        early,effect=receipt();early['result']['run']['value']['state']='EXECUTING'
        final,_=receipt();samples=iter([early,final]);calls=[]
        def inspect():calls.append(1);return next(samples)
        with patch.object(runner,'effects',return_value=[effect]),patch.object(runner,'native_boundaries',return_value={'actual':True}),patch.object(runner.time,'sleep'):
            value=runner.wait_complete({},inspect,final['binding']['run'])
        self.assertEqual(value[0],final);self.assertEqual(len(calls),2)

    def test_normal_wait_retains_last_failure_on_timeout(self):
        import run_registered_counter as runner
        early,effect=receipt();early['result']['run']['value']['state']='EXECUTING'
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            with patch.object(runner,'effects',return_value=[effect]),patch.object(runner.time,'sleep'),patch.object(runner.time,'monotonic',side_effect=[0,0,2]):
                with self.assertRaises(RuntimeError):runner.wait_complete({'evidence':Path(folder)},lambda:early,early['binding']['run'],1)
            self.assertEqual(json.loads((Path(folder)/'normal-wait-timeout.json').read_bytes())['receipt'],early)


class AuthorInputsTests(unittest.TestCase):
    def test_fresh_exact_one_node_closed_references(self):
        contract={'implementation':'m5.counter','version':'1.0.0'}
        first,workflow=fresh_definitions(str(uuid.uuid4()),contract)
        second,_=fresh_definitions(first['catalog'],contract)
        self.assertFalse({r['id'] for r in first['definitions']} & {r['id'] for r in second['definitions']})
        keys={r['key'] for r in first['definitions']}
        def check(value):
            if isinstance(value,dict):
                if set(value)=={'$ref'}:self.assertIn(value['$ref'],keys)
                else:
                    for v in value.values():check(v)
            elif isinstance(value,list):
                for v in value:check(v)
        check(first);check(workflow)
        self.assertEqual(workflow['spec']['steps'],[{'id':'count','task':'count'}])
        task=workflow['spec']['tasks']['count']
        self.assertEqual(task['properties']['increment']['default']['data']['range'],{'min':1,'max':1})
        self.assertEqual(task['on_unknown'],'HOLD_AND_RECONCILE')

    def test_target_uses_compiler_node_identity(self):
        initial={'steps':[{'host':'host/sim','intent':{'original':True},'id':'step/count'}]}
        resolved={'root':{'id':'flow/main/sequence','body':{'kind':'SEQUENCE','children':[
            {'id':'flow/main/skill/1','body':{'kind':'OPERATION','binding':'skill/1'}}]}},
            'bindings':{'skill/1':{'host':'host/sim','intent':{'original':True}}}}
        target,plan=execution_target(initial,resolved,{'reference':{'id':'publication'},'policy':{'sha256':'p'}})
        self.assertEqual(target['execution']['nodes'],{'flow/main/skill/1':'count'})
        self.assertEqual(target['steps'][0]['id'],'flow/main/skill/1')
        resolved['bindings']['skill/1']['intent']={'changed':True}
        with self.assertRaises(ValueError):execution_target(initial,resolved,{'reference':{},'policy':{}})

    def test_multiple_nodes_refused(self):
        resolved={'root':{'body':{'kind':'SEQUENCE','children':[{},{}]}}}
        with self.assertRaises(ValueError):execution_target({'steps':[]},resolved,{'reference':{},'policy':{}})


class TransportTests(unittest.TestCase):
    def test_original_api_request_survives_recover(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            calls=[]
            author=SimpleNamespace(root=Path(folder),cp=lambda p:'/author/'+p,
                cli=lambda *args: calls.append(args) or SimpleNamespace(returncode=0,stdout='{"id":"same"}',stderr=''))
            api=PublicApi(author,'operator',RuntimeError)
            api.mutate('start','/api/v1/runs/start',{'run':'same'})
            first=json.loads((Path(folder)/'requests/operator/start.json').read_bytes())
            api.recover('start')
            self.assertEqual(calls[0][1],calls[1][1])
            self.assertEqual(first,json.loads((Path(folder)/'requests/operator/start.json').read_bytes()))
            with self.assertRaises(ValueError):api.mutate('start','/api/v1/runs/start',{'run':'new'})

    def test_unowned_container_mutation_refused(self):
        class Base:
            def run(self,*args,**kwargs):return args
        docker=owned_docker_type(Base)();docker.prefix='fresh';docker.containers=['fresh-host'];docker.volumes=[]
        self.assertEqual(docker.run('stop','fresh-host'),('stop','fresh-host'))
        for name in ['rx-f2-s1d-hb','old-host','fresh-not-owned']:
            with self.assertRaises(ValueError):docker.run('stop',name)
        attacks=[('stop','fresh-host','foreign'),('kill','--signal','KILL','fresh-host','rx-f2-s1d-hb'),
                 ('rm','fresh-host','foreign'),('restart','fresh-host','--time','10','foreign'),
                 ('stop','--unexpected-option','fresh-host'),('exec','--unknown','fresh-host','cat'),
                 ('start','fresh-host','--','foreign')]
        for args in attacks:
            with self.subTest(args=args),self.assertRaises(ValueError):docker.run(*args)
        self.assertEqual(docker.run('exec','fresh-host','printf','foreign'),('exec','fresh-host','printf','foreign'))
        self.assertEqual(mutation_targets('kill',['--signal=KILL','fresh-host']),['fresh-host'])
        self.assertEqual(mutation_targets('exec',['--user','10001:10001','fresh-host','sh','-c','echo foreign']),['fresh-host'])

    def test_actual_author_mount_and_image_boundary(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root=Path(folder);workspace=root/'author';workspace.mkdir();terminal=root/'terminal';terminal.mkdir();logs=root/'logs';logs.mkdir()
            state={'Image':'sha256:candidate','HostConfig':{'ReadonlyRootfs':True},
                'Mounts':[{'Type':'bind','Destination':'/author','Source':str(workspace),'RW':True}]}
            docker=SimpleNamespace(prefix='fresh',containers=[],run=lambda *a:None,state=lambda n:copy.deepcopy(state))
            author=Author(docker,'sha256:candidate',workspace,terminal,logs)
            with patch('infrastructure.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='{}',stderr='')) as launch:
                author.command('python3',['-c','print(1)'],'good')
                launch.assert_called_once()
            for corruption in ['foreign-image','signer-mount','writable-root']:
                broken=copy.deepcopy(state)
                if corruption=='foreign-image':broken['Image']='sha256:other'
                elif corruption=='signer-mount':broken['Mounts'].append({'Type':'bind','Destination':'/signer','Source':'/private','RW':False})
                else:broken['HostConfig']['ReadonlyRootfs']=False
                docker.state=lambda n:broken
                with patch('infrastructure.subprocess.run') as launch:
                    with self.assertRaises(ValueError):author.command('python3',[],corruption)
                    launch.assert_not_called()

    def test_historical_overlay_is_exactly_one_readonly_nested_bind(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root=Path(folder).resolve();workspace=root/'author';workspace.mkdir();terminal=root/'terminal';terminal.mkdir();logs=root/'logs';logs.mkdir()
            old=root/'historical/client';old.mkdir(parents=True)
            state={'Image':'sha256:candidate','HostConfig':{'ReadonlyRootfs':True},'Mounts':[
                {'Type':'bind','Destination':'/author','Source':str(workspace),'RW':True},
                {'Type':'bind','Destination':'/terminal','Source':str(terminal),'RW':False},
                {'Type':'bind','Destination':'/author/historical-client','Source':str(old),'RW':False}]}
            commands=[];docker=SimpleNamespace(prefix='fresh',containers=[],run=lambda *a:commands.append(a),state=lambda n:copy.deepcopy(state))
            author=Author(docker,'sha256:candidate',workspace,terminal,logs)
            with patch('historical_bundle.validate_historical_bundle',return_value={'client_files':{'rx':'fixture'}}),patch('infrastructure.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='{}',stderr='')):
                author.command('python3',['-E','-s','-B','probe'],'historical',network=True,historical_client=old)
                self.assertIn(str(old)+':/author/historical-client:ro',commands[0])
                state['Mounts'][2]['RW']=True
                with self.assertRaises(ValueError):author.command('python3',[],'bad-overlay',network=True,historical_client=old)

    def test_exporter_refuses_external_paths_before_subprocess(self):
        class Base:pass
        material=installed_materials_type(Base)();material.temporary=Path('/new');material.platform='candidate'
        with patch('infrastructure.subprocess.run') as run:
            with self.assertRaises(ValueError):material.exporter('export_delivery_final',{'RX_CELL_DELIVERY_SEED':'/frozen/cp2'},'wrong')
            run.assert_not_called()


if __name__=='__main__':unittest.main()
