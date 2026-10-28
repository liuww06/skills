import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('evaluation', ROOT / 'scripts/evaluate.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class EvaluationTests(unittest.TestCase):
    def test_missing_sdk_is_blocked_not_passed(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/test-engineering.py'),
                                     '--dotnet', str(Path(temp) / 'missing-sdk'), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(2, result.returncode, result.stderr)
            report = evaluation.load_json(output / 'results.json')
            self.assertEqual('blocked', report['records'][0]['status'])

    def test_every_skill_has_four_routing_scenarios(self):
        cases = evaluation.load_json(ROOT / 'evals/cases.json')['cases']
        self.assertEqual(len(cases), len({c['id'] for c in cases}))
        for skill in (ROOT / 'plugins/engineering/skills').iterdir():
            scenarios = {c['scenario'] for c in cases if c['skill'] == skill.name}
            self.assertEqual({'positive', 'adjacent', 'insufficient', 'restricted'}, scenarios)
        for case in cases:
            self.assertTrue((ROOT / 'plugins/engineering/skills' / case['skill'] / 'SKILL.md').is_file())
            self.assertTrue(case['prompt'] and case['rubric'])
            self.assertIn(case.get('mutation'), {None, 'comment-only'} | set(evaluation.fixtures.MUTATIONS))

    def test_prepared_bug_and_user_edits_are_isolated(self):
        case = next(c for c in evaluation.load_json(ROOT / 'evals/cases.json')['cases'] if c['id'] == 'bugfix-user-edits')
        before = evaluation.snapshot(evaluation.fixtures.FIXTURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'case'
            manifest = evaluation.prepare(case, output, 'enabled')
            source = (output / 'workspace/src/Pricing/PriceCalculator.cs').read_text(encoding='utf-8')
            self.assertIn('quantity > 10', source)
            self.assertIn('user note:', source)
            self.assertTrue((output / 'workspace/user-notes.txt').is_file())
            self.assertEqual(manifest['before'], evaluation.snapshot(output / 'workspace'))
        self.assertEqual(before, evaluation.snapshot(evaluation.fixtures.FIXTURE))

    def test_zero_missing_skipped_and_failed_results(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with self.assertRaisesRegex(ValueError, 'no TRX'):
                evaluation.fixtures.test_results(directory)
            for total, executed, passed, failed, valid in (
                (0, 0, 0, 0, False), (2, 0, 0, 0, False), (2, 1, 1, 0, False),
                (1, 1, 0, 1, True), (2, 2, 2, 0, True)):
                with self.subTest(total=total, passed=passed):
                    (directory / 'test.trx').write_text(f'<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010"><ResultSummary><Counters total="{total}" executed="{executed}" passed="{passed}" failed="{failed}" /></ResultSummary></TestRun>', encoding='utf-8')
                    if valid:
                        self.assertEqual(total, evaluation.fixtures.test_results(directory)['total'])
                    else:
                        with self.assertRaises(ValueError):
                            evaluation.fixtures.test_results(directory)

    def test_pass_record_requires_model_exit_and_independent_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'host.log').write_text('host evidence', encoding='utf-8')
            (directory / 'grade.md').write_text('reviewed source, commands and assertions', encoding='utf-8')
            record = {'case_id':'change-review-clean','layer':'agent','host':'fixture-host',
                      'host_version':'1.0','model_version':'model-version','skill_version':'engineering@0.1.0',
                      'condition':'enabled','timestamp':'2026-10-28T00:00:00Z', 'status':'passed',
                      'exit_code':0, 'reason':'independent review found no regression',
                      'evidence':['host.log','grade.md'], 'checks':[{'status':'passed','evidence':'grade.md'}]}
            path = directory / 'record.json'
            path.write_text(json.dumps(record), encoding='utf-8')
            self.assertEqual('passed', evaluation.validate_record(path)['status'])
            for change in ({'model_version':None}, {'exit_code':9}, {'checks':[]},
                           {'evidence':['missing']}, {'evidence':['../outside']}, {'status':'PASS'}):
                with self.subTest(change=change):
                    path.write_text(json.dumps(record | change), encoding='utf-8')
                    with self.assertRaises(ValueError):
                        evaluation.validate_record(path)


if __name__ == '__main__':
    unittest.main()
