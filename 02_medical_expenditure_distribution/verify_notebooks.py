"""Run MEPS notebooks, verify raw preservation and independent aggregate checks."""
from pathlib import Path
import sys
import os
import json
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec
from analysis import PROJECT,load_data,analyze,sha256,lorenz
from reporting import summary_markdown


class ProjectKernel(KernelManager):
    @property
    def kernel_spec(self):
        return KernelSpec(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                          display_name='Project Python',language='python')


def verify_aggregates():
    raw,digest=load_data();sample,s,tables=analyze(raw)
    assert (s['raw_n'],s['positive_weight_n'],s['zero_weight_n'])==(18919,18463,456)
    assert np.isclose(s['represented_population'],334530273,atol=.5,rtol=0)
    x,l=lorenz(sample.TOTEXP23,sample.PERWT23F)
    for p,key in [(.01,'top1_share'),(.05,'top5_share'),(.1,'top10_share')]:
        np.testing.assert_allclose(s[key],1-np.interp(1-p,x,l),atol=1e-12)
    np.testing.assert_allclose(s['bottom50_share'],np.interp(.5,x,l),atol=1e-12)
    for name in ['age','health','poverty','inpatient']:
        table=tables[name]
        for column in ['population_share','top5_population_share','spending_share']:
            np.testing.assert_allclose(table[column].sum(),1,atol=1e-12)
        np.testing.assert_allclose(np.dot(table.population_share,table['mean']),s['mean'],rtol=1e-12)
    assert s['component_max_abs_difference']['services']==0
    assert s['component_max_abs_difference']['payers']<=10
    # Independent matrix form of stratified-PSU Taylor variance.
    z=sample.PERWT23F*(sample.TOTEXP23-s['mean'])/sample.PERWT23F.sum()
    matrix=sample.assign(z=z).pivot_table(index='VARSTR',columns='VARPSU',values='z',aggfunc='sum')
    sizes=matrix.notna().sum(axis=1)
    expected_variance=(sizes*matrix.var(axis=1,ddof=1)).sum()
    np.testing.assert_allclose(s['se']**2,expected_variance,rtol=1e-12)
    saved=json.loads((PROJECT/'outputs/summary.json').read_text())
    for key,value in s.items():
        if isinstance(value,(float,int)):np.testing.assert_allclose(saved[key],value,rtol=1e-12)
    assert (PROJECT/'eda_summary.md').read_text()==summary_markdown(s,tables)
    assert saved['raw_sha256']==digest
    return digest


def main():
    before={str(f.relative_to(PROJECT)):sha256(f) for f in (PROJECT/'data/raw').rglob('*') if f.is_file()}
    done=[];executed=[]
    with tempfile.TemporaryDirectory(prefix='medical-notebooks-') as temp:
        os.environ['MPLCONFIGDIR']=str(Path(temp)/'mpl')
        os.environ['XDG_CACHE_HOME']=str(Path(temp)/'cache')
        os.environ['IPYTHONDIR']=str(Path(temp)/'ipython')
        for path in sorted((PROJECT/'notebooks').glob('*.ipynb')):
            notebook=nbformat.read(path,as_version=4)
            NotebookClient(notebook,timeout=180,kernel_manager_class=ProjectKernel,
                           resources={'metadata':{'path':str(path.parent)}}).execute()
            assert not any(o.output_type=='error' for c in notebook.cells for o in c.get('outputs',[]))
            executed.append((path,notebook))
            done.append({'notebook':path.name,'cells':len(notebook.cells),'passed':True})
            print('PASS',path.name,flush=True)
    digest=verify_aggregates()
    assert before=={str(f.relative_to(PROJECT)):sha256(f) for f in (PROJECT/'data/raw').rglob('*') if f.is_file()}
    for path,notebook in executed:nbformat.write(notebook,path)
    report={'verified_at':datetime.now(ZoneInfo('America/Phoenix')).isoformat(),
            'python':sys.version.split()[0],'notebooks':done,'raw_files_sha256':before,
            'raw_files_unchanged':True,'independent_checks':['Lorenz/concentration complement',
                'subgroup population and expenditure partitions','subgroup mean reconstruction',
                'official sample counts and rounded population total','matrix Taylor variance',
                'generated report and saved aggregate figures'],
            'code_sha256':{f.name:sha256(f) for f in PROJECT.glob('*.py')},
            'notebook_sha256':{path.name:sha256(path) for path,_ in executed},
            'figure_sha256':{f.name:sha256(f) for f in (PROJECT/'outputs').glob('*.png')}}
    (PROJECT/'outputs/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS independent checks; raw data preserved')


if __name__=='__main__':main()
