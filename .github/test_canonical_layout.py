#!/usr/bin/env python3
"""Regression cases for finite compatibility routes and canonical document ownership."""
import importlib.util,json,os,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(os.environ.get('RX_CANONICAL_TEST_ROOT',Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('canonical_layout',ROOT/'tools/docs/check_canonical_layout.py')
CHECK=importlib.util.module_from_spec(spec);spec.loader.exec_module(CHECK)
class CanonicalLayoutTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('RX_CANONICAL_TEST_TMPDIR'));self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  m=json.loads((ROOT/'provenance/import/M4-canonical-document-map.json').read_text());self.manifest=m
  paths={r['target_path'] for r in m['moves']}|{r['path'] for r in m['compatibility_projections']}
  for r in m['contract_mirrors']:paths|={r['platform'],r['solutions']}
  paths|={'provenance/import/M4-canonical-document-map.json','provenance/import/M3-document-origins.json','provenance/import/M2-source-manifest.json'}
  for path in paths:
   p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,p)
 def rejected_change(self,path,value,pattern):
  p=self.root/path;old=p.read_bytes()
  try:
   p.write_bytes(value)
   with self.assertRaisesRegex(ValueError,pattern):CHECK.check(self.root)
  finally:p.write_bytes(old)
 def test_complete_layout_passes(self):
  result=CHECK.check(self.root);self.assertEqual(result['hash_bound_documents'],18);self.assertEqual(result['v1_contract_mirrors'],24)
 def test_every_hash_bound_mutation_fails(self):
  for r in self.manifest['hash_bound_documents']:
   with self.subTest(path=r['path']):self.rejected_change(r['path'],(self.root/r['path']).read_bytes()+b'changed','Hash-bound bytes changed')
 def test_every_platform_and_solutions_mirror_mutation_fails(self):
  for r in self.manifest['contract_mirrors']:
   for consumer in ['platform','solutions']:
    with self.subTest(path=r[consumer]):self.rejected_change(r[consumer],(self.root/r[consumer]).read_bytes()+b'changed','Canonical/mirror bytes differ')
 def test_every_projection_mutation_fails(self):
  for r in self.manifest['compatibility_projections']:
   with self.subTest(path=r['path']):self.rejected_change(r['path'],(self.root/r['path']).read_bytes()+b'changed','Compatibility projection changed')
 def test_repointed_or_self_consistent_migration_map_fails(self):
  p='provenance/import/M4-canonical-document-map.json';m=json.loads((self.root/p).read_text());m['moves'][0]['target_path']='../escaped.md'
  self.rejected_change(p,json.dumps(m).encode(),'Historical M4 migration map changed')
 def test_old_path_resurrection_is_not_a_second_owner(self):
  p=self.root/self.manifest['moves'][0]['source_path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('duplicate source')
  with self.assertRaisesRegex(ValueError,'Old imported document still owns'):CHECK.check(self.root)
 def test_missing_canonical_document_fails(self):
  (self.root/'docs/01_product_definition.md').unlink()
  with self.assertRaisesRegex(ValueError,'Missing regular file'):CHECK.check(self.root)
 def test_symlink_is_not_a_compatibility_projection(self):
  p=self.root/'contracts/42_framework_master_plan.md';p.unlink();p.symlink_to('../docs/42_framework_master_plan.md')
  with self.assertRaisesRegex(ValueError,'Symlink refused'):CHECK.check(self.root)
 def test_unlisted_evidence_copy_fails(self):
  (self.root/'references/new-run.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'Unexpected reference copy'):CHECK.check(self.root)
 def test_ordinary_current_documents_remain_editable(self):
  p=self.root/'docs/01_product_definition.md';p.write_bytes(p.read_bytes()+b'\nA later reviewed explanation.\n')
  self.assertEqual(CHECK.check(self.root)['ordinary_current_bytes'],'EDITABLE_NOT_FROZEN')
 def test_historical_m3_record_mutation_fails(self):
  self.rejected_change('provenance/import/M3-document-origins.json',b'{}','Historical M3 origin index changed')
if __name__=='__main__':unittest.main()
