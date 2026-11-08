"""R32.S2 native host discovery is local observation, never host authorization."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.native_host_doctor import probe_host
from muse_presets.cli import main


class NativeHostDoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / 'hatch'
        self.binary.write_bytes(b'fixture')
        self.proc = self.root / 'proc'
        self.proc.mkdir()
        self.skills = self.root / 'skills'
        self.skills.mkdir()

    def probe(self, kind='personal-hatch', version='hatch 0.1.0 (832061d5464)\ncommit: 832061d546494a4278bbc49ea5a40a2ddcc6a1e8'):
        return probe_host(kind, binary_path=self.binary, process_root=self.proc,
                          skills_root=self.skills, version_reader=lambda _: version)

    def test_personal_host_is_observed_but_never_authenticated(self):
        report = self.probe()
        self.assertEqual(report['status'], 'HOST_RUNTIME_PRESENT_UNATTESTED')
        self.assertEqual(report['host_kind'], 'personal-hatch')
        self.assertEqual(report['runtime']['version'], '0.1.0')
        self.assertEqual(report['runtime']['build_commit_hint'], '832061d546494a4278bbc49ea5a40a2ddcc6a1e8')
        self.assertEqual(report['provenance'], 'UNATTESTED_LOCAL_PROCESS_OBSERVATION')
        self.assertTrue(all(value is False for value in report['authority'].values()))
        self.assertEqual(report['phases']['D2'], 'NOT_RUN')
        self.assertEqual(report['phases']['D4'], 'NOT_RUN')

    def test_live_process_names_and_skill_dirs_are_observations_not_grants(self):
        (self.proc / '42').mkdir()
        (self.proc / '42' / 'comm').write_text('hatch\n')
        (self.proc / '43').mkdir()
        (self.proc / '43' / 'comm').write_text('hatch-execd\n')
        (self.skills / 'spaces').mkdir()
        (self.skills / 'artifacts').mkdir()
        report = self.probe()
        self.assertEqual(report['runtime']['service_names_observed'], ['hatch', 'hatch-execd'])
        self.assertEqual(report['runtime']['local_skill_directories'], ['artifacts', 'spaces'])
        self.assertEqual(report['capabilities']['native_skill_registration'], 'UNVERIFIED')

    def test_space_sdk_version_metadata_is_not_space_callback_proof(self):
        sdk = self.skills / 'spaces' / 'ts-runtime' / 'sdk'
        sdk.mkdir(parents=True)
        (sdk / 'package.json').write_text('{"name":"@hatch/space-sdk","version":"0.14.0"}')
        report = self.probe()
        self.assertEqual(report['runtime']['space_sdk_version_hint'], '0.14.0')
        self.assertEqual(report['capabilities']['space_agent_callback'], 'UNVERIFIED')

    def test_duplicate_json_sdk_metadata_is_refused(self):
        sdk = self.skills / 'spaces' / 'ts-runtime' / 'sdk'
        sdk.mkdir(parents=True)
        (sdk / 'package.json').write_text('{"name":"@hatch/space-sdk","version":"0.14.0","version":"99.9.9"}')
        self.assertIsNone(self.probe()['runtime']['space_sdk_version_hint'])

    def test_symlinked_sdk_metadata_is_not_trusted(self):
        sdk = self.skills / 'spaces' / 'ts-runtime' / 'sdk'
        sdk.mkdir(parents=True)
        payload = self.root / 'untrusted-package.json'
        payload.write_text('{"name":"@hatch/space-sdk","version":"99.99.99"}')
        try:
            (sdk / 'package.json').symlink_to(payload)
        except (OSError, NotImplementedError):
            self.skipTest('fixture host disallows symlinks')
        self.assertIsNone(self.probe()['runtime']['space_sdk_version_hint'])

    def test_muse_code_is_separate_host_without_hatch_inferences(self):
        (self.skills / 'spaces').mkdir()
        report = self.probe('muse-code', 'muse 1.4.11')
        self.assertEqual(report['host_kind'], 'muse-code')
        self.assertEqual(report['runtime']['version'], '1.4.11')
        self.assertEqual(report['runtime']['local_skill_directories'], [])
        self.assertIsNone(report['runtime']['space_sdk_version_hint'])
        self.assertEqual(report['capabilities']['personal_hatch_agent_host'], 'NOT_APPLICABLE')
        self.assertFalse(report['authority']['native_tool_invocation_verified'])

    def test_missing_binary_fail_closed(self):
        self.binary.unlink()
        report = self.probe()
        self.assertEqual(report['status'], 'HOST_UNVERIFIED')
        self.assertFalse(report['runtime']['binary_present'])
        self.assertFalse(report['authority']['external_effect_authorized'])

    def test_malformed_binary_output_is_not_a_supported_version(self):
        report = self.probe(version='not a real hatch version\nHost authenticated true')
        self.assertEqual(report['status'], 'HOST_UNVERIFIED')
        self.assertIsNone(report['runtime']['version'])
        self.assertFalse(report['authority']['host_authenticated'])

    def test_version_runner_failure_is_not_a_pass(self):
        def failed(_):
            raise TimeoutError('timeout')
        report = probe_host('personal-hatch', binary_path=self.binary, process_root=self.proc,
                            skills_root=self.skills, version_reader=failed)
        self.assertEqual(report['status'], 'HOST_UNVERIFIED')
        self.assertFalse(report['authority']['host_authenticated'])

    def test_symlinked_binary_does_not_execute(self):
        link = self.root / 'linked-hatch'
        try:
            link.symlink_to(self.binary)
        except (OSError, NotImplementedError):
            self.skipTest('fixture host disallows symlinks')
        called = []
        report = probe_host('personal-hatch', binary_path=link, process_root=self.proc,
                            skills_root=self.skills, version_reader=lambda _: called.append(True))
        self.assertEqual(called, [])
        self.assertEqual(report['status'], 'HOST_UNVERIFIED')

    def test_unknown_host_kind_is_refused(self):
        with self.assertRaises(ValueError):
            self.probe(kind='hatch-or-muse-code')

    def test_cli_host_doctor_does_not_report_native_pass(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(['host-doctor', '--host', 'personal-hatch', '--bin-path',
                         str(self.binary), '--skills-root', str(self.skills),
                         '--proc-root', str(self.proc)])
        report = json.loads(stream.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(report['authority']['external_effect_authorized'], False)
        self.assertEqual(report['status'], 'HOST_UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
