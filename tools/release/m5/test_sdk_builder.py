"""Pure builder metadata/gate tests. No pip, Cargo, CMake, Docker or product CLI."""
import copy
from email.message import EmailMessage
import hashlib
import json
from pathlib import Path
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import build_sdk_artifacts as b

HERE=Path(__file__).resolve().parent


def lock(packages):
    rows=['version = 4']
    for value in packages:
        rows.append('[[package]]')
        for name,content in value.items():rows.append(name+' = '+json.dumps(content))
    return ('\n'.join(rows)+'\n').encode()


def package(name,version='0.1.0',source=None,checksum=None):
    value={'name':name,'version':version}
    if source is not None:value['source']=source
    if checksum is not None:value['checksum']=checksum
    return value


class LockGateTests(unittest.TestCase):
    def setUp(self):
        self.local=[package('rx-domain'),package('rx-process-contract')]
        self.dep=package('serde','1.0.0','registry+https://github.com/rust-lang/crates.io-index','a'*64)
        self.original=lock([*self.local,self.dep,package('rx-platformd'),package('unused','2.0','registry+x','b'*64)])

    def test_prunes_without_new_dependency_identity(self):
        result=b.validate_lock_subset(self.original,lock([*self.local,self.dep]))
        self.assertEqual(result['removed_packages'],2)
        self.assertEqual(result['local_crates'],['rx-domain','rx-process-contract'])
        self.assertEqual(result['third_party'],[self.dep])

    def test_version_source_and_checksum_changes_are_rejected(self):
        for key,value in [('version','1.0.1'),('source','registry+https://untrusted.invalid/index'),('checksum','b'*64)]:
            altered=dict(self.dep,**{key:value})
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate_lock_subset(self.original,lock([*self.local,altered]))

    def test_private_or_missing_local_crate_is_rejected(self):
        for packages in [[*self.local,self.dep,package('rx-platformd')],[self.local[0],self.dep]]:
            with self.assertRaises(ValueError):b.validate_lock_subset(self.original,lock(packages))

    def test_duplicate_and_changed_format_are_rejected(self):
        with self.assertRaises(ValueError):b.validate_lock_subset(self.original,lock([*self.local,self.dep,self.dep]))
        with self.assertRaises(ValueError):b.validate_lock_subset(self.original,lock([*self.local,self.dep]).replace(b'version = 4',b'version = 3'))

    def test_workspace_derivation_changes_only_members(self):
        original=b'''[workspace]\nmembers = ["crates/rx-domain", "crates/private", "crates/rx-process-contract"]\nresolver = "3"\n[workspace.package]\nlicense = "Apache-2.0"\n[workspace.dependencies]\nserde = {version="1",features=["derive"]}\n'''
        expected=tomllib.loads(original.decode());expected['workspace']['members']=b.RUST_MEMBERS
        self.assertEqual(tomllib.loads(b.minimal_workspace(original).decode()),expected)
        with self.assertRaises(ValueError):b.minimal_workspace(original.replace(b'resolver = "3"',b'default-members=["crates/private"]'))

    def test_rust_metadata_cannot_import_private_path_dependency(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder)
            value={'workspace_members':['a','b'],'packages':[
                {'id':'a','name':'rx-domain','source':None,'manifest_path':str(root/'crates/rx-domain/Cargo.toml')},
                {'id':'b','name':'rx-process-contract','source':None,'manifest_path':str(root/'crates/rx-process-contract/Cargo.toml')} ]}
            b.validate_rust_metadata(value,root)
            bad=copy.deepcopy(value);bad['packages'].append({'id':'c','name':'private','source':None,'manifest_path':'/elsewhere/Cargo.toml'})
            with self.assertRaises(ValueError):b.validate_rust_metadata(bad,root)


class ProvenanceTests(unittest.TestCase):
    def test_canonical_repository_forms_only(self):
        for url in ['https://github.com/jack0682/RobotTransformation.git','git@github.com:jack0682/RobotTransformation.git',
                    'ssh://git@github.com/jack0682/RobotTransformation']:
            self.assertEqual(b.normalize_origin(url),b.REPOSITORY)
        for url in ['https://evil.invalid/jack0682/RobotTransformation','https://github.com/owner/repo/tree/main']:
            with self.assertRaises(ValueError):b.normalize_origin(url)

    def test_tree_parser_refuses_escape_symlink_gitlink_and_duplicates(self):
        good=b'100644 blob '+b'a'*40+b'\trx-platform/a.py\0'
        self.assertEqual(b.parse_tree(good)[0]['path'],'rx-platform/a.py')
        for value in [good+good,good.replace(b'rx-platform/a.py',b'../a.py'),good.replace(b'100644',b'120000'),good.replace(b'100644 blob',b'160000 commit')]:
            with self.assertRaises(ValueError):b.parse_tree(value)

    def test_source_copy_checks_git_blob_before_writing(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            base=Path(folder);repo=base/'repo';(repo/'rx-platform').mkdir(parents=True)
            source=repo/'rx-platform/a.py';source.write_bytes(b'original\n');source.chmod(0o644)
            oid=hashlib.sha1(b'blob 9\0original\n').hexdigest()
            raw=f'100644 blob {oid}\trx-platform/a.py\0'.encode()
            runner=SimpleNamespace(run=lambda *args,**kwargs:SimpleNamespace(stdout=raw))
            snapshot={'commit':'f'*40,'object_format':'sha1'}
            b.copy_tracked(runner,repo,snapshot,['rx-platform'],base/'out','rx-platform')
            self.assertEqual((base/'out/a.py').read_bytes(),b'original\n')
            source.write_bytes(b'changed\n')
            with self.assertRaises(ValueError):b.copy_tracked(runner,repo,snapshot,['rx-platform'],base/'bad','rx-platform')

    def test_source_work_output_cannot_overlap(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            base=Path(folder);repo=base/'repo'
            for component in ['rx-platform','rx-solutions']:
                (repo/component).mkdir(parents=True);(repo/component/'Cargo.toml').touch()
            b.validate_paths(repo,base/'work',base/'output')
            for work,output in [(repo/'generated',base/'output'),(base/'work',base/'work/artifacts'),(base/'work',repo/'artifacts')]:
                with self.assertRaises(ValueError):b.validate_paths(repo,work,output)
            (base/'alias').symlink_to(repo,target_is_directory=True)
            with self.assertRaises(ValueError):b.validate_paths(base/'alias',base/'work',base/'output')

    def test_source_snapshot_requires_exact_clean_repository(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder).resolve();head='a'*40
            def value(runner,repo,*args):
                if args==('rev-parse','--show-toplevel'):return str(root)
                if args==('rev-parse','HEAD'):return head
                if args[0]=='status':return ''
                if args[0]=='remote':return 'https://github.com/'+b.REPOSITORY+'.git'
                if args==('rev-parse','--show-object-format'):return 'sha1'
                return 'b'*40
            with patch.object(b,'git',side_effect=value):
                result=b.source_snapshot(None,root,head)
                self.assertTrue(result['clean'])
                with self.assertRaises(ValueError):b.source_snapshot(None,root,'c'*40)
            with patch.object(b,'git',side_effect=lambda r,p,*a:' M tracked.py' if a[0]=='status' else value(r,p,*a)):
                with self.assertRaises(ValueError):b.source_snapshot(None,root,head)


class WheelTests(unittest.TestCase):
    def test_wheel_metadata_and_traversal_gate(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path=Path(folder)/'sample.whl'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('rxclpy-0.1.0.dist-info/METADATA','Metadata-Version: 2.3\nName: rxclpy\nVersion: 0.1.0\nRequires-Dist: protobuf==7.36.2\n\n')
                z.writestr('rxclpy-0.1.0.dist-info/WHEEL','Wheel-Version: 1.0\nTag: py3-none-any\n')
            meta=b.wheel_metadata(path)
            self.assertEqual(meta['name'],'rxclpy');self.assertEqual(meta['tags'],['py3-none-any'])
            with zipfile.ZipFile(path,'a') as z:z.writestr('../escape','bad')
            with self.assertRaises(ValueError):b.wheel_metadata(path)

    def test_offline_transitive_versions_match_producer_conformance(self):
        environment=[{'name':'pip','version':'26.0'},{'name':'rxclpy','version':'0.1.0'},
                     {'name':'typing_extensions','version':'4.15.0'}]
        records=[{'name':'rxclpy','version':'0.1.0'},{'name':'typing-extensions','version':'4.15.0'}]
        b.validate_python_closure(records,environment)
        records[1]['version']='4.16.0'
        with self.assertRaises(ValueError):b.validate_python_closure(records,environment)

    def test_dynamic_library_metadata_does_not_export_build_paths(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);lib=root/'lib';lib.mkdir();file=lib/'librxclcpp.so';file.write_bytes(b'ELF fixture')
            result=b.dynamic_dependencies('librxclcpp.so => '+str(file)+' (0x123)\nlinux-vdso.so.1 (0x456)',root)
            self.assertEqual(result[0]['origin'],'sdk');self.assertEqual(result[0]['artifact_path'],'lib/librxclcpp.so')
            self.assertNotIn(str(root),json.dumps(result))
            with self.assertRaises(ValueError):b.dynamic_dependencies('libx.so => not found',root)


class PipelineStateTests(unittest.TestCase):
    def fixture(self,base,rust_failure):
        repo=base/'repo'
        for component in ['rx-platform','rx-solutions']:
            (repo/component).mkdir(parents=True);(repo/component/'Cargo.toml').touch()
        args=['build_sdk_artifacts.py','--repo',str(repo),'--expected-head','a'*40,'--solutions-image','sha256:'+'b'*64,
            '--architecture','amd64','--historical-bundle','/historical','--work',str(base/'work'),'--output',str(base/'output'),'--execute']
        if not rust_failure:args+=['--no-include-rust']
        return args

    def test_rust_failure_never_emits_signable_final_checksums(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            base=Path(folder);args=self.fixture(base,True)
            source={'commit':'a'*40,'components':{}}
            image=[{'Id':'sha256:'+'b'*64,'Os':'linux','Architecture':'amd64'}]
            with patch('sys.argv',args),patch.dict('os.environ',{'CI':'true'}),patch.object(b.platform,'system',return_value='Linux'), \
                 patch.object(b.platform,'machine',return_value='x86_64'),patch.object(b,'source_snapshot',return_value=source), \
                 patch.object(b.Runner,'text',return_value=json.dumps(image)),patch.object(b,'toolchain',return_value={}), \
                 patch.object(b,'build_clients',return_value={'artifacts':{}}), \
                 patch.object(b,'build_adapter',return_value={'artifact':{'path':'external-adapter-sdk.tar.gz'}}), \
                 patch.object(b,'build_verification_kit',return_value={'artifact':{'path':'verification-kit.tar.gz'}}), \
                 patch.object(b,'build_historical',return_value={'artifact':{'path':'historical-runtime-client.tar.gz'}}), \
                 patch.object(b,'build_rust',side_effect=ValueError('dependency checksum changed')):
                self.assertEqual(b.main(),2)
            self.assertFalse((base/'output/CHECKSUMS.sha256').exists());self.assertFalse((base/'output/manifest.json').exists())
            result=json.loads((base/'work/partial-build.json').read_bytes())
            self.assertEqual(result['status'],'PARTIAL_UNVERIFIED');self.assertEqual(result['rust']['status'],'UNVERIFIED')

    def test_missing_ci_guard_runs_no_process(self):
        args=['build_sdk_artifacts.py','--repo','/repo','--expected-head','a'*40,'--solutions-image','sha256:'+'b'*64,
            '--architecture','amd64','--historical-bundle','/historical','--work','/work','--output','/output','--execute']
        with patch('sys.argv',args),patch.dict('os.environ',{'CI':'false'}),patch.object(b.subprocess,'run') as run:
            with self.assertRaises(SystemExit) as caught:b.main()
            self.assertEqual(caught.exception.code,2);run.assert_not_called()


if __name__=='__main__':unittest.main()
