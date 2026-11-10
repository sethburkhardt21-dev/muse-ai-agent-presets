"""Portable path contract, including Windows ADS/device forms tested as inputs."""
from pathlib import Path
import tempfile
import os
import unittest
from muse_presets import model_toy_bundle as b, model_toy_math as m
from test_model_toy_math import example

class PortablePathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='r60-portable-paths-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.data=self.root/'dataset.json';raw=m.canonical_json(example());self.data.write_bytes(raw)
        self.pin=m.digest(raw)

    def refuse(self,name):
        with self.assertRaisesRegex(m.Refused,'PATH'):
            b.run_experiment(self.data,self.pin,self.root/name,reviewed_data=True)
        self.assertFalse((self.root/name).exists())

    def test_windows_alternate_data_stream_refused(self):
        self.refuse('existing-owner.txt:checkpoint')

    def test_windows_device_names_refused(self):
        for name in ('CON','prn','AUX','nul.json','COM1','LPT9.json','con.txt','COM\u00b9'):
            with self.subTest(name=name):self.refuse(name)

    def test_windows_trailing_dot_and_space_refused(self):
        for name in ('output.','output '):
            with self.subTest(name=name):self.refuse(name)

    def test_cross_platform_path_metacharacters_refused(self):
        # On Windows a backslash is parsed as a path separator, not a filename
        # character. A missing intermediate directory still must fail closed.
        names=('a|b','a*b','a?b','a<b','a>b','a"b','a\nb')
        if os.name!='nt':
            names=('a\\b',)+names
        for name in names:
            with self.subTest(name=name):self.refuse(name)
        if os.name=='nt':
            with self.assertRaisesRegex(m.Refused,'PARENT_MISSING'):
                b.run_experiment(self.data,self.pin,self.root/'a'/'b',reviewed_data=True)
            self.assertFalse((self.root/'a').exists())

    def test_normal_space_and_unicode_directory_allowed(self):
        target=self.root/'toy results é'
        result=b.run_experiment(self.data,self.pin,target,reviewed_data=True)
        self.assertEqual(result['status'],'LOCAL_TOY_EXPERIMENT_RECORDED')

if __name__=='__main__':unittest.main()
