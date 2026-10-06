"""Pure synthetic archive-closure tests; no old client bytecode/product API execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import historical_bundle as historical

HERE=Path(__file__).resolve().parent


class HistoricalTests(unittest.TestCase):
    def scope(self):
        temp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(temp.cleanup)
        root=Path(temp.name);client=root/'client';client.mkdir();rows=[]
        for name in sorted(historical.CLIENT_FILES):
            file=client/name;file.write_text('synthetic metadata fixture '+name);file.chmod(0o444)
            rows.append({'name':name,'bytes':file.stat().st_size,'sha256':historical.sha(file)})
        (root/'historical_runtime_probe.py').write_text('synthetic nonexecutable probe bytes')
        probe=historical.sha(root/'historical_runtime_probe.py')
        lock={'classification':'PUBLISHED_INSTALLED_RUNTIME_CLIENT','runtime_compatibility_status':'NOT_RUN',
              'release':{'sha256':'f'*64},'files':rows}
        (root/'HISTORICAL_CONSUMER_LOCK.json').write_text(json.dumps(lock));lock_sha=historical.sha(root/'HISTORICAL_CONSUMER_LOCK.json')
        origin={'classification':lock['classification'],'original_asset':lock['release'],'runtime_compatibility':'NOT_RUN',
            'new_sdk_relabelled_as_old':False,'materialization':{'runtime_executed':False},
            'tools':{'lock_sha256':lock_sha,'probe_sha256':probe}}
        (root/'ORIGIN.json').write_text(json.dumps(origin))
        for name in ['LICENSE','NOTICE']:(root/name).write_text('fixture only')
        self.enterContext(patch.object(historical,'LOCK_SHA',lock_sha));self.enterContext(patch.object(historical,'PROBE_SHA',probe))
        return root

    def test_exact_readonly_four_file_closure(self):
        root=self.scope();pins=historical.validate_historical_bundle(root)
        self.assertEqual(set(pins['client_files']),historical.CLIENT_FILES)
        (root/'client/current-client.py').write_text('wrong source')
        with self.assertRaises(ValueError):historical.validate_historical_bundle(root)

    def test_writable_or_changed_original_refused(self):
        root=self.scope();file=root/'client/rx';file.chmod(0o644)
        with self.assertRaises(ValueError):historical.validate_historical_bundle(root)
        file.write_text('changed');file.chmod(0o444)
        with self.assertRaises(ValueError):historical.validate_historical_bundle(root)

    def test_live_receipt_requires_idle_state_and_final_pins(self):
        root=self.scope();pins=historical.validate_historical_bundle(root)
        receipt={'schema':'rx.historical-runtime-consumer-probe.v1','status':'PASS_FOR_REPORTED_SCOPE',
            'classification':pins['classification'],'lock_sha256':pins['lock_sha256'],
            **{k:pins['client_files'] for k in ['before_file_sha256','after_file_sha256','final_file_sha256']},
            'public_before':{'installation':{'id':'same'},'runs':[],'work':[]},
            'public_after':{'installation':{'id':'same'},'runs':[],'work':[]},
            'negative':{'refused':True,'admitted_drafts_unchanged':True}}
        historical.validate_live_receipt(receipt,pins)
        for case in ['pins','run','state','negative']:
            bad=copy.deepcopy(receipt)
            if case=='pins':bad['final_file_sha256']['rx']='0'*64
            elif case=='run':bad['public_before']['runs']=['one'];bad['public_after']['runs']=['one']
            elif case=='state':bad['public_after']['installation']['id']='different'
            else:bad['negative']['admitted_drafts_unchanged']=False
            with self.subTest(case=case),self.assertRaises(ValueError):historical.validate_live_receipt(bad,pins)


if __name__=='__main__':unittest.main()
