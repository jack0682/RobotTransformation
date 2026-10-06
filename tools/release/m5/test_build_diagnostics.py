import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_diagnostics as d
import build_distribution_candidate as builder
import build_sdk_artifacts as sdk
import publish_ci_evidence as publisher

HERE=Path(__file__).resolve().parent
VOCAB={'schema':d.VOCAB_SCHEMA,'commit':'a'*40,'files':[
    {'path':'rx-solutions/runtime/rx-host/tests/external_process.rs','lines':80,'functions':{'native_case':[12]}},
    {'path':'rx-solutions/native/executor/CMakeLists.txt','lines':40,'functions':{}},
    {'path':'tools/release/m5/build_sdk_artifacts.py','lines':800,'functions':{}}]}
SECRET='PRIVATE_FIXTURE_CANARY_012345678901234567890123456789'
RESOURCE={'disk_total_bytes':1000000,'disk_free_bytes':500000,'memory_total_bytes':None,'memory_available_bytes':None}

class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def report(self,text='unclassified '+SECRET):
        log=self.root/'private.log';log.write_text(text)
        with patch.object(d,'resources',return_value=RESOURCE):return d.make_report(VOCAB,'DISTRIBUTION_BUILD','solutions',1,[('stderr',log)],self.root)
    def test_only_known_source_locations_and_codes_survive(self):
        value=self.report('error[E0425]: '+SECRET+'\n#8 3.4 --> runtime/rx-host/tests/external_process.rs:20:7\nFile "/private/'+SECRET+'", line 1\n')
        public=d.render_report(value,VOCAB);text=json.dumps(public)
        self.assertNotIn(SECRET,text);self.assertIn('E0425',text);self.assertIn('external_process.rs',text)
        self.assertEqual(public['events'][-1]['line'],20)
    def test_test_name_is_mapped_to_public_declaration(self):
        value=self.report('test nested::native_case ... FAILED\ntest '+SECRET+' ... FAILED\n')
        self.assertEqual(value['events'],[d.event('TEST_FAILED',None,0,12),d.event('TEST_FAILED')])
    def test_unknown_paths_and_out_of_range_lines_are_omitted(self):
        value=self.report('--> runtime/rx-host/tests/external_process.rs:9999:1\n--> /private/'+SECRET+':4:8')
        self.assertEqual(value['events'],[d.event('UNCLASSIFIED')])
    def test_python_and_cmake_locations_are_bounded(self):
        text='File "/home/runner/source/tools/release/m5/build_sdk_artifacts.py", line 400\n#2 1.0 CMake Error at /executor/CMakeLists.txt:20 (project): '+SECRET
        value=self.report(text);locations={(e['file'],e['line']) for e in value['events'] if e['file'] is not None}
        self.assertEqual(locations,{(2,400),(1,20)});self.assertNotIn(SECRET,json.dumps(value))
    def test_signal_and_exit137_are_not_oom_proof(self):
        value=self.report('signal: 9, SIGKILL\nexit code: 137\n')
        self.assertEqual({e['kind'] for e in value['events']},{'SIGKILL_MESSAGE','CHILD_EXIT_137'})
        self.assertEqual(value['resource_scope'],'POST_COMMAND_SNAPSHOT_NOT_PEAK_OR_OOM_PROOF')
        self.assertNotIn('OOM',json.dumps(value['events']))
    def test_public_schema_rejects_raw_text_hash_and_invalid_types(self):
        original=self.report()
        for mutate in [lambda v:v.update(raw=SECRET),lambda v:v['logs'][0].update(sha256='a'*64),
            lambda v:v['events'][0].update(message=SECRET),lambda v:v.update(returncode=0),
            lambda v:v.update(returncode=True),lambda v:v['resources'].update(token=SECRET),
            lambda v:v['events'][0].update(file=0,line=999),lambda v:v.update(source_commit='b'*40)]:
            value=copy.deepcopy(original);mutate(value)
            with self.assertRaises(ValueError):d.validate_report(value,VOCAB)
    def test_forged_sidecar_cannot_inject_opaque_fields(self):
        nested=self.report();nested['events'][0]['message']=SECRET
        value=self.report(d.PREFIX+json.dumps(nested))
        self.assertNotIn(SECRET,json.dumps(value));self.assertEqual(value['events'],[d.event('UNCLASSIFIED')])
    def test_line_and_log_bounds_do_not_echo_content(self):
        value=self.report('x'*17000+SECRET)
        self.assertEqual(value['events'],[d.event('LOG_BOUND')]);self.assertNotIn(SECRET,json.dumps(value))
        with patch.object(d,'MAX_LOG',1):value=self.report(SECRET)
        self.assertEqual(value['events'],[d.event('LOG_BOUND')])
    def test_raw_log_hash_stays_in_private_receipt(self):
        log=self.root/'raw';log.write_text(SECRET);path=self.root/'closed-failure.json'
        with patch.object(d,'resources',return_value=RESOURCE):value=d.save_failure(path,VOCAB,'SDK_BUILD','sdk',1,[('stderr',log)],self.root)
        fingerprint=hashlib.sha256(SECRET.encode()).hexdigest()
        self.assertNotIn(fingerprint,path.read_text());self.assertNotIn(SECRET,path.read_text())
        private=self.root/'private-build-diagnostics/raw-log-hashes.json';self.assertIn(fingerprint,private.read_text())
    def test_sidecar_failure_is_always_nonzero_and_redacted(self):
        vocab=self.root/'vocab.json';vocab.write_text(json.dumps(VOCAB));log=self.root/'raw';log.write_text(SECRET)
        with patch('sys.argv',['diag','--vocabulary',str(vocab),'--log',str(log),'--returncode','101']),patch('sys.stdout',new_callable=io.StringIO) as output:
            with self.assertRaises(SystemExit) as error:d.main()
            self.assertEqual(error.exception.code,1);self.assertNotIn(SECRET,output.getvalue())
    def test_early_projection_cannot_copy_raw_logs_or_artifacts(self):
        work=self.root/'m5-dist-work';work.mkdir();value=self.report()
        (work/'closed-failure.json').write_text(json.dumps(value));(work/'raw.stderr').write_text(SECRET)
        out=self.root/'approved'
        with patch.object(d,'vocabulary',return_value=VOCAB):self.assertTrue(publisher.publish_early_failure(self.root,out,self.root,'a'*40))
        files={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
        self.assertEqual(files,{'LEAK_AUDIT.json','evidence/diagnostics/closed-build-failure.json'})
        for path in out.rglob('*'):
            if path.is_file():self.assertNotIn(SECRET,path.read_text())
        self.assertEqual(json.loads((out/'LEAK_AUDIT.json').read_text())['status'],'PUBLIC_EVIDENCE_REFUSED')
    def test_any_acceptance_phase_trace_disables_early_path(self):
        for name in ('m5-local-work','m5-local-sim'):
            trace=self.root/name;trace.symlink_to(self.root/'absent')
            with patch.object(d,'vocabulary') as vocab:self.assertFalse(publisher.publish_early_failure(self.root,self.root/'out',self.root,'a'*40));vocab.assert_not_called()
            trace.unlink();trace.mkdir()
            self.assertFalse(publisher.publish_early_failure(self.root,self.root/'out',self.root,'a'*40));trace.rmdir()
    def test_invalid_early_receipt_never_creates_approved_output(self):
        work=self.root/'m5-dist-work';work.mkdir();value=self.report();value['events'][0]['message']=SECRET
        (work/'closed-failure.json').write_text(json.dumps(value));out=self.root/'approved'
        with patch.object(d,'vocabulary',return_value=VOCAB),self.assertRaises(ValueError):publisher.publish_early_failure(self.root,out,self.root,'a'*40)
        self.assertFalse(out.exists())
    def test_docker_recipe_retains_original_failure_and_source_boundary(self):
        runtime='FROM rust AS p-build\nWORKDIR /source\nFROM rust AS s-build\nRUN apt-get update\n'
        runtime+='RUN '+ ' && \\\n    '.join('cargo test --locked -p rx-host > /out/'+name for name in ['external-process.log','host-recovery.log','executor-recovery.log','executor-identity.log'])+'\n'
        bounded=builder.bounded_recipe(runtime,'','fixture');result=builder.diagnostic_recipe(bounded)
        self.assertEqual(result.count('exit "$rc"'),4);self.assertEqual(result.count(' || { rc=$?;'),4)
        self.assertIn('COPY --from=m5_diagnostics / /opt/m5-diagnostics/',result)
        self.assertNotIn('COPY --from=m5_diagnostics / /source',result)
        self.assertNotIn('cat /out/',result)
    def test_wrong_head_and_dirty_public_source_are_not_relabelled(self):
        with patch.object(d.subprocess,'check_output',return_value=b'b'*40+b'\n'):
            with self.assertRaises(ValueError):d.vocabulary(self.root,'a'*40)
        code=self.root/'rx-solutions/lib.rs';code.parent.mkdir();code.write_bytes(b'private changed bytes')
        expected=b'fn public_test() {}\n';oid=hashlib.sha1(b'blob '+str(len(expected)).encode()+b'\0'+expected).hexdigest()
        tree=('100644 blob '+oid+'\trx-solutions/lib.rs\0').encode()
        with patch.object(d.subprocess,'check_output',side_effect=[b'a'*40+b'\n',tree]):
            with self.assertRaises(ValueError):d.vocabulary(self.root,'a'*40)

    def test_early_main_never_copies_raw_stage_and_preserves_failure(self):
        work=self.root/'m5-dist-work';work.mkdir();(work/'closed-failure.json').write_text(json.dumps(self.report()))
        out=self.root/'approved'
        argv=['publisher','--mode','producer','--runner-temp',str(self.root),'--output',str(out),'--repo',str(self.root),'--candidate','a'*40]
        with patch('sys.argv',argv),patch.object(d,'vocabulary',return_value=VOCAB),patch.object(publisher,'include_files',side_effect=AssertionError('raw stage copy entered')):
            with self.assertRaises(SystemExit):publisher.main()
        self.assertFalse((self.root/'m5-producer-publication-inputs').exists())
        self.assertTrue((out/'evidence/diagnostics/closed-build-failure.json').is_file())

    def test_invalid_candidate_early_main_refuses_without_raw_fallback(self):
        work=self.root/'m5-dist-work';work.mkdir();(work/'closed-failure.json').write_text(json.dumps(self.report()))
        out=self.root/'approved'
        argv=['publisher','--mode','producer','--runner-temp',str(self.root),'--output',str(out),'--repo',str(self.root),'--candidate','b'*40]
        with patch('sys.argv',argv),patch.object(d,'vocabulary',side_effect=ValueError('CLOSED_DIAGNOSTIC_INVALID')),patch.object(publisher,'include_files',side_effect=AssertionError('raw stage copy entered')):
            with self.assertRaises(SystemExit):publisher.main()
        self.assertEqual({p.name for p in out.iterdir()},{'LEAK_AUDIT.json'})

    def test_ambiguous_function_name_does_not_invent_a_test_location(self):
        vocab=copy.deepcopy(VOCAB);vocab['files'][1]['functions']={'native_case':[5]}
        events=d.parse_text('test nested::native_case ... FAILED',vocab,'solutions')
        self.assertEqual(events,[d.event('TEST_FAILED')])

    def test_sdk_failure_uses_only_initial_verified_vocabulary(self):
        runner=type('Runner',(),{})();runner.work=self.root;runner.commands=[];runner.logs=self.root
        with patch.object(sdk,'vocabulary',side_effect=AssertionError('must not reread changed HEAD')):
            sdk.record_closed_sdk_failure(runner,None)
            self.assertFalse((self.root/'closed-failure.json').exists())
            try:raise ValueError(SECRET)
            except ValueError:sdk.record_closed_sdk_failure(runner,VOCAB)
        self.assertTrue((self.root/'closed-failure.json').is_file())
        self.assertNotIn(SECRET,(self.root/'closed-failure.json').read_text())

    def test_preexisting_output_has_no_readiness_and_is_untouched(self):
        work=self.root/'m5-dist-work';work.mkdir();(work/'closed-failure.json').write_text(json.dumps(self.report()))
        out=self.root/'approved';out.mkdir();(out/'unapproved').write_text(SECRET);github=self.root/'step-output'
        argv=['publisher','--mode','producer','--runner-temp',str(self.root),'--output',str(out),'--repo',str(self.root),'--candidate','a'*40]
        with patch('sys.argv',argv),patch.dict(os.environ,{'GITHUB_OUTPUT':str(github)}),patch.object(d,'vocabulary',return_value=VOCAB),patch.object(publisher,'include_files',side_effect=AssertionError('raw stage copy entered')):
            with self.assertRaises(SystemExit):publisher.main()
        self.assertFalse(github.exists());self.assertEqual((out/'unapproved').read_text(),SECRET)
        self.assertEqual({p.name for p in out.iterdir()},{'unapproved'})

    def test_output_symlink_is_not_resolved_or_mutated(self):
        out=self.root/'approved';target=self.root/'foreign';target.mkdir();(target/'keep').write_text(SECRET);out.symlink_to(target)
        github=self.root/'step-output'
        argv=['publisher','--mode','producer','--runner-temp',str(self.root),'--output',str(out),'--repo',str(self.root),'--candidate','a'*40]
        with patch('sys.argv',argv),patch.dict(os.environ,{'GITHUB_OUTPUT':str(github)}),patch.object(d,'vocabulary',return_value=VOCAB):
            with self.assertRaises(SystemExit):publisher.main()
        self.assertFalse(github.exists());self.assertEqual({p.name for p in target.iterdir()},{'keep'})

    def test_fresh_closed_projection_has_readiness_but_still_fails(self):
        work=self.root/'m5-dist-work';work.mkdir();(work/'closed-failure.json').write_text(json.dumps(self.report()))
        out=self.root/'approved';github=self.root/'step-output'
        argv=['publisher','--mode','producer','--runner-temp',str(self.root),'--output',str(out),'--repo',str(self.root),'--candidate','a'*40]
        with patch('sys.argv',argv),patch.dict(os.environ,{'GITHUB_OUTPUT':str(github)}),patch.object(d,'vocabulary',return_value=VOCAB):
            with self.assertRaises(SystemExit):publisher.main()
        self.assertEqual(github.read_text(),'m5_publication_ready=true\n')
        self.assertFalse((out/'evidence/artifacts').exists())

    def test_unknown_recipe_fails_closed(self):
        with self.assertRaises(ValueError):builder.diagnostic_recipe('unrecognized')

if __name__=='__main__':unittest.main()
