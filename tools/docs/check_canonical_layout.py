#!/usr/bin/env python3
"""Check M4 canonical ownership, retained contracts and finite compatibility routes.
Ordinary current document bytes are editable; historical migration hashes are provenance.
"""
from __future__ import annotations
import argparse,hashlib,json,posixpath,sys
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
DOCS_COMMIT='4384ed49e384c53e645f71757ce597292b928eb6'
IMPORT_COMMIT='0cecec7516879584c4bd6d2ba24cbe5b3c8e54a0'
M4_MAP_SHA256='bbe903fac1649a196f784b96cbe080ad2ca29cb9110c9c81ec9e464160774c99'
# Import verification itself remains tools/migration/check_origin.py's responsibility.
ROUTES={
 'contracts/implementation/laser_cell_model.md':('docs/implementation/laser_cell_model.md','Cell model'),
 'contracts/42_framework_master_plan.md':('docs/42_framework_master_plan.md','Framework master plan'),
}
JSON_PROJECTIONS={
 'references/execution_v2_design_2026-10-02/legacy-freeze.json',
 'references/execution_v2_design_2026-10-02/sizing.json',
}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def route_bytes(path,canonical,title):
 target=posixpath.relpath(canonical,posixpath.dirname(path))
 frozen='https://github.com/jack0682/rx_docs/blob/'+DOCS_COMMIT+'/'+canonical
 return (f'# {title} — compatibility route\n\n'
  'This page preserves the relative link in the byte-frozen workflow-execution/v2 contract. '
  'It is navigation only: it has no independent normative authority and is not a replacement contract or a content mirror.\n\n'
  f'- [Current canonical document]({target})\n'
  f'- [Immutable document used at migration]({frozen})\n\n'
  'The original rx_docs history and the referenced contract bytes remain unchanged. '
  'Migration does not accept a Run, settle UNKNOWN, or qualify a physical installation.\n').encode()
def mapped(path):
 for old,new in [('rx_docs/docs/contracts','contracts/semantic'),('rx_docs/docs/cell_operations','contracts/cell-operations'),('rx_docs/docs','docs'),('rx_docs/references','references')]:
  if path==old:return new
  if path.startswith(old+'/'):return new+path[len(old):]
 raise ValueError('Unmapped historical document path: '+path)
def safe(root,path,exists=True):
 if not isinstance(path,str) or '\\' in path or '\0' in path:raise ValueError('Invalid path')
 rel=PurePosixPath(path)
 if rel.is_absolute() or '..' in rel.parts or str(rel)!=path:raise ValueError('Unsafe path: '+path)
 target=root/path
 for p in [target,*target.parents]:
  if p.is_symlink():raise ValueError('Symlink refused: '+path)
  if p==root:break
 if not target.resolve().is_relative_to(root.resolve()):raise ValueError('Path escapes root: '+path)
 if exists and not target.is_file():raise ValueError('Missing regular file: '+path)
 return target
def current_path(historical):
 return mapped(historical) if historical.startswith('rx_docs/') else historical

def check(root):
 root=Path(root).resolve()
 map_raw=safe(root,'provenance/import/M4-canonical-document-map.json').read_bytes()
 if sha(map_raw)!=M4_MAP_SHA256:raise ValueError('Historical M4 migration map changed')
 manifest=json.loads(map_raw)
 if manifest.get('schema')!='rx.canonical-document-migration.v1' or manifest.get('phase')!='M4':raise ValueError('Unexpected canonical map schema')
 if manifest.get('source_import_commit')!=IMPORT_COMMIT or manifest.get('source_docs_commit')!=DOCS_COMMIT:raise ValueError('Migration origin differs')
 origin_raw=safe(root,'provenance/import/M3-document-origins.json').read_bytes()
 if sha(origin_raw)!=manifest['m3_document_origins_sha256']:raise ValueError('Historical M3 origin index changed')
 origin=json.loads(origin_raw)
 imported=json.loads(safe(root,'provenance/import/M2-source-manifest.json').read_text())['payload']['files']
 import_docs={r['target_path']:r for r in imported if r['target_path'].startswith('rx_docs/')}
 if len(import_docs)!=121:raise ValueError('Imported document inventory differs')
 moves=manifest['moves']
 if len(moves)!=121 or {r['source_path'] for r in moves}!=set(import_docs) or len({r['target_path'] for r in moves})!=121:raise ValueError('Migration coverage/collision differs')
 for record in moves:
  old,new=record['source_path'],record['target_path'];expected=import_docs[old]
  if new!=mapped(old) or record['import_sha256']!=expected['sha256'] or record['source_blob_oid']!=expected['blob_oid'] or record['mode']!=expected['mode']:raise ValueError('Migration source/target differs: '+old)
  if safe(root,old,exists=False).exists():raise ValueError('Old imported document still owns a path: '+old)
  safe(root,new)
 # Hash-bound inventory comes from the unchanged historical M3 record, not a new allowlist.
 expected_bound={mapped(r['path']):r['sha256'] for r in origin['hash_bound_documents']}
 bound=manifest['hash_bound_documents']
 if len(expected_bound)!=18 or len(bound)!=18 or {r['path']:r['sha256'] for r in bound}!=expected_bound:raise ValueError('Hash-bound inventory differs')
 for path,expected in expected_bound.items():
  if sha(safe(root,path).read_bytes())!=expected:raise ValueError('Hash-bound bytes changed: '+path)
 # Keep all 24 published v1.0 mirror files byte-identical, not only the eight normative MDs.
 expected_mirrors={}
 for record in moves:
  path=record['target_path']
  for prefix,consumer in [('contracts/semantic/v1.0/','spec/contracts/v1.0/'),('contracts/cell-operations/v1.0/','spec/cell_operations/v1.0/')]:
   if path.startswith(prefix):expected_mirrors[path]=(f'rx-platform/{consumer}'+path[len(prefix):],f'rx-solutions/sdk/{consumer}'+path[len(prefix):])
 mirrors=manifest['contract_mirrors']
 if len(expected_mirrors)!=24 or len(mirrors)!=24 or {r['canonical']:(r['platform'],r['solutions']) for r in mirrors}!=expected_mirrors:raise ValueError('Contract mirror inventory differs')
 for canonical,(platform,solutions) in expected_mirrors.items():
  raw=safe(root,canonical).read_bytes()
  if raw!=safe(root,platform).read_bytes() or raw!=safe(root,solutions).read_bytes():raise ValueError('Canonical/mirror bytes differ: '+canonical)
 projections=manifest['compatibility_projections']
 expected_paths=set(ROUTES)|JSON_PROJECTIONS
 if len(projections)!=4 or {r['path'] for r in projections}!=expected_paths:raise ValueError('Finite compatibility inventory differs')
 workflow=safe(root,'contracts/semantic/workflow-execution/v2/README.md').read_text()
 for record in projections:
  path=record['path'];raw=safe(root,path).read_bytes()
  if sha(raw)!=record['sha256'] or len(raw)!=record['bytes']:raise ValueError('Compatibility projection changed: '+path)
  href=record['inbound_href']
  if ']('+href+')' not in workflow or posixpath.normpath(posixpath.join('contracts/semantic/workflow-execution/v2',href))!=path:raise ValueError('Compatibility route no longer matches bound link: '+path)
  if path in ROUTES:
   canonical,title=ROUTES[path]
   if record['disposition']!='COMPATIBILITY_ROUTING_NOT_CONTENT_MIRROR' or record['canonical_target']!=canonical or raw!=route_bytes(path,canonical,title):raise ValueError('Routing page authority/content differs: '+path)
   safe(root,canonical)
  else:
   original=import_docs['rx_docs/'+path]
   if record['disposition']!='EXACT_FROZEN_EVIDENCE_PROJECTION' or sha(raw)!=original['sha256'] or record['source_blob_oid']!=original['blob_oid']:raise ValueError('Evidence projection differs from original: '+path)
 reference_files={p.relative_to(root).as_posix() for p in (root/'references').rglob('*') if p.is_file() or p.is_symlink()}
 if reference_files!=JSON_PROJECTIONS:raise ValueError('Unexpected reference copy; evidence belongs to rx_docs')
 return {'moves':121,'hash_bound_documents':18,'v1_contract_mirrors':24,'exact_evidence_projections':2,'navigation_only_routes':2,'ordinary_current_bytes':'EDITABLE_NOT_FROZEN','scope':'CANONICAL_LAYOUT_NOT_RUNTIME_ACCEPTANCE'}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
 print(json.dumps(check(args.root),sort_keys=True))
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError,TypeError) as e:print('Canonical layout: '+str(e),file=sys.stderr);raise SystemExit(1)
