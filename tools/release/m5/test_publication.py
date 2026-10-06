import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import publish_ci_evidence as publisher
import package_handoff as handoff

ROOT=Path(__file__).resolve().parent

class Publication(unittest.TestCase):
    def setUp(self):
        (ROOT/'.test-work').mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.test-work');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'approved'
    def invoke(self,mode):
        with patch('sys.argv',['publish','--mode',mode,'--runner-temp',str(self.root),'--output',str(self.out)]),contextlib.redirect_stdout(io.StringIO()):
            publisher.main()
    def test_sdk_without_credentials_is_explicit_marker_scope(self):
        work=self.root/'m5-sdk-consumer';work.mkdir();(work/'result.json').write_text('{"component":"safe"}')
        self.invoke('sdk')
        audit=json.loads((self.out/'LEAK_AUDIT.json').read_text());self.assertEqual(audit['status'],'PUBLIC_EVIDENCE_APPROVED')
        self.assertEqual(audit['secret_classes_observed'],{})
        scope=json.loads((self.out/'evidence/PUBLICATION_SCOPE.json').read_text())
        self.assertEqual(scope['private_value_scan_scope'],'NO_PRIVATE_FIXTURES_GENERATED_IN_SDK_CONSUMER')
        self.assertTrue(scope['generic_private_key_markers_checked'])
    def test_sdk_private_key_marker_refuses_payload_publication(self):
        work=self.root/'m5-sdk-consumer';work.mkdir();(work/'failure.stderr').write_text('-----BEGIN PRIVATE KEY-----\nfixture')
        with self.assertRaises(SystemExit):self.invoke('sdk')
        self.assertEqual({p.name for p in self.out.iterdir()},{'LEAK_AUDIT.json'})
        self.assertNotIn('fixture',(self.out/'LEAK_AUDIT.json').read_text())
    def test_producer_missing_actual_private_inventory_refuses_with_receipt(self):
        work=self.root/'m5-dist-work';work.mkdir();(work/'build.stderr').write_text('possibly private diagnostic')
        with self.assertRaises(SystemExit):self.invoke('producer')
        self.assertEqual({p.name for p in self.out.iterdir()},{'LEAK_AUDIT.json'})
    def test_producer_actual_uploaded_artifact_is_scanned(self):
        private=self.root/'m5-local-work/private-acceptance/state';private.mkdir(parents=True)
        first='first-fixture-token-for-detection-only';second='second-fixture-token-for-detection-only'
        (private/'client-token').write_text(first);(private/'worker-token').write_text(second)
        sdk=self.root/'m5-sdk';sdk.mkdir();(sdk/'leaked.json').write_text(json.dumps({'bad':first}))
        with self.assertRaises(SystemExit):self.invoke('producer')
        self.assertEqual({p.name for p in self.out.iterdir()},{'LEAK_AUDIT.json'})
        self.assertNotIn(first,(self.out/'LEAK_AUDIT.json').read_text())
    def test_registered_inner_refusal_never_reselects_raw_evidence(self):
        root=self.root/'m5-runtime-consumer/registered/normal';private=root/'private';private.mkdir(parents=True)
        key='fixture-private-key-contents-not-a-real-key';password='fixture-password-only'
        (private/'fixture.key').write_text(key);(private/'operator.password').write_text(password)
        raw=root/'evidence';raw.mkdir();(raw/'secret.json').write_text(json.dumps({'value':key}))
        approved=root/'public-approved';approved.mkdir();(approved/'LEAK_AUDIT.json').write_text('{"status":"PUBLIC_EVIDENCE_REFUSED"}')
        self.invoke('runtime')
        public=self.out/'evidence/runtime-consumer/registered/normal'
        self.assertFalse((public/'evidence').exists())
        self.assertEqual(json.loads((public/'public-approved/LEAK_AUDIT.json').read_text())['status'],'PUBLIC_EVIDENCE_REFUSED')
        self.assertNotIn(key,'\n'.join(p.read_text() for p in self.out.rglob('*') if p.is_file()))
    def test_handoff_rejects_extra_file(self):
        root=self.root/'handoff';root.mkdir();tools={}
        for name in handoff.TOOLS:(root/name).write_text(name);tools[name]=handoff.sha_file(root/name)
        (root/'control.json').write_text(json.dumps({'schema':'rx.m5.ci-handoff.v1','tools':tools}))
        handoff.verify_tools(root)
        (root/'unlisted.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'extra'):handoff.verify_tools(root)


if __name__=='__main__':unittest.main()
