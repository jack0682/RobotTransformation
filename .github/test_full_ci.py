#!/usr/bin/env python3
"""Bounded M3 negative fixtures; no real signing, product build, Docker or network."""
import importlib.util
import json
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/governance'))
sys.path.insert(0, str(ROOT / 'tools/migration'))
import check_ci
import check_origin
import check_repository


class FullGateTests(unittest.TestCase):
    def test_all_sixteen_results_required_and_every_non_success_refused(self):
        good = {name: {'result': 'success'} for name in check_ci.FULL_SCOPE['required_jobs']}
        self.assertEqual(len(good), 16)
        check_ci.check(good, check_ci.FULL_SCOPE)
        for name in good:
            for state in ('failure', 'cancelled', 'skipped', None):
                bad = copy.deepcopy(good); bad[name]['result'] = state
                with self.subTest(name=name, state=state), self.assertRaises(ValueError): check_ci.check(bad, check_ci.FULL_SCOPE)
            bad = dict(good); bad.pop(name)
            with self.assertRaises(ValueError): check_ci.check(bad, check_ci.FULL_SCOPE)
        with self.assertRaises(ValueError): check_ci.check({**good, 'extra': {'result': 'success'}}, check_ci.FULL_SCOPE)

    def test_old_stage_cannot_claim_full_union(self):
        old = {name: {'result': 'success'} for name in check_ci.IMPORT_SCOPE['required_jobs']}
        check_ci.check(old, check_ci.IMPORT_SCOPE)
        with self.assertRaises(ValueError): check_ci.check(old, check_ci.FULL_SCOPE)
        with self.assertRaises(ValueError): check_ci.stage({**check_ci.FULL_SCOPE, 'product_validation': 'ACCEPTED'})

    def test_runner_context_is_step_only_not_job_env(self):
        workflow = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertEqual(check_repository.job_env_runner_errors(workflow), [])
        for job, component in [('platform_rust', 'rx-platform'), ('solutions_rust', 'rx-solutions')]:
            step = '        env:\n          CARGO_TARGET_DIR: ${{ runner.temp }}/' + component + '-target\n'
            self.assertIn(step, workflow)
            invalid = workflow.replace(step, '', 1)
            invalid = invalid.replace('  ' + job + ':\n', '  ' + job + ':\n    env:\n      CARGO_TARGET_DIR: ${{ runner.temp }}/' + component + '-target\n', 1)
            with self.subTest(job=job):
                errors = check_repository.job_env_runner_errors(invalid)
                self.assertEqual(len(errors), 1)
                self.assertIn('jobs.' + job + '.env', errors[0])
        bracket = "jobs:\n  fixture:\n    env:\n      TARGET: ${{ runner['temp'] }}\n    steps:\n      - run: true\n"
        self.assertEqual(len(check_repository.job_env_runner_errors(bracket)), 1)
        valid = "jobs:\n  fixture:\n    steps:\n      - run: true\n        env:\n          TARGET: ${{ runner.temp }}\n"
        self.assertEqual(check_repository.job_env_runner_errors(valid), [])

    def test_original_real_gpg_and_skills_architectures_remain(self):
        workflow = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertEqual(workflow.count('python3 -B .github/test_commit_policy.py'), 2)
        self.assertEqual(workflow.count('arch: amd64'), 2)
        self.assertEqual(workflow.count('arch: arm64'), 2)
        self.assertEqual(workflow.count('path: compat-platform'), 1)
        self.assertIn('m3-identities/logs/**', workflow)
        self.assertIn('python3 -B .github/test_documents.py', workflow)
        for component in ('rx-platform', 'rx-solutions'):
            source = (ROOT / component / '.github/test_commit_policy.py').read_text()
            self.assertIn('GIT_OPTIONAL_LOCKS="0"', source)
            self.assertIn('--quick-generate-key', source)

    def test_docker_build_receives_internal_jobs_and_cache_scope(self):
        docker = (ROOT / 'rx-solutions/docker/Skills.Dockerfile').read_text()
        builder = (ROOT / 'rx-solutions/tools/build_skill_release.py').read_text()
        self.assertIn('cargo build --jobs "$CARGO_BUILD_JOBS"', docker)
        self.assertIn('RX_CARGO_CACHE_SCOPE', docker)
        self.assertIn('"CARGO_BUILD_JOBS=" + str(args.build_jobs)', builder)
        self.assertIn('"RX_CARGO_CACHE_SCOPE=" + args.cache_namespace', builder)
        self.assertIn('"component_sources": sources', builder)


class OriginGuardTests(unittest.TestCase):
    def test_candidate_protected_module_is_not_imported_before_pin(self):
        (ROOT / '.g0-validation').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.g0-validation') as temp:
            root = Path(temp)
            path = root / check_origin.PROTECTED[0]; path.parent.mkdir(parents=True); path.write_text('def require(*a): pass\n')
            def git(where, *args, **kwargs):
                if '--show-toplevel' in args: return str(root).encode()
                if '--is-shallow-repository' in args: return b'false'
                if args[0] == 'for-each-ref': return b''
                if '--git-path' in args: return str(root/'grafts').encode()
                if args == ('rev-parse', 'HEAD'): return b'a'*40
                if args[0] == 'merge-base': return b''
                if args[0] == 'show': return b'def require(value):\n    if not value: raise ValueError()\n'
                raise AssertionError(args)
            with patch.object(check_origin, 'raw_git', side_effect=git), patch('builtins.exec') as execute:
                with self.assertRaisesRegex(ValueError, 'Frozen import/identity proof changed'): check_origin.verify(root)
                execute.assert_not_called()

    def test_nonancestor_is_refused_before_any_proof_execution(self):
        root = ROOT
        def git(where, *args, **kwargs):
            if '--show-toplevel' in args: return str(root).encode()
            if '--is-shallow-repository' in args: return b'false'
            if args[0] == 'for-each-ref': return b''
            if '--git-path' in args: return str(ROOT/'.g0-validation/no-grafts').encode()
            if args == ('rev-parse', 'HEAD'): return b'a'*40
            if args[0] == 'merge-base': raise ValueError('not an ancestor')
            raise AssertionError(args)
        with patch.object(check_origin, 'raw_git', side_effect=git), self.assertRaisesRegex(ValueError, 'not an ancestor'):
            check_origin.verify(root)

    def test_current_root_inventory_is_exact(self):
        try:
            git_root = Path(check_repository.git("rev-parse", "--show-toplevel").strip()).resolve()
        except ValueError:
            git_root = None
        if git_root == ROOT.resolve():
            paths = check_repository.git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
            files = sorted({ROOT / name for name in paths if name})
        else:
            # Only the deliberately Git-free staging fixture uses filesystem inventory.
            files = [p for p in ROOT.rglob("*") if (p.is_file() or p.is_symlink())
                     and p.relative_to(ROOT).parts[0] not in {".git", ".g0-validation"} and "__pycache__" not in p.parts]
        self.assertEqual(check_repository.check(ROOT, files), [])
        self.assertTrue(check_repository.check(ROOT, files + [ROOT/'unlisted-script.py']))
        workflow = ROOT / '.github/workflows/ci.yml'
        original = Path.read_text
        text = original(workflow)
        mutants = [text.replace('          - arch: arm64\n            runner: ubuntu-24.04-arm\n', '', 1),
                   text.replace('      - name: Audit original import without freezing current product files\n',
                                '      - if: false\n        name: Audit original import without freezing current product files\n')]
        for mutant in mutants:
            self.assertNotEqual(mutant, text)
            def read(path, *args, **kwargs):
                return mutant if path == workflow else original(path, *args, **kwargs)
            with patch.object(Path, 'read_text', read):
                self.assertTrue(check_repository.check(ROOT, files))



class SkillProvenanceTests(unittest.TestCase):
    def test_component_identity_and_dirty_refusal(self):
        spec = importlib.util.spec_from_file_location('skill_release', ROOT/'rx-solutions/tools/build_skill_release.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        (ROOT/'.g0-validation').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.g0-validation') as temp:
            root = Path(temp); (root/'rx-solutions').mkdir()
            (root/'repository-settings.json').write_text(json.dumps({'repository':'jack0682/RobotTransformation'}))
            def command(*args):
                if '--show-toplevel' in args: return str(root)
                if 'status' in args: return ''
                if args[-1] == 'HEAD': return 'a'*40
                return 'b'*40
            with patch.object(module, 'command', side_effect=command):
                value = module.source_identity(root/'rx-solutions')
                self.assertEqual(value['component_path'], 'rx-solutions')
                self.assertEqual(value['commit'], 'a'*40)
                self.assertEqual(value['tree_oid'], 'b'*40)
            def dirty(*args): return ' M changed' if 'status' in args else command(*args)
            with patch.object(module, 'command', side_effect=dirty), self.assertRaisesRegex(ValueError, 'clean'):
                module.source_identity(root/'rx-solutions')


if __name__ == '__main__': unittest.main(verbosity=2)
