import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
CHECKER=HERE/'integration/overlay/tools/governance/check_m5_workflow.py'
WORKFLOW=HERE/'workflow.yml'
if not CHECKER.is_file():
    CHECKER=HERE.parents[2]/'tools/governance/check_m5_workflow.py'
    WORKFLOW=HERE.parents[2]/'.github/workflows/m5-artifact-candidate.yml'
spec=importlib.util.spec_from_file_location('m5_execution_policy',CHECKER)
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)

class Policy(unittest.TestCase):
    def setUp(self):self.workflow=WORKFLOW.read_text()
    def test_reviewed_shape(self):self.assertEqual(policy.workflow_errors(self.workflow),[])
    def test_path_filter_cannot_skip_changed_product_input(self):
        for key in ('paths','paths-ignore','branches-ignore'):
            value=self.workflow.replace('  pull_request:\n','  pull_request:\n    '+key+': [tools/**]\n')
            self.assertTrue(policy.workflow_errors(value))
    def test_tolerated_failure_or_privileged_event_refused(self):
        self.assertTrue(policy.workflow_errors(self.workflow+'\ncontinue-on-error: true\n'))
        self.assertTrue(policy.workflow_errors(self.workflow.replace('pull_request:\n','pull_request_target:\n')))
    def test_architecture_or_parallel_scope_reduction_refused(self):
        for value in (self.workflow.replace('arch: arm64','arch: other',1),self.workflow.replace('max-parallel: 2','max-parallel: 1',1)):
            self.assertTrue(policy.workflow_errors(value))
    def test_core_checkout_in_artifact_consumer_refused(self):
        value=self.workflow.replace('  sdk_consumer:\n','  sdk_consumer:\n    extra: actions/checkout@'+'a'*40+'\n')
        self.assertTrue(policy.workflow_errors(value))
    def test_provider_pin_required(self):
        self.assertTrue(policy.workflow_errors(self.workflow.replace('actions/checkout@11d5960a326750d5838078e36cf38b85af677262','actions/checkout@main')))
    def test_historical_scope_or_aggregate_reduction_refused(self):
        self.assertTrue(policy.workflow_errors(self.workflow.replace('prepare_historical_bundle.py','unrelated.py')))
        self.assertTrue(policy.workflow_errors(self.workflow.replace('needs: [produce, sdk_consumer, runtime_consumer]','needs: [produce]')))


if __name__=='__main__':unittest.main()
