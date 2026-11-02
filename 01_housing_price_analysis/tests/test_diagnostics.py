import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd
import statsmodels.api as sm
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from diagnostics import FEATURES, centered_vif, fit_final, load_sample

class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_sample()
        cls.model = fit_final(cls.df)
        cls.baseline = json.loads((PROJECT/'tests/original_model_baseline.json').read_text())

    def test_data_and_sample_preserved(self):
        for name, digest in self.baseline['data_sha256'].items():
            self.assertEqual(hashlib.sha256((PROJECT/'data/processed'/name).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.df), 3052)
        self.assertEqual(self.df.fips.nunique(), 3052)
        self.assertTrue(self.df.fips.str.fullmatch(r'\d{5}').all())

    def test_vif_against_independent_correlation_inverse(self):
        got = centered_vif(sm.add_constant(self.df[FEATURES]))
        self.assertEqual(got.Variable.tolist(), FEATURES)
        np.testing.assert_allclose(got.VIF, np.diag(np.linalg.inv(self.df[FEATURES].corr())), rtol=1e-9)
        np.testing.assert_allclose(got.VIF, [2.673121,2.666541,1.542502,1.257323,1.309659], atol=5e-7)

    def test_translation_and_units_invariance(self):
        original = centered_vif(sm.add_constant(self.df[FEATURES]))
        changed = self.df[FEATURES]*[.001,100,2,10,100]+[12,5,20,2,10]
        np.testing.assert_allclose(centered_vif(sm.add_constant(changed)).VIF, original.VIF, rtol=1e-9)

    def test_model_and_inference_unchanged(self):
        m, b = self.model, self.baseline
        before = [v.copy() for v in [m.params,m.bse,m.pvalues,m.fittedvalues,m.resid]]
        centered_vif(pd.DataFrame(m.model.exog, columns=m.model.exog_names))
        for old, new in zip(before,[m.params,m.bse,m.pvalues,m.fittedvalues,m.resid]):
            np.testing.assert_array_equal(old,new)
        for key in ['params','bse','pvalues']:
            np.testing.assert_allclose(getattr(m,key),b[key],rtol=1e-8,atol=1e-100)
        h = m.get_robustcov_results(cov_type='HC3')
        np.testing.assert_allclose(h.bse,b['hc3_bse'],rtol=1e-8)
        np.testing.assert_allclose(h.pvalues,b['hc3_pvalues'],rtol=1e-8,atol=1e-100)
        self.assertAlmostEqual(m.rsquared,b['rsquared'],places=12)
        self.assertTrue((h.pvalues[1:] < .05).all())

    def test_invalid_design(self):
        X = self.df[FEATURES].copy()
        with self.assertRaises(ValueError): centered_vif(X)
        X = sm.add_constant(X)
        X.loc[0,FEATURES[0]] = np.nan
        with self.assertRaises(ValueError): centered_vif(X)
        X.loc[:,FEATURES[0]] = 1
        with self.assertRaises(ValueError): centered_vif(X)

    def test_influence_screening(self):
        cooks = self.model.get_influence().cooks_distance[0]
        self.assertAlmostEqual(float(cooks.max()),.03449101571843338,places=10)
        self.assertEqual(int((cooks > 4/self.model.nobs).sum()),176)
        self.assertEqual(int((cooks > 1).sum()),0)

    def test_actual_notebook_diagnostic_cell(self):
        n=json.loads((PROJECT/'notebooks/04_interpretable_modeling.ipynb').read_text())
        scope={'BASE_DIR':PROJECT,'X':sm.add_constant(self.df[FEATURES])}
        exec(''.join(n['cells'][25]['source']),scope)
        np.testing.assert_allclose(scope['vif_table'].VIF,centered_vif(scope['X']).VIF)

if __name__ == '__main__': unittest.main()
