"""Execute all four notebooks in fresh kernels and verify model/data preservation.

Run from repository root: python 01_housing_price_analysis/verify_notebooks.py --write
Requires the original raw inputs for notebooks 01/02; fails explicitly if absent.
--write refreshes notebook outputs only, after all four runs pass.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec

PROJECT = Path(__file__).resolve().parent


class ProjectKernel(KernelManager):
    @property
    def kernel_spec(self):
        return KernelSpec(argv=[sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                          display_name='Project Python', language='python')


def hashes(folder):
    return {str(f.relative_to(PROJECT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(folder.rglob('*')) if f.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    baseline = json.loads((PROJECT/'tests/original_model_baseline.json').read_text())
    required = ['zillow/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'] + [
        f'census/{name}' for name in ['B19013_income.csv','B01003_population.csv',
                                    'B15003_education.csv','B25010_household_size.csv','B23025_employment.csv']]
    missing = [name for name in required if not (PROJECT/'data/raw'/name).exists()]
    if missing:
        raise FileNotFoundError(f'Full preprocessing verification requires raw files: {missing}')
    before = hashes(PROJECT/'data')
    for name, digest in baseline['data_sha256'].items():
        assert before['data/processed/'+name] == digest, f'Baseline data changed: {name}'
    checks = {
        '01_zillow_preprocessing.ipynb': '''
assert len(zillow_2022) == 3061
assert month_coverage.observed_months_2022.value_counts().to_dict() == {12:3021,11:40}
''',
        '02_census_preprocessing.ipynb': '''
assert len(acs_features) == 3143
assert acs_features.fips.nunique() == 3143
assert not acs_features.isna().any().any()
''',
        '03_housing_price_eda.ipynb': '''
assert len(eda_df) == eda_df.fips.nunique() == 3052
assert float(comparison_fmt.loc['median_income_2022', 'Model 4']) > 0
''',
        '04_interpretable_modeling.ipynb': '''
import json
b = json.loads((BASE_DIR/'tests/original_model_baseline.json').read_text())
assert final_model.model.exog_names == b['names']
assert final_model.nobs == df.fips.nunique() == b['nobs']
assert df.fips.str.fullmatch(r'\\d{5}').all()
for key in ['params','bse','pvalues']:
    np.testing.assert_allclose(getattr(final_model,key),b[key],rtol=1e-8,atol=1e-100)
np.testing.assert_allclose(final_model_hc3.bse,b['hc3_bse'],rtol=1e-8)
np.testing.assert_allclose(final_model_hc3.pvalues,b['hc3_pvalues'],rtol=1e-8,atol=1e-100)
assert abs(final_model.rsquared-b['rsquared']) < 1e-12
np.testing.assert_allclose(final_model.fittedvalues,X.to_numpy()@np.array(b['params']),atol=1e-10)
np.testing.assert_allclose(final_model.resid,y-X.to_numpy()@np.array(b['params']),atol=1e-10)
np.testing.assert_allclose(vif_table.VIF,[2.673121,2.666541,1.542502,1.257323,1.309659],atol=5e-7)
expected = 100*np.expm1(final_model.params['log_population']*(np.log1p(2*reference_population)-np.log1p(reference_population)))
assert abs(effects['Population: doubling at median P']-expected) < 1e-12
assert abs(expected-2.1284) < .0001
assert int((cooks_d > 4/final_model.nobs).sum()) == 176
# Join monthly coverage only for validation; do not change the fitted sample.
raw = pd.read_csv(BASE_DIR/'data/raw/zillow/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
raw['fips'] = raw.StateCodeFIPS.astype(str).str.zfill(2)+raw.MunicipalCodeFIPS.astype(str).str.zfill(3)
_, raw['observed_months'] = annual_available_months(raw)
assert df[['fips']].merge(raw[['fips','observed_months']],on='fips',validate='one_to_one').observed_months.value_counts().to_dict() == {12:3012,11:40}
print('Validated final model, inference, VIF, effects and coverage')
'''}
    completed = []
    executed = []
    with tempfile.TemporaryDirectory(prefix='housing-notebooks-') as temp:
        os.environ['MPLCONFIGDIR'] = str(Path(temp)/'matplotlib')
        os.environ['XDG_CACHE_HOME'] = str(Path(temp)/'cache')
        os.environ['IPYTHONDIR'] = str(Path(temp)/'ipython')
        for name, check in checks.items():
            path = PROJECT/'notebooks'/name
            notebook = nbformat.read(path, as_version=4)
            original_count = len(notebook.cells)
            notebook.cells.append(nbformat.v4.new_code_cell(check))
            NotebookClient(notebook, timeout=180, kernel_manager_class=ProjectKernel,
                           resources={'metadata':{'path':str(path.parent)}}).execute()
            notebook.cells.pop()
            assert not any(o.output_type == 'error' for c in notebook.cells
                           for o in c.get('outputs', []))
            completed.append({'notebook':name,'cells':original_count,'validation':'passed'})
            executed.append((path,notebook))
            print(f'PASS {name} ({original_count} cells + validation)', flush=True)
    assert hashes(PROJECT/'data') == before, 'Data bytes changed during notebook execution'
    # Check public-facing numbers and period descriptions against computed invariants.
    readme = (PROJECT/'README.md').read_text()
    summary = (PROJECT/'executive_summary.md').read_text()
    for text in [readme, summary]:
        assert '2018–2022' in text and '3,052' in text and '40' in text
        assert '1.26' in text and '2.67' in text
    assert '2.128' in readme
    if args.write:
        for path, notebook in executed:
            nbformat.write(notebook, path)
        report = {'verified_at':datetime.now(ZoneInfo('America/Phoenix')).isoformat(),
                  'python':sys.version.split()[0], 'notebooks':completed,
                  'data_hashes_before_equal_after':True, 'data_sha256':before,
                  'model_baseline':baseline['source_commit'],
                  'documents_checked':['README.md','executive_summary.md']}
        (PROJECT/'tests/notebook_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: model baseline, document invariants and all raw/processed data hashes preserved')


if __name__ == '__main__':
    main()
