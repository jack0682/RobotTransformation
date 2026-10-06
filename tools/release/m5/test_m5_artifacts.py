import io
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import artifacts
import build_distribution_candidate as distro
import consume_sdk_artifacts as consumer
import consume_runtime_artifacts as runtime
import verify_release_provenance as provenance

_spec=importlib.util.spec_from_file_location('component_conformance',Path(__file__).parent/'sdk/external-adapter/conformance.py')
component=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(component)

ROOT=Path(__file__).resolve().parent
TEMP=ROOT/'.test-work'

class Fixture(unittest.TestCase):
    def setUp(self):
        TEMP.mkdir(exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=TEMP);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def archive(self,entries):
        out=self.root/'input.tar'
        with tarfile.open(out,'w') as stream:
            for name,kind,payload in entries:
                item=tarfile.TarInfo(name);item.mode=0o644
                if kind=='file':item.size=len(payload);stream.addfile(item,io.BytesIO(payload))
                else:item.type=kind;item.linkname=payload;stream.addfile(item)
        return out
    def test_traversal_archive(self):
        for name in ['../outside','/root/x','sdk/../x','sdk/.git/config','sdk/a\\b','sdk//x']:
            with self.subTest(name=name):
                file=self.archive([(name,'file',b'x')])
                with self.assertRaises(ValueError):artifacts.validate_tar(file)
    def test_duplicate_archive(self):
        file=self.archive([('sdk/a','file',b'x'),('sdk/a','file',b'x')])
        with self.assertRaisesRegex(ValueError,'duplicate'):artifacts.validate_tar(file)
    def test_hardlink_archive(self):
        file=self.archive([('sdk/link',tarfile.LNKTYPE,'sdk/file')])
        with self.assertRaisesRegex(ValueError,'hardlink'):artifacts.validate_tar(file)
    def test_symlink_escape(self):
        file=self.archive([('sdk/link',tarfile.SYMTYPE,'../../outside')])
        with self.assertRaisesRegex(ValueError,'escapes'):artifacts.validate_tar(file)
    def test_member_beneath_symlink(self):
        file=self.archive([('sdk/link',tarfile.SYMTYPE,'lib'),('sdk/link/a','file',b'x')])
        with self.assertRaisesRegex(ValueError,'beneath'):artifacts.validate_tar(file)
    def test_valid_shared_library_alias_roundtrip(self):
        folder=self.root/'sdk';folder.mkdir();(folder/'lib.so.1').write_bytes(b'ELF fixture');(folder/'lib.so').symlink_to('lib.so.1')
        target=self.root/'sdk.tar.gz';record=artifacts.archive(folder,target,'sdk')
        output=artifacts.extract_new(target,self.root/'extracted','sdk')
        self.assertEqual(artifacts.inventory(output),record['inventory'])
        self.assertTrue((output/'lib.so').is_symlink())
    def test_extract_prefix_mismatch(self):
        file=self.archive([('other/a','file',b'x')])
        with self.assertRaisesRegex(ValueError,'prefix'):artifacts.extract_new(file,self.root/'out','sdk')
        self.assertFalse((self.root/'out').exists())
    def test_extract_no_overwrite(self):
        file=self.archive([('sdk/a','file',b'x')]);out=self.root/'out';out.mkdir();(out/'sentinel').write_bytes(b'keep')
        with self.assertRaises(FileExistsError):artifacts.extract_new(file,out,'sdk')
        self.assertEqual((out/'sentinel').read_bytes(),b'keep')
    def test_checksum_tamper_and_extra(self):
        (self.root/'a').write_bytes(b'a');raw=artifacts.checksums(self.root,['a'])
        self.assertEqual(artifacts.verify_checksums(self.root,raw),{'a':artifacts.sha(b'a')})
        (self.root/'extra').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'extra'):artifacts.verify_checksums(self.root,raw)
        (self.root/'extra').unlink();(self.root/'a').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'mismatch'):artifacts.verify_checksums(self.root,raw)
    def test_empty_checksums(self):
        with self.assertRaisesRegex(ValueError,'empty'):artifacts.verify_checksums(self.root,b'')
    def test_duplicate_checksums(self):
        (self.root/'a').write_bytes(b'a');raw=artifacts.checksums(self.root,['a'])
        with self.assertRaisesRegex(ValueError,'duplicate'):artifacts.verify_checksums(self.root,raw+raw)
    def test_checksum_symlink_refused(self):
        (self.root/'a').write_bytes(b'a');(self.root/'link').symlink_to('a')
        with self.assertRaisesRegex(ValueError,'symlink'):artifacts.checksums(self.root,['link'])
    def test_deterministic_archive(self):
        src=self.root/'src';src.mkdir();(src/'f').write_bytes(b'fixed');first=self.root/'a.gz';second=self.root/'b.gz'
        artifacts.archive(src,first,'sdk');os.utime(src/'f',(100,200));artifacts.archive(src,second,'sdk')
        self.assertEqual(first.read_bytes(),second.read_bytes())
    def test_bounded_build_recipe_exact_transforms(self):
        source='FROM rust AS p-build\nRUN --mount=type=cache,id=rx-runtime-skill-p-target x\nFROM rust AS s-build\nRUN CARGO_BUILD_JOBS=2 cargo build\n'
        output=distro.bounded_recipe(source,'RUN cmake --build /x -j2\n','fixture')
        self.assertEqual(output.count('ENV CARGO_BUILD_JOBS=1'),2)
        self.assertNotIn('JOBS=2',output);self.assertNotIn('-j2',output);self.assertIn('id=rx-m5-fixture-p-target',output)
    def test_recipe_unknown_stage_refused(self):
        with self.assertRaisesRegex(ValueError,'unrecognized'):distro.bounded_recipe('FROM rust AS changed','', 'fixture')
    def test_recipe_bad_namespace_refused(self):
        with self.assertRaisesRegex(ValueError,'namespace'):distro.bounded_recipe('','','../unsafe')
    def test_source_witness_requires_exact_bytes_and_lock(self):
        (self.root/'Cargo.toml').write_bytes(b'manifest');(self.root/'Cargo.lock').write_bytes(b'lock')
        raw=b''.join(artifacts.sha((self.root/name).read_bytes()).encode()+b'  /source/'+name.encode()+b'\n' for name in ('Cargo.toml','Cargo.lock'))
        self.assertEqual(len(distro.verify_source_manifest(raw,self.root)),2)
        (self.root/'Cargo.lock').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'differs'):distro.verify_source_manifest(raw,self.root)
    def test_source_witness_missing_dependency_closure(self):
        with self.assertRaisesRegex(ValueError,'closure'):distro.verify_source_manifest(b'',self.root)
    def test_source_witness_traversal(self):
        with self.assertRaisesRegex(ValueError,'unsafe'):distro.verify_source_manifest(b'a'*64+b'  /source/../outside\n',self.root)
    def test_recovery_log_requires_named_actual_success(self):
        for name,witness in distro.WITNESSES.items():(self.root/name).write_text(f'test {witness} ... ok\ntest result: ok. 1 passed; 0 failed\n')
        self.assertEqual(len(distro.verify_recovery_logs(self.root)),3)
        (self.root/'host-recovery.log').write_text('test result: ok. 1 passed; 0 failed\n')
        with self.assertRaisesRegex(ValueError,'did not pass'):distro.verify_recovery_logs(self.root)
    def test_fixed_corpus_equality_is_not_status_only(self):
        row={'name':'one','actual':'OK','expected':'OK','sha256':'abc'}
        self.assertEqual(consumer.compare_corpus({'cases':[row]},{'cases':[row]}),1)
        with self.assertRaises(ValueError):consumer.compare_corpus({'cases':[row]},{'cases':[dict(row,sha256='changed')]})
        with self.assertRaises(ValueError):consumer.compare_corpus({'cases':[]},{'cases':[]})
    def test_installer_shutdown_and_exact_images_required(self):
        session=self.root/'sessions/fresh';session.mkdir(parents=True)
        images={'platform':'sha256:p','solutions':'sha256:s'}
        value={'images':images,'profile':'FILE_SIMULATION','physical_execution':'NOT_SUPPORTED','phase':'STOPPED',
            'recorded_verification':{'status':'PASS'},'shutdown':[{'running':False,'exit_code':0}]}
        (session/'session.json').write_text(json.dumps(value));self.assertEqual(runtime.installer_result(self.root,images)['session'],'fresh')
        value['shutdown'][0]['running']=True;(session/'session.json').write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'shutdown'):runtime.installer_result(self.root,images)
    def test_signature_uses_external_keyring_and_exact_checksums(self):
        files=self.root/'artifacts';files.mkdir();(files/'payload').write_bytes(b'delivered')
        (files/'CHECKSUMS.sha256').write_bytes(artifacts.checksums(files,['payload']))
        signature=self.root/'signature.asc';signature.write_bytes(b'fixture signature')
        keyring=self.root/'trusted.gpg';keyring.write_bytes(b'fixture public keyring')
        argv=['verify','--artifacts',str(files),'--signature',str(signature),'--trusted-keyring',str(keyring),
            '--trusted-keyring-sha256',artifacts.sha(keyring.read_bytes()),'--output',str(self.root/'verified.json')]
        process=subprocess.CompletedProcess([],0,'[GNUPG:] VALIDSIG PUBLICFIXTURE\n','')
        # Patch the module's TemporaryDirectory via its original factory to keep
        # tests inside this staging scope without replacing global recursion.
        factory=tempfile.TemporaryDirectory
        with patch('sys.argv',argv),patch.object(provenance.tempfile,'TemporaryDirectory',lambda **k:factory(dir=self.root)),patch.object(provenance.subprocess,'run',return_value=process) as command:
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):provenance.main()
        args=command.call_args.args[0];self.assertEqual(Path(args[-1]).name,'CHECKSUMS.sha256')
        self.assertNotEqual(args[-1],str(files/'CHECKSUMS.sha256'))
        self.assertEqual(Path(args[args.index('--keyring')+1]).name,'trusted.gpg');self.assertNotIn('--import',args)
        self.assertEqual(json.loads((self.root/'verified.json').read_text())['status'],'EXACT_CHECKSUMS_SIGNATURE_VERIFIED')
    def test_untrusted_keyring_stops_before_gpg(self):
        files=self.root/'artifacts';files.mkdir();keyring=self.root/'trusted';keyring.write_bytes(b'public')
        argv=['verify','--artifacts',str(files),'--signature',str(self.root/'sig'),'--trusted-keyring',str(keyring),
              '--trusted-keyring-sha256','0'*64,'--output',str(self.root/'receipt')]
        with patch('sys.argv',argv),patch.object(provenance.subprocess,'run') as command:
            with self.assertRaisesRegex(ValueError,'policy'):provenance.main()
            command.assert_not_called()


    def component_fixture(self):
        dispatch={'operation':'op','invocation':'inv','device_session':'session','input':{'binding':{'selection':{'intent_digest':'intent'}}}}
        value={'challenge':'challenge','profile_digest':'profile','device_session':'session','dispatch':dispatch,'sources':['ready','done']}
        current={'schema':'rx.external-native-snapshot.v1','challenge':'challenge','profile_digest':'profile','device_session':'session','samples':{'ready':{},'done':{}}}
        frame={'schema':'rx.external-native-completion.v1','challenge':'challenge','dispatch_digest':component.expected_record(value)['dispatch_digest'],
               'operation':'op','invocation':'inv','intent_digest':'intent','profile_digest':'profile','device_session':'session','current':current,
               'capture':{'native_id':'inv','status_schema':'m5.counter.completed.v1','status':0,'captured_at':{},'device_session':'session'}}
        return value,frame
    def test_component_full_completion_tuple(self):
        value,frame=self.component_fixture();component.check_completion(value,frame,True)
        for key in ('dispatch_digest','profile_digest','device_session','invocation','operation','intent_digest'):
            changed=copy.deepcopy(frame);changed[key]='wrong'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'correlation'):component.check_completion(value,changed,True)
        changed=copy.deepcopy(frame);changed['capture']['native_id']='wrong'
        with self.assertRaisesRegex(ValueError,'identity'):component.check_completion(value,changed,True)
    def test_component_missing_normal_completion_refused(self):
        value,frame=self.component_fixture()
        entry={'schema':'rx.external-native-entry.v1','challenge':value['challenge'],'request_sha256':artifacts.sha(component.encoded(value)),
               'operation':'op','invocation':'inv','intent_digest':'intent','profile_digest':'profile','device_session':'session'}
        component.check_frames(value,[entry,frame],'none')
        with self.assertRaisesRegex(ValueError,'frame'):component.check_frames(value,[entry],'none')
    def test_component_effect_and_callback_identity(self):
        value,_=self.component_fixture();marker={'operation':'op','invocation':'inv','selection':{'intent_digest':'intent'},'acquired_at':{}}
        effect={**marker,'primitive':'count','increment':1,'count_before':0,'count_after':1}
        component.check_markers(value,[marker],[effect],[marker],True)
        for group in ('entry','effect','completion'):
            rows=[[dict(marker)],[dict(effect)],[dict(marker)]];rows[('entry','effect','completion').index(group)][0]['invocation']='wrong'
            with self.subTest(group=group),self.assertRaisesRegex(ValueError,'correlation'):component.check_markers(value,*rows,True)


if __name__=='__main__':unittest.main()
