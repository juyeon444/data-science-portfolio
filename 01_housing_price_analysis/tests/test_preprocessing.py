"""Boundary and regression checks for housing-data preprocessing and diagnostics."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from preprocessing import (validate_county_keys, extract_counties, merge_counties,
                           read_county_csv, education_shares, annual_available_months,
                           preserve_processed)
from diagnostics import population_doubling_effect


class PreprocessingTests(unittest.TestCase):
    def test_county_summary_level_and_pr(self):
        frame = pd.DataFrame({'GEO_ID': ['0500000US01001', '0400000US01000',
                              '1600000US01001', '0500000US72001', None]})
        self.assertEqual(extract_counties(frame).fips.tolist(), ['01001'])

    def test_bad_and_duplicate_keys(self):
        for keys in [[None], ['1001'], ['01000'], ['72001'], ['abcde'], ['01001', '01001']]:
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                validate_county_keys(pd.DataFrame({'fips': keys}))
        good = pd.DataFrame({'fips': ['01001']})
        with self.assertRaises(ValueError):
            merge_counties(good, pd.concat([good, good]))

    def test_csv_preserves_leading_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder)/'data.csv'
            f.write_text('fips,value\n01001,3\n')
            self.assertEqual(read_county_csv(f).fips.tolist(), ['01001'])

    def test_education_missing_partial_and_invalid_counts(self):
        good = pd.DataFrame({'total': [100], 'hs': [40], 'ba': [20]})
        ba, hs = education_shares(good, 'total', ['ba'], ['hs', 'ba'])
        self.assertEqual((ba.iloc[0], hs.iloc[0]), (.2, .6))
        for replacements in [{'ba': np.nan}, {'ba': np.nan, 'hs': np.nan},
                             {'ba': -1}, {'total': 0}, {'hs': 100}]:
            invalid = good.assign(**replacements)
            with self.subTest(replacements=replacements), self.assertRaises(ValueError):
                education_shares(invalid, 'total', ['ba'], ['hs', 'ba'])

    def test_available_month_policy(self):
        columns = pd.date_range('2022-01-01', periods=12, freq='ME').strftime('%Y-%m-%d')
        frame = pd.DataFrame([[100.]*12, [np.nan]+[110.]*11, [np.nan]*12], columns=columns)
        mean, counts = annual_available_months(frame)
        np.testing.assert_allclose(mean.iloc[:2], [100, 110])
        self.assertTrue(np.isnan(mean.iloc[2]))
        self.assertEqual(counts.tolist(), [12, 11, 0])
        with self.assertRaises(ValueError): annual_available_months(frame.drop(columns=columns[0]))
        with self.assertRaises(ValueError): annual_available_months(frame.assign(**{columns[0]: -1}))

    def test_preservation_does_not_rewrite_or_accept_changed_data(self):
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder)/'processed.csv'
            f.write_text('fips,value\n01001,1.0000\n')
            before = f.read_bytes()
            preserve_processed(pd.DataFrame({'fips': ['01001'], 'value': [1.]}), f)
            self.assertEqual(f.read_bytes(), before)
            with self.assertRaises(AssertionError):
                preserve_processed(pd.DataFrame({'fips': ['01001'], 'value': [2.]}), f)
            self.assertEqual(f.read_bytes(), before)

    def test_actual_census_notebook_rejects_incomplete_education(self):
        n = json.loads((PROJECT/'notebooks/02_census_preprocessing.ipynb').read_text())
        scope = dict(pd=pd, np=np, EXCLUDE_STATE_FIPS={'72'},
                     extract_counties=extract_counties, education_shares=education_shares)
        for cell in n['cells']:
            if cell['cell_type'] == 'code':
                definitions = [node for node in ast.parse(''.join(cell['source'])).body
                               if isinstance(node, ast.FunctionDef)]
                if definitions:
                    exec(compile(ast.Module(body=definitions, type_ignores=[]), 'census-notebook', 'exec'), scope)
        raw = {'GEO_ID':['0500000US01001'], 'NAME':['Synthetic county'], 'B15003_001E':[100]}
        raw.update({f'B15003_{i:03d}E':[1.] for i in range(17,26)})
        self.assertEqual(len(scope['preprocess_education'](pd.DataFrame(raw))), 1)
        for column in ['B15003_022E', 'B15003_017E']:
            with self.subTest(column=column), self.assertRaises(ValueError):
                scope['preprocess_education'](pd.DataFrame(raw).assign(**{column:np.nan}))
        self.assertTrue(scope['standardize_county_fips'](
            pd.DataFrame({'GEO_ID':['0400000US01000']})).empty)

    def test_population_doubling_exact_log1p_contrast(self):
        beta = .0303846632333451
        population = np.array([1., 100., 25000.])
        expected = 100*((((1+2*population)/(1+population))**beta)-1)
        np.testing.assert_allclose(population_doubling_effect(beta, population), expected, atol=1e-12)
        self.assertNotAlmostEqual(float(population_doubling_effect(beta, 25000)), 100*np.expm1(beta), places=2)
        for invalid in [0, -1, np.nan]:
            with self.assertRaises(ValueError): population_doubling_effect(beta, invalid)

    def test_actual_model_notebook_cells_against_original_baseline(self):
        # Execute the real model-loading/specification/effect/inference cells,
        # not a separate reconstruction using fit_final(). No notebook writes.
        n = json.loads((PROJECT/'notebooks/04_interpretable_modeling.ipynb').read_text())
        scope = dict(BASE_DIR=PROJECT, PROCESSED_DIR=PROJECT/'data/processed',
                     np=np, pd=pd, sm=sm, OLSInfluence=OLSInfluence,
                     read_county_csv=read_county_csv, merge_counties=merge_counties,
                     population_doubling_effect=population_doubling_effect)
        for idx in [4,6,12,15,17,19,25,28,31,34]:
            exec(''.join(n['cells'][idx]['source']), scope)
        b = json.loads((PROJECT/'tests/original_model_baseline.json').read_text())
        m, h = scope['final_model'], scope['final_model_hc3']
        self.assertEqual(m.model.exog_names, b['names'])
        self.assertEqual(m.nobs, b['nobs'])
        self.assertEqual(scope['df'].fips.nunique(), b['nobs'])
        self.assertTrue(scope['df'].fips.str.fullmatch(r'\d{5}').all())
        for key in ['params','bse','pvalues']:
            np.testing.assert_allclose(getattr(m,key), b[key], rtol=1e-8, atol=1e-100)
        np.testing.assert_allclose(h.bse, b['hc3_bse'], rtol=1e-8)
        np.testing.assert_allclose(h.pvalues, b['hc3_pvalues'], rtol=1e-8, atol=1e-100)
        np.testing.assert_allclose(m.fittedvalues, m.model.exog@np.array(b['params']), atol=1e-10)
        np.testing.assert_allclose(m.resid, m.model.endog-m.model.exog@np.array(b['params']), atol=1e-10)
        self.assertAlmostEqual(m.rsquared, b['rsquared'], places=12)
        effect = scope['effects']['Population: doubling at median P']
        self.assertAlmostEqual(effect, population_doubling_effect(m.params['log_population'], scope['reference_population']))

    def test_eda_format_does_not_round_income_to_zero(self):
        n=json.loads((PROJECT/'notebooks/03_housing_price_eda.ipynb').read_text())
        scope={'pd':pd,'comparison':pd.DataFrame({'Model 1':{'median_income_2022':1.162878076e-5}})}
        exec(''.join(n['cells'][42]['source']),scope)
        text=scope['comparison_fmt'].loc['median_income_2022','Model 1']
        self.assertGreater(float(text), 0)

if __name__ == '__main__': unittest.main()
