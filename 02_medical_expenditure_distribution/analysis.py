"""Weighted, descriptive MEPS HC-251 EDA. Raw workbook is read, never rewritten."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import t

PROJECT = Path(__file__).resolve().parent
RAW = PROJECT/'data/raw/h251.xlsx'
CACHE = PROJECT/'data/processed/analysis_columns.csv'
SERVICES = {'Office-based':'OBVEXP23', 'Outpatient':'OPTEXP23', 'Emergency':'ERTEXP23',
            'Inpatient':'IPTEXP23', 'Prescriptions':'RXEXP23', 'Dental':'DVTEXP23',
            'Home health agency':'HHAEXP23', 'Home health independent':'HHNEXP23',
            'Vision':'VISEXP23', 'Other supplies/equipment':'OTHEXP23'}
PAYERS = {'Out of pocket':'TOTSLF23','Medicare':'TOTMCR23','Medicaid':'TOTMCD23',
          'Private':'TOTPRV23','VA/CHAMPVA':'TOTVA23','TRICARE':'TOTTRI23',
          'Other federal':'TOTOFD23','State/local':'TOTSTL23',
          'Workers compensation':'TOTWCP23','Other unclassified':'TOTOSR23'}
COLUMNS = list(dict.fromkeys(['DUPERSID','TOTEXP23','PERWT23F','VARSTR','VARPSU',
                            'AGE23X','SEX','POVCAT23','RTHLTH31','IPDIS23','IPNGTD23']+
                            list(SERVICES.values())+list(PAYERS.values())))


def sha256(path):
    with open(path,'rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read_selected_xlsx(path, columns):
    """Stream selected named columns; avoid loading 26 million cells into memory.

    The supplied workbook has one sheet, H251, and shared-string headers.
    Fail on changed layout, formula cells, absent headers or duplicate identifiers.
    """
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with ZipFile(path) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = book.find(ns+'sheets')
        if len(sheets)!=1 or sheets[0].get('name')!='H251':
            raise ValueError('Expected a single H251 worksheet')
        strings = [''.join(node.itertext()) for node in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        def value(cell):
            if cell.find(ns+'f') is not None:
                raise ValueError('Unexpected formula in source')
            v = cell.find(ns+'v')
            if v is None: return None
            return strings[int(v.text)] if cell.get('t')=='s' else v.text
        mapping = None
        rows = []
        with archive.open('xl/worksheets/sheet1.xml') as stream:
            for _,node in ET.iterparse(stream,events=['end']):
                if node.tag != ns+'row': continue
                if mapping is None:
                    headers = {''.join(c for c in cell.get('r') if c.isalpha()):value(cell) for cell in node}
                    if len(set(headers.values()))!=len(headers): raise ValueError('Duplicate headers')
                    mapping = {col:name for col,name in headers.items() if name in columns}
                    if set(mapping.values())!=set(columns): raise ValueError('Required columns missing')
                else:
                    row = {}
                    for cell in node:
                        column = ''.join(c for c in cell.get('r') if c.isalpha())
                        if column in mapping: row[mapping[column]] = value(cell)
                    if any(v is not None for v in row.values()): rows.append(row)
                node.clear()
    frame = pd.DataFrame(rows,columns=columns)
    frame['DUPERSID'] = frame['DUPERSID'].astype('string')
    for column in columns:
        if column!='DUPERSID': frame[column]=pd.to_numeric(frame[column],errors='raise')
    return frame


def load_data(raw=RAW, cache=CACHE):
    """Cache selected columns locally, tied to both raw and cache content hashes."""
    raw,cache=Path(raw),Path(cache)
    raw_hash = sha256(raw)
    meta=cache.with_suffix('.json')
    if cache.exists() and meta.exists():
        record=json.loads(meta.read_text())
        if record.get('raw_sha256')==raw_hash and record.get('columns')==COLUMNS and record.get('cache_sha256')==sha256(cache):
            return pd.read_csv(cache,dtype={'DUPERSID':str}),raw_hash
    df=read_selected_xlsx(raw,COLUMNS)
    cache.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(cache,index=False)
    meta.write_text(json.dumps({'raw_sha256':raw_hash,'cache_sha256':sha256(cache),'columns':COLUMNS},indent=2)+'\n')
    return df,raw_hash


def validate_sample(frame):
    if frame.DUPERSID.isna().any() or frame.DUPERSID.duplicated().any(): raise ValueError('Invalid person keys')
    if not np.isfinite(frame.PERWT23F).all() or (frame.PERWT23F<0).any(): raise ValueError('Invalid weights')
    sample=frame.loc[frame.PERWT23F>0].copy()
    if sample.empty: raise ValueError('No positive person weights')
    expenses=['TOTEXP23']+list(SERVICES.values())+list(PAYERS.values())
    if not np.isfinite(sample[expenses]).all().all() or (sample[expenses]<0).any().any():
        raise ValueError('Missing or negative expenditure values; do not silently drop/recode')
    if not np.isfinite(sample[['VARSTR','VARPSU']]).all().all() or (sample[['VARSTR','VARPSU']]<=0).any().any():
        raise ValueError('Invalid design variables')
    for components in [SERVICES,PAYERS]:
        diff=sample[list(components.values())].sum(axis=1)-sample.TOTEXP23
        # PUF components are independently rounded to whole dollars. Report differences.
        if diff.abs().max()>10: raise ValueError('Component reconciliation exceeds $10 per person')
    return sample


def check_arrays(values,weights):
    y,w=np.asarray(values,dtype=float),np.asarray(weights,dtype=float)
    if y.ndim!=1 or y.shape!=w.shape or not len(y): raise ValueError('Invalid shapes')
    if not np.isfinite(y).all() or not np.isfinite(w).all() or (y<0).any() or (w<=0).any():
        raise ValueError('Nonnegative finite values and positive finite weights required')
    return y,w


def weighted_quantile(values,weights,q):
    """Left-inverse weighted empirical CDF; no interpolation between dollar values."""
    y,w=check_arrays(values,weights)
    if not 0<=q<=1: raise ValueError('q outside [0,1]')
    order=np.argsort(y,kind='stable');y,w=y[order],w[order]
    return float(y[min(np.searchsorted(np.cumsum(w),q*w.sum(),side='left'),len(y)-1)])


def top_fraction(values,weights,fraction):
    """Exactly p of weighted population, splitting boundary ties proportionally.

    Membership is a descriptive allocation, not a literal subset of persons.
    Every member of the same expenditure tie receives the same fraction.
    """
    y,w=check_arrays(values,weights)
    if not 0<=fraction<=1: raise ValueError('fraction outside [0,1]')
    if fraction==0: return np.zeros(len(y))
    if fraction==1: return np.ones(len(y))
    order=np.argsort(-y,kind='stable');ys,ws=y[order],w[order]
    target=fraction*w.sum();index=min(np.searchsorted(np.cumsum(ws),target,side='left'),len(y)-1)
    cutoff=ys[index];above=y>cutoff;tied=y==cutoff
    remaining=target-w[above].sum()
    membership=above.astype(float)
    membership[tied]=np.clip(remaining/w[tied].sum(),0,1)
    return membership


def concentration(values,weights,fraction):
    y,w=check_arrays(values,weights)
    if np.dot(y,w)<=0: raise ValueError('Spending shares undefined for all-zero expenditure')
    a=top_fraction(y,w,fraction)
    return float(np.dot(y*w,a)/np.dot(y,w))


def lorenz(values,weights):
    y,w=check_arrays(values,weights)
    if np.dot(y,w)<=0: raise ValueError('Lorenz curve undefined for all-zero expenditure')
    order=np.argsort(y,kind='stable');y,w=y[order],w[order]
    return np.r_[0,np.cumsum(w)/w.sum()],np.r_[0,np.cumsum(y*w)/np.dot(y,w)]


def survey_mean(frame):
    """With-replacement stratified-PSU Taylor SE for the overall weighted mean.

    Linearized contributions are w_i*(y_i-mean)/sum(w). All positive-weight
    persons enter; singleton strata fail explicitly. No FPC is assumed.
    """
    y,w=check_arrays(frame.TOTEXP23,frame.PERWT23F);mean=np.average(y,weights=w)
    lin=frame[['VARSTR','VARPSU']].copy();lin['z']=w*(y-mean)/w.sum()
    psu=lin.groupby(['VARSTR','VARPSU']).z.sum()
    counts=psu.groupby(level=0).size()
    if (counts<2).any(): raise ValueError('Singleton stratum requires an explicit variance policy')
    variance=0.
    for _,z in psu.groupby(level=0):variance+=len(z)/(len(z)-1)*np.square(z-z.mean()).sum()
    df=int(len(psu)-len(counts));se=float(np.sqrt(variance));margin=t.ppf(.975,df)*se
    return {'mean':float(mean),'se':se,'ci_low':float(mean-margin),'ci_high':float(mean+margin),'design_df':df}


def grouped(frame, column, membership):
    w=frame.PERWT23F.to_numpy();y=frame.TOTEXP23.to_numpy();a=np.asarray(membership)
    out=[]
    for group in sorted(frame[column].unique()):
        mask=(frame[column]==group).to_numpy();wg=w[mask];yg=y[mask]
        out.append({'group':group,'n':int(mask.sum()),'population_share':float(wg.sum()/w.sum()),
                    'top5_population_share':float(np.dot(w[mask],a[mask])/np.dot(w,a)),
                    'mean':float(np.average(yg,weights=wg)),
                    'median':weighted_quantile(yg,wg,.5),
                    'spending_share':float(np.dot(wg,yg)/np.dot(w,y))})
    return pd.DataFrame(out)


def component_table(frame,columns,membership):
    w=frame.PERWT23F.to_numpy();a=np.asarray(membership);total=np.dot(w,frame.TOTEXP23)
    top_total=np.dot(w*a,frame.TOTEXP23)
    return pd.DataFrame([{'component':name,'overall_share':float(np.dot(w,frame[col])/total),
                         'top5_share':float(np.dot(w*a,frame[col])/top_total)} for name,col in columns.items()])


def analyze(frame):
    df=validate_sample(frame);y,w=df.TOTEXP23.to_numpy(),df.PERWT23F.to_numpy()
    top=top_fraction(y,w,.05)
    df['age_group']=pd.cut(df.AGE23X,[-np.inf,-.01,17,44,64,np.inf],
                           labels=['Unknown','0–17','18–44','45–64','65+']).astype(str)
    df['health_group']=df.RTHLTH31.map({1:'Excellent',2:'Very good',3:'Good',4:'Fair',5:'Poor'}).fillna('Missing/inapplicable')
    df['poverty_group']=df.POVCAT23.map({1:'Below poverty',2:'Near poor',3:'Low income',4:'Middle income',5:'High income'}).fillna('Missing/inapplicable')
    df['inpatient_group']=np.where(df.IPDIS23<0,'Missing/inapplicable',np.where(df.IPDIS23>0,'Any inpatient stay','No inpatient stay'))
    mean=survey_mean(df);x,l=lorenz(y,w)
    summary={**mean,'raw_n':len(frame),'positive_weight_n':len(df),'zero_weight_n':int((frame.PERWT23F==0).sum()),
             'represented_population':float(w.sum()),'total_spending':float(np.dot(w,y)),
             'median':weighted_quantile(y,w,.5),'p90':weighted_quantile(y,w,.9),
             'p95':weighted_quantile(y,w,.95),'p99':weighted_quantile(y,w,.99),
             'zero_share':float(w[y==0].sum()/w.sum()),'gini':float(1-2*np.trapezoid(l,x)),
             'top1_share':concentration(y,w,.01),'top5_share':concentration(y,w,.05),
             'top10_share':concentration(y,w,.1),'bottom50_share':1-concentration(y,w,.5),
             'unweighted_mean':float(y.mean()),'unweighted_median':float(np.median(y)),
             'unweighted_top5_share':concentration(y,np.ones(len(y)),.05),
             'component_max_abs_difference':{name:float((df[list(cols.values())].sum(axis=1)-df.TOTEXP23).abs().max()) for name,cols in [('services',SERVICES),('payers',PAYERS)]},
             'component_weighted_difference':{name:float(np.dot(w,df[list(cols.values())].sum(axis=1)-df.TOTEXP23)) for name,cols in [('services',SERVICES),('payers',PAYERS)]}}
    tables={name:grouped(df,col,top) for name,col in [('age','age_group'),('health','health_group'),('poverty','poverty_group'),('inpatient','inpatient_group')]}
    tables['services']=component_table(df,SERVICES,top);tables['payers']=component_table(df,PAYERS,top)
    tables['concentration']=pd.DataFrame({'population_fraction':[.01,.05,.1,.5],
                                        'spending_share':[summary['top1_share'],summary['top5_share'],summary['top10_share'],1-summary['bottom50_share']]})
    return df,summary,tables


def export_results(summary,tables,raw_hash):
    out=PROJECT/'outputs';out.mkdir(exist_ok=True)
    record={**summary,'raw_sha256':raw_hash,'source':'AHRQ MEPS HC-251, 2023',
            'concentration_boundary':'fractional allocation proportional to weights within expenditure ties',
            'inference':'Taylor 95% t interval for overall mean only; other metrics are descriptive point estimates'}
    (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    for name,table in tables.items():table.to_csv(out/(name+'.csv'),index=False)
    from reporting import summary_markdown
    (PROJECT/'eda_summary.md').write_text(summary_markdown(summary,tables))


if __name__=='__main__':
    frame,digest=load_data();sample,summary,tables=analyze(frame);export_results(summary,tables,digest)
    print(json.dumps(summary,indent=2))
