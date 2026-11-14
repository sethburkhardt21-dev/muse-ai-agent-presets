"""The downloadable product must contain verified usable packages, not counts alone."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,importlib.util,io,json,unittest,zipfile
R=Path(__file__).resolve().parents[1]

class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=R/'examples/export_specialist_collection.py'
        if not path.is_file():return
        spec=importlib.util.spec_from_file_location('r5_distribution',path)
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
        cls.payload=cls.module.build_bundle()

    def require_bundle(self):
        self.assertTrue(hasattr(self,'payload'),'Reproducible collection bundle exporter has not been implemented')

    def test_download_contains_100_starters_and_four_real_extension_kits(self):
        self.require_bundle()
        with zipfile.ZipFile(io.BytesIO(self.payload)) as z:
            names=z.namelist()
            self.assertEqual(len([n for n in names if n.startswith('starters/') and n.endswith('.zip')]),100)
            self.assertEqual(len([n for n in names if n.startswith('kits/') and n.endswith('.zip')]),4)
            self.assertEqual(len(json.loads(z.read('SPECIALISTS.json'))),15)
            self.assertIn('START_HERE.md',names)

    def test_outer_and_all_nested_package_hashes_are_valid(self):
        self.require_bundle()
        with zipfile.ZipFile(io.BytesIO(self.payload)) as z:
            manifest=json.loads(z.read('BUNDLE_MANIFEST.json'))
            self.assertEqual(set(z.namelist()),set(manifest['files'])|{'BUNDLE_MANIFEST.json'})
            for name,pin in manifest['files'].items():
                raw=z.read(name);self.assertEqual(hashlib.sha256(raw).hexdigest(),pin)
                if name.endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(raw)) as inner:
                        sub=json.loads(inner.read('MANIFEST.json'))
                        for item,expected in sub['files'].items():
                            self.assertEqual(hashlib.sha256(inner.read(item)).hexdigest(),expected)
            self.assertFalse(manifest['native_agents_installed'])
            self.assertEqual(manifest['standalone_extensions_packaged'],4)

    def test_bundle_contains_actual_local_results_and_honest_workflow_limits(self):
        self.require_bundle()
        with zipfile.ZipFile(io.BytesIO(self.payload)) as z:
            reports=[n for n in z.namelist() if n.startswith('reports/')]
            self.assertEqual(len(reports),9)
            for name in reports:
                report=json.loads(z.read(name))
                self.assertTrue(report['results']);self.assertFalse(report['external_actions_performed'])
                if 'workflow' in report:self.assertFalse(report['full_workflow_executed'])

    def test_existing_download_destination_is_not_overwritten(self):
        self.require_bundle()
        with TemporaryDirectory() as directory:
            destination=Path(directory)/'bundle.zip';destination.write_bytes(b'owned-content')
            self.assertEqual(self.module.main(['--to',str(destination)]),2)
            self.assertEqual(destination.read_bytes(),b'owned-content')

if __name__=='__main__':unittest.main()
