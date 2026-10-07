#!/usr/bin/env python3
"""Root policy regressions for M4: exact ownership and narrow language exceptions."""
from contextlib import contextmanager
import json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/governance'))
import check_repository as gate
class CanonicalRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  folder=ROOT/'.g0-validation';folder.mkdir(exist_ok=True)
  cls.temporary=tempfile.TemporaryDirectory(prefix='canonical-root-',dir=folder)
  cls.root=Path(cls.temporary.name)/'candidate'
  if (ROOT/'.git').exists():
   cls.root.mkdir()
   paths=gate.git('ls-files','-z','--cached','--others','--exclude-standard').split('\0')
   for name in sorted(set(paths)-{''}):
    source=ROOT/name;target=cls.root/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target,follow_symlinks=False)
  else:
   shutil.copytree(ROOT,cls.root,ignore=shutil.ignore_patterns('.git','.g0-validation','__pycache__'))
 @classmethod
 def tearDownClass(cls):cls.temporary.cleanup()
 def files(self):return sorted(p for p in self.root.rglob('*') if p.is_file() or p.is_symlink())
 def errors(self,files=None):return gate.check(self.root,self.files() if files is None else files)
 @contextmanager
 def changed(self,name,raw,register=False,canonical=False):
  p=self.root/name;before=p.read_bytes() if p.exists() else None
  inventory=self.root/'.github/root-file-inventory.json';old_inventory=inventory.read_bytes()
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  if register:
   data=json.loads(old_inventory);data['files']=sorted(set(data['files'])|{name})
   if canonical:data['canonical_documents']=sorted(set(data['canonical_documents'])|{name})
   inventory.write_text(json.dumps(data))
  try:yield
  finally:
   if before is None:p.unlink()
   else:p.write_bytes(before)
   inventory.write_bytes(old_inventory)
 def test_full_root_candidate_has_exact_owned_files(self):self.assertEqual(self.errors(),[])
 def test_current_canonical_korean_prose_can_evolve(self):
  name='docs/01_product_definition.md';raw=(self.root/name).read_bytes()+('\n\uac00\ub098\ub2e4\n').encode()
  with self.changed(name,raw):self.assertEqual(self.errors(),[])
 def test_root_governance_korean_is_still_rejected(self):
  for name in ['README.md','tools/governance/common.py']:
   with self.subTest(name=name),self.changed(name,(self.root/name).read_bytes()+'\n\uac00\n'.encode()):
    self.assertTrue(any('must be English' in e for e in self.errors()))
 def test_unlisted_document_is_not_accepted_by_prefix(self):
  with self.changed('docs/unlisted.md',b'# Not listed\n'):self.assertTrue(any('Undeclared root file' in e for e in self.errors()))
 def test_declared_new_ordinary_document_is_explicitly_owned(self):
  with self.changed('docs/new-note.md',b'# A reviewed new note\n',register=True,canonical=True):self.assertEqual(self.errors(),[])
 def test_root_governance_cannot_be_reclassified_as_a_document(self):
  name='.github/root-file-inventory.json';data=json.loads((self.root/name).read_text());data['canonical_documents'].append('README.md')
  with self.changed(name,json.dumps(data).encode()):self.assertTrue(any('ownership differs' in e for e in self.errors()))
 def test_python_source_cannot_enter_document_language_exception(self):
  with self.changed('docs/payload.py',b'print(1)\n',register=True,canonical=True):
   self.assertTrue(any('only declared Markdown and JSON' in e for e in self.errors()))
 def test_ai_artifact_is_rejected_even_when_explicitly_listed_as_document(self):
  with self.changed('docs/AGENTS.md',b'# An assistant instruction\n',register=True,canonical=True):
   self.assertTrue(any('assistant/harness artifact' in e for e in self.errors()))
 def test_missing_source_component_still_fails(self):
  files=[p for p in self.files() if not p.relative_to(self.root).as_posix().startswith('rx-platform/')]
  self.assertTrue(any('Missing source component: rx-platform' in e for e in self.errors(files)))
 def test_bound_source_hash_cannot_hide_in_document_language_scope(self):
  name='contracts/semantic/v1.0/01_responsibility_and_semantics.md'
  with self.changed(name,(self.root/name).read_bytes()+b'changed'):
   self.assertTrue(any('Hash-bound bytes changed' in e for e in self.errors()))
 def test_consumer_mirror_hash_is_required_by_root_gate(self):
  name='rx-platform/spec/contracts/v1.0/README.md'
  with self.changed(name,(self.root/name).read_bytes()+b'changed'):
   self.assertTrue(any('Canonical/mirror bytes differ' in e for e in self.errors()))
 def test_compatibility_route_hash_is_required_by_root_gate(self):
  name='contracts/42_framework_master_plan.md'
  with self.changed(name,(self.root/name).read_bytes()+b'changed'):
   self.assertTrue(any('Compatibility projection changed' in e for e in self.errors()))
 def test_old_document_tree_cannot_reappear(self):
  with self.changed('rx_docs/docs/01_product_definition.md',b'# Wrong second owner\n'):
   self.assertTrue(any('Old imported document still owns' in e for e in self.errors()))
 def test_legacy_rendered_href_cannot_borrow_historical_lookup(self):
  with self.changed('docs/stale-link.md',b'[old](../rx_docs/docs/01_product_definition.md)\n',register=True,canonical=True):
   self.assertTrue(any('missing local target' in e for e in self.errors()))
 def test_document_inventory_cannot_drop_existing_owner(self):
  name='.github/root-file-inventory.json';data=json.loads((self.root/name).read_text());data['canonical_documents'].remove('docs/01_product_definition.md')
  with self.changed(name,json.dumps(data).encode()):self.assertTrue(any('ownership differs' in e for e in self.errors()))
if __name__=='__main__':unittest.main(verbosity=2)
