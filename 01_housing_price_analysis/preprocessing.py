"""Shared validation for the original housing sample; no imputation or row selection change."""
from pathlib import Path
import numpy as np
import pandas as pd


def validate_county_keys(frame):
    """Require non-null, unique five-digit county identifiers (not numeric values)."""
    out = frame.copy()
    keys = out['fips'].astype('string')
    valid = keys.str.fullmatch(r'\d{5}').fillna(False)
    # State/territory total identifiers end in 000; PR is outside this project.
    valid &= ~keys.str.endswith('000').fillna(True)
    valid &= ~keys.str.startswith('72').fillna(True)
    if not valid.all() or keys.duplicated().any():
        raise ValueError('FIPS must be unique, non-null five-digit county keys; PR excluded')
    out['fips'] = keys.astype(str)
    return out


def extract_counties(frame, geo_col='GEO_ID'):
    # ACS county summary level 050; a five-digit suffix alone is insufficient.
    out = frame.loc[frame[geo_col].astype('string').str.fullmatch(
        r'0500000US\d{5}').fillna(False)].copy()
    out['fips'] = out[geo_col].str[-5:]
    out = out.loc[~out['fips'].str.startswith('72')].copy()
    return validate_county_keys(out)


def read_county_csv(path):
    return validate_county_keys(pd.read_csv(path, dtype={'fips': str}))


def merge_counties(left, right):
    left, right = validate_county_keys(left), validate_county_keys(right)
    return left.merge(right, on='fips', how='inner', validate='one_to_one')


def education_shares(frame, total, ba_columns, hs_columns):
    """Reject incomplete counts rather than treating missing components as zero."""
    columns = list(dict.fromkeys([total] + hs_columns + ba_columns))
    values = frame[columns].apply(pd.to_numeric, errors='coerce')
    if not np.isfinite(values.to_numpy()).all() or (values < 0).any().any():
        raise ValueError('Education counts must be complete, finite and nonnegative')
    if (values[total] <= 0).any():
        raise ValueError('Education denominator must be positive')
    ba = values[ba_columns].sum(axis=1, min_count=len(ba_columns)) / values[total]
    hs = values[hs_columns].sum(axis=1, min_count=len(hs_columns)) / values[total]
    if not (ba.between(0, 1) & hs.between(0, 1) & (hs >= ba)).all():
        raise ValueError('Invalid education shares')
    return ba, hs


def annual_available_months(frame, year=2022):
    """Retain historical available-month means; report counts, never impute months."""
    columns = sorted(c for c in frame if c.startswith(f'{year}-'))
    expected = pd.date_range(f'{year}-01-01', periods=12, freq='ME').strftime('%Y-%m-%d').tolist()
    if columns != expected:
        raise ValueError('Exactly twelve month-end columns are required')
    values = frame[columns].apply(pd.to_numeric, errors='raise')
    observed = values.to_numpy()[values.notna().to_numpy()]
    if not np.isfinite(observed).all() or (observed <= 0).any():
        raise ValueError('Observed home values must be finite and positive')
    return values.mean(axis=1), values.notna().sum(axis=1)


def preserve_processed(frame, path):
    """Verify existing data without rewriting it; create output only if absent."""
    path = Path(path)
    if path.exists():
        existing = pd.read_csv(path, dtype={'fips': str})
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), existing,
                                      check_dtype=False, rtol=1e-12, atol=1e-12)
        print(f'Verified unchanged: {path.name}')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
        print(f'Created: {path.name}')
