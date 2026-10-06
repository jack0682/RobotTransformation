"""Only fabricated strings/DER fixtures; never real key generation or product execution."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch

from leak_audit import (collect_private,approve_public,refuse_public,retained_tempdir_type,AuditIncomplete)

HERE=Path(__file__).resolve().parent
SEED=bytes(range(1,33))
DER=bytes.fromhex('302e020100300506032b657004220420')+SEED
BODY=base64.b64encode(DER)
PEM=b'-----BEGIN PRIVATE KEY-----\n'+BODY+b'\n-----END PRIVATE KEY-----\n'
PASSWORD='fixture-password-never-a-real-credential'
TOKEN='fixture_token_0123456789abcdef0123456789abcdef'


class LeakTests(unittest.TestCase):
    def scope(self):
        temp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(temp.cleanup)
        root=Path(temp.name);private=root/'private';private.mkdir();public=root/'raw';public.mkdir()
        (private/'key.pem').write_bytes(PEM)
        (private/'signing-fixtures.json').write_text(json.dumps({'keys':[{'private_seed_hex':SEED.hex(),'public_key':'f'*64}]}))
        (private/'browser.json').write_text(json.dumps({'credentials':{'engineer':PASSWORD}}))
        (private/'client-token').write_text(TOKEN)
        return root,private,public,collect_private([private],required_minimums={'PRIVATE_KEY':1,'PRIVATE_SEED':1,'PASSWORD':1,'TOKEN':1})

    def test_actual_key_body_seed_token_and_password_refused_without_values(self):
        cases=[PEM,BODY,SEED,SEED.hex().encode(),TOKEN.encode(),PASSWORD.encode(),json.dumps(PEM.decode()).encode()]
        for index,secret in enumerate(cases):
            with self.subTest(index=index):
                root,private,public,inventory=self.scope();(public/'log.stdout').write_bytes(b'prefix '+secret+b' suffix')
                approved=root/'approved';receipt=approve_public(inventory,public,approved,extra_documents={'result.json':{'status':'PASS'}})
                self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
                self.assertEqual({f.name for f in approved.iterdir()},{'LEAK_AUDIT.json'})
                safe=(approved/'LEAK_AUDIT.json').read_bytes()
                for value in [SEED.hex().encode(),TOKEN.encode(),PASSWORD.encode(),BODY,hashlib.sha256(PASSWORD.encode()).hexdigest().encode()]:
                    self.assertNotIn(value,safe)
                self.assertIn(secret,(public/'log.stdout').read_bytes())

    def test_public_keys_hashes_paths_and_unrelated_words_are_allowed(self):
        root,private,public,inventory=self.scope()
        payload={'public_key':'f'*64,'verifying_key':'e'*64,'signature':'d'*128,
            'private_key':'/terminal/private_key','password_file':'/terminal/engineer.password',
            'password_field_schema':'string','note':'No credential value here'}
        (public/'observation.json').write_text(json.dumps(payload))
        receipt=approve_public(inventory,public,root/'approved',extra_documents={'result.json':{'status':'PASS_FOR_REPORTED_SCOPE'}})
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_APPROVED')
        self.assertEqual(json.loads((root/'approved/evidence/observation.json').read_bytes()),payload)
        self.assertTrue((root/'approved/evidence/result.json').exists())
        self.assertNotIn(PASSWORD,repr(inventory))

    def test_extra_result_cannot_bypass_scan(self):
        root,private,public,inventory=self.scope()
        receipt=approve_public(inventory,public,root/'approved',extra_documents={'result.json':{'debug':PASSWORD}})
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
        self.assertFalse((root/'approved/evidence').exists())

    def test_nested_compressed_log_is_checked(self):
        root,private,public,inventory=self.scope()
        inner=gzip.compress(('password='+PASSWORD).encode())
        archive=public/'logs.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            item=tarfile.TarInfo('logs/trace.gz');item.size=len(inner);tar.addfile(item,io.BytesIO(inner))
        receipt=approve_public(inventory,public,root/'approved')
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
        self.assertEqual(receipt['reason'],'ACTUAL_PRIVATE_VALUE_FOUND')

    def test_compressed_secret_detected_even_without_extension(self):
        root,private,public,inventory=self.scope()
        (public/'opaque-blob').write_bytes(gzip.compress(TOKEN.encode()))
        receipt=approve_public(inventory,public,root/'approved')
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
        self.assertEqual(receipt['reason'],'ACTUAL_PRIVATE_VALUE_FOUND')

    def test_unknown_and_oversized_scope_fails_closed(self):
        root,private,public,inventory=self.scope();(public/'large').write_bytes(b'a'*64)
        receipt=approve_public(inventory,public,root/'approved',max_member_bytes=32)
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
        empty=root/'empty-private';empty.mkdir()
        with self.assertRaises(AuditIncomplete):collect_private([empty])
        with self.assertRaises(AuditIncomplete):collect_private([private],required_minimums={'TOKEN':2})

    def test_copy_race_cannot_publish_changed_bytes(self):
        root,private,public,inventory=self.scope();source=public/'clean.json';source.write_text('{}')
        def unsafe_copy(a,b):Path(b).write_text(PASSWORD)
        with patch('leak_audit.shutil.copyfile',side_effect=unsafe_copy):
            receipt=approve_public(inventory,public,root/'approved')
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')
        self.assertEqual({p.name for p in (root/'approved').iterdir()},{'LEAK_AUDIT.json'})

    def test_public_symlink_cannot_expose_private_tree(self):
        root,private,public,inventory=self.scope();(public/'alias').symlink_to(private/'key.pem')
        receipt=approve_public(inventory,public,root/'approved')
        self.assertEqual(receipt['status'],'PUBLIC_EVIDENCE_REFUSED')

    def test_refusal_reason_cannot_echo_a_password(self):
        root,private,public,inventory=self.scope();receipt=refuse_public(root/'approved',PASSWORD)
        self.assertEqual(receipt['reason'],'AUDIT_UNAVAILABLE')
        self.assertNotIn(PASSWORD,json.dumps(receipt))

    def test_registered_tempdir_retention_does_not_change_other_cleanup(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);retained=root/'retained';retained.mkdir()
            adapted=retained_tempdir_type(tempfile.TemporaryDirectory,retained)
            with adapted(prefix='rx-installed-acceptance-') as selected:
                Path(selected,'client-token').write_text(TOKEN)
            self.assertTrue(Path(selected).is_relative_to(retained));self.assertTrue(Path(selected,'client-token').exists())
            with adapted(prefix='unrelated-',dir=root) as normal:Path(normal,'value').write_text('fixture')
            self.assertFalse(Path(normal).exists())
            collected=collect_private([retained],required_minimums={'TOKEN':1})
            self.assertEqual(collected.counts['TOKEN'],1)


if __name__=='__main__':unittest.main()
