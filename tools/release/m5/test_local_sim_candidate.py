"""Pure LOCAL_SIM producer gates; no installer, build, Docker or product calls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

from artifacts import archive,inventory,sha_file
import local_sim_candidate as local

HERE=Path(__file__).resolve().parent


def fixtures():
    snapshot={'repository':'jack0682/RobotTransformation','commit':'a'*40,'components':{
        'rx-platform':{'tree_oid':'b'*40},'rx-solutions':{'tree_oid':'c'*40}}}
    release={'schema':'rx.local-sim.release.v1','version':'migration-rc.test','architecture':'amd64',
        'image':'rx-local-skills:migration-rc.test-amd64','image_id':'sha256:'+'d'*64,
        'platform_commit':'a'*40,'solutions_commit':'a'*40,'source_dirty':False,
        'build_jobs':1,'cache_namespace':'m5-local-test','physical_execution':'NOT_SUPPORTED',
        'component_sources':{role:{'repository':snapshot['repository'],'commit':snapshot['commit'],
            'component_path':component,'tree_oid':snapshot['components'][component]['tree_oid']}
            for role,component in [('platform','rx-platform'),('solutions','rx-solutions')]}}
    return snapshot,release


class ReleaseTests(unittest.TestCase):
    def test_exact_monorepo_component_tuple_required(self):
        snapshot,release=fixtures()
        local.validate_release(release,snapshot,'amd64','migration-rc.test','m5-local-test')
        for key,value in [('solutions_commit','e'*40),('source_dirty',True),('build_jobs',2),('physical_execution','SUPPORTED')]:
            bad=copy.deepcopy(release);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):local.validate_release(bad,snapshot,'amd64','migration-rc.test','m5-local-test')
        release['component_sources']['platform']['component_path']='.'
        with self.assertRaises(ValueError):local.validate_release(release,snapshot,'amd64','migration-rc.test','m5-local-test')

    def test_installer_result_is_exact_release_and_named_checks(self):
        _,release=fixtures()
        result={'status':'PASS','release':release,'checks':sorted(local.EXPECTED_CHECKS),'physical_execution':'NOT_PERFORMED',
            'normal_result':{'request':{'request_id':str(uuid.uuid4()),'skill':'external-sum','version':'1.0.0','input':{'values':[2,4,8]}},
                'output':{'total':14,'receipt':str(uuid.uuid4())},'operation':{'outcome':'SUCCEEDED'}}}
        accepted=local.validate_acceptance(result,release)
        self.assertEqual(set(accepted['recognized_checks']),local.EXPECTED_CHECKS)
        for alteration in ['status','check','duplicate','release','outcome','sum']:
            bad=copy.deepcopy(result)
            if alteration=='status':bad['status']='UNKNOWN'
            elif alteration=='check':bad['checks'].remove('key-version-and-physical-scope-refusals')
            elif alteration=='duplicate':bad['checks'].append(bad['checks'][0])
            elif alteration=='release':bad['release']['image_id']='sha256:'+'e'*64
            elif alteration=='outcome':bad['normal_result']['operation']['outcome']='UNRESOLVED'
            else:bad['normal_result']['output']['total']=15
            with self.subTest(alteration=alteration),self.assertRaises(ValueError):local.validate_acceptance(bad,release)

    def test_current_image_matches_digest_architecture_and_user(self):
        _,release=fixtures();item={'Id':release['image_id'],'Architecture':'amd64','Os':'linux','Config':{'User':'10001:10001'}}
        local.validate_current_image([item],release)
        for key,value in [('Id','sha256:'+'e'*64),('Architecture','arm64'),('Os','windows'),('Config',{'User':'0'})]:
            bad=copy.deepcopy(item);bad[key]=value
            with self.assertRaises(ValueError):local.validate_current_image([bad],release)


class InventoryTests(unittest.TestCase):
    def test_published_bundle_bytes_match_tested_directory(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);bundle=root/'bundle';bundle.mkdir();(bundle/'rx').write_text('public CLI fixture')
            (bundle/'rx').chmod(0o755)
            file=root/'bundle.tar.gz';archive(bundle,file,'rx-local-skills')
            expected=inventory(bundle);local.verify_bundle_archive(file,expected)
            expected['rx']['sha256']='0'*64
            with self.assertRaises(ValueError):local.verify_bundle_archive(file,expected)

    def test_original_checksum_refuses_changed_or_extra_archive(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);payload=root/'bundle.tar.gz';payload.write_bytes(b'archive fixture');checks=root/'CHECKSUMS.sha256'
            checks.write_text(sha_file(payload)+'  '+payload.name+'\n');local.validate_original_archive_checksum(payload,checks)
            payload.write_bytes(b'changed')
            with self.assertRaises(ValueError):local.validate_original_archive_checksum(payload,checks)
            checks.write_text(sha_file(payload)+'  '+payload.name+'\n'+'0'*64+'  other.tar.gz\n')
            with self.assertRaises(ValueError):local.validate_original_archive_checksum(payload,checks)

    def test_ignored_stray_cannot_enter_docker_or_bundle_input(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            repo=Path(folder);prefixes=['rx-platform/crates','rx-platform/proto','rx-platform/spec','rx-solutions/deployment/local-skills']
            for path in prefixes:(repo/path).mkdir(parents=True)
            file=repo/'rx-solutions/deployment/local-skills/rx';file.write_text('tracked')
            records={file.relative_to(repo).as_posix():{}}
            local.reject_untracked_build_inputs(repo,records)
            (file.parent/'credential.ignored').write_text('not tracked')
            with self.assertRaises(ValueError):local.reject_untracked_build_inputs(repo,records)

    def test_source_inventory_compares_actual_git_blob(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            repo=Path(folder);file=repo/'repository-settings.json';file.write_bytes(b'{}');file.chmod(0o644)
            oid=hashlib.sha1(b'blob 2\0{}').hexdigest();raw=f'100644 blob {oid}\trepository-settings.json\0'.encode()
            runner=SimpleNamespace(run=lambda *a,**kw:SimpleNamespace(stdout=raw))
            snapshot={'commit':'a'*40,'object_format':'sha1'}
            result=local.source_inventory(runner,repo,snapshot)
            self.assertEqual(result['repository-settings.json']['sha256'],sha_file(file))
            file.write_bytes(b'changed')
            with self.assertRaises(ValueError):local.source_inventory(runner,repo,snapshot)

    def test_image_worker_source_parity_is_not_inferred_from_tag(self):
        _,release=fixtures();values={name:'a'*64 for name in local.PUBLIC_IMAGE_FILES}
        files={name:{'sha256':'a'*64} for name in ['rx-solutions/deployment/local-skills/worker.py',
            'rx-solutions/deployment/local-skills/runner.py','rx-solutions/LICENSE','rx-solutions/NOTICE']}
        runner=SimpleNamespace(text=lambda *args,**kwargs:json.dumps(values))
        local.image_inventory(runner,release,files)
        values['/opt/rx/worker.py']='b'*64
        with self.assertRaises(ValueError):local.image_inventory(runner,release,files)


class GuardTests(unittest.TestCase):
    def test_ci_guard_precedes_all_product_processes(self):
        args=['local_sim_candidate.py','--repo','/repo','--expected-head','a'*40,'--architecture','amd64',
            '--work','/work','--output','/output','--execute-fresh-linux-ci']
        with patch('sys.argv',args),patch.dict('os.environ',{'CI':'false'}),patch('build_sdk_artifacts.subprocess.run') as run:
            with self.assertRaises(SystemExit) as caught:local.main()
            self.assertEqual(caught.exception.code,2);run.assert_not_called()


if __name__=='__main__':unittest.main()
